# ---------------------------------------------------------------- package registry + version check
import pkgmeta, deep_agent, deep_ai  # noqa
PK = pkgmeta.load()
PBY = {p['slug']: p for p in PK}
assert {p['version'] for p in PK} == {VERSION}, ('package versions differ from', VERSION, {p['slug']: p['version'] for p in PK})
STATS_BY = {s['pkg']: s for s in STATS}
V1 = {s['id']: s for s in SECTIONS}

# ---------------------------------------------------------------- helpers
def md(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    return s

def T(pair, tag='span', cls=''):
    zh, en = pair
    c = (' ' + cls) if cls else ''
    return f'<{tag} class="zh{c}" lang="zh-CN">{md(zh)}</{tag}><{tag} class="en{c}" lang="en">{md(en)}</{tag}>'

def fmt(n): return f'{n:,}'
def esc(s): return html.escape(str(s), quote=True)

ICON = {
 'sun': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6"/></svg>',
 'moon': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5a8.5 8.5 0 1 0 10.7 10.7Z"/></svg>',
 'menu': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h10"/></svg>',
 'gh': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.16-1.11-1.470-1.11-1.47-.9-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.9 1.52 2.34 1.08 2.91.83.09-.65.35-1.08.63-1.33-2.22-.25-4.550-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02a9.5 9.5 0 0 1 5 0c1.91-1.3 2.75-1.02 2.75-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.840-2.34 4.68-4.57 4.93.36.31.68.92.68 1.85v2.75c0 .27.18.58.69.48A10 10 0 0 0 12 2Z"/></svg>',
 'play': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5.5v13a1 1 0 0 0 1.5.86l10.5-6.5a1 1 0 0 0 0-1.72L9.5 4.64A1 1 0 0 0 8 5.5Z"/></svg>',
 'expand': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7"/></svg>',
 'list': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01"/></svg>',
 'gear': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/></svg>',
 'file': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/></svg>',
 'down': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>',
}
ICON['gh'] = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.16-1.11-1.47-1.11-1.47-.9-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.9 1.52 2.34 1.08 2.91.83.09-.65.35-1.08.63-1.33-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02a9.5 9.5 0 0 1 5 0c1.91-1.3 2.75-1.02 2.75-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.85v2.75c0 .27.18.58.69.48A10 10 0 0 0 12 2Z"/></svg>'
LAYER_NAME = {'modes': 'Run modes', 'coding': 'pi-coding-agent', 'ext': 'Extensions', 'agent': 'pi-agent-core', 'ai': 'pi-ai', 'tui': 'pi-tui', 'infra': 'Infra'}
PKG_LAYER = {p['dir']: p['layer'] for p in PK}

CAPTION = {
 'packages': ('内部依赖：实线 = dependencies，虚线 = devDependencies', 'Internal deps: solid = dependencies, dashed = devDependencies'),
 'layers': ('自上而下的四层运行时栈', 'The four-layer runtime stack, top to bottom'),
 'loop': ('runLoop()：内层循环与外层循环', 'runLoop(): inner and outer loop'),
 'toolexec': ('单个工具调用的处理管道', 'The pipeline for one tool call'),
 'sequence': ('Interactive 模式下的一次提示（含一次 bash 工具调用）', 'One prompt in interactive mode, with one bash tool call'),
 'classes': ('主要类与接口及其组合关系', 'Main classes and interfaces and how they compose'),
 'session': ('一个会话文件中的条目树（示例）', 'The entry tree inside one session file (example)'),
 'compaction': ('三种触发方式共享的压缩路径', 'One compaction path shared by three triggers'),
 'extensions': ('从发现、加载到事件分发', 'From discovery and loading to event dispatch'),
 'modes': ('resolveAppMode() 的分派', 'Dispatch in resolveAppMode()'),
 'providers': ('Provider → API 实现 → 统一事件流', 'Provider → API implementation → normalized event stream'),
 'tui': ('从按键 / 事件到终端输出的一帧', 'One frame, from keypress or event to terminal output'),
 'ac_arch': ('src/ 的 6 个文件、入口与对 pi-ai 的依赖', 'The six files in src/, the entry, and what they use from pi-ai'),
 'ac_state': ('Agent 的运行状态机与守卫', 'The Agent run state machine and its guards'),
 'ac_turn': ('两次请求 + 一次工具调用中的钩子与事件顺序', 'Hook and event order across two requests and one tool call'),
 'ac_events': ('AgentEvent 的嵌套、归约器与 pi-ai 事件映射', 'AgentEvent nesting, the reducer, and the mapping from pi-ai events'),
 'ac_queues': ('两个队列、三个 steering 轮询点与 follow-up', 'Two queues, three steering poll points, and follow-up'),
 'ac_parallel': ('并行与顺序模式的时间线（示意，时长为示例）', 'Parallel vs sequential timelines (illustrative durations)'),
 'ac_proxy': ('StreamFn 的解析与 streamProxy 的往返', 'How the StreamFn is resolved, and the streamProxy round trip'),
 'ac_types': ('核心类型与它们的关系', 'Core types and how they relate'),
 'ai_entry': ('导入路径、得到的内容与加载成本', 'Import paths, what you get, and what it costs to load'),
 'ai_registry': ('ModelsImpl、Provider 与目录刷新', 'ModelsImpl, Provider, and catalog refresh'),
 'ai_pipeline': ('外层流同步返回，setup 在背后异步完成', 'The outer stream returns now; setup completes behind it'),
 'ai_events': ('AssistantMessageEvent 语法与 EventStream 内部', 'AssistantMessageEvent grammar and EventStream internals'),
 'ai_convert': ('transformMessages 的六条规则', 'The six rules of transformMessages'),
 'ai_anthropic': ('Anthropic SSE → 统一事件、停止原因与 thinking 配置', 'Anthropic SSE → unified events, stop reasons and thinking'),
 'ai_budget': ('思考等级、maxTokens 推导与成本公式', 'Thinking levels, maxTokens derivation and the cost formula'),
 'ai_oneshot': ('generateImages() 与 classify()', 'generateImages() and classify()'),
}
assert set(CAPTION) == set(FIGS), set(FIGS) ^ set(CAPTION)

def figure(key, title_pair):
    cap = CAPTION[key]
    return (f'<figure class="diagram" id="fig-{key}"><figcaption><span class="cap">{T(cap)}</span>'
            f'<button class="iconbtn expand" type="button" data-i18n-title="放大查看|Enlarge">{ICON["expand"]}</button></figcaption>'
            f'<div class="diagram-body"><div class="swipe-hint">{T(("← 左右滑动查看，点击放大 →", "← swipe to scroll, tap to enlarge →"))}</div>'
            f'<div class="dg" data-dg="{key}" aria-label="{esc(title_pair[1])} diagram">{FIGS[key].svg()}</div></div></figure>')

def flink(path, ln=None, label=None):
    d, _, b = path.rpartition('/')
    lab = label or f'<span class="dir">{esc(d + "/" if d else "")}</span>{esc(b)}'
    return (f'<a class="f" href="{gh(path, ln)}" target="_blank" rel="noopener"><span>{lab}</span>'
            f'{f"<span class=ln>L{ln}</span>" if ln else ""}</a>')

def files_table(files):
    rows = []
    for path, pat, sym, zh, en in files:
        ln = line_of(path, pat)
        rows.append(f'<tr><td>{flink(path, ln)}</td><td class="sym"><code>{esc(sym)}</code></td><td class="col-role">{T((zh, en))}</td></tr>')
    head = f'<thead><tr><th>{T(("文件", "File"))}</th><th>{T(("符号", "Symbol"))}</th><th class="col-role">{T(("作用", "Role"))}</th></tr></thead>'
    return f'<div class="tbl"><table>{head}<tbody>{"".join(rows)}</tbody></table></div>'

def sec_open(i, sid, layer, title, chip=None):
    chip = chip or LAYER_NAME.get(layer, layer)
    return (f'<section class="sec L-{layer}" id="{sid}" aria-labelledby="h-{sid}">'
            f'<div class="sec-meta"><span class="sec-no">{i:02d}</span><span class="chip L-{layer}">{chip}</span></div>'
            f'<h2 id="h-{sid}">{T(title)}<a class="anchor" href="#{sid}" aria-label="link">#</a></h2>')

def section(i, s, moved_from=None):
    L = s['layer']
    pts = ''.join(f'<li>{T(p)}</li>' for p in s['points'])
    how = ''.join(f'<li>{T(p)}</li>' for p in s['how'])
    mv = (f'<p class="note">{T(("本节沿用第一版的图（原位于总览页），已按 v1.1.0 重新核对。", "This section keeps its first-edition diagram (formerly on the overview page), re-checked against v1.1.0."))}</p>') if moved_from else ''
    return sec_open(i, s['id'], L, s['title']) + f'''
<p class="takeaway"><span class="tl">{T(("一句话结论", "Takeaway"))}</span>{T(s["takeaway"])}</p>{mv}
{figure(s["diagram"], s["title"])}
<div class="grid2"><div class="card"><h3>{ICON["list"]}{T(("要点", "Key points"))}</h3><ul>{pts}</ul></div>
<div class="card"><h3>{ICON["gear"]}{T(("工作原理", "How it works"))}</h3><ol>{how}</ol></div></div>
<div class="files"><h3>{ICON["file"]}{T(("关键文件", "Key files"))} <span style="font-weight:500;letter-spacing:0;text-transform:none">· {REF}</span></h3>{files_table(s["files"])}</div>
</section>'''

# ---------------------------------------------------------------- source scanners (all mechanical)
def ts_files(pdir, sub='src'):
    root = SRC / 'packages' / pdir
    out = []
    for dp, dns, fns in os.walk(root / sub):
        dns[:] = [x for x in dns if x not in ('node_modules', 'dist')]
        for f in fns:
            if f.endswith('.ts') and not f.endswith('.d.ts'):
                fp = Path(dp) / f
                out.append((fp.relative_to(SRC).as_posix(), sum(1 for _ in open(fp, errors='ignore'))))
    return out

def largest(pdir, n=10):
    return sorted([x for x in ts_files(pdir) if '.test.' not in x[0]], key=lambda x: -x[1])[:n]

TEST_RE = re.compile(r'^\s*(?:it|test)(?:\.each\([^)]*\))?\(\s*["\'`]', re.M)
def tests_of(pdir):
    root = SRC / 'packages' / pdir
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [x for x in dns if x not in ('node_modules', 'dist')]
        for f in fns:
            if '.test.' in f and f.endswith(('.ts', '.tsx', '.mjs')):
                fp = Path(dp) / f; txt = fp.read_text(errors='ignore')
                out.append((fp.relative_to(SRC).as_posix(), len(TEST_RE.findall(txt))))
    return sorted(out, key=lambda x: (-x[1], x[0]))

EXP_RE = re.compile(r'^export (?:declare )?(?:abstract )?(async function|function|class|const|let|type|interface|enum) ([A-Za-z_$][\w$]*)', re.M)
def exports_of(path):
    txt = read(path)
    out = []
    for m in EXP_RE.finditer(txt):
        out.append((m.group(1).replace('async ', ''), m.group(2), txt.count('\n', 0, m.start()) + 1))
    return out

def changelog(pdir):
    p = SRC / 'packages' / pdir / 'CHANGELOG.md'
    if not p.exists(): return None
    lines = p.read_text().splitlines()
    try: start = next(i for i, l in enumerate(lines) if l.startswith(f'## [{VERSION}]'))
    except StopIteration: return None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('## [')), len(lines))
    secs = {}; cur = None
    for l in lines[start + 1:end]:
        if l.startswith('### '): cur = l[4:].strip(); secs[cur] = []
        elif l.startswith('- ') and cur: secs[cur].append(l[2:].strip())
    date = re.search(r'\d{4}-\d{2}-\d{2}', lines[start])
    return dict(line=start + 1, path=f'packages/{pdir}/CHANGELOG.md', secs=secs, date=date.group(0) if date else '')

def clean_bullet(b, n=210):
    b = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', b)
    b = re.sub(r'\s*\((?:#\d+(?:,\s*)?)+\)', '', b)
    b = re.sub(r'\s*\(\s*(?:#?\d+[ ,]*)+\)', '', b)
    b = b.replace('**', '')
    if len(b) > n: b = b[:n].rsplit(' ', 1)[0] + ' …'
    if b.count('`') % 2: b = b.replace('`', '')
    return b

# ---------------------------------------------------------------- page chrome
DEPTH = {}
def rel(prefix, path):  # path relative to site root
    return prefix + path

def status_dot(st): return f'<span class="sd s-{st}">{T(pkgmeta.STATUS_NAME[st])}</span>'

def pkg_href(prefix, slug): return f'{prefix}packages/{slug}/index.html'

def topbar(prefix, active, cur_slug=None, toc=True):
    menu = []
    for gid, gname in pkgmeta.GROUP_NAME.items():
        items = [p for p in PK if p['group'] == gid]
        if not items: continue
        menu.append(f'<div class="g">{T(gname)}</div>')
        for p in items:
            on = ' on' if p['slug'] == cur_slug else ''
            menu.append(f'<a class="L-{p["layer"]}{on}" href="{pkg_href(prefix, p["slug"])}"><span class="dotL"></span><span class="nm">{p["slug"]}</span>{status_dot(p["status"])}</a>')
    menu.append(f'<a class="all" href="{prefix}index.html#pkgs">{T(("全部 14 个包 →", "All 14 packages →"))}</a>')
    cur = f'<span class="cur">· {cur_slug}</span>' if cur_slug else ''
    nav = lambda key, href, lab: f'<a href="{href}"{" class=on" if active == key else ""}>{T(lab)}</a>'
    return f'''<header class="topbar"><div class="wrap">
{f'<button class="iconbtn only-mobile" id="toc-btn" type="button" data-i18n-title="目录|Contents">{ICON["menu"]}</button>' if toc else ''}
<a class="brand" href="{prefix}index.html"><span class="logo"><span>π</span></span><span class="t">{T(SITE)}</span><small class="ver" title="Pi {REF}">{REF}</small></a>
<details class="pkgsw{' on' if active == 'pkg' else ''}"><summary>{T(("包", "Packages"))}{cur}{ICON["down"]}</summary><nav class="pkgmenu" aria-label="Packages">{"".join(menu)}</nav></details>
<nav class="topnav">{nav("hub", prefix + "index.html", ("总览", "Overview"))}{nav("roadmap", prefix + "roadmap/index.html", ("路线图", "Roadmap"))}</nav>
<span class="spacer"></span>
<div class="tools">
<a class="btn sm" href="{prefix}slides.html">{ICON["play"].replace("<svg", "<svg width=14 height=14")}<span class="t2">{T(("演示", "Slides"))}</span></a>
<div class="seg" role="group" aria-label="Language"><button type="button" data-set-lang="zh">中</button><button type="button" data-set-lang="en">EN</button></div>
<button class="iconbtn" id="theme-btn" type="button" data-i18n-title="切换明暗|Toggle theme"><span class="th-moon">{ICON["moon"]}</span><span class="th-sun">{ICON["sun"]}</span></button>
<a class="iconbtn gh" href="{GH}/tree/{REF}" target="_blank" rel="noopener" data-i18n-title="GitHub 源码（{REF}）|Source on GitHub ({REF})">{ICON["gh"]}</a>
</div></div><div class="progress"></div></header>'''

def crumbs(prefix, items):
    out = [f'<a href="{prefix}index.html">{T(SITE)}</a>']
    for href, lab in items[:-1]:
        out.append(f'<span class="sep">/</span><a href="{href}">{T(lab)}</a>')
    out.append(f'<span class="sep">/</span><span class="here">{T(items[-1][1])}</span>')
    return f'<nav class="crumbs" aria-label="Breadcrumb">{"".join(out)}</nav>'

def footer():
    return (f'<footer class="foot"><span>{T((f"{SITE[0]} · {SUBTITLE[0]}：内容依据 earendil-works/pi 发布标签 `{REF}`（`{SHORT}`，{COMMIT_DATE[:10]}）生成，所有源码链接指向该标签。", f"{SITE[1]} · {SUBTITLE[1]}: generated from the earendil-works/pi release tag `{REF}` (`{SHORT}`, {COMMIT_DATE[:10]}); every source link points at that tag."))}</span>'
            f'<span>{T(("离线可用 · 无 CDN 依赖", "Works offline · no CDN"))}</span></footer>')

def HEAD(prefix, title_pair, css, extra='', desc=None):
    d = desc or f'{SITE[1]} — a source-grounded architecture walkthrough of earendil-works/pi, analysis of Pi {REF} (tag {REF}, {SHORT}).'
    return f'''<!doctype html>
<html lang="zh-CN" data-theme="light" data-lang="zh"{extra}><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title_pair[0])}</title>
<meta name="description" content="{esc(d)}">
<meta name="pi-version" content="{VERSION}"><meta name="pi-ref" content="{REF} {SHA}">
<meta property="og:title" content="{esc(title_pair[1])}"><meta property="og:description" content="{esc(d)}">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230b0d12'/%3E%3Ctext x='16' y='23' font-size='20' text-anchor='middle' fill='%23a78bfa' font-family='serif'%3E%CF%80%3C/text%3E%3C/svg%3E">
<script src="{prefix}assets/prefs.js"></script>
<link rel="stylesheet" href="{prefix}assets/base.css">{''.join(f'<link rel="stylesheet" href="{prefix}assets/{c}">' for c in css)}
</head>'''

def page(relpath, title_pair, body_html, active, toc_html=None, cur_slug=None, hero='', body_attrs=''):
    depth = relpath.count('/')
    prefix = '../' * depth
    body_html = body_html.replace('{P}', prefix)
    hero = hero.replace('{P}', prefix)
    toc_html = (toc_html or '').replace('{P}', prefix)
    out = HEAD(prefix, title_pair, ['site.css', 'dg.css']) + f'''
<body data-title-zh="{esc(title_pair[0])}" data-title-en="{esc(title_pair[1])}"{body_attrs}>
{topbar(prefix, active, cur_slug, toc=bool(toc_html))}
{hero}
<div class="wrap layout">{f'<aside class="toc" aria-label="Contents">{toc_html}</aside>' if toc_html else '<aside class="toc" aria-hidden="true"></aside>'}
<main id="main">{DEFS}{body_html}
{footer()}</main></div>
<script src="{prefix}assets/dg.js"></script><script src="{prefix}assets/site.js"></script>
</body></html>'''
    out = out.replace('&lt;grad&gt;', '<span class="grad">').replace('&lt;/grad&gt;', '</span>').replace('&lt;br&gt;', '<br>')
    dst = OUT / relpath; dst.parent.mkdir(parents=True, exist_ok=True); dst.write_text(out)
    PAGES.append(relpath)
PAGES = []

def toc_build(groups, foot_links):
    out = []
    for gname, items in groups:
        out.append(f'<div class="toc-g">{T(gname)}</div>')
        for i, sid, title, layer in items:
            out.append(f'<a href="#{sid}" class="L-{layer}"><span class="no">{i:02d}</span><span>{T(title)}</span><span class="dot"></span></a>')
    out.append('<div class="toc-foot">' + ''.join(foot_links) + '</div>')
    return ''.join(out)

def pkg_chip(prefix, slug):
    p = PBY[slug]
    return f'<a class="chip L-{p["layer"]}" href="{pkg_href(prefix, slug)}">{slug}</a>'

def facts_row(p):
    st = STATS_BY.get(p['dir'], {})
    tests = tests_of(p['dir'])
    F = [(p['version'], ('版本', 'version')), (fmt(st.get('src_files', 0)), ('源文件', 'src files')), (fmt(st.get('src_loc', 0)), ('源码行', 'src LOC')),
         (str(len(tests)), ('测试文件', 'test files')), (fmt(sum(c for _, c in tests)), ('测试用例', 'test cases')), (str(len(p['exports']) or 1), ('导出路径', 'export paths'))]
    return '<div class="facts">' + ''.join(f'<div class="fact"><div class="n">{n}</div><div class="k">{T(k)}</div></div>' for n, k in F) + '</div>'

def deps_row(prefix, p):
    parts = []
    parts.append(f'<span><b>{T(("依赖", "Depends on"))}</b></span>' + (''.join(pkg_chip(prefix, s) for s in p['dep_slugs']) or f'<span>{T(("无内部依赖", "no internal deps"))}</span>'))
    parts.append(f'<span style="margin-left:10px"><b>{T(("被依赖", "Used by"))}</b></span>' + (''.join(pkg_chip(prefix, s) for s in p['dependents']) or '<span>—</span>'))
    if p['dev_slugs']: parts.append(f'<span style="margin-left:10px"><b>dev</b></span>' + ''.join(pkg_chip(prefix, s) for s in p['dev_slugs']))
    return '<div class="deps">' + ''.join(parts) + '</div>'

def pkg_hero(p, lead=None):
    prefix = '{P}'
    return f'''<section class="phero L-{p["layer"]}"><div class="wrap">
{crumbs(prefix, [(prefix + "index.html#pkgs", ("包", "Packages")), (None, (p["slug"], p["slug"]))])}
<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><span class="chip L-{p["layer"]}">{LAYER_NAME.get(p["layer"], p["layer"])}</span>{status_dot(p["status"])}<a class="chip L-infra" href="{gh("packages/" + p["dir"])}" target="_blank" rel="noopener">packages/{p["dir"]} · {REF}</a></div>
<h1>{p["slug"]}<span class="npm">{p["npm"]}{" · private" if p["private"] else ""}</span></h1>
<p class="lead">{T(lead or (p["desc"][0] + "。", p["desc"][1] + "."))}</p>
{facts_row(p)}{deps_row(prefix, p)}
</div></section>'''

def checklist(done_keys, half_keys=()):
    out = []
    for k, name, d in pkgmeta.TEMPLATE:
        cls = 'ok' if k in done_keys else 'half' if k in half_keys else ''
        out.append(f'<li class="{cls}"><b>{T(name)}</b>{T(d)}</li>')
    return f'<ul class="checklist">{"".join(out)}</ul>'

def tests_table(p, n=None):
    t = tests_of(p['dir'])
    rows = t if n is None else t[:n]
    trs = ''.join(f'<tr><td>{flink(path)}</td><td class="num">{c}</td></tr>' for path, c in rows)
    more = f'<p class="note">{T((f"另有 {len(t) - len(rows)} 个测试文件未列出（共 {len(t)} 个，{sum(c for _, c in t)} 个用例）。", f"{len(t) - len(rows)} more test files not listed ({len(t)} files, {sum(c for _, c in t)} cases in total)."))}</p>' if len(rows) < len(t) else ''
    return (f'<div class="tbl"><table><thead><tr><th>{T(("测试文件", "Test file"))}</th><th class="num">{T(("用例", "cases"))}</th></tr></thead><tbody>{trs}</tbody></table></div>{more}'
            f'<p class="note">{T(("用例数 = 源码中 `it(` / `test(` 的出现次数（静态统计，不运行测试）。", "Cases = occurrences of `it(` / `test(` in the source (static count; tests were not run)."))}</p>')

def largest_table(p, n=10):
    trs = ''.join(f'<tr><td>{flink(path)}</td><td class="num">{fmt(c)}</td></tr>' for path, c in largest(p['dir'], n))
    return f'<div class="tbl"><table><thead><tr><th>{T(("源文件（按行数）", "Source file (by lines)"))}</th><th class="num">{T(("行", "lines"))}</th></tr></thead><tbody>{trs}</tbody></table></div>'

def exports_paths_table(p, notes=None):
    j = json.loads(read(f'packages/{p["dir"]}/package.json'))
    ex = j.get('exports') or {}
    ln = line_of(f'packages/{p["dir"]}/package.json', r'"exports"') if ex else None
    rows = []
    for k, v in ex.items():
        if k == './package.json': continue
        tgt = v.get('import') if isinstance(v, dict) else v
        note = (notes or {}).get(k)
        rows.append(f'<tr><td><code>{esc(p["npm"] + k[1:])}</code></td><td class="sym"><code>{esc(str(tgt))}</code></td><td class="col-role">{T(note) if note else ""}</td></tr>')
    if not rows: return f'<p class="note">{T(("package.json 没有 exports 字段（使用 main / types）。", "package.json has no exports map (uses main / types)."))}</p>'
    return (f'<div class="tbl"><table><thead><tr><th>{T(("导入路径", "Import path"))}</th><th>{T(("目标", "Target"))}</th><th class="col-role">{T(("说明", "Notes"))}</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
            f'<p class="note">{flink(f"packages/{p["dir"]}/package.json", ln, "package.json · exports")}</p>')
