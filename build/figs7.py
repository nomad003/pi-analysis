"""pi-mcp deep-dive diagrams (mcp_*). Facts read from /workspace/pi-src/packages/mcp at build time."""
import re, json
from svgkit import Fig, maxw, pair
from figs import reg
from figkit import SRC, uml, codebox, bar, dot, hline, vline, chiprow, lines_of

M = 'packages/mcp/src/'
CAM = 'packages/coding-agent/src/'
def _src(p): return (SRC / (M + p)).read_text()
def _ca(p): return (SRC / (CAM + p)).read_text()
def loc(p): return lines_of(M + p)
def has(p, *needles):
    s = _src(p)
    for n in needles: assert n in s, (p, n)
def has_ca(p, *needles):
    s = _ca(p)
    for n in needles: assert n in s, (p, n)
def total_loc(base=M):
    return sum(lines_of(str(x.relative_to(SRC))) for x in (SRC / base).rglob('*.ts') if not x.name.endswith(('.test.ts', '.d.ts')))
def const(p, name):
    m = re.search(r'\b' + name + r'\s*=\s*([^;]+);', _src(p))
    return m.group(1).strip()
def num(p, name):
    v = const(p, name).replace('_', '')
    if '*' in v:
        a, b, *c = [int(x.strip()) for x in v.split('*')]
        r = a * b
        for x in c: r *= x
        return r
    return int(v)
def versions():
    s = _src('protocol/types.ts')
    latest = re.search(r'LATEST_PROTOCOL_VERSION = "([^"]+)"', s).group(1)
    rest = re.findall(r'"(\d{4}-\d\d-\d\d)"', re.search(r'SUPPORTED_PROTOCOL_VERSIONS = \[(.*?)\]', s).group(1))
    return [latest] + rest
def exports():
    j = json.loads((SRC / 'packages/mcp/package.json').read_text())
    return [k for k in j['exports'] if k != './package.json'], j.get('dependencies', {})
def iface(name, p):
    m = re.search(r'^export interface ' + name + r'\b[^{]*\{(.*?)^\}', _src(p), re.M | re.S)
    out = []
    for n in re.findall(r'^\t(?:readonly )?([a-zA-Z_]+)\??[(:<]', m.group(1), re.M):
        if n not in out: out.append(n)
    return out
def rpc_codes():
    blk = re.search(r'JSON_RPC_ERROR_CODES = \{(.*?)\}', _src('protocol/jsonrpc.ts'), re.S).group(1)
    return re.findall(r'(\w+): (-\d+)', blk)
def MiB(n): return f'{n // (1024 * 1024)} MiB' if n % (1024 * 1024) == 0 else f'{n // 1024} KiB'

# ============================================================== mcp_arch
@reg
def mcp_arch():
    tot = total_loc()
    ex, deps = exports()
    f = Fig('mcp_arch', 1120, 600, (f'pi-mcp 模块结构（{tot:,} 行 TypeScript）', f'pi-mcp modules ({tot:,} lines of TypeScript)'))
    COLS = [(('客户端与协议', 'Client & protocol'), 'ext', 'hub', [
                ('client.ts', ('McpClient：握手 · 请求 · 分页', 'McpClient: handshake · requests · paging')),
                ('protocol/jsonrpc.ts', ('JSON-RPC 2.0 消息 · 错误', 'JSON-RPC 2.0 messages · errors')),
                ('protocol/types.ts', ('协议版本 · 能力 · Tool', 'versions · capabilities · Tool')),
                ('protocol/content.ts', ('内容块 · toLlmContent()', 'content blocks · toLlmContent()')),
                ('auth-provider.ts', ('AuthProvider 接口', 'the AuthProvider interface')),
                ('index.ts', ('包入口 "."', 'package entry "."'))]),
            (('传输', 'Transports'), 'infra', 'plug', [
                ('transports/transport.ts', ('McpTransport · TransportEvents', 'McpTransport · TransportEvents')),
                ('transports/stdio.ts', ('子进程 · 按行 JSON', 'child process · line-delimited JSON')),
                ('transports/streamable-http.ts', ('POST + SSE · 会话 · 重连', 'POST + SSE · sessions · reconnect')),
                ('transports/in-memory.ts', ('测试用的一对传输', 'a linked pair for tests')),
                ('testing/index.ts', ('入口 "./testing"', 'entry "./testing"'))]),
            (('OAuth（入口 ./oauth）', 'OAuth (entry ./oauth)'), 'agent', 'key', [
                ('oauth/flow.ts', ('authorizeMcp · PKCE · 刷新', 'authorizeMcp · PKCE · refresh')),
                ('oauth/discovery.ts', ('.well-known 元数据发现', '.well-known metadata discovery')),
                ('oauth/types.ts', ('元数据 · 令牌 · 客户端类型', 'metadata · token · client types')),
                ('oauth/provider.ts', ('McpOAuthProvider · 状态存储', 'McpOAuthProvider · state store')),
                ('oauth/callback.ts', ('本地回调服务器', 'loopback callback server')),
                ('oauth/errors.ts', ('OAuthError 等 5 个类', 'OAuthError and 4 more'))])]
    W, X0 = 352, 16
    for ci, (title, lay, ic, rows) in enumerate(COLS):
        x = X0 + ci * (W + 16)
        f.group(x, 52, W, 384, lay, title, None, ic, title_mono=False, gid=f'g{ci}')
        for ri, (p, role) in enumerate(rows):
            f.node(f'n{ci}{ri}', x + 12, 98 + ri * 54, W - 24, 46, lay, p, role, None, tsize=11.5, ssize=10, tag=f'{loc(p):,}', strong=(p == 'client.ts'))
    assert ex == ['.', './oauth', './testing'], ex
    f.group(16, 452, 1088, 104, 'ext', ('导入路径、依赖与使用者', 'Import paths, dependencies and users'), None, 'box', title_mono=False, gid='bot')
    x = 32
    for e in ex:
        x += f.chip(x, 500, '@earendil-works/pi-mcp' + e[1:], 'ext', size=10.5, h=22) + 8
    dep = ' · '.join(f'{k} {v}' for k, v in deps.items())
    x += 18
    f.text(x, 515, ('运行时依赖：', 'runtime dep:'), 10.5, 600, cls='faint', layer='label')
    x += maxw(('运行时依赖：', 'runtime dep:'), 10.5, 600) + 6
    x += f.chip(x, 500, dep, 'infra', size=10.5, h=22) + 18
    n = total_loc(CAM + 'extensions/mcp')
    f.chip(x, 500, f'coding-agent · extensions/mcp ({n:,})', 'coding', size=10.5, h=22)
    f.text(32, 542, ('不依赖任何 pi 包；pi 内唯一的使用者是 coding-agent 的内置 MCP 扩展。', 'Depends on no pi package; inside pi its only user is coding-agent\'s built-in MCP extension.'), 10, 450, cls='muted', layer='label')
    f.legend(24, 582, [('layer:ext', ('客户端 · 协议', 'client · protocol')), ('layer:infra', ('传输', 'transports')), ('layer:agent', 'OAuth')])
    f.note(1096, 582, ('标签 = 行数', 'tag = lines of code'), 10.5, anchor='end')
    return f

# ============================================================== mcp_lifecycle
@reg
def mcp_lifecycle():
    has('client.ts', 'type ClientState = "idle" | "connecting" | "connected" | "closed";', 'await transport.start();', '"notifications/initialized"',
        'transport.setProtocolVersion?.(result.protocolVersion);', 'await this.close().catch(() => {});', 'capabilities.roots = {};')
    has('transports/streamable-http.ts', 'message.method === "notifications/initialized") this.startGetStream();', 'headers.set("MCP-Protocol-Version"')
    V = versions()
    f = Fig('mcp_lifecycle', 1120, 640, ('连接：状态机与 initialize 握手', 'Connecting: the state machine and the initialize handshake'))
    E = f.edge
    # state machine
    f.group(16, 52, 1088, 112, 'ext', ('McpClient 状态', 'McpClient state'), ('只能 connect 一次；closed 不可逆', 'connect() once; closed is final'), 'loop', title_mono=False, gid='sm')
    S = [('idle', None), ('connecting', None), ('connected', None), ('closed', None)]
    xs = [40, 300, 600, 900]
    for i, (s, _) in enumerate(S):
        f.node(f's{i}', xs[i], 100, 180, 40, 'err' if s == 'closed' else 'ext', s, None, None, kind='pill', align='center', strong=(s == 'connected'))
    E([(220, 120), (300, 120)], 's0', 's1', 'main', 'ext', label='connect()', lpos=(260, 108))
    E([(480, 120), (600, 120)], 's1', 's2', 'main', 'ext', label=('握手完成', 'handshake done'), lpos=(540, 108), lmono=False, lsize=9.5)
    E([(780, 120), (900, 120)], 's2', 's3', 'main', 'err', label='close()', lpos=(840, 108))
    E([(390, 140), (390, 154), (990, 154), (990, 140)], 's1', 's3', 'err', label=('任一步失败 → close()', 'any step fails → close()'), lpos=(690, 154), lmono=False, lsize=9.5, r=6)
    # sequence
    f.group(16, 184, 700, 400, 'infra', ('握手时序（client.connect）', 'Handshake sequence (client.connect)'), None, 'stream', title_mono=False, gid='seq')
    LX = {'c': 110, 't': 360, 's': 610}
    for k, (t, s) in {'c': ('McpClient', None), 't': ('McpTransport', None), 's': (('MCP 服务器', 'MCP server'), None)}.items():
        f.node('h' + k, LX[k] - 80, 226, 160, 32, 'ext' if k == 'c' else 'infra' if k == 't' else 'coding', t, None, None, kind='pill', align='center', tsize=11.5, mono=isinstance(t, str))
        vline(f, LX[k], 258, 570)
    msgs = [('c', 't', '1', 'transport.start()', ('stdio：启动子进程 · http：无操作', 'stdio: spawn the process · http: no-op')),
            ('c', 's', '2', 'initialize', (f'protocolVersion "{V[0]}" · capabilities · clientInfo', f'protocolVersion "{V[0]}" · capabilities · clientInfo')),
            ('s', 'c', '3', 'InitializeResult', ('protocolVersion · capabilities · serverInfo · instructions', 'protocolVersion · capabilities · serverInfo · instructions')),
            ('c', 'c', '4', None, (f'校验：版本必须是支持的 {len(V)} 个之一', f'check: the version must be one of the {len(V)} supported')),
            ('c', 't', '5', 'setProtocolVersion(v)', ('http：之后每个请求带 MCP-Protocol-Version', 'http: every later request carries MCP-Protocol-Version')),
            ('c', 's', '6', 'notifications/initialized', ('http：此后才打开 GET 事件流', 'http: only now is the GET stream opened'))]
    y = 278
    for a, b, n, lab, sub in msgs:
        if a == b:
            f.step(n, LX[a] - 22, y + 4, 'ext', r=8)
            f.text(LX[a] + 12, y + 8, sub, 10, 450, cls='muted', layer='label')
            y += 40; continue
        x1, x2 = LX[a], LX[b]
        E([(x1, y + 10), (x2, y + 10)], None, None, 'main' if a == 'c' else 'event', 'ext' if a == 'c' else 'coding', r=0)
        f.step(n, (LX['c'] - 22) if a == 'c' else (LX['c'] - 22), y + 4, 'ext', r=8)
        lx = min(x1, x2) + 12
        f.text(lx, y, lab, 10.5, 600, True, cls='strongt', layer='label')
        f.text(lx, y + 27, sub, 9.5, 450, cls='muted', layer='label')
        y += 50
    f.text(32, 574, ('initialize 不可取消；roots 选项存在时 capabilities 自动加上 roots: {}。', 'initialize cannot be cancelled; with a roots option, capabilities gains roots: {} automatically.'), 9.8, 450, cls='faint', layer='label')
    # capabilities
    h1 = uml(f, 'cc', 736, 184, 368, 'ext', 'ClientCapabilities', '«client»', [['+' + m for m in iface('ClientCapabilities', 'protocol/types.ts')]])
    h2 = uml(f, 'scap', 736, 184 + h1 + 16, 368, 'coding', 'ServerCapabilities', '«server»', [['+' + m for m in iface('ServerCapabilities', 'protocol/types.ts')]])
    yv = 184 + h1 + 16 + h2 + 18
    f.text(736, yv + 12, ('支持的协议版本', 'SUPPORTED VERSIONS'), 10, 700, cls='faint', layer='label', ls='.06em')
    x = 736
    for i, v in enumerate(V):
        x += f.chip(x, yv + 22, v, 'ext', size=10, h=20, cls='solid' if i == 0 else '') + 6
    f.text(736, yv + 64, ('第一个 = LATEST_PROTOCOL_VERSION，默认发送它', 'the first = LATEST_PROTOCOL_VERSION, sent by default'), 9.8, 450, cls='muted', layer='label')
    f.legend(24, 618, [('layer:ext', ('实线：客户端 → 服务器', 'solid: client → server')), ('layer:coding', ('虚线：服务器 → 客户端', 'dashed: server → client')), ('err', ('失败', 'failure'))])
    return f

# ============================================================== mcp_requests
@reg
def mcp_requests():
    has('client.ts', 'const id = this.nextRequestId++;', 'const progressToken = options.onProgress ? id : undefined;', 'this.armTimeout(requestId, entry);',
        'cancellable: method !== "initialize"', 'method: "notifications/cancelled"', 'this.requestHandlers.set("ping", () => ({}));', '"roots/list"',
        'JSON_RPC_ERROR_CODES.methodNotFound', 'result: result ?? {}', 'returned duplicate cursor', 'this.incoming.get(params.requestId)?.abort(params.reason);')
    to = num('client.ts', 'DEFAULT_REQUEST_TIMEOUT_MS'); mp = num('client.ts', 'MAX_LIST_PAGES')
    f = Fig('mcp_requests', 1120, 660, ('请求簿记：超时、进度、取消与分页', 'Request bookkeeping: timeouts, progress, cancellation and paging'))
    E = f.edge
    f.group(16, 52, 680, 414, 'ext', ('客户端发出的请求', 'Requests the client sends'), ('client.request(method, params, opts)', 'client.request(method, params, opts)'), 'msg', title_mono=False, gid='out')
    ST = [('id = nextRequestId++', ('递增整数', 'an increasing integer')),
          ('_meta.progressToken = id', ('仅当传了 onProgress', 'only with onProgress')),
          ('pending.set(id, entry)', ('resolve · reject · timer · signal', 'resolve · reject · timer · signal')),
          (f'armTimeout({to:,} ms)', ('默认值，可按请求覆盖', 'default; per-request override')),
          ('transport.send(message)', ('发送失败 → 直接 reject', 'send fails → reject at once'))]
    for i, (t, s) in enumerate(ST):
        y = 98 + i * 58
        f.node(f'r{i}', 32, y, 290, 46, 'ext', t, s, None, tsize=11, ssize=9.5, strong=(i == 2))
        if i: E([(177, y - 12), (177, y)], f'r{i-1}', f'r{i}', 'main', 'ext')
    OUT = [('ok', 'event', 'coding', ('响应到达', 'response arrives'), ('result → resolve · error → McpError(code)', 'result → resolve · error → McpError(code)')),
           ('pr', 'event', 'ext', 'notifications/progress', ('重新计时 + onProgress(…)', 're-arm the timeout + onProgress(…)')),
           ('tm', 'err', 'err', ('超时', 'timeout'), ('McpTimeoutError + notifications/cancelled', 'McpTimeoutError + notifications/cancelled')),
           ('ab', 'err', 'err', ('signal 中止', 'signal aborted'), ('McpAbortError + notifications/cancelled', 'McpAbortError + notifications/cancelled')),
           ('cl', 'err', 'err', ('传输关闭 / close()', 'transport closed / close()'), ('所有 pending → McpConnectionClosedError', 'all pending → McpConnectionClosedError'))]
    for i, (k, kind, lay, t, s) in enumerate(OUT):
        y = 98 + i * 58
        f.node(k, 378, y, 302, 46, lay, t, s, None, tsize=11, ssize=9.5, mono=isinstance(t, str))
    E([(322, 237), (346, 237), (346, 121), (378, 121)], 'r2', 'ok', 'event', 'coding', r=6)
    for i, (k, kind, lay, *_ ) in enumerate(OUT[1:], 1):
        y = 98 + i * 58 + 23
        E([(346, 237 if i == 2 else y), (378, y)] if i == 2 else [(346, 237), (346, y), (378, y)], 'r2', k, kind, lay if lay != 'err' else None, r=6)
    f.text(32, 400, ('initialize 例外：中止或超时只 reject，不发 notifications/cancelled（规范禁止取消 initialize）。', 'Exception: initialize is rejected on abort/timeout but never cancelled — the spec forbids it.'), 9.8, 450, cls='muted', layer='label')
    f.text(32, 420, ('每条进度通知都把超时重新计时，长任务只要持续报进度就不会超时。', 'Every progress notification re-arms the timeout, so long tasks that keep reporting never time out.'), 9.8, 450, cls='muted', layer='label')
    f.text(32, 440, ('未知 id 的响应只报 onError，不影响其他请求。', 'A response with an unknown id only goes to onError; other requests are unaffected.'), 9.8, 450, cls='muted', layer='label')
    # incoming
    f.group(716, 52, 388, 414, 'coding', ('服务器发来的请求', 'Requests from the server'), None, 'inbox', title_mono=False, gid='in')
    f.node('hm', 732, 98, 356, 46, 'coding', 'requestHandlers.get(method)', ('内置：ping → {} · roots/list（配置了 roots 时）', 'built in: ping → {} · roots/list (when roots are set)'), None, tsize=11, ssize=9.5)
    f.node('nf', 904, 168, 184, 44, 'err', ('没有处理器', 'no handler'), f'`{dict(rpc_codes())["methodNotFound"]} Method not found', None, tsize=10.5, ssize=9.5, mono=False)
    f.node('hx', 732, 236, 356, 46, 'coding', 'handler(params, { signal })', ('incoming.set(id, AbortController)', 'incoming.set(id, AbortController)'), None, tsize=11, ssize=9.5)
    f.node('hr', 732, 306, 356, 46, 'coding', ('回复', 'reply'), ('result ?? {} · McpError 原样 · 其他 → -32603', 'result ?? {} · McpError as is · other → -32603'), None, tsize=11, ssize=9.5, mono=False)
    f.node('hc', 732, 376, 356, 46, 'err', 'notifications/cancelled', ('{ requestId } → 中止该处理器的 signal', '{ requestId } → abort that handler\'s signal'), None, tsize=11, ssize=9.5)
    E([(996, 144), (996, 168)], 'hm', 'nf', 'err', r=6)
    E([(800, 144), (800, 236)], 'hm', 'hx', 'main', 'coding')
    E([(800, 282), (800, 306)], 'hx', 'hr', 'main', 'coding')
    E([(1088, 399), (1096, 399), (1096, 259), (1088, 259)], 'hc', 'hx', 'err', r=4)
    f.text(732, 446, ('setRequestHandler(method, fn) 可增加或替换处理器。', 'setRequestHandler(method, fn) adds or replaces a handler.'), 9.8, 450, cls='muted', layer='label')
    # paging
    f.group(16, 486, 1088, 128, 'infra', ('分页：listAll()', 'Paging: listAll()'), ('listTools · listResources · listResourceTemplates', 'listTools · listResources · listResourceTemplates'), 'layers', title_mono=False, gid='pg')
    P = [('request(method, { cursor })', ('第一页不带 cursor', 'first page without cursor')), ('items.push(...page)', ('tools / resources / resourceTemplates', 'tools / resources / resourceTemplates')),
         ('nextCursor?', ('缺失、null 或 "" → 结束', 'missing, null or "" → done')), (('重复 cursor → 抛错', 'duplicate cursor → throw'), (f'最多 {mp:,} 页', f'at most {mp:,} pages'))]
    x = 32
    for i, (t, s) in enumerate(P):
        f.node(f'p{i}', x, 534, 248, 46, 'err' if i == 3 else 'infra', t, s, None, tsize=11, ssize=9.5, mono=isinstance(t, str))
        if i: E([(x - 22, 557), (x, 557)], f'p{i-1}', f'p{i}', 'main', 'infra')
        x += 270
    f.text(32, 600, ('listResourcesPage(cursor) 等单页方法留给需要自己控制分页的调用方。', 'Single-page methods such as listResourcesPage(cursor) are there for callers that page themselves.'), 9.5, 450, cls='faint', layer='label')
    f.legend(24, 640, [('main', ('流程', 'flow')), ('event', ('收到消息', 'message received')), ('err', ('失败 / 取消', 'failure / cancel'))])
    return f

# ============================================================== mcp_stdio
@reg
def mcp_stdio():
    has('transports/stdio.ts', 'crossSpawn(this.options.command', 'detached: USE_PROCESS_GROUPS', 'process.kill(-pid, signal);', '`${JSON.stringify(message)}\\n`',
        'this.stdoutBuffer.indexOf(0x0a)', 'replace(/\\r$/, "")', 'spawn("taskkill", ["/pid", String(pid), "/T", "/F"]', 'process.once("exit"', 'child.stdin?.end();',
        'this.options.inheritEnv === false ? { ...this.options.env } : { ...process.env, ...this.options.env }')
    has('transports/transport.ts', 'DEFAULT_MAX_MESSAGE_BYTES = 16 * 1024 * 1024')
    grace = num('transports/stdio.ts', 'STDIN_CLOSE_GRACE_MS'); ct = num('transports/stdio.ts', 'DEFAULT_CLOSE_TIMEOUT_MS')
    se = num('transports/stdio.ts', 'DEFAULT_MAX_STDERR_BYTES'); mm = num('transports/transport.ts', 'DEFAULT_MAX_MESSAGE_BYTES')
    f = Fig('mcp_stdio', 1120, 600, ('StdioTransport：子进程、按行 JSON 与三段式关闭', 'StdioTransport: a child process, line-delimited JSON and a three-step shutdown'))
    E = f.edge
    # start
    f.group(16, 52, 340, 330, 'infra', 'start()', ('启动服务器进程', 'spawn the server'), 'play', gid='st')
    f.node('cs', 32, 98, 308, 58, 'infra', 'crossSpawn(command, args)', ('cross-spawn：Windows 上也能跑 .cmd 包装', 'cross-spawn: .cmd shims work on Windows too'), None, tsize=11, ssize=9.5)
    f.node('env', 32, 170, 308, 46, 'infra', 'env = process.env + env', ('inheritEnv: false → 只用 env', 'inheritEnv: false → env only'), None, tsize=11, ssize=9.5)
    f.node('pg', 32, 230, 308, 46, 'infra', 'detached: true', ('非 Windows：自己的进程组', 'non-Windows: its own process group'), None, tsize=11, ssize=9.5)
    f.node('ws', 32, 290, 308, 46, 'infra', 'await "spawn" | "error"', ('命令不存在 → start() reject', 'missing command → start() rejects'), None, tsize=11, ssize=9.5)
    E([(186, 156), (186, 170)], 'cs', 'env', 'main', 'infra'); E([(186, 216), (186, 230)], 'env', 'pg', 'main', 'infra'); E([(186, 276), (186, 290)], 'pg', 'ws', 'main', 'infra')
    f.text(32, 364, ('进程组记入 liveProcessGroups；宿主退出时统一 SIGTERM。', 'Groups go into liveProcessGroups; host exit SIGTERMs them all.'), 9.5, 450, cls='muted', layer='label')
    # framing
    f.group(376, 52, 728, 330, 'ext', ('分帧', 'Framing'), ('一行 = 一条 JSON-RPC 消息', 'one line = one JSON-RPC message'), 'stream', title_mono=False, gid='fr')
    f.node('cl', 392, 104, 150, 44, 'ext', 'McpClient', None, None, kind='pill', align='center', tsize=11.5)
    f.node('in', 620, 98, 200, 56, 'infra', 'child.stdin', ('JSON.stringify(msg) + "\\n"', 'JSON.stringify(msg) + "\\n"'), None, tsize=11, ssize=9.5)
    f.node('srv', 900, 98, 188, 270, 'coding', ('MCP 服务器', 'MCP server'), ('子进程', 'child process'), 'cpu', mono=False, strong=True)
    f.node('out', 620, 188, 200, 56, 'infra', 'child.stdout', ('按 0x0a 切分 · 去掉 \\r', 'split at 0x0a · strip \\r'), None, tsize=11, ssize=9.5)
    f.node('err', 620, 290, 200, 56, 'infra', 'child.stderr', (f'保留最后 {MiB(se)} · onStderr', f'keeps the last {MiB(se)} · onStderr'), None, tsize=11, ssize=9.5)
    E([(542, 126), (620, 126)], 'cl', 'in', 'main', 'ext', label='send()', lpos=(581, 114))
    E([(820, 126), (900, 126)], 'in', 'srv', 'main', 'ext')
    E([(900, 216), (820, 216)], 'srv', 'out', 'event', 'coding')
    E([(900, 318), (820, 318)], 'srv', 'err', 'dep')
    E([(620, 216), (467, 216), (467, 148)], 'out', 'cl', 'event', 'coding', label='onMessage', lpos=(530, 204), r=6)
    f.text(392, 268, ('空行跳过；解析失败 → onError，继续读下一行', 'blank lines skipped; parse failure → onError, keep reading'), 9.5, 450, cls='muted', layer='label')
    f.text(392, 286, (f'单行超过 {MiB(mm)} → 丢弃并报错', f'a line over {MiB(mm)} → dropped with an error'), 9.5, 450, cls='muted', layer='label')
    f.text(392, 340, ('stderr 只是日志：', 'stderr is only a log:'), 9.5, 600, cls='faint', layer='label')
    f.text(392, 358, ('stderr: "inherit" 时直接给宿主终端', 'stderr: "inherit" sends it to the host terminal'), 9.5, 450, cls='muted', layer='label')
    # close timeline
    f.group(16, 402, 1088, 152, 'err', 'close()', ('规范要求的关闭顺序：先关 stdin，再发信号', 'the spec\'s shutdown order: close stdin first, then signals'), 'x', gid='cls')
    T = [(0, 'stdin.end()', ('让服务器自己退出', 'let the server exit on its own'), 'infra'),
         (grace, 'SIGTERM', (f'{grace} ms 后 · 整个进程组', f'after {grace} ms · the whole group'), 'err'),
         (grace + ct, 'SIGKILL', (f'再过 {ct:,} ms（closeTimeoutMs）', f'{ct:,} ms later (closeTimeoutMs)'), 'err')]
    x0, x1 = 48, 760
    hline(f, x0, x1, 470, cls='rule')
    for i, (t, lab, sub, lay) in enumerate(T):
        x = x0 + (x1 - x0) * i / 2
        dot(f, x, 470, lay, 5)
        f.text(x, 456, f't = {t:,} ms', 9.5, 600, True, 'start' if i == 0 else 'middle' if i == 1 else 'end', cls='faint', layer='label')
        f.text(x, 494, lab, 11, 650, True, 'start' if i == 0 else 'middle' if i == 1 else 'end', cls='strongt', layer='label')
        f.text(x, 512, sub, 9.5, 450, False, 'start' if i == 0 else 'middle' if i == 1 else 'end', cls='muted', layer='label')
    f.text(800, 460, ('子进程 "close" 后：', 'after the child\'s "close":'), 10, 650, cls='strongt', layer='label')
    f.text(800, 480, ('再对进程组发一次 SIGTERM，', 'SIGTERM the group once more, so'), 9.5, 450, cls='muted', layer='label')
    f.text(800, 496, ('npx / uvx 包装下的真正服务器也会退出', 'the real server under npx / uvx exits too'), 9.5, 450, cls='muted', layer='label')
    f.text(800, 522, ('Windows：taskkill /pid … /T /F', 'Windows: taskkill /pid … /T /F'), 9.5, 500, True, cls='muted', layer='label')
    f.text(48, 540, ('服务器提前退出时：残留的半行 → onError，然后 onClose（只触发一次），McpClient 拒绝所有 pending 请求。', 'If the server exits first: a leftover partial line → onError, then onClose (fires once); McpClient rejects every pending request.'), 9.5, 450, cls='faint', layer='label')
    f.legend(24, 580, [('main', ('客户端 → 服务器', 'client → server')), ('event', ('服务器 → 客户端', 'server → client')), ('dep', ('日志', 'log'))])
    return f

# ============================================================== mcp_http
@reg
def mcp_http():
    S = 'transports/streamable-http.ts'
    has(S, 'accept: "application/json, text/event-stream"', 'response.status === 202 || response.status === 204', 'headers.set("Mcp-Session-Id"', 'headers.set("MCP-Protocol-Version"',
        'if (response.status === 405)', 'return status === 408 || status === 429 || status >= 500;', '"last-event-id": lastEventId', 'method: "DELETE"', 'AbortSignal.timeout(1_000)',
        'new McpAuthRequiredError(response, body)', 'response.status === 404 && this.sessionIdValue', 'error="?insufficient_scope"?', 'Math.min(initial * 2 ** attempt, this.maxDelay())',
        'MCP response stream failed: ', 'if (attempt > 0 || !onUnauthorized || !needsAuthorization(response)) return response;')
    d0 = num(S, 'DEFAULT_RECONNECT_INITIAL_DELAY_MS'); dm = num(S, 'DEFAULT_RECONNECT_MAX_DELAY_MS'); rmax = num(S, 'DEFAULT_RECONNECT_MAX_RETRIES')
    f = Fig('mcp_http', 1120, 680, ('StreamableHttpTransport：一个 URL，POST 发消息，SSE 收消息', 'StreamableHttpTransport: one URL, POST to send, SSE to receive'))
    E = f.edge
    # request headers
    f.group(16, 52, 360, 300, 'infra', ('每个请求的头', 'Headers on every request'), None, 'file', title_mono=False, gid='hd')
    H = [('Accept', 'application/json, text/event-stream'), ('Content-Type', 'application/json'), ('Mcp-Session-Id', ('服务器在响应里分配后', 'once the server assigned one')),
         ('MCP-Protocol-Version', ('握手协商出的版本', 'the negotiated version')), ('Authorization', ('Bearer <authProvider.token()>', 'Bearer <authProvider.token()>'))]
    for i, (k, v) in enumerate(H):
        y = 104 + i * 46
        f.text(32, y, k, 10.5, 650, True, cls='strongt', layer='label')
        f.text(32, y + 18, v, 9.5, 450, isinstance(v, str), cls='muted', layer='label')
    f.text(32, 334, ('options.headers 先放入，上面这些覆盖它们。', 'options.headers go first; these override them.'), 9.5, 450, cls='faint', layer='label')
    # POST branch
    f.group(396, 52, 708, 300, 'ext', 'send(message) → POST', ('按消息类型和 Content-Type 分支', 'branches on message kind and Content-Type'), 'msg', gid='post')
    f.node('po', 412, 98, 200, 46, 'ext', 'authorizedFetch("POST")', ('401/403 → 见下方', '401 / 403 → see below'), None, tsize=10.5, ssize=9.5, strong=True)
    f.node('nt', 652, 98, 436, 46, 'ext', ('通知 / 响应', 'notification / response'), ('202 · 丢弃 body；若是 notifications/initialized → 打开 GET 流', '202 · discard the body; notifications/initialized → open the GET stream'), None, tsize=10.5, ssize=9.5, mono=False)
    f.node('js', 652, 160, 436, 46, 'ext', 'application/json', ('一条或一批（数组）消息 → onMessage', 'one message or a batch (array) → onMessage'), None, tsize=10.5, ssize=9.5)
    f.node('sse', 652, 222, 436, 46, 'ext', 'text/event-stream', ('consumeResponseStream(body, id)：读到该 id 的响应为止', 'consumeResponseStream(body, id): read until that id\'s response'), None, tsize=10.5, ssize=9.5)
    f.node('bad', 652, 284, 436, 46, 'err', ('请求却得到 202/204，或其他类型', 'a request answered 202/204, or another type'), 'McpHttpError', None, tsize=10.5, ssize=9.5, mono=False)
    for k, y in (('nt', 121), ('js', 183), ('sse', 245), ('bad', 307)):
        E([(612, 121), (632, 121), (632, y), (652, y)] if k != 'nt' else [(612, 121), (652, 121)], 'po', k, 'err' if k == 'bad' else 'main', None if k == 'bad' else 'ext', r=6)
    # status mapping
    f.group(16, 372, 360, 260, 'err', ('错误映射', 'Error mapping'), ('checkResponse()', 'checkResponse()'), 'shield', title_mono=False, gid='st')
    SM = [('401', 'McpAuthRequiredError', ('带 wwwAuthenticate', 'carries wwwAuthenticate')), ('404', 'McpSessionExpiredError', ('仅当已有会话 id', 'only with a session id')),
          ('others', 'McpHttpError(status)', ('body 截到 8 KiB', 'body capped at 8 KiB'))]
    for i, (c, n, s) in enumerate(SM):
        y = 418 + i * 52
        f.chip(32, y, c, 'err', size=10, h=20, cls='solid')
        f.text(100, y + 14, n, 10.5, 650, True, cls='strongt', layer='label')
        f.text(100, y + 32, s, 9.5, 450, cls='muted', layer='label')
    f.text(32, 584, ('401，或 403 且 error="insufficient_scope"：', '401, or 403 with error="insufficient_scope":'), 9.5, 600, cls='faint', layer='label')
    f.text(32, 602, ('先交给 authProvider.onUnauthorized() 一次，再重发', 'hand to authProvider.onUnauthorized() once, then retry'), 9.5, 450, cls='muted', layer='label')
    # streams & reconnect
    f.group(396, 372, 708, 260, 'agent', ('SSE 流与重连', 'SSE streams and reconnection'), None, 'loop', title_mono=False, gid='rc')
    f.node('get', 412, 418, 330, 54, 'agent', 'runGetStream()', ('一直保持打开；405 = 服务器不提供', 'kept open; 405 = server offers none'), None, tsize=11, ssize=9.5)
    f.node('rs', 758, 418, 330, 54, 'agent', 'consumeResponseStream()', ('只有带事件 id 时才续传', 'resumes only if events carry ids'), None, tsize=11, ssize=9.5)
    f.node('bo', 412, 494, 676, 56, 'agent', ('退避重连：Last-Event-ID 续传', 'Back-off reconnect, resuming with Last-Event-ID'),
           (f'延迟 = 服务器的 retry 字段，否则 min({d0:,} × 2^n, {dm:,}) ms · 连续失败 {rmax} 次放弃', f'delay = the server\'s retry field, else min({d0:,} × 2^n, {dm:,}) ms · give up after {rmax} failures in a row'), None, mono=False, tsize=11, ssize=9.5, strong=True)
    E([(577, 472), (577, 494)], 'get', 'bo', 'main', 'agent'); E([(923, 472), (923, 494)], 'rs', 'bo', 'main', 'agent')
    f.text(412, 574, ('可重试：408 · 429 · 5xx · 网络错误（TypeError、E*/UND_ERR_* 码）；认证、会话与协议错误不重试。', 'Retryable: 408 · 429 · 5xx · network errors (TypeError, E* / UND_ERR_* codes); auth, session and protocol errors are not.'), 9.5, 450, cls='muted', layer='label')
    f.text(412, 594, ('响应流断掉且无法续传：为该请求合成一条 -32603 错误响应，其余请求不受影响。', 'A response stream that breaks and cannot resume: a synthetic -32603 error response for that request only.'), 9.5, 450, cls='muted', layer='label')
    f.text(412, 614, ('close()：中止所有 fetch，带会话 id 发 DELETE（1 s 超时，复用上一个 token）。', 'close(): abort every fetch, send DELETE with the session id (1 s timeout, reusing the last token).'), 9.5, 450, cls='muted', layer='label')
    f.legend(24, 658, [('main', ('分支', 'branch')), ('err', ('错误', 'error')), ('layer:agent', ('流', 'streams'))])
    return f

# ============================================================== mcp_oauth
@reg
def mcp_oauth():
    has('oauth/discovery.ts', '/.well-known/oauth-protected-resource', '/.well-known/oauth-authorization-server', '/.well-known/openid-configuration', 'resource_metadata', 'authorization_servers?.[0]')
    has('oauth/flow.ts', 'code_challenge_method", "S256"', 'registration_endpoint', 'grant_type: "refresh_token"', 'new OAuthIssuerMismatchError', '["invalid_client", "unauthorized_client"]',
        'error.code === "invalid_grant"', 'invalidateCredentials?.("all")', 'invalidateCredentials?.("tokens")', 'throw new McpOAuthAuthorizationRequiredError()', 'inFlight ??=',
        'url.protocol !== "https:" || url.pathname === "/"', 'stepUpScope(granted?.scope, challenge.scope)')
    has('oauth/callback.ts', 'options.host ?? "127.0.0.1"', 'options.path ?? "/callback"', 'options.timeoutMs ?? 5 * 60_000', 'options.port ?? 0')
    has('oauth/provider.ts', 'state?.serverUrl === this.serverUrl ? state : { serverUrl: this.serverUrl }')
    f = Fig('mcp_oauth', 1120, 720, ('OAuth：从 401 到可用的访问令牌', 'OAuth: from a 401 to a usable access token'))
    E = f.edge
    # trigger
    f.node('u', 16, 56, 250, 52, 'err', ('HTTP 401 · 403 insufficient_scope', 'HTTP 401 · 403 insufficient_scope'), ('来自 StreamableHttpTransport', 'from StreamableHttpTransport'), 'shield', mono=False, tsize=10.5, ssize=9.5)
    f.node('ad', 300, 56, 380, 52, 'agent', 'adaptOAuthProvider().onUnauthorized', ('并发 401 共用一次 · token 已换过就直接重试', 'concurrent 401s share one run · token already replaced → just retry'), None, tsize=10.5, ssize=9.5)
    f.node('az', 714, 56, 390, 52, 'agent', 'authorizeMcp(provider, options)', ('→ "AUTHORIZED" | "REDIRECT"', '→ "AUTHORIZED" | "REDIRECT"'), 'key', tsize=11, ssize=9.5, strong=True)
    E([(266, 82), (300, 82)], 'u', 'ad', 'err'); E([(680, 82), (714, 82)], 'ad', 'az', 'main', 'agent')
    # runFlow steps
    f.group(16, 128, 1088, 410, 'agent', 'runFlow()', ('每一步的结果都存进 provider', 'each step\'s result is saved in the provider'), 'loop', gid='rf')
    ST = [(('1 · 发现', '1 · Discover'), [('WWW-Authenticate: resource_metadata=…', 'mono'), ('/.well-known/oauth-protected-resource{path}', 'mono'), (('→ authorization_servers[0]（缺省：服务器根）', '→ authorization_servers[0] (default: server root)'), ''),
                                         ('/.well-known/oauth-authorization-server{path}', 'mono'), ('/.well-known/openid-configuration{path}', 'mono'), (('结果缓存为 discoveryState', 'cached as discoveryState'), '')]),
          (('2 · resource 与 scope', '2 · resource and scope'), [(('resource 必须与服务器 URL 匹配', 'resource must match the server URL'), ''), (('scope = 参数 || scopes_supported', 'scope = option || scopes_supported'), ''), (('   || clientMetadata.scope', '   || clientMetadata.scope'), ''),
                                                             (('403 step-up：已授予 ∪ 挑战要求', '403 step-up: granted ∪ challenged'), '')]),
          (('3 · 客户端身份', '3 · Client identity'), [(('已存的 clientInformation', 'stored clientInformation'), ''), (('或 Client ID Metadata Document', 'or a Client ID Metadata Document'), ''), (('   （https、路径非根）', '   (https, non-root path)'), ''),
                                                        (('或动态注册 registration_endpoint', 'or dynamic registration at registration_endpoint'), '')])]
    xs, ws = [32, 420, 760], [372, 324, 328]
    for i, (t, rows) in enumerate(ST):
        x, w = xs[i], ws[i]
        f.text(x, 176, t, 11.5, 700, cls='strongt', layer='label')
        for j, (r, kind) in enumerate(rows):
            f.text(x, 200 + j * 20, r, 9.5 if kind == 'mono' else 10, 450, kind == 'mono', cls='muted', layer='label')
    vline(f, 406, 166, 318); vline(f, 746, 166, 318)
    f.node('rt', 32, 336, 300, 64, 'agent', ('4 · 有 refresh_token？', '4 · Have a refresh_token?'), 'grant_type=refresh_token', None, mono=False, kind='dec', tsize=11, ssize=9.5)
    f.node('ok', 32, 438, 300, 52, 'coding', ('saveTokens → "AUTHORIZED"', 'saveTokens → "AUTHORIZED"'), ('刷新成功；scope 缺省 = 原授权的', 'refreshed; missing scope = the grant\'s'), 'check', tsize=10.5, ssize=9)
    f.node('pk', 380, 336, 330, 64, 'agent', ('5 · startAuthorization()', '5 · startAuthorization()'), ('PKCE S256 · state · resource', 'PKCE S256 · state · resource'), None, sub2=('saveCodeVerifier → redirectToAuthorization', 'saveCodeVerifier → redirectToAuthorization'), tsize=11, ssize=9.5)
    f.node('rd', 380, 438, 330, 52, 'err', ('返回 "REDIRECT"', 'returns "REDIRECT"'), ('传输里 → McpOAuthAuthorizationRequiredError', 'in the transport → McpOAuthAuthorizationRequiredError'), None, mono=False, tsize=10.5, ssize=9)
    f.node('cx', 760, 336, 328, 64, 'agent', ('6 · 带 authorizationCode 再调一次', '6 · Called again with authorizationCode'), ('iss 校验（RFC 9207）', 'iss check (RFC 9207)'), None, sub2=('exchangeAuthorizationCode + codeVerifier', 'exchangeAuthorizationCode + codeVerifier'), mono=False, tsize=11, ssize=9.5)
    f.node('ok2', 760, 438, 328, 52, 'coding', ('saveTokens → "AUTHORIZED"', 'saveTokens → "AUTHORIZED"'), ('scope 缺省 = 请求的 scope', 'missing scope = the requested one'), 'check', tsize=10.5, ssize=9)
    E([(182, 400), (182, 438)], 'rt', 'ok', 'main', 'coding', label=('有', 'yes'), lpos=(204, 419), lmono=False, lsize=9.5)
    E([(332, 368), (380, 368)], 'rt', 'pk', 'main', 'agent', label=('无', 'no'), lpos=(356, 356), lmono=False, lsize=9.5)
    E([(545, 400), (545, 438)], 'pk', 'rd', 'err')
    E([(924, 400), (924, 438)], 'cx', 'ok2', 'main', 'coding')
    f.text(32, 524, ('刷新遇到网络错误或 server_error → 落到第 5 步；其他 OAuthError 抛出，交给 authorizeMcp 的恢复逻辑。', 'A refresh that hits a network error or server_error falls through to step 5; other OAuthErrors are thrown to authorizeMcp\'s recovery.'), 9.8, 450, cls='muted', layer='label')
    f.text(32, 508, ('错误恢复：invalid_client / unauthorized_client → 清空全部凭据重来；invalid_grant → 只清令牌重来。', 'Recovery: invalid_client / unauthorized_client → wipe all credentials and rerun; invalid_grant → wipe tokens only and rerun.'), 9.8, 450, cls='muted', layer='label')
    # callback + store
    f.group(16, 554, 530, 128, 'infra', 'OAuthCallbackServer.listen()', None, 'globe', gid='cb')
    f.text(32, 602, ('127.0.0.1 · 端口 0（随机）· 路径 /callback', '127.0.0.1 · port 0 (random) · path /callback'), 10, 500, cls='strongt', layer='label')
    f.text(32, 621, ('浏览器带回 code · state · iss；5 分钟超时', 'the browser brings back code · state · iss; 5-minute timeout'), 9.8, 450, cls='muted', layer='label')
    f.text(32, 640, ('之后用这些参数调用第 6 步', 'step 6 then runs with these parameters'), 9.8, 450, cls='muted', layer='label')
    f.text(32, 664, ('pi：只有 /mcp 里的登录会走浏览器；连接本身从不弹浏览器。', 'pi: only sign-in from /mcp opens a browser; connections never do.'), 9.5, 450, cls='faint', layer='label')
    f.group(566, 554, 538, 128, 'coding', 'McpOAuthProvider', ('McpOAuthState', 'McpOAuthState'), 'db', gid='pv')
    x = 582
    for k in ['clientInformation', 'tokens', 'tokensExpireAt', 'codeVerifier', 'oauthState', 'discovery']:
        x += f.chip(x, 594, k, 'coding', size=9.5, h=20) + 6
    assert x < 1096, x
    f.text(582, 640, ('按精确的 serverUrl 存取：别的服务器的状态一律忽略。', 'keyed by the exact serverUrl: state of any other server is ignored.'), 9.5, 450, cls='muted', layer='label')
    f.text(582, 660, ('默认 MemoryOAuthStateStore；pi 存到 mcp-auth.json。', 'default MemoryOAuthStateStore; pi persists to mcp-auth.json.'), 9.5, 450, cls='muted', layer='label')
    f.legend(24, 702, [('main', ('流程', 'flow')), ('err', ('需要用户参与 / 失败', 'needs the user / failure')), ('layer:coding', ('成功', 'success'))])
    return f

# ============================================================== mcp_content : content → LLM + errors
@reg
def mcp_content():
    has('protocol/content.ts', 'text: `[audio ${block.mimeType} omitted]`', 'text: `${block.name}: ${block.uri}`', 'resource.mimeType?.startsWith("image/")', '[binary resource ${resource.uri}',
        'content.length === 0 && result.structuredContent !== undefined', 'JSON.stringify(result.structuredContent, null, 2)')
    blocks = re.findall(r'^export interface (\w+Content) \{\n\ttype: "(\w+)"', _src('protocol/content.ts'), re.M)
    assert [b[1] for b in blocks] == ['text', 'image', 'audio', 'resource_link', 'resource'], blocks
    f = Fig('mcp_content', 1120, 620, ('工具结果怎样变成模型输入，以及错误类型', 'How tool results become model input, and the error types'))
    E = f.edge
    f.group(16, 52, 640, 452, 'ext', 'toLlmContent(result)', ('CallToolResult → (text | image)[]', 'CallToolResult → (text | image)[]'), 'filter', gid='tl')
    f.text(32, 104, 'ContentBlock', 10, 700, True, cls='faint', layer='label', ls='.04em')
    f.text(410, 104, 'LlmContent', 10, 700, True, cls='faint', layer='label', ls='.04em')
    R = [(f'{blocks[0][0]} · "text"', '{ type: "text", text }', 'coding', ('原样', 'as is')),
         (f'{blocks[1][0]} · "image"', '{ type: "image", data, mimeType }', 'ai', ('原样', 'as is')),
         (f'{blocks[2][0]} · "audio"', '"[audio <mime> omitted]"', 'err', ('占位文字', 'placeholder')),
         ('ResourceLinkContent · "resource_link"', '"<name>: <uri>"', 'coding', ('名称 + URI', 'name + URI')),
         ('resource · TextResourceContents', '{ type: "text", text }', 'coding', ('内嵌文本', 'embedded text')),
         ('resource · Blob, mimeType image/*', '{ type: "image", data: blob }', 'ai', ('内嵌图片', 'embedded image')),
         ('resource · other blob', '"[binary resource … omitted]"', 'err', ('占位文字', 'placeholder'))]
    for i, (a, b, lay, why) in enumerate(R):
        y = 118 + i * 50
        f.node(f'a{i}', 32, y, 270, 38, 'ext', a, None, None, tsize=10, kind='card')
        f.node(f'b{i}', 410, y, 230, 38, lay, b, None, None, tsize=10)
        E([(302, y + 19), (410, y + 19)], f'a{i}', f'b{i}', 'err' if lay == 'err' else 'main', None if lay == 'err' else 'ext', label=why, lpos=(356, y + 8), lmono=False, lsize=8.5)
    f.node('sc', 32, 470 - 6, 608, 34, 'infra', ('content 为空但有 structuredContent → 一条 JSON 文本（缩进 2）', 'no content but structuredContent → one JSON text block (indent 2)'), None, None, mono=False, tsize=10.5)
    # errors
    f.group(676, 52, 428, 452, 'err', ('错误类型', 'Error types'), ('缩进 = 子类', 'indent = subclass'), 'x', title_mono=False, gid='er')
    ERR = [('McpError', ('code · data：JSON-RPC 错误响应', 'code · data: a JSON-RPC error response'), 0),
           ('McpTimeoutError', ('请求超时', 'request timed out'), 0), ('McpAbortError', ('signal 中止', 'signal aborted'), 0),
           ('McpConnectionClosedError', ('传输关闭 / 未连接', 'transport closed / not connected'), 0),
           ('McpHttpError', ('status · body', 'status · body'), 0), ('McpAuthRequiredError', ('401 · wwwAuthenticate', '401 · wwwAuthenticate'), 1), ('McpSessionExpiredError', ('404：会话失效', '404: session expired'), 1),
           ('McpOAuthAuthorizationRequiredError', ('需要用户登录（./oauth）', 'the user must sign in (./oauth)'), 0)]
    for i, (n, s, ind) in enumerate(ERR):
        y = 98 + i * 50
        x = 692 + ind * 30
        f.node(f'e{i}', x, y, 396 - ind * 30, 40, 'err', n, s, None, tsize=10.5, ssize=9)
    E([(707, 344), (707, 368), (722, 368)], 'e4', 'e5', 'dep', r=4)
    E([(707, 368), (707, 418), (722, 418)], 'e4', 'e6', 'dep', r=4)
    # codes
    f.group(16, 524, 1088, 58, 'infra', 'JSON_RPC_ERROR_CODES', None, None, gid='cd')
    x = 220
    for k, v in rpc_codes():
        x += f.chip(x, 543, f'{v} {k}', 'infra', size=10, h=20) + 8
    f.legend(24, 604, [('main', ('转换', 'converted')), ('err', ('降级为文字', 'degraded to text')), ('dep', ('子类', 'subclass'))])
    return f

# ============================================================== mcp_pi : coding-agent integration
@reg
def mcp_pi():
    has_ca('extensions/mcp/tools.ts', 'const name = `mcp__${server}__${tool}`.replace(/[^A-Za-z0-9_]/g, "_");', 'createHash("sha256")', '.slice(0, 8)')
    has_ca('extensions/mcp/config.ts', 'readConfigFile(join(options.agentDir, "mcp.json"), "global", state);', 'options.projectTrusted ? join(options.cwd, CONFIG_DIR_NAME, "mcp.json")', 'auth is only allowed in the global mcp.json')
    has_ca('extensions/mcp/runtime.ts', 'new StreamableHttpTransport({', 'new StdioTransport({', 'new McpClient({')
    has_ca('extensions/mcp/resources.ts', 'list_mcp_resources', 'list_mcp_resource_templates', 'read_mcp_resource')
    has_ca('extensions/mcp/oauth.ts', 'mcp-auth.json')
    has_ca('core/mcp-servers.ts', 'Values may reference environment variables (`${NAME}`) or commands (`!cmd`).')
    has_ca('extensions/mcp/index.ts', 'registerMcpServer', 'tool_call`/`tool_result` hooks')
    ex = re.search(r'export type McpExposure = (.*?);', _ca('core/mcp-servers.ts')).group(1)
    EXP = re.findall(r'"(\w+)"', ex); assert EXP == ['codemode', 'deferred', 'direct', 'hidden'], EXP
    mx = int(re.search(r'MAX_TOOL_NAME_LENGTH = (\d+)', _ca('extensions/mcp/tools.ts')).group(1))
    n = total_loc(CAM + 'extensions/mcp')
    f = Fig('mcp_pi', 1120, 640, ('pi 怎样使用 pi-mcp：coding-agent 的内置 MCP 扩展', 'How pi uses pi-mcp: coding-agent\'s built-in MCP extension'))
    E = f.edge
    # sources
    f.group(16, 52, 330, 330, 'coding', ('服务器从哪里来', 'Where servers come from'), None, 'file', title_mono=False, gid='src')
    f.node('g', 32, 98, 298, 58, 'coding', '~/.pi/agent/mcp.json', ('全局 · 可用 auth: { provider }', 'global · may use auth: { provider }'), None, tsize=11, ssize=9.5)
    f.node('p', 32, 170, 298, 72, 'coding', '.pi/mcp.json', ('仅受信任的项目 · 同名覆盖全局', 'trusted projects only · same name replaces global'), None, sub2=('只写 enabled/exposure 时只改这几项', 'only enabled / exposure → just overrides those'), tsize=11, ssize=9.5)
    f.node('r', 32, 256, 298, 58, 'ext', 'pi.registerMcpServer()', ('扩展注册 · mcp.json 中同名优先', 'from extensions · mcp.json wins on a name clash'), None, tsize=11, ssize=9.5)
    f.text(32, 342, ('格式与其他 MCP 客户端相同：{ "mcpServers": { … } }', 'Same shape as other MCP clients: { "mcpServers": { … } }'), 9.5, 450, cls='muted', layer='label')
    f.text(32, 360, ('env / headers 的值可写 ${NAME} 或 !cmd', 'env / header values may use ${NAME} or !cmd'), 9.5, 450, cls='faint', layer='label')
    # runtime
    f.group(366, 52, 360, 330, 'ext', 'extensions/mcp/', (f'{n:,} 行', f'{n:,} lines'), 'plug', gid='rt')
    f.node('tr', 382, 98, 328, 58, 'infra', ('command → StdioTransport', 'command → StdioTransport'), ('url → StreamableHttpTransport', 'url → StreamableHttpTransport'), None, tsize=10.5, ssize=10, mono=True)
    f.node('mc', 382, 176, 328, 58, 'ext', 'new McpClient({ name, version })', ('会话开始时后台连接', 'connects in the background at session start'), None, tsize=10.5, ssize=9.5, strong=True)
    f.node('oa', 382, 254, 328, 58, 'agent', ('OAuth：存的令牌 + 刷新', 'OAuth: stored token + refresh'), ('<agent-dir>/mcp-auth.json · /mcp 登录', '<agent-dir>/mcp-auth.json · sign in with /mcp'), None, mono=False, tsize=10.5, ssize=9.5)
    E([(546, 156), (546, 176)], 'tr', 'mc', 'main', 'ext'); E([(546, 254), (546, 234)], 'oa', 'mc', 'dep')
    E([(330, 205), (382, 205)], 'p', 'mc', 'main', 'coding')
    f.text(382, 342, ('第一次提示只等待有 direct 工具的服务器；', 'The first prompt waits only for servers with direct tools;'), 9.5, 450, cls='muted', layer='label')
    f.text(382, 360, ('其他服务器在脚本或工具真正用到时再等。', 'others are awaited when a script or tool needs them.'), 9.5, 450, cls='muted', layer='label')
    # tools naming
    f.group(746, 52, 358, 330, 'tui', ('工具名', 'Tool names'), 'createMcpToolName()', 'tool', title_mono=False, gid='nm')
    codebox(f, 762, 98, 326, [(0, 'mcp__<server>__<tool>', 'strongt'), (0, ('# [^A-Za-z0-9_] → _', '# [^A-Za-z0-9_] → _'), 'faint'),
                              (0, 'mcp__docs__search_pages', 'muted'), (0, 'mcp__my_server__get_issue', 'muted')], ('规则', 'RULE'), 10, 18)
    f.text(762, 254, (f'超过 {mx} 个字符或与另一工具重名：', f'Longer than {mx} chars, or clashing:'), 10, 600, cls='strongt', layer='label')
    f.text(762, 272, ('截断 + "_" + sha256(server\\0tool) 前 8 位', 'truncate + "_" + first 8 hex of sha256(server\\0tool)'), 9.5, 450, cls='muted', layer='label')
    f.text(762, 300, ('名字同时就是 codemode 脚本里的标识符：', 'The name is also the identifier in codemode:'), 10, 600, cls='strongt', layer='label')
    f.text(762, 318, 'await tools.mcp__docs__search_pages({…})', 9.5, 450, True, cls='muted', layer='label')
    f.text(762, 346, ('资源走 3 个通用工具：', 'Resources use three generic tools:'), 10, 600, cls='strongt', layer='label')
    f.text(762, 364, 'list_mcp_resources · …_templates · read_mcp_resource', 9, 450, True, cls='muted', layer='label')
    # exposure
    f.group(16, 402, 1088, 186, 'ext', ('exposure：工具怎样出现在模型面前', 'exposure: how tools reach the model'), ('按服务器设置，toolExposure 按工具覆盖', 'set per server; toolExposure overrides per tool'), 'eye', title_mono=False, gid='ex')
    D = {'codemode': (('默认：只能在 codemode 脚本里调用', 'default: callable only from codemode scripts'), ('不进工具声明；脚本用 searchTools() 找', 'not declared; scripts find them via searchTools()'), 'ext', True),
         'deferred': (('tool_search 加载后才声明', 'declared once tool_search loads them'), ('激活 tool_search 而不是 codemode', 'activates tool_search instead of codemode'), 'agent', False),
         'direct': (('立即声明给模型', 'declared to the model right away'), ('和内置工具一样直接调用', 'called directly like built-in tools'), 'coding', False),
         'hidden': (('完全不可达', 'unreachable'), ('/mcp 里可以改回来', 'switch it back in /mcp'), 'infra', False)}
    for i, k in enumerate(EXP):
        a, b, lay, st = D[k]
        x = 32 + i * 266
        f.node(f'x{i}', x, 448, 256, 76, lay, f'"{k}"', a, None, sub2=b, tsize=12, ssize=9.5, strong=st)
    f.text(32, 548, ('codemode 曝光的服务器连上时，若 autoEnableCodemode（默认 true）就自动激活 codemode 工具。', 'When a codemode-exposure server connects, the codemode tool is activated unless autoEnableCodemode (default true) is false.'), 9.8, 450, cls='muted', layer='label')
    f.text(32, 568, ('每次调用都走 pi 的工具管线：tool_call / tool_result 钩子与权限扩展同样作用于 MCP 工具。', 'Every call runs through pi\'s tool pipeline: tool_call / tool_result hooks and permission extensions apply to MCP tools too.'), 9.8, 450, cls='muted', layer='label')
    f.legend(24, 616, [('layer:coding', ('配置', 'config')), ('layer:ext', ('MCP 运行时', 'MCP runtime')), ('layer:agent', 'OAuth'), ('layer:infra', ('传输', 'transport'))])
    return f
