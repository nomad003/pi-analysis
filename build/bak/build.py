#!/usr/bin/env python3
"""Build /workspace/pi-site from source-grounded content. Every file link is resolved against /workspace/pi-src."""
import html, json, os, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path('/workspace/pi-src')
OUT = Path(os.environ.get('PI_OUT', '/workspace/pi-site'))
sys.path.insert(0, str(HERE))
from content import SECTIONS, GROUPS  # noqa
from figs import build_all  # noqa
from svgkit import DEFS  # noqa
FIGS = build_all()
for _k, _f in FIGS.items():
    assert not _f.lint(), (_k, _f.lint())
from slides import SLIDES  # noqa

SHA = subprocess.check_output(['git', '-C', str(SRC), 'rev-parse', 'HEAD'], text=True).strip()
SHORT = SHA[:7]
GH = f'https://github.com/earendil-works/pi'
COMMIT_DATE = subprocess.check_output(['git', '-C', str(SRC), 'log', '-1', '--format=%cI'], text=True).strip()

# ---------------------------------------------------------------- facts (computed, then asserted)
def read(p): return (SRC / p).read_text(errors='ignore')

def line_of(path, pattern):
    if pattern is None: return None
    for i, l in enumerate(read(path).splitlines(), 1):
        if re.search(pattern, l): return i
    raise SystemExit(f'pattern not found: {path} :: {pattern}')

def gh(path, line=None):
    kind = 'tree' if (SRC / path).is_dir() else 'blob'
    if not (SRC / path).exists(): raise SystemExit('missing path ' + path)
    return f'{GH}/{kind}/{SHA}/{path}' + (f'#L{line}' if line else '')

pkgs = sorted(p.name for p in (SRC / 'packages').iterdir() if (p / 'package.json').exists())
providers = len(re.findall(r'^import \{ \w+Provider \} from "\./', read('packages/ai/src/providers/all.ts'), re.M))
api = read('packages/coding-agent/src/core/extensions/types.ts')
api_block = api[api.index('export interface ExtensionAPI'):]
api_block = api_block[:api_block.index('\n}\n')]
ext_events = sorted(set(re.findall(r'\bon\(\s*event: "([a-z_]+)"', api_block)))
rpc = read('packages/coding-agent/src/modes/rpc/rpc-types.ts')
rpc_block = re.search(r'export type RpcCommand\s*=(.*?);\n\n', rpc, re.S).group(1)
rpc_cmds = sorted(set(re.findall(r'type: "([a-z_]+)"', rpc_block)))
tools = re.findall(r'"(\w+)"', re.search(r'export type ToolName = (.*);', read('packages/coding-agent/src/core/tools/index.ts')).group(1))
ai_events = re.findall(r'type: "([a-z_]+)"', re.search(r'export type AssistantMessageEvent\b(.*?)\n\n', read('packages/ai/src/types.ts'), re.S).group(1))
entry_types = sorted(set(re.findall(r'^\ttype: "([a-z_]+)";', read('packages/coding-agent/src/core/session-manager.ts'), re.M)) - {'session'})
known_api = re.findall(r'\| "([a-z-]+)"', re.search(r'export type KnownApi =(.*?);', read('packages/ai/src/types.ts'), re.S).group(1))
FACTS = dict(apis=len(known_api), packages=len(pkgs), providers=providers, ext_events=len(ext_events), rpc=len(rpc_cmds), tools=len(tools),
             ai_events=len(ai_events), entries=len(entry_types), modes=4)
EXPECT = dict(apis=10, packages=14, providers=42, ext_events=41, rpc=33, tools=8, ai_events=12, entries=11, modes=4)
assert FACTS == EXPECT, (FACTS, EXPECT)

# repo stats (same method as the original analysis)
def count_stats():
    out = []
    for p in pkgs:
        sf = sl = tf = tl = al = 0
        root = SRC / 'packages' / p
        for dp, dns, fns in os.walk(root):
            dns[:] = [x for x in dns if x not in ('node_modules', 'dist')]
            for f in fns:
                if not f.endswith('.ts') or f.endswith('.d.ts'): continue
                fp = Path(dp) / f; rel = fp.relative_to(root).as_posix(); al += 1
                n = sum(1 for _ in open(fp, errors='ignore'))
                if re.match(r'test[^/]*/', rel) or '.test.' in f: tf += 1; tl += n
                elif rel.startswith('src/'): sf += 1; sl += n
        out.append(dict(pkg=p, src_files=sf, src_loc=sl, test_files=tf, test_loc=tl, all_ts_files=al))
    return out
STATS = count_stats()
SRC_LOC = sum(s['src_loc'] for s in STATS); TEST_LOC = sum(s['test_loc'] for s in STATS)
PKG_LAYER = {'coding-agent': 'coding', 'agent': 'agent', 'ai': 'ai', 'tui': 'tui'}

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

ICON = {
 'sun': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6"/></svg>',
 'moon': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5a8.5 8.5 0 1 0 10.7 10.7Z"/></svg>',
 'menu': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h10"/></svg>',
 'gh': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.16-1.11-1.47-1.11-1.47-.9-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.9 1.52 2.34 1.08 2.91.83.09-.65.35-1.08.63-1.33-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02a9.5 9.5 0 0 1 5 0c1.91-1.3 2.75-1.02 2.75-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.85v2.75c0 .27.18.58.69.48A10 10 0 0 0 12 2Z"/></svg>',
 'play': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5.5v13a1 1 0 0 0 1.5.86l10.5-6.5a1 1 0 0 0 0-1.72L9.5 4.64A1 1 0 0 0 8 5.5Z"/></svg>',
 'expand': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7"/></svg>',
 'list': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01"/></svg>',
 'gear': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/></svg>',
 'file': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/></svg>',
}
LAYER_NAME = {'modes': 'Run modes', 'coding': 'pi-coding-agent', 'ext': 'Extensions', 'agent': 'pi-agent-core', 'ai': 'pi-ai', 'tui': 'pi-tui', 'infra': 'Infra'}

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
}

def figure(key, title_pair):
    cap = CAPTION[key]
    return (f'<figure class="diagram" id="fig-{key}"><figcaption><span class="cap">{T(cap)}</span>'
            f'<button class="iconbtn expand" type="button" data-i18n-title="放大查看|Enlarge">{ICON["expand"]}</button></figcaption>'
            f'<div class="diagram-body"><div class="swipe-hint">{T(("← 左右滑动查看，点击放大 →", "← swipe to scroll, tap to enlarge →"))}</div>'
            f'<div class="dg" data-dg="{key}" aria-label="{html.escape(title_pair[1])} diagram">{FIGS[key].svg()}</div></div></figure>')

def files_table(files):
    rows = []
    for path, pat, sym, zh, en in files:
        ln = line_of(path, pat)
        d, _, b = path.rpartition('/')
        rows.append(f'<tr><td><a class="f" href="{gh(path, ln)}" target="_blank" rel="noopener"><span><span class="dir">{html.escape(d + "/" if d else "")}</span>{html.escape(b)}</span>'
                    f'{f"<span class=ln>L{ln}</span>" if ln else ""}</a></td><td class="sym"><code>{html.escape(sym)}</code></td>'
                    f'<td class="col-role">{T((zh, en))}</td></tr>')
    head = f'<thead><tr><th>{T(("文件", "File"))}</th><th>{T(("符号", "Symbol"))}</th><th class="col-role">{T(("作用", "Role"))}</th></tr></thead>'
    return f'<div class="tbl"><table>{head}<tbody>{"".join(rows)}</tbody></table></div>'

def section(i, s):
    L = s['layer']
    pts = ''.join(f'<li>{T(p)}</li>' for p in s['points'])
    how = ''.join(f'<li>{T(p)}</li>' for p in s['how'])
    return f'''<section class="sec L-{L}" id="{s["id"]}" aria-labelledby="h-{s["id"]}">
<div class="sec-meta"><span class="sec-no">{i:02d}</span><span class="chip L-{L}">{LAYER_NAME[L]}</span></div>
<h2 id="h-{s["id"]}">{T(s["title"])}<a class="anchor" href="#{s["id"]}" aria-label="link">#</a></h2>
<p class="takeaway"><span class="tl">{T(("一句话结论", "Takeaway"))}</span>{T(s["takeaway"])}</p>
{figure(s["diagram"], s["title"])}
<div class="grid2"><div class="card"><h3>{ICON["list"]}{T(("要点", "Key points"))}</h3><ul>{pts}</ul></div>
<div class="card"><h3>{ICON["gear"]}{T(("工作原理", "How it works"))}</h3><ol>{how}</ol></div></div>
<div class="files"><h3>{ICON["file"]}{T(("关键文件", "Key files"))} <span style="font-weight:500;letter-spacing:0;text-transform:none">· {SHORT}</span></h3>{files_table(s["files"])}</div>
</section>'''

def stats_section(i):
    rows = sorted(STATS, key=lambda x: -x['src_loc'])
    mx = max(s['src_loc'] + s['test_loc'] for s in rows)
    bars = ''.join(
        f'<div class="bar L-{PKG_LAYER.get(s["pkg"], "infra")}"><span class="nm">{s["pkg"]}</span><span class="tr">'
        f'<span class="s" style="width:{s["src_loc"] / mx * 100:.2f}%"></span><span class="t" style="width:{s["test_loc"] / mx * 100:.2f}%"></span></span>'
        f'<span class="v">{fmt(s["src_loc"])}</span></div>' for s in rows)
    trs = ''.join(f'<tr><td><span class="chip L-{PKG_LAYER.get(s["pkg"], "infra")}">{s["pkg"]}</span></td><td class="num">{s["src_files"]}</td><td class="num">{fmt(s["src_loc"])}</td>'
                  f'<td class="num">{s["test_files"]}</td><td class="num">{fmt(s["test_loc"])}</td><td class="num col-role">{s["all_ts_files"]}</td></tr>' for s in rows)
    tot = lambda k: fmt(sum(s[k] for s in STATS))
    trs += f'<tr class="tot"><td>{T(("合计", "Total"))}</td><td class="num">{tot("src_files")}</td><td class="num">{tot("src_loc")}</td><td class="num">{tot("test_files")}</td><td class="num">{tot("test_loc")}</td><td class="num col-role">{tot("all_ts_files")}</td></tr>'
    ca = next(s for s in STATS if s['pkg'] == 'coding-agent')
    return f'''<section class="sec L-infra" id="stats" aria-labelledby="h-stats">
<div class="sec-meta"><span class="sec-no">{i:02d}</span><span class="chip L-infra">Repository</span></div>
<h2 id="h-stats">{T(("仓库统计", "Repository stats"))}<a class="anchor" href="#stats">#</a></h2>
<p class="takeaway L-coding"><span class="tl">{T(("一句话结论", "Takeaway"))}</span>{T((f"约 {SRC_LOC/1000:.0f}k 行源码、{TEST_LOC/1000:.0f}k 行测试；`coding-agent` 一个包就占了 {ca['src_loc']/SRC_LOC*100:.0f}% 的源码，测试代码量与源码相当。", f"About {SRC_LOC/1000:.0f}k lines of source and {TEST_LOC/1000:.0f}k of tests; `coding-agent` alone is {ca['src_loc']/SRC_LOC*100:.0f}% of the source, and test code roughly matches source code."))}</p>
<p class="note">{T((f"统计自提交 `{SHORT}`：只计 `.ts`（不含 `.d.ts`），排除 node_modules 与 dist；src = `src/` 下，test = `test*/` 下或 `*.test.*`。", f"Counted at commit `{SHORT}`: `.ts` only (no `.d.ts`), node_modules and dist excluded; src = under `src/`, test = under `test*/` or `*.test.*`."))}</p>
<div class="bars-key"><span><i></i>{T(("源码行数", "src LOC"))}</span><span><i class="t"></i>{T(("测试行数", "test LOC"))}</span></div>
<div class="bars" role="img" aria-label="Lines of code by package">{bars}</div>
<div class="tbl"><table><thead><tr><th>{T(("包", "Package"))}</th><th class="num">{T(("源文件", "src files"))}</th><th class="num">{T(("源码行", "src LOC"))}</th><th class="num">{T(("测试文件", "test files"))}</th><th class="num">{T(("测试行", "test LOC"))}</th><th class="num col-role">{T(("全部 .ts", "all .ts"))}</th></tr></thead><tbody>{trs}</tbody></table></div>
</section>'''

HEAD = lambda title, css, extra='': f'''<!doctype html>
<html lang="zh-CN" data-theme="light" data-lang="zh"{extra}><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="Source-grounded architecture walkthrough of earendil-works/pi at {SHORT}: agent loop, tools, sessions, compaction, extensions, providers, TUI.">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230b0d12'/%3E%3Ctext x='16' y='23' font-size='20' text-anchor='middle' fill='%23a78bfa' font-family='serif'%3E%CF%80%3C/text%3E%3C/svg%3E">
<script src="assets/prefs.js"></script>
<link rel="stylesheet" href="assets/base.css">{''.join(f'<link rel="stylesheet" href="assets/{c}">' for c in css)}
</head>'''

def build_index():
    by_group = {}
    for i, s in enumerate(SECTIONS, 1): by_group.setdefault(s['group'], []).append((i, s))
    toc = [f'<div class="toc-g">{T(GROUPS[0][1])}</div><a href="#top" style="--l:var(--accent)"><span class="no">00</span>{T(("概览", "Overview"))}</a>']
    for gid, gname in GROUPS:
        items = by_group.get(gid, [])
        if gid == 'data': items = [(len(SECTIONS) + 1, dict(id='stats', title=('仓库统计', 'Repository stats'), layer='infra'))]
        if gid != 'overview': toc.append(f'<div class="toc-g">{T(gname)}</div>')
        for i, s in items:
            toc.append(f'<a href="#{s["id"]}" class="L-{s["layer"]}"><span class="no">{i:02d}</span><span>{T(s["title"])}</span><span class="dot"></span></a>')
    toc.append(f'<div class="toc-foot"><a href="slides.html">▶ {T(("演示模式（{} 页）".format(len(SLIDES)), "Presentation ({} slides)".format(len(SLIDES))))}</a>'
               f'<a href="{GH}/tree/{SHA}" target="_blank" rel="noopener">GitHub · {SHORT}</a></div>')
    stat_cards = [
        (fmt(FACTS['packages']), ('个 workspace 包', 'workspace packages')),
        (f'{SRC_LOC/1000:.0f}k', ('行 TypeScript 源码', 'lines of TS source')),
        (f'{TEST_LOC/1000:.0f}k', ('行测试代码', 'lines of tests')),
        (str(FACTS['providers']), ('个内置 LLM provider', 'built-in LLM providers')),
        (str(FACTS['tools']), ('个内置工具', 'built-in tools')),
        (str(FACTS['ext_events']), ('种扩展事件', 'extension events')),
        (str(FACTS['rpc']), ('种 RPC 命令', 'RPC command types')),
        (str(FACTS['modes']), ('种运行模式', 'run modes')),
    ]
    stats = ''.join(f'<div class="stat"><div class="n">{n}</div><div class="k">{T(k)}</div></div>' for n, k in stat_cards)
    stack = f'''<div class="stack" aria-label="layer stack">
<div class="stack-h"><span>{T(("运行时分层", "Runtime layers"))}</span><span>↓ {T(("一次请求", "one request"))}</span></div>
<a class="tier L-modes" href="#modes"><b>Run modes</b><span>interactive · print · json · rpc</span></a>
<div class="tier-row"><a class="tier L-coding" href="#layers"><b>pi-coding-agent</b><span>AgentSession</span></a><a class="tier L-ext" href="#extensions"><b>Extensions</b><span>{FACTS["ext_events"]} events</span></a></div>
<a class="tier L-agent" href="#loop"><b>pi-agent-core</b><span>runLoop · tools</span></a>
<a class="tier L-ai" href="#providers"><b>pi-ai</b><span>{FACTS["providers"]} providers · {FACTS["ai_events"]} events</span></a>
<a class="tier L-tui" href="#tui"><b>pi-tui</b><span>differential renderer</span></a>
</div>'''
    legend = f'''<div class="legend" id="legend"><h2>{T(("如何阅读这些图", "How to read the diagrams"))}</h2>
<div class="chips">{''.join(f'<span class="chip L-{k}">{v}</span>' for k, v in LAYER_NAME.items())}</div>
<ul><li>{T(("颜色 = 代码所在的层 / 包，所有图、表与幻灯片一致。", "Colour = the layer / package the code lives in, identical across every diagram, table and slide."))}</li>
<li>{T(("圆角容器 = 包或层；卡片 = 类、函数或组件；深色胶囊 = 起止点；红色 = 错误路径。", "Rounded containers = packages or layers; cards = classes, functions or components; dark pill = start / end; red = error path."))}</li>
<li>{T(("实线箭头 = 调用 / 依赖；虚线 = 事件、异步返回或 devDependency；流动的虚线标出主路径；圆形数字 = 执行顺序。", "Solid arrow = call / dependency; dashed = event, async return or devDependency; animated dashes mark the main path; numbered circles = execution order."))}</li>
<li>{T(("每张图右下都有图例。鼠标悬停某个组件会高亮它的连线；点击图可放大、滚轮缩放、拖动平移。", "Every diagram carries its own legend. Hover a component to highlight its connections; click to enlarge, wheel to zoom, drag to pan."))}</li></ul></div>'''
    secs = ''.join(section(i, s) for i, s in enumerate(SECTIONS, 1)) + stats_section(len(SECTIONS) + 1)
    page = HEAD('Pi 架构图解 · earendil-works/pi', ['site.css', 'dg.css']) + f'''
<body data-title-zh="Pi 架构图解 · earendil-works/pi" data-title-en="Pi architecture, illustrated · earendil-works/pi">
<header class="topbar"><div class="wrap">
<button class="iconbtn only-mobile" id="toc-btn" type="button" data-i18n-title="目录|Contents">{ICON["menu"]}</button>
<a class="brand" href="#top"><span class="logo"><span>π</span></span><span class="t">{T(("Pi 架构图解", "Pi, illustrated"))}</span><small>{SHORT}</small></a>
<nav class="topnav"><a href="#layers">{T(("架构", "Architecture"))}</a><a href="#loop">{T(("运行时", "Runtime"))}</a><a href="#extensions">{T(("扩展", "Extensions"))}</a><a href="#stats">{T(("统计", "Stats"))}</a></nav>
<span class="spacer"></span>
<div class="tools">
<a class="btn sm" href="slides.html">{ICON["play"].replace("<svg", "<svg width=14 height=14")}<span class="t2">{T(("演示", "Slides"))}</span></a>
<div class="seg" role="group" aria-label="Language"><button type="button" data-set-lang="zh">中</button><button type="button" data-set-lang="en">EN</button></div>
<button class="iconbtn" id="theme-btn" type="button" data-i18n-title="切换明暗|Toggle theme"><span class="th-moon">{ICON["moon"]}</span><span class="th-sun">{ICON["sun"]}</span></button>
<a class="iconbtn gh" href="{GH}/tree/{SHA}" target="_blank" rel="noopener" data-i18n-title="GitHub 源码|Source on GitHub">{ICON["gh"]}</a>
</div></div><div class="progress"></div></header>

<section class="hero" id="top"><div class="wrap"><div>
<a class="eyebrow" href="{GH}/tree/{SHA}" target="_blank" rel="noopener"><b>{SHORT}</b>earendil-works/pi · {COMMIT_DATE[:10]}</a>
<h1>{T(("读懂 <grad>Pi</grad>：<br>一个可扩展的<br>编码智能体内核", "Inside <grad>Pi</grad>:<br>an extensible coding-agent core"), cls="h1")}</h1>
<p class="lead">{T(("基于源码逐行核对的架构导读。12 张图覆盖包依赖、Agent 循环、工具执行、会话树、压缩、扩展、运行模式、Provider 与 TUI；每个结论都链接到对应提交中的具体代码行。", "An architecture walkthrough checked line by line against the source. Twelve diagrams cover packages, the agent loop, tool execution, the session tree, compaction, extensions, run modes, providers and the TUI — every claim links to the exact lines at this commit."))}</p>
<div class="cta"><a class="btn primary" href="#packages">{T(("开始阅读", "Start reading"))} →</a><a class="btn" href="slides.html">{ICON["play"].replace("<svg", "<svg width=15 height=15")}{T(("演示模式 · {} 页".format(len(SLIDES)), "Presentation · {} slides".format(len(SLIDES))))}</a></div>
<div class="stats">{stats}</div></div>
{stack}
</div></section>

<div class="wrap layout"><aside class="toc" aria-label="Contents">{"".join(toc)}</aside>
<main id="main">{DEFS}{legend}{secs}
<footer class="foot"><span>{T((f"内容依据 earendil-works/pi 提交 `{SHORT}`（{COMMIT_DATE[:10]}）生成，所有链接指向该提交。", f"Generated from earendil-works/pi at `{SHORT}` ({COMMIT_DATE[:10]}); every link points at that commit."))}</span>
<span>{T(("离线可用 · 无 CDN 依赖", "Works offline · no CDN"))}</span></footer></main></div>
<script src="assets/dg.js"></script><script src="assets/site.js"></script>
</body></html>'''
    page = page.replace('&lt;grad&gt;', '<span class="grad">').replace('&lt;/grad&gt;', '</span>').replace('&lt;br&gt;', '<br>')
    (OUT / 'index.html').write_text(page)

# ---------------------------------------------------------------- slides
def build_slides():
    from slides import render_slides
    body = render_slides(T=T, md=md, FACTS=FACTS, STATS=STATS, SRC_LOC=SRC_LOC, TEST_LOC=TEST_LOC, SHORT=SHORT, SHA=SHA, GH=GH,
                         COMMIT_DATE=COMMIT_DATE, ICON=ICON, FIGS=FIGS, DEFS=DEFS, PKG_LAYER=PKG_LAYER, LAYER_NAME=LAYER_NAME, fmt=fmt)
    i = body.index('<body'); i = body.index('>', i) + 1
    body = body[:i] + DEFS + body[i:]
    page = HEAD('Pi 架构 · 演示', ['slides.css', 'dg.css'], extra=' data-default-theme="dark"') + body
    (OUT / 'slides.html').write_text(page)

# ---------------------------------------------------------------- fonts (subset, offline)
def build_fonts(text):
    from fontTools import subset
    from fontTools.ttLib import TTCollection
    fd = OUT / 'assets/fonts'; fd.mkdir(parents=True, exist_ok=True)
    g = '/usr/share/fonts/truetype/sand-box/google'
    latin = 'U+0000-00FF,U+0131,U+0152-0153,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2190-21FF,U+2212,U+2215,U+2260-2265,U+25A0-25FF,U+2713,U+2715,U+FEFF,U+FFFD'
    def sub(src, dst, unicodes=None, text=None, idx=0):
        opts = subset.Options(); opts.flavor = 'woff2'; opts.layout_features = ['*']; opts.name_IDs = ['*']; opts.font_number = idx
        f = subset.load_font(src, opts, dontLoadGlyphNames=True)
        s = subset.Subsetter(opts)
        s.populate(unicodes=subset.parse_unicodes(unicodes) if unicodes else [], text=text or '')
        s.subset(f); subset.save_font(f, str(fd / dst), opts)
    sub(f'{g}/Inter/Inter-VariableFont_opsz,wght.ttf', 'inter-var.woff2', latin)
    sub(f'{g}/JetBrains Mono/JetBrainsMono-VariableFont_wght.ttf', 'jbmono-var.woff2', latin)
    cjk = ''.join(sorted(set(ch for ch in text if ord(ch) >= 0x2E80))) + '，。：；！？（）、《》“”‘’…—「」'
    for w, file in (('400', 'NotoSansCJK-Regular.ttc'), ('700', 'NotoSansCJK-Bold.ttc')):
        path = f'/usr/share/fonts/opentype/noto/{file}'
        idx = next(i for i, ft in enumerate(TTCollection(path).fonts) if 'SC' in ft['name'].getDebugName(1))
        sub(path, f'cjk-{w}.woff2', None, cjk, idx)
    return len(cjk)

def main():
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT / 'assets').mkdir(parents=True)
    for f in (HERE / 'static').iterdir():
        if f.name == 'mmd.js': continue
        shutil.copy(f, OUT / 'assets' / f.name)
    (OUT / 'assets/stats.json').write_text(json.dumps(dict(commit=SHA, facts=FACTS, packages=STATS, extension_events=ext_events,
                                                         rpc_commands=rpc_cmds, tools=tools, session_entry_types=entry_types), indent=1))
    build_index(); build_slides()
    text = (OUT / 'index.html').read_text() + (OUT / 'slides.html').read_text() + ''.join(p.read_text() for p in (OUT / 'assets').glob('*.js'))
    n = build_fonts(text)
    print('built', OUT, FACTS, 'src', SRC_LOC, 'test', TEST_LOC, 'cjk glyphs', n, 'slides', len(SLIDES))

if __name__ == '__main__': main()
