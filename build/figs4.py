"""pi-ai deep-dive diagrams (ai_*). Facts read from /workspace/pi-src/packages/ai at build time (tag v1.1.0)."""
import re
from svgkit import Fig, maxw, pair
from figs import reg
from figkit import SRC, uml, codebox, bar, hline, vline, chiprow, lines_of

AI = SRC / 'packages/ai'
def _t(p): return (AI / p).read_text()
def _union(name, path='src/types.ts'):
    return re.findall(r'"([A-Za-z0-9-]+)"', re.search(rf'export type {name} =(.*?);', _t(path), re.S).group(1))

# ============================================================== ai_entry : entry points
@reg
def ai_entry():
    f = Fig('ai_entry', 1120, 610, ('pi-ai 入口与打包', 'pi-ai entry points and bundling'))
    nprov = len(re.findall(r'^import \{ \w+Provider \} from "\./', _t('src/providers/all.ts'), re.M))
    nlazy = len(list((AI / 'src/api').glob('*.lazy.ts')))
    f.text(24, 40, ('导入路径', 'IMPORT PATH'), 10.5, 700, cls='faint', layer='label', ls='.08em')
    f.text(300, 40, ('得到什么', 'WHAT YOU GET'), 10.5, 700, cls='faint', layer='label', ls='.08em')
    f.text(820, 40, ('加载成本', 'LOAD COST'), 10.5, 700, cls='faint', layer='label', ls='.08em')
    rows = [
        ('@earendil-works/pi-ai', 'ai', ('核心：类型、Type、createModels、createProvider、EventStream、工具函数', 'core: types, Type, createModels, createProvider, EventStream, helpers'), [(('无副作用', 'side-effect free'), 'ai'), (('TypeBox 立即加载', 'eager TypeBox'), 'infra')]),
        ('…/pi-ai/models', 'ai', ('仅 Models 运行时（不含 TypeBox 校验）', 'Models runtime only (no TypeBox validation)'), [(('最小', 'smallest'), 'ai')]),
        ('…/providers/<id>', 'agent', ('一个 provider：模型目录 + 认证 + 懒加载的 API', 'one provider: catalog + auth + lazily-loaded API'), [(('SDK 首次请求时加载', 'SDK on first request'), 'agent')]),
        ('…/providers/all', 'agent', (f'builtinModels() · builtinProviders()（{nprov} 个）', f'builtinModels() · builtinProviders() ({nprov})'), [(('目录全部打包', 'all catalogs bundled'), 'coding'), (('SDK 仍懒加载', 'SDKs still lazy'), 'agent')]),
        ('…/api/<id>', 'coding', ('直接调用某个 API 实现（stream / streamSimple）', 'one API implementation directly (stream / streamSimple)'), [(('SDK 立即加载', 'eager SDK'), 'err')]),
        ('…/oauth · /bun-oauth', 'infra', ('OAuth 登录辅助（Node / Bun）', 'OAuth login helpers (Node / Bun)'), [(('按需', 'on demand'), 'infra')]),
        ('…/utils/*', 'infra', ('event-stream · validation · transcript · overflow …', 'event-stream · validation · transcript · overflow …'), [(('按文件', 'per file'), 'infra')]),
        ('…/pi-ai/compat', 'err', ('旧的全局 API（stream / complete / getModel）超集', 'old global API superset (stream / complete / getModel)'), [(('已弃用', 'deprecated'), 'err')]),
    ]
    y = 56
    for i, (path, l, what, cost) in enumerate(rows):
        f.node(f'e{i}', 24, y, 252, 40, l, path, None, None, tsize=11.5, strong=i in (0, 2, 3))
        f.text(300, y + 25, what, 11, 500, cls='strongt', layer='label')
        chiprow(f, 820, y + 10, cost, size=9.5, h=20)
        if i < len(rows) - 1: hline(f, 24, 1096, y + 46)
        y += 52
    # lazy chain
    cy = 56 + len(rows) * 52 + 64
    f.group(16, cy - 44, 1088, 104, 'agent', ('懒加载链', 'Lazy-loading chain'), (f'{nlazy} 个 *.lazy.ts 包装', f'{nlazy} *.lazy.ts wrappers'), 'bolt', title_mono=False)
    C = [('lp', 'providers/anthropic.ts', 'createProvider({ api })', 'agent'), ('ll', 'anthropic-messages.lazy.ts', 'lazyApi(() => import(…))', 'agent'),
         ('lm', 'anthropic-messages.ts', 'stream · streamSimple', 'coding'), ('ls', '@anthropic-ai/sdk', ('首次请求才加载', 'loaded on first request'), 'infra')]
    x = 36
    for k, t, s, l in C:
        f.node(k, x, cy - 4, 236, 48, l, t, s, None, tsize=11, ssize=10)
        x += 236 + 34
    for a, b, i in (('lp', 'll', 0), ('ll', 'lm', 1), ('lm', 'ls', 2)):
        x0 = 36 + 236 + i * 270
        f.edge([(x0, cy + 20), (x0 + 34, cy + 20)], a, b, 'dep' if i == 0 else 'event', 'agent' if i == 0 else None)
    return f

# ============================================================== ai_registry : Models / Provider
@reg
def ai_registry():
    f = Fig('ai_registry', 1120, 600, ('Models 集合与 Provider', 'The Models collection and providers'))
    nprov = len(re.findall(r'^import \{ \w+Provider \} from "\./', _t('src/providers/all.ts'), re.M))
    # left: factories
    f.node('bp', 24, 40, 236, 56, 'agent', 'builtinProviders()', (f'providers/all · {nprov} 个', f'providers/all · {nprov} providers'), 'layers', tsize=12)
    f.node('cp', 24, 132, 236, 72, 'agent', 'createProvider({…})', 'id · api | { [api]: … } · models', None, sub2='fetchModels? · images? · classifiers? · auth?', tsize=12, ssize=10)
    f.node('cm', 24, 252, 236, 56, 'ai', 'createModels({ providers })', ('或 builtinModels()', 'or builtinModels()'), None, tsize=11.5, strong=True)
    f.edge([(142, 96), (142, 132)], 'bp', 'cp', 'dep', label=('每个调用', 'each calls'), lpos=(142, 114), lmono=False, lsize=10)
    f.edge([(142, 204), (142, 252)], 'cp', 'cm', 'main', 'ai', label='Provider[]', lpos=(142, 228), lsize=10)
    # center: ModelsImpl
    hM = uml(f, 'mi', 300, 40, 380, 'ai', 'ModelsImpl', '«implements Models»', [
        ['-providers: Map<id, Provider>', '-credentials: CredentialStore (InMemory)', '-store?: ModelsStore · authContext'],
        ['+getModel(provider, id) · getModels()', '+getAvailableModels() · checkAuth()', '+refresh({ allowNetwork, signal })', '+login(id, interaction) · logout(id)'],
        ['+stream · complete · streamSimple · completeSimple', '+streamDeferred · cancelDeferred', '+generateImages · classify (never reject)']], lh=17)
    f.edge([(260, 280), (282, 280), (282, 120), (300, 120)], 'cm', 'mi', 'main', 'ai', r=6, label='new', lpos=(282, 200), lsize=9.5)
    # right: Provider
    hP = uml(f, 'pv', 724, 40, 372, 'agent', 'Provider<TApi>', '«interface»', [
        ['+id · name · baseUrl? · headers?', '+auth?: ApiKeyAuth | OAuthAuth …'],
        ['+getModels() · getAllModels()', '+refreshModels?(ctx)', '+stream · streamSimple', '+fetchDeferred? · cancelDeferred?', '+generateImages? · classify?']], lh=17)
    f.edge([(680, 64), (724, 64)], 'mi', 'pv', 'dep', smark='diamond')
    f.text(702, 56, '*', 11, 600, True, 'middle', 'faint', layer='label', owner='note')
    # dispatch
    dy = 40 + hP + 30
    f.node('dp', 724, dy, 372, 64, 'agent', 'dispatch(model, run)', ('单一 api，或按 model.api 查表', 'single api, or look up by model.api'), None, sub2=('缺失 → error 流（不抛出）', 'missing → error stream (no throw)'), tsize=12, ssize=10.5)
    f.edge([(910, 40 + hP), (910, dy)], 'pv', 'dp', 'dep', label=('stream 时', 'on stream'), lpos=(910, 40 + hP + 15), lmono=False, lsize=9.5)
    # refresh flow
    ry = 40 + hM + 46
    f.h = ry + 166
    f.group(16, ry, 1088, 150, 'ai', ('refresh() · 每个 provider 的 refreshModels(ctx)', 'refresh() · each provider’s refreshModels(ctx)'), None, 'loop', title_mono=False)
    S = [('r1', ('读取 ModelsStore', 'read ModelsStore'), 'ctx.stored.models'), ('r2', ('先发布缓存', 'publish cached'), 'publish({ update })'),
         ('r3', ('allowNetwork？', 'allowNetwork?'), ('否 / 已中止 → 结束', 'no / aborted → stop')), ('r4', 'fetchModels(ctx)', ('网络获取目录', 'fetch the catalog')), ('r5', ('合并后发布', 'merge & publish'), ('按 id 覆盖基线', 'override baseline by id'))]
    x = 36; W = 196; G = 18
    for i, (k, t, s) in enumerate(S):
        f.node(k, x, ry + 48, W, 54, 'ai', t, s, None, mono=False if isinstance(t, tuple) else True, kind='dec' if k == 'r3' else 'card', tsize=11.5, ssize=10)
        if i: f.edge([(x - G, ry + 75), (x, ry + 75)], S[i - 1][0], k, 'main', 'ai')
        x += W + G
    f.note(36, ry + 130, ('getModels() 永远同步：返回 基线目录 ∪ 动态目录；refresh 只改变动态部分', 'getModels() stays synchronous: baseline ∪ dynamic models; refresh only swaps the dynamic part'), 10.5)
    return f

# ============================================================== ai_pipeline : streamSimple end to end
@reg
def ai_pipeline():
    f = Fig('ai_pipeline', 1120, 540, ('models.streamSimple() 全链路', 'models.streamSimple() end to end'))
    f.node('call', 24, 40, 220, 56, 'coding', 'models.streamSimple(', 'model, context, options)', 'play', tsize=12, ssize=11, strong=True)
    f.node('norm', 290, 40, 230, 56, 'ai', 'normalizeContext(context)', ('→ TranscriptContext（同步）', '→ TranscriptContext (sync)'), None, tsize=11.5, ssize=10.5)
    f.node('lazy', 566, 40, 250, 56, 'ai', 'lazyStream(model, setup)', ('立即返回外层流', 'returns the outer stream now'), 'stream', tsize=11.5, ssize=10.5, strong=True)
    f.node('ret', 870, 40, 226, 56, 'coding', ('调用方开始迭代', 'caller iterates'), 'for await … · result()', None, mono=False, tsize=11.5)
    E = f.edge
    E([(244, 68), (290, 68)], 'call', 'norm', 'main', 'ai', step=1, spos=(267, 50))
    E([(520, 68), (566, 68)], 'norm', 'lazy', 'main', 'ai', step=2, spos=(543, 50))
    E([(816, 68), (870, 68)], 'lazy', 'ret', 'main', 'coding', flow=True)
    # async setup lane
    sy = 140
    f.group(16, sy, 1088, 196, 'ai', ('setup()（异步，在外层流背后）', 'setup() (async, behind the outer stream)'), None, 'clock', title_mono=False, gid='setup')
    S = [('req', 'requireChatProvider', ('未知 provider → 抛出', 'unknown provider → throw'), 'ai'),
         ('auth', 'applyAuth(model, opts)', 'resolveProviderAuth()', 'ai'),
         ('disp', 'provider.streamSimple', 'dispatch(model.api)', 'agent'),
         ('imp', 'lazyApi → import()', ('首次加载 API 模块', 'first load of the API module'), 'agent'),
         ('impl', 'api.streamSimple()', ('SDK 请求 → 内层流', 'SDK request → inner stream'), 'coding')]
    x = 32; W = 196; G = 16
    for i, (k, t, s, l) in enumerate(S):
        f.node(k, x, sy + 50, W, 56, l, t, s, None, tsize=11, ssize=10, strong=k == 'impl')
        if i: E([(x - G, sy + 78), (x, sy + 78)], S[i - 1][0], k, 'main', l, step=i + 2, spos=(x - G / 2, sy + 38))
        x += W + G
    E([(691, 96), (691, 114), (130, 114), (130, sy + 50)], 'lazy', 'req', 'event', label='setup()', lpos=(410, 114), lsize=10, r=8)
    # auth detail
    codebox(f, 248, sy + 120, 400, [(0, 'resolveProviderAuth order:', 'strongt'), (1, '1 options.apiKey override', 'muted'), (1, '2 stored credential (oauth refresh | api_key)', 'muted'), (1, '3 ambient env (ANTHROPIC_API_KEY …)', 'muted')], size=10, lh=14)
    f.note(668, sy + 136, ('之后合并 headers → transformHeaders → env；', 'then merge headers → transformHeaders → env;'), 10.5)
    f.note(668, sy + 154, ('auth.baseUrl 存在时覆盖 model.baseUrl', 'auth.baseUrl overrides model.baseUrl'), 10.5)
    # forward / error
    fy = 384
    f.node('fwd', 820, fy, 276, 60, 'ai', 'forwardStream(outer, inner)', ('逐个 push 事件 → end(result)', 'push each event → end(result)'), None, tsize=11.5, ssize=10.5, strong=True)
    f.node('err', 290, fy, 330, 60, 'err', ('任一步骤抛出', 'any step throws'), ('→ push({ type: "error", reason: "error" })', '→ push({ type: "error", reason: "error" })'), 'x', kind='err', mono=False, tsize=11.5, ssize=10.5)
    f.node('dur', 820, fy + 92, 276, 48, 'ai', ('done / error 消息', 'done / error message'), ('写入 durationMs（1.1.0）', 'gets durationMs (1.1.0)'), 'clock', mono=False, tsize=11.5, ssize=10.5)
    E([(958, sy + 106), (958, fy)], 'impl', 'fwd', 'main', 'coding', flow=True, step=7, spos=(978, sy + 170))
    E([(958, fy + 60), (958, fy + 92)], 'fwd', 'dur', 'dep')
    E([(130, sy + 196), (130, fy + 30), (290, fy + 30)], 'setup', 'err', 'err', r=8, label=('catch', 'catch'), lpos=(130, fy - 2), lcls='err', lsize=10)
    f.note(290, fy + 86, ('约定：流式 API 从不 reject —— 所有失败都编码成流里的最终 error 事件，', 'contract: streaming APIs never reject — every failure is encoded as the final error event'), 10.5)
    f.note(290, fy + 104, ('outer.result() 同样解析为带 stopReason 与 errorMessage 的 AssistantMessage', 'outer.result() resolves to an AssistantMessage carrying stopReason + errorMessage'), 10.5)
    return f

# ============================================================== ai_events : event grammar + EventStream
@reg
def ai_events():
    ev = re.findall(r'type: "([a-z_]+)"', re.search(r'export type AssistantMessageEvent\b(.*?)\n\n', _t('src/types.ts'), re.S).group(1))
    stops = _union('StopReason')
    f = Fig('ai_events', 1120, 560, (f'AssistantMessageEvent 语法（{len(ev)} 种）', f'AssistantMessageEvent grammar ({len(ev)} types)'))
    f.node('start', 24, 120, 120, 44, 'ai', 'start', 'partial', None, tsize=12, ssize=10, kind='term', align='center')
    G = [('text', 'text_start', 'text_delta', 'text_end', 'ai'), ('thinking', 'thinking_start', 'thinking_delta', 'thinking_end', 'coding'), ('toolcall', 'toolcall_start', 'toolcall_delta', 'toolcall_end', 'agent')]
    f.group(196, 28, 640, 236, 'ai', ('内容块 × n（按 contentIndex）', 'content blocks × n (by contentIndex)'), None, 'stack', title_mono=False, gid='blocks')
    for i, (k, s, d, e, l) in enumerate(G):
        y = 74 + i * 62
        f.node(f'{k}s', 216, y, 170, 44, l, s, None, None, tsize=11.5)
        f.node(f'{k}d', 420, y, 170, 44, l, d, ('× n · delta', '× n · delta'), None, tsize=11.5, ssize=10)
        f.node(f'{k}e', 624, y, 190, 44, l, e, ('完整块', 'full block'), None, tsize=11.5, ssize=10)
        f.edge([(386, y + 22), (420, y + 22)], f'{k}s', f'{k}d', 'main', l)
        f.edge([(590, y + 22), (624, y + 22)], f'{k}d', f'{k}e', 'main', l)
    f.edge([(144, 142), (196, 142)], 'start', 'blocks', 'main', 'ai')
    f.node('done', 900, 70, 196, 56, 'term', 'done', ' | '.join(['stop', 'length', 'toolUse', 'deferred']), None, kind='term', align='center', tsize=12, ssize=10)
    f.node('error', 900, 160, 196, 56, 'err', 'error', 'error | aborted', None, kind='err', align='center', tsize=12, ssize=10)
    f.edge([(836, 98), (900, 98)], 'blocks', 'done', 'main', 'accent', label='reason', lpos=(868, 84), lsize=9.5)
    f.edge([(836, 188), (900, 188)], 'blocks', 'error', 'err')
    f.note(216, 252, ('每个事件都带 partial（当前的 AssistantMessage）；toolcall_delta 的参数由 parseStreamingJson 增量解析', 'every event carries partial (the AssistantMessage so far); toolcall_delta args are parsed incrementally by parseStreamingJson'), 10)
    # stop reasons
    sy = 292
    f.text(24, sy + 14, ('StopReason', 'StopReason'), 11, 700, True, cls='strongt', layer='label')
    cols = {'pending': 'infra', 'stop': 'ai', 'length': 'coding', 'toolUse': 'agent', 'error': 'err', 'aborted': 'err', 'deferred': 'tui'}
    chiprow(f, 120, sy, [(s, cols.get(s, 'infra')) for s in stops], size=10, h=21)
    f.note(560, sy + 14, ('pending 只出现在 partial 上；deferred = 异步任务，稍后 streamDeferred(handle)', 'pending only on partials; deferred = async job, fetch later with streamDeferred(handle)'), 10)
    # EventStream internals
    ey = 340
    f.group(16, ey, 1088, 204, 'ai', 'EventStream<T, R>', ('utils/event-stream.ts', 'utils/event-stream.ts'), 'stream', gid='es')
    f.node('prod', 36, ey + 56, 190, 60, 'coding', ('生产者', 'producer'), 'push(event) · end(result?)', None, mono=False, tsize=11.5, ssize=10)
    f.node('q', 300, ey + 46, 250, 40, 'ai', 'queue: FifoQueue<T>', None, None, tsize=11)
    f.node('w', 300, ey + 96, 250, 40, 'ai', 'waiting: FifoQueue<resolve>', None, None, tsize=11)
    f.node('cons', 624, ey + 56, 210, 60, 'coding', ('消费者', 'consumer'), 'for await (const e of s)', None, mono=False, tsize=11.5, ssize=10)
    f.node('res', 880, ey + 56, 206, 60, 'ai', 'result(): Promise<R>', ('done / error 时 resolve', 'resolves on done / error'), None, tsize=11, ssize=10, strong=True)
    f.edge([(226, ey + 66), (300, ey + 66)], 'prod', 'q', 'dep', label=('无人等待', 'no waiter'), lpos=(263, ey + 52), lmono=False, lsize=9.5)
    f.edge([(226, ey + 106), (300, ey + 106)], 'prod', 'w', 'main', 'ai', label=('直接交付', 'hand off'), lpos=(263, ey + 122), lmono=False, lsize=9.5)
    f.edge([(550, ey + 66), (624, ey + 66)], 'q', 'cons', 'dep')
    f.edge([(624, ey + 106), (550, ey + 106)], 'cons', 'w', 'event', label=('排队等待', 'park'), lpos=(587, ey + 122), lmono=False, lsize=9.5)
    f.edge([(834, ey + 86), (880, ey + 86)], 'cons', 'res', 'event')
    f.note(36, ey + 168, ('isComplete(e) 为真后 done = true，后续 push 被忽略；AssistantMessageEventStream 在 done/error/end 时用 performance.now() 写入 durationMs', 'once isComplete(e) is true, done = true and later pushes are dropped; AssistantMessageEventStream stamps durationMs (performance.now) on done / error / end'), 10)
    f.note(36, ey + 186, ('FifoQueue 用两个数组实现摊还 O(1) 出队', 'FifoQueue uses two arrays for amortised O(1) dequeue'), 10)
    return f

# ============================================================== ai_convert : cross-provider message transform
@reg
def ai_convert():
    f = Fig('ai_convert', 1120, 560, ('transformMessages：跨模型交接', 'transformMessages: cross-model handoff'))
    f.node('in', 24, 40, 230, 64, 'coding', 'Message[]', ('来自任意 provider 的历史', 'history from any provider'), 'msg', tsize=12, strong=True)
    f.node('tm', 300, 40, 520, 64, 'ai', 'transformMessages(messages, model, normalizeToolCallId?)', 'api/transform-messages.ts', None, tsize=11.5, ssize=10.5, strong=True)
    f.node('out', 866, 40, 230, 64, 'agent', ('目标 API 的请求', 'target API request'), 'convertMessages(…)', 'globe', mono=False, tsize=12)
    f.edge([(254, 72), (300, 72)], 'in', 'tm', 'main', 'ai', flow=True)
    f.edge([(820, 72), (866, 72)], 'tm', 'out', 'main', 'agent', flow=True)
    R = [('user', ('用户消息', 'user message'), ('模型不支持图像 → 图像换成文字占位', 'model lacks image input → images become a text placeholder'), 'coding'),
         ('think', ('thinking 块', 'thinking blocks'), ('同一模型：保留签名；换模型：转成文本，空的丢弃；redacted 跨模型直接丢弃', 'same model: keep signature; other model: become text, empty ones dropped; redacted dropped cross-model'), 'coding'),
         ('ids', ('工具调用 id', 'tool-call ids'), ('normalizeToolCallId：如 OpenAI 450+ 字符 id → Anthropic ^[a-zA-Z0-9_-]+$ ≤ 64；toolResult 同步改写', 'normalizeToolCallId: e.g. 450+ char OpenAI ids → Anthropic ^[a-zA-Z0-9_-]+$ ≤ 64; toolResults remapped too'), 'agent'),
         ('err', ('失败的 assistant', 'failed assistant'), ('stopReason 为 error / aborted 的消息整条跳过（不可回放）', 'messages with stopReason error / aborted are skipped (not replayable)'), 'err'),
         ('orph', ('孤立工具调用', 'orphaned tool calls'), ('没有结果的调用 → 合成 isError 的 toolResult（"No result provided"）', 'calls without a result → synthesize an isError toolResult ("No result provided")'), 'agent'),
         ('sys', ('system 消息', 'system messages'), ('在工具调用与其结果之间出现时延后，保证结果紧跟调用', 'held back while tool results are pending, so results stay adjacent to their calls'), 'ai')]
    y = 140
    for i, (k, t, d, l) in enumerate(R):
        f.node(k, 300, y, 170, 44, l, t, None, None, mono=False, tsize=11.5, kind='tint' if l == 'err' else 'card')
        f.text(490, y + 27, d, 10.5, 500, cls='strongt', layer='label')
        f.step(i + 1, 280, y + 22, l, r=8)
        y += 58
    vline(f, 384, 104, 140, 'rule')
    f.note(24, 156, ('按顺序应用于整个', 'applied in order to the'), 10.5)
    f.note(24, 174, ('历史；每次请求都会执行', 'whole history, every request'), 10.5)
    f.note(24, 528, ('结果：在 Claude 中途切到 GPT（或反之）时，同一份会话仍能被新 provider 接受', 'result: switch from Claude to GPT (or back) mid-session and the same history is still accepted by the new provider'), 10.5)
    return f

# ============================================================== ai_anthropic : one provider in detail
@reg
def ai_anthropic():
    f = Fig('ai_anthropic', 1120, 600, ('anthropic-messages：SSE → 事件', 'anthropic-messages: SSE → events'))
    f.text(24, 40, ('Anthropic SSE', 'ANTHROPIC SSE'), 10.5, 700, cls='faint', layer='label', ls='.08em')
    f.text(420, 40, ('处理', 'HANDLING'), 10.5, 700, cls='faint', layer='label', ls='.08em')
    f.text(812, 40, ('发出的事件', 'EMITTED'), 10.5, 700, cls='faint', layer='label', ls='.08em')
    R = [('message_start', ('记录 id · usage', 'record id · usage'), ['start']),
         ('content_block_start · text', ('新建 text 块', 'new text block'), ['text_start']),
         ('content_block_start · thinking', ('新建 thinking 块', 'new thinking block'), ['thinking_start']),
         ('… · redacted_thinking', ('"[Reasoning redacted]" + 签名', '"[Reasoning redacted]" + signature'), ['thinking_start']),
         ('content_block_start · tool_use', ('新建 toolCall，partialJson = ""', 'new toolCall, partialJson = ""'), ['toolcall_start']),
         ('content_block_delta', ('text / thinking / input_json / signature', 'text / thinking / input_json / signature'), ['text_delta', 'thinking_delta', 'toolcall_delta']),
         ('content_block_stop', ('删除 partialJson，完成块', 'delete partialJson, finish block'), ['*_end']),
         ('message_delta', ('stop_reason → mapStopReason · usage', 'stop_reason → mapStopReason · usage'), []),
         ('message_stop', ('calculateCost(model, usage)', 'calculateCost(model, usage)'), ['done'])]
    y = 56
    for i, (s, h, ev) in enumerate(R):
        f.node(f's{i}', 24, y, 300, 34, 'infra', s, None, None, tsize=11)
        f.text(420, y + 22, h, 10.5, 500, i in (5, 7), cls='strongt', layer='label')
        f.edge([(324, y + 17), (404, y + 17)], f's{i}', None, 'dep')
        if ev: chiprow(f, 812, y + 7, [(e, 'err' if e == 'error' else 'ai') for e in ev], size=9.5, h=20, gap=4)
        y += 42
    # stop reason map
    my = 448
    f.group(16, my, 520, 136, 'ai', 'mapStopReason()', None, 'branch', gid='msr')
    M = [('end_turn · pause_turn · stop_sequence', 'stop'), ('max_tokens', 'length'), ('tool_use', 'toolUse'), ('refusal · sensitive', 'error')]
    for i, (a, b) in enumerate(M):
        yy = my + 50 + i * 21
        f.text(36, yy + 4, a, 10, 500, True, cls='muted', layer='label')
        f.text(330, yy + 4, '→', 10, 500, True, cls='faint', layer='label')
        f.chip(352, yy - 9, b, 'err' if b == 'error' else 'ai', size=9.5, h=18)
    # thinking config
    f.group(560, my, 544, 136, 'coding', ('streamSimple() 的 thinking 配置', 'thinking in streamSimple()'), None, 'spark', title_mono=False, gid='thk')
    T = [(('!reasoning', '!reasoning'), ('thinkingEnabled: false', 'thinkingEnabled: false')),
         (('自适应模型', 'adaptive models'), ('thinking: adaptive + effort（由 reasoning 映射）', 'thinking: adaptive + effort (mapped from reasoning)')),
         (('其余模型', 'other models'), ('adjustMaxTokensForThinking → clampMaxTokensToContext', 'adjustMaxTokensForThinking → clampMaxTokensToContext')),
         ('budget', ('min(budget, maxTokens − 1024)', 'min(budget, maxTokens − 1024)'))]
    for i, (a, b) in enumerate(T):
        yy = my + 54 + i * 21
        f.text(576, yy, a, 10, 600, isinstance(a, str) or a[0].startswith('!'), cls='cf c-coding', layer='label')
        f.text(700, yy, b, 10, 500, True, cls='muted', layer='label')
    return f

# ============================================================== ai_budget : thinking levels, tokens, cost
@reg
def ai_budget():
    so = _t('src/api/simple-options.ts')
    bud = dict(re.findall(r'(\w+): (\d+)', re.search(r'DEFAULT_THINKING_BUDGETS: ThinkingBudgets = \{(.*?)\}', so, re.S).group(1)))
    safety = int(re.search(r'CONTEXT_SAFETY_TOKENS = (\d+)', so).group(1)) if 'CONTEXT_SAFETY_TOKENS' in so else None
    levels = re.findall(r'"(\w+)"', re.search(r'EXTENDED_THINKING_LEVELS: ModelThinkingLevel\[\] = \[(.*?)\]', _t('src/models.ts')).group(1))
    f = Fig('ai_budget', 1120, 560, ('思考等级、token 预算与成本', 'Thinking levels, token budgets and cost'))
    f.text(24, 40, ('ModelThinkingLevel（getSupportedThinkingLevels / clampThinkingLevel）', 'ModelThinkingLevel (getSupportedThinkingLevels / clampThinkingLevel)'), 11, 650, cls='strongt', layer='label')
    X0, X1 = 24, 1096; n = len(levels); w = (X1 - X0 - (n - 1) * 8) / n
    for i, lv in enumerate(levels):
        x = X0 + i * (w + 8)
        lay = 'infra' if lv == 'off' else 'coding' if lv in bud else 'tui'
        bar(f, x, 56, w, lay, lv, h=30, size=11)
        sub = (f'{int(bud[lv]):,} tok', f'{int(bud[lv]):,} tok') if lv in bud else (('不思考', 'no thinking') if lv == 'off' else ('需 thinkingLevelMap 声明', 'only if thinkingLevelMap has it'))
        f.text(x + w / 2, 104, sub, 10, 550, lv in bud, 'middle', 'muted', layer='label')
    f.note(24, 128, ('预算 = DEFAULT_THINKING_BUDGETS（可被 options.thinkingBudgets 覆盖）；不支持的等级被 clamp 到最近的可用等级', 'budget = DEFAULT_THINKING_BUDGETS (override with options.thinkingBudgets); unsupported levels clamp to the nearest available one'), 10.5)
    # token stack
    ty = 168
    f.group(16, ty, 1088, 150, 'coding', ('maxTokens 的推导（token 型思考 API）', 'deriving maxTokens (token-budget thinking APIs)'), None, 'stack', title_mono=False)
    cw = 1048
    segs = [(('输入（估算）', 'input (estimated)'), 0.46, 'infra'), (('安全余量', 'safety'), 0.08, 'err'), (('思考预算', 'thinking budget'), 0.24, 'coding'), (('回答 ≥ 1024', 'answer ≥ 1024'), 0.14, 'ai'), (('空闲', 'free'), 0.08, 'infra')]
    x = 36
    for t, frac, l in segs:
        ww = cw * frac
        bar(f, x, ty + 52, ww - 4, l, t, h=30, size=10.5, mono=False, dashed=l == 'infra' and frac < .1)
        x += ww
    f.text(36, ty + 104, ('contextWindow', 'contextWindow'), 10, 600, True, cls='faint', layer='label')
    hline(f, 36, 1084, ty + 92, 'rule')
    f.note(36, ty + 126, (f'clampMaxTokensToContext：maxTokens ≤ contextWindow − 估算输入 − {safety}；思考预算 ≤ maxTokens − MIN_ANSWER_TOKENS', f'clampMaxTokensToContext: maxTokens ≤ contextWindow − estimated input − {safety}; thinking budget ≤ maxTokens − MIN_ANSWER_TOKENS'), 10.5)
    # usage / cost
    uy = 342
    uml(f, 'usage', 24, uy, 360, 'ai', 'Usage', '«interface»', [['+input · output · cacheRead · cacheWrite', '+cacheWrite1h? (Anthropic only)', '+reasoning? (subset of output)', '+totalTokens'], ['+cost: { input · output · cacheRead', '         cacheWrite · total } (USD)']], lh=17)
    codebox(f, 420, uy, 676, [
        (0, 'calculateCost(model, usage):', 'strongt'),
        (1, 'inputTokens = input + cacheRead + cacheWrite', 'muted'),
        (1, 'rates = highest tier with inputTokens > tier.inputTokensAbove', 'muted'),
        (1, 'cost.input     = rates.input     / 1e6 × input', 'muted'),
        (1, 'cost.cacheWrite = (rates.cacheWrite × short + rates.input × 2 × cacheWrite1h) / 1e6', 'muted'),
        (1, 'cost.total     = input + output + cacheRead + cacheWrite', 'muted')], size=10, lh=16, title=('models.ts', 'models.ts'))
    f.note(420, uy + 150, ('isContextOverflow(message, contextWindow)（utils/overflow.ts）识别各家“上下文过长”错误，供压缩重试', 'isContextOverflow(message, contextWindow) (utils/overflow.ts) recognises each provider’s context-overflow error for compact-and-retry'), 10.5)
    f.note(420, uy + 170, ('provider-retry.ts：retryProviderRequest 对 429 / 5xx 重试，受 maxRetryDelayMs 约束', 'provider-retry.ts: retryProviderRequest retries 429 / 5xx, bounded by maxRetryDelayMs'), 10.5)
    return f

# ============================================================== ai_oneshot : images + classifiers
@reg
def ai_oneshot():
    capis = _union('KnownClassifierApi'); iapis = _union('KnownImageApi')
    f = Fig('ai_oneshot', 1120, 480, ('一次性 API：图像与分类器', 'One-shot APIs: images and classifiers'))
    f.node('m', 24, 180, 200, 72, 'ai', 'Models', ('不 reject：失败 = 结果里的', 'never reject: failure ='), 'hub', sub2=('stopReason "error"', 'stopReason "error" in result'), tsize=12.5, ssize=10, strong=True)
    # images
    f.group(270, 24, 826, 176, 'coding', 'generateImages(model, context, opts)', '→ Promise<AssistantImages>', 'eye', gid='img')
    f.node('ip', 290, 72, 220, 52, 'coding', 'openrouter', ('provider', 'provider'), None, tsize=11.5, ssize=10)
    f.node('ia', 548, 72, 220, 52, 'coding', iapis[0], 'ImageApi', None, tsize=11.5, ssize=10)
    f.node('io', 806, 72, 270, 52, 'coding', 'AssistantImages', 'output[] · usage? · stopReason', None, tsize=11.5, ssize=10)
    f.edge([(510, 98), (548, 98)], 'ip', 'ia', 'main', 'coding')
    f.edge([(768, 98), (806, 98)], 'ia', 'io', 'main', 'coding')
    f.note(290, 156, ('ImageModel（model.type = "image"）不出现在 getModels()，用 getAllModels() 查找', 'ImageModels (type "image") are not in getModels(); find them via getAllModels()'), 10.5)
    f.note(290, 176, ('无 generateImages 的 provider → 返回 error 结果', 'providers without generateImages → error result'), 10.5)
    # classifiers
    f.group(270, 224, 826, 236, 'agent', 'classify(model, context, opts)', '→ Promise<ClassifierResult>', 'filter', gid='cls')
    PROV = {'openai-decisions': 'openai', 'typesafe-system-one': 'typesafe · opencode · openrouter · vercel-ai-gateway', 'cloudflare-workers-ai-system-one': 'cloudflare-workers-ai', 'llama-cpp-classify': ('无内置 provider · 通过 createProvider 注册', 'no built-in provider · register via createProvider')}
    for i, a in enumerate(capis):
        y = 270 + i * 32
        f.chip(290, y, a, 'agent', size=10, h=22)
        f.text(560, y + 15, PROV.get(a, '—'), 10.5, 500, isinstance(PROV.get(a), str), cls='muted', layer='label')
    cy = 270 + len(capis) * 32 + 6
    f.text(290, cy + 12, 'ClassifierContext', 11, 650, True, cls='strongt', layer='label')
    f.text(430, cy + 12, ('{ state: JSON, images?（1.1.0）, questions: { [k]: choice | score | bool } }', '{ state: JSON, images? (1.1.0), questions: { [k]: choice | score | bool } }'), 10.5, 500, True, cls='muted', layer='label')
    f.text(290, cy + 34, 'ClassifierResult', 11, 650, True, cls='strongt', layer='label')
    f.text(430, cy + 34, '{ answers: { choice·probabilities | score | probability }, usage?, stopReason }', 10.5, 500, True, cls='muted', layer='label')
    f.edge([(224, 200), (246, 200), (246, 112), (270, 112)], 'm', 'img', 'main', 'coding', r=8)
    f.edge([(224, 232), (246, 232), (246, 342), (270, 342)], 'm', 'cls', 'main', 'agent', r=8)
    return f
