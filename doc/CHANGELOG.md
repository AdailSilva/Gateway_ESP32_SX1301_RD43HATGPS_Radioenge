# CHANGE LOG


## Unreleased
- docs: each repository is self-contained again; references to the other repositories were removed (workspace layout
  in README and user guide, CHANGELOG entries, DIAG_DEFAULT_HOST note, Radioenge board guide)
- docs: new doc/CHIRPSTACK_DEVICE_PROFILES.md: gateway registration (ChirpStack v4 and v3 gateway-profiles) and the 32 example
  device profiles (au915_0/au915_1 x revision A/B x ABP/OTAA x classes A, A+B, A+B+C, A+C), field by field, with the v3
  equivalents; README section "Cadastro no ChirpStack", the same table in CLASSES_LORAWAN.md and in the user guide
- folder and repository renamed again, without the "LoRaWAN_" prefix: LoRaWAN_Gateway_ESP32_SX1301_RD43HATGPS_Radioenge ->
  Gateway_ESP32_SX1301_RD43HATGPS_Radioenge (folder in ~/Apps/lorawan_workspace, GitHub repository, CI package/release files
  Gateway_ESP32_SX1301_RD43HATGPS_Radioenge-<version>-<board>-{full,app}.bin / -parts.zip, README, doc/ and scripts/create_github_repo.sh, which now
  renames a repository still on GitHub with the old name). A build-<board>/ configured in the old folder is deleted and
  configured again by scripts/build.sh
- repository and folder renamed, now naming the concentrator board: LoRaWAN_Gateway_ESP32_with_SX1301 ->
  LoRaWAN_Gateway_ESP32_SX1301_RD43HATGPS_Radioenge (folder in ~/Apps/lorawan_workspace, GitHub repository, CI
  package/release files LoRaWAN_Gateway_ESP32_SX1301_RD43HATGPS_Radioenge-<version>-<board>-{full,app}.bin /
  -parts.zip, README, doc/ and scripts/create_github_repo.sh)
- doc/hardware/Radioenge_LoRaWAN_Gateway.md: new section 0.1, the whole network with Radioenge equipment (this gateway +
  the Radioenge LoRaWAN EndDevice), with the network topology and the EndDevice photo from the
  Radioenge Mote LoRa manual (doc/images/radioenge/radioenge_rede_lorawan_topologia.png, radioenge_enddevice_foto.png)
- fix: the gateway stopped receiving after hours of operation and only came back after a reboot: the SX1301 was reset or lost its 32 MHz clock (power dip on TX, glitch on RESET) while the ESP32 kept running, and lgw_receive() returned 0 packets forever. Field signature: "SX1301 counter (PPS)" frozen and the "Invalid time reference" age growing from the last received frame. SX1301 watchdog:
  - libloragw: new lgw_check_alive() (chip version over SPI, registers written once by lgw_start(), 1 MHz counter advancing like the ESP32 clock since the previous call; non-blocking, a few SPI accesses);
  - thread_up checks it once per second; after 2 failures in a row, on an lgw_receive() error (it used to exit and reboot) or after 30 min without any packet (doubling up to 6 h, never with a downlink queued) it pulses RESET and calls lgw_start() again, in place (~2 s; Wi-Fi, MQTT, web, GPS and OLED untouched), and empties the JIT queues with the new jit_queue_reset() (jit_queue_init() created a new mutex on every call);
  - no limit to these restarts; more than 3 fault restarts in an hour log a hardware warning; the ESP32 reboots only when the SX1301 does not start again (3 attempts);
  - statistics: new "# SX1301 watchdog" line; README: feature, troubleshooting rows and power notes (bulk capacitor, short wires, antenna away from the RESET wire)
- security, web log (/logs, /logs_download): credentials no longer reach the RAM log shown on the web page.
  check_basic_auth() logged the whole Authorization header ("Basic base64(user:password)"; base64 is not
  encryption), so anyone reading /logs or a downloaded .log could recover the web login: the header is no longer
  logged, the comparison is constant-time, and the copies of the credential are wiped before free(). A refused
  login is logged once as "web login refused ... from <IP> <URI>" (not after "Sair"); "Authenticated!" moved to
  debug level
- security: handle_basic_auth() let the request through without a login when check_basic_auth() ran out of
  memory (ESP_ERR_NO_MEM was not treated as a failure); it now answers 503 and refuses the request
- weblog: the serial console session (REPL task "console_repl") is no longer copied to the RAM log. linenoise
  echoes every typed character to stdout, so "web_auth --pass", "mqtt --pass" and "config --wifi-pass" showed the
  password on /logs; the command replies stay on the serial port too (messages of the other tasks unchanged)
- weblog: new weblog_secret() (full text on the serial console, masked text on /logs) used for the Soft AP
  password at boot, and weblog_uri() hides the password of a "scheme://user:pass@host" broker URI in the "mqtt"
  console status and in dump_config()
- Classes LoRaWAN (A, B e C): new doc/CLASSES_LORAWAN.md (what each class is, timing diagrams, when to use
  each one, ChirpStack v4 device-profile settings, support in LMiC/LoRaMac-node/Basics Modem and the state of
  each class in this gateway); README section; new read-only web page /classes (classes_page.h, link
  "Classes" in the top bar of the main, Logs and Diagnostics pages; max_uri_handlers 24 -> 28) and Android
  app screen "Classes LoRaWAN" (school icon in the app bar of the device list and of the gateway screen)
- hardware_design/motherboard: the adapter-board schematic now has one GPIO column per board (ESP32-WROOM-32U,
  ESP32-S3-WROOM-1U-N16R8, ESP32-S3-WROOM-2-N32R16V; netlist CSV too) and a new figure esp32_radioenge_adapter_devkit_pins
  (gen_devkit_map.py: where each wire is soldered on the U1 headers of each DevKit); motherboard/README with the
  per-board pin numbers
- docs: the project is self-contained; references to other repositories of the workspace were removed (README, PORTE_ESP32,
  user guide, hardware_design, scripts, comments)
- docs: the three DevKit wiring guides (doc/hardware/ESP32-WROOM-32U_DevKit.md, ESP32-S3-WROOM-1U_N16R8_DevKit.md,
  ESP32-S3-WROOM-2_N32R16V_DevKit.md) rewritten with the same layout for the three boards and dedicated to the
  Radioenge LoRaWAN Gateway: wiring table (40-pin header + GWLORA 14-pin module), DevKit pinout, the 40-pin header from the
  top and from the bottom with that board's GPIOs (text + image), block-by-block diagram, optional OLED, direct wiring on the
  14-pin module, power, notes (RAK2245 = RESET on pin 11), post-wiring checks and build/flash
- doc: new per-board figures radioenge_header_{esp32,esp32s3_n16r8,esp32s3_n32r16v} and
  radioenge_header_cima_baixo_{esp32,esp32s3_n16r8,esp32s3_n32r16v} (SVG + 3720/3600 px PNG), generated by
  scripts/gen_wiring_radioenge.py; the shared radioenge_header_cima_baixo_esp32s3 is no longer referenced
- README: one "Pinagem" section per board (ESP32-WROOM-32U, ESP32-S3-WROOM-1U-N16R8, ESP32-S3-WROOM-2-N32R16V) with the
  Radioenge pin and the 14-pin module column; README, doc/hardware/README and the Radioenge guide show the per-board figures
- Diagnostics (web /diag and app tab): the three tests (ping, traceroute, nslookup) now start with
  chirpstack-v4.adailsilva.com.br (DIAG_DEFAULT_HOST in diag.h), also first
  in the suggestion list; screenshots web_15_diag_*.png and app gw_12_diag.png updated
- fix: crash loop right after "concentrator started" (ERROR: 24 = INVALID MAX NUMBER OF PACKETS TO FETCH, [up] failed
  packet fetch, abort/reboot): NB_PKT_MAX was 24 (value inherited from the sx1302_hal-based esxp1302 forwarder), but the SX1301 HAL accepts at most
  LGW_PKT_FIFO_SIZE = 16 per lgw_receive(). Back to 8, as in Semtech's packet_forwarder v4.0.1 (also shrinks
  TX_BUFF_SIZE from ~13 KB to ~4.5 KB); a _Static_assert keeps it within the FIFO size
- docs: user_guide.md still said lorawan-gateway in two places, now lorawan-gateway-sx1301 like the firmware
- doc: new figure radioenge_header_cima_baixo_{esp32,esp32s3} (SVG + 3600 px PNG): the Radioenge 40-pin
  header seen from the top and from the bottom, where the jumpers go in (the two rows swap sides), with each board's
  GPIOs and the GND continuity test; generated by scripts/gen_wiring_radioenge.py (header_top_bottom) and added to
  README, doc/hardware/README, the Radioenge guide (new subsection + first-power checklist row) and the three DevKit guides
- docs: README "Gravar e acompanhar o log" and doc/hardware/<board>.md with the full per-board commands
  (Do zero / Atualizar / Só monitorar: fuser on the port, ESP-IDF export, log in logs/), the build of
  the three boards, and a pkt_fwd console example (README, user_guide)
- build: fixed for ESP-IDF 6.x / GCC 16 (-std=gnu23): loragw_reg.c initialised uint8_t buf[4] with a 4-char
  string literal ("\x00\x00\x00\x00", 5 bytes with the NUL), now an error (-Werror=unterminated-string-initialization);
  replaced by {0, 0, 0, 0}
- main/CMakeLists.txt: pin-map comments name header pin 26 (Radioenge) for the SX1301 RESET, pin 11 for RAK2245
- Radioenge LoRaWAN Gateway (RD43HAT / RD43HATGPS, Brazilian, ANATEL 02053-18-07215) is now the main
  concentrator of the project: new guide doc/hardware/Radioenge_LoRaWAN_Gateway.md (specs, wiring, power, GPS/PPS,
  first-power checklist); README, doc/hardware/*, user_guide and PORTE_ESP32 name it first. Firmware unchanged
  except comments and messages: the only wiring difference from the RAK2245 is the RESET on header pin 26
  (BCM GPIO7) instead of 11; same ESP32 GPIO (4 on the ESP32, 6 on the S3)
- power notes: the Radioenge board draws 300 mA in RX and 700 mA in TX (+27 dBm): 5 V / 2 A supply always
- doc/images/web/: the 26 screenshots of the web pages, taken from this firmware's own HTML/JS with sample data
  (temperature card "sem sensor", SX1301 log, SX1301_conf plan JSON, GPS with a valid PPS time reference)
- doc/images/app/: the 14 screens of the Android app, reproduced from app_flutter/lib with sample data
- README.md and app_flutter/README.md: screenshots back in every section
- doc/user_guide.md (English): user guide for the SX1301 boards, wiring and PPS
- app: GPS texts name the SX1301 board and the header pin (no "HAT")

## v0.0.1 (first release of LoRaWAN_Gateway_ESP32_with_SX1301, now LoRaWAN_Gateway_ESP32_SX1301_RD43HATGPS_Radioenge)

Port of the Semtech SX1301 reference software (lora_gateway v5.0.1 + packet_forwarder v4.0.1) to the ESP32,
built on ESP-IDF following the esxp1302 port (web page, MQTT, app, three boards).
The full analysis of what changed is in doc/PORTE_ESP32.md.

### libloragw (lora_gateway v5.0.1 -> ESP-IDF)
- loragw_spi.c rewritten on the ESP-IDF spi_master driver: same lgw_spi_* API, 7-bit address + R/W bit,
  FPGA mux header when needed, bursts split in chunks; host and pins from main/CMakeLists.txt
  (SPI3_HOST on the ESP32, SPI2_HOST/IOMUX on the S3), 8 MHz by default (lgw_spi_speed_hz)
- loragw_gpio.c (new): lgw_reset() replaces reset_lgw.sh (RESET active high, optional POWER_EN)
- loragw_aux.c: wait_ms/wait_us with vTaskDelay + esp_rom_delay_us instead of clock_nanosleep
- loragw_hal.c: the three SX1301 firmwares (cal, arb, agc) are const arrays in flash; load_firmware() takes a
  const pointer and its read-back buffer is allocated on the heap; lgw_start() fails if a firmware load fails
- lgw_get_instcnt() (new): free-running SX1301 time emulated from esp_timer, resynchronised every 20 s by briefly
  clearing GPS_EN, because TIMESTAMP is latched on PPS when the GPS is enabled
- rx/tx packet counters as unsigned int (Xtensa: uint32_t is unsigned long), printf formats fixed
- gps code kept (NMEA/UBX parser), serial port opened with the ESP-IDF UART driver

### Packet forwarder
- parse_SX1301_configuration (SX1301_conf: clksrc, lorawan_public, radio_0/1 SX1257/SX1255, tx_lut_0..15,
  chan_multiSF_0..7, chan_Lora_std, chan_FSK, lbt_cfg) replaces the sx1302_hal parser; no debug/spectral-scan/
  temperature sections
- single TX path: one JIT queue, lgw_send(pkt), lgw_status(TX_STATUS)
- uplink stats from the SX1301 rx struct (rssi, snr, datarate bit mask); no fine timestamp, no per-channel RSSI
- GPS time sync with the PPS wired to the SX1301 (CONFIG_GW_GPS_PPS_SX1301, default y) using lgw_get_trigcnt()
- sx1301_wiring_diag: MISO/CS test, chip version 103 with both reset polarities and two SPI clocks
- status JSON and web page: no temperature sensor ("sem sensor")

### Project
- names: ESP32_SX1301, Soft AP "lorawan-gateway-sx1301", mDNS esp32-sx1301-xxxxxx, console ESP32_SX1301>,
  export _type "esp32_sx1301", Android app esp32_sx1301_app
- frequency plans (SX1301_conf): AU915 SB0, AU915 SB1 (default), US915, EU868 (SX1257) and CN470 (SX1255)
- three boards: esp32 (ESP32-WROOM-32U), esp32s3_n16r8 (ESP32-S3-WROOM-1U-N16R8),
  esp32s3_n32r16v (ESP32-S3-WROOM-2-N32R16V); GitHub Actions builds all three
- pinout: Raspberry Pi header, CS pin 24, RESET pin 11 on the RAK2245 (pin 26 on the Radioenge)
- documentation in pt-BR: README.md, doc/hardware/ (one guide per board), doc/PORTE_ESP32.md
- LICENSE.TXT includes the lora_gateway / packet_forwarder license
- builds with no warnings on ESP-IDF v5.5.1 for the three boards; not yet validated on hardware
