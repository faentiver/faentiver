"""Erzeugt assets/rings.svg: der GitHub-Beitragskalender als goldene Ringe.

Ablauf pro Runde: Die Ringe werden Spalte für Spalte mit Funkeln eingesammelt, der RINGS-Zähler zählt mit,
dann erscheint „ZONE CLEAR!“, danach tauchen die Ringe wieder auf.

Läuft täglich als GitHub-Action. Braucht GITHUB_TOKEN (oder GH_TOKEN) für die GraphQL-API.
Ohne Token wird der letzte Stand aus data/contributions.json verwendet.
"""

import json
import os
import urllib.request
from datetime import date
from pathlib import Path

from font import fancy_text, outlined_text, text_rects, text_width
from pixel import svg_rects
from ring_sprite import FRAME_MS
from sprites import COLORS, fatih_ring_frames, sparkle_frames

ROOT = Path(__file__).resolve().parent.parent
LOGIN = "faentiver"
QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
  totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}"""

CELL = 17  # 16-Pixel-Ring + 1 Pixel Abstand
COLS, ROWS = 53, 7
HALF = 27  # das Jahr in zwei Hälften untereinander: 27 + 26 Wochen
W = 840
GX = (W - HALF * CELL) // 2
GY = 50
GY2 = GY + ROWS * CELL + 14
H = GY2 + ROWS * CELL + 34
CYCLE = 13.0
SWEEP_START, SWEEP = 0.8, 7.0
CLEAR_IN, CLEAR_OUT = 8.1, 11.4
RESPAWN = 11.7
RING = 16


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


def streak(days):
    best = cur = 0
    for d in days:
        cur = cur + 1 if d["contributionCount"] > 0 else 0
        best = max(best, cur)
    return best


def pct(t):
    return f"{max(0.0, min(100.0, t / CYCLE * 100)):.3f}%"


def build(cal):
    weeks = cal["weeks"][-COLS:]
    days = [d for w in weeks for d in w["contributionDays"]]
    total = sum(d["contributionCount"] for d in days)
    active = sum(1 for d in days if d["contributionCount"] > 0)
    dt = SWEEP / COLS

    def t_col(c):
        return SWEEP_START + c * dt

    css = [
        "@keyframes rf{0%{opacity:1}" + f"{100 / 16:.3f}" + "%{opacity:0}}",
        f".rf{{opacity:0;animation:rf {FRAME_MS * 16 / 1000}s step-end infinite}}",
        "@keyframes sp{0%{opacity:1}" + f"{0.07 / CYCLE * 100:.3f}" + "%{opacity:0}}",
        f".sp{{opacity:0;animation:sp {CYCLE}s step-end infinite}}",
    ]
    defs = [f'<clipPath id="r"><rect width="{W}" height="{H}" rx="15"/></clipPath>']

    frames = fatih_ring_frames()
    for i, f in enumerate(frames):
        defs.append(f'<g id="rf{i}">{svg_rects(f, 1, COLORS)}</g>')
    n = len(frames)
    defs.append('<g id="ring">' + "".join(
        f'<g class="rf" style="animation-delay:{-(n - i) * FRAME_MS / 1000:.3f}s"><use xlink:href="#rf{i}"/></g>' for i in range(n)) + "</g>")
    for i, f in enumerate(sparkle_frames(16)):
        defs.append(f'<g id="sp{i}">{svg_rects(f, 1, COLORS)}</g>')

    p = [f'<g clip-path="url(#r)"><rect width="{W}" height="{H}" fill="{COLORS["panel"]}"/>']
    # feines Punktraster wie ein Level-Hintergrund
    p.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#bg)"/>')
    defs.append(
        '<pattern id="bg" width="14" height="14" patternUnits="userSpaceOnUse">'
        f'<rect x="0" y="0" width="1" height="1" fill="{COLORS["dot"]}" opacity=".45"/></pattern>'
    )

    # HUD links: RINGS (zählt mit), STREAK, DAYS
    hx, hy = 28, 18
    p.append(outlined_text("RINGS", hx, hy, 2, COLORS["o4"], COLORS["navy"]))
    cx = hx + text_width("RINGS", 2) + 10
    # Zählerstände: 0 bis zur ersten Spalte, danach kumuliert je Spalte, nach dem Respawn wieder 0
    states = [(0.0, 0)]
    cum = 0
    for c, w in enumerate(weeks):
        cum += sum(d["contributionCount"] for d in w["contributionDays"])
        if cum != states[-1][1]:
            states.append((t_col(c), cum))
    states.append((RESPAWN, 0))
    for i, (start, value) in enumerate(states):
        end = states[i + 1][0] if i + 1 < len(states) else CYCLE
        if end <= start:
            continue
        name = f"cnt{i}"
        css.append(f"@keyframes {name}{{0%,{pct(start)}{{opacity:0}}{pct(start)},{pct(end)}{{opacity:1}}{pct(end)},100%{{opacity:0}}}}")
        css.append(f".{name}{{opacity:0;animation:{name} {CYCLE}s step-end infinite}}")
        if start == 0.0:
            css[-2] = f"@keyframes {name}{{0%,{pct(end)}{{opacity:1}}{pct(end)},100%{{opacity:0}}}}"
        p.append(f'<g class="{name}">{outlined_text(f"{value:04d}", cx, hy, 2, "#ffffff", COLORS["navy"])}</g>')
    cx += text_width("0000", 2) + 26
    for label, value in (("STREAK", str(streak(days))), ("DAYS", str(active))):
        p.append(outlined_text(label, cx, hy, 2, COLORS["o4"], COLORS["navy"]))
        cx += text_width(label, 2) + 10
        p.append(outlined_text(value, cx, hy, 2, "#ffffff", COLORS["navy"]))
        cx += text_width(value, 2) + 26
    zone = "CONTRIBUTION ZONE"
    p.append(outlined_text(zone, W - 28 - text_width(zone, 2), hy, 2, "#ffffff", COLORS["navy"]))

    # Ringe bzw. leere Felder
    for c, w in enumerate(weeks):
        x0 = GX + (c % HALF) * CELL
        gy = GY if c < HALF else GY2
        t = t_col(c)
        respawn = RESPAWN + c * 0.012
        kname = f"k{c}"
        css.append(
            f"@keyframes {kname}{{0%,{pct(t)}{{opacity:1;transform:scale(1)}}"
            f"{pct(t + 0.09)}{{opacity:0;transform:scale(1.7)}}"
            f"{pct(respawn)}{{opacity:0;transform:scale(.2)}}"
            f"{pct(respawn + 0.25)}{{opacity:1;transform:scale(1.15)}}"
            f"{pct(respawn + 0.4)},100%{{opacity:1;transform:scale(1)}}}}"
            f".{kname}{{animation:{kname} {CYCLE}s linear infinite;transform-box:fill-box;transform-origin:center}}"
        )
        col_rings, col_sparks = [], []
        for d in w["contributionDays"]:
            row = date.fromisoformat(d["date"]).isoweekday() % 7  # Sonntag oben, wie bei GitHub
            cy = gy + row * CELL
            lvl = d["contributionLevel"]
            if lvl == "NONE":
                p.append(f'<rect x="{x0 + 7}" y="{cy + 7}" width="2" height="2" fill="{COLORS["dot"]}"/>')
                continue
            col_rings.append(f'<use xlink:href="#ring" x="{x0}" y="{cy}"/>')
            col_sparks.append((x0, cy))
        if col_rings:
            p.append(f'<g class="{kname}">{"".join(col_rings)}</g>')
            for i in range(4):
                sparks = "".join(f'<use xlink:href="#sp{i}" x="{sx}" y="{sy}"/>' for sx, sy in col_sparks)
                p.append(f'<g class="sp" style="animation-delay:{t + i * 0.07:.3f}s">{sparks}</g>')

    # „ZONE CLEAR!“-Banner nach dem Einsammeln
    clear = "ZONE CLEAR!"
    cw = text_width(clear, 4)
    banner_y = H // 2 - 22
    css.append(
        f"@keyframes clr{{0%,{pct(CLEAR_IN)}{{transform:translateX(-900px)}}{pct(CLEAR_IN + 0.35)},{pct(CLEAR_OUT)}{{transform:translateX(0)}}"
        f"{pct(CLEAR_OUT + 0.3)},100%{{transform:translateX(900px)}}}}"
        f".clr{{animation:clr {CYCLE}s steps(1,end) infinite}}"
    )
    tally = f"{total} RINGS COLLECTED"
    banner = (
        f'<rect x="0" y="{banner_y - 14}" width="{W}" height="72" fill="{COLORS["navy"]}" opacity=".94"/>'
        f'<rect x="0" y="{banner_y - 14}" width="{W}" height="3" fill="{COLORS["o4"]}"/>'
        f'<rect x="0" y="{banner_y + 55}" width="{W}" height="3" fill="{COLORS["o4"]}"/>'
        + fancy_text(clear, (W - cw) // 2, banner_y, 4, ["#ffffff", "#fff3a0", "#ffd84a", "#ffb21e"], COLORS["navy"], COLORS["shadow"], 2)
        + outlined_text(tally, (W - text_width(tally, 2)) // 2, banner_y + 36, 2, "#ffffff", COLORS["navy"])
    )
    css[-1] = css[-1].replace("steps(1,end)", "cubic-bezier(.5,0,.3,1)")
    p.append(f'<g class="clr">{banner}</g>')

    # Fußzeile
    foot = f"LAST 12 MONTHS · UPDATED {date.today().isoformat()}"
    svg, _ = text_rects(foot, W - 28 - text_width(foot, 1), H - 18, 1, COLORS["dim"])
    p.append(svg)
    p.append("</g>")

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" shape-rendering="crispEdges" role="img">'
        f"<title>{total} Beiträge im letzten Jahr als goldene Ringe</title>"
        f"<style>{''.join(css)}</style><defs>{''.join(defs)}</defs>{''.join(p)}</svg>"
    )


if __name__ == "__main__":
    out = ROOT / "assets" / "rings.svg"
    out.write_text(build(fetch()))
    print(f"{out} ({out.stat().st_size // 1024} KB)")
