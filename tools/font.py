"""5×7-Pixelschrift (Großbuchstaben, Ziffern, ein paar Zeichen)."""

GLYPHS = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "10001", "11001", "10101", "10011", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    " ": ["00000"] * 7,
    "·": ["00000", "00000", "00000", "00100", "00000", "00000", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    ":": ["00000", "00100", "00000", "00000", "00000", "00100", "00000"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "×": ["00000", "10001", "01010", "00100", "01010", "10001", "00000"],
    "▶": ["10000", "11000", "11100", "11110", "11100", "11000", "10000"],
}
# Ş: S mit Cedille (unterlängig, achte Zeile)
GLYPHS["Ş"] = GLYPHS["S"] + ["00100", "01000"]


def text_rects(text, x, y, px, color, spacing=1):
    """SVG-Rechtecke für einen Text in der Pixelschrift. Gibt (svg, breite) zurück.
    Mit color=None bekommen die Rechtecke keine Füllfarbe und erben sie (für <use>)."""
    out = []
    cx = x
    fill = f' fill="{color}"' if color else ""
    for ch in text.upper() if text.upper() != text else text:
        glyph = GLYPHS.get(ch, GLYPHS[" "])
        for gy, row in enumerate(glyph):
            gx = 0
            while gx < len(row):
                if row[gx] == "1":
                    run = 1
                    while gx + run < len(row) and row[gx + run] == "1":
                        run += 1
                    out.append(f'<rect x="{cx + gx * px:g}" y="{y + gy * px:g}" width="{run * px:g}" height="{px:g}"{fill}/>')
                    gx += run
                else:
                    gx += 1
        cx += (len(glyph[0]) + spacing) * px
    return "".join(out), cx - x - spacing * px


def text_width(text, px, spacing=1):
    return len(text) * (5 + spacing) * px - spacing * px


_ids = iter(range(10 ** 6))


def fancy_text(text, x, y, px, bands, outline, shadow, o):
    """Titelschrift: Füllung mit Farbverlauf in Zeilenbändern, Kontur (Versatz o) und Schlagschatten."""
    tid = f"txt{next(_ids)}"
    rows = {}
    cx = x
    for ch in text:
        glyph = GLYPHS.get(ch, GLYPHS[" "])
        for gy, row in enumerate(glyph):
            band = bands[min(len(bands) - 1, gy * len(bands) // 7)]
            for gx, bit in enumerate(row):
                if bit == "1":
                    rows.setdefault(band, []).append(f'<rect x="{cx - x + gx * px:g}" y="{gy * px:g}" width="{px:g}" height="{px:g}"/>')
        cx += 6 * px
    body = "".join(r for rs in rows.values() for r in rs)
    offsets = [(dx, dy) for dx in (-o, 0, o) for dy in (-o, 0, o) if dx or dy]
    out = [f'<defs><g id="{tid}">{body}</g></defs>']
    out.append(f'<use xlink:href="#{tid}" x="{x + o * 2:g}" y="{y + o * 2:g}" fill="{shadow}"/>')
    out.append(f'<g fill="{outline}">' + "".join(f'<use xlink:href="#{tid}" x="{x + dx:g}" y="{y + dy:g}"/>' for dx, dy in offsets) + "</g>")
    for band, rs in rows.items():
        out.append(f'<g fill="{band}" transform="translate({x:g},{y:g})">{"".join(rs)}</g>')
    return "".join(out)


def outlined_text(text, x, y, px, color, outline):
    """Text mit 1-Pixel-Kontur in alle Richtungen (gut lesbar auf hellem und dunklem Grund).
    Der Text wird einmal definiert und für Kontur und Füllung per <use> wiederverwendet."""
    tid = f"txt{next(_ids)}"
    body = text_rects(text, 0, 0, px, None)[0]
    offsets = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1), (0, 2), (1, 2), (-1, 2))
    uses = "".join(f'<use xlink:href="#{tid}" x="{x + dx * px:g}" y="{y + dy * px:g}"/>' for dx, dy in offsets)
    return (
        f'<defs><g id="{tid}">{body}</g></defs>'
        f'<g fill="{outline}">{uses}</g><use xlink:href="#{tid}" x="{x:g}" y="{y:g}" fill="{color}"/>'
    )
