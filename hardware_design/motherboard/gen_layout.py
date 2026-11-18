#!/usr/bin/env python3
"""Desenho de posicionamento (vista de cima, componentes) da placa adaptadora na placa perfurada 70 × 90 mm.
Escala 1 mm = 8 px. Coordenadas em mm a partir do canto inferior esquerdo da placa perfurada.
As medidas do shield seguem o padrão Raspberry Pi HAT: CONFERIR encaixando a Radioenge antes de soldar.
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
SANS = "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
K = 8.0
PX, PY = 70.0, 90.0
OX, OY = 120, 120          # margem do desenho (px)


def X(mm): return OX + mm * K
def Y(mm): return OY + (PY - mm) * K   # y para cima


def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def T(x, y, s, size=13, fill="#0f172a", anchor="middle", weight="normal", font=SANS):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-family="{font}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{esc(s)}</text>'


def rect(x0, y0, x1, y1, fill, stroke, dash="", rx=4, op=1):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{X(x0):.1f}" y="{Y(y1):.1f}" width="{(x1-x0)*K:.1f}" height="{(y1-y0)*K:.1f}" rx="{rx}" '
            f'fill="{fill}" fill-opacity="{op}" stroke="{stroke}" stroke-width="2"{d}/>')


W = int(OX * 2 + PX * K + 520)
H = int(OY + PY * K + 150)
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Posicionamento na placa perfurada">',
     '<title>Placa adaptadora ESP32 ↔ Radioenge — posicionamento na placa perfurada 70 × 90 mm</title>',
     f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="#fff" stroke="#e2e8f0" stroke-width="2"/>',
     T(W / 2, 44, "Placa adaptadora — posicionamento na placa perfurada 70 × 90 mm (vista de cima)", 22, "#0f172a", "middle", "700"),
     T(W / 2, 72, "Medidas em mm · o shield segue o padrão Raspberry Pi HAT (65 × 56,5 mm): encaixe a Radioenge no J1 antes de soldar para conferir", 13.5, "#475569")]
# placa perfurada com grade
o.append(rect(0, 0, PX, PY, "#fef3c7", "#b45309", rx=6))
g = []
x = 1.27
while x < PX:
    y = 1.27
    while y < PY:
        g.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="1.3" fill="#d6b36a"/>')
        y += 2.54
    x += 2.54
o.append("".join(g))
for cx, cy in ((2.5, 2.5), (PX - 2.5, 2.5), (2.5, PY - 2.5), (PX - 2.5, PY - 2.5)):
    o.append(f'<circle cx="{X(cx):.1f}" cy="{Y(cy):.1f}" r="{1.6*K:.1f}" fill="#fff" stroke="#92400e" stroke-width="2"/>')
# shield (contorno tracejado, fica 11 mm acima)
o.append(rect(2.5, 33.5, 67.5, 90, "#1e3a8a", "#1e3a8a", dash="10 6", op=0.10))
o.append(T(X(35), Y(70), "Radioenge (shield 65 × 56,5 mm)", 15, "#1e3a8a", "middle", "700"))
o.append(T(X(35), Y(70) + 20, "fica 11 mm acima, sobre espaçadores M2.5", 12, "#1e3a8a"))
for hx, hy in ((6, 37), (64, 37), (6, 86), (64, 86)):
    o.append(f'<circle cx="{X(hx):.1f}" cy="{Y(hy):.1f}" r="{1.4*K:.1f}" fill="#fff" stroke="#1e3a8a" stroke-width="2.5"/>')
    o.append(T(X(hx), Y(hy) + 4, "M2.5", 9.5, "#1e3a8a", "middle", "700"))
# SMA na borda
for sy in (81.5, 49.3):
    o.append(f'<rect x="{X(67.5):.1f}" y="{Y(sy)-3.2*K:.1f}" width="{9*K:.1f}" height="{6.4*K:.1f}" rx="3" fill="#d4af37" stroke="#92400e" stroke-width="1.5"/>')
o.append(T(X(68), Y(49.3) + 44, "SMA LoRa / GPS", 12, "#92400e", "start", "700"))
o.append(T(X(68), Y(49.3) + 60, "(CONFERIR posição)", 11, "#92400e", "start"))
# J1 2x20
jx0, jy = 35 - 24.13, 37
o.append(rect(jx0 - 1.3, jy - 2.6, jx0 + 48.26 + 1.3, jy + 2.6, "#111827", "#111827", rx=3))
for i in range(20):
    for r, dy in ((0, -1.27), (1, 1.27)):
        pin = 2 * i + 1 + r if True else 0
        col = "#fbbf24"
        if pin in (19, 21, 23, 24): col = "#2563eb"
        if pin in (26, 11): col = "#ea580c"
        if pin in (8, 10): col = "#9333ea"
        if pin in (2, 4): col = "#dc2626"
        if pin in (6, 9, 14, 20, 25, 30, 34, 39): col = "#9ca3af"
        o.append(f'<circle cx="{X(jx0 + i*2.54 + 1.27):.1f}" cy="{Y(jy + dy):.1f}" r="3.6" fill="{col}"/>')
o.append(T(X(jx0 + 52), Y(jy + 2.6) - 8, "J1 (2×20)", 13, "#111827", "end", "700"))
o.append(T(X(jx0 + 1.27), Y(jy - 2.6) + 16, "pino 1? (confira o quadrado na Radioenge)", 10.5, "#111827", "start", "700"))
# DevKit (faixa inferior)
o.append(rect(0.5, 3.5, 63.5, 29.5, "#0f172a", "#0f172a", op=0.88, rx=6))
o.append(T(X(32), Y(19), "U1 · DevKit ESP32 / ESP32-S3", 15, "#fff", "middle", "700"))
o.append(T(X(32), Y(19) + 20, "em 2 barras fêmeas (meça a distância entre fileiras)", 12, "#cbd5e1"))
o.append(rect(-3.5, 10, 4, 22, "#94a3b8", "#475569", rx=3))
o.append(T(X(0.25), Y(16) + 4, "USB", 12, "#1f2937", "middle", "700"))
# J2, C1, JP1, JP2, J3
items = [(-2.0, 58, 6, 66, "#fee2e2", "#dc2626", "J2"), (52, 44, 60, 49, "#fee2e2", "#dc2626", "C1 (deitado)"),
         (40, 44, 44, 47, "#fff7ed", "#dc2626", "JP1"), (46, 44, 50, 47, "#fff7ed", "#ea580c", "JP2"),
         (65, 6, 69.5, 17, "#dcfce7", "#16a34a", "J3")]
for x0, y0, x1, y1, f, s, lbl in items:
    o.append(rect(x0, y0, x1, y1, f, s, rx=3))
o.append(T(X(2), Y(62) + 4, "J2", 12, "#dc2626", "middle", "700"))
o.append(T(X(2), Y(58) + 16, "jack DC (de painel)", 10.5, "#dc2626", "start", "600"))
o.append(T(X(56), Y(46.5) + 4, "C1", 11, "#dc2626", "middle", "700"))
o.append(T(X(42), Y(45.5) + 4, "JP1", 10, "#dc2626", "middle", "700"))
o.append(T(X(48), Y(45.5) + 4, "JP2", 10, "#ea580c", "middle", "700"))
o.append(T(X(67.25), Y(11.5) + 4, "J3", 11, "#16a34a", "middle", "700"))
# cotas
o.append(f'<path d="M{X(0)} {Y(0)+30} H{X(PX)}" stroke="#334155" stroke-width="1.5" marker-start="url(#a)" marker-end="url(#a)"/>')
o.append(T(X(PX / 2), Y(0) + 50, "70 mm", 13, "#334155", "middle", "700"))
o.append(f'<path d="M{X(0)-40} {Y(0)} V{Y(PY)}" stroke="#334155" stroke-width="1.5"/>')
o.append(T(X(0) - 50, Y(PY / 2), "90 mm", 13, "#334155", "end", "700"))
# legenda / passos
lx = X(PX) + 170
steps = ["1. Encaixe a Radioenge no J1 (2×20 macho, pinos longos)",
         "   com os 4 espaçadores M2.5 × 11 mm e marque os furos.",
         "2. Fure a placa perfurada nos 4 furos M2.5 (Ø 2,7 mm).",
         "3. Solde o J1 com a Radioenge encaixada (alinhamento).",
         "4. Solde as barras fêmeas do U1 na distância da DevKit.",
         "5. Ligue pela face de solda, fios curtos:",
         "   MOSI, MISO, SCLK, CS, RESET (via JP2), GPS.",
         "6. +5V: J2 → F1 → pinos 2/4 do J1 e C1/C2;",
         "   JP1 leva o +5V ao 5V/VIN da DevKit.",
         "7. GND: todos os pinos GND do J1 + DevKit + J2.",
         "8. Antes de encaixar: confira com o multímetro que os",
         "   pinos 1 e 17 (3V3) do J1 estão SEM ligação.",
         "",
         "Cores no J1:  azul SPI · laranja RESET (26/11)",
         "roxo GPS · vermelho 5V · cinza GND"]
for k, s in enumerate(steps):
    o.append(T(lx, Y(PY) + 10 + k * 24, s, 13, "#334155" if not s.startswith("Cores") and not s.startswith("roxo") else "#475569",
               "start", "600" if s[:2] in ("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.") else "normal"))
o.insert(3, '<defs><marker id="a" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#334155"/></marker></defs>')
open(os.path.join(HERE, "esp32_radioenge_adapter_layout.svg"), "w", encoding="utf-8").write("\n".join(o) + "\n</svg>\n")
print("ok")
