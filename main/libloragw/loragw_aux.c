/*
 / _____)             _              | |
( (____  _____ ____ _| |_ _____  ____| |__
 \____ \| ___ |    (_   _) ___ |/ ___)  _ \
 _____) ) ____| | | || |_| ____( (___| | | |
(______/|_____)_|_|_| \__)_____)\____)_| |_|
  (C)2013 Semtech-Cycleo

Description:
    LoRa concentrator HAL auxiliary functions

    ESP32 PORT: clock_nanosleep() does not exist in FreeRTOS. wait_ms() sleeps
    with vTaskDelay() for the whole RTOS ticks and busy-waits the remainder
    with esp_rom_delay_us(). The SX1302 port (esxp1302) only did
    vTaskDelay(ms / portTICK_PERIOD_MS): with the default 100 Hz tick,
    wait_ms(1)...wait_ms(9) became NO delay at all. The SX1301 start sequence
    (lgw_start: radio reset, PLL lock, calibration) relies on those 1-5 ms
    waits, so here they are real.

License: Revised BSD License, see LICENSE.TXT file include in the project
Maintainer: Sylvain Miermont
*/


/* -------------------------------------------------------------------------- */
/* --- DEPENDANCIES --------------------------------------------------------- */

#include <stdio.h>  /* printf fprintf */

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_rom_sys.h"    /* esp_rom_delay_us */

#include "loragw_aux.h"

/* -------------------------------------------------------------------------- */
/* --- PRIVATE MACROS ------------------------------------------------------- */

#if DEBUG_AUX == 1
    #define DEBUG_MSG(str)                fprintf(stderr, str)
    #define DEBUG_PRINTF(fmt, args...)    fprintf(stderr,"%s:%d: "fmt, __FUNCTION__, __LINE__, args)
#else
    #define DEBUG_MSG(str)
    #define DEBUG_PRINTF(fmt, args...)
#endif

/* -------------------------------------------------------------------------- */
/* --- PUBLIC FUNCTIONS DEFINITION ------------------------------------------ */

void wait_ms(unsigned long a) {
    const unsigned long tick_ms = portTICK_PERIOD_MS;   /* 10 ms at 100 Hz, 1 ms at 1000 Hz */

    DEBUG_PRINTF("NOTE dly: %lu ms\n", a);

    if (a >= tick_ms) {
        /* +1 tick: vTaskDelay(n) may return up to 1 tick early (partial first tick) */
        vTaskDelay((TickType_t)(a / tick_ms) + 1);
        a %= tick_ms;
        if (a == 0) {
            return;
        }
    }
    /* remainder shorter than one tick: busy-wait (never sleeps less than asked) */
    esp_rom_delay_us((uint32_t)a * 1000U);
}

/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */

void wait_us(unsigned long a) {
    if (a >= 1000UL * portTICK_PERIOD_MS) {
        wait_ms(a / 1000UL);
        a %= 1000UL;
    }
    if (a > 0) {
        esp_rom_delay_us((uint32_t)a);
    }
}

/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */

void timeout_start(struct timeval * start) {
    gettimeofday(start, NULL);
}

/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */

int timeout_check(struct timeval start, uint32_t timeout_ms) {
    struct timeval tm;
    int64_t ms;

    gettimeofday(&tm, NULL);
    ms = (int64_t)(tm.tv_sec - start.tv_sec) * 1000 + (tm.tv_usec - start.tv_usec) / 1000;
    return (ms > (int64_t)timeout_ms) ? -1 : 0;
}

/* --- EOF ------------------------------------------------------------------ */
