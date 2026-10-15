"""chord deep-dive diagrams (chord_*). Facts read from /workspace/pi-src/packages/chord at build time."""
import re
from svgkit import Fig, maxw, pair
from figs import reg
from figkit import SRC, uml, codebox, bar, dot, hline, vline, chiprow, lines_of
from pkgsrc import Pkg, users_of

K = Pkg('packages/chord/src/')
CAX = 'packages/coding-agent/src/experimental/services/'

def facet_env_methods():
    blk = re.search(r'export interface FacetEnvironment \{(.*?)^\}', K.src('types.ts'), re.S | re.M).group(1)
    return re.findall(r'^\t([a-zA-Z]+)<?', blk, re.M)
def update_types():
    blk = re.search(r'export type ServiceProviderUpdate =(.*?)\};\n', K.src('types.ts'), re.S).group(1)
    return re.findall(r'type: "(\w+)"', blk)
def error_codes():
    return re.findall(r'"(service_\w+)"', re.search(r'REMOTE_SERVICE_ERROR_CODES = \[(.*?)\]', K.src('services/errors.ts'), re.S).group(1))
def op_verbs():
    blk = re.search(r'export type Op =(.*?);\n', K.src('delta/index.ts'), re.S).group(1)
    return re.findall(r'readonly \["(\w)"', blk)

# ============================================================== chord_arch
@reg
def chord_arch():
    tot = K.total(); ex = K.exports(); deps = K.pkg().get('dependencies', {})
    assert list(ex) == ['.', './context', './delta', './bundler', './node'], ex
    f = Fig('chord_arch', 1120, 600, (f'chord 模块结构（{tot:,} 行 TypeScript）', f'chord modules ({tot:,} lines of TypeScript)'))
    COLS = [(('API 与类型', 'API & types'), 'infra', 'braces', [
                ('index.ts', ('根入口：重新导出', 'root entry: re-exports')),
                ('api.ts', ('createFacetHost() 等', 'createFacetHost() …')),
                ('types.ts', ('Facet · Service · Context …', 'Facet · Service · Context …')),
                ('json.ts', ('isJsonValue · copyJson', 'isJsonValue · copyJson'))]),
            (('Facet 宿主', 'Facet host'), 'agent', 'layers', [
                ('facets/host.ts', ('FacetKernel：激活 · 重载', 'FacetKernel: activate · reload')),
                ('facets/loader.ts', ('LoadedFacets 的释放', 'disposing LoadedFacets'))]),
            (('服务', 'Services'), 'ext', 'hub', [
                ('services/consumer.ts', ('远程绑定：稳定外观', 'remote binding: stable facade')),
                ('services/provider.ts', ('RemoteServiceProvider', 'RemoteServiceProvider')),
                ('services/state.ts', ('复制状态 · 订阅', 'replicated state · subscriptions')),
                ('services/wire.ts', ('$chord.service 控制调用', '$chord.service control calls')),
                ('services/state-codec.ts', ('每个订阅一套路径字典', 'one path dictionary per subscription')),
                ('services/instances.ts', ('keyed 实例 · generation', 'keyed instances · generations')),
                ('services/handle.ts', ('ServiceSlot · 代理视图', 'ServiceSlot · proxy views'))]),
            (('Delta', 'Delta'), 'coding', 'diff', [
                ('delta/tracker.ts', ('track() · Draft · prepare/adopt', 'track() · Draft · prepare/adopt')),
                ('delta/index.ts', ('Op · WireOp · apply · 编解码', 'Op · WireOp · apply · codec')),
                ('delta/diff.ts', ('diffRevisions()', 'diffRevisions()')),
                ('delta/apply-immutable-trusted.ts', ('结构共享地重放', 'structurally shared replay')),
                ('delta/revision-validator.ts', ('校验不可信的 op', 'validates untrusted ops'))]),
            (('Context 与 Node', 'Context & Node'), 'modes', 'box', [
                ('context/index.ts', ('取消 · 调用范围的值', 'cancellation · scoped values')),
                ('node/bundle-loader.ts', ('校验 SHA-256 · node:vm', 'SHA-256 check · node:vm')),
                ('node/bundle.ts', ('esbuild → .cjs + 清单', 'esbuild → .cjs + manifest')),
                ('node/package.ts', ('package.json 中的 chord.facets', 'chord.facets in package.json'))])]
    WS, X0, GAP = [176, 196, 224, 256, 188], 16, 12
    XS = [X0 + sum(WS[:i]) + GAP * i for i in range(5)]
    for ci, (title, lay, ic, rows) in enumerate(COLS):
        x, W = XS[ci], WS[ci]
        f.group(x, 52, W, 384, lay, title, None, ic, title_mono=False, gid=f'g{ci}')
        for ri, (p, role) in enumerate(rows):
            f.node(f'n{ci}{ri}', x + 10, 96 + ri * 47, W - 20, 40, lay, p.split('/')[-1], role, None, tsize=10.5, ssize=8.8, tag=f'{K.loc(p):,}',
                   strong=p in ('facets/host.ts', 'delta/tracker.ts', 'services/consumer.ts'))
    f.text(XS[1] + 12, 214, ('setup 同步声明依赖；', 'setup declares deps synchronously;'), 9.3, 450, cls='muted', layer='label')
    f.text(XS[1] + 12, 230, ('宿主校验整张图后', 'the host validates the whole graph,'), 9.3, 450, cls='muted', layer='label')
    f.text(XS[1] + 12, 246, ('按依赖顺序激活。', 'then activates in dependency order.'), 9.3, 450, cls='muted', layer='label')
    f.text(XS[1] + 12, 290, ('较小的文件：', 'Smaller files:'), 9.3, 600, cls='faint', layer='label')
    for i, p in enumerate(['services/errors.ts', 'services/loopback.ts', 'services/state-internals.ts', 'delta/draft.ts', 'node/manifest.ts', 'bundler.ts · node.ts']):
        f.text(XS[1] + 12, 308 + i * 16, f'{p}', 9.3, 500, True, cls='faint', layer='label')
    # bottom
    f.group(16, 452, 1088, 104, 'infra', ('导入路径、依赖与使用者', 'Import paths, dependencies and users'), None, 'box', title_mono=False, gid='bot')
    x = 32
    for k in ex:
        w = f.chip(x, 494, '@earendil-works/chord' + k[1:], 'infra', size=9.8, h=20)
        x += w + 8
    dep = ' · '.join(f'{k} {v}' for k, v in deps.items())
    f.text(x + 6, 508, ('依赖：', 'dep:'), 10, 600, cls='faint', layer='label')
    f.chip(x + 6 + maxw(('依赖：', 'dep:'), 10, 600) + 4, 494, dep, 'modes', size=9.8, h=20)
    U = users_of('@earendil-works/chord')
    f.text(32, 538, ('被这些包导入（src 中的文件数）：', 'Imported by (files in src):'), 10, 600, cls='faint', layer='label')
    xx = 32 + maxw(('被这些包导入（src 中的文件数）：', 'Imported by (files in src):'), 10, 600) + 8
    for name, n in U:
        xx += f.chip(xx, 524, f'{name} · {n}', 'coding' if name == 'coding-agent' else 'infra', size=9.8, h=20) + 6
    f.legend(24, 580, [('layer:agent', 'facets'), ('layer:ext', ('服务与状态', 'services & state')), ('layer:coding', 'delta'), ('layer:modes', 'context · node')])
    f.note(1096, 580, ('标签 = 行数；不依赖任何其他 pi 包', 'tag = lines; depends on no other pi package'), 10.5, anchor='end')
    return f

# ============================================================== chord_facets : one generation's lifecycle
@reg
def chord_facets():
    K.has('facets/host.ts', 'throw new Error(`Facet ${facet.id} setup must be synchronous`);', 'Facet dependency cycle: ', 'is provided by both ',
          'but no facet provides it', 'for (const id of this.#activationOrder) await this.#facets.get(id)!.lifecycle.activate();',
          '[...this.#activationOrder].reverse()', 'for (const effect of this.#effects.splice(0).reverse())', 'Facet generation startup and cleanup failed',
          'onDeactivate: (callback) => lifecycle.own(callback)')
    M = facet_env_methods()
    assert M == ['use', 'observe', 'provide', 'provideMany', 'replicatedState', 'own', 'onActivate', 'onDeactivate'], M
    f = Fig('chord_facets', 1120, 640, ('一个 facet 代：setup → 校验 → 连接 → 激活 → 释放', 'One facet generation: setup → validate → connect → activate → dispose'))
    E = f.edge
    PH = [('setup', ('同步调用 facet.setup(env)', 'facet.setup(env), synchronously'), 'agent'),
          ('assembling', ('外部目录 · 校验 · 排序', 'catalogues · validate · order'), 'agent'),
          ('connecting', ('等所有绑定 ready()', 'wait for every binding ready()'), 'ext'),
          ('activating', ('按拓扑顺序 activate()', 'activate() in topological order'), 'agent'),
          ('active', ('服务可用', 'services usable'), 'coding'),
          ('disposing', ('逆序释放', 'reverse-order disposal'), 'infra')]
    x = 16; w = 172
    for i, (t, s, lay) in enumerate(PH):
        f.node(f'p{i}', x, 64, w, 56, lay, t, s, None, tsize=12, ssize=9.2, strong=(t == 'active'))
        if i: E([(x - 11, 92), (x, 92)], f'p{i-1}', f'p{i}', 'main', lay)
        x += w + 11
    f.text(16, 146, ('任何一步失败：#terminate() 释放已建好的一切，原错误与清理错误一起以 AggregateError 抛出（"Facet generation startup and cleanup failed"）。', 'A failure at any step: #terminate() disposes whatever was built and throws the original error with any cleanup errors as an AggregateError ("Facet generation startup and cleanup failed").'), 9.6, 450, cls='err', layer='label')
    # FacetEnvironment
    f.group(16, 168, 452, 388, 'agent', ('setup(env) 能做的事', 'What setup(env) can do'), 'FacetEnvironment', 'gear', title_mono=False, gid='env')
    D = {'use': ('声明对单例服务的硬依赖，返回稳定句柄', 'hard dependency on a singleton; returns a stable handle'),
         'observe': ('依赖 keyed 服务，逐个观察活着的实例', 'depend on a keyed service; observe each live instance'),
         'provide': ('提供单例实现（必须是对象）', 'provide a singleton implementation (an object)'),
         'provideMany': ('拥有 keyed 服务，返回 spawn(key, impl)', 'own a keyed service; returns spawn(key, impl)'),
         'replicatedState': ('创建本 facet 的可变复制状态', 'create mutable replicated state'),
         'own': ('登记一个释放函数', 'register a disposal function'),
         'onActivate': ('依赖就绪后的异步初始化', 'async init once dependencies are ready'),
         'onDeactivate': ('最终拆除（= own）', 'final teardown (same as own)')}
    for i, m in enumerate(M):
        y = 212 + i * 41
        f.text(32, y + 10, f'env.{m}()', 10.5, 600, True, cls='strongt', layer='label')
        f.text(32, y + 27, D[m], 9.3, 450, cls='muted', layer='label')
        if i: hline(f, 32, 452, y - 6)
    # validation
    f.group(484, 168, 620, 196, 'agent', ('assembling：validateFacets()', 'assembling: validateFacets()'), None, 'check', title_mono=False, gid='val')
    V = [(('每个服务只能有一个提供者（facet 或宿主的外部来源）', 'each service has exactly one provider (a facet or a host source)'), '"is provided by both … and …"'),
         (('singleton / keyed 模式必须一致', 'singleton / keyed modes must match'), '"provided as both singleton and keyed"'),
         (('每个 use / observe 都必须有提供者', 'every use / observe needs a provider'), '"… but no facet provides it"'),
         (('依赖图无环：Kahn 拓扑排序给出激活顺序', 'no cycles: a Kahn topological sort gives the activation order'), '"Facet dependency cycle: …"')]
    for i, (a, b) in enumerate(V):
        y = 210 + i * 36
        f.text(500, y + 8, a, 9.8, 500, cls='strongt', layer='label')
        f.text(500, y + 24, b, 9.2, 450, True, cls='err', layer='label')
    # example
    f.group(484, 380, 620, 176, 'coding', ('例：两个 facet', 'Example: two facets'), None, 'branch', title_mono=False, gid='ex')
    f.node('fa', 500, 424, 200, 52, 'agent', 'models-facet', ('env.provide(Models, impl)', 'env.provide(Models, impl)'), None, tsize=11, ssize=9.2)
    f.node('fb', 500, 490, 200, 52, 'agent', 'ui-facet', ('env.use(Models)', 'env.use(Models)'), None, tsize=11, ssize=9.2)
    E([(600, 490), (600, 476)], 'fb', 'fa', 'dep')
    f.text(724, 440, ('激活：models-facet → ui-facet', 'activate: models-facet → ui-facet'), 10, 600, cls='strongt', layer='label')
    f.text(724, 462, ('释放：ui-facet → models-facet', 'dispose: ui-facet → models-facet'), 10, 600, cls='strongt', layer='label')
    f.text(724, 488, ('每个 facet 内部，own() 登记的释放', 'Inside each facet, own() disposals'), 9.3, 450, cls='muted', layer='label')
    f.text(724, 504, ('函数也按登记的逆序执行；', 'also run in reverse registration order;'), 9.3, 450, cls='muted', layer='label')
    f.text(724, 520, ('错误收集后统一抛出。', 'errors are collected and rethrown.'), 9.3, 450, cls='muted', layer='label')
    f.text(16, 584, ('setup 返回 Promise 会被拒绝（"setup must be synchronous"）；use / provide 等只能在 setup 期间调用，句柄只能在 active 期间使用。', 'A setup that returns a Promise is rejected ("setup must be synchronous"); use / provide and friends work only during setup, and handles only while active.'), 9.6, 450, cls='muted', layer='label')
    f.legend(24, 618, [('layer:agent', ('facet 宿主', 'facet host')), ('layer:ext', ('远程绑定', 'remote bindings')), ('main', ('阶段顺序', 'phase order')), ('dep', ('依赖', 'depends on'))])
    return f

# ============================================================== chord_reload : FacetHost.reload()
@reg
def chord_reload():
    K.has('facets/host.ts', 'must preserve its service requirements and provisions', 'Facet reload failed after cutover', 'const retirementErrors = await disposeFacetRecords(previous.reverse());',
          'provision.replace(this.provider);', 'this.#serviceSlots.bindSingleton(provision.service.id, provision.implementation);', 'provision.connectRemote(this.provider);', 'this.#phase = "reloading";')
    f = Fig('chord_reload', 1120, 600, ('FacetHost.reload(facets)：不断开句柄地替换实现', 'FacetHost.reload(facets): replace implementations without disconnecting handles'))
    E = f.edge
    S = [('1', ('检查', 'Check'), ('phase 必须是 active；ID 唯一且都已激活', 'phase must be active; IDs unique and all active'), 'agent'),
         ('2', ('候选 setup', 'Candidate setup'), ('sameFacetShape()：requires / provides 不变', 'sameFacetShape(): same requires / provides'), 'agent'),
         ('3', ('激活候选', 'Activate candidates'), ('按原激活顺序；旧实现仍在服务请求', 'in the existing order; the old ones still serve'), 'agent'),
         ('4', ('切换', 'Cut over'), ('单例：local → bindSingleton · 远程 → replace()', 'singletons: local → bindSingleton · remote → replace()'), 'coding'),
         ('5', ('退役旧 facet', 'Retire old facets'), ('逆序 dispose', 'dispose in reverse order'), 'infra'),
         ('6', ('连接 keyed', 'Connect keyed'), ('新实例拿到新的 generation', 'new instances get fresh generations'), 'ext')]
    for i, (n, t, s, lay) in enumerate(S):
        y = 64 + i * 66
        f.node(f's{i}', 56, y, 470, 54, lay, t, s, None, mono=False, tsize=12, ssize=9.5, strong=(i == 3))
        f.step(n, 32, y + 27, lay)
        if i: E([(291, y - 12), (291, y)], f's{i-1}', f's{i}', 'main', lay)
    # failure lanes
    f.group(560, 52, 544, 188, 'err', ('失败时', 'On failure'), None, 'x', title_mono=False, gid='fail')
    f.text(576, 102, ('切换之前（第 1–3 步）', 'Before the cutover (steps 1–3)'), 10.5, 650, cls='strongt', layer='label')
    f.text(576, 122, ('释放候选；宿主回到 active，旧实现照常工作。', 'candidates are disposed; the host returns to active and the old ones keep working.'), 9.5, 450, cls='muted', layer='label')
    f.text(576, 140, ('只有清理也失败时才中止整个代。', 'Only if cleanup fails too is the whole generation aborted.'), 9.5, 450, cls='muted', layer='label')
    f.text(576, 176, ('切换之后（第 4–6 步）', 'After the cutover (steps 4–6)'), 10.5, 650, cls='strongt', layer='label')
    f.text(576, 196, ('#abort(previous)：撤销所有 facet 的服务访问并终止整个代，', '#abort(previous): revoke every facet\'s service access and terminate'), 9.5, 450, cls='muted', layer='label')
    f.text(576, 214, ('抛出 "Facet reload failed after cutover"。', 'the generation; throws "Facet reload failed after cutover".'), 9.5, 450, cls='muted', layer='label')
    # handles
    f.group(560, 256, 544, 196, 'ext', ('为什么句柄不断开', 'Why handles stay connected'), 'services/handle.ts', 'hub', title_mono=False, gid='h')
    f.node('cons', 576, 304, 150, 44, 'agent', 'consumer', ('拿着代理视图', 'holds a proxy view'), None, tsize=11, ssize=9)
    f.node('slot', 776, 304, 150, 44, 'ext', 'ServiceSlot', ('宿主拥有', 'owned by the host'), None, tsize=11, ssize=9, strong=True)
    f.node('old', 960, 290, 128, 34, 'infra', 'old impl', None, None, tsize=10.5)
    f.node('new', 960, 336, 128, 34, 'coding', 'new impl', None, None, tsize=10.5)
    E([(726, 326), (776, 326)], 'cons', 'slot', 'main', 'ext')
    E([(926, 318), (943, 318), (943, 307), (960, 307)], 'slot', 'old', 'dep', r=4)
    E([(926, 334), (943, 334), (943, 353), (960, 353)], 'slot', 'new', 'main', 'coding', r=4)
    f.text(576, 380, ('每次访问成员时，代理都通过 slot.resolve() 读当前实现，', 'Every member access resolves the current implementation through'), 9.5, 450, cls='muted', layer='label')
    f.text(576, 398, ('所以 bind(new) 之后，已有句柄立即调用新代码。', 'slot.resolve(), so after bind(new) existing handles call the new code.'), 9.5, 450, cls='muted', layer='label')
    f.text(576, 422, ('unbind() 之后访问 → "Service … is disconnected"。', 'Access after unbind() → "Service … is disconnected".'), 9.5, 450, True, cls='faint', layer='label')
    f.text(56, 482, ('README 推荐的重载流程：先 load() 候选的 LoadedFacets → 把 facets 交给 reload() → 失败则释放候选；', 'The README\'s reload recipe: load() the candidate LoadedFacets → pass its facets to reload() → dispose the candidate on failure;'), 9.6, 450, cls='muted', layer='label')
    f.text(56, 500, ('成功切换之后才释放退役的那一代 LoadedFacets（代码随之可被回收）。', 'dispose the retired LoadedFacets only after a successful cutover (its code can then be collected).'), 9.6, 450, cls='muted', layer='label')
    f.text(56, 526, ('keyed 实例按代区分（ServiceInstanceAddress = key + generation）：重载后旧实例关闭，新实例以新 generation 出现。', 'Keyed instances are generation-specific (ServiceInstanceAddress = key + generation): old instances close, new ones appear with new generations.'), 9.6, 450, cls='muted', layer='label')
    f.legend(24, 576, [('main', ('步骤', 'steps')), ('layer:coding', ('切换', 'cutover')), ('layer:err', ('失败处理', 'failure handling'))])
    return f

# ============================================================== chord_services : tokens, modes, handles, context
@reg
def chord_services():
    K.has('api.ts', 'Service IDs beginning with $chord. are reserved', 'export function defineService<T>(id: string, options: { readonly local: true }): Service<T>;')
    K.has('types.ts', 'export type RemoteServiceContract<T>')
    for fn in ['BACKGROUND_CONTEXT', 'TODO_CONTEXT', 'createContextKey', 'withContextValue', 'withAbortSignal', 'withoutAbortSignal', 'withCancel', 'awaitWithContext']:
        K.has('context/index.ts', f'export const {fn}' if fn.endswith('CONTEXT') else f'export function {fn}')
    ca = Pkg(CAX)
    ca.has('transcript.ts', 'defineService<Transcript>("pi.transcript")', 'readonly state: ReplicatedState<ConversationView>;')
    ca.has('models.ts', 'defineService<Models>("pi.models")')
    ca.has('presentation-ui.ts', 'defineService<PresentationUI>("pi.local.presentation-ui", { local: true })')
    f = Fig('chord_services', 1120, 600, ('服务：令牌 · 模式 · 稳定句柄 · Context', 'Services: tokens · modes · stable handles · Context'))
    E = f.edge
    # token panel
    f.group(16, 52, 536, 236, 'ext', ('服务令牌：defineService<T>(id, options?)', 'Service tokens: defineService<T>(id, options?)'), None, 'key', title_mono=False, gid='tok')
    f.node('rem', 32, 96, 244, 34, 'ext', ('远程（默认）', 'remote (default)'), None, 'globe', mono=False, tsize=11.5)
    f.text(44, 150, ('成员只能是：', 'members must be:'), 9.3, 450, cls='muted', layer='label')
    f.text(44, 167, '(…json, Context) => Promise', 9.3, 600, True, cls='strongt', layer='label')
    f.text(44, 184, ('或 ReplicatedState<json>', 'or ReplicatedState<json>'), 9.3, 600, True, cls='strongt', layer='label')
    f.node('loc', 292, 96, 244, 34, 'infra', ('本地：{ local: true }', 'local: { local: true }'), None, 'cpu', mono=False, tsize=11.5)
    f.text(304, 150, ('任意 TypeScript 形状；', 'any TypeScript shape;'), 9.3, 450, cls='muted', layer='label')
    f.text(304, 167, ('只在本进程内提供，', 'provided in-process only,'), 9.3, 450, cls='muted', layer='label')
    f.text(304, 184, ('不能跨传输。', 'never crosses a transport.'), 9.3, 450, cls='muted', layer='label')
    f.text(32, 214, ('coding-agent/src/experimental/services 中的例子：', 'Examples from coding-agent/src/experimental/services:'), 9.3, 600, cls='faint', layer='label')
    x = 32
    for s, lay in [('pi.transcript', 'ext'), ('pi.models', 'ext'), ('pi.agent-controller', 'ext'), ('pi.local.presentation-ui', 'infra')]:
        x += f.chip(x, 224, s, lay, size=9.6, h=20) + 6
    f.text(32, 266, ('空 ID 会抛错；"$chord." 前缀保留给 chord 自己的控制调用。', 'An empty ID throws; the "$chord." prefix is reserved for chord\'s own control calls.'), 9.3, 450, cls='muted', layer='label')
    # modes
    f.group(568, 52, 536, 236, 'agent', ('两种提供方式', 'Two provision modes'), None, 'layers', title_mono=False, gid='mode')
    f.node('sg', 584, 96, 244, 52, 'agent', 'singleton', ('provide(S, impl) ↔ use(S)', 'provide(S, impl) ↔ use(S)'), None, tsize=11.5, ssize=9.3)
    f.node('ky', 844, 96, 244, 52, 'agent', 'keyed', ('provideMany(S) ↔ observe(S, …)', 'provideMany(S) ↔ observe(S, …)'), None, tsize=11.5, ssize=9.3)
    f.text(584, 174, ('一个服务 ID 只有一个实现；', 'One implementation per service ID;'), 9.3, 450, cls='muted', layer='label')
    f.text(584, 191, ('use() 返回稳定句柄。', 'use() returns a stable handle.'), 9.3, 450, cls='muted', layer='label')
    f.text(844, 174, ('spawn(key, impl) 返回 close()；', 'spawn(key, impl) returns close();'), 9.3, 450, cls='muted', layer='label')
    f.text(844, 191, ('observer 对每个活实例被调用，', 'the observer runs for each live'), 9.3, 450, cls='muted', layer='label')
    f.text(844, 208, ('实例关闭时执行其清理函数。', 'instance and cleans up on close.'), 9.3, 450, cls='muted', layer='label')
    f.text(584, 244, ('来源：facet 提供，或宿主的 serviceSources（外部服务目录）提供——', 'Source: a facet, or one of the host\'s serviceSources (external catalogues)'), 9.3, 450, cls='muted', layer='label')
    f.text(584, 261, ('两者不能同时提供同一个服务。', '— never both for the same service.'), 9.3, 450, cls='muted', layer='label')
    # handle chain
    f.group(16, 304, 536, 252, 'coding', ('一个调用的路径', 'The path of one call'), None, 'play', title_mono=False, gid='call')
    R = [('h', 'models.select(m, ctx)', ('facet 拿到的句柄', 'handle the facet holds'), 'agent'),
         ('s', 'ServiceSlot.resolve()', ('取当前实现（重载可换）', 'current implementation (reload-safe)'), 'ext'),
         ('i', 'impl.select(m, ctx)', ('本地对象，或远程绑定的成员代理', 'local object, or a remote member proxy'), 'coding')]
    for i, (n, t, s, lay) in enumerate(R):
        y = 348 + i * 66
        f.node(n, 32, y, 300, 50, lay, t, s, None, tsize=10.8, ssize=9.2, strong=(i == 1))
        if i: E([(182, y - 16), (182, y)], R[i - 1][0], n, 'main', lay)
    f.text(348, 368, ('远程成员最后一个', 'A remote member\'s last'), 9.3, 450, cls='muted', layer='label')
    f.text(348, 385, ('参数必须是 Context，', 'argument must be a Context,'), 9.3, 450, cls='muted', layer='label')
    f.text(348, 402, ('否则 service_invalid_value。', 'else service_invalid_value.'), 9.3, 450, cls='muted', layer='label')
    f.text(348, 434, ('绑定关闭后调用 →', 'Calling after the binding'), 9.3, 450, cls='muted', layer='label')
    f.text(348, 451, ('service_stale_instance。', 'closes → service_stale_instance.'), 9.3, 450, cls='muted', layer='label')
    # context
    f.group(568, 304, 536, 252, 'modes', ('Context：显式传递的调用上下文', 'Context: an explicitly passed call context'), 'chord/context', 'clock', title_mono=False, gid='ctx')
    C = [('BACKGROUND_CONTEXT · TODO_CONTEXT', ('根上下文（TODO 标记"尚待接线"）', 'roots (TODO marks "not wired yet")')),
         ('createContextKey · withContextValue', ('调用范围内的键值', 'call-scoped values')),
         ('withAbortSignal · withCancel', ('合并取消信号（AbortSignal.any）', 'combine cancellation (AbortSignal.any)')),
         ('withoutAbortSignal', ('保留值，去掉取消', 'keep values, drop cancellation')),
         ('awaitWithContext(p, ctx)', ('取消时只拒绝等待者，不中止 p', 'cancellation rejects the waiter only, not p'))]
    for i, (a, b) in enumerate(C):
        y = 348 + i * 40
        f.text(584, y + 6, a, 9.8, 600, True, cls='strongt', layer='label')
        f.text(584, y + 23, b, 9.2, 450, cls='muted', layer='label')
    f.legend(24, 580, [('layer:ext', ('远程服务', 'remote services')), ('layer:infra', ('本地服务', 'local services')), ('layer:agent', ('facet 侧', 'facet side')), ('layer:modes', 'Context')])
    return f

# ============================================================== chord_remote : provider ↔ transport ↔ binding
@reg
def chord_remote():
    U = update_types(); assert U == ['state', 'reset', 'unavailable', 'replaced', 'spawned', 'closed'], U
    EC = error_codes(); assert len(EC) == 8, EC
    K.has('services/provider.ts', 'if (subscriber.buffer.length === 100) {', '{ type: "reset", snapshot }', 'export function createRemoteServiceEndpoint(')
    K.has('services/wire.ts', 'const SERVICE_CONTROL_ID = "$chord.service";')
    K.has('services/loopback.ts', 'export function createLoopbackServiceTransport(provider: RemoteServiceProvider)')
    K.has('api.ts', 'export function createRemoteServiceBinding(')
    f = Fig('chord_remote', 1120, 620, ('跨进程服务：provider ⇄ transport ⇄ binding', 'Services across processes: provider ⇄ transport ⇄ binding'))
    E = f.edge
    f.group(16, 52, 330, 300, 'agent', ('提供方进程', 'Provider process'), None, 'cpu', title_mono=False, gid='pv')
    f.node('impl', 32, 96, 298, 48, 'agent', ('服务实现', 'service implementation'), ('facet 的 provide / provideMany', 'a facet\'s provide / provideMany'), None, mono=False, tsize=11)
    f.node('prov', 32, 176, 298, 56, 'agent', 'RemoteServiceProvider', ('invoke(call) · subscribe(id, mode)', 'invoke(call) · subscribe(id, mode)'), None, tsize=11, ssize=9.2, strong=True)
    f.node('ep', 32, 264, 298, 56, 'agent', 'createRemoteServiceEndpoint()', ('处理 "$chord.service" 控制调用', 'serves "$chord.service" control calls'), None, tsize=10.5, ssize=9.2)
    E([(181, 176), (181, 144)], 'prov', 'impl', 'main', 'agent', label=('调用 [...args, ctx]', 'calls [...args, ctx]'))
    E([(181, 264), (181, 232)], 'ep', 'prov', 'main', 'agent')
    f.group(362, 52, 396, 300, 'infra', ('传输（应用自选）', 'Transport (application\'s choice)'), 'RemoteServiceTransport', 'plug', title_mono=False, gid='tr')
    f.text(378, 100, 'invoke(call, context)', 10.2, 600, True, cls='strongt', layer='label')
    f.text(378, 118, 'subscribe(serviceId, mode, listener, ctx)', 10.2, 600, True, cls='strongt', layer='label')
    f.text(378, 146, ('chord 不规定外层协议：这些值可以放进', 'chord does not prescribe the outer protocol:'), 9.3, 450, cls='muted', layer='label')
    f.text(378, 163, ('任何路由 / 请求 / 事件信封。', 'wrap these values in any envelope.'), 9.3, 450, cls='muted', layer='label')
    f.text(378, 258, ('$chord.service 的三种控制调用：', 'Three $chord.service control calls:'), 9.5, 600, cls='faint', layer='label')
    for i, c in enumerate(['catalogue', 'subscribe(subscriptionId, serviceId, mode)', 'unsubscribe(subscriptionId)']):
        f.text(390, 276 + i * 17, '· ' + c, 9.5, 500, True, cls='muted', layer='label')
    f.text(378, 338, ('同进程：createLoopbackServiceTransport(provider)', 'In-process: createLoopbackServiceTransport(provider)'), 9.3, 600, True, cls='faint', layer='label')
    f.group(774, 52, 330, 300, 'ext', ('使用方进程', 'Consumer process'), None, 'user', title_mono=False, gid='cs')
    f.node('bind', 790, 176, 298, 56, 'ext', 'createRemoteServiceBinding()', ('稳定外观：成员代理 + 复制状态', 'stable facade: member proxies + replicas'), None, tsize=10.5, ssize=9.2, strong=True)
    f.node('use', 790, 96, 298, 48, 'ext', ('facet 的 use() / observe()', 'a facet\'s use() / observe()'), ('像本地对象一样调用', 'calls it like a local object'), None, mono=False, tsize=11)
    f.node('rep', 790, 264, 298, 56, 'ext', 'state.value · state.subscribe()', ('按序重放 delta 的副本', 'replica that replays deltas in order'), None, tsize=10.5, ssize=9.2)
    E([(939, 144), (939, 176)], 'use', 'bind', 'main', 'ext')
    E([(939, 232), (939, 264)], 'bind', 'rep', 'event', 'ext')
    E([(790, 196), (330, 196)], 'bind', 'prov', 'main', 'ext', label=('调用 / 订阅', 'invoke / subscribe'), lpos=(560, 188))
    E([(330, 216), (790, 216)], 'prov', 'bind', 'event', 'agent', label=('更新', 'updates'), lpos=(560, 232))
    # update kinds
    f.group(16, 368, 540, 196, 'coding', ('订阅更新的 6 种类型', 'The 6 subscription update types'), 'ServiceProviderUpdate', 'stream', title_mono=False, gid='up')
    D = {'state': ('某成员的一批 op，sequence 连续', 'a batch of ops for one member, contiguous sequence'),
         'reset': ('整份快照：每个 state 都是 ["r", value]', 'full snapshot: every state is ["r", value]'),
         'unavailable': ('当前没有提供者', 'no provider right now'),
         'replaced': ('提供者被替换（如重载）', 'the provider was replaced (e.g. reload)'),
         'spawned': ('keyed 新实例出现', 'a new keyed instance appeared'),
         'closed': ('keyed 实例关闭', 'a keyed instance closed')}
    for i, u in enumerate(U):
        y = 410 + i * 24
        f.text(32, y + 4, u, 10, 650, True, cls='strongt', layer='label')
        f.text(132, y + 4, D[u], 9.3, 450, cls='muted', layer='label')
    # backpressure + errors
    f.group(572, 368, 532, 196, 'err', ('背压与错误', 'Backpressure and errors'), None, 'shield', title_mono=False, gid='bp')
    f.text(588, 412, ('每个订阅最多缓存 100 个待发更新；第 101 个到来时，', 'At most 100 pending updates per subscription; when update 101'), 9.5, 450, cls='muted', layer='label')
    f.text(588, 430, ('整个队列被替换成一个 { type: "reset", snapshot }。', 'arrives the whole queue becomes one { type: "reset", snapshot }.'), 9.5, 450, cls='muted', layer='label')
    f.text(588, 448, ('普通 state 更新绝不允许 sequence 跳号。', 'An ordinary state update never permits a sequence gap.'), 9.5, 600, cls='strongt', layer='label')
    f.text(588, 478, ('可以跨边界的 8 个错误码：', 'The 8 error codes that may cross the boundary:'), 9.3, 600, cls='faint', layer='label')
    x, y = 588, 488
    for c in EC:
        s = c.replace('service_', '')
        w = maxw(s, 9.4, 500, True) + 16
        if x + w > 1092: x, y = 588, y + 26
        x += f.chip(x, y, s, 'err', size=9.4, h=20) + 6
    f.legend(24, 596, [('main', ('调用', 'calls')), ('event', ('订阅更新', 'subscription updates')), ('layer:agent', ('提供方', 'provider')), ('layer:ext', ('使用方', 'consumer'))])
    f.note(1096, 596, ('错误码都带 service_ 前缀', 'all codes carry a service_ prefix'), 10.5, anchor='end')
    return f

# ============================================================== chord_state : replicated state change pipeline
@reg
def chord_state():
    K.has('services/state.ts', 'Replicated state cannot be changed reentrantly from a change callback', 'Replicated state change callbacks must be synchronous',
          'if (prepared.ops.length === 0) return;', 'this.#sequence += 1;', 'if (this.#pending.length === 100) {', 'Replicated state update sequence has a gap', 'if (sequence !== this.#sequence + 1) {')
    f = Fig('chord_state', 1120, 600, ('复制状态：一次 change() 如何变成远端的新值', 'Replicated state: how one change() becomes a new value elsewhere'))
    E = f.edge
    P = [('change(ctx, draft => …)', ('不可重入；回调必须同步', 'no reentrancy; callback must be sync'), 'agent'),
         ('tracker.beginChange()', ('拿到 Draft 代理', 'get a Draft proxy'), 'coding'),
         ('mutate(draft)', ('像普通对象一样改', 'mutate like a plain object'), 'coding'),
         ('change.prepare()', ('算出 ops（失败则 abort）', 'compute ops (abort on throw)'), 'coding'),
         ('tracker.adopt(prepared)', ('换根指针：新不可变版本', 'swap the root: new immutable revision'), 'coding'),
         ('publish(value, ops)', ('sequence + 1；没有 op 就不发布', 'sequence + 1; no ops, no publish'), 'agent')]
    for i, (t, s, lay) in enumerate(P):
        y = 60 + i * 62
        f.node(f'c{i}', 32, y, 330, 50, lay, t, s, None, tsize=10.8, ssize=9.2, strong=(i in (0, 5)))
        f.step(str(i + 1), 18, y + 25, lay, r=9)
        if i: E([(197, y - 12), (197, y)], f'c{i-1}', f'c{i}', 'main', lay)
    f.text(32, 450, ('回调抛错 → 原值和 sequence 都不变。', 'Callback throws → value and sequence unchanged.'), 9.5, 450, cls='err', layer='label')
    f.text(32, 468, ('replace(ctx, value) 走同一条路径（prepareReplace）。', 'replace(ctx, value) takes the same path (prepareReplace).'), 9.5, 450, cls='muted', layer='label')
    # fan-out
    f.group(398, 52, 706, 240, 'ext', ('发布之后：两类订阅者', 'After publishing: two kinds of subscriber'), None, 'stream', title_mono=False, gid='fan')
    f.node('ex', 414, 96, 330, 64, 'ext', ('内部精确订阅', 'internal exact subscriptions'), ('(ops, sequence, ctx)：同步，拿到每个版本', '(ops, sequence, ctx): synchronous, every revision'), None, mono=False, tsize=11, ssize=9.2)
    f.node('pub', 758, 96, 330, 64, 'ext', 'state.subscribe(fn)', ('(value, ctx, delivery)：每个订阅串行', '(value, ctx, delivery): serialized per subscription'), None, tsize=11, ssize=9.2)
    f.text(414, 186, ('→ 远程编码器 / provider 订阅', '→ remote encoders / provider subscriptions'), 9.5, 450, cls='muted', layer='label')
    f.text(414, 204, ('每个 client × state 独立编码', 'encoded separately per client × state'), 9.5, 450, cls='muted', layer='label')
    f.text(758, 186, ('先 hydrate（当前值），再 update；', 'hydrate (current value) first, then updates;'), 9.5, 450, cls='muted', layer='label')
    f.text(758, 204, ('最多 100 个待处理：溢出时只留最新的，', 'at most 100 pending: on overflow keep the newest,'), 9.5, 450, cls='muted', layer='label')
    f.text(758, 222, ('所以公开的 sequence 可能跳号。', 'so public sequences may skip.'), 9.5, 450, cls='muted', layer='label')
    f.text(758, 252, ('异步回调里读捕获的 value，不要读 state.value。', 'In async callbacks read the captured value, not state.value.'), 9.3, 600, cls='faint', layer='label')
    # replica
    f.group(398, 308, 706, 248, 'coding', ('远端副本：严格按序', 'The remote replica: strictly in order'), None, 'db', title_mono=False, gid='rep')
    seq = [('hydrate(7, [["r", v]])', ('基线', 'baseline'), 'coding'), ('update(8, ops)', ('apply', 'apply'), 'coding'), ('update(9, ops)', ('apply', 'apply'), 'coding'), ('update(11, …)', ('跳号！', 'gap!'), 'err')]
    x = 414
    for i, (t, s, lay) in enumerate(seq):
        w = 196 if i == 0 else 148
        f.node(f'r{i}', x, 352, w, 50, lay, t, s, None, tsize=10.2, ssize=9.2, strong=(lay == 'err'))
        if i: E([(x - 18, 377), (x, 377)], f'r{i-1}', f'r{i}', 'err' if lay == 'err' else 'main', lay)
        x += w + 18
    f.text(414, 432, ('update 要求 sequence == 上一个 + 1；否则清空副本并抛出', 'update requires sequence == previous + 1; otherwise the replica clears and throws'), 9.5, 450, cls='muted', layer='label')
    f.text(414, 450, '"Replicated state update sequence has a gap"', 9.5, 600, True, cls='err', layer='label')
    f.text(414, 480, ('provider 侧的 reset 是唯一合法的"重新起跑"：它带着新的基线 sequence，', 'A provider reset is the only legal restart: it carries new baseline sequences,'), 9.5, 450, cls='muted', layer='label')
    f.text(414, 498, ('并清空该订阅的路径字典。', 'and clears that subscription\'s path dictionaries.'), 9.5, 450, cls='muted', layer='label')
    f.text(414, 528, ('值是不可变、结构共享的：没变的子树在版本之间共用。', 'Values are immutable and structurally shared: unchanged subtrees are reused.'), 9.5, 450, cls='muted', layer='label')
    f.legend(24, 580, [('main', ('顺序', 'order')), ('layer:coding', 'delta tracker'), ('layer:ext', ('订阅', 'subscriptions')), ('err', ('违约', 'violation'))])
    return f

# ============================================================== chord_delta : op vocabulary
@reg
def chord_delta():
    V = op_verbs(); assert V == list('rsdatpm'), V
    K.has('delta/tracker.ts', 'const MAX_DELTA_OPERATIONS = 4_096;', 'const MAX_SIMPLE_OBJECT_NODES = 128;', 'return [["r", cloneNode(context.root!)]];')
    K.has('delta/index.ts', 'let nextId = 0;', 'out.push(["#", id, path]); // second use: define, then reference', 'Arity omission is scoped to a batch.')
    K.has('delta/diff.ts', 'const DEFAULT_OVERLAP_SCAN = 65_536;')
    K.has('delta/index.ts', '["#", id, path]    defines an id, emitted on a path\'s SECOND use', 'a shortened tuple  reuses the previous op\'s path; arity disambiguates')
    f = Fig('chord_delta', 1120, 560, ('Delta：7 种 op 与线上压缩', 'Delta: 7 ops and on-the-wire compression'))
    f.group(16, 52, 540, 380, 'coding', ('Op（delta/index.ts）', 'Op (delta/index.ts)'), None, 'diff', title_mono=False, gid='ops')
    D = [('["r", value]', ('替换根', 'replace the root')),
         ('["s", path, value]', ('设置字段 / 下标', 'set a field / index')),
         ('["d", path]', ('删除字段', 'delete a field')),
         ('["a", path, str]', ('字符串末尾追加', 'append to a string')),
         ('["t", path, n]', ('字符串去掉前 n 个字符', 'drop the first n chars of a string')),
         ('["p", path, start, del, items]', ('数组 splice', 'array splice')),
         ('["m", path, perm]', ('数组重排：new[i] = old[perm[i]]', 'reorder: new[i] = old[perm[i]]'))]
    for i, (a, b) in enumerate(D):
        y = 98 + i * 46
        f.chip(32, y, a[2], 'coding', size=11, h=24)
        f.text(70, y + 16, a, 10.2, 600, True, cls='strongt', layer='label')
        f.text(310, y + 16, b, 9.6, 450, cls='muted', layer='label')
        if i: hline(f, 32, 540, y - 10)
    # string emit
    f.group(572, 52, 532, 184, 'agent', ('字符串怎样变成 op', 'How a string change becomes ops'), None, 'code', title_mono=False, gid='str')
    f.text(588, 108, ('新值以旧值开头', 'new starts with old'), 9.8, 600, cls='strongt', layer='label')
    f.text(800, 108, '→ ["a", path, tail]', 9.8, 600, True, cls='muted', layer='label')
    f.text(588, 138, ('旧值的后缀是新值的前缀', 'old suffix = new prefix'), 9.8, 600, cls='strongt', layer='label')
    f.text(800, 138, '→ ["t", …] + ["a", …]', 9.8, 600, True, cls='muted', layer='label')
    f.text(588, 156, ('（重叠扫描最多 65,536 字符：滚动日志）', '(overlap scan up to 65,536 chars: rolling logs)'), 9.2, 450, cls='faint', layer='label')
    f.text(588, 186, ('其他情况', 'anything else'), 9.8, 600, cls='strongt', layer='label')
    f.text(800, 186, '→ ["s", path, new]', 9.8, 600, True, cls='muted', layer='label')
    f.text(588, 220, ('超过 4,096 个 op → 折叠成一个 ["r", 整个根]', 'more than 4,096 ops → fold into one ["r", whole root]'), 9.5, 600, cls='err', layer='label')
    # wire
    f.group(572, 252, 532, 180, 'ext', ('WireOp：只多两种压缩', 'WireOp: just two compressions'), None, 'compress', title_mono=False, gid='wire')
    f.text(588, 308, ('["#", id, path]：路径第二次出现时定义一个编号', '["#", id, path]: defines an id on a path\'s second use'), 9.6, 500, cls='strongt', layer='label')
    f.text(588, 330, ('之后用数字代替该路径', 'later ops reference it by number'), 9.4, 450, cls='muted', layer='label')
    f.text(588, 356, ('缩短的元组：同一批内复用上一个 op 的路径', 'shortened tuples reuse the previous op\'s path (within a batch)'), 9.6, 500, cls='strongt', layer='label')
    f.text(588, 386, ('编码器 / 解码器每个订阅一对，每个实例 × 成员一本字典；', 'one encoder / decoder per subscription, one dictionary per'), 9.4, 450, cls='muted', layer='label')
    f.text(588, 404, ('替换、不可用、关闭、重新 hydrate 时清空。', 'instance × member; cleared on replace, unavailable, close, hydrate.'), 9.4, 450, cls='muted', layer='label')
    # example
    codebox(f, 16, 448, 1088, [(0, ('draft.output += "done\\n"; draft.count += 1;   // 两次修改', 'draft.output += "done\\n"; draft.count += 1;   // two edits'), 'muted'),
                               (0, '→ ops  [["a", ["output"], "done\\n"], ["s", ["count"], 3]]', ''),
                               (0, ('→ wire [["a", ["output"], "done\\n"], ["s", ["count"], 3]]   // 路径各用一次，不定义编号', '→ wire [["a", ["output"], "done\\n"], ["s", ["count"], 3]]   // each path used once: no ids'), 'muted'),
                               (0, ('下一批再追加 output（第二次使用）→ ["#", 0, ["output"]], ["a", 0, "…"]', 'next batch appends to output (second use) → ["#", 0, ["output"]], ["a", 0, "…"]'), 'muted')],
            ('例：README 里的 { output, count }', 'Example: the README\'s { output, count }'))
    return f

# ============================================================== chord_bundle : bundler → manifest → loader
@reg
def chord_bundle():
    nb = Pkg('packages/chord/src/node/')
    nb.has('bundle.ts', 'const entryPrefix = `facet-${shortHash(input.entryName)}`;', 'entryNames: `${entryPrefix}-[hash]`', 'format: "cjs"', 'bundle: true', 'banner: { js: \'"use strict";\' }',
           'supported: { "dynamic-import": false }', '"node22.19"', '"es2022"', '.tmp-${randomUUID()}', '.old-${randomUUID()}')
    nb.has('manifest.ts', 'FACET_BUNDLE_FORMAT = "chord.facet-bundle"', 'FACET_BUNDLE_MANIFEST_FILE = "chord-facets.json"', 'FACET_BUNDLE_ARTIFACT_FORMAT = "chord.facet-bundle-artifact"')
    nb.has('bundle-loader.ts', 'import { compileFunction } from "node:vm";', 'required undeclared external import', 'createHash("sha256")', 'Facet bundle integrity check failed')
    nb.has('package.ts', 'metadata.peerDependencies')
    f = Fig('chord_bundle', 1120, 600, ('打包与加载 facet：esbuild → 清单 → 校验后在 node:vm 中运行', 'Bundling and loading facets: esbuild → manifest → verified, then run in node:vm'))
    E = f.edge
    f.node('pkg', 16, 80, 220, 76, 'coding', ('插件包', 'plugin package'), ('package.json 的 "chord": { facets }', 'package.json "chord": { facets }'), 'file', mono=False, tsize=11.5, ssize=9.2)
    f.node('bun', 286, 80, 250, 76, 'modes', 'bundleFacetPackage()', ('esbuild：cjs · bundle · 单文件', 'esbuild: cjs · bundled entries'), 'bolt', tsize=11, ssize=9.2, strong=True)
    f.node('out', 586, 80, 250, 76, 'infra', ('输出目录', 'output directory'), ('facet-<hash>.cjs + chord-facets.json', 'facet-<hash>.cjs + chord-facets.json'), 'box', mono=False, tsize=11.5, ssize=9.2)
    f.node('ld', 886, 80, 218, 76, 'agent', 'createFacetBundleLoader', ('load() → LoadedFacets', 'load() → LoadedFacets'), 'play', tsize=10.5, ssize=9.2, strong=True)
    E([(236, 118), (286, 118)], 'pkg', 'bun', 'main', 'coding')
    E([(536, 118), (586, 118)], 'bun', 'out', 'main', 'modes')
    E([(836, 118), (886, 118)], 'out', 'ld', 'main', 'infra')
    f.group(16, 180, 520, 216, 'modes', ('打包时', 'At bundle time'), 'node/bundle.ts', 'bolt', title_mono=False, gid='b')
    B = [('依赖包（peer）和 @earendil-works/chord 都标为 external', 'peers and @earendil-works/chord stay external'),
         ('入口名 facet-<12 位短哈希>-[hash]，扩展名 .cjs', 'entry names facet-<12-char hash>-[hash], .cjs'),
         ('target node22.19 或 es2022；不支持动态 import；"use strict" 横幅', 'target node22.19 or es2022; no dynamic import; "use strict" banner'),
         ('先写到 .<out>.tmp-<uuid>，再改名替换', 'write to .<out>.tmp-<uuid>, then rename into place'),
         ('旧目录先移到 .old-<uuid>；替换失败 → 移回', 'old dir moved to .old-<uuid>; swap fails → moved back')]
    for i, (a, b) in enumerate(zip(*[(x[0] for x in B), (x[1] for x in B)])):
        f.text(32, 232 + i * 32, '· ', 10, 600, cls='strongt', layer='label')
        f.text(44, 232 + i * 32, (a, b), 9.6, 450, cls='muted', layer='label')
    f.group(552, 180, 552, 216, 'infra', ('清单 chord-facets.json', 'Manifest chord-facets.json'), 'node/manifest.ts', 'file', title_mono=False, gid='m')
    codebox(f, 568, 220, 520, [(0, '{ "format": "chord.facet-bundle", "version": 2,', ''),
                               (1, '"plugin": { "id": …, "version": … },', ''),
                               (1, '"entries": [{', ''),
                               (2, '"file": "facet-….cjs",', ''),
                               (2, '"integrity": "sha256-…",', 'strongt'),
                               (2, '"externalImports": ["…"],', ''),
                               (2, '"sourceMap": … }] }', '')], None)
    f.group(16, 412, 1088, 140, 'agent', ('加载时：createFacetBundleLoader(...).load()', 'At load time: createFacetBundleLoader(...).load()'), 'node/bundle-loader.ts', 'shield', title_mono=False, gid='l')
    L = [('1', ('读清单', 'read manifest'), ('格式 / 版本必须匹配', 'format / version must match')),
         ('2', ('校验 SHA-256', 'verify SHA-256'), ('与 integrity 不符就拒绝', 'reject on integrity mismatch')),
         ('3', ('node:vm 编译', 'compile in node:vm'), ('compileFunction(code, …)', 'compileFunction(code, …)')),
         ('4', ('受限 require', 'restricted require'), ('未声明的 external → 报错', 'undeclared external → error')),
         ('5', ('校验 facets', 'validate facets'), ('然后交给 reload()', 'then hand to reload()'))]
    for i, (n, t, s) in enumerate(L):
        x = 52 + i * 212
        f.node(f'l{i}', x, 456, 180, 56, 'agent', t, s, None, mono=False, tsize=11, ssize=9.2, strong=(i == 1))
        f.step(n, x - 14, 456, 'agent', r=9)
        if i: E([(x - 32, 484), (x, 484)], f'l{i-1}', f'l{i}', 'main', 'agent')
    f.text(32, 536, ('也可以把整个包读成一个 artifact（readFacetBundleArtifact，格式 chord.facet-bundle-artifact）再用 createFacetBundleArtifactLoader 加载。', 'A bundle can also be read as one artifact (readFacetBundleArtifact, format chord.facet-bundle-artifact) and loaded with createFacetBundleArtifactLoader.'), 9.3, 450, cls='faint', layer='label')
    f.legend(24, 580, [('layer:modes', ('打包', 'bundling')), ('layer:infra', ('产物', 'artifacts')), ('layer:agent', ('加载', 'loading')), ('main', ('流程', 'flow'))])
    return f
