#!/usr/bin/env python3
"""Gera os diagramas de ligação ESP32 ↔ Radioenge LoRaWAN Gateway (SX1301),
no estilo visual dos demais SVGs do projeto.

uso: python3 scripts/gen_wiring_radioenge.py doc/images
PNG em alta resolução: renderizar os SVGs com deviceScaleFactor 3 (Chromium/Playwright);
os radioenge_header_cima_baixo_*.svg (1800 px) com deviceScaleFactor 2 (PNG de 3600 px).

Por placa (esp32, esp32s3_n16r8, esp32s3_n32r16v) saem:
  wiring_<placa>.svg, radioenge_header_<placa>.svg e radioenge_header_cima_baixo_<placa>.svg
(os wiring_* mantêm os nomes antigos: wiring_esp32_wroom32u, wiring_esp32s3_wroom1u_n16r8, wiring_esp32s3_wroom2).
"""
import os, sys

SANS = "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
C = dict(spi="#2563eb", ctl="#ea580c", i2c="#16a34a", gps="#9333ea",
         pwr="#dc2626", gnd="#1f2937", rpi="#6b7280")

DEFS = ('<defs><pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        '<rect width="6" height="6" fill="#d1d5db"/><line x1="0" y1="0" x2="0" y2="6" stroke="#9ca3af" stroke-width="3"/></pattern>'
        '<filter id="sh" x="-5%" y="-5%" width="110%" height="115%"><feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0f172a" flood-opacity="0.18"/></filter>'
        '<linearGradient id="pcb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1e293b"/><stop offset="1" stop-color="#0f172a"/></linearGradient>'
        '<linearGradient id="pcbS3" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1e3a5f"/><stop offset="1" stop-color="#0b2540"/></linearGradient>'
        '<linearGradient id="hat" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#065f46"/><stop offset="1" stop-color="#064e3b"/></linearGradient>'
        '<linearGradient id="rdg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1e3a8a"/><stop offset="1" stop-color="#172554"/></linearGradient>'
        '</defs>')


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def T(x, y, s, size=13, fill="#0f172a", anchor="middle", weight="normal", font=SANS):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{font}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" >{esc(s)}</text>')


def pill(cx, y, s, color, size=11.5, k=6.45, h=18, anchor="middle"):
    w = len(s) * k + 16
    x = cx - w / 2 if anchor == "middle" else (cx if anchor == "start" else cx - w)
    tx = x + w / 2
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="{h/2:.1f}" fill="{color}"/>'
            + T(tx, y + h * 0.725, s, size, "#fff", "middle", "600"))


# --------------------------------------------------------------------------
# 1) ESP32 ↔ Radioenge (um por placa)
# --------------------------------------------------------------------------
def wiring(board):
    sections = [
        ("SPI", C["spi"], [
            ("MOSI", board["mosi"], "19 · MOSI", ">"),
            ("MISO", board["miso"], "21 · MISO", "<"),
            ("SCLK", board["sclk"], "23 · SCLK", ">"),
            ("CS SX1301", board["cs"], "24 · CE0", ">"),
        ]),
        ("CONTROLE", C["ctl"], [
            ("RESET SX1301 (ativo alto)", board["rst"], "26 · RESET", ">"),
        ]),
        ("GPS (OPCIONAL · RD43HATGPS)", C["gps"], [
            ("TX → GPS RXD", board["gtx"], "8 · TXD", ">", True),
            ("RX ← GPS TXD", board["grx"], "10 · RXD", "<", True),
        ]),
        ("ENERGIA", C["pwr"], [
            ("5 V", board["v5"], "2/4 · 5V", ">"),
            ("GND", "GND", "6 · GND", None),
        ]),
    ]
    out = []
    y = 194
    rows_y = []
    for title, color, rows in sections:
        out.append(T(620, y, title, 12.5, color, "middle", "700"))
        ry = y + 36
        for r in rows:
            label, gpio, hat, d = r[:4]
            dashed = len(r) > 4
            col = C["gnd"] if label == "GND" else color
            out.append(f'<circle cx="374" cy="{ry}" r="6" fill="{col}" stroke="#fff" stroke-width="2"/>')
            out.append(f'<circle cx="866" cy="{ry}" r="6" fill="{col}" stroke="#fff" stroke-width="2"/>')
            dash = ' stroke-dasharray="8 6"' if dashed else ""
            out.append(f'<line x1="380" y1="{ry}" x2="860" y2="{ry}" stroke="{col}" stroke-width="4" stroke-linecap="round"{dash}/>')
            if d == ">":
                out.append(f'<path d="M660.0 {ry} l-12 -7 v14 z" fill="{col}"/>')
            elif d == "<":
                out.append(f'<path d="M580.0 {ry} l12 -7 v14 z" fill="{col}"/>')
            out.append(pill(620, ry - 25, label, col))
            out.append(T(360, ry + 4.5, gpio, 13.5, "#fff", "end", "700", MONO))
            out.append(T(880, ry + 4.5, hat, 13, "#fff", "start", "700", MONO))
            rows_y.append(ry)
            ry += 36
        y = ry - 36 + 44
    last = rows_y[-1]
    bh = last + 20 - 120
    H = last + 20 + 128
    head = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1240" height="{H}" viewBox="0 0 1240 {H}" role="img" aria-label="Ligação {esc(board["title"])} ↔ Radioenge LoRaWAN Gateway">',
        f'<title>Ligação {esc(board["title"])} ↔ Radioenge LoRaWAN Gateway (SX1301)</title>',
        DEFS,
        f'<rect x="1" y="1" width="1238" height="{H-2}" rx="14" fill="#ffffff" stroke="#e2e8f0" stroke-width="2"/>',
        T(620, 44, f'{board["title"]}  ↔  Radioenge LoRaWAN Gateway', 24, "#0f172a", "middle", "700"),
        T(620, 72, "Fios SPI curtos (< 15 cm) e de mesmo comprimento · GND comum · lógica de 3,3 V nos dois lados · fonte 5 V / 2 A", 13.5, "#475569"),
        f'<rect x="90" y="120" width="300" height="{bh}" rx="14" fill="url(#{board["grad"]})" filter="url(#sh)"/>',
        f'<rect x="850" y="120" width="300" height="{bh}" rx="14" fill="url(#rdg)" filter="url(#sh)"/>',
        T(240, 150, board["name"], 15, "#fff", "middle", "700"),
        T(240, 170, board["spi"], 12, "#cbd5e1"),
        T(1000, 150, "Radioenge RD43HAT / RD43HATGPS", 15, "#fff", "middle", "700"),
        T(1000, 170, "SX1301 + 2× SX1257 · conector RPi 40 pinos", 12, "#bfdbfe"),
    ]
    b = last + 20
    foot = [
        T(240, b + 40, board["antenna"], 13, "#334155", "middle", "600"),
        T(240, b + 62, "Não ligar: 3V3 do conector (pinos 1 e 17)", 12.5, "#b45309", "middle", "700"),
        T(1000, b + 40, "Antena LoRa 902–928 MHz (SMA, até 6 dBi)", 13, "#334155", "middle", "600"),
        T(1000, b + 62, "Nunca ligar sem antena no conector LoRa!", 12.5, "#dc2626", "middle", "700"),
        T(620, b + 96, f'RAK2245: o mesmo fio de RESET vai ao pino 11 · OLED SSD1306 opcional só no ESP32 (SDA {board["sda"]} · SCL {board["scl"]})', 12.5, "#475569"),
    ]
    return "\n".join(head + out + foot) + "\n</svg>\n"


BOARDS = {
    "wiring_esp32_wroom32u.svg": dict(
        title="ESP32-WROOM-32U DevKit", name="ESP32-WROOM-32U DevKit", grad="pcb",
        spi="VSPI · SPI3_HOST · BOARD=esp32", mosi="GPIO23", miso="GPIO19", sclk="GPIO18",
        cs="GPIO5", rst="GPIO4", gtx="GPIO17", grx="GPIO16", v5="5V/VIN", sda="GPIO21", scl="GPIO22",
        antenna="Antena Wi-Fi externa (u.FL)"),
    "wiring_esp32s3_wroom1u_n16r8.svg": dict(
        title="ESP32-S3-WROOM-1U (N16R8) DevKit", name="ESP32-S3-WROOM-1U", grad="pcbS3",
        spi="FSPI · SPI2_HOST · BOARD=esp32s3_n16r8", mosi="GPIO11", miso="GPIO13", sclk="GPIO12",
        cs="GPIO10", rst="GPIO6", gtx="GPIO17", grx="GPIO18", v5="5V", sda="GPIO4", scl="GPIO5",
        antenna="Antena Wi-Fi externa (conector u.FL)"),
    "wiring_esp32s3_wroom2.svg": dict(
        title="ESP32-S3-WROOM-2 (N32R16V) DevKit", name="ESP32-S3-WROOM-2", grad="pcbS3",
        spi="FSPI · SPI2_HOST · BOARD=esp32s3_n32r16v", mosi="GPIO11", miso="GPIO13", sclk="GPIO12",
        cs="GPIO10", rst="GPIO6", gtx="GPIO17", grx="GPIO18", v5="5V", sda="GPIO4", scl="GPIO5",
        antenna="Antena de PCB (deixar fora da caixa)"),
}


# --------------------------------------------------------------------------
# 2) Conector de 40 pinos da Radioenge com os GPIOs de cada placa
# --------------------------------------------------------------------------
BCM = {1: "3V3", 2: "5V", 3: "GPIO2", 4: "5V", 5: "GPIO3", 6: "GND", 7: "GPIO4", 8: "GPIO14", 9: "GND",
       10: "GPIO15", 11: "GPIO17", 12: "GPIO18", 13: "GPIO27", 14: "GND", 15: "GPIO22", 16: "GPIO23",
       17: "3V3", 18: "GPIO24", 19: "GPIO10", 20: "GND", 21: "GPIO9", 22: "GPIO25", 23: "GPIO11",
       24: "GPIO8", 25: "GND", 26: "GPIO7", 27: "ID_SD", 28: "ID_SC", 29: "GPIO5", 30: "GND", 31: "GPIO6",
       32: "GPIO12", 33: "GPIO13", 34: "GND", 35: "GPIO19", 36: "GPIO16", 37: "GPIO26", 38: "GPIO20",
       39: "GND", 40: "GPIO21"}
# pino: (função, cor, gpio S3, gpio ESP32)
USED = {
    2: ("5V", C["pwr"], "5V", "5V/VIN"),
    4: ("5V (alt.)", C["pwr"], "—", "—"),
    6: ("GND", C["gnd"], "GND", "GND"),
    8: ("GPS RXD", C["gps"], "GPIO17", "GPIO17"),
    10: ("GPS TXD", C["gps"], "GPIO18", "GPIO16"),
    19: ("MOSI", C["spi"], "GPIO11", "GPIO23"),
    21: ("MISO", C["spi"], "GPIO13", "GPIO19"),
    23: ("SCLK", C["spi"], "GPIO12", "GPIO18"),
    24: ("CS SX1301", C["spi"], "GPIO10", "GPIO5"),
    26: ("RESET SX1301", C["ctl"], "GPIO6", "GPIO4"),
}
NOTE = {11: "RESET da RAK2245 — não usar", 3: "I2C (não usado)", 5: "I2C (não usado)"}


# placa -> (título, nome curto da coluna, índice em USED: 2 = S3, 3 = ESP32)
HDR_BOARDS = {
    "esp32": ("ESP32-WROOM-32U DevKit", "ESP32 (esp32)", 3),
    "esp32s3_n16r8": ("ESP32-S3-WROOM-1U-N16R8 DevKit", "ESP32-S3 (n16r8)", 2),
    "esp32s3_n32r16v": ("ESP32-S3-WROOM-2-N32R16V DevKit", "ESP32-S3 (n32r16v)", 2),
}


def header(board=None):
    """board=None: as duas famílias lado a lado; board="esp32"/"esp32s3_n16r8"/...: só aquela placa."""
    H = 920
    hb = HDR_BOARDS.get(board)
    sub = (f"{hb[0]} · SX1301 + 2× SX1257 · RD43HAT / RD43HATGPS · pino 1 = quadrado (3V3)" if hb else
           "SX1301 + 2× SX1257 · RD43HAT / RD43HATGPS · padrão Raspberry Pi · pino 1 = quadrado (3V3)")
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1240" height="{H}" viewBox="0 0 1240 {H}" role="img" aria-label="Radioenge LoRaWAN Gateway — conector de 40 pinos">',
         f'<title>Radioenge LoRaWAN Gateway — conector de 40 pinos com os GPIOs do {hb[0] if hb else "ESP32"}</title>', DEFS,
         f'<rect x="1" y="1" width="1238" height="{H-2}" rx="14" fill="#ffffff" stroke="#e2e8f0" stroke-width="2"/>',
         T(620, 44, "Radioenge LoRaWAN Gateway (SPI) — conector de 40 pinos" + (f" · {hb[0].replace(' DevKit', '')}" if hb else ""),
           22 if hb else 24, "#0f172a", "middle", "700"),
         T(620, 72, sub, 14, "#475569")]
    if hb:
        heads = [(210, hb[1], "middle"), (1030, hb[1], "middle"), (530, "Função", "end"), (710, "Função", "start")]
    else:
        heads = [(160, "ESP32", "middle"), (250, "ESP32-S3", "middle"), (990, "ESP32-S3", "middle"),
                 (1080, "ESP32", "middle"), (530, "Função", "end"), (710, "Função", "start")]
    for x, s, a in heads:
        o.append(T(x, 120, s, 13, "#0f172a", a, "700"))
    o.append('<rect x="540.0" y="128" width="160" height="576" rx="10" fill="url(#rdg)" filter="url(#sh)"/>')
    o.append('<rect x="560.0" y="138" width="120" height="556" rx="4" fill="#111827"/>')
    for row in range(20):
        cy = 152 + row * 28
        for side, pin in (("L", 2 * row + 1), ("R", 2 * row + 2)):
            cx = 592.0 if side == "L" else 648.0
            u = USED.get(pin)
            if pin in (1, 17):
                fill = "#fde68a"
            elif u:
                fill = u[1]
            elif BCM[pin] == "GND":
                fill = "#4b5563"
            else:
                fill = "#6b7280"
            if pin == 1:
                o.append(f'<rect x="{cx-9:.1f}" y="{cy-9}" width="18" height="18" rx="2" fill="{fill}" stroke="#fbbf24" stroke-width="2"/>')
            else:
                o.append(f'<circle cx="{cx}" cy="{cy}" r="9" fill="{fill}" stroke="#fbbf24" stroke-width="2"/>')
            o.append(T(cx, cy + 3.5, str(pin), 9.5, "#fff" if pin not in (1, 17) else "#92400e", "middle", "700", MONO))
            fx, anc = (530.0, "end") if side == "L" else (710.0, "start")
            s3x, e32x = (250, 160) if side == "L" else (990, 1080)
            if pin in (1, 17):
                o.append(T(fx, cy + 4.5, "3V3 — NÃO conectar", 12, "#b45309", anc, "700"))
            elif u:
                func, col, s3, e32 = u
                o.append(pill(fx, cy - 10, func, col, 12, 6.72, 20, anc))
                if hb:
                    g = u[hb[2]]
                    o.append(T(210 if side == "L" else 1030, cy + 4.5, g, 13.5, col, "middle", "700", MONO))
                else:
                    o.append(T(s3x, cy + 4.5, s3, 12.5, col, "middle", "700", MONO))
                    o.append(T(e32x, cy + 4.5, e32, 12.5, col, "middle", "700", MONO))
            else:
                o.append(T(fx, cy + 4.5, BCM[pin], 11.5, "#94a3b8", anc, "normal", MONO))
                if pin in NOTE:
                    nx = 330 if side == "L" else 900
                    o.append(T(nx, cy + 4.5, NOTE[pin], 11.5, "#b45309" if pin == 11 else "#94a3b8", "middle", "600"))
    o.append(T(70, 750, "Legenda", 13, "#334155", "start", "700"))
    leg = [(70, 764, C["spi"], "SPI (SX1301)"), (400, 764, C["ctl"], "Controle (RESET ativo alto, pino 26)"),
           (730, 764, C["gps"], "UART GPS (opcional, só RD43HATGPS)"), (70, 788, C["pwr"], "Alimentação 5 V (4,6–5,5 V)"),
           (400, 788, C["gnd"], "GND"), (730, 788, "#fde68a", "3V3 gerado na placa: não ligar")]
    for x, y, col, s in leg:
        o.append(f'<rect x="{x}" y="{y}" width="26" height="16" rx="8" fill="{col}"/>')
        o.append(T(x + 34, y + 12.5, s, 12.5, "#334155", "start"))
    o.append(T(70, 836, "Os nomes GPIOxx em cinza são numeração do Raspberry Pi (BCM), não são GPIOs do ESP32."
               + ("" if hb else " ESP32-S3 = N16R8 e N32R16V (mesmos fios)."), 12.5, "#334155", "start"))
    o.append(T(70, 858, "Única diferença para a RAK2245: o RESET vai ao pino 26 (BCM GPIO7, “Reset - Chip Selection” no manual), não ao pino 11.", 12.5, "#334155", "start"))
    o.append(T(70, 880, "Fonte: Tabelas 8 e 9 do Manual de Técnico do LoRaWAN Gateway Radioenge (rev. jul/2023).", 12.5, "#64748b", "start"))
    return "\n".join(o) + "\n</svg>\n"


# --------------------------------------------------------------------------
# 3) Conector de 14 vias do módulo GWLORA (ligação direta, sem o shield RPi)
# --------------------------------------------------------------------------
MOD = [  # pino, função, cor, ESP32, S3, sentido
    (1, "GND", C["gnd"], "GND", "GND", ""),
    (2, "GND", C["gnd"], "GND", "GND", ""),
    (3, "+5VCC", C["pwr"], "5V/VIN", "5V", "→"),
    (4, "+5VCC", C["pwr"], "5V/VIN", "5V", "→"),
    (5, "RESET", C["ctl"], "GPIO4", "GPIO6", "→"),
    (6, "SCK", C["spi"], "GPIO18", "GPIO12", "→"),
    (7, "MISO", C["spi"], "GPIO19", "GPIO13", "←"),
    (8, "MOSI", C["spi"], "GPIO23", "GPIO11", "→"),
    (9, "CSN", C["spi"], "GPIO5", "GPIO10", "→"),
    (10, "NC", "#9ca3af", "—", "—", ""),
    (11, "TimePulse (PPS)", "#9ca3af", "não ligar", "não ligar", ""),
    (12, "GPSRESET", "#9ca3af", "não ligar", "não ligar", ""),
    (13, "GPSRXD", C["gps"], "GPIO17 (TX)", "GPIO17 (TX)", "→"),
    (14, "GPSTXD", C["gps"], "GPIO16 (RX)", "GPIO18 (RX)", "←"),
]


def module14():
    H = 790
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1240" height="{H}" viewBox="0 0 1240 {H}" role="img" aria-label="Módulo GWLORA da Radioenge — conector de 14 vias">',
         '<title>Radioenge GWLORA v1 — conector de 14 vias com os GPIOs do ESP32</title>', DEFS,
         f'<rect x="1" y="1" width="1238" height="{H-2}" rx="14" fill="#ffffff" stroke="#e2e8f0" stroke-width="2"/>',
         T(620, 44, "Módulo Radioenge GWLORA v1 — ligação direta pelo conector de 14 vias", 24, "#0f172a", "middle", "700"),
         T(620, 72, "Sem o shield de 40 pinos · passo de 2,54 mm · Tabela 7 / Figura 3 do manual da Radioenge", 14, "#475569")]
    # módulo
    o.append('<rect x="80" y="110" width="1080" height="200" rx="14" fill="url(#rdg)" filter="url(#sh)"/>')
    o.append(T(130, 150, "GWLORA v1", 14, "#bfdbfe", "start", "700", MONO))
    o.append(T(130, 172, "SX1301 + 2× SX1257 · GPS u-blox (RD43HATGPS)", 12.5, "#cbd5e1", "start"))
    o.append(T(1110, 150, "RF (SMA)  ·  GPS (SMA)", 12.5, "#cbd5e1", "end", "600"))
    o.append('<rect x="210" y="246" width="820" height="44" rx="6" fill="#111827"/>')
    x0, dx = 250, 57
    for i, (pin, func, col, e32, s3, d) in enumerate(MOD):
        cx = x0 + i * dx
        o.append(f'<circle cx="{cx}" cy="268" r="12" fill="{col}" stroke="#fbbf24" stroke-width="2.5"/>')
        o.append(T(cx, 272.5, str(pin), 11, "#fff", "middle", "700", MONO))
    # tabela
    o.append(T(620, 350, "Pino do módulo → GPIO", 13, "#0f172a", "middle", "700"))
    cols = [(140, "Pino", "middle"), (330, "Função no módulo", "middle"), (520, "Sentido", "middle"),
            (720, "ESP32 (esp32)", "middle"), (960, "ESP32-S3 (n16r8 / n32r16v)", "middle")]
    for x, s, a in cols:
        o.append(T(x, 380, s, 12.5, "#475569", a, "700"))
    y = 404
    for i, (pin, func, col, e32, s3, d) in enumerate(MOD):
        if i % 2 == 0:
            o.append(f'<rect x="80" y="{y-16}" width="1080" height="22" rx="4" fill="#f1f5f9"/>')
        o.append(f'<circle cx="140" cy="{y-5}" r="9" fill="{col}"/>')
        o.append(T(140, y - 1.5, str(pin), 9.5, "#fff", "middle", "700", MONO))
        o.append(T(330, y, func, 12.5, col if col != "#9ca3af" else "#64748b", "middle", "700"))
        o.append(T(520, y, {"→": "ESP32 → módulo", "←": "módulo → ESP32"}.get(d, "—"), 12, "#64748b"))
        gc = col if col != "#9ca3af" else "#94a3b8"
        o.append(T(720, y, e32, 12.5, gc, "middle", "700", MONO))
        o.append(T(960, y, s3, 12.5, gc, "middle", "700", MONO))
        y += 22
    o.append(T(80, y + 22, "Os pinos 1/2 (GND) e 3/4 (+5 V) são duplicados: ligue os dois de cada par. O módulo gera os 3,3 V; não há pino de 3V3 neste conector.", 12.5, "#334155", "start"))
    o.append(T(80, y + 44, "TimePulse (11) e GPSRESET (12) não vão ao conector RPi do shield; o firmware espera o PPS já dentro da placa (CONFIG_GW_GPS_PPS_SX1301=y).", 12.5, "#334155", "start"))
    return "\n".join(o) + "\n</svg>\n"


# --------------------------------------------------------------------------
# 4) Conector de 40 pinos visto de CIMA e de BAIXO (os jumpers entram por baixo)
# --------------------------------------------------------------------------
# pino: (sinal, cor, gpio ESP32, gpio S3, sentido) · sentido ">" = ESP32 -> shield, "<" = shield -> ESP32
TB_USED = {
    1: ("3V3 · NÃO ligar", "#e0a800", None, None, ""), 17: ("3V3 · NÃO ligar", "#e0a800", None, None, ""),
    2: ("5V", C["pwr"], "5V/VIN", "5V", ">"), 4: ("5V (alt.)", C["pwr"], None, None, ""),
    6: ("GND", C["gnd"], "GND", "GND", ">"),
    8: ("GPS RXD", C["gps"], "GPIO17", "GPIO17", ">"), 10: ("GPS TXD", C["gps"], "GPIO16", "GPIO18", "<"),
    19: ("MOSI", C["spi"], "GPIO23", "GPIO11", ">"), 21: ("MISO", C["spi"], "GPIO19", "GPIO13", "<"),
    23: ("SCLK", C["spi"], "GPIO18", "GPIO12", ">"), 24: ("CS", C["spi"], "GPIO5", "GPIO10", ">"),
    26: ("RESET", C["ctl"], "GPIO4", "GPIO6", ">"),
}
for _g in (9, 14, 20, 25, 30, 34, 39):
    TB_USED[_g] = ("GND", C["gnd"], None, None, "")
TB_LIGHT = {"#e0a800": "#fde68a", C["pwr"]: "#fecaca", C["gnd"]: "#ffffff", C["gps"]: "#e9d5ff",
            C["spi"]: "#bfdbfe", C["ctl"]: "#fed7aa"}


TB_FAM = {
    "esp32": (False, "ESP32-WROOM-32U (esp32)"),
    "esp32s3": (True, "ESP32-S3 (n16r8 / n32r16v)"),
    "esp32s3_n16r8": (True, "ESP32-S3-WROOM-1U-N16R8 (esp32s3_n16r8)"),
    "esp32s3_n32r16v": (True, "ESP32-S3-WROOM-2-N32R16V (esp32s3_n32r16v)"),
}


def header_top_bottom(board="esp32"):
    W, H, top, pitch = 1800, 1340, 250, 42
    s3, fam = TB_FAM[board]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
         f'aria-label="Radioenge LoRaWAN Gateway — conector de 40 pinos visto de cima e de baixo">',
         f'<title>Radioenge LoRaWAN Gateway — conector de 40 pinos visto de cima e de baixo ({fam})</title>',
         f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="#ffffff" stroke="#e2e8f0" stroke-width="2"/>',
         T(900, 60, "Radioenge LoRaWAN Gateway · conector de 40 pinos", 38, "#0f172a", "middle", "700"),
         T(900, 102, f"A mesma placa vista por cima e por baixo: as fileiras trocam de lado. Os jumpers entram por baixo. GPIOs: {fam}",
           21, "#475569")]

    def panel(ox, mirror):
        bx0, bx1 = (ox + 40, ox + 560) if not mirror else (ox + 300, ox + 820)
        o.append(T(ox + 430, 165, "Vista de BAIXO" if mirror else "Vista de CIMA", 28, "#0f172a", "middle", "700"))
        o.append(T(ox + 430, 198, "placa virada, conector fêmea para você (onde entram os jumpers)" if mirror
                   else "lado dos componentes, como na Figura 2 do manual", 19, "#64748b"))
        o.append(f'<rect x="{bx0}" y="{top-30}" width="{bx1-bx0}" height="{20*pitch+60}" rx="18" '
                 f'fill="{"#14532d" if mirror else "#166534"}"/>')
        for fx, lab in ((0.12, "SMA LoRa"), (0.32, "SMA GPS")):
            x = bx0 + (bx1 - bx0) * (1 - fx if mirror else fx)
            o.append(f'<circle cx="{x:.1f}" cy="{top+8}" r="20" fill="#d4d4d8" stroke="#71717a" stroke-width="3"/>'
                     f'<circle cx="{x:.1f}" cy="{top+8}" r="7" fill="#a1a1aa"/>')
            o.append(T(x, top + 50, lab, 16, "#dcfce7"))
        mx = (bx0 + bx1) / 2 + (60 if mirror else -60)
        my = top + 20 * pitch / 2
        o.append(f'<text x="{mx:.1f}" y="{my:.1f}" font-family="{SANS}" font-size="22" fill="#bbf7d0" text-anchor="middle" '
                 f'transform="rotate(-90 {mx:.1f} {my:.1f})">{"lado de baixo (solda)" if mirror else "lado dos componentes"}</text>')
        xe, xo = (bx0 + 40, bx0 + 90) if mirror else (bx1 - 40, bx1 - 90)
        o.append(f'<rect x="{min(xo, xe)-24}" y="{top-6}" width="98" height="{20*pitch+12}" rx="8" fill="#0b0f19"/>')
        for r in range(20):
            y = top + 16 + r * pitch
            for n, x in ((2 * r + 1, xo), (2 * r + 2, xe)):
                sig, col, g32, gs3, d = TB_USED.get(n, ("", "#9ca3af", None, None, ""))
                if n == 1:
                    o.append(f'<rect x="{x-15}" y="{y-15}" width="30" height="30" rx="4" fill="{col}" stroke="#fde68a" stroke-width="3"/>')
                else:
                    o.append(f'<circle cx="{x}" cy="{y}" r="15" fill="{col}" stroke="#facc15" stroke-width="2.5"/>')
                o.append(T(x, y + 5, str(n), 13, "#111" if col == "#e0a800" else "#fff", "middle", "700"))
                if not sig:
                    continue
                g = gs3 if s3 else g32
                lab = sig if not g else f'{sig} {"←" if d == ">" else "→"} {g}'
                outer = n % 2 == 0
                if mirror:
                    tx, anc = (bx0 - 14, "end") if outer else (xo + 30, "start")
                else:
                    tx, anc = (bx1 + 14, "start") if outer else (xo - 30, "end")
                fill = col if outer else TB_LIGHT[col]
                o.append(T(tx, y + 7, lab, 20, fill, anc, "700"))
        o.append(T(ox + 430, top + 20 * pitch + 70,
                   "Pino 1 (quadrado) e pino 2 na mesma ponta · fileira par na borda, "
                   + ("agora à esquerda" if mirror else "à direita"), 19, "#334155"))

    panel(0, False)
    panel(900, True)
    o.append('<line x1="900" y1="140" x2="900" y2="1150" stroke="#e2e8f0" stroke-width="3" stroke-dasharray="10 8"/>')
    o.append(f'<text x="60" y="1230" font-family="{SANS}" font-size="21" fill="#0f172a"><tspan font-weight="700">'
             'Teste de orientação (desligado, multímetro no bip):</tspan> a carcaça dos SMA é GND. '
             'Os pinos 6, 9, 14, 20 e 25 têm que apitar com ela.</text>')
    o.append(T(60, 1264, "Se apitarem 5, 19, 26… em vez disso, a contagem está espelhada. Os pinos 2 e 4 (5 V) "
               "têm que apitar entre si.", 21, "#0f172a", "start"))
    o.append(T(60, 1298, "Pinos em cinza: não ligados ao ESP32. ← = sai do ESP32 para o shield, → = vem do shield. "
               "Fonte: Tabelas 8 e 9 do Manual de Técnico Radioenge (jul/2023).", 18, "#64748b", "start"))
    return "\n".join(o) + "\n</svg>\n"


if __name__ == "__main__":
    dst = sys.argv[1]
    for fn, b in BOARDS.items():
        open(os.path.join(dst, fn), "w").write(wiring(b))
    open(os.path.join(dst, "radioenge_header.svg"), "w").write(header())
    open(os.path.join(dst, "radioenge_modulo_14vias.svg"), "w").write(module14())
    # um desenho por placa: conector de 40 pinos (vista de cima) e vista de cima × de baixo
    for b in ("esp32", "esp32s3_n16r8", "esp32s3_n32r16v"):
        open(os.path.join(dst, f"radioenge_header_{b}.svg"), "w").write(header(b))
        open(os.path.join(dst, f"radioenge_header_cima_baixo_{b}.svg"), "w").write(header_top_bottom(b))
    print("ok")
