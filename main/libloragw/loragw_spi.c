/*
 / _____)             _              | |
( (____  _____ ____ _| |_ _____  ____| |__
 \____ \| ___ |    (_   _) ___ |/ ___)  _ \
 _____) ) ____| | | || |_| ____( (___| | | |
(______/|_____)_|_|_| \__)_____)\____)_| |_|
  (C)2013 Semtech-Cycleo

Description:
    Host specific functions to address the LoRa concentrator registers through
    a SPI interface.
    Single-byte read/write and burst read/write.
    Does not handle pagination.
    Could be used with multiple SPI ports in parallel (explicit file descriptor)

    ESP32 PORT (ESP-IDF spi_master), replaces loragw_spi.native.c (Linux spidev):
    - spidev open/ioctl         -> spi_bus_initialize() + spi_bus_add_device()
    - SPI_IOC_MESSAGE transfers -> spi_device_polling_transmit()
    - same frames as the Linux HAL, byte for byte:
        MUX_MODE0 (no FPGA): [R/W|addr7] [data...]
        MUX_MODE1 (FPGA)   : [mux target] [R/W|addr7] [data...]
    - bursts are cut in LGW_BURST_CHUNK (1024 B) pieces, each one a new
      transaction with the command byte(s) again, exactly like the Linux code
      (one ioctl per chunk, chip select released between chunks).
    The API (void *spi_target) is unchanged, so loragw_reg.c, loragw_fpga.c and
    loragw_radio.c are the original Semtech files.

License: Revised BSD License, see LICENSE.TXT file include in the project
Maintainer: Sylvain Miermont
*/


/* -------------------------------------------------------------------------- */
/* --- DEPENDANCIES --------------------------------------------------------- */

#include <stdint.h>     /* C99 types */
#include <stdio.h>      /* printf fprintf */
#include <stdlib.h>     /* malloc free */
#include <string.h>     /* memset */

#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "esp_attr.h"

#include "loragw_spi.h"
#include "loragw_hal.h"

/* -------------------------------------------------------------------------- */
/* --- PRIVATE MACROS ------------------------------------------------------- */

#if DEBUG_SPI == 1
    #define DEBUG_MSG(str)                fprintf(stderr, str)
    #define DEBUG_PRINTF(fmt, args...)    fprintf(stderr,"%s:%d: "fmt, __FUNCTION__, __LINE__, args)
    #define CHECK_NULL(a)                if(a==NULL){fprintf(stderr,"%s:%d: ERROR: NULL POINTER AS ARGUMENT\n", __FUNCTION__, __LINE__);return LGW_SPI_ERROR;}
#else
    #define DEBUG_MSG(str)
    #define DEBUG_PRINTF(fmt, args...)
    #define CHECK_NULL(a)                if(a==NULL){return LGW_SPI_ERROR;}
#endif

/* -------------------------------------------------------------------------- */
/* --- PRIVATE CONSTANTS ---------------------------------------------------- */

#define READ_ACCESS     0x00
#define WRITE_ACCESS    0x80

/* Pins and SPI controller come from main/CMakeLists.txt (pin map per board).
 * These defaults are only a fallback (classic ESP32, VSPI pins). */
#ifndef SX1301_SPI_HOST
#define SX1301_SPI_HOST SPI3_HOST
#endif
#ifndef PIN_NUM_MISO
#define PIN_NUM_MISO    19
#endif
#ifndef PIN_NUM_MOSI
#define PIN_NUM_MOSI    23
#endif
#ifndef PIN_NUM_CLK
#define PIN_NUM_CLK     18
#endif
#ifndef PIN_NUM_CS
#define PIN_NUM_CS      5
#endif

/* -------------------------------------------------------------------------- */
/* --- PRIVATE VARIABLES ---------------------------------------------------- */

int lgw_spi_speed_hz = SPI_SPEED;

/* Zeros clocked out on MOSI while reading a burst (DMA capable, internal RAM) */
static DMA_ATTR uint8_t spi_zero[LGW_BURST_CHUNK];

/* -------------------------------------------------------------------------- */
/* --- PRIVATE FUNCTIONS ---------------------------------------------------- */

/* number of command bytes and their value, as in loragw_spi.native.c */
static int spi_command(uint8_t spi_mux_mode, uint8_t spi_mux_target, uint8_t rw, uint8_t address, uint8_t *cmd) {
    if (spi_mux_mode == LGW_SPI_MUX_MODE1) {
        cmd[0] = spi_mux_target;
        cmd[1] = rw | (address & 0x7F);
        return 2;
    }
    cmd[0] = rw | (address & 0x7F);
    return 1;
}

/* one burst chunk: command byte(s) in the address phase, then the data */
static int spi_burst_chunk(spi_device_handle_t dev, const uint8_t *cmd, int cmd_size,
                           const uint8_t *tx, uint8_t *rx, int len) {
    spi_transaction_ext_t et;

    memset(&et, 0, sizeof(et));
    et.base.flags = SPI_TRANS_VARIABLE_CMD | SPI_TRANS_VARIABLE_ADDR | SPI_TRANS_VARIABLE_DUMMY;
    et.command_bits = 0;
    et.dummy_bits = 0;
    et.address_bits = 8 * cmd_size;
    et.base.addr = (cmd_size == 2) ? (((uint32_t)cmd[0] << 8) | cmd[1]) : cmd[0];
    et.base.length = 8 * len;
    et.base.rxlength = (rx != NULL) ? 8 * len : 0;
    et.base.tx_buffer = tx;
    et.base.rx_buffer = rx;
    return (spi_device_polling_transmit(dev, (spi_transaction_t *)&et) == ESP_OK) ? LGW_SPI_SUCCESS : LGW_SPI_ERROR;
}

/* -------------------------------------------------------------------------- */
/* --- PUBLIC FUNCTIONS DEFINITION ------------------------------------------ */

/* SPI initialization and configuration */
int lgw_spi_open(void **spi_target_ptr) {
    spi_device_handle_t *dev;
    esp_err_t err;

    CHECK_NULL(spi_target_ptr);

    spi_bus_config_t buscfg = {
        .miso_io_num = PIN_NUM_MISO,
        .mosi_io_num = PIN_NUM_MOSI,
        .sclk_io_num = PIN_NUM_CLK,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = LGW_BURST_CHUNK + 4,
    };
    spi_device_interface_config_t devcfg = {
        .clock_speed_hz = lgw_spi_speed_hz,
        .mode = 0,                      /* SPI mode 0, MSB first, 8 bits per word (as spidev) */
        .spics_io_num = PIN_NUM_CS,
        .queue_size = 2,
    };

    dev = malloc(sizeof(spi_device_handle_t));
    if (dev == NULL) {
        DEBUG_MSG("ERROR: MALLOC FAIL\n");
        return LGW_SPI_ERROR;
    }

    err = spi_bus_initialize(SX1301_SPI_HOST, &buscfg, SPI_DMA_CH_AUTO);
    if (err != ESP_OK) {
        printf("ERROR: spi_bus_initialize failed: %s\n", esp_err_to_name(err));
        free(dev);
        return LGW_SPI_ERROR;
    }
    err = spi_bus_add_device(SX1301_SPI_HOST, &devcfg, dev);
    if (err != ESP_OK) {
        printf("ERROR: spi_bus_add_device failed: %s\n", esp_err_to_name(err));
        spi_bus_free(SX1301_SPI_HOST);
        free(dev);
        return LGW_SPI_ERROR;
    }

    /* weak pull-up on MISO: a read of 0xFF then means "nothing answers",
     * 0x00 means "MISO held low" (SX1301 unpowered or held in reset) */
    gpio_pullup_en(PIN_NUM_MISO);

    *spi_target_ptr = (void *)dev;
    DEBUG_MSG("Note: SPI port opened and configured ok\n");
    return LGW_SPI_SUCCESS;
}

/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */

/* SPI release */
int lgw_spi_close(void *spi_target) {
    spi_device_handle_t *dev = (spi_device_handle_t *)spi_target;
    int ret = LGW_SPI_SUCCESS;

    CHECK_NULL(spi_target);
    if (spi_bus_remove_device(*dev) != ESP_OK) ret = LGW_SPI_ERROR;
    if (spi_bus_free(SX1301_SPI_HOST) != ESP_OK) ret = LGW_SPI_ERROR;
    free(dev);
    DEBUG_MSG("Note: SPI port closed\n");
    return ret;
}

/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */

/* Simple write */
int lgw_spi_w(void *spi_target, uint8_t spi_mux_mode, uint8_t spi_mux_target, uint8_t address, uint8_t data) {
    spi_transaction_t t;
    int n;

    CHECK_NULL(spi_target);
    if ((address & 0x80) != 0) {
        DEBUG_MSG("WARNING: SPI address > 127\n");
    }

    memset(&t, 0, sizeof(t));
    t.flags = SPI_TRANS_USE_TXDATA;
    n = spi_command(spi_mux_mode, spi_mux_target, WRITE_ACCESS, address, t.tx_data);
    t.tx_data[n] = data;
    t.length = 8 * (n + 1);

    if (spi_device_polling_transmit(*(spi_device_handle_t *)spi_target, &t) != ESP_OK) {
        DEBUG_MSG("ERROR: SPI WRITE FAILURE\n");
        return LGW_SPI_ERROR;
    }
    DEBUG_MSG("Note: SPI write success\n");
    return LGW_SPI_SUCCESS;
}

/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */

/* Simple read */
int lgw_spi_r(void *spi_target, uint8_t spi_mux_mode, uint8_t spi_mux_target, uint8_t address, uint8_t *data) {
    spi_transaction_t t;
    int n;

    CHECK_NULL(spi_target);
    CHECK_NULL(data);
    if ((address & 0x80) != 0) {
        DEBUG_MSG("WARNING: SPI address > 127\n");
    }

    memset(&t, 0, sizeof(t));
    t.flags = SPI_TRANS_USE_TXDATA | SPI_TRANS_USE_RXDATA;
    n = spi_command(spi_mux_mode, spi_mux_target, READ_ACCESS, address, t.tx_data);
    t.tx_data[n] = 0x00;
    t.length = 8 * (n + 1);
    t.rxlength = t.length;

    if (spi_device_polling_transmit(*(spi_device_handle_t *)spi_target, &t) != ESP_OK) {
        DEBUG_MSG("ERROR: SPI READ FAILURE\n");
        return LGW_SPI_ERROR;
    }
    *data = t.rx_data[n];   /* in_buf[command_size - 1] in the Linux HAL */
    DEBUG_MSG("Note: SPI read success\n");
    return LGW_SPI_SUCCESS;
}

/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */

/* Burst (multiple-byte) write */
int lgw_spi_wb(void *spi_target, uint8_t spi_mux_mode, uint8_t spi_mux_target, uint8_t address, uint8_t *data, uint16_t size) {
    uint8_t cmd[2];
    int cmd_size, size_to_do, chunk_size, offset;

    CHECK_NULL(spi_target);
    CHECK_NULL(data);
    if ((address & 0x80) != 0) {
        DEBUG_MSG("WARNING: SPI address > 127\n");
    }
    if (size == 0) {
        DEBUG_MSG("ERROR: BURST OF NULL LENGTH\n");
        return LGW_SPI_ERROR;
    }

    cmd_size = spi_command(spi_mux_mode, spi_mux_target, WRITE_ACCESS, address, cmd);
    for (offset = 0, size_to_do = size; size_to_do > 0; offset += chunk_size, size_to_do -= chunk_size) {
        chunk_size = (size_to_do < LGW_BURST_CHUNK) ? size_to_do : LGW_BURST_CHUNK;
        if (spi_burst_chunk(*(spi_device_handle_t *)spi_target, cmd, cmd_size, data + offset, NULL, chunk_size) != LGW_SPI_SUCCESS) {
            DEBUG_MSG("ERROR: SPI BURST WRITE FAILURE\n");
            return LGW_SPI_ERROR;
        }
        DEBUG_PRINTF("BURST WRITE: to trans %d # chunk %d # transferred %d \n", size_to_do, chunk_size, offset + chunk_size);
    }
    DEBUG_MSG("Note: SPI burst write success\n");
    return LGW_SPI_SUCCESS;
}

/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */

/* Burst (multiple-byte) read */
int lgw_spi_rb(void *spi_target, uint8_t spi_mux_mode, uint8_t spi_mux_target, uint8_t address, uint8_t *data, uint16_t size) {
    uint8_t cmd[2];
    int cmd_size, size_to_do, chunk_size, offset;

    CHECK_NULL(spi_target);
    CHECK_NULL(data);
    if ((address & 0x80) != 0) {
        DEBUG_MSG("WARNING: SPI address > 127\n");
    }
    if (size == 0) {
        DEBUG_MSG("ERROR: BURST OF NULL LENGTH\n");
        return LGW_SPI_ERROR;
    }

    cmd_size = spi_command(spi_mux_mode, spi_mux_target, READ_ACCESS, address, cmd);
    for (offset = 0, size_to_do = size; size_to_do > 0; offset += chunk_size, size_to_do -= chunk_size) {
        chunk_size = (size_to_do < LGW_BURST_CHUNK) ? size_to_do : LGW_BURST_CHUNK;
        if (spi_burst_chunk(*(spi_device_handle_t *)spi_target, cmd, cmd_size, spi_zero, data + offset, chunk_size) != LGW_SPI_SUCCESS) {
            DEBUG_MSG("ERROR: SPI BURST READ FAILURE\n");
            return LGW_SPI_ERROR;
        }
        DEBUG_PRINTF("BURST READ: to trans %d # chunk %d # transferred %d \n", size_to_do, chunk_size, offset + chunk_size);
    }
    DEBUG_MSG("Note: SPI burst read success\n");
    return LGW_SPI_SUCCESS;
}

/* --- EOF ------------------------------------------------------------------ */
