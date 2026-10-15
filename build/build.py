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

# The analysed source is the Pi release tag v1.1.0. Every GitHub link points at the tag.
VERSION = '1.1.0'
REF = 'v' + VERSION
SHA = subprocess.check_output(['git', '-C', str(SRC), 'rev-parse', 'HEAD'], text=True).strip()
TAG_SHA = subprocess.check_output(['git', '-C', str(SRC), 'rev-parse', REF + '^{commit}'], text=True).strip()
assert SHA == TAG_SHA, f'/workspace/pi-src must be checked out at {REF} ({TAG_SHA[:9]}), found {SHA[:9]}'
SHORT = SHA[:7]
GH = 'https://github.com/earendil-works/pi'
COMMIT_DATE = subprocess.check_output(['git', '-C', str(SRC), 'log', '-1', '--format=%cI'], text=True).strip()
SITE = ('图解 Pi Agent', 'Pi Agent, Illustrated')
SUBTITLE = (f'Pi v{VERSION} 源码分析', f'Analysis of Pi v{VERSION}')

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
    return f'{GH}/{kind}/{REF}/{path}' + (f'#L{line}' if line else '')

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

# ---------------------------------------------------------------- package registry + version check
import pkgmeta, deep_agent, deep_ai, deep_ca, deep_tui, deep_mcp, deep_cm, deep_chord, deep_durable, deep_env  # noqa
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
 'ca_arch': ('四个入口、core/ 的主要模块（标签为行数）与依赖', 'Four entry points, the main core/ modules (tags = lines) and dependencies'),
 'ca_startup': ('main() 从参数到运行模式的 14 步', 'The 14 steps in main(), from arguments to run mode'),
 'ca_session': ('AgentSession 为 Agent 的每个钩子安装的实现，以及运行后的外层循环', 'What AgentSession installs into each Agent hook, and the post-run outer loop'),
 'ca_runtime': ('替换会话的 6 步与取消分支', 'The six steps of replacing a session, and the cancel branch'),
 'ca_tools': ('8 个内置工具、截断上限与可替换的 Operations', 'The eight built-in tools, truncation limits and swappable Operations'),
 'ca_jsonl': ('会话文件的位置、内容、条目类型与读写路径', 'Session file location, contents, entry types, and the write and read paths'),
 'ca_extapi': ('pi 对象的方法分组、41 种事件与 ctx', 'Method groups on pi, the 41 events, and ctx'),
 'ca_rpc': ('stdin / stdout 上的五种消息与全部 RPC 命令', 'The five message kinds on stdin / stdout and every RPC command'),
 'ca_config': ('设置合并、资源加载流程与 system prompt 分段', 'Settings merge, the resource load pipeline and system prompt sections'),
 'tui_arch': ('四组模块与 components/（标签为行数）', 'Four module groups and components/ (tags = lines)'),
 'tui_component': ('接口、一棵组件树示例、每帧的约定与内置组件', 'Interfaces, an example tree, the per-frame contract and built-in components'),
 'tui_render': ('渲染调度、帧准备与 regular 屏幕的 7 个判断', 'Render scheduling, frame preparation and the regular screen\'s seven checks'),
 'tui_screens': ('regular 与 fullscreen 的对比及备用屏的一帧', 'Regular vs fullscreen, and one alternate-screen frame'),
 'tui_input': ('从 stdin 字节到组件的 8 步输入分发', 'Eight-step input dispatch from stdin bytes to the component'),
 'tui_editor': ('Editor 的状态、按键分支顺序与自动补全', 'Editor state, key-branch order and autocomplete'),
 'tui_overlay': ('覆盖层选项、9 个锚点、合成步骤与焦点栈', 'Overlay options, nine anchors, compositing and the focus stack'),
 'tui_terminal': ('启动协商、输出序列与按终端识别的能力', 'Start-up negotiation, output sequences and per-terminal capabilities'),
 'mcp_arch': ('三组模块、四个导入路径与 pi 中的使用者', 'Three module groups, the import paths and the user inside pi'),
 'mcp_lifecycle': ('连接状态机、initialize 握手与双方能力', 'The connection state machine, the initialize handshake and both sides\' capabilities'),
 'mcp_requests': ('请求簿记、超时与取消、服务器请求与分页', 'Request bookkeeping, timeouts and cancellation, server requests and paging'),
 'mcp_stdio': ('启动子进程、按行分帧与分阶段关闭', 'Spawning the child, line framing and the staged close'),
 'mcp_http': ('POST 的三种响应、错误映射与 SSE 重连', 'The three POST responses, error mapping and SSE reconnects'),
 'mcp_oauth': ('触发条件、授权流程六步与本地回调服务器', 'Triggers, the six-step flow and the local callback server'),
 'mcp_content': ('结果内容到模型内容的映射与错误类型', 'Mapping result content to model content, and the error types'),
 'mcp_pi': ('配置来源、运行时、工具命名与四种曝光方式', 'Config sources, the runtime, tool naming and the four exposures'),
 'cm_arch': ('宿主、沙箱内与给模型看的三组模块', 'Host, in-sandbox and model-facing module groups'),
 'cm_sandbox': ('宿主线程、worker 线程与 QuickJS 虚拟机', 'The host thread, the worker thread and the QuickJS VM'),
 'cm_exec': ('一次 execute() 的步骤与五种结局', 'The steps of one execute() and its five endings'),
 'cm_bridge': ('一次工具调用在 VM、worker 与宿主之间的往返', 'One tool call\'s round trip between VM, worker and host'),
 'cm_prelude': ('脚本 API、硬限额、锁定与保留名', 'The script API, hard limits, lockdown and reserved names'),
 'cm_types': ('公共类型与 @options 源码格式', 'Public types and the @options source format'),
 'cm_decl': ('从 JSON Schema 到 TypeScript 声明', 'From JSON Schema to TypeScript declarations'),
 'cm_pi': ('codemode 工具：嵌套调用、globals 与 store 条目', 'The codemode tool: nested calls, globals and store entries'),
 'chord_arch': ('chord 的模块、导入路径与 pi 中的使用者', 'chord modules, import paths and the user inside pi'),
 'chord_facets': ('一个 facet 代：setup、校验、连接、激活与释放', 'One facet generation: setup, validation, wiring, activation and release'),
 'chord_reload': ('reload(facets)：句柄不断开地替换实现', 'reload(facets): replacing implementations without breaking handles'),
 'chord_services': ('服务令牌、模式、稳定句柄与 Context', 'Service tokens, modes, stable handles and Context'),
 'chord_remote': ('跨进程服务：provider、transport 与 binding', 'Services across processes: provider, transport and binding'),
 'chord_state': ('复制状态：一次 change() 如何变成远端的新值', 'Replicated state: how one change() becomes a new value on the other side'),
 'chord_delta': ('Delta 的 7 种 op 与线上压缩', 'The seven delta ops and on-the-wire compression'),
 'chord_bundle': ('esbuild 打包、清单与校验后在 node:vm 中加载', 'Bundling with esbuild, the manifest, and verified loading in node:vm'),
 'dur_arch': ('durable 的模块、子路径与使用者', 'durable modules, subpaths and users'),
 'dur_model': ('概念模型：一切都是提交到存储里的记录', 'The model: everything is a record committed to storage'),
 'dur_run': ('回答一次输入：条目与任务按时间排开', 'One answered input, as entries and tasks over time'),
 'dur_tasks': ('Task：可恢复的状态机与所有权', 'Tasks: a resumable state machine with ownership'),
 'dur_inbox': ('会话忙时的提交：steer、followUp、reject 与 write', 'Submitting to a busy conversation: steer, followUp, reject and write'),
 'dur_docs': ('文档与观察：UI 需要的都是已提交的状态', 'Documents and watching: everything a UI needs is committed state'),
 'dur_storage': ('一个 commit(writes) 接口，四种存储后端', 'One commit(writes) interface, four storage backends'),
 'dur_ext': ('扩展：工具、提示词段、钩子、包装器与任务', 'Extensions: tools, sections, hooks, wraps and tasks'),
 'env_arch': ('TypeScript 客户端与 Rust 守护进程的模块', 'The modules of the TypeScript client and the Rust daemon'),
 'env_split': ('分工：结果要与远端的 NodeExecutionEnv 一致', 'The split of work: results must match NodeExecutionEnv on the remote machine'),
 'env_ssh': ('经 SSH 连上一台机器：信任、探测、部署与启动', 'Reaching a machine over SSH: trust, detection, deployment and start'),
 'env_frames': ('线上格式：同步行之后只有帧', 'The wire format: after the sync line, only frames'),
 'env_session': ('一条连接的一生：懒启动、心跳与丢失后重启', 'The life of a connection: lazy start, heartbeats and restart after loss'),
 'env_exec': ('exec：命令、输出窗口、溢出文件与取消', 'exec: commands, output windows, spill files and cancellation'),
 'env_files': ('ExecutionEnv 的文件方法与守护进程的 17 个文件 op', "ExecutionEnv file methods and the daemon's 17 file ops"),
 'env_watch': ('文件监视：在文件旁边运行的 NodeFileWatcher', 'Watching: NodeFileWatcher running next to the files'),
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
# ---------------------------------------------------------------- package pages
GROUP_TOC = {'arch': ('架构', 'Architecture'), 'flows': ('关键流程', 'Key flows'), 'types': ('数据类型', 'Data types'), 'ref': ('参考', 'Reference'), 'v1': ('第一版章节', 'First-edition sections')}

def api_section_agent(i, p):
    files = ['index.ts', 'agent.ts', 'agent-loop.ts', 'proxy.ts', 'stream-fn.ts', 'types.ts']
    rows = []
    idx = read('packages/agent/src/index.ts')
    for f in files[1:]:
        path = 'packages/agent/src/' + f
        ex = exports_of(path)
        if f == 'stream-fn.ts': ex = [e for e in ex if e[1] in idx]
        vals = [e for e in ex if e[0] not in ('type', 'interface')]
        types = [e for e in ex if e[0] in ('type', 'interface')]
        link = lambda e: f'<a href="{gh(path, e[2])}" target="_blank" rel="noopener"><code>{esc(e[1])}</code></a>'
        rows.append(f'<tr><td>{flink(path)}</td><td>{" ".join(link(e) for e in vals) or "—"}</td><td class="col-role">{" ".join(link(e) for e in types) or "—"}</td></tr>')
    nv = sum(1 for f in files[1:] for e in exports_of('packages/agent/src/' + f) if e[0] not in ('type', 'interface'))
    return sec_open(i, 'api', 'agent', ('公共 API', 'Public API')) + f'''
<p class="takeaway"><span class="tl">{T(("一句话结论", "Takeaway"))}</span>{T(("只有一个导入路径 `@earendil-works/pi-agent-core`。日常只需要 `Agent`；需要自己管理状态时直接用 `agentLoop()` / `runAgentLoop()`；`runToolCall()` 让宿主在循环之外复用同一套工具管道。", "There is a single import path, `@earendil-works/pi-agent-core`. Day to day you only need `Agent`; manage state yourself with `agentLoop()` / `runAgentLoop()`; `runToolCall()` lets a host reuse the same tool pipeline outside the loop."))}</p>
<div class="tbl"><table><thead><tr><th>{T(("文件", "File"))}</th><th>{T(("值导出", "Value exports"))}</th><th class="col-role">{T(("类型导出", "Type exports"))}</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<p class="note">{T(("由构建脚本扫描 `export` 声明生成，每个符号都链接到 v1.1.0 中的定义行。`getDefaultStreamFn` 未从 index.ts 导出。", "Generated by scanning `export` declarations at build time; each symbol links to its definition at v1.1.0. `getDefaultStreamFn` is not re-exported from index.ts."))}</p>
</section>'''

AI_EXPORT_NOTES = {
 '.': ('核心：类型、`Type`、`createModels`、`createProvider`、事件流、工具函数', 'core: types, `Type`, `createModels`, `createProvider`, event streams, helpers'),
 './models': ('只有 Models 运行时', 'Models runtime only'),
 './compat': ('旧全局 API（已弃用）', 'old global API (deprecated)'),
 './providers/*': ('每个 provider 一个文件；`all` = 全部', 'one file per provider; `all` = everything'),
 './api/*': ('直接使用某个 API 实现（立即加载 SDK）', 'one API implementation directly (eager SDK)'),
 './utils/*': ('event-stream、validation、overflow 等', 'event-stream, validation, overflow …'),
 './oauth': ('OAuth 登录辅助', 'OAuth login helpers'),
 './bedrock-provider': ('Amazon Bedrock（单独入口，依赖 AWS SDK）', 'Amazon Bedrock (separate entry, AWS SDK)'),
 './bun-oauth': ('Bun 运行时的 OAuth 辅助', 'OAuth helpers for Bun'),
}
def api_section_ai(i, p):
    idx = read('packages/ai/src/index.ts')
    n_lines = len([l for l in idx.splitlines() if l.startswith('export')])
    key = ['createModels', 'createProvider', 'calculateCost', 'Type', 'validateToolArguments', 'isContextOverflow', 'AssistantMessageEventStream', 'createAssistantMessageEventStream', 'normalizeContext', 'getSupportedThinkingLevels', 'clampThinkingLevel']
    present = [k for k in key if re.search(rf'\b{k}\b', idx)]
    return sec_open(i, 'api', 'ai', ('公共 API', 'Public API')) + f'''
<p class="takeaway"><span class="tl">{T(("一句话结论", "Takeaway"))}</span>{T((f"9 个导出路径。根入口 `src/index.ts` 有 {n_lines} 条 export 语句；其中最常用的是 " + "、".join(f"`{k}`" for k in present[:8]) + "。", f"Nine export paths. The root entry `src/index.ts` has {n_lines} export statements; the most used are " + ", ".join(f"`{k}`" for k in present[:8]) + "."))}</p>
{exports_paths_table(p, AI_EXPORT_NOTES)}
</section>'''

def index_exports_table(index_path, base):
    """Group the named re-exports in an index.ts by source module (value vs type)."""
    src = read(index_path)
    mods = {}
    for m in re.finditer(r'export\s+(type\s+)?\{([^}]*)\}\s*from\s*"([^"]+)"', src):
        alltype, names, mod = m.group(1), m.group(2), m.group(3)
        d = mods.setdefault(mod, ([], []))
        for n in names.split(','):
            n = n.strip()
            if not n or n.startswith('//'): continue
            n = re.sub(r'\s*//.*', '', n)
            is_t = bool(alltype) or n.startswith('type ')
            n = n.replace('type ', '').split(' as ')[-1].strip()
            (d[1] if is_t else d[0]).append(n)
    for m in re.finditer(r'export \* from "([^"]+)"', src):
        mods.setdefault(m.group(1), (['*'], []))
    rows = []
    def cell(xs, cap=14):
        if not xs: return '—'
        show = ' '.join(f'<code>{esc(x)}</code>' for x in xs[:cap])
        return show + (f' <span class="note">+{len(xs) - cap}</span>' if len(xs) > cap else '')
    for mod, (v, t) in mods.items():
        if mod.startswith('.'):
            path = base + mod[2:]
            first = f'{flink(path)}'
        else:
            first = f'<code>{esc(mod)}</code>'
        rows.append(f'<tr><td>{first}</td><td>{cell(v)}</td><td class="col-role">{cell(t, 10)}</td></tr>')
    nv = sum(len(v) for v, _ in mods.values()); nt = sum(len(t) for _, t in mods.values())
    tbl = (f'<details class="cl-pkg"><summary><b>{T((f"展开全部 {len(mods)} 个来源模块", f"Show all {len(mods)} source modules"))}</b><span class="cnt"><span>{nv} values</span><span>{nt} types</span></span></summary><div class="body"><div class="tbl"><table><thead><tr><th>{T(("来源模块", "Source module"))}</th><th>{T(("值导出", "Value exports"))}</th><th class="col-role">{T(("类型导出", "Type exports"))}</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div></div></details>')
    return tbl, len(mods), nv, nt

def key_exports_table(index_path, base, picks):
    """picks: [(module, [names], (zh, en))] — verified against the index.ts re-exports."""
    src = read(index_path); rows = []
    for mod, names, note in picks:
        for n in names: assert re.search(r'\b' + re.escape(n) + r'\b', src), (index_path, n)
        path = base + mod
        links = ' '.join(f'<a href="{gh(path, line_of(path, rf"^export (?:declare )?(?:abstract )?(?:async )?(?:function|class|const|interface|type) {n}\b"))}" target="_blank" rel="noopener"><code>{esc(n)}</code></a>' for n in names)
        rows.append(f'<tr><td>{flink(path)}</td><td>{links}</td><td class="col-role">{T(note)}</td></tr>')
    return f'<div class="tbl"><table><thead><tr><th>{T(("模块", "Module"))}</th><th>{T(("常用导出", "Key exports"))}</th><th class="col-role">{T(("用途", "Use"))}</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'

CA_KEY = [('core/sdk.ts', ['createAgentSession'], ('一次性建好会话', 'build a session in one call')),
          ('core/agent-session-runtime.ts', ['AgentSessionRuntime', 'createAgentSessionRuntime'], ('可替换会话的宿主', 'the host that swaps sessions')),
          ('core/agent-session.ts', ['AgentSession'], ('一次会话', 'one session')),
          ('core/session-manager.ts', ['SessionManager'], ('JSONL 会话树', 'the JSONL session tree')),
          ('core/settings-manager.ts', ['SettingsManager'], ('两层设置', 'two-layer settings')),
          ('core/resource-loader.ts', ['DefaultResourceLoader'], ('扩展 · 技能 · 提示 · 主题', 'extensions · skills · prompts · themes')),
          ('core/tools/index.ts', ['createCodingTools', 'createReadOnlyTools'], ('内置工具', 'built-in tools')),
          ('modes/interactive/interactive-mode.ts', ['InteractiveMode'], ('交互界面', 'the interactive UI')),
          ('modes/rpc/rpc-client.ts', ['RpcClient'], ('RPC 客户端', 'RPC client'))]
TUI_KEY = [('tui.ts', ['Container', 'CURSOR_MARKER'], ('组件模型', 'component model')),
           ('tui-main-screen.ts', ['TuiMainScreen'], ('regular 屏幕', 'regular screen')),
           ('tui-alt-screen.ts', ['TuiAltScreen'], ('fullscreen 屏幕', 'fullscreen screen')),
           ('terminal.ts', ['ProcessTerminal'], ('真实终端', 'the real terminal')),
           ('components/editor.ts', ['Editor'], ('多行编辑器', 'multi-line editor')),
           ('autocomplete.ts', ['CombinedAutocompleteProvider'], ('/ · @ · 路径补全', '/ · @ · path completion')),
           ('keys.ts', ['matchesKey', 'parseKey'], ('按键识别', 'key recognition')),
           ('keybindings.ts', ['KeybindingsManager', 'getKeybindings'], ('键位', 'bindings')),
           ('utils.ts', ['visibleWidth', 'truncateToWidth'], ('宽度工具', 'width helpers'))]

CA_EXPORT_NOTES = {
 '.': ('SDK：createAgentSession、AgentSessionRuntime、SessionManager、工具、扩展类型、主题与组件', 'SDK: createAgentSession, AgentSessionRuntime, SessionManager, tools, extension types, theme and components'),
 './rpc-entry': ('以 RPC 模式启动（等同 pi --mode rpc）', 'start in RPC mode (same as pi --mode rpc)'),
 './client': ('源码入口：客户端（仓库内使用）', 'source entry: client (used inside the repo)'),
 './experimental/plugin': ('源码入口：实验性插件 API', 'source entry: experimental plugin API'),
}
def api_section_ca(i, p):
    j = json.loads(read('packages/coding-agent/package.json'))
    ln = line_of('packages/coding-agent/package.json', r'"exports"')
    rows = []
    for k, v in j['exports'].items():
        if k == './package.json': continue
        tgt = v.get('import') or v.get('source') if isinstance(v, dict) else v
        rows.append(f'<tr><td><code>{esc(p["npm"] + k[1:])}</code></td><td class="sym"><code>{esc(str(tgt))}</code></td><td class="col-role">{T(CA_EXPORT_NOTES.get(k, ("", "")))}</td></tr>')
    bins = ' '.join(f'`{k}` → `{v}`' for k, v in j.get('bin', {}).items())
    tbl, nm, nv, nt = index_exports_table('packages/coding-agent/src/index.ts', 'packages/coding-agent/src/')
    return sec_open(i, 'api', 'coding', ('公共 API', 'Public API')) + f'''
<p class="takeaway"><span class="tl">{T(("一句话结论", "Takeaway"))}</span>{T((f"一个命令（{bins}）加 {len(rows)} 个导入路径。SDK 根入口从 {nm} 个模块重新导出 {nv} 个值和 {nt} 个类型；最常用的是 `createAgentSession`、`createAgentSessionRuntime`、`SessionManager`、`SettingsManager`、`createCodingTools` 和扩展类型。", f"One command ({bins}) plus {len(rows)} import paths. The SDK root re-exports {nv} values and {nt} types from {nm} modules; the most used are `createAgentSession`, `createAgentSessionRuntime`, `SessionManager`, `SettingsManager`, `createCodingTools` and the extension types."))}</p>
<div class="tbl"><table><thead><tr><th>{T(("导入路径", "Import path"))}</th><th>{T(("目标", "Target"))}</th><th class="col-role">{T(("说明", "Notes"))}</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<p class="note">{flink("packages/coding-agent/package.json", ln, "package.json · exports")}</p>
<h3 class="subh">{T(("常用导出", "Key exports"))}</h3>{key_exports_table("packages/coding-agent/src/index.ts", "packages/coding-agent/src/", CA_KEY)}
<h3 class="subh">{T(("根入口 index.ts 的全部导出（按来源模块）", "Every root index.ts export, by source module"))}</h3>{tbl}
<p class="note">{T(("由构建脚本解析 `export { … } from` 语句生成；每个模块最多列出 14 个值、10 个类型。", "Generated by parsing the `export { … } from` statements at build time; at most 14 values and 10 types are listed per module."))}</p>
</section>'''

def api_section_tui(i, p):
    tbl, nm, nv, nt = index_exports_table('packages/tui/src/index.ts', 'packages/tui/src/')
    return sec_open(i, 'api', 'tui', ('公共 API', 'Public API')) + f'''
<p class="takeaway"><span class="tl">{T(("一句话结论", "Takeaway"))}</span>{T((f"package.json 没有 exports 字段，只有一个入口 `dist/index.js`。`src/index.ts` 从 {nm} 个模块重新导出 {nv} 个值和 {nt} 个类型：组件、TUI 与两种屏幕、终端、按键与键位、编辑器接口、宽度工具和图片。", f"package.json has no exports map — one entry, `dist/index.js`. `src/index.ts` re-exports {nv} values and {nt} types from {nm} modules: components, the TUI and both screens, the terminal, keys and bindings, the editor interface, width helpers and images."))}</p>
<h3 class="subh">{T(("常用导出", "Key exports"))}</h3>{key_exports_table("packages/tui/src/index.ts", "packages/tui/src/", TUI_KEY)}
<h3 class="subh">{T(("index.ts 的全部导出（按来源模块）", "Every index.ts export, by source module"))}</h3>{tbl}
<p class="note">{T(("由构建脚本解析 `export { … } from` 语句生成。", "Generated by parsing the `export { … } from` statements at build time."))}</p>
</section>'''

MCP_KEY = [('client.ts', ['McpClient'], ('一个服务器连接：握手、请求、分页', 'one server connection: handshake, requests, paging')),
           ('transports/stdio.ts', ['StdioTransport'], ('本地子进程', 'a local child process')),
           ('transports/streamable-http.ts', ['StreamableHttpTransport', 'McpAuthRequiredError'], ('远程 HTTP + SSE', 'remote HTTP + SSE')),
           ('transports/transport.ts', ['McpTransport'], ('自定义传输', 'custom transports')),
           ('protocol/content.ts', ['toLlmContent'], ('结果 → 模型内容', 'results → model content')),
           ('protocol/types.ts', ['LATEST_PROTOCOL_VERSION', 'SUPPORTED_PROTOCOL_VERSIONS'], ('协议版本', 'protocol versions')),
           ('protocol/jsonrpc.ts', ['McpError'], ('JSON-RPC 错误', 'JSON-RPC errors'))]
MCP_OAUTH_KEY = [('flow.ts', ['authorizeMcp'], ('完整的授权流程', 'the full authorization flow')),
                 ('provider.ts', ['McpOAuthProvider'], ('凭据与状态', 'credentials and state')),
                 ('callback.ts', ['OAuthCallbackServer'], ('本地回调服务器', 'local callback server')),
                 ('discovery.ts', ['discoverOAuthServerInfo'], ('元数据发现', 'metadata discovery'))]
CM_KEY = [('runtime/host.ts', ['CodemodeSandbox'], ('沙箱：execute(code)', 'the sandbox: execute(code)')),
          ('types.ts', ['CodemodeTool', 'CodemodeResult'], ('工具与结果', 'tools and results')),
          ('declarations.ts', ['renderDeclarations', 'renderToolSignature', 'schemaToType'], ('给模型的 TypeScript', 'TypeScript for the model')),
          ('source.ts', ['parseCodemodeSource', 'CODEMODE_SOURCE_GRAMMAR'], ('@options 与 Lark 语法', '@options and the Lark grammar')),
          ('identifier.ts', ['toCodemodeIdentifier'], ('工具名 → 标识符', 'tool name → identifier')),
          ('runtime/prelude-source.ts', ['MAX_OUTPUT_CHARS', 'MAX_STORE_VALUE_CHARS'], ('脚本限额', 'script limits'))]
MCP_EXPORT_NOTES = {'.': ('客户端、传输、协议类型、内容转换与错误', 'client, transports, protocol types, content conversion and errors'),
                    './oauth': ('OAuth：发现、注册、授权流程、回调服务器与 provider', 'OAuth: discovery, registration, the flow, callback server and provider'),
                    './testing': ('测试用：内存传输对', 'for tests: an in-memory transport pair')}
CM_EXPORT_NOTES = {'.': ('沙箱、类型、声明渲染、源码解析与限额', 'the sandbox, types, declaration rendering, source parsing and limits'),
                   './declarations': ('只有声明渲染，不加载 wasm', 'declaration rendering only, no wasm'),
                   './source': ('只有源码解析与语法', 'source parsing and grammar only'),
                   './worker': ('worker 入口，供打包时单独引用', 'the worker entry, referenced separately when bundling')}
def _exports_rows(dir_, p, notes):
    j = json.loads(read(f'packages/{dir_}/package.json'))
    rows = []
    for k, v in j['exports'].items():
        tgt = (v.get('import') or v.get('source')) if isinstance(v, dict) else v
        rows.append(f'<tr><td><code>{esc(p["npm"] + k[1:])}</code></td><td class="sym"><code>{esc(str(tgt))}</code></td><td class="col-role">{T(notes.get(k, ("", "")))}</td></tr>')
    tbl = f'<div class="tbl"><table><thead><tr><th>{T(("导入路径", "Import path"))}</th><th>{T(("目标", "Target"))}</th><th class="col-role">{T(("说明", "Notes"))}</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
    return rows, tbl + f'<p class="note">{flink(f"packages/{dir_}/package.json", line_of(f"packages/{dir_}/package.json", r"\"exports\""), "package.json · exports")}</p>'

def api_section_mcp(i, p):
    rows, etbl = _exports_rows('mcp', p, MCP_EXPORT_NOTES)
    tbl, nm, nv, nt = index_exports_table('packages/mcp/src/index.ts', 'packages/mcp/src/')
    return sec_open(i, 'api', p['layer'], ('公共 API', 'Public API')) + f'''
<p class="takeaway"><span class="tl">{T(("一句话结论", "Takeaway"))}</span>{T((f"{len(rows)} 个导入路径。根入口从 {nm} 个模块重新导出 {nv} 个值和 {nt} 个类型：`McpClient`、两种传输、协议类型、`toLlmContent` 与错误类；OAuth 在 `./oauth`，内存传输在 `./testing`。", f"{len(rows)} import paths. The root re-exports {nv} values and {nt} types from {nm} modules: `McpClient`, the two transports, protocol types, `toLlmContent` and the error classes; OAuth lives in `./oauth` and the in-memory transport in `./testing`."))}</p>
{etbl}
<h3 class="subh">{T(("常用导出", "Key exports"))}</h3>{key_exports_table("packages/mcp/src/index.ts", "packages/mcp/src/", MCP_KEY)}
<h3 class="subh">{T(("./oauth 的常用导出", "Key ./oauth exports"))}</h3>{key_exports_table("packages/mcp/src/oauth/index.ts", "packages/mcp/src/oauth/", MCP_OAUTH_KEY)}
<h3 class="subh">{T(("根入口 index.ts 的全部导出（按来源模块）", "Every root index.ts export, by source module"))}</h3>{tbl}
<p class="note">{T(("由构建脚本解析 `export { … } from` 语句生成。", "Generated by parsing the `export { … } from` statements at build time."))}</p>
</section>'''

def api_section_cm(i, p):
    rows, etbl = _exports_rows('codemode', p, CM_EXPORT_NOTES)
    tbl, nm, nv, nt = index_exports_table('packages/codemode/src/index.ts', 'packages/codemode/src/')
    return sec_open(i, 'api', p['layer'], ('公共 API', 'Public API')) + f'''
<p class="takeaway"><span class="tl">{T(("一句话结论", "Takeaway"))}</span>{T((f"{len(rows)} 个导入路径。根入口从 {nm} 个模块重新导出 {nv} 个值和 {nt} 个类型；核心只有一个类 `CodemodeSandbox`，其余是声明渲染、源码解析、限额常量和类型。", f"{len(rows)} import paths. The root re-exports {nv} values and {nt} types from {nm} modules; the core is a single class, `CodemodeSandbox`, and the rest is declaration rendering, source parsing, limit constants and types."))}</p>
{etbl}
<h3 class="subh">{T(("常用导出", "Key exports"))}</h3>{key_exports_table("packages/codemode/src/index.ts", "packages/codemode/src/", CM_KEY)}
<h3 class="subh">{T(("index.ts 的全部导出（按来源模块）", "Every index.ts export, by source module"))}</h3>{tbl}
<p class="note">{T(("由构建脚本解析 `export { … } from` 语句生成。", "Generated by parsing the `export { … } from` statements at build time."))}</p>
</section>'''

CHORD_KEY = [('api.ts', ['createFacetHost'], ('启动宿主：加载 facet、激活、提供服务', 'start a host: load facets, activate, provide services')),
             ('api.ts', ['defineFacet', 'defineService'], ('声明插件与服务令牌', 'declare plugins and service tokens')),
             ('api.ts', ['replicatedState'], ('跨边界复制的状态', 'state replicated across the boundary')),
             ('api.ts', ['createStaticFacetLoader', 'combineFacetLoaders'], ('组合 facet 来源', 'compose facet sources')),
             ('api.ts', ['createRemoteServiceBinding'], ('把远端服务接进宿主', 'bind a remote service into a host')),
             ('services/provider.ts', ['RemoteServiceProvider', 'createRemoteServiceEndpoint'], ('把本地服务暴露给远端', 'expose local services to a remote side'))]
DUR_KEY = [('session/session.ts', ['createSession'], ('在 Storage 之上打开会话', 'open a session over a Storage')),
           ('harness/harness.ts', ['Harness'], ('带模型、工具与扩展的会话', 'a session with model, tools and extensions')),
           ('tasks.ts', ['defineTask'], ('可恢复的分阶段任务', 'resumable, phased tasks')),
           ('documents.ts', ['defineDoc', 'defineDocFamily'], ('持久化文档', 'durable documents')),
           ('harness/define.ts', ['defineTool', 'defineExtension'], ('工具与扩展', 'tools and extensions')),
           ('harness/inbox.ts', ['InboxDoc'], ('收件箱文档', 'the inbox document')),
           ('storage/memory.ts', ['MemoryStorage'], ('内存存储', 'in-memory storage'))]
ENV_KEY = [('ssh.ts', ['connectSsh'], ('探测、部署并连接', 'detect, deploy and connect')),
           ('ssh.ts', ['scanHostKey', 'acceptHostKey'], ('主机密钥信任', 'host-key trust')),
           ('ssh.ts', ['detectPlatform', 'deployDaemon', 'packagedDaemon'], ('平台探测与守护进程部署', 'platform detection and daemon deployment')),
           ('connection.ts', ['Connection'], ('分帧请求 / 回复连接', 'the framed request / reply connection')),
           ('remote-env.ts', ['RemoteExecutionEnv'], ('远端的 ExecutionEnv', 'an ExecutionEnv on the remote host')),
           ('watch.ts', ['RemoteWatcher'], ('远端文件监视', 'remote file watching'))]
CHORD_EXPORT_NOTES = {'.': ('facet 宿主、服务、复制状态、RPC 线格式与类型', 'the facet host, services, replicated state, the RPC wire format and types'),
                      './context': ('上下文与取消', 'context and cancellation'),
                      './delta': ('JSON 草稿与增量', 'JSON drafts and deltas'),
                      './bundler': ('把 facet 包打成可校验的 bundle', 'bundle a facet package with integrity data'),
                      './node': ('Node 专用：从磁盘加载 bundle', 'Node only: load bundles from disk'),
                      './package.json': ('包元数据', 'package metadata')}
DUR_EXPORT_NOTES = {'.': ('会话、Harness、任务、文档、扩展与类型', 'sessions, the Harness, tasks, documents, extensions and types'),
                    './env': ('ExecutionEnv 接口（env 包实现它）', 'the ExecutionEnv interface (implemented by env)'),
                    './env/node': ('本机 Node 实现', 'the local Node implementation'),
                    './tools': ('内置工具', 'built-in tools'),
                    './storage/memory': ('内存存储', 'in-memory storage'),
                    './storage/jsonl': ('JSONL 存储', 'JSONL storage'),
                    './storage/jsonl/node': ('JSONL 的 Node 文件后端', 'the Node file backend for JSONL'),
                    './storage/sqlite': ('SQLite 存储', 'SQLite storage'),
                    './storage/sqlite/cloudflare': ('Cloudflare Durable Object SQLite 后端', 'the Cloudflare Durable Object SQLite backend'),
                    './storage/sqlite/node': ('Node SQLite 后端', 'the Node SQLite backend'),
                    './testing': ('测试运行器与一致性套件', 'the test runner and conformance suites'),
                    './package.json': ('包元数据', 'package metadata')}
ENV_EXPORT_NOTES = {'.': ('SSH 部署、连接、远程 ExecutionEnv 与监视', 'SSH deployment, the connection, the remote ExecutionEnv and watching')}

def _api_generic(i, p, dir_, notes, keys, take):
    rows, etbl = _exports_rows(dir_, p, notes)
    tbl, nm, nv, nt = index_exports_table(f'packages/{dir_}/src/index.ts', f'packages/{dir_}/src/')
    return sec_open(i, 'api', p['layer'], ('公共 API', 'Public API')) + f'''
<p class="takeaway"><span class="tl">{T(("一句话结论", "Takeaway"))}</span>{T(take(len([k for k in json.loads(read(f'packages/{dir_}/package.json'))['exports'] if k != './package.json']), nm, nv, nt))}</p>
{etbl}
<h3 class="subh">{T(("常用导出", "Key exports"))}</h3>{key_exports_table(f"packages/{dir_}/src/index.ts", f"packages/{dir_}/src/", keys)}
<h3 class="subh">{T(("根入口 index.ts 的全部导出（按来源模块）", "Every root index.ts export, by source module"))}</h3>{tbl}
<p class="note">{T(("由构建脚本解析 `export { … } from` 语句生成。", "Generated by parsing the `export { … } from` statements at build time."))}</p>
</section>'''

def api_section_chord(i, p):
    return _api_generic(i, p, 'chord', CHORD_EXPORT_NOTES, CHORD_KEY, lambda r, nm, nv, nt: (
        f"{r} 个导入路径（另有 `./package.json`）。根入口从 {nm} 个模块重新导出 {nv} 个值和 {nt} 个类型：`createFacetHost`、`defineFacet` / `defineService`、`replicatedState` 与远程服务的线格式；打包与磁盘加载分别在 `./bundler` 与 `./node`。",
        f"{r} import paths (plus `./package.json`). The root re-exports {nv} values and {nt} types from {nm} modules: `createFacetHost`, `defineFacet` / `defineService`, `replicatedState` and the remote-service wire format; bundling and loading from disk live in `./bundler` and `./node`."))

def api_section_durable(i, p):
    return _api_generic(i, p, 'durable', DUR_EXPORT_NOTES, DUR_KEY, lambda r, nm, nv, nt: (
        f"{r} 个导入路径（另有 `./package.json`）。根入口从 {nm} 个模块重新导出 {nv} 个值和 {nt} 个类型：`createSession`、`Harness`、`defineTask`、`defineDoc` 与扩展 API；执行环境、工具与各存储后端各有自己的子路径。",
        f"{r} import paths (plus `./package.json`). The root re-exports {nv} values and {nt} types from {nm} modules: `createSession`, `Harness`, `defineTask`, `defineDoc` and the extension API; the execution environment, tools and each storage backend have their own subpaths."))

def api_section_env(i, p):
    return _api_generic(i, p, 'env', ENV_EXPORT_NOTES, ENV_KEY, lambda r, nm, nv, nt: (
        f"只有 {r} 个导入路径。index.ts 从 {nm} 个模块导出 {nv} 个值和 {nt} 个类型：SSH 部署与主机密钥、`Connection`、`RemoteExecutionEnv` 与 `RemoteWatcher`。",
        f"Just {r} import path. index.ts exports {nv} values and {nt} types from {nm} modules: SSH deployment and host keys, `Connection`, `RemoteExecutionEnv` and `RemoteWatcher`."))

def ext_section(i, layer, items):
    cards = ''.join(f'<div><b><code>{esc(k)}</code></b>{T(d)}</div>' for k, d in items)
    return sec_open(i, 'ext', layer, ('扩展点', 'Extension points')) + f'<div class="ext-list">{cards}</div></section>'

def tests_section(i, p, n=None, lead=None):
    t = tests_of(p['dir'])
    return sec_open(i, 'tests', p['layer'], ('测试', 'Tests')) + (f'<p class="takeaway"><span class="tl">{T(("一句话结论", "Takeaway"))}</span>{T(lead)}</p>' if lead else '') + tests_table(p, n) + '</section>'

def xref_section(i, p, items, extra=''):
    cards = ''.join(f'<a class="pkgcard L-{PBY[s]["layer"]}" href="{pkg_href("{P}", s)}"><span class="h"><b>{s}</b>{status_dot(PBY[s]["status"])}</span><p>{T(d)}</p></a>' for s, d in items)
    return sec_open(i, 'xref', p['layer'], ('交叉链接', 'Cross-links')) + f'<div class="pkgcards">{cards}</div>{extra}</section>'

def deck_link(slug, n):
    return f'<a href="{{P}}packages/{slug}/slides.html">▶ {T((f"本包演示（{n} 页）", f"Package slides ({n})"))}</a>'

def build_deep(slug, mod, order, api_fn, test_lead, slides_n):
    p = PBY[slug]
    secs = {s['id']: s for s in mod.SECTIONS}
    body, toc_groups, i = [], {}, 0
    for kind, sid in order:
        i += 1
        if kind == 'sec':
            s = secs[sid]; body.append(section(i, s)); g = s['group']; title, layer = s['title'], s['layer']
        elif kind == 'v1':
            s = V1[sid]; body.append(section(i, s, moved_from='index')); g = 'flows'; title, layer = s['title'], s['layer']
        elif kind == 'api':
            body.append(api_fn(i, p)); g = 'ref'; title, layer = ('公共 API', 'Public API'), p['layer']
        elif kind == 'ext':
            body.append(ext_section(i, p['layer'], mod.EXT_POINTS)); g = 'ref'; title, layer = ('扩展点', 'Extension points'), p['layer']
        elif kind == 'tests':
            body.append(tests_section(i, p, 20, test_lead)); g = 'ref'; title, layer = ('测试', 'Tests'), p['layer']
        elif kind == 'xref':
            body.append(xref_section(i, p, mod.XREF)); g = 'ref'; title, layer = ('交叉链接', 'Cross-links'), p['layer']
        toc_groups.setdefault(g, []).append((i, sid if kind in ('sec', 'v1') else kind, title, layer))
    toc = toc_build([(GROUP_TOC[g], toc_groups[g]) for g in ('arch', 'flows', 'types', 'ref') if g in toc_groups],
                    [deck_link(slug, slides_n), f'<a href="{gh("packages/" + p["dir"])}" target="_blank" rel="noopener">GitHub · packages/{p["dir"]} · {REF}</a>'])
    intro = f'<p class="takeaway L-{p["layer"]}" style="--l:var(--{p["layer"]})"><span class="tl">{T(("这个包是什么", "What this package is"))}</span>{T(mod.INTRO["takeaway"])}</p><p class="note">{T(mod.INTRO["role"])}</p>'
    page(f'packages/{slug}/index.html', (f'{slug} · {SITE[0]}', f'{slug} · {SITE[1]}'), intro + ''.join(body), 'pkg', toc, slug, hero=pkg_hero(p))
    return [s for k, s in order if k == 'sec']

PARTIAL = {
 'coding-agent': dict(v1=['session', 'compaction', 'extensions', 'modes'], hub=['sequence', 'classes'], done={'files', 'tests', 'xref'}, half={'overview', 'arch', 'flows', 'types', 'ext'},
                      lead=('`pi-coding-agent` 是产品本身：`AgentSession` 把 `Agent`、会话树、工具、扩展与模型运行时组装在一起。第一版的 4 个相关章节已迁移到这里；完整的包级深挖（API、设置、工具实现、RPC）在路线图中。', 'The product itself: `AgentSession` assembles `Agent`, the session tree, tools, extensions and the model runtime. The four related first-edition sections now live here; the full package deep dive (API, settings, tool implementations, RPC) is on the roadmap.')),
 'tui': dict(v1=['tui'], hub=[], done={'files', 'tests', 'xref'}, half={'overview', 'flows'},
             lead=('`pi-tui` 是独立的终端 UI 库：组件树渲染成行，差分写入终端。第一版的 TUI 章节已迁移到这里；组件、按键与输入处理的深挖在路线图中。', 'A standalone terminal UI library: the component tree renders to lines and only the diff is written to the terminal. The first-edition TUI section now lives here; components, keys and input handling are on the roadmap.')),
}

def build_partial(slug):
    p = PBY[slug]; cfg = PARTIAL[slug]
    body, items, i = [], [], 0
    for sid in cfg['v1']:
        i += 1; s = V1[sid]; body.append(section(i, s, moved_from='index')); items.append((i, sid, s['title'], s['layer']))
    i += 1; body.append(sec_open(i, 'files-top', p['layer'], ('最大的源文件', 'Largest source files')) + largest_table(p) + '</section>'); items.append((i, 'files-top', ('最大的源文件', 'Largest source files'), p['layer']))
    i += 1; body.append(sec_open(i, 'api', p['layer'], ('导出路径', 'Export paths')) + exports_paths_table(p) + '</section>'); items.append((i, 'api', ('导出路径', 'Export paths'), p['layer']))
    i += 1; body.append(tests_section(i, p, 15)); items.append((i, 'tests', ('测试', 'Tests'), p['layer']))
    i += 1
    xr = [(s, PBY[s]['desc']) for s in (p['dep_slugs'] + p['dependents'])[:6]]
    hub_links = ''.join(f'<li><a href="{{P}}index.html#{h}">{T(V1[h]["title"])}</a></li>' for h in cfg['hub'])
    extra = f'<div class="moved">{T(("总览页上与本包相关的第一版章节：", "First-edition sections about this package that stay on the overview:"))}<ul>{hub_links}</ul></div>' if hub_links else ''
    body.append(xref_section(i, p, xr, extra)); items.append((i, 'xref', ('交叉链接', 'Cross-links'), p['layer']))
    i += 1; body.append(sec_open(i, 'plan', 'infra', ('深挖计划', 'Deep-dive plan'), 'Roadmap') + f'<p class="note">{T(("按包模板的进度（绿 = 完成，半 = 已有第一版内容）：", "Progress against the package template (green = done, half = first-edition content exists):"))}</p>' + checklist(cfg['done'], cfg['half']) + f'<p class="note"><a href="{{P}}roadmap/index.html">{T(("查看完整路线图 →", "See the full roadmap →"))}</a></p></section>')
    items.append((i, 'plan', ('深挖计划', 'Deep-dive plan'), 'infra'))
    toc = toc_build([(GROUP_TOC['v1'], items[:len(cfg['v1'])]), (GROUP_TOC['ref'], items[len(cfg['v1']):])],
                    [f'<a href="{gh("packages/" + p["dir"])}" target="_blank" rel="noopener">GitHub · packages/{p["dir"]} · {REF}</a>'])
    intro = f'<p class="takeaway" style="--l:var(--{p["layer"]})"><span class="tl">{T(("状态：部分完成", "Status: partial"))}</span>{T(cfg["lead"])}</p>'
    page(f'packages/{slug}/index.html', (f'{slug} · {SITE[0]}', f'{slug} · {SITE[1]}'), intro + ''.join(body), 'pkg', toc, slug, hero=pkg_hero(p))

def build_stub(slug):
    p = PBY[slug]
    cl = changelog(p['dir'])
    body, items, i = [], [], 0
    def add(sid, title, html_, layer=None):
        nonlocal i; i += 1; layer = layer or p['layer']
        body.append(sec_open(i, sid, layer, title) + html_ + '</section>'); items.append((i, sid, title, layer))
    lead = (f'本页是自动生成的占位页：以下事实全部来自 v1.1.0 的 package.json 与源码扫描；人工撰写的架构图与流程分析尚未开始（见下方模板清单）。',
            'This is a generated placeholder: every fact below comes from package.json and a source scan at v1.1.0; the hand-written diagrams and flow analysis have not started yet (see the template checklist below).')
    body.append(f'<p class="takeaway" style="--l:var(--infra)"><span class="tl">{T(("状态：计划中", "Status: planned"))}</span>{T(lead)}</p>')
    add('api', ('导出路径', 'Export paths'), exports_paths_table(p))
    ext = ''.join(f'<code>{esc(d)}</code> ' for d in p['ext_deps']) or '—'
    add('deps', ('依赖', 'Dependencies'), f'<div class="prose"><p>{T(("外部运行时依赖：", "External runtime dependencies: "))}{ext}</p></div>')
    add('files-top', ('最大的源文件', 'Largest source files'), largest_table(p, 8))
    t = tests_of(p['dir'])
    add('tests', ('测试', 'Tests'), tests_table(p, 10) if t else f'<p class="note">{T(("没有找到 *.test.* 文件。", "No *.test.* files found."))}</p>')
    if cl:
        n = {k: len(v) for k, v in cl['secs'].items()}
        cnt = ' · '.join(f'{k} {v}' for k, v in n.items())
        add('changes', (f'{VERSION} 变更', f'Changes in {VERSION}'), f'<p class="note">{flink(cl["path"], cl["line"], f"CHANGELOG.md · [{VERSION}] · {cl["date"]}")} · {esc(cnt) or "—"}</p>')
    add('plan', ('模板清单', 'Template checklist'), checklist(set()) + f'<p class="note"><a href="{{P}}roadmap/index.html">{T(("查看完整路线图 →", "See the full roadmap →"))}</a></p>', 'infra')
    toc = toc_build([(('占位页', 'Placeholder'), items)], [f'<a href="{gh("packages/" + p["dir"])}" target="_blank" rel="noopener">GitHub · packages/{p["dir"]} · {REF}</a>'])
    page(f'packages/{slug}/index.html', (f'{slug} · {SITE[0]}', f'{slug} · {SITE[1]}'), ''.join(body), 'pkg', toc, slug, hero=pkg_hero(p))

# ---------------------------------------------------------------- hub
MOVED = {'loop': 'agent-core', 'toolexec': 'agent-core', 'providers': 'pi-ai', 'session': 'coding-agent', 'compaction': 'coding-agent',
         'extensions': 'coding-agent', 'modes': 'coding-agent', 'tui': 'tui'}
HUB_SECS = ['packages', 'layers', 'sequence', 'classes']
assert set(MOVED) | set(HUB_SECS) == set(V1), 'every first-edition section must have a home'

def pkg_cards(prefix):
    out = []
    for gid, gname in pkgmeta.GROUP_NAME.items():
        items = [p for p in PK if p['group'] == gid]
        out.append(f'<div class="grp-h">{T(gname)}</div><div class="pkgcards">')
        for p in items:
            st = STATS_BY.get(p['dir'], {})
            out.append(f'<a class="pkgcard L-{p["layer"]} {p["status"]}" href="{pkg_href(prefix, p["slug"])}"><span class="h"><span class="dotL"></span><b>{p["slug"]}</b>{status_dot(p["status"])}</span>'
                       f'<p>{T((p["desc"][0], p["desc"][1]))}</p><span class="m"><span>{fmt(st.get("src_loc", 0))} LOC</span><span>{len(tests_of(p["dir"]))} tests</span><span>{len(p["dep_slugs"])} deps</span></span></a>')
        out.append('</div>')
    return ''.join(out)

def stats_section(i):
    rows = sorted(STATS, key=lambda x: -x['src_loc'])
    mx = max(s['src_loc'] + s['test_loc'] for s in rows)
    href = {p['dir']: p['slug'] for p in PK}
    bars = ''.join(
        f'<div class="bar L-{PKG_LAYER.get(s["pkg"], "infra")}"><span class="nm">{s["pkg"]}</span><span class="tr">'
        f'<span class="s" style="width:{s["src_loc"] / mx * 100:.2f}%"></span><span class="t" style="width:{s["test_loc"] / mx * 100:.2f}%"></span></span>'
        f'<span class="v">{fmt(s["src_loc"])}</span></div>' for s in rows)
    trs = ''.join(f'<tr><td><a class="chip L-{PKG_LAYER.get(s["pkg"], "infra")}" href="{pkg_href("{P}", href[s["pkg"]])}">{s["pkg"]}</a></td><td class="num">{s["src_files"]}</td><td class="num">{fmt(s["src_loc"])}</td>'
                  f'<td class="num">{s["test_files"]}</td><td class="num">{fmt(s["test_loc"])}</td><td class="num col-role">{s["all_ts_files"]}</td></tr>' for s in rows)
    tot = lambda k: fmt(sum(s[k] for s in STATS))
    trs += f'<tr class="tot"><td>{T(("合计", "Total"))}</td><td class="num">{tot("src_files")}</td><td class="num">{tot("src_loc")}</td><td class="num">{tot("test_files")}</td><td class="num">{tot("test_loc")}</td><td class="num col-role">{tot("all_ts_files")}</td></tr>'
    ca = STATS_BY['coding-agent']
    return sec_open(i, 'stats', 'infra', ('仓库统计', 'Repository stats'), 'Repository') + f'''
<p class="takeaway L-coding"><span class="tl">{T(("一句话结论", "Takeaway"))}</span>{T((f"约 {SRC_LOC/1000:.0f}k 行源码、{TEST_LOC/1000:.0f}k 行测试；`coding-agent` 一个包就占了 {ca['src_loc']/SRC_LOC*100:.0f}% 的源码，测试代码量与源码相当。", f"About {SRC_LOC/1000:.0f}k lines of source and {TEST_LOC/1000:.0f}k of tests; `coding-agent` alone is {ca['src_loc']/SRC_LOC*100:.0f}% of the source, and test code roughly matches source code."))}</p>
<p class="note">{T((f"统计自标签 `{REF}`（`{SHORT}`）：只计 `.ts`（不含 `.d.ts`），排除 node_modules 与 dist；src = `src/` 下，test = `test*/` 下或 `*.test.*`。", f"Counted at tag `{REF}` (`{SHORT}`): `.ts` only (no `.d.ts`), node_modules and dist excluded; src = under `src/`, test = under `test*/` or `*.test.*`."))}</p>
<div class="bars-key"><span><i></i>{T(("源码行数", "src LOC"))}</span><span><i class="t"></i>{T(("测试行数", "test LOC"))}</span></div>
<div class="bars" role="img" aria-label="Lines of code by package">{bars}</div>
<div class="tbl"><table><thead><tr><th>{T(("包", "Package"))}</th><th class="num">{T(("源文件", "src files"))}</th><th class="num">{T(("源码行", "src LOC"))}</th><th class="num">{T(("测试文件", "test files"))}</th><th class="num">{T(("测试行", "test LOC"))}</th><th class="num col-role">{T(("全部 .ts", "all .ts"))}</th></tr></thead><tbody>{trs}</tbody></table></div>
</section>'''

def build_hub(n_slides):
    P = '{P}'
    i = 1
    body = [sec_open(i, 'pkgs', 'coding', ('14 个包', 'The 14 packages'), 'Packages') + f'''
<p class="takeaway"><span class="tl">{T(("一句话结论", "Takeaway"))}</span>{T(("从这里进入每个包的子页面。核心栈是 `coding-agent → agent-core → pi-ai`，外加 `tui`；其余包提供 MCP、代码沙箱、遥测、持久化运行时与远程会话。", "Enter each package's page from here. The core stack is `coding-agent → agent-core → pi-ai`, plus `tui`; the rest provide MCP, the code sandbox, telemetry, the durable runtime and remote sessions."))}</p>
{pkg_cards(P)}
<div class="moved">{T(("第一版中按包划分的章节已迁移到对应子页面（旧链接 `index.html#loop` 等会自动跳转）：", "First-edition sections that belong to one package now live on that package's page (old links such as `index.html#loop` redirect automatically):"))}<ul>
{"".join(f'<li><a href="{pkg_href(P, s)}#{k}">{T(V1[k]["title"])}</a> → <code>{s}</code></li>' for k, s in MOVED.items())}</ul></div></section>''']
    toc_items = [(1, 'pkgs', ('14 个包', 'The 14 packages'), 'coding')]
    legend = f'''<div class="legend" id="legend"><h2>{T(("如何阅读这些图", "How to read the diagrams"))}</h2>
<div class="chips">{''.join(f'<span class="chip L-{k}">{v}</span>' for k, v in LAYER_NAME.items())}</div>
<ul><li>{T(("颜色 = 代码所在的层 / 包，所有页面、图、表与幻灯片一致。", "Colour = the layer / package the code lives in, identical across every page, diagram, table and slide."))}</li>
<li>{T(("圆角容器 = 包或层；卡片 = 类、函数或组件；深色胶囊 = 起止点；红色 = 错误路径。", "Rounded containers = packages or layers; cards = classes, functions or components; dark pill = start / end; red = error path."))}</li>
<li>{T(("实线箭头 = 调用 / 依赖；虚线 = 事件、异步返回或 devDependency；流动的虚线标出主路径；圆形数字 = 执行顺序。", "Solid arrow = call / dependency; dashed = event, async return or devDependency; animated dashes mark the main path; numbered circles = execution order."))}</li>
<li>{T(("每张图都带图例。鼠标悬停某个组件会高亮它的连线；点击图可放大、滚轮缩放、拖动平移。", "Every diagram carries its own legend. Hover a component to highlight its connections; click to enlarge, wheel to zoom, drag to pan."))}</li></ul></div>'''
    for sid in HUB_SECS:
        i += 1; s = V1[sid]; body.append(section(i, s)); toc_items.append((i, sid, s['title'], s['layer']))
    i += 1; body.append(stats_section(i)); toc_items.append((i, 'stats', ('仓库统计', 'Repository stats'), 'infra'))
    toc = toc_build([(('总览', 'Overview'), toc_items[:1]), (('全局', 'Big picture'), toc_items[1:-1]), (('数据', 'Data'), toc_items[-1:])],
                    [f'<a href="{P}roadmap/index.html">{T(("路线图与变更日志", "Roadmap & changelog"))}</a>',
                     f'<a href="{P}slides.html">▶ {T((f"演示模式（{n_slides} 页）", f"Presentation ({n_slides} slides)"))}</a>',
                     f'<a href="{GH}/tree/{REF}" target="_blank" rel="noopener">GitHub · {REF}</a>'])
    stat_cards = [(fmt(FACTS['packages']), ('个 workspace 包', 'workspace packages')), (f'{SRC_LOC/1000:.0f}k', ('行 TypeScript 源码', 'lines of TS source')),
                  (f'{TEST_LOC/1000:.0f}k', ('行测试代码', 'lines of tests')), (str(FACTS['providers']), ('个内置 LLM provider', 'built-in LLM providers')),
                  (str(FACTS['tools']), ('个内置工具', 'built-in tools')), (str(FACTS['ext_events']), ('种扩展事件', 'extension events')),
                  (str(FACTS['rpc']), ('种 RPC 命令', 'RPC command types')), (str(len(FIGS)), ('张手绘架构图', 'hand-laid diagrams'))]
    stats = ''.join(f'<div class="stat"><div class="n">{n}</div><div class="k">{T(k)}</div></div>' for n, k in stat_cards)
    stack = f'''<div class="stack" aria-label="layer stack">
<div class="stack-h"><span>{T(("运行时分层", "Runtime layers"))}</span><span>↓ {T(("一次请求", "one request"))}</span></div>
<a class="tier L-modes" href="{pkg_href(P, "coding-agent")}#modes"><b>Run modes</b><span>interactive · print · json · rpc</span></a>
<div class="tier-row"><a class="tier L-coding" href="{pkg_href(P, "coding-agent")}"><b>pi-coding-agent</b><span>AgentSession</span></a><a class="tier L-ext" href="{pkg_href(P, "coding-agent")}#extensions"><b>Extensions</b><span>{FACTS["ext_events"]} events</span></a></div>
<a class="tier L-agent" href="{pkg_href(P, "agent-core")}"><b>pi-agent-core</b><span>Agent · runLoop · tools</span></a>
<a class="tier L-ai" href="{pkg_href(P, "pi-ai")}"><b>pi-ai</b><span>{FACTS["providers"]} providers · {FACTS["ai_events"]} events</span></a>
<a class="tier L-tui" href="{pkg_href(P, "tui")}"><b>pi-tui</b><span>differential renderer</span></a>
</div>'''
    hero = f'''<section class="hero" id="top"><div class="wrap"><div>
<a class="eyebrow" href="{GH}/releases/tag/{REF}" target="_blank" rel="noopener"><b>{REF}</b>{T(SUBTITLE)} · {COMMIT_DATE[:10]}</a>
<h1>{T(("图解 <grad>Pi Agent</grad>", "<grad>Pi Agent</grad>,<br>Illustrated"), cls="h1")}</h1>
<p class="lead">{T((f"基于 Pi v{VERSION} 源码逐行核对的架构导读。总览页给出全局；每个包有自己的子页面——`coding-agent`、`agent-core`、`pi-ai`、`tui` 四个核心包以及 `mcp`、`codemode`、`chord`、`durable`、`env` 已完成深挖。共 {len(FIGS)} 张手绘架构图，每个结论都链接到 `{REF}` 标签中的具体代码行。", f"An architecture walkthrough checked line by line against the Pi v{VERSION} source. This overview gives the big picture; every package has its own page — the four core packages `coding-agent`, `agent-core`, `pi-ai` and `tui`, plus `mcp`, `codemode`, `chord`, `durable` and `env`, are fully covered. {len(FIGS)} hand-laid diagrams, and every claim links to the exact lines at tag `{REF}`."))}</p>
<div class="cta"><a class="btn primary" href="#pkgs">{T(("浏览 14 个包", "Browse the 14 packages"))} →</a><a class="btn" href="{P}slides.html">{ICON["play"].replace("<svg", "<svg width=15 height=15")}{T((f"演示模式 · {n_slides} 页", f"Presentation · {n_slides} slides"))}</a></div>
<div class="stats">{stats}</div></div>
{stack}
</div></section>'''
    moved_js = esc(json.dumps({k: f'packages/{s}/index.html#{k}' for k, s in MOVED.items()}))
    page('index.html', (f'{SITE[0]} · {SUBTITLE[0]}', f'{SITE[1]} · {SUBTITLE[1]}'), body[0] + legend + ''.join(body[1:]), 'hub', toc, hero=hero, body_attrs=f' data-moved="{moved_js}"')

# ---------------------------------------------------------------- roadmap + changelog
def build_roadmap():
    P = '{P}'
    rows = ''.join(f'<tr><td><a class="chip L-{p["layer"]}" href="{pkg_href(P, p["slug"])}">{p["slug"]}</a></td><td><code>{p["npm"]}</code></td><td>{status_dot(p["status"])}</td><td class="col-role">{T(p["desc"])}</td></tr>' for p in PK)
    cnt = {s: sum(1 for p in PK if p['status'] == s) for s in ('done', 'partial', 'planned')}
    plan = f'''<p class="takeaway"><span class="tl">{T(("一句话结论", "Takeaway"))}</span>{T((f"信息架构 = 一个总览页 + 每个包一个子页面，全部使用同一个包模板。当前 {cnt['done']} 个完成、{cnt['partial']} 个部分完成、{cnt['planned']} 个计划中（已有自动生成的占位页，链接全部有效）。", f"Information architecture = one overview page + one page per package, all following the same package template. Currently {cnt['done']} done, {cnt['partial']} partial and {cnt['planned']} planned (each already has a generated placeholder page, so every link works)."))}</p>
<div class="tbl"><table><thead><tr><th>{T(("包", "Package"))}</th><th>npm</th><th>{T(("状态", "Status"))}</th><th class="col-role">{T(("定位", "Role"))}</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    tmpl = f'<p class="note">{T(("每个包页面按以下 9 项组织；完成的包页面全部覆盖，占位页显示进度。", "Every package page is organised by these nine parts; finished pages cover all of them, placeholders show progress."))}</p>' + checklist({k for k, *_ in pkgmeta.TEMPLATE})
    nxt = [(('第 7 批（下一批）：protocol / client / server / telemetry / evals', 'Batch 7 (next): protocol, client, server, telemetry, evals'), ('CBOR 帧协议与远程会话；遥测契约；评测套件。', 'The CBOR framing protocol and remote sessions; telemetry contracts; evaluation suites.'))]
    nxt_html = '<ol class="prose">' + ''.join(f'<li><b>{T(a)}</b> — {T(b)}</li>' for a, b in nxt) + '</ol>'
    # site changelog
    site_cl = [
        (('本次更新：chord、durable 与 env 完成（第 6 批）', 'This update: chord, durable and env done (batch 6)'), [('chord 深挖：新增 8 张图（模块、facet 生命周期、热重载、服务、远程服务、复制状态、增量与草稿、打包与加载）。', 'chord deep dive: 8 new diagrams (modules, the facet lifecycle, hot reload, services, remote services, replicated state, deltas and drafts, bundling and loading).'),
                                     ('durable 深挖：新增 8 张图（模块、数据模型、一次运行、任务、收件箱、文档、存储、扩展）。', 'durable deep dive: 8 new diagrams (modules, the data model, one run, tasks, the inbox, documents, storage, extensions).'),
                                     ('env 深挖：新增 8 张图（模块、TypeScript 与 Rust 的分工、SSH 部署、帧格式、一次连接、命令执行、文件操作、文件监视）。', 'env deep dive: 8 new diagrams (modules, the TypeScript / Rust split, SSH deployment, the frame format, one connection, command execution, file operations, file watching).'),
                                     (f'三个包各有 10 页的演示文稿，公共 API 表按 index.ts 的导出自动生成；全站合计 {len(FIGS)} 张图。', f'A 10-slide deck for each package and public-API tables generated from the index.ts exports; {len(FIGS)} diagrams site-wide.')]),
        (('上次更新：mcp 与 codemode 完成（第 5 批）', 'Previous update: mcp and codemode done (batch 5)'), [('mcp 深挖：新增 8 张图（模块、连接生命周期与握手、请求与分页、stdio 传输、Streamable HTTP、OAuth、结果内容与错误、在 pi 中的使用）。', 'mcp deep dive: 8 new diagrams (modules, connection lifecycle and handshake, requests and paging, the stdio transport, Streamable HTTP, OAuth, result content and errors, how pi uses it).'),
                                     ('codemode 深挖：新增 8 张图（模块、三层隔离、一次执行、工具调用往返、脚本 API 与限额、类型与源码格式、TypeScript 声明、在 pi 中的使用）。', 'codemode deep dive: 8 new diagrams (modules, three layers of isolation, one execution, the tool-call round trip, the script API and limits, types and the source format, TypeScript declarations, how pi uses it).'),
                                     ('两个包各有 10 页的演示文稿。', 'A 10-slide deck for each package.'),
                                     ('演示文稿：较高的图（如 tui 的差分渲染、coding-agent 的会话装配与 JSONL 格式）改用“左文右图”版式，显示得更大。', 'Decks: tall diagrams (such as tui differential rendering, coding-agent session wiring and the JSONL format) now use a text-beside-diagram layout and render larger.'),
                                     ('telemetry 按路线图留在第 7 批。', 'telemetry stays in batch 7, as planned.')]),
        (('更早：coding-agent 与 tui 完成', 'Earlier: coding-agent and tui done'), [(f'coding-agent 深挖：新增 9 张图（模块、CLI 启动、AgentSession 装配、会话替换、内置工具、JSONL 格式、扩展 API、RPC 协议、设置与资源），并保留第一版的 4 节', f'coding-agent deep dive: 9 new diagrams (modules, CLI start-up, AgentSession wiring, session replacement, built-in tools, the JSONL format, the extension API, the RPC protocol, settings and resources), keeping the four first-edition sections.'),
                                     ('tui 深挖：新增 8 张图（模块、组件模型、差分渲染、两种屏幕、输入与按键、编辑器与补全、覆盖层、终端能力）。', 'tui deep dive: 8 new diagrams (modules, the component model, differential rendering, the two screens, input and keys, the editor and autocomplete, overlays, terminal capabilities).'),
                                     ('两个包各有 10 页的演示文稿；两个包的公共 API 表按 index.ts 的导出自动生成。', 'A 10-slide deck for each package; both public-API tables are generated from the index.ts exports.'),
                                     ('修复：中文幻灯片页脚显示英文站名。', 'Fix: Chinese slides showed the English site name in the footer.')]),
        (('信息架构', 'Information architecture'), [('单页 → 总览 + 14 个包子页面 + 路线图；全站顶部导航带包切换器，子页面有面包屑。', 'Single page → overview + 14 package pages + roadmap; a global top nav with a package switcher, breadcrumbs on sub-pages.'),
                                                   ('第一版 12 节全部保留：4 节留在总览，8 节迁到所属包页面；旧锚点自动跳转。', 'All 12 first-edition sections kept: 4 stay on the overview, 8 moved to their package pages; old anchors redirect.')]),
        (('新内容', 'New content'), [('agent-core 与 pi-ai 深挖：新增 16 张手绘图（当时合计 28 张），公共 API、扩展点、测试与交叉链接。', 'agent-core and pi-ai deep dives: 16 new hand-laid diagrams (28 in total at the time), plus public API, extension points, tests and cross-links.'),
                                     ('两个包各自的演示文稿；12 个包的自动占位页。', 'A slide deck for each of the two packages; generated placeholder pages for 12 packages.')]),
        (('源码版本', 'Source version'), [(f'分析对象从开发中的提交 `4130bd5` 改为发布标签 `{REF}`（`{SHORT}`，{COMMIT_DATE[:10]}）；所有 GitHub 链接改为指向该标签，所有行号重新计算。', f'The analysed source moved from the in-progress commit `4130bd5` to the release tag `{REF}` (`{SHORT}`, {COMMIT_DATE[:10]}); every GitHub link now targets the tag and every line number was recomputed.'),
                                          ('构建时断言：所有 14 个包的 package.json 版本均为 1.1.0；12 项核心计数（provider、API、事件、RPC 命令等）在标签上与第一版一致。', 'Build-time assertions: all 14 package.json versions are 1.1.0; the 12 core counts (providers, APIs, events, RPC commands …) are unchanged at the tag.')]),
        (('名称', 'Name'), [('站点更名为“图解 Pi Agent”。', 'The site is now called “Pi Agent, Illustrated”.')]),
    ]
    site_html = '<div class="grid2">' + ''.join(f'<div class="card"><h3>{ICON["list"]}{T(t)}</h3><ul>{"".join(f"<li>{T(x)}</li>" for x in items)}</ul></div>' for t, items in site_cl) + '</div>'
    # upstream changelog
    ups = []
    tot = {}
    for p in PK:
        cl = changelog(p['dir'])
        if not cl:
            ups.append(f'<div class="cl-pkg L-{p["layer"]}"><div style="padding:12px 16px;font-size:14px"><b class="mono">{p["slug"]}</b> · <span class="note">{T(("没有 CHANGELOG.md", "no CHANGELOG.md"))}</span></div></div>'); continue
        cnts = ''.join(f'<span>{esc(k)} {len(v)}</span>' for k, v in cl['secs'].items())
        for k, v in cl['secs'].items(): tot[k] = tot.get(k, 0) + len(v)
        body = []
        for k in ('Breaking Changes', 'Added', 'Changed', 'Fixed', 'Removed', 'Deprecated'):
            if k not in cl['secs'] or not cl['secs'][k]: continue
            b = cl['secs'][k]; show = b[:4]
            body.append(f'<h4>{esc(k)} · {len(b)}</h4><ul>' + ''.join(f'<li lang="en">{md(clean_bullet(x))}</li>' for x in show) + ('<li class="note">…</li>' if len(b) > len(show) else '') + '</ul>')
        if not body: body.append(f'<p class="note">{T(("该版本没有单独的条目。", "No entries of its own in this release."))}</p>')
        ups.append(f'<details class="cl-pkg"{" open" if p["status"] == "done" else ""}><summary><span class="dotL L-{p["layer"]}"></span><b>{p["slug"]}</b>{status_dot(p["status"])}<span class="cnt">{cnts}</span></summary>'
                   f'<div class="body">{"".join(body)}<p class="note" style="margin-top:10px">{flink(cl["path"], cl["line"], f"CHANGELOG.md · [{VERSION}] · {cl["date"]}")}</p></div></details>')
    tot_s = ' · '.join(f'{k} {v}' for k, v in tot.items())
    ups_html = f'<p class="note">{T((f"Pi v{VERSION} 发布于 {COMMIT_DATE[:10]}。以下摘自各包 CHANGELOG.md 的 `[{VERSION}]` 段（原文为英文，每类最多显示 4 条）。合计：{tot_s}。", f"Pi v{VERSION} was released on {COMMIT_DATE[:10]}. Excerpts from each package's CHANGELOG.md `[{VERSION}]` section (at most four per category). Totals: {tot_s}."))}</p>' + ''.join(ups)
    secs = [('plan', ('站点规划', 'Site plan'), plan, 'coding'), ('template', ('包模板', 'Package template'), tmpl, 'agent'), ('next', ('下一步', 'Next steps'), nxt_html, 'ai'),
            ('changelog-site', ('本版站点变更', 'What changed in this edition'), site_html, 'ext'), ('changelog', (f'Pi {VERSION} 变更日志', f'Pi {VERSION} changelog'), ups_html, 'modes')]
    body, items = [], []
    for i, (sid, title, h, layer) in enumerate(secs, 1):
        body.append(sec_open(i, sid, layer, title, 'Roadmap' if i < 4 else 'Changelog') + h + '</section>'); items.append((i, sid, title, layer))
    toc = toc_build([(('路线图', 'Roadmap'), items[:3]), (('变更日志', 'Changelog'), items[3:])], [f'<a href="{P}index.html">{T(("← 返回总览", "← Back to overview"))}</a>'])
    hero = f'''<section class="phero L-coding"><div class="wrap">{crumbs(P, [(None, ("路线图", "Roadmap"))])}
<h1>{T(("路线图与变更日志", "Roadmap & changelog"))}<span class="npm">{SITE[1]} · Pi {REF}</span></h1>
<p class="lead">{T(("站点如何组织、每个包的进度、下一步计划，以及 Pi v1.1.0 相对上一版本的变化。", "How the site is organised, where each package stands, what comes next, and what changed in Pi v1.1.0."))}</p></div></section>'''
    page('roadmap/index.html', (f'路线图 · {SITE[0]}', f'Roadmap · {SITE[1]}'), ''.join(body), 'roadmap', toc, hero=hero)

# ---------------------------------------------------------------- slides
def render_deck(relpath, slides=None, **kw):
    from slides import render_slides
    depth = relpath.count('/'); prefix = '../' * depth
    body = render_slides(T=T, md=md, FACTS=FACTS, STATS=STATS, SRC_LOC=SRC_LOC, TEST_LOC=TEST_LOC, SHORT=SHORT, SHA=SHA, GH=GH,
                         COMMIT_DATE=COMMIT_DATE, ICON=ICON, FIGS=FIGS, DEFS=DEFS, PKG_LAYER=PKG_LAYER, LAYER_NAME=LAYER_NAME, fmt=fmt,
                         slides=slides, prefix=prefix, foot=T((f'{SITE[0]} · Pi {REF}', f'{SITE[1]} · Pi {REF}')), ref_url=f'{GH}/tree/{REF}', ref_label=f'github.com/earendil-works/pi · {REF}',
                         eyebrow=f'<b>{REF}</b>{T(SUBTITLE)} · {COMMIT_DATE[:10]}', **kw)
    i = body.index('<body'); i = body.index('>', i) + 1
    body = body[:i] + DEFS + body[i:]
    title = kw.get('deck_title', (f'{SITE[0]} · 演示', f'{SITE[1]} · Slides'))
    dst = OUT / relpath; dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(HEAD(prefix, title, ['slides.css', 'dg.css'], extra=' data-default-theme="dark"') + body)
    PAGES.append(relpath)

def pkg_deck(slug, mod):
    p = PBY[slug]
    secs = {s['diagram']: s for s in mod.SECTIONS}
    sl = [dict(kind='title', h1=(slug, slug), sub=(p['desc'][0], p['desc'][1]), layers=[p['layer']] + [PBY[d]['layer'] for d in p['dep_slugs']][:2])]
    for j, k in enumerate(mod.SLIDE_KEYS, 1):
        s = secs[k]
        kick = (f'{j:02d} · {s["title"][0]}', f'{j:02d} · {s["title"][1]}')
        if FIGS[k].h / FIGS[k].w >= 0.6:   # tall diagrams: text beside the diagram, which then renders larger
            sl.append(dict(kind='side', layer=s['layer'], diagram=k, kicker=kick, title=s['title'], points=s['points'][:2]))
        else:
            sl.append(dict(kind='wide', layer=s['layer'], diagram=k, kicker=kick, title=s['title'], note=s['points'][0]))
    sl.append(dict(kind='close', layer=p['layer'], kicker=('扩展点', 'Extension points'), title=(f'{slug} 的扩展点', f'Where to plug into {slug}'),
                   items=[((k, k), d, p['layer']) for k, d in mod.EXT_POINTS[:5]]))
    render_deck(f'packages/{slug}/slides.html', sl, back='index.html', deck_title=(f'{slug} · {SITE[0]} · 演示', f'{slug} · {SITE[1]} · Slides'))
    return len(sl)

# ---------------------------------------------------------------- fonts (subset, offline)
def build_fonts(text):
    from fontTools import subset
    from fontTools.ttLib import TTCollection
    fd = OUT / 'assets/fonts'; fd.mkdir(parents=True, exist_ok=True)
    g = '/usr/share/fonts/truetype/sand-box/google'
    latin = 'U+0000-00FF,U+0131,U+0152-0153,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2190-21FF,U+2212,U+2215,U+2260-2265,U+25A0-25FF,U+2713,U+2715,U+FEFF,U+FFFD,U+00D7,U+2208-220C,U+222A,U+2205,U+2026'
    def sub(src, dst, unicodes=None, text=None, idx=0):
        opts = subset.Options(); opts.flavor = 'woff2'; opts.layout_features = ['*']; opts.name_IDs = ['*']; opts.font_number = idx
        f = subset.load_font(src, opts, dontLoadGlyphNames=True)
        s = subset.Subsetter(opts)
        s.populate(unicodes=subset.parse_unicodes(unicodes) if unicodes else [], text=text or '')
        s.subset(f); subset.save_font(f, str(fd / dst), opts)
    sym = ''.join(sorted(set(ch for ch in text if 0x2000 <= ord(ch) < 0x2E80)))
    sub(f'{g}/Inter/Inter-VariableFont_opsz,wght.ttf', 'inter-var.woff2', latin)
    sub(f'{g}/JetBrains Mono/JetBrainsMono-VariableFont_wght.ttf', 'jbmono-var.woff2', latin + ',' + ','.join(f'U+{ord(c):04X}' for c in sym))
    cjk = ''.join(sorted(set(ch for ch in text if ord(ch) >= 0x2E80))) + '，。：；！？（）、《》“”‘’…—「」①②③④'
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
    (OUT / 'assets/stats.json').write_text(json.dumps(dict(site=SITE[1], version=VERSION, ref=REF, commit=SHA, commit_date=COMMIT_DATE, facts=FACTS, packages=STATS,
                                                         package_status={p['slug']: p['status'] for p in PK}, extension_events=ext_events,
                                                         rpc_commands=rpc_cmds, tools=tools, session_entry_types=entry_types), indent=1))
    n_ac = pkg_deck('agent-core', deep_agent); n_ai = pkg_deck('pi-ai', deep_ai); n_ca = pkg_deck('coding-agent', deep_ca); n_tui = pkg_deck('tui', deep_tui)
    n_mcp = pkg_deck('mcp', deep_mcp); n_cm = pkg_deck('codemode', deep_cm)
    n_ch = pkg_deck('chord', deep_chord); n_du = pkg_deck('durable', deep_durable); n_env = pkg_deck('env', deep_env)
    build_deep('agent-core', deep_agent, [('sec', 'ac-arch'), ('api', 'api'), ('sec', 'ac-lifecycle'), ('v1', 'loop'), ('sec', 'ac-turn'), ('v1', 'toolexec'),
               ('sec', 'ac-parallel'), ('sec', 'ac-events'), ('sec', 'ac-queues'), ('sec', 'ac-proxy'), ('sec', 'ac-types'), ('ext', 'ext'), ('tests', 'tests'), ('xref', 'xref')],
               api_section_agent, ('4 个测试文件覆盖循环（钩子顺序、队列、并行工具、截断）、Agent 生命周期、端到端与代理流。', 'Four test files cover the loop (hook order, queues, parallel tools, truncation), the Agent lifecycle, end-to-end runs and the proxy stream.'), n_ac)
    build_deep('pi-ai', deep_ai, [('sec', 'ai-entry'), ('sec', 'ai-registry'), ('api', 'api'), ('sec', 'ai-pipeline'), ('v1', 'providers'), ('sec', 'ai-events'),
               ('sec', 'ai-convert'), ('sec', 'ai-anthropic'), ('sec', 'ai-budget'), ('sec', 'ai-oneshot'), ('ext', 'ext'), ('tests', 'tests'), ('xref', 'xref')],
               api_section_ai, ('测试以 provider 为单位组织：每个 API 实现都有流式、工具调用、停止原因与错误路径的测试，另有跨 provider 交接与成本计算测试。', 'Tests are organised per provider: every API implementation has tests for streaming, tool calls, stop reasons and error paths, plus cross-provider handoff and cost tests.'), n_ai)
    build_deep('coding-agent', deep_ca, [('sec', 'ca-arch'), ('api', 'api'), ('sec', 'ca-startup'), ('v1', 'modes'), ('sec', 'ca-session'), ('sec', 'ca-runtime'),
               ('sec', 'ca-tools'), ('sec', 'ca-jsonl'), ('v1', 'session'), ('v1', 'compaction'), ('sec', 'ca-extapi'), ('v1', 'extensions'), ('sec', 'ca-rpc'), ('sec', 'ca-config'),
               ('ext', 'ext'), ('tests', 'tests'), ('xref', 'xref')],
               api_section_ca, ('测试最多的是会话与交互：AgentSession（重试、压缩、排队）、SessionManager 的树与迁移、扩展事件、RPC 协议与各个工具都有独立测试文件。', 'Most tests cover sessions and interaction: AgentSession (retry, compaction, queues), the SessionManager tree and migrations, extension events, the RPC protocol and each tool have their own test files.'), n_ca)
    build_deep('tui', deep_tui, [('sec', 'tui-arch'), ('api', 'api'), ('sec', 'tui-component'), ('v1', 'tui'), ('sec', 'tui-render'), ('sec', 'tui-screens'),
               ('sec', 'tui-input'), ('sec', 'tui-editor'), ('sec', 'tui-overlay'), ('sec', 'tui-terminal'), ('ext', 'ext'), ('tests', 'tests'), ('xref', 'xref')],
               api_section_tui, ('测试集中在按键解析、编辑器行为、差分渲染与覆盖层布局；大部分用虚拟终端断言实际输出的转义序列和屏幕内容。', 'Tests concentrate on key parsing, editor behaviour, differential rendering and overlay layout; most assert the actual escape sequences and screen contents on a virtual terminal.'), n_tui)
    build_deep('mcp', deep_mcp, [('sec', 'mcp-arch'), ('api', 'api'), ('sec', 'mcp-lifecycle'), ('sec', 'mcp-requests'), ('sec', 'mcp-stdio'), ('sec', 'mcp-http'),
               ('sec', 'mcp-oauth'), ('sec', 'mcp-content'), ('sec', 'mcp-pi'), ('ext', 'ext'), ('tests', 'tests'), ('xref', 'xref')],
               api_section_mcp, ('每个模块一个测试文件：客户端（握手、请求、分页、取消）、内容转换、OAuth 流程、stdio 子进程与 Streamable HTTP；大多通过内存传输、测试用子进程或本地 HTTP 服务器端到端验证。', 'One test file per area: the client (handshake, requests, paging, cancellation), content conversion, the OAuth flow, stdio child processes and Streamable HTTP; most run end to end over the in-memory transport, a fixture child process or a local HTTP server.'), n_mcp)
    build_deep('codemode', deep_cm, [('sec', 'cm-arch'), ('api', 'api'), ('sec', 'cm-sandbox'), ('sec', 'cm-exec'), ('sec', 'cm-bridge'), ('sec', 'cm-prelude'),
               ('sec', 'cm-types'), ('sec', 'cm-decl'), ('sec', 'cm-pi'), ('ext', 'ext'), ('tests', 'tests'), ('xref', 'xref')],
               api_section_cm, ('三个测试文件：沙箱（真实的 worker 与 QuickJS，覆盖工具调用、超时、中止、限额与锁定）、声明渲染与源码解析。', 'Three test files: the sandbox (a real worker and QuickJS, covering tool calls, timeouts, aborts, limits and lockdown), declaration rendering and source parsing.'), n_cm)
    build_deep('chord', deep_chord, [('sec', 'chord-arch'), ('api', 'api'), ('sec', 'chord-facets'), ('sec', 'chord-reload'), ('sec', 'chord-services'), ('sec', 'chord-remote'),
               ('sec', 'chord-state'), ('sec', 'chord-delta'), ('sec', 'chord-bundle'), ('ext', 'ext'), ('tests', 'tests'), ('xref', 'xref')],
               api_section_chord, ('测试按模块分文件：facet 宿主与加载器、服务（含线格式与更新投递）、复制状态（值、差分、草稿、投递与模糊测试）、增量（应用、克隆、差分）、上下文与打包，另有增量性能基准。', 'Tests are split by area: the facet host and loaders, services (including the wire format and update delivery), replicated state (values, diffs, drafts, delivery and a fuzz test), deltas (apply, clone, diff), context and bundling, plus delta benchmarks.'), n_ch)
    build_deep('durable', deep_durable, [('sec', 'dur-arch'), ('api', 'api'), ('sec', 'dur-model'), ('sec', 'dur-run'), ('sec', 'dur-tasks'), ('sec', 'dur-inbox'),
               ('sec', 'dur-docs'), ('sec', 'dur-storage'), ('sec', 'dur-ext'), ('ext', 'ext'), ('tests', 'tests'), ('xref', 'xref')],
               api_section_durable, ('测试覆盖会话与 Harness、任务的恢复与迁移、文档、收件箱、压缩与各个存储后端；存储与执行环境另有可复用的一致性套件（`./testing`），env 包用同一套件验证远程实现。', 'Tests cover sessions and the Harness, task recovery and migration, documents, the inbox, compaction and every storage backend; storage and the execution environment also have reusable conformance suites (`./testing`), which the env package runs against its remote implementation.'), n_du)
    build_deep('env', deep_env, [('sec', 'env-arch'), ('api', 'api'), ('sec', 'env-split'), ('sec', 'env-ssh'), ('sec', 'env-frames'), ('sec', 'env-session'),
               ('sec', 'env-exec'), ('sec', 'env-files'), ('sec', 'env-watch'), ('ext', 'ext'), ('tests', 'tests'), ('xref', 'xref')],
               api_section_env, ('TypeScript 测试跑 durable 的执行环境一致性套件，并与本机 `NodeExecutionEnv` 做差分对比；SSH 测试覆盖主机密钥与部署；守护进程的 Rust 代码另有自己的单元测试。', 'The TypeScript tests run durable\'s execution-environment conformance suite and diff the results against the local `NodeExecutionEnv`; the SSH tests cover host keys and deployment; the daemon\'s Rust code has its own unit tests.'), n_env)
    for p in PK:
        if p['status'] == 'planned': build_stub(p['slug'])
    render_deck('slides.html')
    build_hub(len(SLIDES)); build_roadmap()
    text = ''.join((OUT / r).read_text() for r in PAGES) + ''.join(p.read_text() for p in (OUT / 'assets').glob('*.js'))
    assert '1.10.0' not in text, 'stale version string'
    n = build_fonts(text)
    (OUT / 'assets/pages.json').write_text(json.dumps(PAGES, indent=1))
    print('built', OUT, 'pages', len(PAGES), FACTS, 'figs', len(FIGS), 'cjk glyphs', n, 'ref', REF, SHORT)

if __name__ == '__main__': main()
