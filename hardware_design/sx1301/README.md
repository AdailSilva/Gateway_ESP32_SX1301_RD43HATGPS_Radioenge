# Projeto de referência SX1301 (Semtech)

O projeto de referência da Semtech para o SX1301 é a placa de demonstração **SX1301AP1CAS, 915 MHz, revisão e286V02b**. É o projeto que a Semtech chama de "PCB_E286" nos JSON do `lora_gateway`, e é a base da Radioenge LoRaWAN Gateway, da RAK2245/RAK831 e da IMST iC880A.

> O pacote (esquema, Gerber e BOM) não está nesta pasta porque a Semtech o distribui na própria página do produto, com cadastro. Se você baixar, coloque o arquivo aqui (`hardware_design/sx1301/`) para ficar junto do projeto.

| Item | Valor |
|---|---|
| Placa de referência | SX1301AP1CAS (demoboard), 915 MHz, rev. e286V02b |
| Concentrador | SX1301 (banda base digital, 8 canais LoRa + 1 LoRa de serviço + 1 FSK) |
| Rádios | 2 × SX1257 (rádio A e rádio B); o rádio B fornece o clock de 32 MHz (`clksrc` = 1) |
| Interface com o host | SPI (até 10 MHz; o firmware usa 8 MHz) + RESET ativo alto |
| PPS | entrada do SX1301 ligada ao GPS na própria placa (o `CONFIG_GW_GPS_PPS_SX1301=y` do firmware depende disso) |

## Onde está cada coisa no firmware

| Parâmetro do projeto de referência | Onde fica |
|---|---|
| `clksrc`, `rssi_offset` (−166 dB), `tx_notch_freq`, `tx_lut_0..15` | `main/packet_forwarder/global_conf.json/global_conf.*.json`, seção `SX1301_conf` |
| Firmwares do SX1301 (AGC, ARB, CAL) | embutidos na HAL portada (`main/libloragw/`) |
| Pulso de RESET (equivalente ao `reset_lgw.sh`) | `lgw_reset()` em `main/libloragw/loragw_gpio.c` |

A Radioenge não publica esses parâmetros no manual. Eles ficam no `global_conf_AU915.json` da imagem do cartão SD dela (`Radioenge_LoRaGW_V4.zip`, pasta `/opt/LoRa/packet_forwarder/lora_pkt_fwd/`). Se algum valor diferir do projeto de referência, prevalece o da Radioenge ([guia](../../doc/hardware/Radioenge_LoRaWAN_Gateway.md#1-conferência-do-firmware-para-esta-placa)).

## Links

- Página do SX1301 na Semtech (folha de dados e projetos de referência): <https://www.semtech.com/products/wireless-rf/lora-core/sx1301>
- Ficha da placa de referência (Würth Elektronik / Semtech): <https://www.we-online.com/icref/en/semtech/SX1301-SX1301-Reference-Board-SX1301AP1CAS-915MHz-Other>
- HAL original (`lora_gateway`, base do porte): <https://github.com/Lora-net/lora_gateway>
- *Packet forwarder* original: <https://github.com/Lora-net/packet_forwarder>
