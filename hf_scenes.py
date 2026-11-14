#!/usr/bin/env python3
"""
hf_scenes.py - the visual language. Every frame is authored HTML/CSS/SVG.

Nothing here is a stock clip or an ffmpeg pattern: each scene is a real
composition - dot-matrix maps with drawn routes, colonnades with parallax,
medallion portraits, animated timelines, counters, skylines - animated on a
seekable GSAP timeline so HyperFrames can capture any frame deterministically.

scene(kind, shot, ctx) -> (html, tweens)

tweens are local to the shot: (selector, at, duration, from_dict, to_dict, ease)
"""

import math
import random

# ---------------------------------------------------------------- palette

BG = "#0a0806"
INK = "#f2e9d6"
DIM = "#a2967f"
GOLD = "#c9a227"
BLOOD = "#7d1d1d"
STEEL = "#5d6b73"

SERIF = "Georgia, 'DejaVu Serif', 'Times New Roman', serif"
MONO = "'DejaVu Sans Mono', 'Courier New', monospace"

GRAIN = ("url(\"data:image/svg+xml;utf8,"
         "<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'>"
         "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' "
         "numOctaves='3' stitchTiles='stitch'/>"
         "<feColorMatrix type='saturate' values='0'/></filter>"
         "<rect width='300' height='300' filter='url(%23n)' opacity='0.6'/></svg>\")")

CSS = """
:root{
  --bg:%(bg)s; --ink:%(ink)s; --dim:%(dim)s; --gold:%(gold)s;
  --blood:%(blood)s; --steel:%(steel)s;
  --serif:%(serif)s; --mono:%(mono)s;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:var(--bg);}
#root{position:relative;overflow:hidden;background:var(--bg);isolation:isolate;}
.clip{position:absolute;inset:0;}
.scene{position:absolute;inset:0;overflow:hidden;background:var(--bg);}
.layer{position:absolute;inset:0;will-change:transform;}
.grain{position:absolute;inset:-8%%;background-image:%(grain)s;background-size:340px 340px;
  opacity:.07;mix-blend-mode:overlay;pointer-events:none;}
.vig{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(115%% 85%% at 50%% 45%%,rgba(0,0,0,0) 42%%,rgba(0,0,0,.42) 80%%,rgba(0,0,0,.70) 100%%);}
.frame{position:absolute;inset:52px;border:1px solid rgba(201,162,39,.20);pointer-events:none;}
.frame i{position:absolute;width:16px;height:16px;border:1px solid rgba(201,162,39,.55);}
.frame i:nth-child(1){left:-1px;top:-1px;border-right:0;border-bottom:0;}
.frame i:nth-child(2){right:-1px;top:-1px;border-left:0;border-bottom:0;}
.frame i:nth-child(3){left:-1px;bottom:-1px;border-right:0;border-top:0;}
.frame i:nth-child(4){right:-1px;bottom:-1px;border-left:0;border-top:0;}
.eyebrow{font-family:var(--mono);font-size:22px;letter-spacing:.44em;text-transform:uppercase;
  color:var(--gold);opacity:.92;}
.h1{font-family:var(--serif);font-weight:400;color:var(--ink);margin:0;}
.h2{font-family:var(--serif);font-weight:400;color:var(--ink);margin:0;}
.sub{font-family:var(--serif);font-style:italic;color:var(--dim);}
.rule{height:1px;background:linear-gradient(90deg,rgba(201,162,39,.9),rgba(201,162,39,0));}
.tag{font-family:var(--mono);font-size:17px;letter-spacing:.22em;text-transform:uppercase;color:var(--dim);}
.glow{position:absolute;border-radius:50%%;filter:blur(90px);}
.ring{fill:none;stroke:rgba(201,162,39,.28);}
.grid-dot{fill:rgba(242,233,214,.34);}
.grid-dot.on{fill:rgba(201,162,39,.95);}
.route{fill:none;stroke:var(--gold);stroke-width:3;stroke-linecap:round;
  stroke-dasharray:2000;stroke-dashoffset:2000;filter:drop-shadow(0 0 8px rgba(201,162,39,.55));}
.city{fill:var(--ink);}
.city-ring{fill:none;stroke:rgba(201,162,39,.75);stroke-width:2;}
.city-label{font-family:var(--mono);font-size:17px;letter-spacing:.2em;text-transform:uppercase;
  fill:rgba(242,233,214,.95);}
.tick{stroke:rgba(242,233,214,.40);stroke-width:1;}
.tick.on{stroke:var(--gold);}
.axis{stroke:rgba(242,233,214,.34);stroke-width:1;}
.bar{fill:var(--gold);opacity:.85;}
.bar.dim{fill:var(--steel);opacity:.6;}
"""


def css():
    return CSS % dict(bg=BG, ink=INK, dim=DIM, gold=GOLD, blood=BLOOD, steel=STEEL,
                      serif=SERIF, mono=MONO, grain=GRAIN)


# ---------------------------------------------------------------- helpers

def esc(s):
    return (str(s or "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def label_of(shot, limit=64):
    s = (shot.get("label") or shot.get("text") or shot.get("type") or "").strip()
    s = " ".join(s.split())
    return s[:limit]


def title_of(shot):
    s = label_of(shot, 80)
    if not s:
        return "The record"
    return s[0].upper() + s[1:]


def rng_for(shot):
    return random.Random(int(shot.get("seed") or 1) * 7919 + int(shot.get("shot_index") or 0))


def chrome(shot, ctx, extra=""):
    """Frame, grain, vignette - shared by every scene."""
    return (extra +
            '<div class="frame"><i></i><i></i><i></i><i></i></div>'
            '<div class="grain"></div><div class="vig"></div>')


def tw(sel, at, dur, frm, to, ease="power3.out"):
    return (sel, round(at, 3), round(dur, 3), frm, to, ease)


def base_tweens(i, shot, hold=True):
    """Fade in / out on the scene container, plus a slow camera push."""
    d = float(shot["duration_sec"])
    t = [tw("#s%d" % i, 0, min(0.55, d * 0.12), {"opacity": 0}, {"opacity": 1}, "power2.out")]
    if hold:
        t.append(tw("#s%d" % i, max(0.1, d - 0.42), 0.42, {"opacity": 1}, {"opacity": 0}, "power2.in"))
    return t


def push(sel, dur, amount=0.05):
    return tw(sel, 0, dur, {"scale": 1.0}, {"scale": 1.0 + amount}, "none")


# ---------------------------------------------------------------- title card

def sc_title(i, shot, ctx):
    d = float(shot["duration_sec"])
    title = title_of(shot)
    eyebrow = ctx.get("eyebrow") or ("Chapter %02d" % (ctx.get("chapter", 1)))
    sub = ctx.get("sub") or ""
    num = "%02d" % (ctx.get("chapter") or 1)
    html = (
        '<div class="scene" id="s%d">'
        '<div class="layer" id="s%d-bg">'
        '<div class="glow" style="width:900px;height:900px;left:510px;top:120px;'
        'background:radial-gradient(circle,rgba(201,162,39,.13),rgba(201,162,39,0) 70%%)"></div>'
        '<svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;inset:0">'
        '<circle class="ring" cx="960" cy="500" r="330"/>'
        '<circle class="ring" cx="960" cy="500" r="440" stroke-dasharray="2 14"/>'
        '<circle class="ring" cx="960" cy="500" r="560" stroke-dasharray="1 22"/>'
        '</svg></div>'
        '<div class="layer" id="s%d-cam" style="display:flex;flex-direction:column;'
        'justify-content:center;align-items:center;text-align:center;padding:0 220px">'
        '<div class="eyebrow" id="s%d-eyebrow">%s</div>'
        '<div style="height:34px"></div>'
        '<h1 class="h1" id="s%d-title" style="font-size:112px;letter-spacing:-.01em;max-width:1480px">%s</h1>'
        '<div style="height:40px"></div>'
        '<div class="rule" id="s%d-rule" style="width:520px;transform-origin:center"></div>'
        '<div style="height:34px"></div>'
        '<div class="sub" id="s%d-sub" style="font-size:30px">%s</div>'
        '</div>'
        '<div class="tag" style="position:absolute;left:96px;bottom:92px">%s</div>'
        '%s'
        '</div>'
    ) % (i, i, i, i, esc(eyebrow), i, esc(title), i, i, esc(sub), esc(num),
         chrome(shot, ctx))
    t = base_tweens(i, shot)
    t += [
        tw("#s%d-eyebrow" % i, 0.15, 0.9, {"opacity": 0, "y": -14}, {"opacity": 1, "y": 0}),
        tw("#s%d-title" % i, 0.35, 1.25, {"opacity": 0, "y": 54, "letterSpacing": "0.06em"},
           {"opacity": 1, "y": 0, "letterSpacing": "0em"}, "power4.out"),
        tw("#s%d-rule" % i, 1.05, 1.0, {"scaleX": 0, "opacity": 0}, {"scaleX": 1, "opacity": 1}, "power2.inOut"),
        tw("#s%d-sub" % i, 1.35, 1.0, {"opacity": 0, "y": 18}, {"opacity": 1, "y": 0}),
        tw("#s%d-bg svg" % i, 0, d, {"rotate": 0, "opacity": 1}, {"rotate": 3, "opacity": 1}, "none"),
        push("#s%d-cam" % i, d, 0.035),
    ]
    return html, t


# ---------------------------------------------------------------- map

BLOB = [(0.30, 0.32), (0.38, 0.24), (0.47, 0.21), (0.55, 0.25), (0.63, 0.23),
        (0.72, 0.28), (0.79, 0.37), (0.80, 0.47), (0.74, 0.57), (0.66, 0.63),
        (0.58, 0.60), (0.50, 0.65), (0.42, 0.62), (0.35, 0.54), (0.30, 0.44)]

CITIES = [
    ("Roma", 0.52, 0.44), ("Carthago", 0.45, 0.55), ("Alexandria", 0.66, 0.58),
    ("Londinium", 0.41, 0.27), ("Athenae", 0.61, 0.46), ("Antiochia", 0.73, 0.50),
    ("Massilia", 0.47, 0.38), ("Byzantium", 0.68, 0.42),
]


def _inside(x, y, poly=BLOB):
    inside = False
    n = len(poly)
    for k in range(n):
        x1, y1 = poly[k]
        x2, y2 = poly[(k + 1) % n]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1):
            inside = not inside
    return inside


def _dot_grid(w=1920, h=1080, cols=44, rows=23, x0=90, y0=90):
    out = []
    dx = (w - 2 * x0) / float(cols - 1)
    dy = (h - 2 * y0) / float(rows - 1)
    for r in range(rows):
        for c in range(cols):
            x = x0 + c * dx
            y = y0 + r * dy
            on = _inside((x - x0) / (w - 2 * x0), (y - y0) / (h - 2 * y0))
            out.append((x, y, on))
    return out


def _grid_svg():
    parts = []
    for x, y, on in _dot_grid():
        parts.append('<circle class="grid-dot%s" cx="%.1f" cy="%.1f" r="%s"/>'
                     % (" on" if on else "", x, y, "3.1" if on else "2.2"))
    return "".join(parts)


def _cities_svg(names):
    out = []
    for name, ux, uy in names:
        x = 90 + ux * 1740
        y = 90 + uy * 900
        out.append(
            '<g><circle class="city-ring" cx="%.1f" cy="%.1f" r="13"/>'
            '<circle class="city" cx="%.1f" cy="%.1f" r="4.5"/>'
            '<text class="city-label" x="%.1f" y="%.1f">%s</text></g>'
            % (x, y, x, y, x + 24, y + 6, esc(name)))
    return "".join(out)


def _route_path(points):
    d = "M %.1f %.1f" % points[0]
    for p in points[1:]:
        d += " L %.1f %.1f" % p
    return d


def sc_map(i, shot, ctx, variant="map"):
    d = float(shot["duration_sec"])
    rng = rng_for(shot)
    picks = rng.sample(CITIES, 5)
    order = sorted(picks, key=lambda c: c[1])
    pts = [(90 + c[1] * 1740, 90 + c[2] * 900) for c in order]
    route = _route_path(pts)
    title = title_of(shot)
    eyebrow = ctx.get("eyebrow") or "The map"
    html = (
        '<div class="scene" id="s%d">'
        '<div class="layer" id="s%d-cam">'
        '<svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;inset:0">'
        '<g id="s%d-grid" opacity="0">%s</g>'
        '<path class="route" id="s%d-route" d="%s"/>'
        '<g id="s%d-cities" opacity="0">%s</g>'
        '</svg></div>'
        '<div class="layer" style="padding:78px 96px;display:flex;flex-direction:column;'
        'justify-content:space-between">'
        '<div><div class="eyebrow" id="s%d-eyebrow">%s</div>'
        '<h2 class="h2" id="s%d-title" style="font-size:64px;max-width:1100px;margin-top:18px">%s</h2></div>'
        '<div class="tag" id="s%d-foot">%s</div>'
        '</div>'
        '%s'
        '</div>'
    ) % (i, i, i, _grid_svg(), i, route, i, _cities_svg(picks), i, esc(eyebrow),
         i, esc(title), i, esc("%s  ·  %d places" % (ctx.get("chapter_label") or "empire", len(picks))),
         chrome(shot, ctx))
    t = base_tweens(i, shot)
    t += [
        tw("#s%d-grid" % i, 0.1, 1.1, {"opacity": 0}, {"opacity": 1}),
        tw("#s%d-route" % i, 0.7, max(1.2, d * 0.5), {"strokeDashoffset": 2000}, {"strokeDashoffset": 0}, "none"),
        tw("#s%d-cities" % i, 1.1, 0.9, {"opacity": 0, "y": 10}, {"opacity": 1, "y": 0}),
        tw("#s%d-eyebrow" % i, 0.2, 0.8, {"opacity": 0, "x": -18}, {"opacity": 1, "x": 0}),
        tw("#s%d-title" % i, 0.4, 1.0, {"opacity": 0, "y": 26}, {"opacity": 1, "y": 0}),
        tw("#s%d-foot" % i, 1.5, 0.8, {"opacity": 0}, {"opacity": 1}),
        push("#s%d-cam" % i, d, 0.07),
    ]
    return html, t


# ---------------------------------------------------------------- timeline

def sc_timeline(i, shot, ctx):
    d = float(shot["duration_sec"])
    marks = ctx.get("marks") or ["Origins", "The Republic", "The Generals",
                                 "The Empire", "The Crisis", "The Fall"]
    n = min(len(marks), 6)
    marks = marks[:n]
    x0, x1, y = 220.0, 1700.0, 560.0
    step = (x1 - x0) / float(n - 1)
    ticks, labels = [], []
    for k, m in enumerate(marks):
        x = x0 + k * step
        ticks.append('<line class="tick" id="s%d-t%d" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                     % (i, k, x, y - 16, x, y + 16))
        up = -1 if k % 2 == 0 else 1
        labels.append(
            '<text class="city-label" id="s%d-l%d" x="%.1f" y="%.1f" text-anchor="middle">%s</text>'
            % (i, k, x, y + (up * 64) + (0 if up > 0 else 0), esc(m[:26])))
    title = title_of(shot)
    html = (
        '<div class="scene" id="s%d">'
        '<div class="layer" id="s%d-cam">'
        '<svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;inset:0">'
        '<line class="axis" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" id="s%d-axis"/>'
        '%s%s'
        '<line class="tick on" id="s%d-head" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
        '<circle id="s%d-knob" cx="%.1f" cy="%.1f" r="9" fill="%s"/>'
        '</svg></div>'
        '<div class="layer" style="padding:88px 96px">'
        '<div class="eyebrow" id="s%d-eyebrow">%s</div>'
        '<h2 class="h2" id="s%d-title" style="font-size:66px;max-width:1200px;margin-top:18px">%s</h2>'
        '</div>'
        '%s'
        '</div>'
    ) % (i, i, x0, y, x1, y, i, "".join(ticks), "".join(labels), i,
         x0, y - 60, x0, y + 60, i, x0, y, GOLD, i, esc(ctx.get("eyebrow") or "Chronology"),
         i, esc(title), chrome(shot, ctx))
    t = base_tweens(i, shot)
    t.append(tw("#s%d-axis" % i, 0.15, 0.9, {"opacity": 0, "scaleX": 0}, {"opacity": 1, "scaleX": 1}))
    t.append(tw("#s%d-head" % i, 0.3, max(1.4, d * 0.62), {"x1": x0, "x2": x0},
                {"x1": x1, "x2": x1}, "power1.inOut"))
    t.append(tw("#s%d-knob" % i, 0.3, max(1.4, d * 0.62), {"cx": x0}, {"cx": x1}, "power1.inOut"))
    t.append(tw("#s%d-eyebrow" % i, 0.2, 0.7, {"opacity": 0}, {"opacity": 1}))
    t.append(tw("#s%d-title" % i, 0.35, 0.9, {"opacity": 0, "y": 24}, {"opacity": 1, "y": 0}))
    for k in range(n):
        at = 0.5 + (d * 0.6) * (k / float(max(1, n - 1)))
        t.append(tw("#s%d-t%d" % (i, k), at, 0.4, {"opacity": 0, "scaleY": 0.2},
                    {"opacity": 1, "scaleY": 1}))
        t.append(tw("#s%d-l%d" % (i, k), at + 0.1, 0.5, {"opacity": 0, "y": 8}, {"opacity": 1, "y": 0}))
    return html, t


# ---------------------------------------------------------------- colonnade

def sc_columns(i, shot, ctx):
    d = float(shot["duration_sec"])
    rng = rng_for(shot)
    title = title_of(shot)

    def colonnade(y_base, h, w, gap, n, colour, opacity):
        parts = []
        total = n * gap
        x0 = 960 - total / 2.0
        for k in range(n):
            x = x0 + k * gap
            parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" opacity="%s"/>'
                         % (x, y_base - h, w, h, colour, opacity))
            parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" opacity="%s"/>'
                         % (x - w * 0.22, y_base - h - 16, w * 1.44, 18, colour, opacity))
            parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" opacity="%s"/>'
                         % (x - w * 0.18, y_base - 12, w * 1.36, 14, colour, opacity))
        return "".join(parts)

    back = colonnade(880, 430, 26, 150, 9, "#4a3624", 0.95)
    mid = colonnade(950, 560, 46, 300, 5, "#2b1e13", 1)
    html = (
        '<div class="scene" id="s%d">'
        '<div class="layer" id="s%d-sky" style="background:linear-gradient(180deg,#1a1208 0%%,#2a1d0e 55%%,#0a0806 100%%)">'
        '<div class="glow" style="width:1200px;height:700px;left:360px;top:-120px;'
        'background:radial-gradient(circle,rgba(201,162,39,.16),rgba(201,162,39,0) 70%%)"></div></div>'
        '<div class="layer" id="s%d-back"><svg width="1920" height="1080" viewBox="0 0 1920 1080" '
        'style="position:absolute;inset:0">%s</svg></div>'
        '<div class="layer" id="s%d-mid"><svg width="1920" height="1080" viewBox="0 0 1920 1080" '
        'style="position:absolute;inset:0">%s</svg></div>'
        '<div class="layer" id="s%d-shaft" style="background:linear-gradient(102deg,'
        'rgba(255,225,160,0) 38%%,rgba(255,225,160,.09) 47%%,rgba(255,225,160,.02) 56%%,'
        'rgba(255,225,160,0) 62%%)"></div>'
        '<div class="layer" style="padding:88px 96px">'
        '<div class="eyebrow" id="s%d-eyebrow">%s</div>'
        '<h2 class="h2" id="s%d-title" style="font-size:64px;max-width:980px;margin-top:18px;'
        'text-shadow:0 4px 40px rgba(0,0,0,.8)">%s</h2></div>'
        '%s'
        '</div>'
    ) % (i, i, i, back, i, mid, i, i, esc(ctx.get("eyebrow") or "The city"), i, esc(title),
         chrome(shot, ctx))
    t = base_tweens(i, shot)
    t += [
        tw("#s%d-back" % i, 0, d, {"scale": 1.0, "y": 0}, {"scale": 1.03, "y": -6}, "none"),
        tw("#s%d-mid" % i, 0, d, {"scale": 1.02, "y": 0}, {"scale": 1.10, "y": 14}, "none"),
        tw("#s%d-shaft" % i, 0, d, {"x": -260, "opacity": .5}, {"x": 260, "opacity": 1}, "none"),
        tw("#s%d-eyebrow" % i, 0.25, 0.8, {"opacity": 0, "y": -12}, {"opacity": 1, "y": 0}),
        tw("#s%d-title" % i, 0.5, 1.1, {"opacity": 0, "y": 34}, {"opacity": 1, "y": 0}),
    ]
    return html, t


# ---------------------------------------------------------------- medallion

def sc_portrait(i, shot, ctx):
    d = float(shot["duration_sec"])
    title = title_of(shot)
    rng = rng_for(shot)
    leaves = []
    for side in (-1, 1):
        for k in range(14):
            ang = math.radians(-58 + k * 8.4)
            r = 210
            x = 960 + side * r * math.cos(ang)
            y = 470 + r * math.sin(ang)
            rot = math.degrees(ang) + (90 if side < 0 else -90)
            leaves.append('<ellipse cx="%.1f" cy="%.1f" rx="26" ry="9" fill="none" '
                          'stroke="rgba(201,162,39,.55)" stroke-width="1.4" '
                          'transform="rotate(%.1f %.1f %.1f)"/>'
                          % (x, y, rot + (28 if side < 0 else -28), x, y))
    html = (
        '<div class="scene" id="s%d">'
        '<div class="layer" id="s%d-cam">'
        '<div class="glow" style="width:760px;height:760px;left:580px;top:110px;'
        'background:radial-gradient(circle,rgba(201,162,39,.14),rgba(201,162,39,0) 68%%)"></div>'
        '<svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;inset:0">'
        '<circle cx="960" cy="470" r="232" fill="none" stroke="rgba(201,162,39,.28)" stroke-width="1.5"/>'
        '<circle cx="960" cy="470" r="252" fill="none" stroke="rgba(201,162,39,.14)" stroke-width="1"/>'
        '<g id="s%d-wreath">%s</g>'
        '<path d="M 960 300 C 900 340 888 420 900 470 C 908 520 880 560 900 600 L 960 630 '
        'L 1020 600 C 1040 560 1012 520 1020 470 C 1032 420 1020 340 960 300 Z" '
        'fill="rgba(242,233,214,.14)" stroke="rgba(242,233,214,.58)" stroke-width="2"/>'
        '<circle cx="960" cy="470" r="300" fill="none" stroke="rgba(201,162,39,.10)"/>'
        '</svg></div>'
        '<div class="layer" style="position:absolute;left:0;right:0;top:790px;text-align:center">'
        '<div class="eyebrow" id="s%d-eyebrow">%s</div>'
        '<h2 class="h2" id="s%d-title" style="font-size:72px;margin-top:16px">%s</h2>'
        '</div>'
        '%s'
        '</div>'
    ) % (i, i, i, "".join(leaves), i, esc(ctx.get("eyebrow") or "The person"), i, esc(title),
         chrome(shot, ctx))
    t = base_tweens(i, shot)
    t += [
        tw("#s%d-wreath" % i, 0, d, {"rotate": -6, "opacity": 0},
           {"rotate": 6, "opacity": 1}, "none"),
        tw("#s%d-cam svg" % i, 0, d, {"scale": 1.0}, {"scale": 1.06}, "none"),
        tw("#s%d-eyebrow" % i, 0.5, 0.9, {"opacity": 0, "y": 14}, {"opacity": 1, "y": 0}),
        tw("#s%d-title" % i, 0.75, 1.1, {"opacity": 0, "y": 26}, {"opacity": 1, "y": 0}),
    ]
    return html, t


# ---------------------------------------------------------------- quote

def sc_quote(i, shot, ctx):
    d = float(shot["duration_sec"])
    words = (label_of(shot, 70) or "The record speaks").split()
    spans = "".join('<span class="qw" id="s%d-w%d" style="display:inline-block">%s</span> '
                    % (i, k, esc(w)) for k, w in enumerate(words))
    html = (
        '<div class="scene" id="s%d">'
        '<div class="layer" style="display:flex;align-items:center;justify-content:center;'
        'padding:0 240px">'
        '<div style="max-width:1400px">'
        '<div style="font-family:var(--serif);font-size:200px;line-height:.6;color:%s;'
        'opacity:.5;height:90px" id="s%d-mark">&ldquo;</div>'
        '<h2 class="h2" id="s%d-q" style="font-size:96px;line-height:1.12;font-style:italic">%s</h2>'
        '<div style="height:44px"></div>'
        '<div class="rule" id="s%d-rule" style="width:340px;transform-origin:left"></div>'
        '<div style="height:22px"></div>'
        '<div class="tag" id="s%d-attr">%s</div>'
        '</div></div>'
        '%s'
        '</div>'
    ) % (i, GOLD, i, i, spans, i, i, esc(ctx.get("chapter_label") or "from the record"),
         chrome(shot, ctx))
    t = base_tweens(i, shot)
    t.append(tw("#s%d-mark" % i, 0.15, 0.8, {"opacity": 0, "y": -20}, {"opacity": .5, "y": 0}))
    for k in range(len(words)):
        t.append(tw("#s%d-w%d" % (i, k), 0.35 + k * 0.16, 0.55,
                    {"opacity": 0, "y": 26, "filter": "blur(6px)"},
                    {"opacity": 1, "y": 0, "filter": "blur(0px)"}))
    t.append(tw("#s%d-rule" % i, 0.6 + len(words) * 0.16, 0.8,
                {"scaleX": 0}, {"scaleX": 1}, "power2.inOut"))
    t.append(tw("#s%d-attr" % i, 0.9 + len(words) * 0.16, 0.7, {"opacity": 0}, {"opacity": 1}))
    return html, t


# ---------------------------------------------------------------- counter / bars

def sc_stat(i, shot, ctx):
    d = float(shot["duration_sec"])
    rng = rng_for(shot)
    big = rng.choice([12, 23, 47, 68, 112, 214, 476, 1200])
    suffix = rng.choice(["", "", "", " years", "%"])
    marks = (ctx.get("marks") or ["A", "B", "C", "D"])[:4]
    bars = []
    x0, y0, wmax = 260.0, 760.0, 1080.0
    for k, m in enumerate(marks):
        v = 0.35 + rng.random() * 0.6
        y = y0 + k * 62
        bars.append('<rect class="bar%s" id="s%d-b%d" x="%.1f" y="%.1f" width="0" height="26" rx="2"/>'
                    % (" dim" if k % 2 else "", i, k, x0, y))
        bars.append('<text class="city-label" x="%.1f" y="%.1f" style="font-size:15px">%s</text>'
                    % (x0, y - 10, esc(m[:30])))
        bars.append('<text class="city-label" id="s%d-v%d" x="%.1f" y="%.1f" text-anchor="end" '
                    'style="font-size:15px;fill:%s">%d</text>'
                    % (i, k, x0 + wmax, y - 10, GOLD, int(v * 100)))
    html = (
        '<div class="scene" id="s%d">'
        '<div class="layer" style="padding:96px">'
        '<div class="eyebrow" id="s%d-eyebrow">%s</div>'
        '<div id="s%d-num" style="font-family:var(--serif);font-size:250px;line-height:1;'
        'color:%s;margin-top:8px">0</div>'
        '<div class="sub" id="s%d-cap" style="font-size:32px;margin-top:8px">%s</div>'
        '</div>'
        '<div class="layer"><svg width="1920" height="1080" viewBox="0 0 1920 1080" '
        'style="position:absolute;inset:0">%s</svg></div>'
        '%s'
        '</div>'
    ) % (i, i, esc(ctx.get("eyebrow") or "By the numbers"), i, GOLD, i, esc(title_of(shot)),
         "".join(bars), chrome(shot, ctx))
    t = base_tweens(i, shot)
    t.append(tw("#s%d-eyebrow" % i, 0.2, 0.7, {"opacity": 0}, {"opacity": 1}))
    t.append(tw("#s%d-num" % i, 0.35, min(2.6, d * 0.6), {"innerText": 0, "opacity": 0},
                {"innerText": big, "opacity": 1, "snap": {"innerText": 1}}, "power2.out"))
    t.append(tw("#s%d-cap" % i, 0.7, 0.8, {"opacity": 0, "y": 14}, {"opacity": 1, "y": 0}))
    for k, m in enumerate(marks):
        v = 0.35 + rng.random() * 0.6
        t.append(tw("#s%d-b%d" % (i, k), 0.8 + k * 0.22, 1.1, {"width": 0},
                    {"width": round(1080 * v, 1)}, "power2.out"))
    return html, t


# ---------------------------------------------------------------- battle

def sc_battle(i, shot, ctx):
    d = float(shot["duration_sec"])
    rng = rng_for(shot)
    ax, ay = 380, 420
    bx, by = 1540, 660
    left = "M %d %d C 700 360, 860 400, 940 520" % (ax, ay)
    right = "M %d %d C 1240 720, 1080 680, 990 560" % (bx, by)
    units = []
    for k in range(6):
        units.append('<rect x="%d" y="%d" width="18" height="18" fill="rgba(201,162,39,.85)"/>'
                     % (300 + k * 34, 470))
        units.append('<rect x="%d" y="%d" width="18" height="18" fill="rgba(125,29,29,.75)"/>'
                     % (1520 + k * 34, 700))
    html = (
        '<div class="scene" id="s%d">'
        '<div class="layer" id="s%d-cam">'
        '<svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;inset:0">'
        '<g opacity=".22">%s</g>'
        '<path class="route" id="s%d-a" d="%s" stroke="%s"/>'
        '<path class="route" id="s%d-b" d="%s" stroke="%s"/>'
        '<circle id="s%d-clash" cx="965" cy="540" r="0" fill="none" stroke="rgba(255,214,120,.9)" stroke-width="3"/>'
        '</svg></div>'
        '<div class="layer" style="padding:88px 96px">'
        '<div class="eyebrow" id="s%d-eyebrow">%s</div>'
        '<h2 class="h2" id="s%d-title" style="font-size:62px;max-width:900px;margin-top:16px">%s</h2>'
        '</div>'
        '%s'
        '</div>'
    ) % (i, i, "".join(units), i, left, GOLD, i, right, BLOOD, i, i,
         esc(ctx.get("eyebrow") or "The clash"), i, esc(title_of(shot)), chrome(shot, ctx))
    t = base_tweens(i, shot)
    t += [
        tw("#s%d-a" % i, 0.2, 1.5, {"strokeDashoffset": 2000}, {"strokeDashoffset": 0}, "none"),
        tw("#s%d-b" % i, 0.5, 1.5, {"strokeDashoffset": 2000}, {"strokeDashoffset": 0}, "none"),
        tw("#s%d-clash" % i, 1.9, 1.2, {"r": 0, "opacity": 1}, {"r": 160, "opacity": 0}, "power2.out"),
        tw("#s%d-eyebrow" % i, 0.25, 0.7, {"opacity": 0}, {"opacity": 1}),
        tw("#s%d-title" % i, 0.45, 0.9, {"opacity": 0, "y": 22}, {"opacity": 1, "y": 0}),
        push("#s%d-cam" % i, d, 0.05),
    ]
    return html, t


# ---------------------------------------------------------------- coin

def sc_artifact(i, shot, ctx):
    d = float(shot["duration_sec"])
    html = (
        '<div class="scene" id="s%d">'
        '<div class="layer" id="s%d-cam">'
        '<div class="glow" style="width:900px;height:900px;left:510px;top:90px;'
        'background:radial-gradient(circle,rgba(201,162,39,.13),rgba(201,162,39,0) 70%%)"></div>'
        '<svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;inset:0">'
        '<ellipse cx="960" cy="470" rx="420" ry="120" fill="none" stroke="rgba(201,162,39,.16)" '
        'stroke-dasharray="3 12"/>'
        '<g id="s%d-coin">'
        '<circle cx="960" cy="470" r="230" fill="#3a2a15" stroke="rgba(201,162,39,.75)" stroke-width="6"/>'
        '<circle cx="960" cy="470" r="196" fill="none" stroke="rgba(201,162,39,.45)" stroke-width="2"/>'
        '<path d="M 960 330 C 912 372 900 430 908 470 C 914 512 892 546 910 580 L 960 606 '
        'L 1010 580 C 1028 546 1006 512 1012 470 C 1020 430 1008 372 960 330 Z" '
        'fill="rgba(201,162,39,.28)" stroke="rgba(255,225,160,.6)" stroke-width="2"/>'
        '<g opacity=".7">%s</g>'
        '</g>'
        '<rect id="s%d-sheen" x="-300" y="180" width="220" height="600" '
        'fill="rgba(255,240,200,.16)" transform="rotate(14 960 470)"/>'
        '</svg></div>'
        '<div class="layer" style="position:absolute;left:0;right:0;top:800px;text-align:center">'
        '<div class="eyebrow" id="s%d-eyebrow">%s</div>'
        '<h2 class="h2" id="s%d-title" style="font-size:64px;margin-top:14px">%s</h2>'
        '</div>'
        '%s'
        '</div>'
    ) % (i, i, i,
         "".join('<line x1="%d" y1="470" x2="%d" y2="470" stroke="rgba(255,225,160,.35)" '
                 'stroke-width="1"/>' % (960 + 210 * math.cos(a), 960 + 236 * math.cos(a))
                 for a in [k * math.pi / 12 for k in range(24)]),
         i, i, esc(ctx.get("eyebrow") or "The object"), i, esc(title_of(shot)), chrome(shot, ctx))
    t = base_tweens(i, shot)
    t += [
        tw("#s%d-coin" % i, 0, d, {"rotateY": 0, "scale": 1.0},
           {"rotateY": 26, "scale": 1.06}, "none"),
        tw("#s%d-sheen" % i, 0, d * 0.8, {"x": -320}, {"x": 2000}, "none"),
        tw("#s%d-eyebrow" % i, 0.35, 0.8, {"opacity": 0}, {"opacity": 1}),
        tw("#s%d-title" % i, 0.6, 1.0, {"opacity": 0, "y": 22}, {"opacity": 1, "y": 0}),
    ]
    return html, t


# ---------------------------------------------------------------- skyline

def sc_city(i, shot, ctx):
    d = float(shot["duration_sec"])
    rng = rng_for(shot)

    def skyline(base, hmin, hmax, colour, opacity, n, wmin, wmax):
        parts = []
        x = -60
        while x < 1980:
            w = rng.randint(wmin, wmax)
            h = rng.randint(hmin, hmax)
            parts.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" opacity="%s"/>'
                         % (x, base - h, w, h, colour, opacity))
            if rng.random() < 0.4:
                parts.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" opacity="%s"/>'
                             % (x + w // 3, base - h - 26, max(8, w // 4), 26, colour, opacity))
            x += w + rng.randint(6, 26)
        return "".join(parts)

    back = skyline(880, 120, 320, "#38281a", 1, 40, 30, 90)
    mid = skyline(980, 200, 460, "#241a10", 1, 26, 50, 130)
    smoke = "".join('<ellipse class="sm" cx="%d" cy="%d" rx="60" ry="30" fill="rgba(120,110,95,.10)"/>'
                    % (rng.randint(200, 1720), rng.randint(420, 620)) for _ in range(6))
    html = (
        '<div class="scene" id="s%d">'
        '<div class="layer" style="background:linear-gradient(180deg,#241708 0%%,#3a2410 40%%,#0a0806 100%%)">'
        '<div class="glow" style="width:1400px;height:500px;left:260px;top:180px;'
        'background:radial-gradient(circle,rgba(201,162,39,.14),rgba(201,162,39,0) 70%%)"></div></div>'
        '<div class="layer" id="s%d-smoke"><svg width="1920" height="1080" viewBox="0 0 1920 1080" '
        'style="position:absolute;inset:0">%s</svg></div>'
        '<div class="layer" id="s%d-back"><svg width="1920" height="1080" viewBox="0 0 1920 1080" '
        'style="position:absolute;inset:0">%s</svg></div>'
        '<div class="layer" id="s%d-mid"><svg width="1920" height="1080" viewBox="0 0 1920 1080" '
        'style="position:absolute;inset:0">%s</svg></div>'
        '<div class="layer" style="padding:88px 96px">'
        '<div class="eyebrow" id="s%d-eyebrow">%s</div>'
        '<h2 class="h2" id="s%d-title" style="font-size:62px;max-width:980px;margin-top:16px;'
        'text-shadow:0 4px 40px rgba(0,0,0,.85)">%s</h2></div>'
        '%s'
        '</div>'
    ) % (i, i, smoke, i, back, i, mid, i, esc(ctx.get("eyebrow") or "The city"), i,
         esc(title_of(shot)), chrome(shot, ctx))
    t = base_tweens(i, shot)
    t += [
        tw("#s%d-back" % i, 0, d, {"scale": 1.0, "x": 0}, {"scale": 1.02, "x": -14}, "none"),
        tw("#s%d-mid" % i, 0, d, {"scale": 1.02, "x": 0}, {"scale": 1.07, "x": 26}, "none"),
        tw("#s%d-smoke" % i, 0, d, {"y": 30, "opacity": .8}, {"y": -70, "opacity": .25}, "none"),
        tw("#s%d-eyebrow" % i, 0.25, 0.8, {"opacity": 0}, {"opacity": 1}),
        tw("#s%d-title" % i, 0.5, 1.0, {"opacity": 0, "y": 26}, {"opacity": 1, "y": 0}),
    ]
    return html, t


SCENES = {
    "title": sc_title,
    "map": sc_map,
    "timeline": sc_timeline,
    "columns": sc_columns,
    "portrait": sc_portrait,
    "quote": sc_quote,
    "stat": sc_stat,
    "battle": sc_battle,
    "artifact": sc_artifact,
    "city": sc_city,
}


def scene(kind, i, shot, ctx):
    fn = SCENES.get(kind) or sc_map
    return fn(i, shot, ctx)
