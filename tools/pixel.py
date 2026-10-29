"""Pixel-Art-Werkzeuge ohne Abhängigkeiten: Raster, Formen, Kontur, PNG- und SVG-Ausgabe."""

import struct
import zlib

PALETTE = {
    "K": "#0b1440",  # Kontur
    "B": "#1f5fe8",  # Blau
    "D": "#1640a8",  # Blau, Schatten
    "H": "#5b95ff",  # Blau, Glanz
    "S": "#f6c690",  # Haut
    "T": "#d8945a",  # Haut, Schatten
    "W": "#ffffff",  # Weiß
    "G": "#22c04a",  # Iris
    "E": "#0a0f1e",  # Pupille, Nase
    "R": "#e8262c",  # Schuh
    "r": "#9e1218",  # Schuh, Schatten
    "Y": "#ffd21a",  # Ring
    "O": "#d48800",  # Ring, Schatten
    "L": "#fff6b0",  # Ring, Glanz
    "M": "#7a1c1c",  # Mund
    "c": "#8ccfff",  # Himmel hell
    "C": "#5aaef5",  # Himmel
    "N": "#0c1633",  # Nachthimmel
    "P": "#ff5a7a",  # Wange, Funken
}


class Grid:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [[None] * w for _ in range(h)]

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return None

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def fill(self, inside, c, only=None):
        """Setzt jedes Pixel, dessen Mittelpunkt `inside` erfüllt. `only` beschränkt auf bestehende Farben."""
        for y in range(self.h):
            for x in range(self.w):
                if inside(x + 0.5, y + 0.5) and (only is None or self.px[y][x] in only):
                    self.px[y][x] = c

    def ellipse(self, cx, cy, rx, ry, c, only=None):
        self.fill(lambda x, y: ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0, c, only)

    def poly(self, pts, c, only=None):
        def inside(x, y):
            hit = False
            j = len(pts) - 1
            for i in range(len(pts)):
                xi, yi = pts[i]
                xj, yj = pts[j]
                if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                    hit = not hit
                j = i
            return hit

        self.fill(inside, c, only)

    def line(self, pts, c):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            steps = int(max(abs(x1 - x0), abs(y1 - y0))) * 2 + 1
            for i in range(steps + 1):
                t = i / steps
                self.set(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t), c)

    def outline(self, color="K", background=(None,)):
        """Zeichnet eine 1-Pixel-Kontur außen um alle Pixel, die nicht Hintergrund sind."""
        marks = []
        for y in range(self.h):
            for x in range(self.w):
                if self.px[y][x] in background:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        n = self.get(x + dx, y + dy)
                        if n not in background and n != color:
                            marks.append((x, y))
                            break
        for x, y in marks:
            self.px[y][x] = color

    def paste(self, other, ox, oy, skip=(None,)):
        for y in range(other.h):
            for x in range(other.w):
                c = other.px[y][x]
                if c not in skip:
                    self.set(ox + x, oy + y, c)

    def apply(self, rows, ox=0, oy=0):
        """Überschreibt Pixel per Textmaske ('.' = unverändert, '_' = löschen)."""
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch == "_":
                    self.set(ox + x, oy + y, None)
                elif ch != ".":
                    self.set(ox + x, oy + y, ch)


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def write_png(path, grid, scale, palette=PALETTE, background=None):
    """Schreibt das Raster als PNG (RGBA), jedes Pixel `scale`×`scale` groß."""
    bg = (*hex_rgb(background), 255) if background else (0, 0, 0, 0)
    raw = bytearray()
    for y in range(grid.h):
        line = bytearray()
        for x in range(grid.w):
            c = grid.px[y][x]
            rgba = (*hex_rgb(palette[c]), 255) if c is not None else bg
            line.extend(bytes(rgba) * scale)
        for _ in range(scale):
            raw.append(0)
            raw.extend(line)

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    w, h = grid.w * scale, grid.h * scale
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def svg_rects(grid, scale=1, palette=PALETTE, ox=0, oy=0):
    """Gibt das Raster als SVG-Rechtecke aus; waagerechte Läufe gleicher Farbe werden zusammengefasst."""
    out = []
    for y in range(grid.h):
        x = 0
        while x < grid.w:
            c = grid.px[y][x]
            if c is None:
                x += 1
                continue
            run = 1
            while x + run < grid.w and grid.px[y][x + run] == c:
                run += 1
            out.append(
                f'<rect x="{ox + x * scale:g}" y="{oy + y * scale:g}" width="{run * scale:g}" height="{scale:g}" fill="{palette[c]}"/>'
            )
            x += run
    return "".join(out)
