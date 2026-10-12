"""Render every diagram standalone (light/dark, zh/en) and screenshot each SVG at 1x/2x for review."""
import sys, asyncio, importlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import svgkit, figs
importlib.reload(svgkit); importlib.reload(figs)
from playwright.async_api import async_playwright
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else '/workspace/pi-shots/dg'); OUT.mkdir(parents=True, exist_ok=True)
only = sys.argv[2].split(',') if len(sys.argv) > 2 else None
S = Path(__file__).parent / 'static'
FIGS = figs.build_all()
for k, f in FIGS.items():
    for w in f.lint(): print('LINT', w)
def page(theme, lang):
    css = (S / 'base.css').read_text().replace('url(fonts/', 'url(/workspace/pi-site/assets/fonts/') + (S / 'dg.css').read_text()
    body = ''.join(f'<div class="box" id="b-{k}"><div class="dg">{f.svg()}</div></div>' for k, f in FIGS.items() if not only or k in only)
    return f'<!doctype html><html data-theme="{theme}" data-lang="{lang}"><head><meta charset="utf-8"><style>{css} body{{background:var(--surface);margin:0;padding:20px}} .box{{display:inline-block;padding:16px;margin:0 0 20px;border:1px solid var(--border);border-radius:14px;background:var(--surface)}} .dg svg.pd{{max-width:none}}</style></head><body>{svgkit.DEFS}{body}</body></html>'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        for theme in ('light', 'dark'):
            for lang in ('zh', 'en'):
                if theme == 'dark' and lang == 'en': continue
                f = Path(f'/tmp/dgprev-{theme}-{lang}.html'); f.write_text(page(theme, lang))
                pg = await b.new_page(viewport={'width': 1500, 'height': 900}, device_scale_factor=1.5)
                await pg.goto('file://' + str(f)); await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(300)
                for k in FIGS:
                    if only and k not in only: continue
                    await pg.locator(f'#b-{k}').screenshot(path=str(OUT / f'{k}-{theme}-{lang}.png'), animations='disabled')
                await pg.close()
        await b.close()
asyncio.run(main())
print('shots in', OUT)
