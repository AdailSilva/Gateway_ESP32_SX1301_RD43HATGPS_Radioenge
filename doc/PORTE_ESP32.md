# Como o HAL da Semtech foi portado para o ESP32

Este documento explica **o que precisou mudar** para o código da Semtech, escrito para Linux (Raspberry Pi e similares), rodar num **ESP32 sem sistema operacional completo**. Ele tem duas partes:

1. **O caminho de referência:** o que o projeto [esxp1302](https://github.com/lora-gateway/esxp1302) mudou no [sx1302_hal v2.1.0](https://github.com/Lora-net/sx1302_hal) para rodar no ESP32. As mesmas técnicas foram usadas aqui.
2. **SX1301:** como as mesmas ideias foram aplicadas ao [lora_gateway v5.0.1](https://github.com/Lora-net/lora_gateway) e ao [packet_forwarder v4.0.1](https://github.com/Lora-net/packet_forwarder) para criar **este** projeto.

---

## 0. Por que o código original não roda direto no ESP32

No Raspberry Pi, o HAL da Semtech conta com o Linux para fazer o trabalho de baixo nível:

| O HAL usa no Linux | Para quê | Existe no ESP32? |
|---|---|---|
| `/dev/spidev0.0` + `ioctl(SPI_IOC_MESSAGE)` | falar SPI com o concentrador | **não**: o ESP-IDF tem o driver `spi_master` |
| `/dev/i2c-1` + `ioctl(I2C_RDWR)` | sensor de temperatura, DAC (SX1302) | **não**: driver `i2c` do ESP-IDF |
| `/dev/ttyS0` + `termios` | ler o GPS | **não**: driver `uart` do ESP-IDF |
| `/sys/class/gpio` (no `reset_lgw.sh`) | pulso de RESET antes de iniciar | **não há shell**: o firmware gera o pulso com `gpio_set_level()` |
| `clock_nanosleep()` | `wait_ms()` / `wait_us()` | **não**: `vTaskDelay()` e `esp_rom_delay_us()` |
| `pthread_create()` / `pthread_mutex_*` | threads `up`, `down`, `jit`, `gps`… | existe uma camada pthread, mas o padrão no ESP-IDF são **tarefas FreeRTOS** e **semáforos** |
| `fopen("global_conf.json")` | ler a configuração | **não há sistema de arquivos** por padrão: o JSON é **embutido no firmware** |
| `getaddrinfo()` + `connect()` em socket UDP | falar com o servidor | o lwIP tem sockets, mas o porte usa `sendto()` com o IP resolvido |
| `Makefile` + `library.cfg` → `inc/config.h` | build | o ESP-IDF usa **CMake**; o `config.h` passa a ser um arquivo fixo |
| `uint32_t` = `unsigned int` (ARM Linux 32 bits) | `printf("%u")`, ponteiros `uint32_t*` | no Xtensa/RISC-V do ESP-IDF, `uint32_t` = **`unsigned long`**: `%u` gera aviso e `unsigned int*` ≠ `uint32_t*` (erro no GCC 14) |

Também falta tudo o que no Pi vem do sistema: Wi-Fi, NTP, configuração persistente, interface de usuário. O porte acrescenta isso com Wi-Fi do ESP-IDF, SNTP, **NVS**, console serial e servidor web.

---

## 1. Referência: o que o esxp1302 mudou no sx1302_hal

### 1.1 Biblioteca `libloragw`

| Arquivo | Linux (sx1302_hal) | ESP32 (esxp1302) |
|---|---|---|
| `loragw_spi.c` | `open("/dev/spidev0.0")`, `ioctl` para modo, velocidade e transferências | `spi_bus_initialize()` + `spi_bus_add_device()`; transferências com `spi_device_polling_transmit()` e `spi_transaction_ext_t` (fase de comando = alvo do mux, fase de endereço = endereço de 16 bits). Assinaturas passam a receber `spi_device_handle_t*`. Os pinos vêm de `PIN_NUM_MISO/MOSI/CLK/CS` e o controlador de `SX1302_SPI_HOST` |
| `loragw_i2c.c` | `i2c_linuxdev_open/read/write` em `/dev/i2c-1` | `i2c_esp32_open/read/write` com o driver `i2c` do ESP-IDF; pinos `I2C_MASTER_SDA_IO/SCL_IO` |
| `loragw_stts751.c`, `loragw_ad5338r.c` | recebem o descritor do I2C | perdem o descritor, usam o I2C global |
| `loragw_gps.c` | `termios` em `/dev/ttyS0` | `uart_driver_install()` / `uart_read_bytes()`; `lgw_gps_enable(..., uart_port_t)` |
| `loragw_aux.c` | `clock_nanosleep()` | `vTaskDelay(ms / portTICK_PERIOD_MS)` (**atenção:** com o tick padrão de 100 Hz, `wait_ms(1..9)` vira espera **zero**) |
| `loragw_gpio.c` (**novo**) | — (o RESET é feito pelo `reset_lgw.sh`) | `lgw_reset()`: liga `POWER_EN` (se houver) e dá o pulso de 100 ms no `SX1302_RESET_PIN` |
| `loragw_hal.c` | abre o I2C, procura o STTS751 e **falha** se não achar; grava log em arquivo | abre o I2C do ESP32; sensor de temperatura **opcional** (só aviso); sem arquivo de log; `abs()` de `uint32_t` trocado por comparação explícita |
| `loragw_usb.c`, `sx1250_usb.c`, `sx1261_usb.c` | concentrador USB (Corecell USB) | mantidos só para compilar (sem USB no ESP32) |
| `loragw_sx1302_timestamp.c` | `uint32_t` | `unsigned int` (e correção da expansão do contador de 27 bits) |
| `config.h` | gerado pelo `Makefile` a partir de `library.cfg` | arquivo fixo no repositório |
| tipos | `uint32_t` em várias assinaturas | trocados por `unsigned int` (mesmo tamanho no ESP32) para evitar erros de ponteiro e de `printf` |

### 1.2 Packet forwarder (`lora_pkt_fwd.c`)

| Linux | ESP32 |
|---|---|
| `main()` com `getopt`, sinais (`SIGINT`) | `app_main()` → tarefa `pkt_fwd_main()`; sem sinais |
| `pthread_create()` para `thread_up/down/jit/gps/valid/spectral_scan` | `xTaskCreatePinnedToCore()` |
| `pthread_mutex_t` | `SemaphoreHandle_t` (`xSemaphoreCreateMutex`) |
| `global_conf.json` + `local_conf.json` em arquivo | JSON **embutido** em `global_json.h` (gerado por script) e lido com `json_parse_array_with_comments()` (função nova no `parson.c`) |
| servidor/porta/ID no JSON | também no **NVS**, editáveis no console e na página web |
| `getaddrinfo()` + `connect()` + `send()` | DNS do lwIP + `sendto()` |
| reset por script antes do programa | `lgw_reset()` antes do `lgw_start()` |
| — | Wi-Fi (Station/Soft AP), SNTP, console (`esp_console`), OLED SSD1306, LEDs e botões |

### 1.3 Build

`Makefile` → projeto **ESP-IDF** (`CMakeLists.txt` + componente `main`) e alternativa PlatformIO; o `run_me.sh` gera `webpage.h` e `global_json.h` e grava com `esptool`.

### 1.4 O que este projeto acrescentou sobre o esxp1302

MQTT/MQTTS no formato ChirpStack v4 (Protobuf), página web completa em pt-BR, GPS ligado/desligado em tempo real, mDNS, diagnóstico de fiação, três placas (ESP32-WROOM-32U, ESP32-S3-WROOM-1U-N16R8, ESP32-S3-WROOM-2-N32R16V), versão pelo Git, CI/Releases e app Android. Nada disso depende do concentrador.

---

## 2. SX1301: o que foi feito neste projeto

O ponto de partida foi o **mesmo** caminho do esxp1302, mas aplicado ao HAL do SX1301, que é bem menor (≈ 5,2 mil linhas de C, contra ≈ 14,3 mil do sx1302_hal) e **não tem** I2C, sensor de temperatura, SX1250, SX1261, USB nem timestamp fino.

### 2.1 Diferenças de hardware que mudam o porte

| | SX1302 (sx1302_hal) | SX1301 (lora_gateway) |
|---|---|---|
| Protocolo SPI | `[alvo do mux] [R/W + endereço de 15 bits] [dado]` | `[R/W + endereço de 7 bits] [dado]` (sem FPGA) ou `[alvo] [R/W + 7 bits] [dado]` (com FPGA). A paginação é por registrador (página no endereço 0) |
| Rádios | SX1250 (SPI próprio via SX1302) | **SX1257** (868/915 MHz) ou **SX1255** (433/470 MHz), configurados pelos registradores do SX1301 |
| Firmware interno | carregado pelo HAL (`arb`, `agc`) | **3 firmwares** de 8 KB (`cal`, `arb`, `agc`) carregados e **conferidos por leitura** em cada `lgw_start()` |
| Contador de tempo | registrador "instantâneo" + latch do PPS | só o registrador `TIMESTAMP`, que guarda o contador **no PPS** quando `GPS_EN = 1` |
| Sensor de temperatura | STTS751 (I2C) | **nenhum** no HAL |
| Tabela de ganho TX | uma por RF chain (`pwr_idx` no SX1250) | **uma só**, `tx_lut_0..15` com `pa_gain`, `mix_gain`, `dig_gain`, `dac_gain` |
| Modem de TX | — | **um só**, compartilhado pelas duas RF chains |
| LBT / spectral scan | SX1261 | só nas placas com **FPGA** + SX127x (referência Semtech) |
| EUI do chip | `lgw_get_eui()` | não existe: o EUI vem do MAC do ESP32 (+FFFE) ou da página |

### 2.2 `libloragw` (lora_gateway v5.0.1 → ESP-IDF)

| Arquivo | Situação | O que mudou |
|---|---|---|
| `loragw_spi.c` | **reescrito** (era `loragw_spi.native.c`) | Driver `spi_master`. **API original mantida** (`void *spi_target`, `spi_mux_mode`, `spi_mux_target`, endereço de 7 bits), então `loragw_reg.c`, `loragw_fpga.c` e `loragw_radio.c` continuam os originais. Mesmos quadros do Linux, byte a byte: 2 bytes (sem FPGA) ou 3 (com FPGA). Rajadas em pedaços de 1024 bytes, cada um com o comando de novo e CS liberado entre eles, como cada `ioctl` do Linux. 8 MHz (máximo do SX1301: 10 MHz). Pull-up fraco no MISO para o diagnóstico (0xFF = ninguém responde, 0x00 = linha presa em 0) |
| `loragw_aux.c` | **reescrito** | `wait_ms()` dorme os ticks inteiros com `vTaskDelay()` e completa o resto com `esp_rom_delay_us()`. No tick de 100 Hz do ESP-IDF, `wait_ms(1)`…`wait_ms(9)` agora esperam de verdade (no esxp1302 eram zero). Isso importa no `lgw_start()` do SX1301: reset dos rádios, travamento do PLL e calibração dependem dessas esperas. Também ganhou `wait_us()`, `timeout_start()` e `timeout_check()` |
| `loragw_gpio.c/h` | **novo** | `lgw_reset()`: o mesmo pulso do `lora_gateway/reset_lgw.sh` (RESET em 1 por 100 ms, depois 0 por 100 ms) e `POWER_EN` opcional. Pinos `SX1301_RESET_PIN` / `SX1301_POWER_EN_PIN` |
| `loragw_hal.c` | **ajustado** | **(1)** A verificação do firmware lia 8 KB para um vetor **na pilha** (`uint8_t fw_check[8192]`): agora é `malloc`. **(2)** Os três firmwares (`*.var`) passaram a `static const`: ficam na flash, e não ocupam 24 KB de RAM. **(3)** `lgw_start()` agora **confere** o retorno de `load_firmware()`: se a leitura de volta falhar (quase sempre fiação/SPI), ele para com erro. O original ignorava. **(4)** Mensagens `ERROR:` saem sempre no console (no original só com `DEBUG_HAL=1`). **(5)** `lgw_get_instcnt()` **novo** (ver 2.4). **(6)** `lgw_get_trigcnt(unsigned int*)` |
| `loragw_hal.h` | **ajustado** | Campos `uint32_t` de `lgw_pkt_rx_s` / `lgw_pkt_tx_s` passaram a `unsigned int` (mesmo tamanho), a mesma escolha do esxp1302, para o packet forwarder compartilhado compilar sem erro no GCC 14 |
| `loragw_reg.c` | original | Só as mensagens de erro passaram a sair sempre (`v0`/`v255` ajudam a achar fio solto) |
| `loragw_radio.c`, `loragw_fpga.c` | originais | — |
| `loragw_lbt.c` | original | Variável do contador trocada para `unsigned int` (tipo do `lgw_get_trigcnt`) |
| `loragw_gps.c/h` | **do porte esxp1302** | A parte de tempo (`lgw_gps_sync`, `lgw_cnt2utc`, `lgw_gps2cnt`…) é **idêntica** nos dois HALs. Foi usada a versão já portada (driver `uart`) |
| `loragw_i2c.c/h` | do porte esxp1302 | Só para o OLED opcional: o HAL do SX1301 não usa I2C |
| `config.h` | fixo | `LIBLORAGW_VERSION "5.0.1"` e os `DEBUG_*` |
| `main/CMakeLists.txt` | — | Os `printf` do HAL usam `%u` com `uint32_t`. No ESP32 o valor sai certo (32 bits), mas o GCC avisa e o ESP-IDF transforma o aviso em erro. Só nesses arquivos `-Wformat` fica como aviso, em vez de editar ~100 `printf` da Semtech |

### 2.3 Packet forwarder

A base é o forwarder do **esxp1302** (sx1302_hal), com o Wi-Fi, a web, o MQTT, o GPS, o console e a NVS deste projeto. As partes que falam com o concentrador foram trocadas pela lógica do **packet_forwarder v4.0.1** do SX1301:

| Parte | sx1302_hal (esxp1302) | SX1301 (este projeto) |
|---|---|---|
| Configuração | objeto `SX130x_conf`: `com_type`, `com_path`, `full_duplex`, `fine_timestamp`, `sx1261_conf`, `chan_multiSF_All`, `tx_gain_lut` por rádio | objeto **`SX1301_conf`** do v4: `lorawan_public`, `clksrc`, `antenna_gain`, `lbt_cfg`, `radio_0/1` (`type`, `freq`, `rssi_offset`, `tx_enable`, `tx_notch_freq`, `tx_freq_min/max`), `chan_multiSF_0..7`, `chan_Lora_std`, `chan_FSK`, **`tx_lut_0..15`**. Função `parse_SX1301_configuration()` portada do v4 |
| Chamadas do HAL | `lgw_board_setconf(&c)`, `lgw_rxrf_setconf(i, &c)`, `lgw_txgain_setconf(rf, &lut)`, `lgw_send(&pkt)`, `lgw_status(rf, TX_STATUS, &s)` | `lgw_board_setconf(c)`, `lgw_rxrf_setconf(i, c)`, `lgw_txgain_setconf(&lut)`, **`lgw_send(pkt)`**, **`lgw_status(TX_STATUS, &s)`** |
| Pacote recebido (`rxpk`) | `rssic`, `rssis`, `freq_offset`, `modem_id`, `ftime` | **`rssi`** (canal). Saem do JSON: `rssis`, `foff`, `mid`, `ftime` |
| SF | `datarate` = número do SF (5..12) | `datarate` = **máscara** (`DR_LORA_SF7 = 0x02` … `SF12 = 0x40`). A estatística por SF foi corrigida. Antes, o índice `datarate - 5` estouraria o vetor. SF5/SF6 não existem no SX1301 |
| Filas JIT | uma por RF chain | **uma só** (`jit_queue[0]`): o SX1301 tem **um** modem de TX para as duas RF chains, como no v4 |
| Hora do concentrador | `lgw_get_instcnt()` (registrador) | `lgw_get_instcnt()` **emulado** (2.4) |
| Temperatura | STTS751, `"temp"` no `stat` | não existe; o status mostra "sem sensor" |
| Spectral scan, LBT com SX1261, debug `ref_payload` | sim | **removidos** (LBT só pelo FPGA, via `lbt_cfg`) |
| EUI do chip | `lgw_get_eui()` | não existe; o EUI do gateway é o MAC do Wi-Fi + FFFE, ou o valor da página |
| Diagnóstico de fiação | lê o registrador `0x5606` (esperado 0x10) e o SX1262 | lê o registrador **1** do SX1301 (esperado **103 = 0x67**) pelo SPI e por bit-bang, com as duas polaridades de reset e dois clocks |
| GPS | a sincronização de tempo só existia com `GPS_PPS_GPIO` | nova opção **`GW_GPS_PPS_SX1301`** (padrão: ligada): em RAK2245, RAK831 + GPS e iC880A + GPS, o PPS chega ao **próprio SX1301** |

### 2.4 Hora "instantânea" do SX1301 (`lgw_get_instcnt`)

O JIT precisa saber **agora** o valor do contador de 1 MHz do concentrador para programar cada downlink. O SX1302 tem um registrador para isso. O SX1301 só tem o `TIMESTAMP`, que, com `GPS_EN = 1`, guarda o valor do contador **no último PPS**.

O packet forwarder v4 resolveu isso com o `timersync.c`: a cada 60 s ele desliga o `GPS_EN`, lê o contador "livre", liga de novo e guarda a diferença em relação ao relógio do Linux. Este porte faz o mesmo dentro do HAL:

1. `lgw_get_instcnt()` lê `esp_timer_get_time()` (64 bits, 1 µs).
2. A cada **20 s** (`LGW_INSTCNT_SYNC_S`), ou logo depois de `lgw_start()`, ele faz `GPS_EN = 0`, lê `TIMESTAMP` entre duas leituras do `esp_timer`, devolve o `GPS_EN` anterior e guarda `offset = contador − esp_timer` (módulo 2³²).
3. Valor devolvido: `(uint32_t)esp_timer + offset`. A conta em 32 bits trata a volta do contador sozinha.

Com 20 ppm de diferença entre os cristais, o erro máximo entre duas sincronizações é de 0,4 ms. A margem do JIT é de 40 ms.

### 2.5 Planos de frequência embutidos (`global_conf.json/*.json`)

Todos no formato `SX1301_conf`, com rádios **SX1257**, `clksrc: 1` e a tabela TX de 16 níveis do `global_conf.json` de referência da Semtech (-6 a 27 dBm):

| Arquivo | Plano | Rádios (radio_0 / radio_1) | TX |
|---|---|---|---|
| `global_conf.au915_sb0.json` | AU915 ch 0–7 + 64 | 915,6 / 916,3 MHz | 915–928 MHz |
| `global_conf.au915_sb1.json` (padrão) | AU915 ch 8–15 + 65 | 917,2 / 917,9 MHz | 915–928 MHz |
| `global_conf.us915.json` | US915 ch 8–15 + 65 | 904,3 / 905,0 MHz | 902–928 MHz |
| `global_conf.eu868.json` | EU868, como o `global_conf.json` da Semtech | 867,5 / 868,5 MHz | 863–870 MHz |
| `global_conf.cn490.json` | CN470 ch 0–7 | 470,6 / 471,4 MHz, **SX1255** | 470–510 MHz |

Limites do SX1301 conferidos (`lgw_rxif_setconf`): canal de 125 kHz até ±400 kHz do centro do rádio; canal de 500 kHz até ±300 kHz. O CN470 só funciona em placas de 470 MHz (SX1255).

### 2.6 O que **não** mudou

- O protocolo UDP Semtech (`PROTOCOL.md`), o JIT (`jitqueue.c`), o MQTT/ChirpStack (`mqtt_gw.c`, `cs_codec.c`), o servidor web, o console, o NVS, o GPS em tempo real, o mDNS e as três placas ESP32.
- `jitqueue.c` ganhou só uma correção: o mutex da fila era recriado a cada `jit_queue_init()`, que é chamado mais de uma vez. Agora é criado uma vez só.

### 2.7 O que ainda precisa ser validado em bancada

- **Radioenge LoRaWAN Gateway** (placa principal): RESET no pino 26 do conector, 5 V / 2 A, e os parâmetros `clksrc`, `rssi_offset`, `tx_notch_freq` e `tx_lut_*` comparados com o `global_conf_AU915.json` da imagem do cartão SD da Radioenge. Roteiro em [`hardware/Radioenge_LoRaWAN_Gateway.md`](hardware/Radioenge_LoRaWAN_Gateway.md#6-primeira-ligação-o-que-conferir).
- Recepção nos 8+2 canais e o RSSI (`rssi_offset` -166 dB vale para as placas de referência; RAK2245/iC880A usam o mesmo, mas convém calibrar).
- Potência real de TX com a tabela `tx_lut_*` da sua placa (a do fabricante pode ser diferente).
- `clksrc`: 1 na maioria (RAK831, RAK2245, iC880A, RHF0M301). Se o `lgw_start()` falhar na calibração, teste 0.
- Sincronização GPS/PPS e class B (beacons). Na Radioenge RD43HATGPS, confirmar que o *TimePulse* do GPS chega ao SX1301 dentro da placa (ele não sai no conector RPi).
