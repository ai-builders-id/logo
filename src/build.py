"""Build every aibuilders.id logo variant from source.

Sources (this folder):
  black.svg  - the keycap body (potrace of the original logo.png); its holes are the key face + arrow
  white.svg  - the key face (with the arrow cut out)
  SpaceGrotesk-Variable.ttf - wordmark font, set at weight 700, outlined to paths

Run:  python3 src/build.py   (needs fonttools, uharfbuzz, playwright)
"""
import re, os, json, io
from pathlib import Path
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen

SRC = Path(__file__).parent
OUT = SRC.parent

# Brand palette — taken 1:1 from ai-builders-prototype/ds.css
C = {
    "ink":   "#272C35",  # --ink   hsl(220 15% 18%)
    "cream": "#FAF7F0",  # --cream hsl(42 50% 96%)
    "kraft": "#F3EFE8",  # --kraft hsl(39 30% 93%)
    "red":   "#D92635",  # --red   hsl(355 70% 50%)
    "blue":  "#285ABD",  # --blue  hsl(220 65% 45%)
    "yellow": "#F6E9B6", # --note-yellow
}

WORD = "aibuilders.id"
TRACK = -0.015  # em, same as .brand-word in ds.css

# ---------- mark ----------
def path_d(svgfile):
    return re.search(r'<path d="([^"]+)"', (SRC / svgfile).read_text(), re.S).group(1).replace("\n", " ")

BODY, FACE = path_d("black.svg"), path_d("white.svg")
MW, MH = 3122, 2720  # potrace canvas (cropped original)

def mark(x, y, h, body, face=None):
    s = h / MH
    g = f'<g transform="translate({x:.2f},{y:.2f}) scale({s:.5f}) translate(0,{MH}) scale(0.1,-0.1)">'
    if face:
        g += f'<path fill="{face}" d="{FACE}"/>'
    g += f'<path fill="{body}" d="{BODY}"/></g>'
    return g

# ---------- wordmark ----------
font = TTFont(SRC / "SpaceGrotesk-Variable.ttf")
font = instantiateVariableFont(font, {"wght": 700})
buf = io.BytesIO(); font.save(buf); fbytes = buf.getvalue()
UPM = font["head"].unitsPerEm
gs = font.getGlyphSet()

hbf = hb.Font(hb.Face(fbytes))
hbuf = hb.Buffer(); hbuf.add_str(WORD); hbuf.guess_segment_properties()
hb.shape(hbf, hbuf, {"kern": True, "liga": False})
order = font.getGlyphOrder()

glyphs, pen_x = [], 0
for info, pos in zip(hbuf.glyph_infos, hbuf.glyph_positions):
    glyphs.append((order[info.codepoint], pen_x + pos.x_offset))
    pen_x += pos.x_advance + TRACK * UPM
pen_x -= TRACK * UPM

# outline + bounds in font units (y up)
bp = BoundsPen(gs)
word_d = []
for name, ox in glyphs:
    p = SVGPathPen(gs)
    gs[name].draw(p)
    d = p.getCommands()
    if d:
        word_d.append((ox, d))
    b = BoundsPen(gs); gs[name].draw(b)
    if b.bounds:
        x0, y0, x1, y1 = b.bounds
        bp.bounds = (x0 + ox, y0, x1 + ox, y1) if bp.bounds is None else (
            min(bp.bounds[0], x0 + ox), min(bp.bounds[1], y0), max(bp.bounds[2], x1 + ox), max(bp.bounds[3], y1))
WX0, WY0, WX1, WY1 = bp.bounds
ASC = font["OS/2"].sCapHeight or WY1  # 'b','l','d' ascender ≈ top of bounds
WY1_ = WY1

def word(x, y_top, height, fill):
    """Draw the wordmark so its ink box (ascender top → baseline/descender) spans `height` from y_top."""
    s = height / (WY1_ - WY0)
    parts = "".join(f'<path transform="translate({ox:.1f},0)" d="{d}"/>' for ox, d in word_d)
    return (f'<g fill="{fill}" transform="translate({x - WX0 * s:.2f},{y_top + WY1_ * s:.2f}) scale({s:.5f},{-s:.5f})">'
            f'{parts}</g>'), (WX1 - WX0) * s

def word_w(height):
    return (WX1 - WX0) * height / (WY1_ - WY0)

# ---------- compositions ----------
def svg(w, h, body, bg=None, rx=0):
    rect = f'<rect width="{w:.0f}" height="{h:.0f}" rx="{rx}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}">'
            f'{rect}{body}</svg>\n')

H = 1000           # mark height unit
PAD = 0.25 * H     # clear space on exported files (≈ ¼ mark height)
TXT = 0.46 * H     # wordmark ink height in horizontal lockup
GAP = 0.20 * H

def horizontal(body, face, text, bg=None, pad=PAD):
    mw = MW / MH * H
    tw = word_w(TXT)
    w, h = pad * 2 + mw + GAP + tw, pad * 2 + H
    m = mark(pad, pad, H, body, face)
    t, _ = word(pad + mw + GAP, pad + (H - TXT) / 2 + 0.04 * H, TXT, text)  # nudge: optical centre of the keycap sits low
    return svg(w, h, m + t, bg)

def stacked(body, face, text, bg=None, pad=PAD):
    mw = MW / MH * H
    th = 0.36 * H
    tw = word_w(th)
    w = pad * 2 + max(mw, tw)
    h = pad * 2 + H + 0.22 * H + th
    m = mark((w - mw) / 2, pad, H, body, face)
    t, _ = word((w - tw) / 2, pad + H + 0.22 * H, th, text)
    return svg(w, h, m + t, bg)

def mark_only(body, face, bg=None, pad=PAD, square=False, rx=0):
    mw = MW / MH * H
    if square:
        side = max(mw, H) + pad * 2
        return svg(side, side, mark((side - mw) / 2, (side - H) / 2, H, body, face), bg, rx)
    return svg(mw + pad * 2, H + pad * 2, mark(pad, pad, H, body, face), bg)

def wordmark(fill, bg=None, pad=PAD * 0.6):
    th = TXT
    tw = word_w(th)
    t, _ = word(pad, pad, th, fill)
    return svg(tw + pad * 2, th + pad * 2, t, bg)

ink, cream = C["ink"], C["cream"]
FILES = {
    # 01 — primary (light backgrounds): ink keycap, cream face
    "01-primary/aibuilders-logo-horizontal.svg": horizontal(ink, cream, ink),
    "01-primary/aibuilders-logo-stacked.svg":    stacked(ink, cream, ink),
    "01-primary/aibuilders-mark.svg":            mark_only(ink, cream),
    "01-primary/aibuilders-wordmark.svg":        wordmark(ink),
    # 02 — reversed (dark / photo backgrounds): cream keycap, ink face
    "02-reversed/aibuilders-logo-horizontal-reversed.svg": horizontal(cream, ink, cream),
    "02-reversed/aibuilders-logo-stacked-reversed.svg":    stacked(cream, ink, cream),
    "02-reversed/aibuilders-mark-reversed.svg":            mark_only(cream, ink),
    "02-reversed/aibuilders-wordmark-reversed.svg":        wordmark(cream),
    # 03 — one-colour (face knocked out to transparent) for print, stamps, embroidery, watermarks
    "03-mono/aibuilders-logo-horizontal-ink.svg":   horizontal(ink, None, ink),
    "03-mono/aibuilders-mark-ink.svg":              mark_only(ink, None),
    "03-mono/aibuilders-logo-horizontal-cream.svg": horizontal(cream, None, cream),
    "03-mono/aibuilders-mark-cream.svg":            mark_only(cream, None),
    # 04 — on brand-colour backgrounds
    "04-on-color/aibuilders-logo-horizontal-on-ink.svg":   horizontal(cream, ink, cream, bg=ink, pad=0.45 * H),
    "04-on-color/aibuilders-logo-horizontal-on-kraft.svg": horizontal(ink, cream, ink, bg=C["kraft"], pad=0.45 * H),
    "04-on-color/aibuilders-logo-horizontal-on-red.svg":   horizontal(cream, C["red"], cream, bg=C["red"], pad=0.45 * H),
    "04-on-color/aibuilders-logo-horizontal-on-blue.svg":  horizontal(cream, C["blue"], cream, bg=C["blue"], pad=0.45 * H),
    "04-on-color/aibuilders-logo-stacked-on-ink.svg":      stacked(cream, ink, cream, bg=ink, pad=0.45 * H),
    "04-on-color/aibuilders-logo-stacked-on-kraft.svg":    stacked(ink, cream, ink, bg=C["kraft"], pad=0.45 * H),
    # 05 — app icon / avatar / favicon tiles (square, mark only)
    "05-icon/aibuilders-icon-ink.svg":    mark_only(cream, ink, bg=ink, pad=0.3 * H, square=True),
    "05-icon/aibuilders-icon-kraft.svg":  mark_only(ink, cream, bg=C["kraft"], pad=0.3 * H, square=True),
    "05-icon/aibuilders-icon-red.svg":    mark_only(cream, C["red"], bg=C["red"], pad=0.3 * H, square=True),
    "05-icon/aibuilders-icon-blue.svg":   mark_only(cream, C["blue"], bg=C["blue"], pad=0.3 * H, square=True),
    "05-icon/aibuilders-icon-yellow.svg": mark_only(ink, cream, bg=C["yellow"], pad=0.3 * H, square=True),
    "05-icon/favicon.svg":                mark_only(cream, ink, bg=ink, pad=0.14 * H, square=True, rx=int(0.28 * H)),
}

for rel, content in FILES.items():
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# ---------- PNG exports ----------
from playwright.sync_api import sync_playwright

def png_jobs():
    for rel in FILES:
        if rel.endswith("favicon.svg"):
            for px in (32, 180, 512):
                yield rel, f"05-icon/favicon-{px}.png", px
        elif rel.startswith("05-icon/"):
            yield rel, rel.replace(".svg", "-1024.png"), 1024
        else:
            yield rel, rel.replace(".svg", ".png"), 2000

with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page()
    for rel, out, width in png_jobs():
        s = (OUT / rel).read_text()
        vw, vh = map(float, re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', s).groups())
        h = round(width * vh / vw)
        s = re.sub(r'width="[\d.]+" height="[\d.]+"', f'width="{width}" height="{h}"', s, count=1)
        pg.set_viewport_size({"width": width, "height": h})
        pg.set_content(f'<html><body style="margin:0;background:transparent">{s}</body></html>')
        pg.locator("svg").screenshot(path=str(OUT / out), omit_background=True)
    br.close()

print(f"{len(FILES)} SVGs written to {OUT}")
