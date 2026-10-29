"""Eigene Pixel-Sprites im 16-Bit-Stil: Ring-Drehframes, Funkeln, Wolke, Palme, Kacheln."""

import math

from pixel import Grid

COLORS = {
    # Ring (Gold-Rampe: Kontur → Glanz)
    "o1": "#6b3200", "o2": "#b06400", "o3": "#e29400", "o4": "#ffc81e", "o5": "#fff07a", "o6": "#ffffff",
    # Himmel
    "s0": "#1442b0", "s1": "#1b52c4", "s2": "#2464d6", "s3": "#3078e4", "s4": "#418cee", "s5": "#58a2f6",
    "s6": "#74b8fc", "s7": "#94ccff",
    # Wolken
    "c0": "#ffffff", "c1": "#e6f3ff", "c2": "#c4e0fc", "c3": "#9cc6f2",
    # Berge
    "m0": "#24529e", "m1": "#3464b8", "m2": "#5288d8", "m3": "#a6ccf4",
    # Wasser
    "w0": "#1f5cc8", "w1": "#2f74e0", "w2": "#5294f0", "w3": "#d6efff",
    # Hügel
    "h0": "#0e4a22", "h1": "#176a30", "h2": "#21853a", "h3": "#33a346", "h4": "#56c254", "h5": "#86dc66",
    # Gras
    "g0": "#1a5a20", "g1": "#2c8f30", "g2": "#52c63c", "g3": "#9af05a",
    # Erde (Kacheln mit Kanten)
    "e0": "#5a2006", "e1": "#8a3a10", "e2": "#a8501c", "e3": "#c86a24", "e4": "#e48c3c", "e5": "#f6b464",
    # Palme
    "t0": "#4a2410", "t1": "#7a4018", "t2": "#a8642a", "t3": "#cc8a40",
    "p0": "#0c4a1c", "p1": "#167a2c", "p2": "#28a03c", "p3": "#5cc84c", "p4": "#9ae66a",
    "n0": "#5a3410", "n1": "#8a5a22",
    # Blumen
    "f0": "#ffffff", "f1": "#ffe14a", "f2": "#ff6aa0",
    # UI
    "navy": "#0b1440", "shadow": "#050a24", "panel": "#0b1433", "dot": "#1a2a58", "dim": "#5b6f9e",
}

SPIN = (1.0, 0.86, 0.6, 0.3, 0.0, 0.3, 0.6, 0.86)  # Breitenfaktoren der acht Drehframes, 0 = Kante


def ring_frames(size=12):
    """Acht Drehframes eines goldenen Pixel-Rings.

    Das Goldband wird je Pixel 8×8-fach abgetastet. Voll bedeckte Pixel werden Gold, teilweise bedeckte
    an den Treppenstufen werden Kontur, danach umschließt eine 1-Pixel-Kontur den Rest. So bleibt die
    Silhouette rund, ohne gerade Seiten, und alles besteht aus festen Palettenfarben.
    Licht von oben links: außen oben links hell, auf der Innenwand unten rechts hell (gewölbter Reif)."""
    frames = []
    ss = 8
    c = size / 2
    ry = size / 2 - 1.05
    rx = ry * 0.95
    band = max(1.6, size * 0.19)
    ri = 1 - band / ry
    lx, ly = -0.7071, -0.7071
    for k, sx in enumerate(SPIN):
        g = Grid(size, size)
        back = k > 4
        if sx == 0.0:
            x0 = size // 2 - 1
            for y in range(2, size - 2):
                g.set(x0, y, "o5" if y < size * 0.5 else "o4")
                g.set(x0 + 1, y, "o3" if y < size * 0.65 else "o2")
            g.outline("o1")
            frames.append(g)
            continue
        w = max(rx * sx, 0.9)
        for y in range(size):
            for x in range(size):
                n = 0
                nx = ny = 0.0
                for j in range(ss):
                    for i in range(ss):
                        px_, py_ = x + (i + 0.5) / ss, y + (j + 0.5) / ss
                        ex, ey = (px_ - c) / w, (py_ - c) / ry
                        r = (ex * ex + ey * ey) ** 0.5
                        if ri <= r <= 1.0 and r > 0:
                            n += 1
                            u = (r - ri) / (1 - ri)  # 0 = Innenkante, 1 = Außenkante
                            bend = 2 * u - 1
                            nx += ex / r * bend
                            ny += ey / r * bend
                cov = n / ss ** 2
                if cov < 0.16:
                    continue
                if cov < 0.5:
                    g.set(x, y, "o1")
                    continue
                f = (nx * lx + ny * ly) / n * 1.6
                if back:
                    f -= 0.45
                if sx < 0.5:
                    f = f * 0.6 + (0.25 if x + 0.5 < c else -0.35)  # schmale Frames: links hell, rechts dunkel
                col = "o5" if f > 0.45 else ("o4" if f > -0.05 else ("o3" if f > -0.5 else "o2"))
                g.set(x, y, col)
        g.outline("o1")
        if k in (0, 1, 7):  # Glanzpunkt oben links
            for dy in range(size):
                hit = False
                for dx in range(size):
                    gx = round(c - w * 0.66) + dx // 3
                    gy = round(c - ry * 0.66) + dy // 3
                    if g.get(gx, gy) == "o5":
                        g.set(gx, gy, "o6")
                        hit = True
                        break
                if hit:
                    break
        frames.append(g)
    return frames


def sparkle_frames(size=16):
    """Vier Frames eines Funkelns beim Einsammeln."""
    frames = []
    c = size // 2
    for k in range(4):
        g = Grid(size, size)
        if k == 0:
            for d in range(-1, 2):
                g.set(c + d, c, "o6")
                g.set(c, c + d, "o6")
        elif k in (1, 2):
            ray = (3, 6)[k - 1]
            for d in range(-ray, ray + 1):
                col = "o6" if abs(d) < ray - 1 else "o5"
                g.set(c + d, c, col)
                g.set(c, c + d, col)
            for d in range(1, (2, 4)[k - 1]):
                for sx_, sy_ in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                    g.set(c + d * sx_, c + d * sy_, "o5")
        else:
            for sx_, sy_ in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                dist = 6 if sx_ and sy_ else 7
                g.set(c + sx_ * dist, c + sy_ * dist, "o5")
        frames.append(g)
    return frames


def cloud(w=40, h=16, seed=0):
    """Wolke aus überlappenden Kugeln, von oben nach unten heller → dunkler, flache Unterkante."""
    g = Grid(w, h)
    blobs = [(0.18, 0.62, 0.20), (0.36, 0.42, 0.26), (0.58, 0.36, 0.28), (0.78, 0.55, 0.22), (0.5, 0.7, 0.3)]
    if seed % 2:
        blobs = [(1 - x, y, r) for x, y, r in blobs]
    for bx, by, br in blobs:
        cx, cy, r = bx * w, by * h, br * w
        g.fill(lambda x, y, cx=cx, cy=cy, r=r: (x - cx) ** 2 + ((y - cy) * 1.6) ** 2 <= r * r and y < h - 1, "c1")
    for y in range(h):
        for x in range(w):
            if g.px[y][x]:
                above = g.get(x, y - 2)
                if above is None:
                    g.px[y][x] = "c0"
                elif y > h * 0.72:
                    g.px[y][x] = "c3" if y > h * 0.85 else "c2"
    return g


def palm(height=36, lean=1):
    """Palme mit gekrümmtem, segmentiertem Stamm, vollen hängenden Wedeln und Kokosnüssen."""
    w = 40
    g = Grid(w, height)
    top_x, top_y = w // 2, 10
    # Stamm: unten breiter, leicht gebogen, Segmente mit dunkler Kerbe
    for y in range(top_y, height):
        t = (height - y) / (height - top_y)
        x = round(top_x - lean * 5 * (1 - t) ** 2 + lean * 2)
        seg = (height - y) % 4
        width = 3 if y < height - 6 else 4
        for i in range(width):
            col = ("t1", "t2", "t3", "t2")[i] if seg else ("t0", "t1", "t2", "t1")[i]
            g.set(x - 1 + i, y, col)
    # Wedel als Kreis-Stempel entlang hängender Bögen
    fronds = Grid(w, height)
    leaves = [(-18, 9, 0.9), (-13, 13, 0.6), (18, 9, 0.9), (13, 13, 0.6), (-8, 3, 0.4), (9, 3, 0.4), (-1, -2, 0.2), (3, 6, 0.3), (-4, 7, 0.3)]
    for dxe, droop, arch in leaves:
        steps = 30
        for i in range(steps + 1):
            t = i / steps
            x = top_x + dxe * t
            y = top_y - 5 * arch * math.sin(t * math.pi) + droop * t * t
            r = 2.3 * (1 - t) ** 0.8 + 0.5
            fronds.fill(lambda px_, py_, x=x, y=y, r=r: (px_ - x - 0.5) ** 2 + (py_ - y - 0.5) ** 2 <= r * r, "p2")
    # Schattierung: oben hell, unten dunkel, mit Kontur
    for y in range(height):
        for x in range(w):
            if fronds.px[y][x] == "p2":
                if fronds.get(x, y - 1) is None:
                    fronds.px[y][x] = "p4" if (x + y) % 4 == 0 else "p3"
                elif fronds.get(x, y + 1) is None or fronds.get(x, y + 2) is None:
                    fronds.px[y][x] = "p1"
    fronds.outline("p0")
    g.paste(fronds, 0, 0)
    # Kokosnüsse unter der Krone
    for cx_, cy_ in ((top_x - 2, top_y + 1), (top_x + 1.5, top_y + 1), (top_x - 0.3, top_y + 2.5)):
        g.fill(lambda x, y, cx_=cx_, cy_=cy_: (x - cx_) ** 2 + (y - cy_) ** 2 <= 2.0, "n0")
        g.set(round(cx_ - 0.5), round(cy_ - 0.5), "n1")
    return g


def ground_tile(tile=16, grass=5, height=22):
    """Bodenkachel: Grasnarbe mit Halmen, darunter Erde im Schachbrett mit Licht- und Schattenkanten."""
    g = Grid(tile, height)
    sq = (height - grass) // 2
    for x in range(tile):
        g.set(x, 1, "g3")
        g.set(x, 2, "g2")
        g.set(x, 3, "g2" if x % 4 else "g1")
        g.set(x, 4, "g1")
    for x, hgt in ((1, 1), (4, 2), (5, 1), (9, 1), (12, 2), (13, 1)):
        for i in range(hgt):
            g.set(x % tile, 0 - i + 0, "g3")
    for x in range(tile):  # Grasnarbe hängt in Zacken über die Erde
        if x % 3 != 1:
            g.set(x, grass, "g0")
    for y in range(grass + (1 if True else 0), height):
        for x in range(tile):
            if g.get(x, y) == "g0":
                continue
            sx, sy = x // (tile // 2), (y - grass) // sq
            light = (sx + sy) % 2 == 0
            lx, ly = x % (tile // 2), (y - grass) % sq
            last_x, last_y = tile // 2 - 1, sq - 1
            if light:
                col = "e5" if (lx == 0 or ly == 0) else ("e2" if (lx == last_x or ly == last_y) else "e4")
            else:
                col = "e2" if (lx == 0 or ly == 0) else ("e0" if (lx == last_x or ly == last_y) else "e1")
            g.set(x, y, col)
    return g



def fatih_ring_frames():
    """Fatihs eigener Ring (16 Frames à 16×16) als Raster mit Palettenschlüsseln u1…u5."""
    from ring_sprite import FRAMES, PALETTE

    for k, v in PALETTE.items():
        COLORS["u" + k] = v
    frames = []
    for rows in FRAMES:
        g = Grid(16, 16)
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch != ".":
                    g.set(x, y, "u" + ch)
        frames.append(g)
    return frames
