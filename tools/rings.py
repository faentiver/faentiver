"""Erzeugt assets/rings.svg: der GitHub-Beitragskalender als goldene Ringe, die ein Komet einsammelt.

Läuft täglich als GitHub-Action. Braucht GITHUB_TOKEN (oder GH_TOKEN) für die GraphQL-API.
Ohne Token wird der letzte Stand aus data/contributions.json verwendet.
"""

import json
import os
import urllib.request
from datetime import date
from pathlib import Path

from font import outlined_text, text_rects, text_width
from pixel import Grid, svg_rects
from sprites import COLORS, comet, ring

ROOT = Path(__file__).resolve().parent.parent
LOGIN = "faentiver"
QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
  totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}"""

W, H = 840, 236
CELL = 14
COLS, ROWS = 53, 7
GX = (W - COLS * CELL) // 2
GY = 52
RUN, CYCLE = 9.0, 12.0  # Sekunden: Lauf über die Breite, ganzer Zyklus
SIZE = {"FIRST_QUARTILE": 8, "SECOND_QUARTILE": 10, "THIRD_QUARTILE": 12, "FOURTH_QUARTILE": 12}


def fetch():
    cache = ROOT / "data" / "contributions.json"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
            headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            cal = json.load(r)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        cache.parent.mkdir(exist_ok=True)
        cache.write_text(json.dumps(cal, indent=1))
        return cal
    return json.loads(cache.read_text())


def streaks(days):
    best = cur = 0
    for d in days:
        cur = cur + 1 if d["contributionCount"] > 0 else 0
        best = max(best, cur)
    return best


def build(cal):
    weeks = cal["weeks"][-COLS:]
    days = [d for w in weeks for d in w["contributionDays"]]
    total = cal["totalContributions"]
    active = sum(1 for d in days if d["contributionCount"] > 0)

    # Komet: Startposition und Geschwindigkeit, daraus der Zeitpunkt, an dem er eine Spalte erreicht
    c_scale = 2
    c_w = 22 * c_scale
    x_from, x_to = -c_w - 20, W + 20
    head = 18 * c_scale

    def t_at(x):
        return RUN * (x - x_from - head) / (x_to - x_from)

    css = f"""
    .spin{{animation:spin 1s steps(1,end) infinite;transform-box:fill-box;transform-origin:center}}
    .col{{animation:collect {CYCLE}s linear infinite both;transform-box:fill-box;transform-origin:center}}
    .spark{{opacity:0;animation:spark {CYCLE}s linear infinite}}
    .comet{{animation:run {CYCLE}s linear infinite}}
    .beam{{animation:run {CYCLE}s linear infinite}}
    .cf0{{animation:flick .16s step-end infinite reverse}}
    .cf1{{animation:flick .16s step-end infinite}}
    .ground{{animation:gs .5s linear infinite}}
    @keyframes spin{{0%{{transform:scaleX(1)}}25%{{transform:scaleX(.55)}}50%{{transform:scaleX(.15)}}75%{{transform:scaleX(.55)}}}}
    @keyframes collect{{0%{{opacity:1;transform:scale(1)}}2%{{opacity:0;transform:scale(1.9)}}72%{{opacity:0;transform:scale(.3)}}82%{{opacity:1;transform:scale(1)}}100%{{opacity:1;transform:scale(1)}}}}
    @keyframes spark{{0%{{opacity:1}}4%{{opacity:0}}100%{{opacity:0}}}}
    @keyframes run{{0%{{transform:translateX({x_from}px)}}{RUN / CYCLE * 100:.2f}%{{transform:translateX({x_to}px)}}100%{{transform:translateX({x_to}px)}}}}
    @keyframes flick{{0%{{opacity:1}}50%{{opacity:0}}}}
    @keyframes gs{{from{{transform:translateX(0)}}to{{transform:translateX(-16px)}}}}
    """

    defs = [f'<clipPath id="r"><rect width="{W}" height="{H}" rx="16"/></clipPath>']
    for s in sorted(set(SIZE.values())):
        defs.append(f'<g id="ring{s}">{svg_rects(ring(s), 1, COLORS)}</g>')
    defs.append('<g id="spark"><rect x="2" y="0" width="1" height="5" fill="#fff6b0"/><rect x="0" y="2" width="5" height="1" fill="#fff6b0"/><rect x="2" y="2" width="1" height="1" fill="#ffffff"/></g>')

    p = [f'<g clip-path="url(#r)"><rect width="{W}" height="{H}" fill="{COLORS["panel"]}"/>']

    # HUD oben links, Zonen-Titel oben rechts
    hx, hy = 28, 18
    for label, value in (("RINGS", f"{total:04d}"), ("STREAK", str(streaks(days))), ("DAYS", str(active))):
        p.append(outlined_text(label, hx, hy, 2, COLORS["Y"], COLORS["navy"]))
        hx += text_width(label, 2) + 10
        p.append(outlined_text(value, hx, hy, 2, "#ffffff", COLORS["navy"]))
        hx += text_width(value, 2) + 26
    zone = "CONTRIBUTION ZONE"
    p.append(outlined_text(zone, W - 28 - text_width(zone, 2), hy, 2, "#ffffff", COLORS["navy"]))

    # Lichtsäule, die mit dem Kometen läuft (zeigt, welche Spalte gerade eingesammelt wird)
    p.append(f'<g class="beam"><rect x="{head - CELL // 2}" y="{GY - 4}" width="{CELL}" height="{ROWS * CELL + 8}" fill="#5bb4ff" opacity=".10"/></g>')

    # Ringe bzw. leere Felder
    for c, w in enumerate(weeks):
        cx = GX + c * CELL + CELL / 2
        delay = t_at(cx)
        for d in w["contributionDays"]:
            row = date.fromisoformat(d["date"]).isoweekday() % 7  # Sonntag oben, wie bei GitHub
            cy = GY + row * CELL + CELL / 2
            lvl = d["contributionLevel"]
            if lvl == "NONE":
                p.append(f'<rect x="{cx - 1:g}" y="{cy - 1:g}" width="2" height="2" fill="{COLORS["dot"]}"/>')
                continue
            s = SIZE[lvl]
            glow = f'<circle cx="{cx:g}" cy="{cy:g}" r="7" fill="#ffd21a" opacity=".18"/>' if lvl == "FOURTH_QUARTILE" else ""
            p.append(
                f'{glow}<g class="col" style="animation-delay:{delay:.2f}s"><g class="spin">'
                f'<use xlink:href="#ring{s}" x="{cx - s / 2:g}" y="{cy - s / 2:g}"/></g></g>'
                f'<g class="spark" style="animation-delay:{delay:.2f}s"><use xlink:href="#spark" x="{cx - 2.5:g}" y="{cy - 9:g}"/></g>'
            )

    # Laufstrecke mit Gras und Schachbrett
    ty = GY + ROWS * CELL + 44
    p.append(f'<rect x="0" y="{ty}" width="{W}" height="3" fill="{COLORS["g1"]}"/><rect x="0" y="{ty + 3}" width="{W}" height="2" fill="{COLORS["g2"]}"/>')
    tiles = []
    for x in range(0, W + 32, 8):
        for i, y in enumerate(range(ty + 5, H, 8)):
            col = COLORS["e1"] if ((x // 8) + i) % 2 == 0 else COLORS["e2"]
            tiles.append(f'<rect x="{x}" y="{y}" width="8" height="8" fill="{col}"/>')
    p.append(f'<g class="ground">{"".join(tiles)}</g>')

    # Komet auf der Strecke
    c0, c1 = svg_rects(comet(0), 1, COLORS), svg_rects(comet(1), 1, COLORS)
    p.append(
        f'<g transform="translate(0,{ty - 9 * c_scale - 2})"><g class="comet"><g transform="scale({c_scale})">'
        f'<g class="cf0">{c0}</g><g class="cf1">{c1}</g></g></g></g>'
    )

    # Fußzeile
    foot = f"LAST 12 MONTHS · UPDATED {date.today().isoformat()}"
    svg, _ = text_rects(foot, W - 28 - text_width(foot, 1), GY + ROWS * CELL + 14, 1, "#5b6f9e")
    p.append(svg)
    p.append("</g>")

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" shape-rendering="crispEdges" role="img">'
        f"<title>{total} Beiträge im letzten Jahr als goldene Ringe</title>"
        f"<style>{css}</style><defs>{''.join(defs)}</defs>{''.join(p)}</svg>"
    )


if __name__ == "__main__":
    out = ROOT / "assets" / "rings.svg"
    out.write_text(build(fetch()))
    print(f"{out} ({out.stat().st_size // 1024} KB)")
