# ---------------------------------------------------------------- package registry + version check
import pkgmeta, deep_agent, deep_ai, deep_ca, deep_tui, deep_mcp, deep_cm, deep_chord, deep_durable, deep_env, deep_protocol, deep_client, deep_server  # noqa
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
 'proto_arch': ('pi-protocol 的三层：信封 schema、编解码与分帧', 'pi-protocol in three layers: envelope schemas, codec and framing'),
 'proto_pipe': ('一条消息的往返：校验、CBOR、分帧与反向解码', 'One message there and back: validation, CBOR, framing and decoding'),
 'proto_messages': ('协议版本 8 的 3 种客户端消息与 5 种服务端消息', 'Protocol version 8: 3 client messages and 5 server messages'),
 'proto_targets': ('RpcTarget：逻辑服务器、持久 Session 与实时附着', 'RpcTarget: logical server, durable Session and live attachment'),
 'proto_handshake': ('一条连接上的消息顺序：握手、请求、附着、订阅与取消', 'Message order on one connection: handshake, requests, attachment, subscriptions, cancellation'),
 'proto_frame': ('4 字节长度前缀与 FrameDecoder 的状态', 'The 4-byte length prefix and FrameDecoder states'),
 'proto_cbor': ('严格的 CBOR 子集：主类型、上限与一个编码例子', 'The strict CBOR subset: major types, limits and a worked encoding'),
 'proto_chord': ('分界：信封归 protocol，调用归 chord，数据归应用', 'The boundary: envelope for protocol, call for chord, data for the application'),
 'cli_arch': ('pi-client 的结构：Client、Connection 与可替换的字节传输', 'pi-client: Client, Connection and a pluggable byte transport'),
 'cli_lifecycle': ('Connection 的三个状态与握手失败', 'Connection in three states, and handshake failures'),
 'cli_request': ('一个请求：守卫、登记、编码、发送与按 id 结算', 'One request: guards, registration, encoding, sending and settlement by id'),
 'cli_subscribe': ('一个服务订阅：快照之前缓冲，start() 之后按序交付', 'One service subscription: buffered before the snapshot, ordered after start()'),
 'cli_attach': ('带外附着与 createClientServiceTransport', 'Out-of-band attachments and createClientServiceTransport'),
 'cli_transport': ('ByteTransport 契约与 Unix 写队列', 'The ByteTransport contract and the Unix write queue'),
 'cli_discover': ('discoverUnixServers：目录、过滤与并发握手探测', 'discoverUnixServers: directory, filtering and concurrent handshake probes'),
 'cli_errors': ('五种错误与断开之后的恢复', 'Five errors and recovery after a disconnect'),
 'srv_arch': ('pi-server 的结构：Server、SessionRouter、监听器与测试工具', 'pi-server: Server, SessionRouter, listeners and the testing kit'),
 'srv_host': ('ServerHost：应用交给 Server 的能力', 'ServerHost: the capabilities the app hands to the Server'),
 'srv_conn': ('一条服务器连接的五个阶段与握手', 'Five stages of a server connection, and the handshake'),
 'srv_request': ('handleRequest：核对、路由、订阅与错误映射', 'handleRequest: checks, routing, subscriptions and error mapping'),
 'srv_router': ('SessionRouter：按连接串行的 attach 与调用准入', 'SessionRouter: per-connection attach and call admission'),
 'srv_release': ('附着结束的六种方式与唯一的释放路径', 'Six ways an attachment ends, and the one release path'),
 'srv_unix': ('Unix 监听器：私有绑定、硬链接发布、按身份清理', 'The Unix listener: private bind, hard-link publish, identity-checked cleanup'),
 'srv_errors': ('ServerError 的五个子类与 ./testing 工具', 'The five ServerError subclasses and the ./testing kit'),
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
