"""pi-coding-agent deep-dive diagrams (ca_*). Facts read from /workspace/pi-src/packages/coding-agent at build time."""
import re, json
from svgkit import Fig, maxw, tw, icon, pair
from figs import reg
from figkit import SRC, uml, codebox, bar, dot, hline, vline, chiprow, lines_of

CA = 'packages/coding-agent/'
S = CA + 'src/'
def _src(p): return (SRC / (S + p)).read_text()
def loc(p):
    q = SRC / (S + p)
    if q.is_file(): return lines_of(S + p)
    return sum(lines_of(str(x.relative_to(SRC))) for x in q.rglob('*.ts') if not x.name.endswith(('.test.ts', '.d.ts')))
def nfiles(p): return sum(1 for x in (SRC / (S + p)).rglob('*.ts') if not x.name.endswith(('.test.ts', '.d.ts')))
def L(n): return (f'{n:,} 行', f'{n:,} lines')

def ext_events():
    s = _src('core/extensions/types.ts')
    m = re.search(r'^export interface ExtensionAPI\b.*?^\}', s, re.M | re.S)
    return sorted(set(re.findall(r'\bon\(\s*event: "([a-z_]+)"', m.group(0))))
def api_methods():
    s = _src('core/extensions/types.ts')
    m = re.search(r'^export interface ExtensionAPI\b.*?^\}', s, re.M | re.S)
    return sorted(set(re.findall(r'^\t([a-zA-Z]+)[<(]', m.group(0), re.M)) - {'on'})
def iface_members(name, path='core/extensions/types.ts'):
    s = _src(path)
    m = re.search(r'^export interface ' + name + r'\b[^{]*\{(.*?)^\}', s, re.M | re.S)
    out = []
    for n in re.findall(r'^\t(?:readonly )?([a-zA-Z]+)\??[(:<]', m.group(1), re.M):
        if n not in out: out.append(n)
    return out
def rpc_commands():
    s = _src('modes/rpc/rpc-types.ts')
    blk = re.search(r'^export type RpcCommand =(.*?);\n', s, re.M | re.S).group(1)
    groups, cur = [], None
    for ln in blk.splitlines():
        c = re.match(r'\s*// (.+)', ln)
        if c: cur = [c.group(1).split(' (')[0], []]; groups.append(cur); continue
        t = re.search(r'type: "([a-z_]+)"', ln)
        if t and cur: cur[1].append(t.group(1))
    return groups
def entry_types():
    s = (SRC / (S + 'core/session-manager.ts')).read_text()
    return re.findall(r'^export interface [A-Za-z]+Entry(?:<[^>]*>)? extends SessionEntryBase \{\n\ttype: "([a-z_]+)"', s, re.M)

# ============================================================== ca_arch : module map
@reg
def ca_arch():
    f = Fig('ca_arch', 1120, 600, ('pi-coding-agent 模块结构', 'pi-coding-agent modules'))
    f.text(24, 70, ('入口', 'ENTRY POINTS'), 10.5, 700, cls='faint', layer='label', ls='.08em')
    f.node('cli', 24, 88, 196, 56, 'modes', 'cli.ts', ('bin: pi → setupCli()', 'bin: pi → setupCli()'), 'terminal', ssize=10.5)
    f.node('rpce', 24, 160, 196, 56, 'modes', 'rpc-entry.ts', ('main(["--mode","rpc",…])', 'main(["--mode","rpc",…])'), 'plug', ssize=10.5)
    f.node('main', 24, 262, 196, 72, 'coding', 'main.ts', ('参数 → 会话 → 模式', 'args → session → mode'), 'play', sub2=L(loc('main.ts')), strong=True, ssize=10.5)
    nidx = len([l for l in _src('index.ts').splitlines() if l.startswith('export')])
    f.node('idx', 24, 384, 196, 72, 'coding', 'index.ts', ('SDK 入口', 'SDK entry point'), 'braces', sub2=(f'{nidx} 条 export 语句', f'{nidx} export statements'), ssize=10.5)
    E = f.edge
    E([(122, 216), (122, 262)], 'rpce', 'main', 'dep')
    E([(220, 116), (236, 116), (236, 286), (220, 286)], 'cli', 'main', 'main', 'modes', r=6)
    # core
    GX, GW = 248, 640
    f.group(GX, 52, GW, 404, 'coding', 'src/core/', (f'{nfiles("core")} 个文件 · {loc("core"):,} 行', f'{nfiles("core")} files · {loc("core"):,} lines'), 'box', gid='core')
    cells = [('agent-session.ts', ('提示 · 队列 · 压缩 · 重试', 'prompt · queues · compact · retry'), 'cpu', True),
             ('agent-session-runtime.ts', ('替换会话：new · switch · fork', 'replace: new · switch · fork'), 'loop', True),
             ('sdk.ts', ('createAgentSession()：组装 Agent', 'createAgentSession(): wires Agent'), 'plug', True),
             ('session-manager.ts', ('JSONL 会话树 · 11 种条目', 'JSONL session tree · 11 entry types'), 'tree', False),
             ('compaction/', ('压缩与分支摘要', 'compaction · branch summaries'), 'compress', False),
             ('tools/', ('8 个内置工具 · 截断', '8 built-in tools · truncation'), 'tool', False),
             ('extensions/', ('jiti 加载 · runner · 41 种事件', 'jiti loader · runner · 41 events'), 'plug', False),
             ('model-runtime.ts', ('provider · 认证 · 模型路由', 'providers · auth · routing'), 'spark', False),
             ('settings-manager.ts', ('全局 + 项目 settings.json', 'global + project settings.json'), 'gear', False),
             ('resource-loader.ts', ('扩展 · 技能 · 提示模板', 'extensions · skills · prompts'), 'layers', False),
             ('package-manager.ts', ('npm / git 包 · pi 清单', 'npm / git packages · pi manifest'), 'box', False),
             ('system-prompt.ts', ('分段构建 system 提示', 'sectioned system prompt'), 'file', False)]
    CW = 196
    for i, (p, sub, ic, strong) in enumerate(cells):
        x = GX + 16 + (i % 3) * (CW + 10); y = 96 + (i // 3) * 88
        nid = 'c%d' % i
        f.node(nid, x, y, CW, 76, 'coding', p, sub, None, sub2=L(loc('core/' + p.rstrip('/'))), ssize=10, tsize=11.5 if len(p) > 18 else 12.5, strong=strong)
    E([(220, 310), (GX, 310)], 'main', 'core', 'main', 'coding', flow=True)
    E([(220, 420), (GX, 420)], 'idx', 'core', 'dep')
    # modes etc.
    MX, MW = 904, 192
    f.group(MX, 52, MW, 270, 'modes', 'src/modes/', (f'{loc("modes"):,} 行', f'{loc("modes"):,} lines'), 'monitor', gid='modes')
    f.node('mi', MX + 14, 96, MW - 28, 64, 'modes', 'interactive/', ('InteractiveMode · TUI', 'InteractiveMode · TUI'), None, sub2=L(loc('modes/interactive')), ssize=10)
    f.node('mp', MX + 14, 170, MW - 28, 64, 'modes', 'print-mode.ts', ('text · json 事件流', 'text · json event stream'), None, sub2=L(loc('modes/print-mode.ts')), ssize=10)
    f.node('mr', MX + 14, 244, MW - 28, 64, 'modes', 'rpc/', ('JSONL stdin/stdout', 'JSONL over stdin/stdout'), None, sub2=L(loc('modes/rpc')), ssize=10)
    E([(MX, 200), (GX + GW, 200)], 'modes', 'core', 'main', 'modes', label=('驱动', 'drive'), lpos=(896, 186), lmono=False, lsize=9.5)
    f.node('bext', MX, 338, MW, 52, 'ext', 'src/extensions/', (f'内置扩展 · {loc("extensions"):,} 行', f'built-in · {loc("extensions"):,} lines'), 'plug', ssize=10)
    f.node('exp', MX, 404, MW, 52, 'infra', 'src/experimental/', (f'实验功能 · {loc("experimental"):,} 行', f'experimental · {loc("experimental"):,} lines'), 'flag', ssize=10)
    # deps band
    pj = json.loads((SRC / CA / 'package.json').read_text())
    deps = sorted(pj.get('dependencies', {}))
    internal = [d.split('/')[-1] for d in deps if d.startswith('@earendil-works/')]
    lay = {'pi-agent-core': 'agent', 'pi-ai': 'ai', 'pi-tui': 'tui', 'pi-mcp': 'ext', 'pi-codemode': 'ext', 'pi-telemetry': 'infra'}
    y = 486
    f.raw(f'<rect class="band" x="16" y="{y-8}" width="1088" height="44" rx="10"/>', 'bg')
    f.text(32, y + 18, ('内部依赖', 'Internal deps'), 11, 700, cls='strongt', layer='label')
    x = 136
    for d in internal: x += f.chip(x, y + 4, d, lay.get(d, 'infra'), size=10, h=20, cls='solid' if d == 'pi-agent-core' else '') + 6
    f.text(1088, y + 18, (f'+ {len(deps) - len(internal)} 个外部依赖', f'+ {len(deps) - len(internal)} external deps'), 11, 600, cls='muted', layer='label', anchor='end')
    f.legend(24, 572, [('main', ('主路径', 'main path')), ('dep', ('import / 调用', 'import / call')), ('layer:coding', 'core'), ('layer:modes', 'modes'), ('layer:ext', ('扩展', 'extensions')), ('layer:infra', ('其他', 'other'))])
    return f

# ============================================================== ca_startup : CLI startup pipeline
@reg
def ca_startup():
    f = Fig('ca_startup', 1120, 560, ('pi 启动流程（cli.ts → main.ts）', 'pi startup (cli.ts → main.ts)'))
    W, H = 200, 84
    XS = [24, 242, 460, 678, 896]
    Y = [64, 214, 364]
    rows = [
        [('setupCli()', ('进程标题 · 环境变量', 'process title · env flags'), 'configureHttpDispatcher()', 'modes', 'terminal'),
         ('main(args)', ('内置扩展 + 自定义工厂', 'built-in + custom factories'), ('--offline → PI_OFFLINE', '--offline → PI_OFFLINE'), 'coding', 'play'),
         (('一次性命令', 'one-shot commands'), 'auth · package · config · mcp', ('处理后直接退出', 'handled → exit'), 'infra', 'bolt'),
         ('parseArgs(args)', ('诊断错误 → exit 1', 'diagnostics → exit 1'), ('--version · --export → 退出', '--version · --export → exit'), 'coding', 'filter'),
         ('resolveAppMode()', 'rpc · json · print · interactive', ('非交互 → 接管 stdout', 'non-TTY → takeOverStdout()'), 'modes', 'monitor')],
        [('runMigrations(cwd)', ('auth · 会话 · 工具 · 键位', 'auth · sessions · tools · keys'), ('弃用警告（交互模式显示）', 'deprecation warnings'), 'infra', 'diff'),
         ('SettingsManager', ('全局 + 项目设置', 'global + project settings'), ('首次运行设置（仅 TTY）', 'first-time setup (TTY)'), 'coding', 'gear'),
         ('createSessionManager()', '--session · --resume · --fork', ('--no-session → 内存', '--no-session → in memory'), 'coding', 'tree'),
         ('ProjectTrustStore', ('按 cwd 记录项目信任', 'project trust per cwd'), ('决定是否加载 .pi/ 资源', 'gates project .pi/ resources'), 'err', 'shield'),
         ('createAgentSessionRuntime()', ('传入 createRuntime 工厂', 'takes a createRuntime factory'), ('之后的会话替换也用它', 'reused for every replacement'), 'coding', 'loop')],
        [('createAgentSessionServices()', 'ModelRuntime · ResourceLoader', ('扩展注册的 provider 入表', 'extension providers registered'), 'coding', 'layers'),
         ('createAgentSession()', ('经 …FromServices() 进入 sdk.ts', 'sdk.ts, via …FromServices()'), ('模型 · thinking · 工具', 'model · thinking · tools'), 'coding', 'cpu'),
         ('prepareInitialMessage()', ('管道 stdin + @文件参数', 'piped stdin + @file args'), ('图片自动缩放', 'images auto-resized'), 'coding', 'inbox'),
         ('initTheme() · diagnostics', ('运行时错误 → exit 1', 'runtime errors → exit 1'), ('非交互且无模型 → exit 1', 'no model (non-TTY) → exit 1'), 'err', 'eye')]]
    k = 0
    for r, row in enumerate(rows):
        for c, (t, s1, s2, lay, ic) in enumerate(row):
            k += 1
            x = XS[c] if r != 1 else XS[4 - c]
            ts = 12.5 if maxw(t, 12.5, 620, True) < W - 26 else 11 if maxw(t, 11, 620, True) < W - 26 else 9.8
            f.node('s%d' % k, x, Y[r], W, H, lay, t, s1, None, sub2=s2, ssize=9.8, tsize=ts, mono=isinstance(t, str), strong=(k in (2, 10, 12)))
            f.step(k, x + 2, Y[r] + 2, 'accent', r=9, onnode=True)
    E = f.edge
    for r in range(3):
        n = 5 if r < 2 else 4
        for c in range(n - 1):
            a, b = r * 5 + c + 1, r * 5 + c + 2
            if r == 1:
                E([(XS[4 - c], Y[r] + H / 2), (XS[3 - c] + W, Y[r] + H / 2)], 's%d' % a, 's%d' % b, 'main', 'accent')
            else:
                E([(XS[c] + W, Y[r] + H / 2), (XS[c + 1], Y[r] + H / 2)], 's%d' % a, 's%d' % b, 'main', 'accent')
    E([(XS[4] + W / 2, Y[0] + H), (XS[4] + W / 2, Y[1])], 's5', 's6', 'main', 'accent')
    E([(XS[0] + W / 2, Y[1] + H), (XS[0] + W / 2, Y[2])], 's10', 's11', 'main', 'accent', label=('createRuntime()', 'createRuntime()'), lpos=(XS[0] + W / 2, (Y[1] + H + Y[2]) / 2), lsize=9.5)
    # mode dispatch
    mx = XS[4]; my = Y[2]
    f.text(mx, my - 8, ('按模式分派', 'DISPATCH BY MODE'), 10, 700, cls='faint', layer='label', ls='.06em')
    modes = [('mr', 'runRpcMode(runtime)', 'modes'), ('mi', 'InteractiveMode.run()', 'tui'), ('mp', 'runPrintMode(runtime)', 'modes')]
    for i, (nid, t, lay) in enumerate(modes):
        f.node(nid, mx + 24, my + i * 30, W - 24, 26, lay, t, None, None, tsize=10.5, kind='pill', align='center')
    E([(XS[3] + W, Y[2] + H / 2), (mx + 8, Y[2] + H / 2), (mx + 8, my + 13), (mx + 24, my + 13)], 's14', 'mr', 'main', 'accent', r=5)
    E([(mx + 8, Y[2] + H / 2), (mx + 8, my + 73), (mx + 24, my + 73)], 's14', 'mp', 'main', 'accent', r=5)
    E([(mx + 8, my + 43), (mx + 24, my + 43)], 's14', 'mi', 'main', 'accent')
    f.note(1096, 494, ('rpc 模式不读管道 stdin（stdin 用于 JSONL 命令）；--help / --list-models 在运行时创建后退出', 'rpc mode never reads piped stdin (stdin carries JSONL commands); --help / --list-models exit after the runtime exists'), 10.5, anchor='end')
    f.legend(24, 532, [('main', ('启动顺序', 'startup order')), ('step', ('步骤', 'step')), ('layer:coding', 'core'), ('layer:modes', 'modes'), ('layer:err', ('门控 / 退出', 'gate / exit')), ('layer:infra', ('一次性', 'one-shot'))])
    return f

# ============================================================== ca_session : what AgentSession plugs into Agent
@reg
def ca_session():
    f = Fig('ca_session', 1120, 756, ('AgentSession 如何装配 Agent', 'How AgentSession wires the Agent'))
    rows = [
        ('sdk', 'streamFn', ('ModelRuntime.streamSimple(model, ctx, opts)', 'ModelRuntime.streamSimple(model, ctx, opts)'), ('会话请求顺带启动 CacheWarmer', 'session requests also start the CacheWarmer'), ('mr', 'ModelRuntime', 'ai')),
        ('sdk', 'convertToLlm', ('messages.ts convertToLlm()', 'messages.ts convertToLlm()'), ('blockImages 开启时再过滤一次图片', 'filters images again when blockImages is on'), ('msg', 'messages.ts', 'coding')),
        ('sdk', 'transformContext', ('ExtensionRunner.emitContext(messages)', 'ExtensionRunner.emitContext(messages)'), ('扩展的 "context" 事件可改写上下文', 'the extension "context" event can rewrite context'), ('er1', 'ExtensionRunner', 'ext')),
        ('as', 'prepareRequest', ('请求投影 · 虚拟模型路由', 'request projection · virtual-model routing'), ('resolveModel() 只影响本次请求', 'resolveModel() affects this request only'), ('mr2', 'ModelRuntime', 'ai')),
        ('as', 'beforeToolCall', ('扩展 "tool_call" 事件', 'extension "tool_call" event'), ('可阻止执行；扩展出错也会阻止', 'may block; an extension error blocks too'), ('er2', 'ExtensionRunner', 'ext')),
        ('as', 'afterToolCall', ('扩展 "tool_result" 事件 + 图片规范化', 'extension "tool_result" + image normalization'), ('可改写 content / details', 'may rewrite content / details'), ('er3', 'ExtensionRunner', 'ext')),
        ('as', 'finishTurn', ('"turn_end" 边界：扩展可追加条目', '"turn_end" boundary: extensions may append'), ('emitBoundary() 先预演再写入会话', 'emitBoundary() previews, then persists'), ('er4', 'ExtensionRunner', 'ext')),
        ('as', 'prepareNextTurn', ('超阈值先压缩 · 重建 system 提示与工具', 'threshold compaction · rebuild prompt + tools'), ('_compactBeforeNextAssistantResponse()', '_compactBeforeNextAssistantResponse()'), ('sm1', 'SessionManager', 'coding')),
        ('as', 'subscribe()', ('_handleAgentEvent：先扩展，后监听器', '_handleAgentEvent: extensions, then listeners'), ('message_end → SessionManager.appendMessage()', 'message_end → SessionManager.appendMessage()'), ('sm2', 'SessionManager', 'coding')),
    ]
    Y0, RH = 100, 46
    AX, AW = 168, 236
    f.group(AX - 14, 52, AW + 28, Y0 + len(rows) * RH - 52 + 6, 'agent', 'Agent', '(pi-agent-core)', 'cpu', gid='agent', title_mono=True)
    f.text(24, 74, ('安装者', 'INSTALLED BY'), 10, 700, cls='faint', layer='label', ls='.06em')
    f.text(458, 74, ('AgentSession 的实现', "AGENTSESSION'S IMPLEMENTATION"), 10, 700, cls='faint', layer='label', ls='.06em')
    f.text(904, 74, ('协作者', 'COLLABORATOR'), 10, 700, cls='faint', layer='label', ls='.06em')
    for i, (who, slot, impl, sub, (cid, cname, clay)) in enumerate(rows):
        y = Y0 + i * RH
        f.chip(24, y + 8, 'sdk.ts' if who == 'sdk' else 'AgentSession', 'coding' if who == 'as' else 'infra', size=9.5, h=20, cls='solid' if who == 'as' else '')
        f.node('h%d' % i, AX, y, AW, 36, 'agent', slot, None, None, tsize=12, strong=True)
        f.node('i%d' % i, 458, y - 2, 420, 40, 'coding', impl, sub, None, tsize=11, ssize=10, mono=True)
        f.node(cid, 904, y + 4, 192, 28, clay, cname, None, None, tsize=11, kind='pill', align='center')
        f.edge([(AX + AW, y + 18), (458, y + 18)], 'h%d' % i, 'i%d' % i, 'main' if who == 'as' else 'dep', 'coding' if who == 'as' else None)
        f.edge([(878, y + 18), (904, y + 18)], 'i%d' % i, cid, 'dep')
    # post-run loop
    by = Y0 + len(rows) * RH + 26
    f.group(16, by, 1088, 162, 'coding', ('运行之后：_runAgentPrompt() 的外层循环', 'After a run: the outer loop in _runAgentPrompt()'), None, 'loop', title_mono=False, gid='post')
    steps = [('agent.prompt()', ('或 agent.continue()', 'or agent.continue()'), 'agent'),
             ('_handlePostAgentRun()', ('检查最后一条 assistant', 'inspect the last assistant'), 'coding'),
             (('可重试错误？', 'retryable error?'), ('_prepareRetry() → 退避', '_prepareRetry() → backoff'), 'err'),
             ('_checkCompaction()', ('overflow / threshold', 'overflow / threshold'), 'coding'),
             (('还有排队消息？', 'queued messages?'), ('hasQueuedMessages()', 'hasQueuedMessages()'), 'coding'),
             ('agent_settled', ('agent_before_settle 之后', 'after agent_before_settle'), 'term')]
    sw, sx0, gap = 158, 36, 20
    sy = by + 52
    for j, (t, s, lay) in enumerate(steps):
        x = sx0 + j * (sw + gap)
        f.node('p%d' % j, x, sy, sw, 50, lay, t, s, None, tsize=10.5 if isinstance(t, str) else 11.5, ssize=9.5, mono=isinstance(t, str), kind='term' if lay == 'term' else 'card', align='center' if lay == 'term' else 'left')
        if j: f.edge([(x - gap, sy + 25), (x, sy + 25)], 'p%d' % (j - 1), 'p%d' % j, 'main', 'coding')
    # loop back: retry / compaction / queued → continue
    lx = [sx0 + j * (sw + gap) + sw / 2 for j in range(6)]
    f.edge([(lx[2], sy + 50), (lx[2], sy + 74), (lx[0], sy + 74), (lx[0], sy + 50)], 'p2', 'p0', 'event', 'err', label=('是 → continue()', 'yes → continue()'), lpos=((lx[0] + lx[2]) / 2 - 30, sy + 74), lmono=False, lsize=9.5, r=6)
    f.edge([(lx[3] - 30, sy + 50), (lx[3] - 30, sy + 86), (lx[0] - 30, sy + 86), (lx[0] - 30, sy + 50)], 'p3', 'p0', 'event', 'coding', r=6)
    f.edge([(lx[4], sy + 50), (lx[4], sy + 86), (lx[3] - 30, sy + 86)], 'p4', 'p0', 'event', 'coding', label=('压缩后 / 有排队 → 再跑一次', 'compacted / queued → run again'), lpos=((lx[3] + lx[4]) / 2, sy + 86), lmono=False, lsize=9.5, r=6, arrow=False)
    f.legend(24, 738, [('main', ('AgentSession 安装的钩子', 'hook installed by AgentSession')), ('dep', ('sdk.ts 在 new Agent() 时传入', 'passed by sdk.ts to new Agent()')), ('event', ('循环回到 continue()', 'loops back to continue()')), ('layer:agent', 'pi-agent-core'), ('layer:ext', ('扩展', 'extensions'))])
    return f

# ============================================================== ca_runtime : session replacement lifecycle
@reg
def ca_runtime():
    f = Fig('ca_runtime', 1120, 600, ('AgentSessionRuntime：替换会话', 'AgentSessionRuntime: replacing the session'))
    h = uml(f, 'rt', 24, 52, 300, 'coding', 'AgentSessionRuntime', '«class»', [
        ['-_session: AgentSession', '-_services: AgentSessionServices', '-createRuntime: Factory', '-rebindSession?(session)', '-beforeSessionInvalidate?()'],
        ['+switchSession(path)', '+newSession({ parentSession })', '+fork(entryId, { position })', '+importFromJsonl(path)', '+dispose()']])
    h2 = uml(f, 'svc', 24, 52 + h + 22, 300, 'coding', 'AgentSessionServices', '«cwd-bound»', [
        ['+cwd · agentDir', '+modelRuntime: ModelRuntime', '+settingsManager: SettingsManager', '+resourceLoader: ResourceLoader', '+diagnostics[]']])
    f.edge([(174, 52 + h), (174, 52 + h + 22)], 'rt', 'svc', 'dep', smark='diamond', arrow=False)
    # flow
    X0, W, H = 372, 340, 54
    steps = [('emitBeforeSwitch / emitBeforeFork', ('session_before_switch · session_before_fork', 'session_before_switch · session_before_fork'), 'ext'),
             (('打开 / 新建 SessionManager', 'open / create the SessionManager'), ('open() · create() · createBranchedSession()', 'open() · create() · createBranchedSession()'), 'coding'),
             ('teardownCurrent(reason)', ('abort() → session_shutdown → dispose()', 'abort() → session_shutdown → dispose()'), 'err'),
             ('createRuntime({ cwd, sessionManager })', ('新的 services + AgentSession', 'fresh services + AgentSession'), 'coding'),
             ('apply(result)', ('替换 session · services · diagnostics', 'swap session · services · diagnostics'), 'coding'),
             ('finishSessionReplacement()', ('rebindSession() → withSession(ctx)', 'rebindSession() → withSession(ctx)'), 'modes')]
    for i, (t, s, lay) in enumerate(steps):
        y = 52 + i * 84
        f.node('f%d' % i, X0, y, W, H, lay, t, s, None, tsize=11 if isinstance(t, str) else 12, ssize=10, mono=isinstance(t, str), strong=i in (3, 5))
        f.step(i + 1, X0 - 14, y + H / 2, 'accent', r=9)
        if i: f.edge([(X0 + W / 2, y - 30), (X0 + W / 2, y)], 'f%d' % (i - 1), 'f%d' % i, 'main', 'accent')
    f.edge([(324, 52 + 26), (X0 - 26, 52 + 26)], 'rt', 'f0', 'main', 'accent')
    f.node('cancel', 800, 52, 160, H, 'err', ('cancel: true', 'cancel: true'), ('→ { cancelled: true }', '→ { cancelled: true }'), None, tsize=11, ssize=10, kind='err')
    f.edge([(X0 + W, 52 + 27), (800, 52 + 27)], 'f0', 'cancel', 'err', label=('扩展取消', 'ext cancels'), lpos=(756, 79), lmono=False, lsize=9.5)
    # side annotations
    f.node('ss', 760, 52 + 5 * 84, 336, H, 'ext', 'session_start { reason }', ('新会话的扩展收到启动事件', "the new session's extensions start"), 'play', tsize=11, ssize=10)
    f.edge([(X0 + W, 52 + 5 * 84 + 27), (760, 52 + 5 * 84 + 27)], 'f5', 'ss', 'event', 'ext')
    f.node('ui', 760, 52 + 2 * 84, 336, H, 'modes', 'beforeSessionInvalidate()', ('同步卸下扩展的 TUI 组件', 'detach extension TUI widgets (sync)'), 'monitor', tsize=11, ssize=10)
    f.edge([(X0 + W, 52 + 2 * 84 + 27), (760, 52 + 2 * 84 + 27)], 'f2', 'ui', 'dep')
    f.node('cr', 760, 52 + 3 * 84, 336, H, 'coding', 'createAgentSessionServices()', ('+ createAgentSessionFromServices()', '+ createAgentSessionFromServices()'), 'layers', tsize=11, ssize=10)
    f.edge([(X0 + W, 52 + 3 * 84 + 27), (760, 52 + 3 * 84 + 27)], 'f3', 'cr', 'dep')
    # reasons table
    ty = 560
    f.raw(f'<rect class="band" x="16" y="{ty-30}" width="1088" height="52" rx="10"/>', 'bg')
    f.text(32, ty - 9, 'session_start.reason', 10.5, 650, True, cls='strongt', layer='label')
    items = [('switchSession', 'resume'), ('newSession', 'new'), ('fork', 'fork'), ('importFromJsonl', 'resume'), ('dispose', 'quit (shutdown)')]
    x = 32
    for m, r in items:
        w = f.chip(x, ty + 0, m + '()', 'coding', size=9.5, h=18)
        f.text(x + w + 6, ty + 13, '→ ' + r, 10, 500, True, cls='muted', layer='label')
        x += w + 6 + maxw('→ ' + r, 10, 500, True) + 22
    f.text(1088, ty - 9, ('启动与 /reload 的 reason 是 startup / reload', 'startup and /reload use reason startup / reload'), 10, 500, cls='faint', layer='label', anchor='end')
    return f

# ============================================================== ca_tools : built-in tools
def _tool_limit(name):
    m = re.search(r'^const DEFAULT_LIMIT = (\d+);', _src(f'core/tools/{name}.ts'), re.M)
    return int(m.group(1)) if m else None

@reg
def ca_tools():
    f = Fig('ca_tools', 1120, 660, ('8 个内置工具', 'The 8 built-in tools'))
    tr = _src('core/tools/truncate.ts')
    ML = int(re.search(r'DEFAULT_MAX_LINES = (\d+)', tr).group(1)); MB = eval(re.search(r'DEFAULT_MAX_BYTES = ([\d *]+);', tr).group(1))
    GL = int(re.search(r'GREP_MAX_LINE_LENGTH = (\d+)', tr).group(1))
    dflt = re.search(r'DEFAULT_TOOL_NAMES: readonly string\[\] = \[([^\]]+)\]', _src('core/settings-manager.ts')).group(1)
    dflt = re.findall(r'"([a-z]+)"', dflt)
    T_ = [('read', 'path · offset? · limit?', (f'文本截断到 {ML} 行 / {MB // 1024}KB', f'text capped at {ML} lines / {MB // 1024}KB'), ('图片作为附件发送', 'images sent as attachments'), 'file'),
          ('bash', 'command · timeout?', ('保留尾部输出，完整输出写临时文件', 'keeps the tail; full output to a temp file'), ('超时 / abort → 杀进程树', 'timeout / abort → kill process tree'), 'terminal'),
          ('edit', 'path · edits[{ oldText, newText }]', ('每个 oldText 唯一且不重叠', 'each oldText unique, non-overlapping'), ('精确匹配失败 → 模糊匹配 · 返回 diff', 'exact fails → fuzzy match · returns diff'), 'diff'),
          ('write', 'path · content', ('递归创建目录后整体覆盖', 'mkdir -p, then overwrite'), ('与 edit 共用按文件的变更队列', 'shares the per-file mutation queue'), 'file'),
          ('grep', 'pattern · path? · glob? …', (f'ripgrep · 默认 {_tool_limit("grep")} 条匹配', f'ripgrep · {_tool_limit("grep")} matches by default'), (f'遵守 .gitignore · 每行 ≤ {GL} 字符', f'respects .gitignore · lines ≤ {GL} chars'), 'filter'),
          ('find', 'pattern · path? · limit?', (f'fd · 默认 {_tool_limit("find")} 个结果', f'fd · {_tool_limit("find")} results by default'), ('遵守 .gitignore', 'respects .gitignore'), 'eye'),
          ('ls', 'path? · limit?', (f'默认 {_tool_limit("ls")} 个条目', f'{_tool_limit("ls")} entries by default'), ('含点文件 · 目录带 /', 'includes dotfiles · dirs end in /'), 'tree'),
          ('powershell', 'command · timeout?', ('Windows 上 bash 的替代', 'the Windows alternative to bash'), ('与 bash 共用 shell 执行器', 'shares the bash shell executor'), 'terminal')]
    CW, CH = 256, 92
    for i, (n, params, d1, d2, ic) in enumerate(T_):
        x = 24 + (i % 4) * (CW + 12); y = 88 + (i // 4) * (CH + 46)
        lay = 'coding' if n in dflt else 'infra' if n == 'powershell' else 'agent'
        f.node('t_' + n, x, y, CW, CH, lay, n, '`' + params, ic, sub2=d1, strong=n in dflt, ssize=9.8, tsize=13.5)
        f.text(x + 12, y + CH + 16, d2, 10, 450, cls='muted', layer='label')
    f.text(24, 72, ('默认启用（DEFAULT_TOOL_NAMES）：', 'ACTIVE BY DEFAULT (DEFAULT_TOOL_NAMES): ') , 10, 700, cls='faint', layer='label', ls='.04em')
    x = 24 + maxw(('默认启用（DEFAULT_TOOL_NAMES）：', 'ACTIVE BY DEFAULT (DEFAULT_TOOL_NAMES): '), 10, 700) + 10
    for d in dflt: x += f.chip(x, 58, d, 'coding', size=9.5, h=18, cls='solid') + 5
    f.text(1096, 72, ('只读集合：read · grep · find · ls', 'read-only set: read · grep · find · ls'), 10, 600, cls='faint', layer='label', anchor='end')
    # pipeline
    py = 390
    f.group(16, py, 1088, 196, 'coding', ('一个工具如何接入', 'How a tool is plugged in'), None, 'plug', title_mono=False, gid='pipe')
    P = [('createXToolDefinition(cwd, opts)', ('ToolDefinition：schema + execute', 'ToolDefinition: schema + execute'), 'coding'),
         ('wrapToolDefinition(def)', ('→ AgentTool（pi-agent-core）', '→ AgentTool (pi-agent-core)'), 'agent'),
         (('AgentSession 工具表', 'AgentSession tool table'), ('内置 + 扩展 registerTool()', 'built-in + extension registerTool()'), 'coding'),
         ('agent.state.tools', ('当前激活的子集', 'the active subset'), 'agent')]
    pw, gap = 236, 34
    for j, (t, s, lay) in enumerate(P):
        x = 36 + j * (pw + gap)
        f.node('pp%d' % j, x, py + 50, pw, 52, lay, t, s, None, tsize=11 if isinstance(t, str) else 12, ssize=9.8, mono=isinstance(t, str))
        if j: f.edge([(x - gap, py + 76), (x, py + 76)], 'pp%d' % (j - 1), 'pp%d' % j, 'main', 'coding')
    ops = [('ReadOperations', 'readFile · access · detectImageMimeType'), ('BashOperations', 'exec(command, cwd, { onData, signal, timeout })'),
           ('EditOperations · WriteOperations', 'readFile · writeFile · mkdir'), ('Grep / Find / LsOperations', ('可换成远程 / 沙箱实现', 'swap in remote / sandboxed backends'))]
    f.text(36, py + 128, ('可替换的 *Operations（默认 = 本地文件系统 / shell）', 'Swappable *Operations (default = local filesystem / shell)'), 10.5, 650, cls='strongt', layer='label')
    for j, (k, d) in enumerate(ops):
        x = 36 + (j % 2) * 530; y = py + 146 + (j // 2) * 22
        w = f.chip(x, y - 13, k, 'coding', size=9.5, h=18)
        f.text(x + w + 8, y, d, 10, 450, isinstance(d, str), cls='muted', layer='label')
    f.note(1096, 618, ('withFileMutationQueue(path)：同一文件（realpath）上的 edit / write 串行，不同文件仍可并行', 'withFileMutationQueue(path): edits / writes to the same file (by realpath) run serially; different files still run in parallel'), 10.5, anchor='end')
    f.legend(24, 644, [('layer:coding', ('默认工具', 'default tools')), ('layer:agent', ('可选工具', 'optional tools')), ('layer:infra', 'Windows'), ('main', ('装配顺序', 'assembly order'))])
    return f

# ============================================================== ca_jsonl : session file anatomy
@reg
def ca_jsonl():
    f = Fig('ca_jsonl', 1120, 684, ('会话文件：JSONL 的结构与读写', 'The session file: JSONL anatomy, write & read paths'))
    sm = (SRC / (S + 'core/session-manager.ts')).read_text()
    ver = int(re.search(r'CURRENT_SESSION_VERSION = (\d+)', sm).group(1))
    codebox(f, 24, 52, 520, [(0, '~/.pi/agent/sessions/', 'muted'), (1, '--home-me-proj--/', 'muted'), (2, '2026-10-07T09-12-33-123Z_<uuidv7>.jsonl', 'strongt')],
            title=('位置：每个 cwd 一个目录', 'LOCATION: one directory per cwd'), size=10.5)
    lines = [(0, f'{{"type":"session","version":{ver},"id":"…","cwd":"/home/me/proj"}}', 'strongt'),
             (0, '{"type":"model_change","id":"a1","parentId":null,…}', 'muted'),
             (0, '{"type":"thinking_level_change","id":"b2","parentId":"a1"}', 'muted'),
             (0, '{"type":"message","id":"c3","parentId":"b2","message":{role:"user"}}', 'muted'),
             (0, '{"type":"message","id":"d4","parentId":"c3",…assistant}', 'muted'),
             (0, '{"type":"compaction","id":"e5","firstKeptEntryId":"c3",…}', 'muted'),
             (0, '{"type":"message","id":"f6","parentId":"c3",…}  ← 分支', 'muted')]
    lines[-1] = (0, ('{"type":"message","id":"f6","parentId":"c3",…}  ← 分支', '{"type":"message","id":"f6","parentId":"c3",…}  ← branch'), 'muted')
    codebox(f, 24, 160, 520, lines, title=('内容：第 1 行是头，其余每行一个条目', 'CONTENT: line 1 is the header, one entry per line after'), size=9.6, lh=19)
    # entry types
    et = entry_types()
    grp = [(('对话', 'conversation'), ['message', 'custom_message'], 'coding'),
           (('状态', 'state'), ['model_change', 'thinking_level_change', 'session_info', 'label'], 'modes'),
           (('上下文改写', 'context rewrites'), ['compaction', 'branch_summary', 'context_edit'], 'ext'),
           (('记账', 'bookkeeping'), ['usage', 'custom'], 'infra')]
    assert sorted(sum((g[1] for g in grp), [])) == sorted(et), et
    f.group(568, 52, 536, 252, 'coding', ('条目类型', 'Entry types'), (f'{len(et)} 种 · 都有 id / parentId / timestamp', f'{len(et)} kinds · all carry id / parentId / timestamp'), 'list' if False else 'braces', title_mono=False, gid='et')
    yy = 100
    for gname, items, lay in grp:
        f.text(588, yy + 14, gname, 10.5, 650, cls='faint', layer='label')
        chiprow(f, 700, yy, [(t, lay) for t in items], size=10, h=21, gap=6)
        yy += 34
    f.text(588, yy + 18, ('CustomMessage / bashExecution 等宿主消息不直接作为 message 写入；', 'Host messages (custom, bashExecution) are not written as plain message entries;'), 10, 450, cls='muted', layer='label')
    f.text(588, yy + 36, ('压缩与分支摘要必须是顶层条目。', 'compaction and branch summaries must be top-level entries.'), 10, 450, cls='muted', layer='label')
    # write path
    wy = 376
    f.text(24, wy - 10, ('写入路径', 'WRITE PATH'), 10.5, 700, cls='faint', layer='label', ls='.08em')
    W_ = [('appendMessage() …', ('append*() 方法之一', 'one of the append*() methods'), 'coding'),
          ('_appendEntry(e)', ('入内存索引 · leafId = e.id', 'index in memory · leafId = e.id'), 'coding'),
          (('还没有对话？', 'no conversation yet?'), ('只有设置条目 → 不建文件', 'setup entries only → no file'), 'err'),
          (('首次 user / assistant', 'first user / assistant'), ('openSync("wx") 写出全部缓冲', 'openSync("wx") flushes the buffer'), 'coding'),
          ('appendFileSync()', ('之后每条追加一行', 'one line per entry afterwards'), 'coding')]
    ww, gap = 196, 27
    for j, (t, s, lay) in enumerate(W_):
        x = 24 + j * (ww + gap)
        f.node('w%d' % j, x, wy, ww, 54, lay, t, s, None, tsize=11 if isinstance(t, str) else 11.5, ssize=9.6, mono=isinstance(t, str), kind='dec' if j == 2 else 'card')
        if j: f.edge([(x - gap, wy + 27), (x, wy + 27)], 'w%d' % (j - 1), 'w%d' % j, 'main', 'coding')
    # read path
    ry = 496
    f.text(24, ry - 10, ('读取路径', 'READ PATH'), 10.5, 700, cls='faint', layer='label', ls='.08em')
    R_ = [('loadEntriesFromFile()', ('逐行解析，跳过坏行', 'line by line, skips bad lines'), 'ai'),
          (f'migrate → v{ver}', ('v1→v2 补 id · v2→v3 hookMessage→custom', 'v1→v2 ids · v2→v3 hookMessage→custom'), 'ai'),
          ('_rewriteFile()', ('迁移后整体重写', 'rewrite if migrated'), 'ai'),
          ('buildSessionProjection(leaf)', ('根→leaf · context_edit · 最新压缩', 'root→leaf · context_edit · newest compaction'), 'agent'),
          ('SessionContext', ('messages · model · thinkingLevel', 'messages · model · thinkingLevel'), 'agent')]
    rw = [170, 262, 132, 248, 212]
    x = 24
    for j, (t, s, lay) in enumerate(R_):
        f.node('r%d' % j, x, ry, rw[j], 54, lay, t, s, None, tsize=10.5, ssize=9.4, mono=True, strong=j == 3)
        if j: f.edge([(x - 12, ry + 27), (x, ry + 27)], 'r%d' % (j - 1), 'r%d' % j, 'main', 'agent')
        x += rw[j] + 12
    f.note(24, 592, ('分支不是复制：fork / navigateTree 只移动 leafId，或用 createBranchedSession() 把根到 leaf 的路径写进新文件。', 'Branching copies nothing: fork / navigateTree just moves leafId, or createBranchedSession() writes the root → leaf path into a new file.'), 10.5)
    f.note(24, 612, ('SessionManager.inMemory() 用于 --no-session、--help、测试：同一套 API，只是从不落盘。', 'SessionManager.inMemory() backs --no-session, --help and tests: the same API, never written to disk.'), 10.5)
    f.legend(24, 664, [('main', ('数据流', 'data flow')), ('layer:coding', ('写入', 'write')), ('layer:ai', ('加载与迁移', 'load & migrate')), ('layer:agent', ('投影成上下文', 'project into context'))])
    return f

# ============================================================== ca_extapi : the ExtensionAPI surface and the 41 events
def ext_interceptable():
    s = _src('core/extensions/types.ts')
    m = re.search(r'^export interface ExtensionAPI\b.*?^\}', s, re.M | re.S).group(0)
    return {mm.group(1) for mm in re.finditer(r'\bon\(\s*event: "([a-z_]+)",(.*?)\): \(\) => void', m, re.S)
            if 'Result' in mm.group(2) or 'ExtensionHandler' not in mm.group(2)}

@reg
def ca_extapi():
    f = Fig('ca_extapi', 1120, 740, ('扩展 API：能力面与 41 种事件', 'The extension API: capabilities and the 41 events'))
    meths = api_methods()
    G = [(('注册', 'register'), [m for m in meths if m.startswith('register')], 'ext'),
         (('注销', 'unregister'), [m for m in meths if m.startswith('unregister')], 'err'),
         (('行动', 'act'), [m for m in meths if m.startswith(('send', 'set', 'append', 'exec'))], 'coding'),
         (('读取', 'read'), [m for m in meths if m.startswith('get')], 'infra')]
    assert sorted(sum((g[1] for g in G), [])) == meths, set(meths) - set(sum((g[1] for g in G), []))
    f.group(16, 52, 420, 452, 'ext', 'pi: ExtensionAPI', (f'{len(meths) + 1} 个方法（含 on）', f'{len(meths) + 1} methods incl. on()'), 'plug', gid='api')
    f.text(36, 100, 'export default (pi) => { … }', 10.5, 600, True, cls='muted', layer='label')
    y = 122
    for gname, items, lay in G:
        f.text(36, y + 13, gname, 10, 700, cls='faint', layer='label', ls='.04em')
        x, yy = 112, y
        for it in items:
            w = maxw(it + '()', 9.5, 550, True) + 14
            if x + w > 424: x, yy = 112, yy + 25
            f.chip(x, yy, it + '()', lay, size=9.5, h=20)
            x += w + 5
        y = yy + 34
    # ctx
    cy = 520
    ctx = iface_members('ExtensionContext'); cmd = iface_members('ExtensionCommandContext'); ui = iface_members('ExtensionUIContext')
    f.group(16, cy, 420, 166, 'modes', ('处理器的第二个参数 ctx', 'ctx, every handler\'s 2nd argument'), None, 'braces', title_mono=False, gid='ctx')
    rowz = [('ExtensionContext', ctx, ['ui', 'cwd', 'sessionManager', 'model', 'signal', 'compact']),
            ('ExtensionCommandContext', cmd, ['newSession', 'fork', 'navigateTree', 'switchSession', 'reload']),
            ('ctx.ui', ui, ['select', 'confirm', 'input', 'notify', 'setWidget', 'custom'])]
    yy = cy + 52
    for nm, allm, show in rowz:
        assert all(s_ in allm for s_ in show), (nm, show)
        f.text(36, yy + 4, nm, 10, 650, True, cls='cf c-modes', layer='label')
        f.text(410, yy + 4, (f'{len(allm)} 个成员', f'{len(allm)} members'), 9.5, 500, cls='faint', layer='label', anchor='end')
        f.text(36, yy + 22, ' · '.join(show) + ' …', 9.8, 450, True, cls='muted', layer='label')
        yy += 40
    # events
    ev = ext_events(); icp = ext_interceptable()
    EG = [(('会话', 'session'), [e for e in ev if e.startswith('session_')] + ['project_trust', 'resources_discover', 'mcp_servers_change'], 'coding'),
          (('运行与轮次', 'run & turn'), ['input', 'before_agent_start', 'agent_start', 'turn_start', 'turn_end', 'agent_end', 'agent_before_settle', 'agent_settled', 'user_bash'], 'agent'),
          (('消息', 'messages'), ['message_start', 'message_update', 'message_end'], 'ai'),
          (('工具', 'tools'), ['tool_call', 'tool_execution_start', 'tool_execution_update', 'tool_execution_end', 'tool_result'], 'ext'),
          (('上下文与 provider', 'context & provider'), ['context', 'context_with_system', 'before_provider_request', 'before_provider_headers', 'after_provider_response', 'provider_stream_event', 'cache_warming_decision'], 'ai'),
          (('模型与界面', 'model & UI'), ['model_select', 'thinking_level_select', 'ui_prompt_start', 'ui_prompt_end'], 'modes')]
    allg = sum((g[1] for g in EG), [])
    assert sorted(allg) == ev and len(allg) == len(ev), (set(ev) - set(allg), set(allg) - set(ev))
    f.group(456, 52, 648, 634, 'agent', 'pi.on(event, handler)', (f'{len(ev)} 种事件 · {len(icp)} 种可返回结果', f'{len(ev)} events · {len(icp)} may return a result'), 'stream', gid='ev')
    y = 100
    for gname, items, lay in EG:
        f.text(476, y + 13, gname, 10, 700, cls='faint', layer='label', ls='.04em')
        x, yy = 600, y
        for it in items:
            w = maxw(it, 9.5, 550, True) + 14
            if x + w > 1090: x, yy = 600, yy + 25
            f.chip(x, yy, it, lay, size=9.5, h=20, cls='solid' if it in icp else '')
            x += w + 5
        y = yy + 36
    # interception examples
    ex = [('input', ('→ { action: "transform" | "handled" }', '→ { action: "transform" | "handled" }')),
          ('tool_call', ('→ { block: true, reason }', '→ { block: true, reason }')),
          ('tool_result', ('→ 改写 content / details', '→ rewrite content / details')),
          ('context', ('→ { messages } 替换本次上下文', '→ { messages } replaces this context')),
          ('session_before_*', ('→ { cancel: true }', '→ { cancel: true }')),
          ('turn_end', ('→ 边界条目：在轮次之间写入会话', '→ boundary entries written between turns'))]
    y = max(y, 470) + 4
    f.text(476, y, ('返回值能做什么（实心 = 可返回结果）', 'What a returned result can do (solid = may return a result)'), 10.5, 650, cls='strongt', layer='label')
    for i, (k, d) in enumerate(ex):
        xx = 476 + (i % 2) * 316; yy = y + 26 + (i // 2) * 26
        w = f.chip(xx, yy - 14, k, 'agent', size=9.5, h=19, cls='solid')
        f.text(xx + w + 6, yy, d, 9.8, 450, isinstance(d, str), cls='muted', layer='label')
    f.legend(24, 718, [('layer:ext', ('注册能力', 'register')), ('layer:coding', ('行动 / 会话', 'act / session')), ('layer:agent', ('运行', 'run')), ('layer:ai', ('消息 · provider', 'messages · provider')), ('layer:modes', 'ctx · UI')])
    return f

# ============================================================== ca_rpc : JSONL RPC protocol
@reg
def ca_rpc():
    groups = rpc_commands()
    n = sum(len(c) for _, c in groups)
    f = Fig('ca_rpc', 1120, 700, (f'RPC 模式：stdin/stdout 上的 JSONL 协议（{n} 种命令）', f'RPC mode: a JSONL protocol over stdin/stdout ({n} commands)'))
    # actors
    f.node('cl', 24, 60, 220, 64, 'infra', ('宿主进程', 'host process'), ('IDE · 编排器 · RpcClient', 'IDE · orchestrator · RpcClient'), 'user', mono=False)
    f.node('pi', 24, 330, 220, 64, 'modes', 'pi --mode rpc', ('或 rpc-entry.ts', 'or rpc-entry.ts'), 'terminal')
    f.node('rm', 24, 430, 220, 64, 'modes', 'runRpcMode(runtime)', ('handleCommand(cmd) · switch', 'handleCommand(cmd) · switch'), 'cpu', ssize=10)
    f.node('as', 24, 530, 220, 64, 'coding', 'AgentSessionRuntime', ('session.prompt() · fork() …', 'session.prompt() · fork() …'), 'loop', ssize=10)
    E = f.edge
    E([(134, 394), (134, 430)], 'pi', 'rm', 'dep')
    E([(134, 494), (134, 530)], 'rm', 'as', 'main', 'coding')
    # pipes
    lanes = [('stdin', ('命令：{ id?, type, … }', 'commands: { id?, type, … }'), 160, 'main', 'accent'),
             ('stdout', ('响应：{ type:"response", id, success, data | error }', 'responses: { type:"response", id, success, data | error }'), 196, 'event', 'coding'),
             ('stdout', ('事件：AgentSessionEvent → toJsonEvent()', 'events: AgentSessionEvent → toJsonEvent()'), 232, 'event', 'agent'),
             ('stdout', ('扩展 UI 请求：extension_ui_request { id, method }', 'UI request: extension_ui_request { id, method }'), 268, 'event', 'ext'),
             ('stdin', ('回答：extension_ui_response { id, value | … }', 'answer: extension_ui_response { id, value | … }'), 304, 'main', 'ext')]
    xs = [64, 100, 136, 172, 208]
    for i, (pipe, lab, y, kind, lay) in enumerate(lanes):
        x = xs[i]
        if pipe == 'stdin':
            E([(x, 124), (x, 330)], 'cl', 'pi', kind, lay)
        else:
            E([(x, 330), (x, 124)], 'pi', 'cl', kind, lay)
        f.step(i + 1, x, y, lay, r=8)
        f.step(i + 1, 270, y, lay, r=8)
        f.chip(284, y - 10, pipe, 'modes' if pipe == 'stdin' else 'infra', size=9.5, h=20)
        f.text(336, y + 4, lab, 10, 450, False, cls='strongt', layer='label')
    f.text(24, 640, ('jsonl.ts：只按 \\n 切分（JSON 字符串里可以有 U+2028/2029），去掉行尾 \\r；不用 readline。', 'jsonl.ts: split on \\n only (JSON strings may contain U+2028/2029), strip a trailing \\r; no readline.'), 10.5, 450, cls='faint', layer='label')
    f.text(24, 660, ('事件输出受 stdout 背压控制：Agent 监听器会等待 drain。', 'Event output honours stdout backpressure: an Agent listener awaits drain.'), 10.5, 450, cls='faint', layer='label')
    # catalogue
    gh_ = 0
    f.group(640, 52, 464, 0, 'modes', 'RpcCommand', (f'{n} 种 · 按 rpc-types.ts 中的分组', f'{n} types · grouped as in rpc-types.ts'), 'list' if False else 'braces', gid='cat')
    y = 100
    lay = {'Prompting': 'coding', 'State': 'infra', 'Model': 'ai', 'Thinking': 'ai', 'Queue modes': 'agent', 'Compaction': 'coding', 'Retry': 'err', 'Bash': 'ext', 'Session': 'coding', 'Messages': 'infra', 'Commands': 'ext'}
    for g, cmds in groups:
        f.text(660, y + 13, g, 10, 700, cls='faint', layer='label', ls='.03em')
        x, yy = 760, y
        for c in cmds:
            w = maxw(c, 9.5, 550, True) + 14
            if x + w > 1092: x, yy = 760, yy + 24
            f.chip(x, yy, c, lay.get(g, 'infra'), size=9.5, h=20, cls='solid' if c == 'prompt' else '')
            x += w + 5
        y = yy + 30
    for i_, g_ in enumerate(f.L['grp']):
        if 'data-id="cat"' in g_: f.L['grp'][i_] = g_.replace('height="0"', f'height="{y - 52 + 2}"', 1)
    f.nodes['cat'] = (640, 52, 464, y - 50)
    f.note(1096, 632, ('prompt 先完成预检再回响应（disposition），之后的一切都以事件到达', 'prompt replies after preflight (disposition); everything after arrives as events'), 10.5, anchor='end')
    f.note(1096, 652, ('select / confirm / input / editor 等待响应；notify / setStatus / setWidget / setTitle 只发不收', 'select / confirm / input / editor await a response; notify / setStatus / setWidget / setTitle are fire-and-forget'), 10.5, anchor='end')
    f.legend(24, 684, [('main', ('stdin → pi', 'stdin → pi')), ('event', ('pi → stdout', 'pi → stdout')), ('layer:coding', ('会话', 'session')), ('layer:ai', ('模型', 'model')), ('layer:ext', ('扩展 / bash', 'extensions / bash'))])
    return f

# ============================================================== ca_config : settings, resources, system prompt
@reg
def ca_config():
    f = Fig('ca_config', 1120, 650, ('配置与资源：settings 合并、ResourceLoader.reload()、system prompt 分段', 'Configuration: settings merge, ResourceLoader.reload(), system prompt sections'))
    E = f.edge
    # --- row 1 : settings
    f.group(16, 52, 1088, 132, 'infra', 'SettingsManager', ('两层 JSON，项目层受信任门控', 'two JSON layers; the project layer is trust-gated'), 'gear', gid='set')
    f.node('g', 36, 100, 236, 60, 'infra', ('全局', 'global'), '`~/.pi/agent/settings.json', 'globe', mono=False, ssize=10)
    f.node('t', 300, 100, 200, 60, 'err', 'ProjectTrustStore', ('门控项目层', 'gates the project layer'), 'shield', ssize=10)
    f.node('p', 528, 100, 220, 60, 'infra', ('项目', 'project'), '`<cwd>/.pi/settings.json', 'file', mono=False, ssize=10)
    f.node('m', 800, 100, 284, 60, 'infra', 'deepMergeSettings()', ('项目覆盖全局 · 对象逐键合并', 'project wins · objects merge per key'), 'layers', ssize=10)
    E([(500, 130), (528, 130)], 't', 'p', 'dep')
    E([(748, 130), (800, 130)], 'p', 'm', 'main', 'infra')
    E([(154, 160), (154, 172), (942, 172), (942, 160)], 'g', 'm', 'main', 'infra')
    # --- row 2 : reload pipeline
    f.group(16, 204, 1088, 132, 'coding', 'DefaultResourceLoader.reload()', ('启动和 /reload 时运行', 'runs at startup and on /reload'), 'loop', gid='rl')
    steps = [('resolveProjectTrust', ('先加载处理 project_trust 的扩展', 'project_trust extensions first')),
             ('settings.reload()', ('按信任状态重读', 're-read for trust state')),
             ('resolve()', ('packageManager', 'packageManager')),
             ('CLI paths', ('-e · --skill · --theme …', '-e · --skill · --theme …')),
             ('loadFinalExtensionSet', ('jiti 加载 · 工厂函数', 'jiti import · factories')),
             (('其余资源', 'other resources'), ('skills · prompts · themes', 'skills · prompts · themes'))]
    W, G_, x = 166, 14, 32
    for i, (t, sub) in enumerate(steps):
        f.node(f'r{i}', x, 254, W, 62, 'coding', t, sub, None, tsize=11, ssize=9.5)
        f.step(i + 1, x + 2, 256, 'coding', r=8, onnode=True)
        if i:
            E([(x - G_, 285), (x, 285)], f'r{i - 1}', f'r{i}', 'main', 'coding')
        x += W + G_
    # --- row 3 left : dirs & context files
    f.group(16, 356, 520, 252, 'ext', ('资源从哪里来', 'Where resources come from'), None, 'file', title_mono=False, gid='dirs')
    codebox(f, 32, 400, 488, [
        (0, '~/.pi/agent/', 'strongt'), (1, 'extensions/  skills/  prompts/  themes/', 'muted'),
        (1, 'settings.json  auth.json  models.json', 'muted'), (1, 'SYSTEM.md  APPEND_SYSTEM.md  AGENTS.md', 'muted'),
        (0, ('<cwd>/.pi/      ← 仅限受信任项目', '<cwd>/.pi/      ← trusted projects only'), 'strongt'), (1, 'extensions/  skills/  prompts/  themes/', 'muted'),
        (1, 'settings.json  SYSTEM.md  APPEND_SYSTEM.md', 'muted')], None, 10, 17)
    f.text(32, 556, ('上下文文件：全局 agentDir + cwd 及每一级祖先目录，每处取第一个存在的', 'Context files: global agentDir + cwd and every ancestor; first match per directory'), 9.8, 450, cls='muted', layer='label')
    x = 32
    for nm in ['AGENTS.override.md', 'AGENTS.md', 'AGENTS.MD', 'CLAUDE.md', 'CLAUDE.MD']:
        x += f.chip(x, 568, nm, 'ext', size=9.5, h=20) + 6
    f.text(32, 600, ('SYSTEM.md / APPEND_SYSTEM.md：项目优先于全局', 'SYSTEM.md / APPEND_SYSTEM.md: project beats global'), 9.8, 450, cls='faint', layer='label')
    # --- row 3 right : system prompt sections
    f.group(556, 356, 548, 252, 'ai', 'buildSystemPromptSections()', ('有序、可单独替换的分段', 'ordered, independently replaceable'), 'stack', gid='sp')
    secs = [('preamble', ('SYSTEM.md 存在时整段替换，并去掉 tools/rules/docs', 'SYSTEM.md replaces it and drops tools/rules/docs')),
            ('<tools>', ('可见工具的一行说明', 'one-line snippet per visible tool')),
            ('<rules>', ('工具准则 + 扩展 promptGuidelines', 'tool guidelines + extension promptGuidelines')),
            ('<docs>', ('pi 自身文档的位置', 'where pi\'s own docs live')),
            ('<addendum>', ('APPEND_SYSTEM.md', 'APPEND_SYSTEM.md')),
            ('<project_context>', ('AGENTS.md / CLAUDE.md …', 'AGENTS.md / CLAUDE.md …')),
            ('<skills>', ('技能清单（需 read 或 bash）', 'skill index (needs read or bash)')),
            ('<cwd>', ('工作目录', 'working directory')),
            ('<custom…>', ('扩展通过 sections 追加', 'extensions add via sections'))]
    for i, (k, d) in enumerate(secs):
        yy = 402 + i * 22
        f.chip(574, yy - 13, k, 'ai', size=9.5, h=18, cls='solid' if i == 0 else '')
        f.text(712, yy, d, 9.8, 450, isinstance(d, str), cls='muted', layer='label')
    f.legend(24, 632, [('layer:infra', 'settings'), ('layer:err', ('信任门', 'trust gate')), ('layer:coding', ('加载流程', 'load pipeline')), ('layer:ext', ('资源', 'resources')), ('layer:ai', 'system prompt')])
    return f
