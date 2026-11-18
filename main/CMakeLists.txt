# libloragw = Semtech lora_gateway v5.0.1 (SX1301 HAL), ported to ESP-IDF.
# Original files: loragw_reg.c, loragw_radio.c, loragw_fpga.c, loragw_lbt.c (unchanged
# apart from printing errors), loragw_hal.c (firmware check on the heap, lgw_get_instcnt).
# ESP32 files: loragw_spi.c (spi_master), loragw_aux.c (FreeRTOS delays),
# loragw_gpio.c (reset pulse of reset_lgw.sh), loragw_gps.c (UART driver),
# loragw_i2c.c (OLED only: the SX1301 HAL has no I2C).
set(libloragw_src
    "libloragw/loragw_aux.c"
    "libloragw/loragw_fpga.c"
    "libloragw/loragw_gpio.c"
    "libloragw/loragw_gps.c"
    "libloragw/loragw_hal.c"
    "libloragw/loragw_i2c.c"
    "libloragw/loragw_lbt.c"
    "libloragw/loragw_radio.c"
    "libloragw/loragw_reg.c"
    "libloragw/loragw_spi.c"
)

set(libtools_src
    "libtools/base64.c"
    "libtools/parson.c"
    "libtools/tinymt32.c"
)

set(pkt_fwd_src
    "packet_forwarder/jitqueue.c"
    "packet_forwarder/lora_pkt_fwd.c"
    "packet_forwarder/mqtt_gw.c"
    "packet_forwarder/cs_codec.c"
    "packet_forwarder/weblog.c"
    "packet_forwarder/ioe.c"
    "packet_forwarder/led_indication.c"
    "packet_forwarder/web_config.c"
    "packet_forwarder/http_server.c"
    "packet_forwarder/diag.c"
    "packet_forwarder/gw_mdns.c"
)


idf_component_register(SRCS
    "${libtools_src}"
    "${libloragw_src}"
    "${pkt_fwd_src}"
    "${main_src}"
    INCLUDE_DIRS "libloragw"
    INCLUDE_DIRS "libtools"
    INCLUDE_DIRS "packet_forwarder"
)

# Firmware version from the Git tag (see the top-level CMakeLists.txt)
idf_build_get_property(fw_version PROJECT_VER)
target_compile_definitions(${COMPONENT_LIB} PRIVATE "ESP32_SX1301_VERSION=\"${fw_version}\"")

# ---------------------------------------------------------------------------
# Board pin map (each value can still be overridden with -D...)
#   BOARD=esp32            -> elseif(IDF_TARGET STREQUAL "esp32") block
#   BOARD=esp32s3_n16r8    -> if(IDF_TARGET STREQUAL "esp32s3") block
#   BOARD=esp32s3_n32r16v  -> if(IDF_TARGET STREQUAL "esp32s3") block
# Both S3 modules use the same DevKitC-1 layout and the same pins: they only
# differ in flash/PSRAM (boards/<board>.defaults).
# ---------------------------------------------------------------------------
if(NOT CMAKE_BUILD_EARLY_EXPANSION AND DEFINED BOARD AND NOT "${BOARD}" STREQUAL "${CONFIG_GW_BOARD_ID}")
    message(FATAL_ERROR "BOARD=${BOARD} but sdkconfig has board ${CONFIG_GW_BOARD_ID}. "
                        "Delete the old sdkconfig.${BOARD} and build-${BOARD}/ and run scripts/build.sh ${BOARD} again.")
endif()

if(IDF_TARGET STREQUAL "esp32s3")
    # ESP32-S3 (WROOM-1U-N16R8 or WROOM-2-N32R16V DevKitC-1) + SX1301 concentrator with a
    # Raspberry Pi 40-pin header (RAK2245 Pi HAT, RHF0M301 / iC880A on an RPi adapter...).
    # Avoids GPIO 26-32 (flash), 33-37 (octal PSRAM), 19/20 (USB console), 43/44 (UART0),
    # strapping pins 0/3/45/46 and 47/48 (1.8 V on the N32R16V; kept free on the N16R8 too).
    #   ESP32-S3        SX1301 board (RPi header pin)
    #   GPIO11  ------> MOSI   (19)
    #   GPIO13  <------ MISO   (21)
    #   GPIO12  ------> SCLK   (23)
    #   GPIO10  ------> CE0/CS (24)  SX1301 chip select
    #   GPIO6   ------> RESET  (26)  SX1301 reset, active high: Radioenge RD43HAT pin 26 (BCM7);
    #                          RAK2245 / RAK831 adapter use pin 11 (BCM17 of reset_lgw.sh)
    #   GPIO4   <-----> SDA          optional OLED SSD1306 (the SX1301 HAL has no I2C)
    #   GPIO5   ------> SCL
    #   GPIO17  ------> GPS_RXD (8)  (optional, GPS switched on in the web page)
    #   GPIO18  <------ GPS_TXD (10) (optional; the PPS goes to the SX1301 on the board itself)
    #   5V      ------> 5V     (2/4)
    #   GND     ------> GND    (6)
    target_compile_definitions(${COMPONENT_LIB} PRIVATE
        SX1301_SPI_HOST=SPI2_HOST
        PIN_NUM_CLK=12
        PIN_NUM_MISO=13
        PIN_NUM_MOSI=11
        PIN_NUM_CS=10
        SX1301_RESET_PIN=6
        SX1301_POWER_EN_PIN=GPIO_NUM_NC     # RAK2245 / RHF0M301 / iC880A: no POWER_EN line
        I2C_MASTER_SDA_IO=4
        I2C_MASTER_SCL_IO=5
        GPS_UART_TXD=17
        GPS_UART_RXD=18
        # GPS: switched on/off in the web page (section GPS) or with "gps on|off"; add
        # GPS_DISABLE here only to build a firmware without it
        USER_BUTTON_1=0                     # BOOT button: hold right after reset -> Soft AP mode
        USER_BUTTON_2=GPIO_NUM_NC
        BLINK_GPIO=GPIO_NUM_NC              # on-board LED of S3 boards is an RGB WS2812
        LED_BLUE_GPIO=GPIO_NUM_NC
        LED_GREEN_GPIO=GPIO_NUM_NC
        LED_RED_GPIO=GPIO_NUM_NC
    )
elseif(IDF_TARGET STREQUAL "esp32")
    # ESP32 (classic: ESP32-WROOM-32/32U DevKit) + SX1301 concentrator with a Raspberry Pi
    # 40-pin header. SPI on the native VSPI pins (18/19/23/5). GPIO12 (MTDI) is avoided:
    # it is a strapping pin, pulled high at boot it selects 1.8 V flash.
    #   ESP32           SX1301 board (RPi header pin)
    #   GPIO23  ------> MOSI   (19)
    #   GPIO19  <------ MISO   (21)
    #   GPIO18  ------> SCLK   (23)
    #   GPIO5   ------> CE0/CS (24)  SX1301 chip select
    #   GPIO4   ------> RESET  (26)  SX1301 reset, active high: Radioenge RD43HAT pin 26 (BCM7);
    #                          RAK2245 / RAK831 adapter use pin 11 (BCM17 of reset_lgw.sh)
    #   GPIO21  <-----> SDA          optional OLED SSD1306
    #   GPIO22  ------> SCL
    #   GPIO17  ------> GPS_RXD (8)  (optional, GPS switched on in the web page)
    #   GPIO16  <------ GPS_TXD (10) (optional)
    #   5V      ------> 5V     (2/4)
    #   GND     ------> GND    (6)
    target_compile_definitions(${COMPONENT_LIB} PRIVATE
        SX1301_SPI_HOST=SPI3_HOST
        PIN_NUM_CLK=18
        PIN_NUM_MISO=19
        PIN_NUM_MOSI=23
        PIN_NUM_CS=5
        SX1301_RESET_PIN=4
        SX1301_POWER_EN_PIN=GPIO_NUM_NC
        I2C_MASTER_SDA_IO=21
        I2C_MASTER_SCL_IO=22
        GPS_UART_TXD=17
        GPS_UART_RXD=16
        USER_BUTTON_1=0                     # BOOT button: hold right after reset -> Soft AP mode
        USER_BUTTON_2=GPIO_NUM_NC
        BLINK_GPIO=2                        # on-board blue LED of most ESP32 DevKits
        LED_BLUE_GPIO=GPIO_NUM_NC
        LED_GREEN_GPIO=GPIO_NUM_NC
        LED_RED_GPIO=GPIO_NUM_NC
    )
endif()


# libloragw (Semtech, written for 32-bit Linux) prints uint32_t/int32_t with %u/%d/%X.
# On Xtensa/RISC-V newlib, uint32_t is "unsigned long" (same 32 bits), so the output is
# correct but GCC reports -Wformat, which ESP-IDF turns into an error (-Werror=all).
# Kept as warnings for these files only, instead of editing ~100 printf of the HAL.
set_source_files_properties(${libloragw_src}
    TARGET_DIRECTORY ${COMPONENT_LIB}
    PROPERTIES COMPILE_OPTIONS "-Wno-error=format;-Wno-format")
