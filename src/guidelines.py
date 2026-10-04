"""Render the illustration PNGs used by README.md into guidelines/.

Run after build.py:  python3 src/guidelines.py
"""
from pathlib import Path
import re
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "guidelines"
OUT.mkdir(exist_ok=True)

INK, CREAM, KRAFT, RED, BLUE, YELLOW = "#272C35", "#FAF7F0", "#F3EFE8", "#D92635", "#285ABD", "#F6E9B6"

def svg(rel):
    return (ROOT / rel).read_text()

def uri(rel):
    return (ROOT / rel).as_uri()

BASE = f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
body{{margin:0;font-family:'Space Grotesk',sans-serif;color:{INK};background:{KRAFT}}}
.cap{{font-size:22px;font-weight:500;margin-top:14px}}
.sub{{font-size:17px;opacity:.65;margin-top:4px}}
</style>"""

PAGES = {}

vbw = float(re.search(r'viewBox="0 0 ([\d.]+)', svg("01-primary/aibuilders-logo-horizontal.svg")).group(1))
PADPX = 820 * 250 / vbw
# --- clear space: horizontal lockup with its ¼-height padding shown as a dashed zone
PAGES["clear-space.png"] = (1400, 340, BASE + f"""
<div style="padding:60px;display:flex;gap:60px;align-items:center">
  <div style="position:relative;background:{CREAM};outline:3px dashed {RED};outline-offset:-3px">
    <img src="{uri('01-primary/aibuilders-logo-horizontal.svg')}" style="display:block;width:820px">
    <div style="position:absolute;left:0;top:0;width:{PADPX:.0f}px;height:100%;background:repeating-linear-gradient(45deg,{RED}22 0 8px,transparent 8px 16px)"></div>
    <div style="position:absolute;right:0;top:0;width:{PADPX:.0f}px;height:100%;background:repeating-linear-gradient(45deg,{RED}22 0 8px,transparent 8px 16px)"></div>
    <div style="position:absolute;left:0;top:0;width:100%;height:{PADPX:.0f}px;background:repeating-linear-gradient(45deg,{RED}22 0 8px,transparent 8px 16px)"></div>
    <div style="position:absolute;left:0;bottom:0;width:100%;height:{PADPX:.0f}px;background:repeating-linear-gradient(45deg,{RED}22 0 8px,transparent 8px 16px)"></div>
  </div>
  <div style="max-width:380px">
    <div style="font-size:34px;font-weight:700">Clear space = ¼ × keycap height</div>
    <div class="sub" style="font-size:20px;margin-top:12px">Nothing — text, edges, other logos — enters the hatched zone. Every exported file already includes it.</div>
  </div>
</div>""")

# --- misuse grid
def dont(inner, label, bg=KRAFT):
    return (f'<div><div style="height:220px;background:{bg};display:grid;place-items:center;overflow:hidden;'
            f'border-radius:10px;position:relative">{inner}'
            f'<div style="position:absolute;top:10px;right:12px;width:34px;height:34px;border-radius:50%;background:{RED};'
            f'color:#fff;font:700 22px/34px sans-serif;text-align:center">✕</div></div>'
            f'<div class="cap">{label}</div></div>')

H = uri("01-primary/aibuilders-logo-horizontal.svg")
HR = uri("02-reversed/aibuilders-logo-horizontal-reversed.svg")
DONTS = [
    dont(f'<img src="{H}" style="width:220px;transform:scale(1.35,0.6)">', "Don't stretch or squash"),
    dont(f'<img src="{H}" style="width:300px;transform:rotate(-12deg)">', "Don't rotate"),
    dont(f'<img src="{H}" style="width:300px;filter:hue-rotate(140deg) saturate(8)">', "Don't recolour off-palette"),
    dont(f'<img src="{H}" style="width:300px;filter:drop-shadow(8px 8px 6px rgba(0,0,0,.6))">', "Don't add effects or shadows"),
    dont(f'<img src="{uri("03-mono/aibuilders-logo-horizontal-ink.svg")}" style="width:300px">', "Don't drop the outline on dark", bg=INK),
    dont(f'<img src="{HR}" style="width:300px">', "Don't put reversed on light", bg=CREAM),
    dont(f'<div style="font:700 34px \'Space Grotesk\';white-space:nowrap;display:flex;align-items:center;gap:10px"><img src="{uri("01-primary/aibuilders-mark.svg")}" style="height:48px">AI Builders ID</div>', "Don't retype or change case"),
    dont(f'<img src="{H}" style="width:300px">', "Don't use busy backgrounds",
         bg=f"repeating-linear-gradient(60deg,{YELLOW} 0 22px,{BLUE} 22px 44px,{RED} 44px 66px)"),
]
PAGES["dont.png"] = (1400, 690, BASE + f"""
<div style="padding:40px;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:28px">{''.join(DONTS)}</div>""")

# --- palette swatches
def sw(hex_, name, token, fg):
    return (f'<div style="background:{hex_};color:{fg};border-radius:12px;padding:22px;height:200px;'
            f'display:flex;flex-direction:column;justify-content:flex-end;border:1px solid #0001">'
            f'<div style="font-size:26px;font-weight:700">{name}</div>'
            f'<div style="font-size:17px;opacity:.8">{hex_} · {token}</div></div>')
PAGES["palette.png"] = (1400, 290, BASE + f"""
<div style="padding:40px;display:grid;grid-template-columns:repeat(6,1fr);gap:18px">
{sw(INK,'Ink','--ink',CREAM)}{sw(CREAM,'Cream','--cream',INK)}{sw(KRAFT,'Kraft','--kraft',INK)}
{sw(RED,'Red','--red',CREAM)}{sw(BLUE,'Blue','--blue',CREAM)}{sw(YELLOW,'Yellow','--note-yellow',INK)}
</div>""")

# --- reversed / mono previews on the backgrounds they're meant for (transparent PNGs vanish on GitHub light mode)
def tile(rel, bg, w=520):
    return f'<div style="background:{bg};border-radius:12px;padding:40px;display:grid;place-items:center"><img src="{uri(rel)}" style="width:{w}px;max-width:100%"></div>'
PAGES["on-dark.png"] = (1400, 330, BASE + f"""
<div style="padding:40px;display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr) minmax(0,1fr);gap:24px">
{tile('01-primary/aibuilders-logo-horizontal-dark-bg.svg', INK, 600)}
{tile('01-primary/aibuilders-logo-stacked-dark-bg.svg', INK, 260)}
{tile('01-primary/aibuilders-mark.svg', INK, 200)}
</div>""")
PAGES["reversed.png"] = (1400, 330, BASE + f"""
<div style="padding:40px;display:grid;grid-template-columns:1.6fr 1fr 1fr;gap:24px;align-items:stretch">
{tile('02-reversed/aibuilders-logo-horizontal-reversed.svg', INK, 600)}
{tile('02-reversed/aibuilders-logo-stacked-reversed.svg', INK, 260)}
{tile('02-reversed/aibuilders-mark-reversed.svg', INK, 200)}
</div>""")
PAGES["mono.png"] = (1400, 330, BASE + f"""
<div style="padding:40px;display:grid;grid-template-columns:1.6fr 1fr 1.6fr 1fr;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr) minmax(0,1.6fr) minmax(0,1fr);gap:24px">
{tile('03-mono/aibuilders-logo-horizontal-ink.svg', CREAM, 420)}
{tile('03-mono/aibuilders-mark-ink.svg', CREAM, 150)}
{tile('03-mono/aibuilders-logo-horizontal-cream.svg', INK, 420)}
{tile('03-mono/aibuilders-mark-cream.svg', INK, 150)}
</div>""")

# --- README buttons (GitHub strips CSS, so buttons are images)
def button(label, icon, bg, fg):
    return (380, 72, BASE + f"""<style>body{{background:transparent}}</style>
<div style="display:inline-block;padding:2px 8px 8px 2px"><div style="display:inline-flex;align-items:center;gap:12px;background:{bg};color:{fg};padding:0 26px;height:64px;
border:2px solid {INK};border-radius:12px 4px 12px 4px;box-shadow:3px 4px 0 {INK};font-size:22px;font-weight:700;white-space:nowrap">
<span style="font-size:24px">{icon}</span>{label}</div></div>""")
PAGES["btn-download-zip.png"] = button("Download all logos (.zip)", "⬇", INK, CREAM)
PAGES["btn-pdf.png"] = button("Brand guide (PDF)", "📄", CREAM, INK)

with sync_playwright() as pw:
    br = pw.chromium.launch()
    for name, (w, h, html) in PAGES.items():
        btn = name.startswith("btn-")
        pg = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=2 if btn else 1)
        f = OUT / "_tmp.html"
        f.write_text(f"<html><body>{html}</body></html>")
        pg.goto(f.as_uri()); pg.wait_for_timeout(600)
        if btn:
            pg.locator("body > div").screenshot(path=str(OUT / name), omit_background=True)
        else:
            pg.screenshot(path=str(OUT / name), full_page=True)
        pg.close()
    (OUT / "_tmp.html").unlink()
    br.close()
print("guidelines/ rendered:", ", ".join(PAGES))
