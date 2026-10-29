"""Erzeugt assets/header.svg: 16-Bit-Kulisse mit Parallax, drehenden Ringen und Titelkarten-Intro."""

import math
from pathlib import Path

from font import fancy_text, outlined_text, text_width
from pixel import Grid, svg_rects
from ring_sprite import FRAME_MS
from sprites import COLORS, cloud, fatih_ring_frames, ground_tile, palm

P = 3  # Bildschirmpixel pro Spielpixel
W, H = 280, 80  # Spielpixel (840 × 240 Bildschirmpixel)
SKY_END = 44
GROUND = 60
GROUND_SPEED = 96  # Bildschirmpixel pro Sekunde

DEFS = []
PAL = dict(COLORS)

# Nachtpalette: überschreibt die Tagesfarben (Ring, Schrift und UI bleiben gleich)
NIGHT = {
    "s0": "#060a22", "s1": "#090f2c", "s2": "#0d1536", "s3": "#111b42", "s4": "#16224e",
    "s5": "#1c2a5a", "s6": "#233466", "s7": "#2b3e72",
    "c0": "#56659a", "c1": "#435284", "c2": "#34416e", "c3": "#283358",
    "m0": "#0e1634", "m1": "#162046", "m2": "#202c58", "m3": "#4a5c96",
    "w0": "#08142e", "w1": "#0e1e42", "w2": "#182c58", "w3": "#b4c8ff",
    "h0": "#03120a", "h1": "#072012", "h2": "#0b2e1a", "h3": "#113e24", "h4": "#1a5030", "h5": "#2a683e",
    "g0": "#051c0e", "g1": "#0c3418", "g2": "#165224", "g3": "#2a7232",
    "e0": "#1a0904", "e1": "#2a1207", "e2": "#381a0b", "e3": "#48230f", "e4": "#5c3016", "e5": "#724222",
    "t0": "#180b04", "t1": "#28140a", "t2": "#381f0f", "t3": "#4a2c16",
    "p0": "#03180a", "p1": "#062812", "p2": "#0b381a", "p3": "#144a24", "p4": "#226032",
    "n0": "#1c0e04", "n1": "#2c1808",
    "mo": "#f6f1d4", "ms": "#d8d0a6", "mc": "#c2b98c",
}


def define(name, grid):
    DEFS.append(f'<g id="{name}">{svg_rects(grid, 1, PAL)}</g>')


def moon():
    """Pixel-Mond 16×16: helle Scheibe, Schatten unten rechts, drei Krater."""
    g = Grid(16, 16)
    g.ellipse(8, 8, 7, 7, "mo")
    g.fill(lambda x, y: (x - 10.5) ** 2 + (y - 10.5) ** 2 > 7.2 ** 2, "ms", only=("mo",))
    for cx, cy, r in ((5.5, 6, 1.6), (10, 4.5, 1.1), (9, 10, 1.9)):
        g.ellipse(cx, cy, r, r, "mc", only=("mo", "ms"))
    return g


def stars(seed=7):
    """Sterne an festen Pseudo-Zufallspositionen im oberen Himmel, in drei Funkel-Gruppen."""
    import random

    rnd = random.Random(seed)
    groups = [[], [], []]
    for i in range(54):
        x, y = rnd.randrange(2, W - 2), rnd.randrange(1, 34)
        big = rnd.random() < 0.18
        col = "#ffffff" if rnd.random() < 0.6 else "#bcd2ff"
        cells = [(x, y)] + ([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)] if big else [])
        groups[i % 3].append("".join(f'<rect x="{cx * P}" y="{cy * P}" width="{P}" height="{P}" fill="{col}"/>' for cx, cy in cells))
    return ["".join(g) for g in groups]


def use(name, x, y):
    return f'<use xlink:href="#{name}" x="{x:g}" y="{y:g}"/>'


def mountains():
    """Bergkette als Höhenprofil, links beleuchtete Hänge, rechte Hänge im Schatten, helle Gipfel."""
    g = Grid(W, 24)
    peaks = [(18, 14, 0.9), (60, 20, 1.0), (98, 12, 0.8), (140, 22, 1.1), (186, 14, 0.85), (230, 19, 1.0), (268, 13, 0.9)]

    def height(x):
        best, side = 0, 0
        for px_, ph, sl in peaks:
            for dx in (-W, 0, W):
                h = ph - abs(x - (px_ + dx)) * sl * 0.9
                if h > best:
                    best, side = h, (x - (px_ + dx))
        return best, side

    for x in range(W):
        h, side = height(x + 0.5)
        top = 24 - h
        for y in range(g.h):
            if y + 0.5 >= top:
                depth = y + 0.5 - top
                if depth < 1.2:
                    col = "m3" if side < 0 else "m2"
                elif side < 0 and depth < 4:
                    col = "m2"
                elif side > 0 and depth > 2:
                    col = "m0"
                else:
                    col = "m1"
                g.set(x, y, col)
    return g


def hills():
    """Rollende Hügel mit horizontalen Streifen (typischer 16-Bit-Look) und heller Oberkante."""
    hgt = 16
    g = Grid(W, hgt)

    def surface(x):
        t = x / W * 2 * math.pi
        return 7 + 3 * math.sin(t * 2 + 0.6) + 1.6 * math.sin(t * 5 + 1.7) + 1.0 * math.sin(t * 3)

    for x in range(W):
        top = surface(x + 0.5)
        for y in range(hgt):
            d = y + 0.5 - top
            if d < 0:
                continue
            if d < 1:
                col = "h0"
            elif d < 2:
                col = "h5"
            elif d < 3:
                col = "h4"
            else:
                band = int((y - 0) // 3)
                col = ("h3", "h2")[band % 2] if d < 6 else ("h2", "h1")[band % 2]
            g.set(x, y, col)
    return g


def build(theme="light"):
    global PAL
    DEFS.clear()
    frames = fatih_ring_frames()  # trägt die Ringfarben in COLORS ein
    PAL = dict(COLORS)
    if theme == "dark":
        PAL.update(NIGHT)
    css = []
    body = []
    S = f'transform="scale({P})"'

    # Himmel in Bändern
    edges = [0, 7, 13, 18, 23, 28, 33, 38, SKY_END]
    for i in range(8):
        body.append(f'<rect x="0" y="{edges[i] * P}" width="840" height="{(edges[i + 1] - edges[i]) * P}" fill="{PAL["s" + str(i)]}"/>')

    if theme == "dark":
        # Sterne in drei Gruppen, die versetzt funkeln
        for i, grp in enumerate(stars()):
            body.append(f'<g class="tw" style="animation-delay:{-i * 0.8:.1f}s">{grp}</g>')
        css.append(".tw{animation:tw 2.4s step-end infinite}@keyframes tw{0%{opacity:1}50%{opacity:.35}75%{opacity:.7}}")
        # Mond mit schwachem Schein
        define("moon", moon())
        body.append('<circle cx="132" cy="42" r="54" fill="#f6f1d4" opacity=".05"/><circle cx="132" cy="42" r="34" fill="#f6f1d4" opacity=".08"/>')
        body.append(f'<g {S}>{use("moon", 36, 6)}</g>')
        # Sternschnuppe alle paar Sekunden
        trail = "".join(
            f'<rect x="{i * P}" y="{-i * P // 2 // P * P}" width="{P}" height="{P}" fill="{c}"/>'
            for i, c in enumerate(("#ffffff", "#ffffff", "#dfe8ff", "#bcd2ff", "#8fa8e8", "#5f78c0"))
        )
        body.append(f'<g transform="translate(700,12)"><g class="shoot">{trail}</g></g>')
        css.append(
            ".shoot{opacity:0;animation:shoot 9s linear 3s infinite}"
            "@keyframes shoot{0%{opacity:0;transform:translate(0,0)}1%{opacity:1}8%{opacity:1;transform:translate(-180px,90px)}9%,100%{opacity:0;transform:translate(-180px,90px)}}"
        )

    # Wolken (zwei Größen), sehr langsam
    define("cl0", cloud(40, 16, 0))
    define("cl1", cloud(28, 11, 1))
    cpos = [("cl0", 8, 6), ("cl1", 70, 16), ("cl0", 128, 3), ("cl1", 190, 12), ("cl0", 232, 8)]
    tiles = "".join(use(n, x + dx, y) for dx in (0, W) for n, x, y in cpos)
    body.append(f'<g class="clouds"><g {S}>{tiles}</g></g>')
    css.append(".clouds{animation:scroll 140s linear infinite}")

    # Berge
    define("mount", mountains())
    body.append(f'<g class="mount"><g {S}>{use("mount", 0, SKY_END - 24)}{use("mount", W, SKY_END - 24)}</g></g>')
    css.append(".mount{animation:scroll 70s linear infinite}")

    # Wasser mit Glitzern
    body.append(f'<rect x="0" y="{SKY_END * P}" width="840" height="{2 * P}" fill="{PAL["w2"]}"/>')
    body.append(f'<rect x="0" y="{(SKY_END + 2) * P}" width="840" height="{6 * P}" fill="{PAL["w1"]}"/>')
    body.append(f'<rect x="0" y="{(SKY_END + 6) * P}" width="840" height="{4 * P}" fill="{PAL["w0"]}"/>')
    for k in range(2):
        dashes = "".join(
            f'<rect x="{(x * 23 + k * 11 + (row * 7)) % W * P}" y="{(SKY_END + 1 + row * 2) * P}" width="{(3 - row % 2) * P}" height="{P}" fill="{PAL["w3"]}"/>'
            for row in range(4) for x in range(12)
        )
        body.append(f'<g class="sh{k}">{dashes}</g>')
    css.append(".sh0{animation:blink .8s step-end infinite}.sh1{animation:blink .8s step-end infinite reverse}")

    # Hügel mit Palmen
    define("hills", hills())
    define("palm0", palm(30, 1))
    define("palm1", palm(27, -1))
    hill_y = GROUND - 16
    palms = "".join(use(n, x + dx, y) for dx in (0, W) for n, x, y in (("palm0", 34, GROUND - 31), ("palm1", 150, GROUND - 28), ("palm0", 222, GROUND - 30)))
    body.append(f'<g class="hills"><g {S}>{use("hills", 0, hill_y)}{use("hills", W, hill_y)}{palms}</g></g>')
    css.append(".hills{animation:scroll 28s linear infinite}")

    # Boden
    gt = ground_tile(16, 5, H - GROUND)
    define("ground", gt)
    gtiles = "".join(use("ground", x, GROUND) for x in range(0, W + 32, 16))
    t_tile = 16 * P / GROUND_SPEED
    body.append(f'<g class="ground"><g {S}>{gtiles}</g></g>')
    css.append(f".ground{{animation:gscroll {t_tile:.3f}s linear infinite}}@keyframes gscroll{{to{{transform:translateX(-{16 * P}px)}}}}")

    # Fatihs Ring (16 Frames, 50 ms), doppelt groß, in einer Reihe, zieht mit dem Boden vorbei
    for i, f in enumerate(frames):
        define(f"r{i}", f)
    n, dur = len(frames), FRAME_MS * len(frames) / 1000
    css.append(f".rf{{opacity:0;animation:rf {dur}s step-end infinite}}@keyframes rf{{0%{{opacity:1}}{100 / n:.3f}%{{opacity:0}}}}")
    ring_one = "".join(f'<g class="rf" style="animation-delay:{-(n - i) * dur / n:.3f}s">{use("r" + str(i), 0, 0)}</g>' for i in range(n))
    DEFS.append(f'<g id="ring">{ring_one}</g>')
    pattern_w = 140  # Spielpixel, Muster wiederholt sich
    arcs = [(30 + j * 14, GROUND - 15) for j in range(5)]  # gerade Reihe
    rings = "".join(
        f'<g transform="translate({(x + dx) * P},{y * P}) scale(2)"><use xlink:href="#ring"/></g>'
        for dx in range(0, W + pattern_w + 1, pattern_w) for x, y in arcs
    )
    t_rings = pattern_w * P / GROUND_SPEED
    body.append(f'<g class="rings">{rings}</g>')
    css.append(f".rings{{animation:rscroll {t_rings:.3f}s linear infinite}}@keyframes rscroll{{to{{transform:translateX(-{pattern_w * P}px)}}}}")

    # Titelkarte: Name mit Verlauf, Untertitel, PRESS START
    name = "FATIH COŞKUN"
    nw = text_width(name, 6)
    nx = (840 - nw) // 2 // 3 * 3
    title = fancy_text(name, nx, 18, 6, ["#ffffff", "#fff3a0", "#ffd84a", "#ffb21e"], PAL["navy"], PAL["shadow"], 3)
    start = "▶ PRESS START"
    px_ = (840 - text_width(start, 3)) // 2 // 3 * 3
    press = outlined_text(start, px_, 87, 3, "#ffffff", PAL["navy"])
    body.append(f'<g class="title">{title}</g><g class="press"><g class="blink">{press}</g></g>')

    # Intro: drei Balken fegen durchs Bild, dann fällt der Name herein
    stripes = []
    for i, col in enumerate(("#2464d6", "#ffc81e", "#e8262c")):
        y0 = i * 80
        stripes.append(f'<polygon points="0,{y0} 900,{y0} 860,{y0 + 80} -40,{y0 + 80}" fill="{col}"/>')
    body.append(f'<g class="intro">{"".join(stripes)}</g>')
    css.append(
        ".intro{animation:intro 1.1s cubic-bezier(.6,0,.4,1) both}"
        "@keyframes intro{0%{transform:translateX(0)}35%{transform:translateX(0)}100%{transform:translateX(1000px)}}"
        ".title{animation:drop .5s steps(5,end) .55s both}"
        "@keyframes drop{from{transform:translateY(-120px)}to{transform:translateY(0)}}"
        ".press{animation:appear .01s 1.2s both}@keyframes appear{from{opacity:0}to{opacity:1}}"
        ".blink{animation:blink 1.2s step-end 1.2s infinite}"
        "@keyframes blink{0%{opacity:1}55%{opacity:0}}"
        "@keyframes scroll{to{transform:translateX(-840px)}}"
    )

    return (
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 840 240" '
        'width="840" height="240" shape-rendering="crispEdges" role="img">'
        "<title>Fatih Coşkun</title>"
        f"<style>{''.join(css)}</style>"
        f'<defs><clipPath id="r"><rect width="840" height="240" rx="15"/></clipPath>{"".join(DEFS)}</defs>'
        f'<g clip-path="url(#r)">{"".join(body)}</g></svg>'
    )


if __name__ == "__main__":
    assets = Path(__file__).resolve().parent.parent / "assets"
    for theme, name in (("light", "header.svg"), ("dark", "header-dark.svg")):
        out = assets / name
        out.write_text(build(theme))
        print(f"{out} ({out.stat().st_size // 1024} KB)")
