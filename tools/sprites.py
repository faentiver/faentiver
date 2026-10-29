"""Eigene Pixel-Sprites für Header und Ring-Kalender: Komet, Ring, Wolke, Palme, Hügel."""

from pixel import Grid

COLORS = {
    # Himmel
    "s1": "#1d4fc4", "s2": "#2c68dd", "s3": "#3f86ee", "s4": "#62a6f7", "s5": "#8cc6ff",
    # Wolke
    "cw": "#ffffff", "cs": "#cfe8ff",
    # Berge in der Ferne
    "m1": "#4b8be8", "m2": "#6aa5f2",
    # Hügel und Gras
    "h1": "#1f7a35", "h2": "#2e9e46", "h3": "#49c25a", "g1": "#6ee05a", "g2": "#2f9d3a",
    # Erde (Schachbrett)
    "e1": "#c46a24", "e2": "#8a3c12", "e3": "#e08a3a",
    # Palme
    "t1": "#8a4a1c", "t2": "#b8682a", "p1": "#1f8f3a", "p2": "#3fc04e",
    # Komet
    "k0": "#ffffff", "k1": "#bfe6ff", "k2": "#5bb4ff", "k3": "#2b72f0", "k4": "#1a3fae",
    # Ring
    "Y": "#ffd21a", "O": "#d48800", "L": "#fff6b0",
    # Schrift und Panels
    "navy": "#0b1440", "panel": "#0c1633", "dot": "#1c2b57",
}


def ring(size=10):
    """Goldener Ring, Vorderansicht, mit dunkelgoldener Kontur."""
    g = Grid(size, size)
    c = size / 2
    r_out, r_in = size / 2 - 0.9, size / 2 - 3.0
    g.fill(lambda x, y: r_in ** 2 <= (x - c) ** 2 + (y - c) ** 2 <= r_out ** 2, "Y")
    g.fill(lambda x, y: r_in ** 2 <= (x - c) ** 2 + (y - c) ** 2 <= (r_in + 0.9) ** 2 and (x > c or y > c), "O", only=("Y",))
    g.fill(lambda x, y: (x - c) ** 2 + (y - c) ** 2 >= (r_out - 0.9) ** 2 and x < c and y < c, "L", only=("Y",))
    g.outline("O")
    return g


def comet(frame=0):
    """Blauer Speed-Komet 22×9 mit flackerndem Schweif nach links."""
    g = Grid(22, 9)
    # Kern
    g.ellipse(17.5, 4.5, 3.6, 3.6, "k3")
    g.ellipse(17.8, 4.3, 2.6, 2.6, "k2")
    g.ellipse(18.2, 4.0, 1.6, 1.6, "k1")
    g.ellipse(18.5, 3.8, 0.8, 0.8, "k0")
    # Schweif: drei Streifen, Länge wechselt pro Frame
    tails = [(3, 2.6, "k2"), (4.5, 1.3, "k1"), (5.5, 1.0, "k3")]
    for i, (y, h, col) in enumerate(tails):
        length = (13, 9, 11)[i] + (2 if (frame + i) % 2 else 0)
        g.fill(lambda x, yy, y=y, h=h, length=length: 14 - length < x < 15 and abs(yy - y - 0.5) < h / 2, col)
    # Schweif-Pixel, die abreißen
    for x, y in ((2, 3), (0, 5), (4, 7), (6, 1)):
        if (x + frame) % 3:
            g.set(x, y, "k1" if y % 2 else "k2")
    g.outline("k4")
    return g


def cloud():
    g = Grid(26, 9)
    for cx, cy, r in ((6, 5.5, 3.5), (12, 4, 4.2), (18.5, 5, 3.8), (13, 6.5, 3.4)):
        g.ellipse(cx, cy, r, r * 0.85, "cw")
    g.fill(lambda x, y: y > 7, "cs", only=("cw",))
    return g


def palm(height=22):
    """Palme mit gestreiftem Stamm."""
    g = Grid(20, height)
    for y in range(6, height):
        x = 9 + (1 if y < height * 0.45 else 0)
        col = "t1" if (y // 2) % 2 else "t2"
        g.set(x, y, col)
        g.set(x + 1, y, col)
    for pts in (
        [(10, 5), (1, 8), (3, 6)],
        [(10, 5), (19, 8), (17, 6)],
        [(10, 5), (4, 1), (7, 3)],
        [(10, 5), (16, 1), (13, 3)],
        [(10, 5), (9, 0), (11, 0)],
    ):
        g.poly(pts, "p1")
    g.fill(lambda x, y: y < 4, "p2", only=("p1",))
    g.outline("h1")
    return g
