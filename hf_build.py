#!/usr/bin/env python3
"""
hf_build.py - turn one chunk of a plan into a real HyperFrames composition.

Every shot becomes a clip on one seekable GSAP timeline. Nothing is
pre-rendered and nothing is an ffmpeg pattern: the HTML *is* the animation,
and HyperFrames captures frames from it in Chrome.

build(plan, chunk, outdir) -> Path to the composition's index.html
"""

import json
import shutil
from pathlib import Path

import hf_scenes

# properties that must be written as SVG attributes, not CSS
SVG_ATTRS = ("x1", "x2", "y1", "y2", "cx", "cy", "r", "width", "height", "d")

FPS = 30


def _split(d):
    css, attr = {}, {}
    for k, v in (d or {}).items():
        if k in SVG_ATTRS:
            attr[k] = v
        else:
            css[k] = v
    return css, attr


def _size(plan):
    size = str(plan.get("size") or "1920x1080")
    try:
        w, h = [int(x) for x in size.lower().split("x")]
    except Exception:
        w, h = 1920, 1080
    return w, h


def _chapters(plan):
    """plan['chapters'] may be a list of dicts or a list of strings."""
    out = []
    for k, c in enumerate(plan.get("chapters") or []):
        if isinstance(c, dict):
            out.append({
                "index": int(c.get("index", k + 1)),
                "title": c.get("title") or "",
                "marks": [str(m) for m in (c.get("marks") or [])][:6],
            })
        else:
            out.append({"index": k + 1, "title": str(c), "marks": []})
    return out


def shot_ctx(plan, shot, chapters):
    """The public-safe chapter context a scene needs, with sane fallbacks."""
    ch = shot.get("chapter")
    try:
        ch = int(ch) if ch is not None else 1
    except Exception:
        ch = 1
    entry = next((c for c in chapters if c["index"] == ch), None)
    if entry is None and chapters:
        entry = chapters[min(ch - 1, len(chapters) - 1)]
    title = (entry or {}).get("title") or ""
    marks = [str(m) for m in (shot.get("marks") or (entry or {}).get("marks") or [])][:6]
    if len(marks) < 2:
        marks = [m for m in ("Origins", "The Republic", "The Generals",
                             "The Empire", "The Crisis", "The Fall")][:6]
    return {
        "chapter": ch,
        "chapter_label": title or ("Chapter %02d" % ch),
        "eyebrow": shot.get("eyebrow") or (("Chapter %02d  ·  %s" % (ch, title)) if title
                                           else ("Chapter %02d" % ch)),
        "sub": shot.get("sub") or "",
        "marks": marks,
    }


def build(plan, chunk, outdir):
    outdir = Path(outdir)
    if outdir.exists():
        shutil.rmtree(outdir, ignore_errors=True)
    outdir.mkdir(parents=True, exist_ok=True)

    w, h = _size(plan)
    chapters = _chapters(plan)
    shots = list(chunk.get("shots") or [])
    if not shots:
        raise RuntimeError("chunk has no shots")

    clips, tweens, counters = [], [], []
    cursor = 0.0
    for k, shot in enumerate(shots):
        d = round(float(shot.get("duration_sec") or 0), 3)
        if d <= 0:
            continue
        kind = shot.get("type") or "map"
        html, local = hf_scenes.scene(kind, k, dict(shot, duration_sec=d),
                                      shot_ctx(plan, shot, chapters))
        clips.append('<section class="clip" id="clip%d" data-start="%.3f" data-duration="%.3f">%s</section>'
                     % (k, cursor, d, html))
        for (sel, at, dur, frm, to, ease) in local:
            f_css, f_attr = _split(frm)
            t_css, t_attr = _split(to)
            num = None
            if "innerText" in f_css or "innerText" in t_css:
                num = int(t_css.pop("innerText", 0))
                f_css.pop("innerText", None)
                f_css.pop("snap", None)
                t_css.pop("snap", None)
            if num is not None:
                counters.append([sel, round(cursor + at, 3), round(dur, 3), num])
            if f_css or f_attr:
                tweens.append([sel, round(cursor + at, 3), round(dur, 3),
                               f_css, t_css, ease, f_attr, t_attr])
            elif t_attr:
                tweens.append([sel, round(cursor + at, 3), round(dur, 3),
                               {}, {}, ease, {}, t_attr])
        cursor += d

    total = round(cursor, 3)
    scale = min(w / 1920.0, h / 1080.0)
    stage = ('<div id="stage" style="position:absolute;left:0;top:0;width:1920px;height:1080px;'
             'transform-origin:0 0;transform:scale(%.6f)">%s</div>' % (scale, "".join(clips)))

    data = json.dumps({"tweens": tweens, "counters": counters}, ensure_ascii=False)
    data = data.replace("</", "<\\/")

    html = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=%(w)d, height=%(h)d"/>
<title>%(slug)s %(chunk)s</title>
<style>
%(css)s
</style>
</head>
<body>
<div id="root" data-composition-id="film" data-start="0" data-width="%(w)d" data-height="%(h)d"
     data-fps="%(fps)d" data-duration="%(total).3f">%(stage)s</div>
<script src="gsap.min.js"></script>
<script>
(function(){
  var D = %(data)s;
  var tl = gsap.timeline({paused: true});
  var seen = {};
  D.tweens.forEach(function(t){
    var sel = t[0], at = t[1], dur = t[2], fcss = t[3], tcss = t[4], ease = t[5] || "power3.out";
    var fattr = t[6] || {}, tattr = t[7] || {};
    if (!seen[sel]) {
      seen[sel] = 1;
      if (Object.keys(fcss).length) tl.set(sel, fcss, 0);
      if (Object.keys(fattr).length) tl.set(sel, {attr: fattr}, 0);
    }
    var vars = {}, k;
    for (k in tcss) vars[k] = tcss[k];
    if (Object.keys(tattr).length) vars.attr = tattr;
    vars.duration = dur;
    vars.ease = ease;
    tl.to(sel, vars, at);
  });
  D.counters.forEach(function(c){
    var box = {v: 0};
    tl.to(box, {v: c[3], duration: c[2], ease: "power2.out", onUpdate: function(){
      var el = document.querySelector(c[0]);
      if (el) el.textContent = Math.round(box.v).toLocaleString("en-US");
    }}, c[1]);
  });
  window.__timelines = window.__timelines || {};
  window.__timelines["film"] = tl;
})();
</script>
</body>
</html>
""" % {
        "slug": plan.get("slug") or "film",
        "chunk": chunk.get("index"),
        "css": hf_scenes.css(),
        "total": total,
        "w": w,
        "h": h,
        "fps": FPS,
        "stage": stage,
        "data": data,
    }

    src = Path(__file__).parent / "gsap.min.js"
    if not src.exists():
        raise RuntimeError("gsap.min.js missing next to hf_build.py")
    shutil.copyfile(src, outdir / "gsap.min.js")

    index = outdir / "index.html"
    with open(index, "w", encoding="utf-8") as f:
        f.write(html)
    print("composition: %s (%d shots, %.2fs, %dx%d)" % (index, len(clips), total, w, h))
    return index


def build_chunk(plan, index, work_root):
    chunk = next((c for c in plan["chunks"] if int(c["index"]) == int(index)), None)
    if chunk is None:
        raise RuntimeError("chunk %s not in plan" % index)
    outdir = Path(work_root) / ("comp_%02d" % int(index))
    build(plan, chunk, outdir)
    return outdir, float(chunk["duration_sec"])
