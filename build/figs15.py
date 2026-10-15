"""pi-telemetry deep-dive diagrams (tel_*). Facts read from /workspace/pi-src/packages/telemetry (and its pi-ai user) at build time."""
import re
from svgkit import Fig, maxw, pair
from figs import reg
from figkit import SRC, uml, codebox, bar, dot, hline, vline, chiprow, lines_of
from pkgsrc import Pkg, users_of

T_ = Pkg('packages/telemetry/src/')
README = (SRC / 'packages/telemetry/README.md').read_text()

def doc(*needles):
    for n in needles: assert n in README, n

def idx_exports():
    """(values, types) declared in or re-exported from index.ts."""
    s = T_.src('index.ts')
    vals = re.findall(r'^export (?:function|const|class) (\w+)', s, re.M)
    types = re.findall(r'^export (?:type|interface) (\w+)', s, re.M)
    for m in re.finditer(r'^export (type )?\{([^}]*)\} from', s, re.M):
        names = [n.strip() for n in m.group(2).split(',') if n.strip()]
        (types if m.group(1) else vals).extend(names)
    return vals, types

def conformance_cases():
    s = T_.src('testing/conformance.ts')
    return re.findall(r'createCase\(\s*factory,\s*"([^"]+)",\s*"([^"]+)"', s)

# ============================================================== tel_arch
@reg
def tel_arch():
    tot = T_.total()
    j = T_.pkg()
    assert list(j['exports']) == ['.', './testing'], j['exports']
    assert not j.get('dependencies'), j.get('dependencies')
    users = dict(users_of('@earendil-works/pi-telemetry'))
    assert set(users) == {'ai'}, users
    T_.has('index.ts', 'export { NOOP_TELEMETRY_CONTEXT } from "./noop.ts";', 'export { InMemoryTelemetryContext } from "./memory.ts";')
    T_.has('memory.ts', 'if (parent?.settled) return NOOP_TELEMETRY_CONTEXT.startSpan(options, callback);')
    T_.has('testing/index.ts', 'export { createTelemetryAdapterConformance } from "./conformance.ts";')
    T_.has('testing/conformance.ts', 'from "node:assert/strict";')
    agent_src = ''.join(p.read_text() for p in (SRC / 'packages/agent/src').rglob('*.ts'))
    doc('AGENT_TELEMETRY_SCHEMAS', '`@earendil-works/pi-agent-core` owns and exports the pi AI-request and harness schemas')
    assert 'AGENT_TELEMETRY_SCHEMAS' not in agent_src and 'pi-telemetry' not in agent_src
    ca_tel = (SRC / 'packages/coding-agent/src/core/telemetry.ts').read_text()
    assert 'process.env.PI_TELEMETRY' in ca_tel and 'pi-telemetry' not in ca_tel
    vals, types = idx_exports()
    f = Fig('tel_arch', 1120, 580, (f'pi-telemetry：{tot:,} 行，契约 + 两个参考实现 + 一套一致性测试', f'pi-telemetry: {tot:,} lines — a contract, two reference contexts and a conformance suite'))
    E = f.edge
    f.group(16, 52, 660, 440, 'infra', 'packages/telemetry/src', None, 'layers', gid='l')
    f.node('ix', 32, 92, 628, 50, 'infra', 'index.ts', ('契约类型 · schema 定义与类型推导 · createTypedSpanStarter · 重新导出两个 context', 'contract types · schema definitions and inference · createTypedSpanStarter · re-exports both contexts'), None, tsize=10.8, ssize=8.8, tag=f'{T_.loc("index.ts")}', strong=True)
    f.node('no', 32, 186, 200, 64, 'infra', 'noop.ts', ('NOOP_TELEMETRY_CONTEXT', 'NOOP_TELEMETRY_CONTEXT'), None, tsize=10.8, ssize=8.6, sub2=('一个冻结的惰性 span', 'one frozen inert span'), tag=f'{T_.loc("noop.ts")}')
    f.node('me', 260, 186, 186, 64, 'infra', 'memory.ts', ('InMemoryTelemetryContext', 'InMemoryTelemetryContext'), None, tsize=10.8, ssize=8.6, sub2=('确定性的内存记录', 'deterministic recording'), tag=f'{T_.loc("memory.ts")}')
    E([(132, 142), (132, 186)], 'ix', 'no', 'dep', 'infra', label=('再导出', 're-export'), lpos=(132, 164), lmono=False, lsize=9.0)
    E([(352, 142), (352, 186)], 'ix', 'me', 'dep', 'infra', label=('再导出', 're-export'), lpos=(352, 164), lmono=False, lsize=9.0)
    E([(260, 218), (232, 218)], 'me', 'no', 'dep', 'infra')
    f.text(32, 270, ('父 span 已结束或记录失败时，memory.ts 退回 NOOP 上下文。', 'memory.ts falls back to the NOOP context when the parent has settled or recording fails.'), 8.8, 450, cls='muted', layer='label')
    f.group(462, 172, 198, 304, 'coding', 'testing/', ('./testing', './testing'), None, dashed=True, gid='tg')
    TF = [('index.ts', ('子路径入口', 'subpath entry')), ('types.ts', ('Fixture · Case 类型', 'Fixture · Case types')), ('conformance.ts', ('9 个用例 · node:assert', '9 cases · node:assert'))]
    for i, (p, d) in enumerate(TF):
        f.node(f't{i}', 474, 212 + i * 58, 174, 48, 'coding', p, d, None, tsize=10.2, ssize=8.6, tag=f'{T_.loc("testing/" + p)}')
    f.text(474, 400, ('只有这里用 Node 的', 'Only this subpath uses'), 8.8, 450, cls='muted', layer='label')
    f.text(474, 416, ('断言 API；根包保持', 'Node assertion APIs; the'), 8.8, 450, cls='muted', layer='label')
    f.text(474, 432, ('运行时无关。', 'root stays runtime-neutral.'), 8.8, 450, cls='muted', layer='label')
    f.text(32, 312, (f'根入口导出 {len(vals)} 个值', f'The root exports {len(vals)} values'), 9.6, 650, cls='strongt', layer='label')
    assert len(vals) == 4, vals
    chiprow(f, 32, 322, vals[:2], 'infra', size=9.0, h=20, gap=5)
    chiprow(f, 32, 346, vals[2:], 'infra', size=9.0, h=20, gap=5)
    f.text(32, 390, (f'… 和 {len(types)} 个类型，例如', f'… and {len(types)} types, such as'), 9.6, 650, cls='strongt', layer='label')
    chiprow(f, 32, 400, ['TelemetryContext', 'TelemetrySpan', 'SpanStatus'], 'infra', size=9.0, h=20, gap=5)
    chiprow(f, 32, 426, ['TelemetrySchemaDefinition', 'TypedSpanStarter'], 'agent', size=9.0, h=20, gap=5)
    chiprow(f, 32, 452, ['SchemaTelemetrySpan', 'Infer*Attributes'], 'agent', size=9.0, h=20, gap=5)
    # right column
    f.group(692, 52, 412, 440, 'ai', ('依赖与使用者', 'Dependencies and users'), None, 'hub', title_mono=False, gid='r')
    f.text(708, 100, ('运行时依赖', 'Runtime dependencies'), 9.6, 650, cls='faint', layer='label', ls='.04em')
    f.text(708, 120, ('无：package.json 只有 devDependencies（@types/node、vitest）', 'none: package.json has only devDependencies (@types/node, vitest)'), 9.0, 450, cls='muted', layer='label')
    f.text(708, 152, ('被导入（src 中导入它的文件数）', 'Imported by (files in src)'), 9.6, 650, cls='faint', layer='label', ls='.04em')
    f.node('ai', 708, 162, 380, 56, 'ai', 'pi-ai', ('ProviderRequestOptions.telemetryContext', 'ProviderRequestOptions.telemetryContext'), None, tsize=10.6, ssize=8.8, sub2=('只传递，不拥有任何 schema', 'propagates it; owns no schema'), tag=f'{users["ai"]}')
    f.text(708, 246, ('README 里写到、但 v1.1.0 源码里没有', 'In the README, but not in the v1.1.0 source'), 9.6, 650, cls='faint', layer='label', ls='.04em')
    f.node('ag', 708, 256, 380, 56, 'agent', 'pi-agent-core', ('AGENT_TELEMETRY_SCHEMAS · startAiSpan …', 'AGENT_TELEMETRY_SCHEMAS · startAiSpan …'), None, tsize=10.6, ssize=8.8, kind='ghost', sub2=('agent-core 既不依赖也不导出它们', 'agent-core neither depends on nor exports them'))
    f.text(708, 340, ('同名但无关', 'Same name, unrelated'), 9.6, 650, cls='faint', layer='label', ls='.04em')
    f.node('ca', 708, 350, 380, 56, 'coding', 'coding-agent · core/telemetry.ts', ('安装遥测：PI_TELEMETRY 或设置项', 'install telemetry: PI_TELEMETRY or a setting'), None, tsize=10.4, ssize=8.8, sub2=('不导入 pi-telemetry', 'does not import pi-telemetry'))
    f.text(708, 436, ('pi-telemetry 只定义契约；', 'pi-telemetry only defines the contract;'), 9.0, 450, cls='muted', layer='label')
    f.text(708, 452, ('导出到 OpenTelemetry、Sentry 等由适配器负责。', 'exporting to OpenTelemetry, Sentry … is the adapter\'s job.'), 9.0, 450, cls='muted', layer='label')
    doc('An adapter translates these generic concepts into the corresponding concepts used by OpenTelemetry, Sentry, logs, or another backend.')
    f.text(16, 518, ('CHANGELOG：整个包在 0.84.0 一次性加入（回调式上下文契约、no-op、内存参考适配器、一致性套件、类型化 schema）；1.1.0 没有新条目。', 'CHANGELOG: the whole package arrived in 0.84.0 (callback context contract, no-op, in-memory reference adapter, conformance suite, typed schemas); 1.1.0 has no entries.'), 9.2, 450, cls='muted', layer='label')
    cl = (SRC / 'packages/telemetry/CHANGELOG.md').read_text()
    assert '## [0.84.0]' in cl and 'Added the callback-based telemetry context contract' in cl
    f.legend(24, 552, [('layer:infra', ('契约与参考实现', 'contract & reference contexts')), ('layer:coding', ('./testing', './testing')), ('layer:ai', ('使用者', 'users')), ('dep', ('导出 / 回退', 'export / fallback'))])
    f.note(1096, 552, ('标签 = 行数 / 文件数', 'tag = lines / files'), 10.5, anchor='end')
    return f

# ============================================================== tel_model : concepts + core types
@reg
def tel_model():
    s = T_.src('index.ts')
    for n in ['export type AttributeValue = string | number | boolean | readonly string[] | readonly number[] | readonly boolean[];',
              'startSpan<T>(options: SpanOptions, callback: (span: TelemetrySpan) => T | Promise<T>): Promise<T>;',
              'export interface TelemetrySpan extends TelemetryContext {', 'addEvent(name: string, attributes?: SpanAttributes): void;',
              'setAttributes(attributes: SpanAttributes): void;', 'setStatus(status: SpanStatus): void;',
              'export type SpanStatus = { status: "ok" } | { status: "error"; error?: { name: string; message: string } };',
              '[name: string]: AttributeValue | undefined;']:
        assert n in s, n
    doc('example.account.load                         span', '├─ event: example.cache.lookup              occurrence during the span',
        'There is no public `end()` method.', 'A span is diagnostic data, not business state.')
    f = Fig('tel_model', 1120, 560, ('模型：span 树、属性、事件、状态；TelemetrySpan 本身就是子 span 的上下文', 'The model: a span tree with attributes, events and status; a TelemetrySpan is itself the context for children'))
    E = f.edge
    f.group(16, 52, 520, 420, 'infra', ('一次运行产生的遥测（README 的例子）', 'Telemetry from one run (the README example)'), None, 'tree', title_mono=False, gid='ex')
    f.node('ctx', 36, 96, 220, 40, 'ai', 'telemetryContext', ('调用方传进来的父上下文', 'the parent passed in by the caller'), None, tsize=10.4, ssize=8.6)
    f.node('sp', 36, 172, 480, 52, 'infra', 'example.account.load', ('span：一次操作的计时记录', 'span: a timed record of one operation'), 'clock', tsize=10.8, ssize=8.8, strong=True, tag='span')
    E([(146, 136), (146, 172)], 'ctx', 'sp', 'main', 'infra', label='startSpan()', lpos=(146, 154), lsize=9.0)
    R = [('attributes', 'account.id=123 · found=true', ('关于 span 的事实', 'facts about the span'), 'infra'),
         ('event', 'example.cache.lookup { cache.hit: false }', ('span 期间的一个时刻', 'a moment during the span'), 'ext'),
         ('status', 'ok', ('最终结果：ok 或 error', 'the outcome: ok or error'), 'modes'),
         ('child span', 'example.db.query', ('span.startSpan() → 子节点', 'span.startSpan() → a child'), 'infra')]
    for i, (k, v, d, ly) in enumerate(R):
        y = 252 + i * 50
        f.node(f'r{i}', 76, y, 440, 40, ly, v, d, None, tsize=9.8, ssize=8.4, tag=k)
        E([(56, 224), (56, y + 20), (76, y + 20)] if i == 0 else [(56, y - 30), (56, y + 20), (76, y + 20)], 'sp', f'r{i}', 'dep', ly, arrow=True)
    f.text(36, 460, ('子 span 只能经由显式传下去的父 span 创建：没有环境上下文（AsyncLocalStorage）。', 'Children are created only through the explicitly passed parent span: no ambient context (AsyncLocalStorage).'), 8.8, 450, cls='muted', layer='label')
    # right: UML
    f.group(552, 52, 552, 420, 'infra', ('核心类型（index.ts）', 'Core types (index.ts)'), None, 'braces', title_mono=False, gid='ty')
    uml(f, 'tc', 568, 92, 520, 'infra', 'TelemetryContext', '«interface»', [['startSpan<T>(options, callback): Promise<T>']])
    uml(f, 'ts', 568, 184, 520, 'infra', 'TelemetrySpan', '«interface» extends TelemetryContext', [['addEvent(name, attributes?): void', 'setAttributes(attributes): void', 'setStatus(status): void']])
    E([(828, 184), (828, 151)], 'ts', 'tc', 'dep', 'infra', emark='tri')
    uml(f, 'so', 568, 316, 252, 'infra', 'SpanOptions', None, [['name: string', 'attributes?: SpanAttributes']])
    uml(f, 'st', 836, 316, 252, 'modes', 'SpanStatus', '«union»', [['{ status: "ok" }', '{ status: "error";', '  error?: { name, message } }']])
    f.text(568, 436, ('AttributeValue = string | number | boolean | 三种只读数组', 'AttributeValue = string | number | boolean | three readonly arrays'), 9.0, 500, cls='strongt', layer='label')
    f.text(568, 454, ('SpanAttributes = { [name]: AttributeValue | undefined }', 'SpanAttributes = { [name]: AttributeValue | undefined }'), 9.0, 500, True, cls='muted', layer='label')
    f.text(16, 500, ('没有公开的 end()：startSpan() 拥有结束时机——回调的值或 promise 落定时 span 才结束。span 是诊断数据，不是业务状态：记录与否不能改变业务结果。', 'There is no public end(): startSpan() owns settlement — the span ends when the callback\'s value or promise settles. A span is diagnostic data, not business state: recording must not change the outcome.'), 9.0, 450, cls='muted', layer='label')
    f.legend(24, 536, [('layer:infra', ('span 与契约', 'spans & contract')), ('layer:ext', ('事件', 'event')), ('layer:modes', ('状态', 'status')), ('main', ('开始 span', 'start a span')), ('dep', ('包含', 'contains'))])
    return f

# ============================================================== tel_lifecycle : one startSpan call
@reg
def tel_lifecycle():
    m = T_.src('memory.ts')
    for n in ['if (parent?.settled) return NOOP_TELEMETRY_CONTEXT.startSpan(options, callback);', 'recordedSpan = createSpan(state, parent, options);',
              'result = callback(span);', 'settleSpan(state, recordedSpan, true, error);\n\t\treturn Promise.reject(error);',
              'if (failed && !span.explicitStatus) span.status = automaticErrorStatus(error);', 'span.endSequence = state.nextEndSequence++;',
              'if (recordedSpan.settled) return;', 'recordedSpan.explicitStatus = true;', 'return { status: "error", error: { name: error.name, message: error.message } };']:
        assert n in m, n
    T_.has('noop.ts', 'return Promise.resolve(callback(noopTelemetrySpan));', 'return Promise.reject(error);', 'Object.freeze(noopTelemetrySpan);')
    f = Fig('tel_lifecycle', 1120, 600, ('一次 startSpan()：同步进入回调一次，回调落定时 span 才结束', 'One startSpan(): the callback runs once, synchronously; the span ends when it settles'))
    E = f.edge
    f.node('call', 16, 96, 180, 44, 'ai', 'startSpan(opts, cb)', None, None, kind='pill', align='center', tsize=10.6)
    f.node('chk', 236, 92, 196, 52, 'infra', ('父 span 已结束？', 'Parent settled?'), ('或 createSpan 抛错', 'or createSpan throws'), None, mono=False, kind='dec', tsize=10.4, ssize=8.6)
    f.node('rec', 472, 92, 220, 52, 'infra', 'createSpan()', ('复制属性 · id = nextSpanId++', 'copy attributes · id = nextSpanId++'), None, tsize=10.6, ssize=8.6)
    f.node('run', 732, 92, 372, 52, 'infra', 'callback(span)', ('同步调用，恰好一次；span 打开', 'called synchronously, exactly once; span open'), 'play', tsize=10.8, ssize=8.8, strong=True)
    E([(196, 118), (236, 118)], 'call', 'chk', 'main', 'infra')
    E([(432, 118), (472, 118)], 'chk', 'rec', 'main', 'infra', label=('否', 'no'), lpos=(452, 104), lmono=False, lsize=9)
    E([(692, 118), (732, 118)], 'rec', 'run', 'main', 'infra')
    f.node('noop', 236, 196, 196, 48, 'term', 'NOOP_TELEMETRY_CONTEXT', ('回调照常执行，不记录', 'callback still runs, nothing recorded'), None, tsize=9.6, ssize=8.4)
    E([(334, 144), (334, 196)], 'chk', 'noop', 'dep', 'infra', label=('是', 'yes'), lpos=(334, 170), lmono=False, lsize=9)
    # outcomes
    f.node('ok', 600, 236, 240, 56, 'coding', ('返回值 / promise 兑现', 'Returns / promise resolves'), ('status 保持 ok（除非显式设置）', 'status stays ok (unless set explicitly)'), 'check', mono=False, tsize=10.4, ssize=8.6)
    f.node('er', 864, 236, 240, 56, 'err', ('同步抛错 / promise 拒绝', 'Throws / promise rejects'), ('自动 error { name, message }', 'automatic error { name, message }'), 'x', mono=False, tsize=10.4, ssize=8.6)
    E([(800, 144), (800, 190), (720, 190), (720, 236)], 'run', 'ok', 'main', 'coding')
    E([(1000, 144), (1000, 190), (984, 190), (984, 236)], 'run', 'er', 'err', 'err')
    f.node('set', 600, 340, 504, 52, 'modes', 'settleSpan()', ('settled = true · endSequence = nextEndSequence++ · 只执行一次', 'settled = true · endSequence = nextEndSequence++ · runs once'), 'flag', tsize=10.8, ssize=8.8)
    E([(720, 292), (720, 340)], 'ok', 'set', 'main', 'modes')
    E([(984, 292), (984, 340)], 'er', 'set', 'err', 'modes')
    f.node('res', 600, 440, 504, 52, 'ai', ('返回的 promise', 'The returned promise'), ('以同一个值兑现，或以同一个值拒绝（同步抛错也变成拒绝）', 'resolves with the same value or rejects with the same value (a sync throw becomes a rejection)'), None, mono=False, tsize=10.4, ssize=8.6)
    E([(852, 392), (852, 440)], 'set', 'res', 'main', 'ai')
    # left: span open / after settle
    f.group(16, 280, 560, 212, 'infra', ('span 的方法', 'Span methods'), None, 'tool', title_mono=False, gid='mt')
    MT = [('setAttributes(a)', ('合并；后写的定义值覆盖，undefined 被忽略', 'merge; later defined values win, undefined ignored')),
          ('addEvent(name, a?)', ('按顺序追加事件', 'append an event, in order')),
          ('setStatus(s)', ('最后一次生效；标记 explicitStatus', 'last write wins; marks explicitStatus')),
          ('startSpan(opts, cb)', ('子 span，parentId = 这个 span', 'a child span, parentId = this span'))]
    for i, (a, b) in enumerate(MT):
        y = 328 + i * 30
        f.text(32, y, a, 9.6, 600, True, cls='strongt', layer='label')
        f.text(196, y, b, 9.0, 450, cls='muted', layer='label')
    f.text(32, 456, ('结束之后：前三个方法静默无效；startSpan 走 NOOP（回调仍执行）。', 'After settlement: the first three are silent no-ops; startSpan goes to NOOP (callback still runs).'), 9.0, 600, cls='strongt', layer='label')
    f.text(32, 474, ('任何记录调用都同步、被动、不抛错；坏数据被整体忽略。', 'Every recording call is synchronous, passive, never throws; bad payloads are ignored whole.'), 8.8, 450, cls='muted', layer='label')
    f.text(16, 530, ('显式状态优先：回调先 setStatus({ status: "ok" }) 再抛错，span 仍是 ok；返回 { ok: false } 这类“预期失败”要自己 setStatus(error)。', 'Explicit status wins: setStatus({ status: "ok" }) and then throw, and the span is still ok; an expected failure returned as { ok: false } must setStatus(error) itself.'), 9.0, 450, cls='muted', layer='label')
    f.text(16, 550, ('NOOP 上下文走同样的路径，只是不记录：一个共享的冻结 span，嵌套 span 也用它。', 'The NOOP context follows the same path without recording: one shared frozen span, nested spans included.'), 9.0, 450, cls='muted', layer='label')
    f.legend(24, 582, [('main', ('正常', 'normal')), ('err', ('抛错 / 拒绝', 'throw / reject')), ('layer:infra', ('memory.ts', 'memory.ts')), ('layer:modes', ('结束', 'settlement'))])
    return f

# ============================================================== tel_contract : README rules ↔ conformance cases
@reg
def tel_contract():
    rules = ['create a child span and invoke the callback synchronously, exactly once;',
             'preserve the callback\'s returned value and rejection value, returning a promise rejected with the same value after a synchronous throw;',
             'keep the native span open until a returned promise settles;',
             'treat normal completion as `ok` and throws/rejections as errors unless an explicit status was set;',
             'make repeated `setStatus()` calls last-write-wins;',
             'merge `setAttributes()` calls, with later defined values replacing earlier values and `undefined` ignored;',
             'make recording methods synchronous, passive, and non-throwing;',
             'ignore calls made after settlement;',
             'ignore a failed recording call atomically, suppress backend failures, and still execute the business callback exactly once.']
    doc(*rules)
    cases = conformance_cases()
    assert len(cases) == 9, cases
    groups = []
    for g, _ in cases:
        if g not in groups: groups.append(g)
    assert groups == ['callback lifecycle', 'status', 'recording', 'parentage', 'passivity'], groups
    T_.has('testing/types.ts', 'export interface TelemetryAdapterFixture extends AsyncDisposable {', 'getSpans(): Promise<readonly RecordedTelemetrySpan[]>;')
    T_.has('testing/conformance.ts', 'await using fixture = await factory();', 'function unreadable<T extends object>(value: T): T {')
    f = Fig('tel_contract', 1120, 620, (f'适配器契约：README 的 {len(rules)} 条规则，与 ./testing 的 {len(cases)} 个一致性用例', f'The adapter contract: {len(rules)} rules in the README, {len(cases)} conformance cases in ./testing'))
    f.group(16, 52, 520, 448, 'infra', ('适配器必须……（README · Adapter Contract）', 'An adapter must … (README · Adapter Contract)'), None, 'shield', title_mono=False, gid='ru')
    RZ = [(('同步调用回调，恰好一次', 'Call the callback synchronously, exactly once'), ('并创建子 span', 'and create a child span')),
          (('保留返回值与拒绝值', 'Preserve the return and rejection value'), ('同步抛错 → 以同一个值拒绝的 promise', 'sync throw → a promise rejected with it')),
          (('promise 落定前 span 保持打开', 'Keep the span open until the promise settles'), ('原生 span 的结束由 startSpan 负责', 'startSpan ends the native span')),
          (('正常 → ok，抛错 → error', 'Normal → ok, throw → error'), ('除非已显式设置状态', 'unless a status was set explicitly')),
          (('setStatus 最后一次生效', 'setStatus is last-write-wins'), None),
          (('setAttributes 合并', 'setAttributes merges'), ('后写的定义值覆盖，undefined 忽略', 'later defined values win, undefined ignored')),
          (('记录方法同步、被动、不抛错', 'Recording is synchronous, passive, non-throwing'), None),
          (('结束之后的调用被忽略', 'Calls after settlement are ignored'), None),
          (('失败的记录调用被整体忽略', 'A failed recording call is ignored whole'), ('后端错误被吞掉，业务回调仍只执行一次', 'backend errors suppressed; callback still runs once'))]
    for i, (a, b) in enumerate(RZ):
        y = 98 + i * 44
        f.step(str(i + 1), 40, y - 4, 'infra')
        f.text(60, y, a, 9.8, 600, cls='strongt', layer='label')
        if b: f.text(60, y + 16, b, 8.8, 450, cls='muted', layer='label')
    # right: cases
    f.group(552, 52, 552, 448, 'coding', 'createTelemetryAdapterConformance(factory)', None, 'check', gid='cs')
    covers = {'admits once synchronously and preserves the result': '1 · 2 · 4',
              'preserves synchronous and asynchronous rejection values': '2 · 4',
              'uses last explicit status without automatic overwrite': '4 · 5',
              'merges attributes and records ordered events': '6',
              'ignores failed attribute calls atomically': '9',
              'makes calls after settlement inert': '8',
              'records nested and concurrent child relationships': '1 · 3',
              'suppresses unreadable telemetry payload failures': '7 · 9',
              'ignores failed status calls atomically': '9'}
    assert set(covers) == {n for _, n in cases}, [n for _, n in cases]
    y = 112; last = None
    for g, n in cases:
        if g != last:
            f.text(568, y, g, 9.4, 700, True, cls='faint', layer='label', ls='.04em'); y += 20; last = g
        f.text(580, y, n, 9.2, 500, True, cls='strongt', layer='label')
        f.chip(1088 - maxw(covers[n], 9.0, 600, True) - 14, y - 13, covers[n], 'infra', size=9.0, h=17)
        y += 26
    f.text(568, 482, ('右侧标签 = 用例覆盖的规则编号（本站的对应关系）', 'tag = the rules a case covers (this site\'s mapping)'), 8.6, 450, cls='faint', layer='label')
    # bottom: fixture
    codebox(f, 16, 516, 1088, [
        (0, 'createTelemetryAdapterConformance(async () => ({ context, getSpans: async () => normalizedSpans(), async [Symbol.asyncDispose]() { … } }))', 'strongt'),
        (0, '→ readonly { group, name, run() }[]   ·   注册到任何测试框架：for (group) describe(group, …) · it(name, () => run())', 'muted'),
    ], None, size=9.2, lh=17)
    f.text(16, 580, ('每个用例用 await using 拿一个全新 fixture；getSpans() 可以先 flush 异步导出器。用 Proxy 构造“读取即抛错”的载荷来检验被动性。', 'Each case takes a fresh fixture with await using; getSpans() may flush an async exporter first. Payloads that throw on read (a Proxy) test passivity.'), 9.0, 450, cls='muted', layer='label')
    f.legend(24, 604, [('layer:infra', ('契约规则', 'contract rules')), ('layer:coding', ('一致性用例（按组）', 'conformance cases (by group)'))])
    return f

# ============================================================== tel_memory : the in-memory reference adapter
@reg
def tel_memory():
    m = T_.src('memory.ts')
    for n in ['spans: [],\n\t\tnextSpanId: 1,\n\t\tnextEndSequence: 1,', 'parentId: parent?.id ?? null,', '/** Returns detached snapshots in span-start order. */',
              'explicitStatus: boolean;', 'readonly endSequence?: number;', 'return Array.isArray(value) ? ([...value] as AttributeValue) : value;']:
        assert n in m, n
    c = T_.src('testing/conformance.ts')
    for n in ['parent.startSpan({ name: "first-child" }, async () => {', 'await firstGate;', 'const second = parent.startSpan({ name: "second-child" }, () => "done");',
              'ok(second.endSequence < first.endSequence);', 'ok(first.endSequence < parent.endSequence);']:
        assert n in c, n
    doc('It records no timestamps.', 'storage is unbounded and process-local')
    f = Fig('tel_memory', 1120, 600, ('InMemoryTelemetryContext：确定性的 id 与结束序号，没有时间戳', 'InMemoryTelemetryContext: deterministic ids and end sequence numbers, no timestamps'))
    E = f.edge
    f.group(16, 52, 400, 300, 'infra', ('每个实例的状态', 'Per-instance state'), 'memory.ts', 'db', gid='st')
    codebox(f, 32, 92, 368, [(0, 'state = {', 'strongt'), (1, 'spans: MutableRecordedTelemetrySpan[]', 'muted'), (1, 'nextSpanId: 1', 'muted'), (1, 'nextEndSequence: 1', 'muted'), (0, '}', 'strongt')], None, size=9.6, lh=16)
    f.text(32, 206, ('每条记录（可变，内部）', 'Each record (mutable, internal)'), 9.6, 650, cls='strongt', layer='label')
    chiprow(f, 32, 216, ['id', 'parentId', 'name', 'attributes', 'events'], 'infra', size=9.0, h=19, gap=5)
    chiprow(f, 32, 241, ['status', 'settled', 'endSequence?', ('explicitStatus', 'err')], 'infra', size=9.0, h=19, gap=5)
    f.text(32, 284, ('getSpans()：按开始顺序返回分离的快照——', 'getSpans(): detached snapshots in start order —'), 9.0, 500, cls='strongt', layer='label')
    f.text(32, 300, ('属性、数组、事件、状态全部复制；', 'attributes, arrays, events and status all copied;'), 8.8, 450, cls='muted', layer='label')
    f.text(32, 316, ('explicitStatus 不出现在快照里。', 'explicitStatus is not part of the snapshot.'), 8.8, 450, cls='muted', layer='label')
    f.text(32, 336, ('改快照不影响记录（有专门的测试）。', 'Mutating a snapshot never leaks back (tested).'), 8.8, 450, cls='muted', layer='label')
    # timeline
    f.group(432, 52, 672, 300, 'coding', ('一致性用例 “records nested and concurrent child relationships”', 'Conformance case “records nested and concurrent child relationships”'), None, 'clock', title_mono=False, gid='tl')
    LN = [('parent', 'id 1', 528, 1064, 3), ('first-child', 'id 2 · parent 1', 570, 980, 2), ('second-child', 'id 3 · parent 1', 612, 724, 1)]
    for i, (nm, sub, x0, x1, es) in enumerate(LN):
        y = 112 + i * 62
        f.text(448, y + 4, nm, 9.6, 650, True, cls='strongt', layer='label')
        f.text(448, y + 20, sub, 8.6, 450, True, cls='muted', layer='label')
        bar(f, x0, y - 10, x1 - x0, 'coding' if i else 'infra', None, h=22)
        f.chip(x1 - 96, y + 18, f'endSequence {es}', 'modes', size=8.8, h=17)
    hline(f, 528, 1088, 300)
    f.text(1088, 318, ('时间 →', 'time →'), 8.8, 450, anchor='end', cls='faint', layer='label')
    f.text(528, 318, ('开始顺序 = id 顺序', 'start order = id order'), 8.8, 450, cls='faint', layer='label')
    f.text(740, 248, ('second-child 同步返回 "done"，先结束；', 'second-child returns "done" synchronously and ends first;'), 8.6, 450, cls='muted', layer='label')
    f.text(740, 262, ('first-child 等闸门打开后才结束。', 'first-child ends once its gate opens.'), 8.6, 450, cls='muted', layer='label')
    # snapshot table
    f.group(16, 368, 1088, 172, 'modes', ('getSpans() 的结果', 'What getSpans() returns'), None, 'queue', title_mono=False, gid='sn')
    COLS = [(36, 'id'), (96, 'parentId'), (196, 'name'), (360, 'status'), (460, 'settled'), (560, 'endSequence'), (700, 'attributes / events')]
    for x, h in COLS:
        f.text(x, 418, h, 9.2, 700, True, cls='faint', layer='label')
    ROWS = [('1', 'null', 'parent', 'ok', 'true', '3', '{} / []'), ('2', '1', 'first-child', 'ok', 'true', '2', '{} / []'), ('3', '1', 'second-child', 'ok', 'true', '1', '{} / []')]
    for r, row in enumerate(ROWS):
        y = 444 + r * 26
        hline(f, 32, 1088, y - 16)
        for (x, _), v in zip(COLS, row):
            f.text(x, y, v, 9.4, 500, True, cls='strongt', layer='label')
    f.text(36, 528, ('回调还在运行时调用 getSpans()：settled = false，没有 endSequence。', 'getSpans() while a callback is still running: settled = false, no endSequence.'), 8.8, 450, cls='muted', layer='label')
    f.text(16, 566, ('用途：测试、本地诊断、只想在进程内收集的应用。存储无上限且只在本进程内；为隔离测试请每次 new 一个实例。', 'Use it for tests, local diagnostics and apps that only want in-process capture. Storage is unbounded and process-local; create a fresh instance per test.'), 9.0, 450, cls='muted', layer='label')
    f.legend(24, 586, [('layer:infra', ('根 span', 'root span')), ('layer:coding', ('子 span', 'child span')), ('layer:modes', ('结束序号', 'end sequence'))])
    return f

# ============================================================== tel_schema : the serializable schema format
@reg
def tel_schema():
    s = T_.src('index.ts')
    for n in ['export type TelemetryAttributeType = "string" | "number" | "boolean" | "string[]" | "number[]" | "boolean[]";',
              'cardinality?: "low" | "high";', 'sensitive?: boolean;', '| { kind: "root_or_external" }', '| { kind: "spans"; spans: readonly string[] };',
              'status: { default: "ok"; errorWhen: string };', 'export type TelemetryStartAttributeDefinition = TelemetryAttributeDefinition & { required: boolean };',
              'endAttributes: Record<string, TelemetryAttributeDefinition>;', 'events?: Record<string, TelemetryEventDefinition>;',
              'export function defineTelemetrySchema<const T extends TelemetrySchemaDefinition>(schema: T): T {\n\treturn schema;\n}']:
        assert n in s, n
    types = re.search(r'export type TelemetryAttributeType = (.*);', s).group(1)
    assert len(re.findall(r'"[\w\[\]]+"', types)) == 6
    doc("'example.read': {", "parents: { kind: 'any' },", "values: ['account', 'project'],", "'example.item_count': {", "'example.cache.hit': {",
        "errorWhen: 'The read throws or returns an error result',", 'performs no runtime validation or parent-rule enforcement')
    f = Fig('tel_schema', 1120, 660, ('可序列化的 schema：span、属性、事件、父子规则与状态规则，全是普通 JSON 数据', 'A serializable schema: spans, attributes, events, parent and status rules — all plain JSON data'))
    E = f.edge
    uml(f, 'sd', 16, 60, 290, 'agent', 'TelemetrySchemaDefinition', None, [['version: number', 'spans: Record<name, SpanDefinition>']])
    uml(f, 'sp', 16, 172, 580, 'agent', 'TelemetrySpanDefinition', None, [['description: string', 'parents: TelemetryParentDefinition', 'startAttributes: Record<name, StartAttributeDefinition>',
                                                                          'endAttributes: Record<name, AttributeDefinition>', 'events?: Record<name, EventDefinition>', 'status: { default: "ok"; errorWhen: string }']])
    E([(161, 139), (161, 172)], 'sd', 'sp', 'dep', 'agent', smark='diamond')
    uml(f, 'ad', 16, 360, 316, 'agent', 'TelemetryAttributeDefinition', None, [['description: string', 'sensitive?: boolean', 'cardinality?: "low" | "high"'],
                                                                              ['type: one of 6 (below)', 'values? · elementValues?', 'examples?']])
    uml(f, 'pa', 352, 360, 244, 'agent', 'TelemetryParentDefinition', None, [['{ kind: "any" }', '{ kind: "root_or_external" }', '{ kind: "spans", spans }']])
    uml(f, 'ev', 352, 476, 244, 'agent', 'TelemetryEventDefinition', None, [['description: string', 'attributes: Record<…>']])
    E([(174, 319), (174, 360)], 'sp', 'ad', 'dep', 'agent', smark='diamond')
    E([(474, 319), (474, 360)], 'sp', 'pa', 'dep', 'agent', smark='diamond')
    E([(596, 290), (610, 290), (610, 515), (596, 515)], 'sp', 'ev', 'dep', 'agent', smark='diamond')
    f.text(16, 584, ('type：string · number · boolean · string[] · number[] · boolean[]', 'type: string · number · boolean · string[] · number[] · boolean[]'), 9.0, 500, True, cls='strongt', layer='label')
    f.text(16, 602, ('values = 标量的封闭集合；elementValues = 数组元素的封闭集合', 'values = a closed set for scalars; elementValues = for array elements'), 8.8, 450, cls='muted', layer='label')
    f.text(16, 620, ('start 与 event 属性另加 required: boolean；end 属性没有，永远可选', 'start and event attributes add required: boolean; end attributes never do'), 8.8, 450, cls='muted', layer='label')
    # right: example
    codebox(f, 628, 60, 476, [
        (0, 'defineTelemetrySchema({', 'strongt'), (1, 'version: 1,', 'muted'), (1, 'spans: {', 'muted'), (2, "'example.read': {", 'strongt'),
        (3, "parents: { kind: 'any' },", 'muted'), (3, 'startAttributes: {', 'muted'), (4, "'example.resource': { type: 'string',", 'muted'),
        (5, "required: true, values: ['account', 'project'] },", 'muted'), (3, '},', 'muted'), (3, 'endAttributes: {', 'muted'),
        (4, "'example.item_count': { type: 'number' },", 'muted'), (3, '},', 'muted'), (3, 'events: {', 'muted'), (4, "'example.cache': { attributes: {", 'muted'),
        (5, "'example.cache.hit': { type: 'boolean',", 'muted'), (6, 'required: true } } },', 'muted'), (3, '},', 'muted'),
        (3, "status: { default: 'ok', errorWhen: '…' },", 'muted'), (2, '},', 'muted'), (1, '},', 'muted'), (0, '} as const)', 'strongt')],
        ('README 的例子（description 字段从略）', 'The README example (descriptions omitted)'), size=9.2, lh=16)
    f.text(628, 474, ('何时可知', 'When a value is known'), 9.6, 650, cls='strongt', layer='label')
    f.text(628, 492, ('startAttributes：开始时传入 starter 的 attributes 参数', 'startAttributes: passed to the starter when the span is created'), 8.8, 450, cls='muted', layer='label')
    f.text(628, 508, ('endAttributes：之后用 span.setAttributes() 补充，可以不调', 'endAttributes: added later with span.setAttributes(), or not at all'), 8.8, 450, cls='muted', layer='label')
    f.text(628, 524, ('两者落在同一个后端 span 的同一个属性袋里。', 'Both land in the same attribute bag of the same backend span.'), 8.8, 450, cls='muted', layer='label')
    f.text(628, 556, ('defineTelemetrySchema() 是类型化的恒等函数：', 'defineTelemetrySchema() is a typed identity function:'), 9.0, 600, cls='strongt', layer='label')
    f.text(628, 572, ('原样返回参数，运行时不校验、不强制父子规则。', 'it returns its argument; no runtime validation or parent rules.'), 8.8, 450, cls='muted', layer='label')
    f.legend(24, 644, [('layer:agent', ('schema 类型', 'schema types')), ('dep', ('包含（◆）', 'contains (◆)'))])
    return f

# ============================================================== tel_typed : createTypedSpanStarter
@reg
def tel_typed():
    s = T_.src('index.ts')
    for n in ['type UniqueTelemetrySchemas<Schemas extends TelemetrySchemaTuple> = [DuplicateTelemetrySpanNames<Schemas>] extends [',
              '{ readonly "duplicate telemetry span names": DuplicateTelemetrySpanNames<Schemas> };',
              'export type TypedSpanStarter<Schemas extends TelemetrySchemaTuple> = UnionToIntersection<',
              'export type ExactTelemetryAttributes<Expected, Actual extends Expected> = Actual &\n\tRecord<Exclude<keyof Actual, keyof Expected>, never>;',
              'telemetryContext.startSpan({ name, attributes }, (span) =>', 'bindTypedSpanStarter<Schemas>(span),',
              '_schemas: Schemas & UniqueTelemetrySchemas<Schemas>,', 'Schema values are used only for type inference; no runtime schema validation is performed.']:
        assert n in s, n
    t = (SRC / 'packages/telemetry/test/telemetry.test.ts').read_text()
    errs = re.findall(r'// @ts-expect-error (.*)', t)
    assert len(errs) == 9, errs
    for n in ['const startSpan = createTypedSpanStarter(telemetryContext, [operationSchema, requestSchema]);', 'parents: { kind: "spans", spans: ["operation"] },',
              'expect(requestSpan?.parentId).toBe(operationSpan?.id);', 'expect(result).toBe(42);']:
        assert n in t, n
    f = Fig('tel_typed', 1120, 600, ('createTypedSpanStarter：编译期按 schema 检查，运行时只是 startSpan 的一层薄包装', 'createTypedSpanStarter: checked against the schemas at compile time, a thin startSpan wrapper at run time'))
    E = f.edge
    f.node('in', 16, 64, 300, 52, 'agent', 'createTypedSpanStarter(ctx, [A, B])', ('一个父上下文 + 一组 schema（元组）', 'one parent context + a tuple of schemas'), None, tsize=10.2, ssize=8.6, strong=True)
    f.group(16, 140, 528, 324, 'agent', ('编译期（TypeScript）', 'Compile time (TypeScript)'), None, 'braces', title_mono=False, gid='ct')
    CT = [('UniqueTelemetrySchemas', ('跨 schema 的同名 span → 参数类型变成 "duplicate telemetry span names"', 'a span name in two schemas → the argument type becomes "duplicate telemetry span names"')),
          ('TypedSpanStarter', ('每个 span 名一个重载（UnionToIntersection）；联合类型的名字必须先收窄', 'one overload per span name (UnionToIntersection); union-typed names must be narrowed')),
          ('ExactTelemetryAttributes', ('多出来的键 → never；缺 required 的 start 属性 → 报错', 'extra keys → never; a missing required start attribute → error')),
          ('AttributeDefinitionValue', ('values / elementValues → 字面量联合；否则 string / number / boolean', 'values / elementValues → literal unions; otherwise string / number / boolean')),
          ('SchemaTelemetrySpan', ('addEvent 只收已声明的事件；setAttributes 只收 end 属性', 'addEvent takes declared events only; setAttributes end attributes only'))]
    for i, (a, b) in enumerate(CT):
        y = 194 + i * 54
        f.text(32, y, a, 10, 650, True, cls='strongt', layer='label')
        f.text(32, y + 18, b, 8.7, 450, cls='muted', layer='label')
    E([(166, 116), (166, 140)], 'in', 'ct', 'main', 'agent')
    f.group(560, 140, 544, 324, 'infra', ('运行时（bindTypedSpanStarter）', 'Run time (bindTypedSpanStarter)'), None, 'play', title_mono=False, gid='rt')
    codebox(f, 576, 184, 512, [(0, 'startSpan(name, attributes, callback) =>', 'strongt'), (1, 'telemetryContext.startSpan({ name, attributes },', 'muted'),
                                (2, '(span) => callback(span,', 'muted'), (3, 'bindTypedSpanStarter(span)))', 'strongt')], None, size=9.6, lh=17)
    f.text(576, 286, ('子 starter 绑定到回调的 span：显式传播，同一套 schema。', 'The child starter is bound to the callback span: explicit propagation, same schemas.'), 8.9, 500, cls='strongt', layer='label')
    f.text(576, 306, ('schema 值只用于类型推导：运行时不检查、不合并、不保留。', 'Schema values only drive type inference: not inspected, merged or kept at run time.'), 8.8, 450, cls='muted', layer='label')
    f.text(576, 340, ('测试里的例子', 'The example from the tests'), 9.4, 650, cls='strongt', layer='label')
    codebox(f, 576, 350, 512, [(0, 'startSpan("operation", { kind: "read" },', 'muted'), (1, '(_op, startChild) => startChild("request",', 'muted'),
                                (2, '{ provider: "example" }, (req) => {', 'muted'), (3, 'req.setAttributes({ response: "cached" }); return 42; }))', 'muted'),
                                (0, '// → 42 · request.parentId === operation.id', 'strongt')], None, size=9.2, lh=17)
    f.text(16, 494, (f'telemetry.test.ts 用 {len(errs)} 处 @ts-expect-error 锁定这些拒绝：', f'telemetry.test.ts pins these rejections with {len(errs)} @ts-expect-error lines:'), 9.4, 650, cls='strongt', layer='label')
    EX = [('缺少 required 事件属性', 'missing required event attribute'), ('封闭集合外的值', 'value outside a closed set'), ('未声明的事件', 'undeclared event'),
          ('空 end schema 的任何属性', 'any attribute on an empty end schema'), ('未收窄的联合 span 名', 'un-narrowed union span name'), ('多出未知键的变量', 'a variable with unknown keys'),
          ('未知 span 名', 'unknown span name'), ('属性取自别的 span', 'attributes from another span'), ('重复的 span 名', 'duplicate span names')]
    x = 16; y = 506
    for a in EX:
        w = maxw(a, 8.8, 550, False) + 14
        if x + w > 1104: x = 16; y += 24
        f.chip(x, y, a, 'err', mono=False, size=8.8, h=19); x += w + 6
    f.legend(24, 584, [('layer:agent', ('类型层', 'type level')), ('layer:infra', ('运行时', 'run time')), ('layer:err', ('编译期拒绝', 'compile-time rejection'))])
    return f

# ============================================================== tel_pi : where the context flows in pi
@reg
def tel_pi():
    A = 'packages/ai/src/'
    ty = (SRC / (A + 'types.ts')).read_text(); so = (SRC / (A + 'api/simple-options.ts')).read_text()
    assert 'import type { TelemetryContext } from "@earendil-works/pi-telemetry";' in ty
    assert 'telemetryContext?: TelemetryContext;' in ty and 'telemetryContext: options?.telemetryContext,' in so
    ai_src = ''.join(p.read_text() for p in (SRC / A).rglob('*.ts'))
    assert sum('telemetryContext' in l for l in ai_src.split('\n')) == 2 and 'startSpan' not in ai_src
    at = (SRC / 'packages/ai/test/telemetry-options.test.ts').read_text()
    assert 'expect(observed).toHaveLength(8);' in at and 'survives direct and Models image dispatch' in at
    doc('`@earendil-works/pi-ai` accepts and propagates `telemetryContext` in provider request options but owns no telemetry schema;',
        'The pi schemas use pi-owned `pi.ai.*`, `pi.harness.*`, and `pi.session.*` names.',
        'Do not persist a `TelemetryContext`, `TelemetrySpan`, or backend-native trace object in records, messages, snapshots, or deferred handles.',
        'The package does not use `AsyncLocalStorage` or another runtime-specific ambient context API. It is suitable for Node.js, Bun, browsers, and workers;')
    f = Fig('tel_pi', 1120, 600, ('在 pi 里：pi-ai 把 telemetryContext 一路传到 provider，自己不开 span', 'In pi: pi-ai carries telemetryContext through to the provider and opens no span itself'))
    E = f.edge
    f.node('app', 16, 64, 230, 52, 'coding', ('应用 / 宿主', 'Application / host'), ('拥有适配器（OTel、Sentry…）', 'owns the adapter (OTel, Sentry …)'), 'user', mono=False, tsize=10.6, ssize=8.6)
    f.node('opt', 290, 64, 340, 52, 'ai', '{ telemetryContext }', ('ProviderRequestOptions · types.ts', 'ProviderRequestOptions · types.ts'), None, tsize=10.6, ssize=8.6, strong=True)
    f.node('bb', 674, 64, 430, 52, 'ai', 'buildBaseOptions()', ('simple-options.ts：SimpleStreamOptions → StreamOptions，原样带上', 'simple-options.ts: SimpleStreamOptions → StreamOptions, passed as is'), None, tsize=10.6, ssize=8.6)
    E([(246, 90), (290, 90)], 'app', 'opt', 'main', 'ai')
    E([(630, 90), (674, 90)], 'opt', 'bb', 'main', 'ai')
    f.group(16, 148, 1088, 168, 'ai', ('pi-ai 的测试证明它在每条分派路径上都还是同一个对象', 'pi-ai tests prove it is the same object on every dispatch path'), 'telemetry-options.test.ts', 'check', title_mono=False, gid='ds')
    D = [('provider.stream', 'models.stream'), ('provider.streamSimple', 'models.streamSimple'), ('provider.fetchDeferred', 'models.fetchDeferred'), ('provider.cancelDeferred', 'models.cancelDeferred'), ('generateImages', 'models.generateImages')]
    for i, (a, b) in enumerate(D):
        x = 32 + i * 214
        f.node(f'd{i}', x, 192, 198, 34, 'ai', a, None, None, tsize=9.6)
        f.node(f'm{i}', x, 238, 198, 34, 'ai', b, None, None, tsize=9.6)
    f.text(32, 298, ('流式与延迟分派共 8 处观察到的 options.telemetryContext 全部 === 传入的对象；图像分派单独一个用例。', 'All 8 observed options.telemetryContext values for streaming and deferred dispatch === the one passed in; image dispatch has its own case.'), 8.8, 450, cls='muted', layer='label')
    # ownership
    f.group(16, 332, 640, 196, 'infra', ('按 README 的分工', 'Ownership, per the README'), None, 'hub', title_mono=False, gid='ow')
    OW = [('pi-telemetry', ('契约、no-op 与内存上下文、schema 工具、一致性套件', 'contract, no-op and in-memory contexts, schema utilities, conformance'), ('v1.1.0 ✓', 'v1.1.0 ✓'), 'infra'),
          ('pi-ai', ('接受并传递 telemetryContext，不拥有 schema', 'accepts and propagates telemetryContext, owns no schema'), ('v1.1.0 ✓', 'v1.1.0 ✓'), 'ai'),
          ('pi-agent-core', ('pi.ai.* / pi.harness.* / pi.session.* schema 与 span 助手', 'pi.ai.* / pi.harness.* / pi.session.* schemas and span helpers'), ('尚未出现', 'not yet'), 'err')]
    for i, (k, d, st, ly) in enumerate(OW):
        y = 388 + i * 46
        f.text(32, y, k, 10, 650, True, cls='strongt', layer='label')
        f.text(32, y + 17, d, 8.8, 450, cls='muted', layer='label')
        f.chip(640 - maxw(st, 9, 600, False) - 14 - 16, y - 12, st, ly, mono=False, size=9, h=18)
    # security
    f.group(672, 332, 432, 196, 'err', ('安全与可移植性', 'Security and portability'), None, 'shield', title_mono=False, gid='se')
    SE = [('不要持久化 context 或 span', 'Never persist a context or span'), ('（记录、消息、快照、deferred handle）', '(records, messages, snapshots, deferred handles)'),
          ('属性只有标量与数组', 'Attributes are scalars and arrays only'), ('避开提示词、输出、文件内容、凭据', 'avoid prompts, outputs, file contents, credentials'),
          ('没有 AsyncLocalStorage', 'No AsyncLocalStorage'), ('Node.js、Bun、浏览器、worker 都能用', 'works in Node.js, Bun, browsers and workers')]
    for i in range(0, 6, 2):
        y = 388 + (i // 2) * 46
        f.text(688, y, SE[i], 9.6, 650, cls='strongt', layer='label')
        f.text(688, y + 17, SE[i + 1], 8.8, 450, cls='muted', layer='label')
    f.text(16, 556, ('pi-ai 的 src 里 telemetryContext 只出现在 2 行（类型声明与 buildBaseOptions），没有一处 startSpan：真正开 span 的是拿到它的 provider 实现或上层代码。', 'telemetryContext appears on just 2 lines of pi-ai\'s src (the type and buildBaseOptions), with no startSpan anywhere: spans are opened by the provider implementation or code above that receives it.'), 9.0, 450, cls='muted', layer='label')
    f.legend(24, 584, [('main', ('传递', 'passed along')), ('layer:ai', ('pi-ai', 'pi-ai')), ('layer:infra', ('pi-telemetry', 'pi-telemetry')), ('layer:err', ('缺口 / 规则', 'gap / rules'))])
    return f
