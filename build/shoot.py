"""Headless verification of the hand-drawn SVG diagrams: light/dark × 1440/1920/390, zh/en; geometry checks in the real browser; screenshots."""
import json, sys, asyncio
from pathlib import Path
from playwright.async_api import async_playwright

SITE = Path('/workspace/pi-site'); OUT = Path(sys.argv[1] if len(sys.argv) > 1 else '/workspace/pi-shots/v1'); OUT.mkdir(parents=True, exist_ok=True)
VIEWS = {'d1440': dict(width=1440, height=900, dpr=1.5), 'd1920': dict(width=1920, height=1080, dpr=1),
         'm390': dict(width=390, height=844, dpr=2, mobile=True)}
KEYS = ['packages', 'layers', 'loop', 'toolexec', 'sequence', 'classes', 'session', 'compaction', 'extensions', 'modes', 'providers', 'tui']
GEOM = r'''() => {
  const vis = (el) => { for (let e = el; e && e.tagName !== 'svg'; e = e.parentElement) if (getComputedStyle(e).display === 'none') return false; return true; };
  const out = {};
  document.querySelectorAll('.dg svg.pd').forEach((svg) => {
    const key = svg.closest('.dg').dataset.dg, issues = [];
    const vb = svg.viewBox.baseVal;
    svg.querySelectorAll('.nd').forEach((nd) => {
      const card = nd.querySelector('rect.card'); if (!card) return; const r = card.getBBox();
      nd.querySelectorAll('text').forEach((t) => { if (!vis(t) || !t.textContent.trim()) return; const b = t.getBBox();
        if (b.x < r.x - 1 || b.x + b.width > r.x + r.width + 1 || b.y < r.y - 1 || b.y + b.height > r.y + r.height + 1) issues.push('text outside node ' + (nd.dataset.id || '') + ': ' + t.textContent); });
    });
    const T = [...svg.querySelectorAll('text')].filter((t) => vis(t) && t.textContent.trim() && !t.closest('.stp')).map((t) => ({t, b: t.getBBox()}));
    for (const {t, b} of T) if (b.x < -1 || b.y < -1 || b.x + b.width > vb.width + 1 || b.y + b.height > vb.height + 1) issues.push('text off canvas: ' + t.textContent);
    for (let i = 0; i < T.length; i++) for (let j = i + 1; j < T.length; j++) {
      const a = T[i].b, c = T[j].b; const ox = Math.min(a.x + a.width, c.x + c.width) - Math.max(a.x, c.x), oy = Math.min(a.y + a.height, c.y + c.height) - Math.max(a.y, c.y);
      if (ox > 1.5 && oy > 2.5) issues.push('text overlap: "' + T[i].t.textContent + '" × "' + T[j].t.textContent + '"');
    }
    const rr = svg.getBoundingClientRect();
    out[key] = {issues, scale: +(rr.width / vb.width).toFixed(3), px: +(rr.width / vb.width * 10.5).toFixed(1)};
  });
  return out;
}'''
report = []

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--allow-file-access-from-files'])
        for vname, vp in VIEWS.items():
            for theme in ('light', 'dark'):
                for page_name in ('index', 'slides'):
                    langs = ('zh', 'en') if vname != 'm390' else ('zh',)
                    for lang in langs:
                        ctx = await b.new_context(viewport={'width': vp['width'], 'height': vp['height']}, device_scale_factor=vp['dpr'],
                                                  is_mobile=vp.get('mobile', False), has_touch=vp.get('mobile', False))
                        pg = await ctx.new_page()
                        logs, net = [], []
                        pg.on('console', lambda m: logs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
                        pg.on('pageerror', lambda e: logs.append(f'pageerror: {e}'))
                        async def route(r):
                            if not r.request.url.startswith('file://'): net.append(r.request.url); await r.abort()
                            else: await r.continue_()
                        await pg.route('**/*', route)
                        await pg.goto(f'file://{SITE}/{page_name}.html?theme={theme}&lang={lang}')
                        await pg.wait_for_function('window.__dg && window.__dg.done', timeout=30000)
                        await pg.wait_for_timeout(300)
                        st = await pg.evaluate('''() => ({n: document.querySelectorAll('.dg svg.pd').length, mermaid: !!document.querySelector('script[src*=mermaid]') || 'mermaid' in window,
                            overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth, theme: document.documentElement.dataset.theme, lang: document.documentElement.dataset.lang,
                            fonts: [...new Set([...document.fonts].filter(f => f.status === 'loaded').map(f => f.family))]})''')
                        tag = f'{page_name}-{vname}-{theme}-{lang}'
                        rec = dict(tag=tag, **st, console=logs, network=net)
                        if page_name == 'index':
                            geom = await pg.evaluate(GEOM)
                            rec['geom'] = geom
                            iss = {k: v['issues'] for k, v in geom.items() if v['issues']}
                            print(tag, 'svgs', st['n'], 'overflowX', st['overflowX'], 'net', len(net), 'console', logs[:2], 'minpx', min(v['px'] for v in geom.values()), 'issues', iss or 'none')
                            if vname != 'm390' or theme == 'light':
                                for k in KEYS:
                                    el = await pg.query_selector(f'#fig-{k}')
                                    await el.scroll_into_view_if_needed(); await pg.wait_for_timeout(60)
                                    await el.screenshot(path=str(OUT / f'{tag}-fig-{k}.png'))
                            if vname == 'd1440' and lang == 'zh':
                                await pg.screenshot(path=str(OUT / f'{tag}-full.png'), full_page=True)
                                # hover focus
                                await pg.evaluate('document.getElementById("fig-layers").scrollIntoView({behavior:"instant",block:"center"})')
                                nd = await pg.query_selector('#fig-layers .nd[data-id="agent"]') or await pg.query_selector('#fig-layers .nd[data-id]')
                                await nd.hover(); await pg.wait_for_timeout(250)
                                rec['hover'] = await pg.evaluate('!!document.querySelector("#fig-layers svg.pd.focus") && document.querySelectorAll("#fig-layers .ed.on").length')
                                await (await pg.query_selector('#fig-layers')).screenshot(path=str(OUT / f'{tag}-hover-layers.png'))
                                await pg.mouse.move(2, 2)
                                await pg.click('#fig-providers .expand'); await pg.wait_for_timeout(450)
                                rec['lightbox'] = await pg.evaluate('!!document.querySelector(".lb:not([hidden]) svg.pd")')
                                await pg.mouse.move(700, 450); await pg.mouse.wheel(0, -400); await pg.wait_for_timeout(250)
                                await pg.screenshot(path=str(OUT / f'{tag}-lightbox.png'))
                                await pg.keyboard.press('Escape')
                                print('   hover edges', rec['hover'], 'lightbox', rec['lightbox'])
                        else:
                            n = await pg.evaluate('document.querySelectorAll(".slide").length')
                            rec['slides'] = n; print(tag, 'slides', n, 'svgs', st['n'], 'console', logs[:2], 'net', len(net))
                            for i in range(1, n + 1):
                                await pg.evaluate(f'location.hash = "#{i}"'); await pg.wait_for_timeout(600)
                                ov = await pg.evaluate('''() => { const s = document.querySelector('.slide.on'); const r = s.getBoundingClientRect();
                                    const bad = [...s.querySelectorAll('h2,p,li,.col,.num,.ci,.bars,.dia,.tiers,.evgrid,.apigrid,.closing,.cols,.nums,.sidetext')].filter(e => { const q = e.getBoundingClientRect(); return q.bottom > r.bottom - 2 || q.right > r.right - 2; }).map(e => e.className || e.tagName);
                                    const svg = s.querySelector('svg.pd'); let px = null; if (svg) { const q = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal; px = +(Math.min(q.width / vb.width, q.height / vb.height) * 10.5).toFixed(1); }
                                    return {bad, px}; }''')
                                if ov['bad']: print('  slide', i, 'overflow:', ov['bad'][:5]); rec.setdefault('slide_overflow', {})[i] = ov['bad']
                                if ov['px']: rec.setdefault('slide_px', {})[i] = ov['px']
                                if vname != 'm390' or i in (1, 4, 6):
                                    await pg.screenshot(path=str(OUT / f'{tag}-s{i:02d}.png'))
                            print('   slide 10.5-unit text px:', rec.get('slide_px'))
                        report.append(rec)
                        await ctx.close()
        await b.close()
    (OUT / 'report.json').write_text(json.dumps(report, indent=1))
    bad = [r['tag'] for r in report if r['n'] == 0 or r['mermaid'] or r['network'] or r['overflowX'] > 0 or r.get('slide_overflow')
           or any('pageerror' in c or c.startswith('error') for c in r['console']) or any(v['issues'] for v in r.get('geom', {}).values())]
    print('FAILURES:', bad or 'none')

asyncio.run(run())
