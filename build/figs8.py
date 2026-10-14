"""pi-codemode deep-dive diagrams (cm_*). Facts read from /workspace/pi-src/packages/codemode at build time."""
import re, json
from svgkit import Fig, maxw, pair
from figs import reg
from figkit import SRC, uml, codebox, bar, dot, hline, vline, chiprow, lines_of

C = 'packages/codemode/src/'
CAC = 'packages/coding-agent/src/extensions/codemode/'
def _src(p): return (SRC / (C + p)).read_text()
def _ca(p): return (SRC / (CAC + p)).read_text()
def loc(p): return lines_of(C + p)
def has(p, *needles):
    s = _src(p)
    for n in needles: assert n in s, (p, n)
def has_ca(p, *needles):
    s = _ca(p)
    for n in needles: assert n in s, (p, n)
def total_loc(base=C):
    return sum(lines_of(str(x.relative_to(SRC))) for x in (SRC / base).rglob('*.ts') if not x.name.endswith(('.test.ts', '.d.ts')))
def num(p, name, src=None):
    v = re.search(r'\b' + name + r'\s*=\s*([^;]+);', src or _src(p)).group(1).replace('_', '')
    r = 1
    for x in v.split('*'): r *= int(x.strip())
    return r
def exports():
    j = json.loads((SRC / 'packages/codemode/package.json').read_text())
    return {k: v['source'] for k, v in j['exports'].items() if k != './package.json'}, j.get('dependencies', {})
def reserved():
    blk = re.search(r'RESERVED_GLOBALS: ReadonlySet<string> = new Set\(\[(.*?)\]\)', _src('runtime/host.ts'), re.S).group(1)
    return re.findall(r'"(\w+)"', blk)
def msg_types():
    s = _src('runtime/protocol.ts')
    w2h = re.search(r'export type WorkerToHostMessage =(.*?);\n\nexport', s, re.S).group(1)
    return list(dict.fromkeys(re.findall(r'type: "(\w+)"', w2h))), re.findall(r'type: "(\w+)"', re.search(r'export type HostToWorkerMessage =(.*?);\n', s, re.S).group(1))
def err_kinds():
    return re.findall(r'\| "(\w+)"', re.search(r'export type CodemodeErrorKind =(.*?);', _src('types.ts'), re.S).group(1))
def fmt_chars(n):
    return f'{n // (1024 * 1024)} Mi' if n % (1024 * 1024) == 0 else f'{n // 1024} Ki'

# ============================================================== cm_arch
@reg
def cm_arch():
    tot = total_loc(); ex, deps = exports()
    assert list(ex) == ['.', './declarations', './source', './worker'], ex
    f = Fig('cm_arch', 1120, 560, (f'pi-codemode 模块结构（{tot:,} 行 TypeScript）', f'pi-codemode modules ({tot:,} lines of TypeScript)'))
    COLS = [(('宿主侧（主线程）', 'Host side (main thread)'), 'ext', 'cpu', [
                ('runtime/host.ts', ('CodemodeSandbox · Execution', 'CodemodeSandbox · Execution')),
                ('runtime/protocol.ts', ('宿主 ↔ worker 消息', 'host ↔ worker messages')),
                ('wasm.ts', ('loadQuickJSWasm()：编译一次', 'loadQuickJSWasm(): compile once')),
                ('types.ts', ('Tool · Result · Error · Options', 'Tool · Result · Error · Options'))]),
            (('沙箱内（worker 线程）', 'Inside the sandbox (worker thread)'), 'agent', 'shield', [
                ('runtime/worker.ts', ('QuickJS VM · bridge · drain', 'QuickJS VM · bridge · drain')),
                ('runtime/prelude-source.ts', ('VM 内的 JS：tools · text · store', 'JS in the VM: tools · text · store'))]),
            (('给模型看的文本', 'Text for the model'), 'coding', 'file', [
                ('declarations.ts', ('JSON Schema → TypeScript 声明', 'JSON Schema → TypeScript declarations')),
                ('source.ts', ('// @options: 行 · Lark 语法', '// @options: line · Lark grammar')),
                ('identifier.ts', ('工具名 → JS 标识符', 'tool name → JS identifier'))])]
    W, X0 = 352, 16
    for ci, (title, lay, ic, rows) in enumerate(COLS):
        x = X0 + ci * (W + 16)
        f.group(x, 52, W, 276, lay, title, None, ic, title_mono=False, gid=f'g{ci}')
        for ri, (p, role) in enumerate(rows):
            f.node(f'n{ci}{ri}', x + 12, 98 + ri * 54, W - 24, 46, lay, p, role, None, tsize=11.5, ssize=10, tag=f'{loc(p):,}', strong=(p in ('runtime/host.ts', 'runtime/worker.ts')))
    E = f.edge
    f.text(384 + 12, 230, ('postMessage 两边只传 JSON 字符串；', 'Only JSON strings cross postMessage;'), 9.8, 450, cls='muted', layer='label')
    f.text(384 + 12, 248, ('VM 内没有 timers、fetch、process、require、模块。', 'the VM has no timers, fetch, process, require or modules.'), 9.8, 450, cls='muted', layer='label')
    f.text(752 + 12, 284, (f'index.ts（{loc("index.ts")} 行）重新导出全部', f'index.ts ({loc("index.ts")} lines) re-exports them all'), 9.8, 450, cls='muted', layer='label')
    # exports
    f.group(16, 348, 1088, 156, 'ext', ('导入路径、依赖与使用者', 'Import paths, dependencies and users'), None, 'box', title_mono=False, gid='bot')
    x = 32
    for k, v in ex.items():
        w = f.chip(x, 394, '@earendil-works/pi-codemode' + k[1:], 'ext', size=10, h=22)
        f.text(x + 4, 432, v.replace('./src/', 'src/'), 9.5, 450, True, cls='faint', layer='label')
        x += w + 10
    dep = ' · '.join(f'{k} {v}' for k, v in deps.items())
    f.text(32, 468, ('运行时依赖：', 'runtime dep:'), 10.5, 600, cls='faint', layer='label')
    xx = 32 + maxw(('运行时依赖：', 'runtime dep:'), 10.5, 600) + 6
    xx += f.chip(xx, 453, dep, 'agent', size=10.5, h=22) + 10
    f.text(xx, 468, ('（QuickJS 编译为 WASI wasm）', '(QuickJS compiled to WASI wasm)'), 10, 450, cls='muted', layer='label')
    n = total_loc(CAC)
    f.chip(760, 453, f'coding-agent · extensions/codemode ({n:,})', 'coding', size=10.5, h=22)
    f.text(32, 490, ('"./worker" 单独导出：打包后的宿主（如 Bun 编译的可执行文件）要把它作为独立入口，再通过 workerUrl 传入。', '"./worker" is exported on its own: bundled hosts (e.g. a Bun-compiled binary) make it a separate entry and pass it as workerUrl.'), 9.5, 450, cls='faint', layer='label')
    f.legend(24, 536, [('layer:ext', ('宿主', 'host')), ('layer:agent', ('沙箱', 'sandbox')), ('layer:coding', ('模型可见的文本', 'model-facing text'))])
    f.note(1096, 536, ('标签 = 行数', 'tag = lines of code'), 10.5, anchor='end')
    return f

# ============================================================== cm_sandbox : the three layers
@reg
def cm_sandbox():
    has('runtime/host.ts', 'new Worker(options.workerUrl, { workerData })', 'Atomics.store(new Int32Array(this.interrupt), 0, 1);', '.terminate()', 'private readonly interrupt = new SharedArrayBuffer(4);')
    has('runtime/worker.ts', 'QuickJS.create({', 'interruptHandler: () => Atomics.load(interrupt, 0) !== 0', 'maxStackSize: MAX_STACK_SIZE', 'wasi: discardOutput', 'vm.newFunction("bridge"')
    has('runtime/prelude-source.ts', '(function lockdown() {', 'keeps the host bridge in a closure')
    w2h, h2w = msg_types()
    f = Fig('cm_sandbox', 1120, 620, ('三层隔离：宿主线程 · worker 线程 · QuickJS 虚拟机', 'Three layers: host thread · worker thread · QuickJS VM'))
    E = f.edge
    f.group(16, 52, 330, 500, 'ext', ('宿主线程', 'Host thread'), 'runtime/host.ts', 'cpu', title_mono=False, gid='h')
    f.node('sb', 32, 98, 298, 58, 'ext', 'CodemodeSandbox', ('工具表 · globals · 默认值', 'tool table · globals · defaults'), None, sub2=('不持有 VM', 'holds no VM'), ssize=9.5, strong=True)
    f.node('ex', 32, 182, 298, 72, 'ext', 'Execution', ('一次 execute() = 一个 worker + 一个 VM', 'one execute() = one worker + one VM'), None, sub2=('计时器 · pending 调用 · output · calls', 'timer · pending calls · output · calls'), ssize=9.5)
    f.node('tl', 32, 280, 298, 58, 'coding', 'CodemodeTool.execute(args, { signal })', ('真正的能力在这里（宿主侧）', 'the real capability lives here (host side)'), None, tsize=10.5, ssize=9.5)
    E([(181, 156), (181, 182)], 'sb', 'ex', 'main', 'ext'); E([(181, 254), (181, 280)], 'ex', 'tl', 'main', 'coding')
    f.text(32, 372, ('结束时：', 'On finish:'), 10, 650, cls='strongt', layer='label')
    f.text(32, 392, ('1 中止所有未完成的工具调用', '1 abort every pending tool call'), 9.8, 450, cls='muted', layer='label')
    f.text(32, 410, ('2 Atomics.store(interrupt, 1)', '2 Atomics.store(interrupt, 1)'), 9.8, 450, True, cls='muted', layer='label')
    f.text(32, 428, ('3 worker.terminate()，再 resolve 结果', '3 worker.terminate(), then resolve'), 9.8, 450, cls='muted', layer='label')
    f.text(32, 456, ('interrupt 是共享的 4 字节；VM 的中断处理器轮询它，', 'interrupt is a shared 4-byte buffer the VM\'s interrupt'), 9.5, 450, cls='faint', layer='label')
    f.text(32, 472, ('因为 Bun 的 terminate() 停不住在 wasm 里空转的线程。', 'handler polls: Bun\'s terminate() cannot stop a thread spinning in wasm.'), 9.5, 450, cls='faint', layer='label')
    f.text(32, 500, ('每次执行都是新 worker：失控的脚本被直接杀掉，', 'A fresh worker per run: a runaway script is killed'), 9.5, 450, cls='faint', layer='label')
    f.text(32, 516, ('不会污染下一次执行。', 'outright and cannot poison the next run.'), 9.5, 450, cls='faint', layer='label')
    # worker
    f.group(396, 52, 708, 500, 'infra', ('worker 线程', 'Worker thread'), 'runtime/worker.ts', 'layers', title_mono=False, gid='w')
    f.node('qc', 412, 98, 676, 58, 'infra', 'QuickJS.create({ wasm, memoryLimit, maxStackSize, interruptHandler, wasi })', ('wasm 模块由宿主编译后经 workerData 共享；引擎自己的 stdout/stderr 被丢弃', 'the wasm module is compiled by the host and shared via workerData; the engine\'s own stdout/stderr is discarded'), None, tsize=10.5, ssize=9.5)
    f.node('br', 412, 182, 200, 72, 'infra', 'bridge(kind, a, b, c)', ('只接收原始值', 'primitives only'), None, sub2='call · global · output · done', tsize=10.5, ssize=9.5, strong=True)
    # VM
    f.group(640, 172, 448, 360, 'agent', ('QuickJS VM（独立的 wasm 实例）', 'QuickJS VM (a separate wasm instance)'), None, 'shield', title_mono=False, gid='vm')
    f.node('pl', 656, 218, 416, 72, 'agent', 'PRELUDE_SOURCE', ('先冻结所有内建对象（lockdown）', 'first freezes every built-in (lockdown)'), None, sub2=('bridge 藏在闭包里，脚本拿不到', 'keeps bridge in a closure the script cannot reach'), ssize=9.5)
    f.node('sc', 656, 316, 416, 72, 'agent', '(async (tools, console) => { <script> })', ('脚本 = async 函数体：可以 return 和顶层 await', 'script = an async function body: return and top-level await work'), None, tsize=10.5, ssize=9.5, strong=True)
    E([(864, 290), (864, 316)], 'pl', 'sc', 'dep')
    f.text(656, 416, ('脚本能看到的全部：', 'Everything the script can see:'), 10, 650, cls='strongt', layer='label')
    chiprow(f, 656, 428, ['tools', 'ALL_TOOLS', 'text', 'image', 'exit', 'console', 'store', 'load'], 'agent', size=9.5, h=20, gap=5)
    f.text(656, 470, ('+ 宿主配置的 globals（如 searchTools、models.*）', '+ host-configured globals (e.g. searchTools, models.*)'), 9.8, 450, cls='muted', layer='label')
    f.text(656, 494, ('没有：', 'Not there:'), 10, 650, cls='err', layer='label')
    chiprow(f, 724, 482, ['setTimeout', 'fetch', 'process', 'require', 'import'], 'err', size=9.5, h=20, gap=5)
    E([(612, 218), (626, 218), (626, 254), (656, 254)], 'br', 'pl', 'dep', r=6)
    # host <-> worker
    E([(330, 205), (412, 205)], 'ex', 'br', 'main', 'ext', label=h2w[0], lpos=(371, 193))
    E([(412, 238), (330, 238)], 'br', 'ex', 'event', 'infra')
    f.text(412, 290, ('worker → 宿主：', 'worker → host:'), 9.8, 650, cls='strongt', layer='label')
    for i, t in enumerate(w2h):
        f.text(412, 310 + i * 18, f'"{t}"', 9.5, 500, True, cls='muted', layer='label')
    f.text(412, 400, ('宿主 → worker：', 'host → worker:'), 9.8, 650, cls='strongt', layer='label')
    f.text(412, 420, f'"{h2w[0]}"' + ' { id, ok, payload }', 9.5, 500, True, cls='muted', layer='label')
    f.text(412, 448, ('参数、结果、值都以 JSON', 'Args, results and values'), 9.5, 450, cls='faint', layer='label')
    f.text(412, 464, ('字符串跨越边界', 'cross as JSON strings'), 9.5, 450, cls='faint', layer='label')
    f.legend(24, 596, [('layer:ext', ('宿主线程', 'host thread')), ('layer:infra', ('worker 线程', 'worker thread')), ('layer:agent', 'QuickJS VM'), ('main', ('宿主 → worker', 'host → worker')), ('event', ('worker → 宿主', 'worker → host'))])
    return f

# ============================================================== cm_exec : one execute() from start to result
@reg
def cm_exec():
    has('runtime/host.ts', 'this.finish({ kind: "timeout", message: `Execution timed out after', 'kind: "sandbox", message: `Failed to load QuickJS', 'Worker exited with code', 'Sandbox bridge broken',
        'this.finish({ kind: "aborted"', 'execution.abort("Sandbox closed")', 'tools: new Map(this.toolsByName)')
    has('runtime/worker.ts', 'vm.evalCode(PRELUDE_SOURCE, "codemode-prelude.js")', 'vm.evalCode(`(async (tools, console) => {${data.code}\\n})`, "codemode.js")', 'vm.executePendingJobs();', 'vm.callFunction(stalled, api)')
    has('wasm.ts', 'const modules = new Map<string, Promise<CodemodeWasmModule>>();', 'modules.delete(resolved);')
    to = num('runtime/host.ts', 'DEFAULT_TIMEOUT_MS'); K = err_kinds()
    assert K == ['script', 'timeout', 'aborted', 'sandbox'], K
    f = Fig('cm_exec', 1120, 640, ('一次 execute(code)：从脚本文本到 CodemodeResult', 'One execute(code): from script text to CodemodeResult'))
    E = f.edge
    f.group(16, 52, 1088, 132, 'ext', ('宿主：new Execution(…)', 'Host: new Execution(…)'), ('工具表在此刻复制一份', 'the tool table is copied at this moment'), 'cpu', title_mono=False, gid='h')
    H = [('execute(code, opts)', ('opts: signal · timeoutMs · store', 'opts: signal · timeoutMs · store')),
         (f'setTimeout({to:,} ms)', ('默认截止时间；Infinity = 不限', 'default deadline; Infinity = none')),
         ('loadQuickJSWasm()', ('每个路径只读取并编译一次', 'read and compiled once per path')),
         ('new Worker(url, workerData)', ('code · tools · globals · wasm · store · interrupt', 'code · tools · globals · wasm · store · interrupt'))]
    x = 32; ws = [220, 222, 222, 340]
    for i, (t, s) in enumerate(H):
        f.node(f'h{i}', x, 98, ws[i], 64, 'ext', t, s, None, tsize=11, ssize=9.5, strong=(i == 3))
        if i: E([(x - 14, 130), (x, 130)], f'h{i-1}', f'h{i}', 'main', 'ext')
        x += ws[i] + 14
    f.group(16, 204, 1088, 132, 'agent', ('worker：准备 VM 并运行', 'Worker: prepare the VM and run'), 'runtime/worker.ts', 'layers', title_mono=False, gid='w')
    Wk = [('QuickJS.create()', ('memoryLimit · maxStackSize', 'memoryLimit · maxStackSize')), ('evalCode(PRELUDE_SOURCE)', ('(bridge, tools, globals, store)', '(bridge, tools, globals, store)')),
          ('evalCode(async wrapper)', ('语法错误 → 直接 done(false)', 'syntax error → done(false) at once')), ('run(fn) → drain()', ('executePendingJobs + stalled()', 'executePendingJobs + stalled()'))]
    x = 32; ws = [230, 262, 270, 262]
    for i, (t, s) in enumerate(Wk):
        f.node(f'w{i}', x, 250, ws[i], 64, 'agent', t, s, None, tsize=11, ssize=9.5, strong=(i == 3))
        if i: E([(x - 14, 282), (x, 282)], f'w{i-1}', f'w{i}', 'main', 'agent')
        x += ws[i] + 14
    E([(950, 162), (950, 192), (23, 192), (23, 282), (32, 282)], 'h3', 'w0', 'main', 'ext', r=6)
    # loop note
    f.text(32, 358, ('之后每收到一个 "result" 消息：settle(id) → drain()。没有计时器和 I/O，所以"无 pending 调用却没结束"= 永远不会结束，stalled() 立即判失败。', 'Then for every "result" message: settle(id) → drain(). With no timers or I/O, "not finished and no call pending" means it never will be, so stalled() fails it at once.'), 9.8, 450, cls='muted', layer='label')
    # outcomes
    f.group(16, 380, 1088, 200, 'infra', ('结束：finish() 只执行一次', 'Finishing: finish() runs exactly once'), None, 'flag', title_mono=False, gid='o')
    O = [('ok: true', ('return 值或 exit()', 'return value or exit()'), ('value · output · calls · storeWrites', 'value · output · calls · storeWrites'), 'coding'),
         ('"script"', ('脚本抛错或解析失败', 'the script threw or failed to parse'), ('name · message · stack', 'name · message · stack'), 'err'),
         ('"timeout"', ('截止时间到', 'the deadline expired'), ('worker 被终止', 'worker terminated'), 'err'),
         ('"aborted"', ('signal 触发或 sandbox.close()', 'signal fired or sandbox.close()'), ('worker 被终止', 'worker terminated'), 'err'),
         ('"sandbox"', ('wasm 陷阱 · worker 退出 · 桥被破坏', 'wasm trap · worker exit · broken bridge'), ('如脚本改了 toJSON', 'e.g. a script patched toJSON'), 'err')]
    for i, (t, a, b, lay) in enumerate(O):
        x = 32 + i * 214
        f.node(f'o{i}', x, 426, 202, 76, lay, t, a, None, sub2=b, tsize=11.5, ssize=9, strong=(i == 0))
    f.text(32, 528, ('失败的结果同样带着 output 与 calls（直到失败那一刻），只有成功的执行才报告 storeWrites。', 'Failed results still carry output and calls (up to the failure); only successful runs report storeWrites.'), 9.8, 450, cls='muted', layer='label')
    f.text(32, 548, ('execute() 本身从不因脚本失败而 reject；只有在 sandbox 已关闭时 reject。', 'execute() itself never rejects for script failures — only when the sandbox is already closed.'), 9.8, 450, cls='muted', layer='label')
    f.legend(24, 616, [('layer:ext', ('宿主', 'host')), ('layer:agent', 'worker / VM'), ('layer:coding', ('成功', 'success')), ('layer:err', ('CodemodeError.kind', 'CodemodeError.kind'))])
    return f

# ============================================================== cm_bridge : one tool call round trip
@reg
def cm_bridge():
    has('runtime/host.ts', 'const record: CodemodeCall | undefined = isTool ? { name, status: "cancelled", durationMs: 0 } : undefined;', 'JSON.parse(message.args)',
        'await tool.execute(args, { signal: pending.controller.signal })', 'reply = { type: "result", id, ok: false, payload: errorMessage(error) };', 'duplicate call id')
    has('runtime/prelude-source.ts', 'entry.reject(new ErrorCtor(payload));', 'Did you mean ')
    f = Fig('cm_bridge', 1120, 640, ('一次工具调用的往返：await tools.x(args)', 'One tool call round trip: await tools.x(args)'))
    E = f.edge
    LX = {'s': 120, 'p': 360, 'w': 590, 'h': 820, 't': 1010}
    HD = {'s': (('脚本', 'script'), 'agent'), 'p': ('prelude', 'agent'), 'w': ('worker.ts', 'infra'), 'h': ('Execution', 'ext'), 't': ('CodemodeTool', 'coding')}
    for k, (t, lay) in HD.items():
        f.node('hd' + k, LX[k] - 80, 56, 160, 32, lay, t, None, None, kind='pill', align='center', tsize=11.5, mono=isinstance(t, str))
        vline(f, LX[k], 88, 580)
    M = [('s', 'p', 'tools.mcp__docs__search({ q })', ('代理按 jsName 或原名找到工具；不存在 → TypeError + 相近名称提示', 'proxy finds the tool by jsName or name; missing → TypeError with near-miss suggestions'), 'main', 'agent'),
         ('p', 'w', 'bridge("call", id, name, argsJson)', ('参数先 JSON.stringify；返回 Promise，记入 pending', 'args JSON.stringify-ed; returns a Promise kept in pending'), 'main', 'agent'),
         ('w', 'h', '{ type: "call", id, target: "tool", name, args }', ('postMessage', 'postMessage'), 'main', 'infra'),
         ('h', 't', 'execute(JSON.parse(args), { signal })', ('calls[] 先记 "cancelled"，完成后改为 ok / error 并记录耗时', 'calls[] starts as "cancelled", becomes ok / error with its duration'), 'main', 'ext'),
         ('t', 'h', ('返回值（必须可 JSON 序列化）或抛错', 'a value (JSON-serializable) or a throw'), None, 'event', 'coding'),
         ('h', 'w', '{ type: "result", id, ok, payload }', ('ok → JSON 文本 · 否则 → 错误消息', 'ok → JSON text · else → the error message'), 'event', 'ext'),
         ('w', 'p', 'settle(id, ok, payload) → drain()', ('executePendingJobs：脚本从 await 处继续', 'executePendingJobs: the script resumes after await'), 'event', 'infra'),
         ('p', 's', ('resolve(JSON.parse(payload)) · reject(new Error(msg))', 'resolve(JSON.parse(payload)) · reject(new Error(msg))'), None, 'event', 'agent')]
    y = 120
    for i, (a, b, lab, sub, kind, lay) in enumerate(M):
        x1, x2 = LX[a], LX[b]
        E([(x1, y + 12), (x2, y + 12)], None, None, kind, lay, r=0)
        f.step(i + 1, min(x1, x2) - 16 if min(x1, x2) > 40 else 24, y + 12, lay, r=8)
        lx = min(x1, x2) + 10
        f.text(lx, y + 4, lab, 10, 600, isinstance(lab, str), cls='strongt', layer='label')
        if sub: f.text(lx, y + 30, sub, 9.3, 450, cls='muted', layer='label')
        y += 54
    f.text(32, 572, ('并发：Promise.all 同时发出的多个调用各有自己的 id，宿主并行执行；同一 id 出现两次 → "sandbox" 错误。', 'Concurrency: calls issued together (Promise.all) each get an id and run in parallel on the host; a repeated id → a "sandbox" error.'), 9.8, 450, cls='muted', layer='label')
    f.text(32, 592, ('globals 走同一条路，只是 target: "global"，且不记入 result.calls。', 'Globals take the same path with target: "global", and are not recorded in result.calls.'), 9.8, 450, cls='muted', layer='label')
    f.legend(24, 620, [('main', ('请求方向', 'request')), ('event', ('返回方向', 'reply'))])
    return f

# ============================================================== cm_prelude : the script-visible API and its limits
@reg
def cm_prelude():
    P = 'runtime/prelude-source.ts'
    has(P, 'for (const level of ["log", "info", "warn", "error", "debug"])', 'not a PNG, JPEG, GIF, or WebP image', 'const OVERRIDABLE = new Set(["constructor", "name", "message", "toString", "toLocaleString", "valueOf", "toJSON"]);',
        'Object.defineProperty(globalThis, "store"', 'Object.defineProperty(globalThis, "load"', 'stored.delete(key);')
    oc, oi = num(P, 'MAX_OUTPUT_CHARS'), num(P, 'MAX_OUTPUT_ITEMS'); sv, st = num(P, 'MAX_STORE_VALUE_CHARS'), num(P, 'MAX_STORE_TOTAL_CHARS')
    to = num('runtime/host.ts', 'DEFAULT_TIMEOUT_MS'); R = reserved()
    f = Fig('cm_prelude', 1120, 640, ('脚本能用什么：prelude 搭出的全部 API 与限额', 'What a script can use: the whole API the prelude builds, and its limits'))
    f.group(16, 52, 700, 452, 'agent', ('脚本可见的全局', 'Script-visible globals'), ('由 PRELUDE_SOURCE 定义，全部只读', 'defined by PRELUDE_SOURCE, all read-only'), 'code', title_mono=False, gid='api')
    A = [('tools.<id>(args) · tools["name"](args)', ('Promise；名字不存在 → TypeError，附相近名称', 'a Promise; unknown name → TypeError with near misses')),
         ('ALL_TOOLS', ('[{ name: <id>, description }]', '[{ name: <id>, description }]')),
         ('text(value)', ('追加文本；非字符串先 JSON 序列化', 'append text; non-strings are JSON-serialized')),
         ('image(url | { image_url } | ImageContent)', ('base64 data: URL；只认 PNG / JPEG / GIF / WebP', 'base64 data: URL; PNG / JPEG / GIF / WebP only')),
         ('console.log · info · warn · error · debug', ('文本项，标记 console: true', 'text items marked console: true')),
         ('exit()', ('立即成功结束，value = undefined', 'finish successfully now, value = undefined')),
         ('store(key, value) · load(key)', ('同步；作用于传入的 JSON 快照；value = undefined 即删除', 'synchronous, on the JSON snapshot passed in; undefined deletes')),
         ('<global>(args) · <ns>.<member>(args)', ('宿主的 globals；spread: true 时传全部参数', 'host globals; spread: true passes every argument')),
         ('return <value>', ('脚本是 async 函数体；返回值即 result.value', 'the script is an async body; the value becomes result.value'))]
    for i, (a, b) in enumerate(A):
        y = 100 + i * 44
        f.text(32, y + 10, a, 10.5, 600, True, cls='strongt', layer='label')
        f.text(32, y + 28, b, 9.5, 450, cls='muted', layer='label')
        if i: hline(f, 32, 700, y - 6)
    # limits
    f.group(736, 52, 368, 452, 'err', ('限额', 'Limits'), ('超出即抛错', 'exceeding throws'), 'shield', title_mono=False, gid='lim')
    LM = [(f'{fmt_chars(oc)} chars', ('输出总字符（文本 + base64 图片）', 'total output chars (text + base64 images)')),
          (f'{oi:,} items', ('text / image / console 调用次数', 'text / image / console calls')),
          (f'{fmt_chars(sv)} chars', ('单个 store 值的 JSON', 'JSON of one store value')),
          (f'{fmt_chars(st)} chars', ('全部 store 的 key + JSON', 'keys + JSON of the whole store')),
          (f'{to:,} ms', ('默认截止时间（含工具耗时）', 'default deadline (tool time included)')),
          ('memoryLimitBytes', ('默认不限（wasm32 上限 4 GiB）', 'default: none (wasm32 caps at 4 GiB)')),
          ('MAX_STACK_SIZE', ('深递归 → 可捕获的 RangeError', 'deep recursion → a catchable RangeError'))]
    for i, (a, b) in enumerate(LM):
        y = 100 + i * 56
        f.chip(752, y, a, 'err', size=10.5, h=22, cls='solid' if i < 4 else '')
        f.text(752, y + 40, b, 9.8, 450, cls='muted', layer='label')
    # lockdown
    f.group(16, 524, 1088, 92, 'infra', ('lockdown：先冻结，再运行脚本', 'lockdown: freeze first, then run the script'), None, 'x', title_mono=False, gid='ld')
    f.text(32, 574, ('所有内建对象被冻结、内建全局只读——脚本改不了 prelude 赖以序列化的 Array.prototype.toJSON 等。常被覆盖的属性改成访问器：', 'Every built-in is frozen and built-in globals are read-only, so a script cannot patch what the prelude serializes with (e.g. Array.prototype.toJSON). Commonly overridden'), 9.8, 450, cls='muted', layer='label')
    f.text(32, 594, ('constructor · name · message · toString · toLocaleString · valueOf · toJSON，在实例上赋值仍然可用（如 Error 子类里 this.name = …）。', 'properties (constructor · name · message · toString · toLocaleString · valueOf · toJSON) become accessors, so assigning them on instances still works.'), 9.8, 450, cls='muted', layer='label')
    f.text(32, 632, (f'保留名（不能注册为 global）：{" · ".join(R)}', f'Reserved names (cannot be globals): {" · ".join(R)}'), 9.5, 500, cls='faint', layer='label')
    return f

# ============================================================== cm_types : the public types + source format
@reg
def cm_types():
    has('source.ts', 'export const CODEMODE_OPTIONS_PREFIX = "// @options:";', 'const SUPPORTED_FIELDS = ["max_output_tokens", "timeout_ms"] as const;', 'const MAX_TIMEOUT_MS = 2_147_483_647;', 'start: options_source | plain_source')
    def mem(name):
        m = re.search(r'^export interface ' + name + r'\b[^{]*\{(.*?)^\}', _src('types.ts'), re.M | re.S)
        return [x for x in dict.fromkeys(re.findall(r'^\t([a-zA-Z]+\??)[(:]', m.group(1), re.M))]
    f = Fig('cm_types', 1120, 620, ('公共类型与脚本源码格式', 'Public types and the script source format'))
    E = f.edge
    h1 = uml(f, 'tool', 16, 52, 340, 'ext', 'CodemodeTool', '«interface»', [['+' + m for m in mem('CodemodeTool')]])
    h2 = uml(f, 'ctx', 16, 52 + h1 + 20, 340, 'ext', 'CodemodeToolContext', '«interface»', [['+' + m for m in mem('CodemodeToolContext')]])
    h3 = uml(f, 'opt', 376, 52, 340, 'infra', 'CodemodeSandboxOptions', '«interface»', [['+' + m for m in mem('CodemodeSandboxOptions')]])
    h4 = uml(f, 'eo', 376, 52 + h3 + 20, 340, 'infra', 'CodemodeExecuteOptions', '«interface»', [['+' + m for m in mem('CodemodeExecuteOptions')]])
    h5 = uml(f, 'res', 736, 52, 368, 'coding', 'CodemodeResult', '«union»', [['+ok: true', '|value · output · calls · storeWrites'], ['+ok: false', '|error · output · calls']])
    h6 = uml(f, 'err', 736, 52 + h5 + 20, 368, 'err', 'CodemodeError', '«interface»', [['+kind: ' + ' | '.join(f'"{k}"' for k in err_kinds()), '+name? · message · stack?']])
    h7 = uml(f, 'call', 736, 52 + h5 + h6 + 40, 368, 'coding', 'CodemodeCall', '«interface»', [['+name · durationMs', '+status: "ok" | "error" | "cancelled"']])
    yb = max(52 + h1 + 20 + h2, 52 + h3 + 20 + h4, 52 + h5 + h6 + h7 + 40) + 24
    f.group(16, yb, 1088, 168, 'tui', ('脚本源码格式（source.ts）', 'Script source format (source.ts)'), 'parseCodemodeSource()', 'file', title_mono=False, gid='src')
    codebox(f, 32, yb + 46, 520, [(0, '// @options: {"max_output_tokens": 2000, "timeout_ms": 30000}', 'strongt'),
                                  (0, 'const r = await tools.read({ path: "package.json" });', 'muted'), (0, 'text(JSON.parse(r).name);', 'muted')], ('示例', 'EXAMPLE'), 10, 18)
    f.text(576, yb + 64, ('可选的第一行只认两个字段：', 'The optional first line accepts two fields only:'), 10, 600, cls='strongt', layer='label')
    f.text(576, yb + 84, ('max_output_tokens：非负安全整数', 'max_output_tokens: a non-negative safe integer'), 9.8, 450, cls='muted', layer='label')
    f.text(576, yb + 102, ('timeout_ms：1 … 2,147,483,647（setTimeout 上限）', 'timeout_ms: 1 … 2,147,483,647 (the setTimeout cap)'), 9.8, 450, cls='muted', layer='label')
    f.text(576, yb + 124, ('该行被替换成空行，行号保持不变；其他字段或坏 JSON → CodemodeSourceError。', 'The line is blanked so line numbers stay put; other fields or bad JSON → CodemodeSourceError.'), 9.5, 450, cls='faint', layer='label')
    f.text(576, yb + 142, ('CODEMODE_SOURCE_GRAMMAR：给支持语法约束的模型的 Lark 语法。', 'CODEMODE_SOURCE_GRAMMAR: a Lark grammar for grammar-constrained models.'), 9.5, 450, cls='faint', layer='label')
    assert yb + 168 < 576, yb
    f.legend(24, 600, [('layer:ext', ('工具', 'tools')), ('layer:infra', ('选项', 'options')), ('layer:coding', ('结果', 'results')), ('layer:err', ('错误', 'errors'))])
    return f

def _ts(schema):
    """Port of declarations.ts toType() for the subset used in the example (object/string/number/boolean, no $ref, no descriptions)."""
    t = schema.get('type')
    if t == 'string': return 'string'
    if t in ('number', 'integer'): return 'number'
    if t == 'boolean': return 'boolean'
    if t == 'object':
        props = schema.get('properties', {}); req = set(schema.get('required', []))
        mem = [f'{k}{"" if k in req else "?"}: {_ts(props[k])};' for k in sorted(props)]
        return '{ ' + ' '.join(mem) + ' }'
    return 'unknown'
def _ident(name):
    out = ''
    for ch in name:
        ok = re.match(r'[A-Za-z_$]', ch) if out == '' else re.match(r'[A-Za-z0-9_$]', ch)
        out += ch if ok else '_'
    return out or '_'

# ============================================================== cm_decl : schemas → TypeScript declarations
@reg
def cm_decl():
    D = 'declarations.ts'
    has(D, 'sections.push(`declare const tools: {\\n${members.join("\\n")}\\n};`);', 'return `${toCodemodeIdentifier(tool.name)}(args: ${input}): Promise<${renderToolOutputType(tool.outputSchema)}>;`;',
        'const names = Object.keys(properties).sort();', 'members.push("[key: string]: unknown;");', 'context.expansions >= MAX_REF_EXPANSIONS', 'return type === "unknown" ? "CallToolResult" : `CallToolResult<${type}>`;',
        'sections.push(`declare const ${namespace}: {\\n${members.join("\\n")}\\n};`);', 'if (lines.length === 1) return `${indent}/** ${lines[0]} */\\n`;')
    mx = num(D, 'DEFAULT_INPUT_SCHEMA_MAX_CHARS'); mr = num(D, 'MAX_REF_EXPANSIONS')
    tool = dict(name='mcp__docs__search-pages', description='Search the documentation.', inputSchema=dict(type='object', properties=dict(query=dict(type='string'), limit=dict(type='integer')), required=['query']))
    sig = f'{_ident(tool["name"])}(args: {_ts(tool["inputSchema"])}): Promise<unknown>;'
    f = Fig('cm_decl', 1120, 616, ('给模型看的 API：JSON Schema → TypeScript 声明', 'The API the model sees: JSON Schema → TypeScript declarations'))
    E = f.edge
    js = json.dumps(tool['inputSchema'])
    codebox(f, 16, 56, 420, [(0, '{', 'muted'), (1, f'name: "{tool["name"]}",', 'strongt'), (1, f'description: "{tool["description"]}",', 'muted'),
                             (1, 'inputSchema: {', 'muted'), (2, 'type: "object",', 'muted'), (2, 'properties: {', 'muted'), (3, 'query: { type: "string" },', 'muted'), (3, 'limit: { type: "integer" }', 'muted'),
                             (2, '},', 'muted'), (2, 'required: ["query"]', 'muted'), (1, '}', 'muted'), (0, '}', 'muted')], ('CodemodeTool（宿主注册）', 'CodemodeTool (registered by the host)'), 10, 17)
    f.node('rd', 460, 140, 190, 64, 'coding', 'renderDeclarations()', ('{ tools, globals }', '{ tools, globals }'), 'code', tsize=11, ssize=9.5, strong=True)
    E([(436, 172), (460, 172)], None, 'rd', 'main', 'coding')
    codebox(f, 674, 56, 430, [(0, 'declare const tools: {', 'muted'), (1, f'/** {tool["description"]} */', 'faint'), (1, sig.split('(args')[0] + '(', 'strongt'),
                              (2, 'args: ' + _ts(tool['inputSchema']), 'strongt'), (1, '): Promise<unknown>;', 'strongt'), (0, '};', 'muted')], ('输出（换行仅为排版）', 'OUTPUT (line breaks added for layout)'), 10, 17)
    E([(650, 172), (674, 172)], 'rd', None, 'main', 'coding')
    f.text(674, 210, ('"-" 不是合法标识符字符 → "_"（toCodemodeIdentifier）', '"-" is not an identifier character → "_" (toCodemodeIdentifier)'), 9.5, 450, cls='muted', layer='label')
    f.text(674, 228, ('属性按名字排序；不在 required 里 → 可选（?）', 'properties are sorted; not in required → optional (?)'), 9.5, 450, cls='muted', layer='label')
    f.text(674, 246, ('脚本里两种写法都行：tools.mcp__docs__search_pages(…)', 'scripts may call either tools.mcp__docs__search_pages(…)'), 9.5, 450, cls='muted', layer='label')
    f.text(674, 264, ('或 tools["mcp__docs__search-pages"](…)', 'or tools["mcp__docs__search-pages"](…)'), 9.5, 450, cls='muted', layer='label')
    # rules
    f.group(16, 314, 1088, 248, 'coding', ('schemaToType() 的规则', 'schemaToType() rules'), None, 'braces', title_mono=False, gid='r')
    RL = [(('标量', 'scalars'), ('string · number / integer → number · boolean · null', 'string · number / integer → number · boolean · null')),
          (('字面量', 'literals'), ('const → 字面量；enum → 字面量联合', 'const → a literal; enum → a union of literals')),
          (('组合', 'combinators'), ('anyOf / oneOf → A | B；allOf → A & B（含 unknown 的部分丢弃）', 'anyOf / oneOf → A | B; allOf → A & B (unknown parts dropped)')),
          (('对象', 'objects'), ('无属性且无 additionalProperties → [key: string]: unknown；属性有 description → // 注释', 'no properties or additionalProperties → [key: string]: unknown; described properties → // comments')),
          (('数组', 'arrays'), ('items → Array<T>；prefixItems → [A, B]；都没有 → unknown[]', 'items → Array<T>; prefixItems → [A, B]; neither → unknown[]')),
          ('$ref', (f'只解析本地 #/…；每个 schema 最多展开 {mr} 次，递归 → unknown', f'local #/… only; at most {mr} expansions per schema, recursion → unknown')),
          (('长度', 'size'), (f'输入类型超过 {mx:,} 个字符 → 整个变成 unknown', f'an input type over {mx:,} characters → unknown altogether')),
          ('MCP', ('outputSchema 形如 CallToolResult → Promise<CallToolResult<T>>，需附 MCP_TYPESCRIPT_PREAMBLE', 'an outputSchema shaped like CallToolResult → Promise<CallToolResult<T>>, with MCP_TYPESCRIPT_PREAMBLE')),
          ('globals', ('name → declare function；ns.member → declare const ns: { … }；signature 可直接给出', 'name → declare function; ns.member → declare const ns: { … }; signature overrides'))]
    for i, (k, v) in enumerate(RL):
        y = 360 + i * 22
        f.text(32, y + 10, k, 10, 700, isinstance(k, str), cls='strongt', layer='label')
        f.text(150, y + 10, v, 9.8, 450, cls='muted', layer='label')
    f.legend(24, 594, [('layer:coding', ('模型可见的文本', 'model-facing text')), ('main', ('渲染', 'render'))])
    return f

# ============================================================== cm_pi : how coding-agent uses it
@reg
def cm_pi():
    has_ca('index.ts', '`codemode` is registered inactive.')
    has_ca('tool.ts', 'exposure: "model-only"', 'constrainedSampling: { type: "grammar", variants: { openai_lark: CODEMODE_SOURCE_GRAMMAR } }', 'export const CODEMODE_STORE_ENTRY_TYPE = "codemode-store";',
           'Only the script\'s output reaches the model; nested results do not.', 'The sandbox (worker, QuickJS wasm) loads on the first call, not at startup.')
    has_ca('execute.ts', 'await ctx.executeTool(tool.name, args, { signal: callSignal })', 'timeoutMs: sourceOptions.timeoutMs ?? Number.POSITIVE_INFINITY', 'if (tool.outputSchema && result.structuredContent !== undefined) return result.structuredContent;',
           'name: "searchTools"', 'name: "describeTool"', 'name: "describeNamespace"', 'const ranker = new Bm25Ranker();')
    mem = num(None, 'CODEMODE_MEMORY_LIMIT_BYTES', _ca('execute.ts')); mo = num(None, 'DEFAULT_MAX_OUTPUT_TOKENS', _ca('execute.ts')); mc = num(None, 'MAX_CONCURRENT_MODEL_CALLS', _ca('execute.ts'))
    ib = int(re.search(r'DEFAULT_CODEMODE_INLINE_BUDGET = (\d+)', _ca('tool.ts')).group(1))
    n = total_loc(CAC)
    f = Fig('cm_pi', 1120, 660, ('pi 怎样使用 pi-codemode：coding-agent 的 codemode 工具', 'How pi uses pi-codemode: coding-agent\'s codemode tool'))
    E = f.edge
    f.node('m', 16, 56, 220, 52, 'modes', ('模型', 'the model'), ('写一段 JavaScript', 'writes JavaScript'), 'spark', mono=False)
    f.node('cm', 290, 56, 380, 52, 'coding', 'codemode(source)', ('exposure: "model-only"：脚本不能再启动脚本', 'exposure: "model-only": scripts cannot start scripts'), 'code', tsize=11.5, ssize=9.5, strong=True)
    f.node('sb', 724, 56, 380, 52, 'ext', 'new CodemodeSandbox({ tools, globals })', (f'每次调用新建 · memoryLimit {mem // (1024*1024)} MiB', f'new per call · memoryLimit {mem // (1024*1024)} MiB'), 'shield', tsize=10.5, ssize=9.5)
    E([(236, 82), (290, 82)], 'm', 'cm', 'main', 'coding'); E([(670, 82), (724, 82)], 'cm', 'sb', 'main', 'ext')
    # what scripts call
    f.group(16, 128, 530, 268, 'coding', ('脚本可调用的工具', 'Tools a script can call'), None, 'tool', title_mono=False, gid='t')
    f.text(32, 176, ('当前激活的 direct 工具 + 所有 codemode / deferred 曝光的工具（多为 MCP）', 'active direct tools + every codemode / deferred-exposure tool (mostly MCP)'), 9.8, 450, cls='muted', layer='label')
    f.node('et', 32, 192, 498, 52, 'coding', 'ctx.executeTool(name, args, { signal })', ('经过 agent 循环的工具管线：校验 · tool_call / tool_result 钩子 · 权限', 'through the agent loop\'s pipeline: validation · tool_call / tool_result hooks · permissions'), None, tsize=10.5, ssize=9.5, strong=True)
    f.text(32, 270, ('嵌套结果怎样交给脚本：', 'How nested results reach the script:'), 10, 650, cls='strongt', layer='label')
    f.text(32, 290, ('有 outputSchema → structuredContent（MCP 工具 → CallToolResult，含 isError）', 'has outputSchema → structuredContent (MCP tools → CallToolResult, incl. isError)'), 9.5, 450, cls='muted', layer='label')
    f.text(32, 308, ('否则 → 文本内容拼成一个字符串', 'otherwise → its text content as one string'), 9.5, 450, cls='muted', layer='label')
    f.text(32, 326, ('失败 / 被阻止 / 参数无效 → reject(Error(错误文本))', 'failed / blocked / invalid → reject(Error(error text))'), 9.5, 450, cls='muted', layer='label')
    f.text(32, 354, ('只有脚本自己的输出回到模型；嵌套结果不会。', 'Only the script\'s own output reaches the model; nested results do not.'), 9.8, 600, cls='strongt', layer='label')
    f.text(32, 374, (f'输出按 max_output_tokens 截断（默认 {mo:,}），完整输出存文件。', f'Output is cut to max_output_tokens (default {mo:,}); the full output is saved to a file.'), 9.5, 450, cls='faint', layer='label')
    E([(400, 108), (400, 128)], 'cm', 't', 'main', 'coding')
    # globals
    f.group(566, 128, 538, 268, 'ext', ('pi 注入的 globals', 'Globals pi injects'), None, 'globe', title_mono=False, gid='g')
    G = [('searchTools(query)', ('BM25 排序搜索可调用工具', 'BM25-ranked search over callable tools')), ('describeTool(name)', ('取一个工具的完整声明', 'one tool\'s full declaration')),
         ('describeNamespace(name)', ('命名空间说明（如 MCP 服务器 instructions）', 'namespace notes (e.g. MCP server instructions)')),
         ('models.*', (f'模型目录 · classify · generateImages；同时最多 {mc} 个', f'model catalog · classify · generateImages; at most {mc} in flight'))]
    for i, (k, v) in enumerate(G):
        y = 176 + i * 50
        f.text(582, y, k, 10.5, 650, True, cls='strongt', layer='label')
        f.text(582, y + 18, v, 9.5, 450, cls='muted', layer='label')
    f.text(582, 380, ('脚本里 load() / store() 同样可用（见下）', 'load() / store() are available too (below)'), 9.5, 450, cls='faint', layer='label')
    E([(914, 108), (914, 128)], 'sb', 'g', 'dep')
    # store + modes
    f.group(16, 416, 530, 180, 'agent', ('store() 的持久化', 'Persisting store()'), None, 'db', title_mono=False, gid='st')
    f.text(32, 462, ('成功的脚本把写入追加为会话条目：', 'Successful scripts append their writes as a session entry:'), 9.8, 450, cls='muted', layer='label')
    f.chip(32, 474, 'customType: "codemode-store" · { set, delete }', 'agent', size=10, h=22)
    f.text(32, 520, ('下一次执行前，从根到当前叶子重放这些条目，得到 load() 的快照——', 'Before the next run, the entries from root to the current leaf are replayed into the load()'), 9.8, 450, cls='muted', layer='label')
    f.text(32, 538, ('因此每个分支只看到自己路径上写入的值。', 'snapshot, so each branch sees only values written on its own path.'), 9.8, 450, cls='muted', layer='label')
    f.text(32, 566, ('超时：只有 // @options 里的 timeout_ms；否则不限（Infinity）。', 'Timeout: only // @options timeout_ms; otherwise none (Infinity).'), 9.5, 450, cls='faint', layer='label')
    f.group(566, 416, 538, 180, 'modes', ('激活与模式', 'Activation and modes'), None, 'gear', title_mono=False, gid='md')
    f.text(582, 462, ('注册时是 inactive；--tools、defaultTools、setActiveTools()，', 'Registered inactive; --tools, defaultTools, setActiveTools(),'), 9.8, 450, cls='muted', layer='label')
    f.text(582, 480, ('或 MCP 扩展（codemode 曝光的服务器）会激活它。', 'or the MCP extension (codemode-exposure servers) activate it.'), 9.8, 450, cls='muted', layer='label')
    f.text(582, 506, ('codemode.mode = "on"（默认）：列出非 direct 的可调用工具', 'codemode.mode = "on" (default): lists the non-direct callable tools'), 9.8, 450, cls='muted', layer='label')
    f.text(582, 524, ('"only"：列出全部，并对模型隐藏 direct 工具的声明', '"only": lists all of them and hides direct tools from the model'), 9.8, 450, cls='muted', layer='label')
    f.text(582, 550, (f'inlineBudget（默认 {ib:,} token）：描述里内联多少声明', f'inlineBudget (default {ib:,} tokens): how many declarations are inlined'), 9.8, 450, cls='muted', layer='label')
    f.text(582, 576, ('支持的 provider 用 Lark 语法约束采样：脚本按原文输出。', 'Providers with grammar sampling use the Lark grammar: scripts come out as raw text.'), 9.5, 450, cls='faint', layer='label')
    f.legend(24, 636, [('layer:coding', 'coding-agent'), ('layer:ext', 'pi-codemode'), ('layer:agent', ('会话', 'session'))])
    f.note(1096, 636, (f'extensions/codemode/：{n:,} 行', f'extensions/codemode/: {n:,} lines'), 10.5, anchor='end')
    return f
