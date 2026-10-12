"""Verify every generated page: static link check (relative files, #anchors, GitHub tag links → real paths/lines at v1.1.0),
then headless Chromium across light/dark × 1440/1920/390 × zh/en: console errors, blocked network, horizontal overflow,
in-browser SVG geometry, slide overflow; screenshots for review."""
import json, sys, asyncio, re, html
from pathlib import Path
from urllib.parse import urlparse, unquote
from playwright.async_api import async_playwright

SITE = Path('/workspace/pi-site'); SRC = Path('/workspace/pi-src'); REF = 'v1.1.0'
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else '/workspace/pi-shots/r1'); OUT.mkdir(parents=True, exist_ok=True)
ONLY = sys.argv[2].split(',') if len(sys.argv) > 2 and sys.argv[2] else None
PAGES = json.loads((SITE / 'assets/pages.json').read_text())
VIEWS = {'d1440': dict(width=1440, height=900, dpr=1), 'd1920': dict(width=1920, height=1080, dpr=1), 'm390': dict(width=390, height=844, dpr=2, mobile=True)}

# ---------------------------------------------------------------- static link check
ids_cache = {}
def ids_of(p):
    if p not in ids_cache: ids_cache[p] = set(re.findall(r'\sid="([^"]+)"', p.read_text()))
    return ids_cache[p]
def link_check():
    bad, n_int, n_gh, n_ext = [], 0, 0, 0
    line_cache = {}
    for rel in PAGES:
        f = SITE / rel; txt = f.read_text()
        for attr, url in re.findall(r'\s(href|src)="([^"]*)"', txt):
            url = html.unescape(url)
            if url.startswith('data:') or url.startswith('mailto:'): continue
            if url.startswith('http'):
                u = urlparse(url)
                if u.netloc == 'github.com' and u.path.startswith('/earendil-works/pi'):
                    n_gh += 1
                    m = re.match(r'/earendil-works/pi(?:/(tree|blob)/([^/]+)(/.*)?|/releases/tag/([^/]+))?$', u.path)
                    if not m: bad.append((rel, url, 'unparsed gh url')); continue
                    ref = m.group(2) or m.group(4)
                    if ref and ref != REF: bad.append((rel, url, 'wrong ref ' + ref)); continue
                    if m.group(3):
                        path = SRC / unquote(m.group(3)).lstrip('/')
                        if not path.exists(): bad.append((rel, url, 'missing path')); continue
                        if (m.group(1) == 'blob') != path.is_file(): bad.append((rel, url, 'tree/blob mismatch')); continue
                        if u.fragment.startswith('L'):
                            if path not in line_cache: line_cache[path] = sum(1 for _ in open(path, errors='ignore'))
                            if int(u.fragment[1:]) > line_cache[path]: bad.append((rel, url, 'line beyond EOF'))
                else: n_ext += 1
                continue
            n_int += 1
            u = urlparse(url)
            tgt = (f.parent / unquote(u.path)).resolve() if u.path else f
            if not tgt.exists(): bad.append((rel, url, 'missing file')); continue
            if u.fragment and tgt.suffix == '.html' and u.fragment not in ids_of(tgt) and not u.fragment.isdigit():
                bad.append((rel, url, 'missing anchor'))
    return dict(internal=n_int, github=n_gh, external=n_ext, broken=bad)

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
    out[key] = {issues, px: +(rr.width / vb.width * 10.5).toFixed(1)};
  });
  return out;
}'''
# elements that stick out of the viewport or overlap their siblings in page chrome
LAYOUT = r'''() => {
  const W = document.documentElement.clientWidth, bad = [];
  document.querySelectorAll('.topbar .wrap > *, .phero *, .hero *, .pkgcard, .fact, .crumbs, .checklist li, .cl-pkg, .ext-list > div, .stat, .legend, .moved').forEach((e) => {
    const r = e.getBoundingClientRect(); if (!r.width || getComputedStyle(e).visibility === 'hidden') return;
    if (e.closest('.pkgmenu') || e.closest('details:not([open]) .body')) return;
    if (r.right > W + 1 || r.left < -1) bad.push((e.className || e.tagName) + ' x=' + Math.round(r.left) + '..' + Math.round(r.right));
  });
  // top bar items must not overlap each other
  const items = [...document.querySelectorAll('.topbar .wrap > *')].filter(e => e.getBoundingClientRect().width && getComputedStyle(e).display !== 'none' && !e.classList.contains('spacer'));
  for (let i = 0; i + 1 < items.length; i++) { const a = items[i].getBoundingClientRect(), b = items[i + 1].getBoundingClientRect(); if (a.right > b.left + 1) bad.push('topbar overlap ' + (items[i].className || items[i].tagName) + ' / ' + (items[i + 1].className || items[i + 1].tagName)); }
  const tb = document.querySelector('.topbar .wrap'); if (tb && tb.scrollWidth > tb.clientWidth + 1) bad.push('topbar scrolls');
  return bad.slice(0, 12);
}'''

report = []
async def run():
    lc = link_check()
    print('LINKS internal', lc['internal'], 'github', lc['github'], 'external', lc['external'], 'broken', len(lc['broken']))
    for b in lc['broken'][:20]: print('   ', b)
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--allow-file-access-from-files'])
        for rel in PAGES:
            if ONLY and not any(o in rel for o in ONLY): continue
            deck = rel.endswith('slides.html')
            name = rel.replace('/index.html', '').replace('/', '_').replace('.html', '') or 'index'
            for vname, vp in VIEWS.items():
                for theme in ('light', 'dark'):
                    for lang in ('zh', 'en'):
                        ctx = await br.new_context(viewport={'width': vp['width'], 'height': vp['height']}, device_scale_factor=vp['dpr'],
                                                   is_mobile=vp.get('mobile', False), has_touch=vp.get('mobile', False))
                        pg = await ctx.new_page(); logs, net = [], []
                        pg.on('console', lambda m: logs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
                        pg.on('pageerror', lambda e: logs.append(f'pageerror: {e}'))
                        async def route(r):
                            if not r.request.url.startswith('file://'): net.append(r.request.url); await r.abort()
                            else: await r.continue_()
                        await pg.route('**/*', route)
                        await pg.goto(f'file://{SITE}/{rel}?theme={theme}&lang={lang}')
                        await pg.wait_for_function('window.__dg && window.__dg.done', timeout=30000)
                        await pg.wait_for_timeout(250)
                        st = await pg.evaluate('''() => ({n: document.querySelectorAll('.dg svg.pd').length, overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
                            theme: document.documentElement.dataset.theme, lang: document.documentElement.dataset.lang, title: document.title,
                            fontsBad: [...document.fonts].filter(f => f.status === 'error').map(f => f.family)})''')
                        tag = f'{name}-{vname}-{theme}-{lang}'
                        rec = dict(tag=tag, page=rel, **st, console=logs, network=net)
                        if not deck:
                            rec['layout'] = await pg.evaluate(LAYOUT)
                            if vname == 'd1440' and theme == 'light':
                                geom = await pg.evaluate(GEOM); rec['geom'] = {k: v for k, v in geom.items() if v['issues']}
                                rec['minpx'] = min([v['px'] for v in geom.values()] or [0])
                            if theme == 'light' and lang == 'zh' and vname in ('d1440', 'm390'):
                                await pg.screenshot(path=str(OUT / f'{tag}-top.png'))
                            if vname == 'd1440' and theme == 'light' and lang == 'zh':
                                await pg.screenshot(path=str(OUT / f'{tag}-full.png'), full_page=True)
                            if vname == 'd1440' and theme == 'dark' and lang == 'en':
                                await pg.screenshot(path=str(OUT / f'{tag}-top.png'))
                                if name.startswith('packages_agent-core') or name.startswith('packages_pi-ai'):
                                    for el in await pg.query_selector_all('figure.diagram'):
                                        fid = await el.get_attribute('id'); await el.scroll_into_view_if_needed()
                                        await el.screenshot(path=str(OUT / f'{tag}-{fid}.png'))
                            if name == 'packages_agent-core' and theme == 'light' and lang == 'zh' and vname in ('d1440', 'm390'):
                                await pg.evaluate('scrollTo(0,0)'); await pg.click('.pkgsw > summary'); await pg.wait_for_timeout(200)
                                rec['switcher'] = await pg.evaluate('(() => { const m = document.querySelector(".pkgmenu"); const r = m.getBoundingClientRect(); return {open: document.querySelector(".pkgsw").open, links: m.querySelectorAll("a").length, right: r.right, bottom: r.bottom, W: innerWidth, H: innerHeight}; })()')
                                await pg.screenshot(path=str(OUT / f'{tag}-switcher.png'))
                            if name == 'index' and vname == 'd1440' and theme == 'light' and lang == 'zh':
                                await pg.evaluate('document.getElementById("fig-layers").scrollIntoView({behavior:"instant",block:"center"})')
                                nd = await pg.query_selector('#fig-layers .nd[data-id]'); await nd.hover(); await pg.wait_for_timeout(250)
                                rec['hover'] = await pg.evaluate('document.querySelectorAll("#fig-layers .ed.on").length')
                                await pg.mouse.move(2, 2)
                                await pg.click('#fig-classes .expand'); await pg.wait_for_timeout(450)
                                rec['lightbox'] = await pg.evaluate('!!document.querySelector(".lb:not([hidden]) svg.pd")')
                                await pg.keyboard.press('Escape')
                        else:
                            n = await pg.evaluate('document.querySelectorAll(".slide").length'); rec['slides'] = n
                            if vname == 'd1920' and lang == 'en': pass
                            for i in range(1, n + 1):
                                await pg.evaluate(f'location.hash = "#{i}"'); await pg.wait_for_timeout(420)
                                ov = await pg.evaluate('''() => { const s = document.querySelector('.slide.on'); const r = s.getBoundingClientRect();
                                    const bad = [...s.querySelectorAll('h2,p,li,.col,.num,.ci,.bars,.dia,.tiers,.evgrid,.apigrid,.closing,.cols,.nums,.sidetext,.kicker,h1')].filter(e => { const q = e.getBoundingClientRect(); return q.width && (q.bottom > r.bottom - 2 || q.right > r.right - 2 || q.left < r.left - 1); }).map(e => e.className || e.tagName);
                                    const svg = s.querySelector('svg.pd'); let px = null; if (svg) { const q = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal; px = +(Math.min(q.width / vb.width, q.height / vb.height) * 10.5).toFixed(1); }
                                    return {bad, px}; }''')
                                if ov['bad']: rec.setdefault('slide_overflow', {})[i] = ov['bad']
                                if ov['px']: rec.setdefault('slide_px', {})[i] = ov['px']
                                if (theme == 'dark' and lang == 'zh' and vname == 'd1440') or (vname == 'm390' and theme == 'light' and lang == 'en' and i <= 3):
                                    await pg.screenshot(path=str(OUT / f'{tag}-s{i:02d}.png'))
                        flag = (st['n'] == 0 and rel != 'roadmap/index.html' and 'packages/' not in rel) or net or st['overflowX'] > 0 or st['fontsBad'] or rec.get('slide_overflow') or rec.get('layout') or rec.get('geom') \
                               or any('pageerror' in c or c.startswith('error') for c in logs)
                        rec['fail'] = bool(flag)
                        if flag or (vname == 'd1440' and theme == 'light' and lang == 'zh'):
                            print(('FAIL ' if flag else 'ok   ') + tag, 'svgs', st['n'], 'ovX', st['overflowX'], 'net', len(net), 'console', logs[:2], 'layout', rec.get('layout', [])[:3],
                                  'geom', {k: v['issues'][:2] for k, v in (rec.get('geom') or {}).items()}, 'minpx', rec.get('minpx'), 'slides_over', rec.get('slide_overflow'), rec.get('switcher', ''), rec.get('hover', ''), rec.get('lightbox', ''))
                        report.append(rec); await ctx.close()
        await br.close()
    (OUT / 'report.json').write_text(json.dumps(dict(links=lc, runs=report), indent=1))
    fails = [r['tag'] for r in report if r['fail']]
    print('RUNS', len(report), 'FAILURES:', len(fails), fails[:30], 'BROKEN LINKS', len(lc['broken']))
asyncio.run(run())
