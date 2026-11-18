/*
 / _____)             _              | |
( (____  _____ ____ _| |_ _____  ____| |__
 \____ \| ___ |    (_   _) ___ |/ ___)  _ \
 _____) ) ____| | | || |_| ____( (___| | | |
(______/|_____)_|_|_| \__)_____)\____)_| |_|
  (C)2019 Semtech

Description:
    Functions to reset the LoRa concentrator (SX1301) from GPIO pins.

    ESP32 PORT: on a Raspberry Pi the SX1301 is reset BEFORE the packet
    forwarder starts, by the shell script lora_gateway/reset_lgw.sh
    (GPIO17 high 100 ms, low 100 ms through /sys/class/gpio). There is no
    shell on the ESP32, so the same pulse is generated here and called by the
    packet forwarder right before lgw_start() (same idea as esxp1302).

License: Revised BSD License, see LICENSE.TXT file include in the project
*/

#ifndef _LORAGW_GPIO_H
#define _LORAGW_GPIO_H

#include "driver/gpio.h"

/* RESET of the SX1301, active HIGH. Raspberry Pi header: pin 26 / BCM7 on the
 * Radioenge LoRaWAN Gateway (main board of the project), pin 11 / BCM17 on RAK2245,
 * RHF0M301, iC880A adapters... Only the wire changes; the ESP32 GPIO is set per
 * board in main/CMakeLists.txt. */
#ifndef SX1301_RESET_PIN
#define SX1301_RESET_PIN          GPIO_NUM_4
#endif

/* Optional power enable of the concentrator (GPIO_NUM_NC when the board has none) */
#ifndef SX1301_POWER_EN_PIN
#define SX1301_POWER_EN_PIN       GPIO_NUM_NC
#endif

#define SX1301_PIN_BIT(p)         (((int)(p) >= 0) ? (1ULL << (p)) : 0ULL)
#define SX1301_GPIO_PIN_SEL       (SX1301_PIN_BIT(SX1301_RESET_PIN) | SX1301_PIN_BIT(SX1301_POWER_EN_PIN))

/* reset the concentrator: POWER_EN high (if any), RESET high 100 ms, low 100 ms */
void lgw_reset(void);

#endif
