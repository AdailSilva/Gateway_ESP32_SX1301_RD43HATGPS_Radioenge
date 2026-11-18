/*
 / _____)             _              | |
( (____  _____ ____ _| |_ _____  ____| |__
 \____ \| ___ |    (_   _) ___ |/ ___)  _ \
 _____) ) ____| | | || |_| ____( (___| | | |
(______/|_____)_|_|_| \__)_____)\____)_| |_|
  (C)2013 Semtech-Cycleo

Description:
    LoRa concentrator HAL common auxiliary functions

License: Revised BSD License, see LICENSE.TXT file include in the project
Maintainer: Sylvain Miermont
*/


#ifndef _LORAGW_AUX_H
#define _LORAGW_AUX_H

/* -------------------------------------------------------------------------- */
/* --- DEPENDANCIES --------------------------------------------------------- */

#include <stdint.h>
#include <sys/time.h>     /* struct timeval */

#include "config.h"    /* library configuration options (dynamically generated) */

/* -------------------------------------------------------------------------- */
/* --- PUBLIC MACROS -------------------------------------------------------- */

/**
@brief Get a particular bit value from a byte
@param b [in]   Any byte from which we want a bit value
@param p [in]   Position of the bit in the byte [0..7]
@param n [in]   Number of bits we want to get
@return The value corresponding the requested bits
*/
#define TAKE_N_BITS_FROM(b, p, n) (((b) >> (p)) & ((1 << (n)) - 1))

/* -------------------------------------------------------------------------- */
/* --- PUBLIC FUNCTIONS PROTOTYPES ------------------------------------------ */

/**
@brief Wait for a certain time (millisecond accuracy)
@param t number of milliseconds to wait.
*/
void wait_ms(unsigned long t);

/**
@brief Wait for a certain time (microsecond accuracy)
@param t number of microseconds to wait.
ESP32 port: added (the SX1302 HAL has it, the packet forwarder uses it).
*/
void wait_us(unsigned long t);

/**
@brief Start / check a timeout (from the SX1302 HAL, used by the packet forwarder)
@return 0 while running, -1 once timeout_ms elapsed since timeout_start()
*/
void timeout_start(struct timeval * start);
int timeout_check(struct timeval start, uint32_t timeout_ms);

#endif

/* --- EOF ------------------------------------------------------------------ */
