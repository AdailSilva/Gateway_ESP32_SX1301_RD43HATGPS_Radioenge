/*
 / _____)             _              | |
( (____  _____ ____ _| |_ _____  ____| |__
 \____ \| ___ |    (_   _) ___ |/ ___)  _ \
 _____) ) ____| | | || |_| ____( (___| | | |
(______/|_____)_|_|_| \__)_____)\____)_| |_|
  (C)2019 Semtech

Description:
    Functions to reset the LoRa concentrator (SX1301) from GPIO pins.
    Same timing as lora_gateway/reset_lgw.sh.

License: Revised BSD License, see LICENSE.TXT file include in the project
*/

#include "loragw_gpio.h"
#include "loragw_aux.h"


void lgw_reset(void)
{
    gpio_config_t gpio_conf = {
        .intr_type = GPIO_INTR_DISABLE,
        .mode = GPIO_MODE_OUTPUT,
        .pin_bit_mask = SX1301_GPIO_PIN_SEL,
        .pull_down_en = 0,
        .pull_up_en = 0,
    };

    /* lgw_reset() is called more than once per boot (pkt_fwd_main and the
     * wiring diagnostic). gpio_config() reserves output pins and, since
     * ESP-IDF 5.x, warns "gpio: conflict found for GPIO[n]" when the pin is
     * already reserved -- by our own previous call. gpio_reset_pin() releases
     * the reservation first; the level is forced LOW before the output is
     * enabled again so the SX1301 does not see a spurious reset pulse. */
    gpio_reset_pin(SX1301_RESET_PIN);
    gpio_set_level(SX1301_RESET_PIN, 0);
    if (SX1301_POWER_EN_PIN != GPIO_NUM_NC) {
        gpio_reset_pin(SX1301_POWER_EN_PIN);
    }
    gpio_config(&gpio_conf);

    if (SX1301_POWER_EN_PIN != GPIO_NUM_NC) {
        gpio_set_level(SX1301_POWER_EN_PIN, 1);
        wait_ms(100);
    }
    /* reset_lgw.sh: echo "1" > value; sleep 0.1; echo "0" > value; sleep 0.1 */
    gpio_set_level(SX1301_RESET_PIN, 1);
    wait_ms(100);
    gpio_set_level(SX1301_RESET_PIN, 0);
    wait_ms(100);
}
