# chord deep dive. Same section schema as deep_agent.py; files: (path, regex, symbol, zh, en)
from pkgsrc import Pkg, users_of
K = Pkg('packages/chord/src/')
U = 'packages/chord/src/'
CAX = 'packages/coding-agent/src/experimental/services/'
SLIDE_KEYS = ['chord_arch', 'chord_facets', 'chord_reload', 'chord_services', 'chord_remote', 'chord_state', 'chord_delta', 'chord_bundle']
_LOC = K.total(); _US = users_of('@earendil-works/chord')
_USZ = '、'.join(f'`{a}`（{b} 个文件）' for a, b in _US); _USE = ', '.join(f'`{a}` ({b} files)' for a, b in _US)

INTRO = dict(
 takeaway=("`chord` 是 Pi 新架构的底座：一个**facet 宿主**把小的功能单元（facet）按依赖顺序装配、激活、热重载和释放；facet 之间只通过有类型的**服务**交流，而服务可以在同一进程里，也可以跨传输在另一个进程里；服务暴露的状态是**复制状态**——提供方用普通的赋值修改，chord 算出最小的 JSON delta 发给每个订阅者。另有 `./context`（取消与调用范围的值）、`./delta`（独立的变更追踪器）和 `./node`（用 esbuild 打包插件、带 SHA-256 校验地加载）。",
           "`chord` is the foundation of Pi's new architecture: a **facet host** assembles small units of functionality (facets) in dependency order, activates them, hot-reloads them and disposes them; facets talk only through typed **services**, which can live in the same process or in another one across a transport; the state services expose is **replicated state** — the provider changes it with plain assignments and chord computes the minimal JSON delta for every subscriber. Around that sit `./context` (cancellation and call-scoped values), `./delta` (a standalone change tracker) and `./node` (bundling plugins with esbuild and loading them with SHA-256 verification)."),
 role=(f"共 {_LOC:,} 行 TypeScript，唯一的运行时依赖是 esbuild，不依赖任何其他 pi 包。使用者：{_USZ}——`coding-agent` 里用到的都在 `src/experimental/` 下。",
       f"{_LOC:,} lines of TypeScript; the only runtime dependency is esbuild, and it depends on no other pi package. Users: {_USE} — everything `coding-agent` uses lives under `src/experimental/`."),
)

SECTIONS = [
dict(id="chord-arch", group="arch", layer="infra", diagram="chord_arch",
 title=("模块结构", "Module structure"),
 takeaway=("五块：API 与类型（`api.ts`、`types.ts`）、facet 宿主（`facets/host.ts` 里的 `FacetKernel`）、服务与复制状态（`services/`）、JSON delta（`delta/`，最大的一块）、以及 context 与 Node 打包加载（`context/`、`node/`）。五个导入路径各对应其中一块。",
           "Five blocks: API & types (`api.ts`, `types.ts`), the facet host (`FacetKernel` in `facets/host.ts`), services & replicated state (`services/`), JSON deltas (`delta/`, the largest), and context plus Node bundling and loading (`context/`, `node/`). Each of the five import paths maps to one of them."),
 points=[
  ("最大的单个文件是 `delta/tracker.ts`：它让提供方像改普通对象一样改状态（Draft 代理），再算出 op。", "The largest single file is `delta/tracker.ts`: it lets a provider change state like a plain object (a Draft proxy) and then computes the ops."),
  ("`./delta` 和 `./context` 可以单独使用，不需要 facet 宿主；`./bundler` 与 `./node` 只在 Node 上需要。", "`./delta` and `./context` work on their own without the facet host; `./bundler` and `./node` are only needed on Node."),
  ("`durable` 是最大的使用者：它的 `viewState()`、`watch()` 和任务图都是 chord 的复制状态，每次异步调用都带一个 chord `Context`。", "`durable` is the biggest user: its `viewState()`, `watch()` and task graph are chord replicated states, and every async call takes a chord `Context`."),
 ],
 how=[
  ("`defineService<T>(id)` 定义令牌，`defineFacet({ id, setup })` 定义功能单元。", "`defineService<T>(id)` defines a token, `defineFacet({ id, setup })` a unit of functionality."),
  ("`createFacetHost({ facets, serviceSources? })` 装配并激活，返回 `{ services, reload, dispose }`。", "`createFacetHost({ facets, serviceSources? })` assembles and activates, returning `{ services, reload, dispose }`."),
  ("跨进程时，一边 `createRemoteServiceEndpoint(provider)`，另一边 `createRemoteServiceBinding({ transport, … })`。", "Across processes, one side uses `createRemoteServiceEndpoint(provider)` and the other `createRemoteServiceBinding({ transport, … })`."),
 ],
 files=[
  (U + "index.ts", r"api\.ts", "export …", "包入口", "package entry"),
  (U + "api.ts", r"^export async function createFacetHost\(", "createFacetHost()", "宿主入口", "host entry"),
  (U + "types.ts", r"^export interface FacetEnvironment", "FacetEnvironment", "setup 的参数", "setup's argument"),
  (U + "facets/host.ts", r"^export class FacetKernel", "FacetKernel", "宿主内核", "the host kernel"),
  (U + "delta/tracker.ts", r"^export function track<", "track()", "变更追踪器", "the change tracker"),
 ]),

dict(id="chord-facets", group="flows", layer="infra", diagram="chord_facets",
 title=("Facet 的一代：装配与激活", "A facet generation: assembly and activation"),
 takeaway=("`activate()` 依次经过 setup → assembling → connecting → activating → active：先同步调用每个 facet 的 `setup(env)` 收集它要用和要提供的服务，再整体校验（一个服务一个提供者、模式一致、无环），按拓扑顺序给出激活顺序，等所有远程绑定 ready，最后按顺序运行各自的 `onActivate`。释放按相反顺序进行。",
           "`activate()` goes setup → assembling → connecting → activating → active: each facet's `setup(env)` runs synchronously to collect what it uses and provides, the whole graph is validated (one provider per service, matching modes, no cycles), a topological sort gives the activation order, every remote binding is awaited until ready, and each `onActivate` runs in order. Disposal runs in reverse."),
 points=[
  ("`setup` 必须同步：返回 Promise 会被拒绝。这让依赖图在任何异步工作开始前就是完整、可校验的。", "`setup` must be synchronous: returning a Promise is rejected. That makes the dependency graph complete and checkable before any async work starts."),
  ("校验错误都带着服务和 facet 的名字：\"is provided by both …\"、\"… but no facet provides it\"、\"Facet dependency cycle: …\"。", "Validation errors name the service and facets: \"is provided by both …\", \"… but no facet provides it\", \"Facet dependency cycle: …\"."),
  ("任何一步失败，`#terminate()` 释放已经建好的部分，把原错误和清理错误合成一个 AggregateError 抛出。", "If any step fails, `#terminate()` disposes what was built and throws the original error together with cleanup errors as one AggregateError."),
  ("每个 facet 内部，`own()` 登记的释放函数也按逆序执行——后建的先拆。", "Within each facet, the disposals registered with `own()` also run in reverse — last built, first torn down."),
 ],
 how=[
  ("`FacetKernel.activate()`：对每个 facet 调 `setup`，得到 `FacetShape`（requires / provides）。", "`FacetKernel.activate()`: call `setup` for each facet to get its `FacetShape` (requires / provides)."),
  ("`#resolveExternalServices()` 读宿主的 `serviceSources` 目录 → `validateFacets()` → `topologicalOrder()`。", "`#resolveExternalServices()` reads the host's `serviceSources` catalogues → `validateFacets()` → `topologicalOrder()`."),
  ("绑定服务 → 等待 `ready()` → 按 `#activationOrder` 逐个 `activate()`。", "Bind services → await `ready()` → `activate()` each facet in `#activationOrder`."),
 ],
 files=[
  (U + "facets/host.ts", r"this\.#phase = \"assembling\";", "activate()", "激活一代", "activating a generation"),
  (U + "facets/host.ts", r"^function validateFacets\(", "validateFacets()", "整图校验", "graph validation"),
  (U + "facets/host.ts", r"^function topologicalOrder\(", "topologicalOrder()", "激活顺序", "activation order"),
  (U + "facets/host.ts", r"^\tasync #terminate\(", "#terminate()", "失败清理", "cleanup on failure"),
  (U + "facets/host.ts", r"^async function disposeFacetRecords\(", "disposeFacetRecords()", "逆序释放", "reverse disposal"),
 ]),

dict(id="chord-reload", group="flows", layer="infra", diagram="chord_reload",
 title=("热重载", "Hot reload"),
 takeaway=("`reload(facets)` 用新实现替换一组已激活的 facet，而使用方手里的句柄不断开：先 setup 候选并检查它们的 requires / provides 与旧的完全相同，再在旧实现仍然服务请求时激活候选，然后**切换**（单例重新绑定、远程提供者 `replace()`），再退役旧 facet、连接新的 keyed 实例。",
           "`reload(facets)` replaces a set of active facets with new implementations without disconnecting anyone's handles: set up the candidates and check their requires / provides are exactly the same, activate them while the old ones still serve, then **cut over** (rebind singletons, `replace()` remote providers), retire the old facets and connect the new keyed instances."),
 points=[
  ("形状不变是硬性要求：重载不能增删依赖或提供的服务（\"must preserve its service requirements and provisions\"）。改形状需要新的一代。", "Unchanged shape is a hard rule: a reload cannot add or remove dependencies or provisions (\"must preserve its service requirements and provisions\"). Changing the shape needs a new generation."),
  ("切换之前失败：释放候选，宿主回到 active，旧实现继续工作。切换之后失败：整个代被中止（\"Facet reload failed after cutover\"）。", "A failure before the cutover disposes the candidates and returns to active with the old code still working. After the cutover, the whole generation is aborted (\"Facet reload failed after cutover\")."),
  ("句柄是代理：每次访问都通过 `ServiceSlot.resolve()` 取当前实现，所以重新 `bind` 之后已有句柄立即用上新代码。", "Handles are proxies: every access resolves the current implementation through `ServiceSlot.resolve()`, so after a rebind existing handles use the new code immediately."),
  ("keyed 实例按 generation 区分：重载后旧实例关闭，新实例以新的 generation 出现，观察者会看到 closed 再 spawned。", "Keyed instances are generation-specific: after a reload the old ones close and new ones appear with new generations, so observers see closed then spawned."),
 ],
 how=[
  ("宿主先用 loader 的 `load()` 拿到候选的 `LoadedFacets`。", "The host first gets the candidate `LoadedFacets` from a loader's `load()`."),
  ("`host.reload(loaded.facets)`；失败就释放候选。", "`host.reload(loaded.facets)`; on failure, dispose the candidate."),
  ("成功后再释放退役的那一代 `LoadedFacets`，旧代码随之可以被回收。", "After success, dispose the retired `LoadedFacets`, so the old code can be collected."),
 ],
 files=[
  (U + "facets/host.ts", r"^\tasync reload\(facets", "reload()", "重载流程", "the reload flow"),
  (U + "facets/host.ts", r"^function sameFacetShape\(", "sameFacetShape()", "形状检查", "shape check"),
  (U + "facets/host.ts", r"^\tasync #abort\(", "#abort()", "切换后失败", "failure after cutover"),
  (U + "services/handle.ts", r"^export class ServiceSlot", "ServiceSlot", "可重新绑定的槽", "the rebindable slot"),
  (U + "services/instances.ts", r"^export class InstanceDirectory", "InstanceDirectory", "keyed 实例与代", "keyed instances and generations"),
 ]),

dict(id="chord-services", group="types", layer="infra", diagram="chord_services",
 title=("服务、句柄与 Context", "Services, handles and Context"),
 takeaway=("服务令牌是 `defineService<T>(id, options?)`。默认是**远程**服务：它的成员只能是 `(…json, Context) => Promise<json>` 或 `ReplicatedState<json>`，这样同一份接口既能在进程内用，也能跨传输用；`{ local: true }` 的服务可以是任意 TypeScript 形状，但永远不出本进程。提供方式有单例（`provide` / `use`）与 keyed（`provideMany` / `observe`）两种。",
           "A service token is `defineService<T>(id, options?)`. By default it is **remote**: its members must be `(…json, Context) => Promise<json>` or `ReplicatedState<json>`, so one interface works both in-process and across a transport; a `{ local: true }` service can have any TypeScript shape but never leaves the process. Provision is either singleton (`provide` / `use`) or keyed (`provideMany` / `observe`)."),
 points=[
  ("远程约束在类型层面检查（`RemoteServiceContract<T>`），运行时在边界上再校验一次（`validateRemoteServiceImplementation`）。", "The remote constraint is checked in the type system (`RemoteServiceContract<T>`) and again at runtime at the boundary (`validateRemoteServiceImplementation`)."),
  ("`coding-agent` 的实验服务就是例子：`pi.transcript` 只有一个 `state: ReplicatedState<ConversationView>`；`pi.local.presentation-ui` 是本地服务。", "`coding-agent`'s experimental services are examples: `pi.transcript` has just `state: ReplicatedState<ConversationView>`; `pi.local.presentation-ui` is a local service."),
  ("每个调用最后一个参数都是 `Context`：它携带取消信号和调用范围的值。`awaitWithContext()` 取消时只拒绝等待者，不会中止正在进行的工作。", "Every call's last argument is a `Context`: it carries cancellation and call-scoped values. `awaitWithContext()` on cancellation rejects only the waiter, never the work in progress."),
  ("ID 以 `$chord.` 开头的服务是保留的：那是 chord 自己的控制调用。", "Service IDs starting with `$chord.` are reserved: that prefix is chord's own control calls."),
 ],
 how=[
  ("`export const Models = defineService<Models>(\"pi.models\")`——类型和令牌同名。", "`export const Models = defineService<Models>(\"pi.models\")` — the type and the token share a name."),
  ("在 facet 的 setup 里：`const models = env.use(Models)`；在 onActivate 或之后调用 `await models.select(m, ctx)`。", "In a facet's setup: `const models = env.use(Models)`; from onActivate on, call `await models.select(m, ctx)`."),
  ("取消：`const { context, cancel } = withCancel(parent)`，把 `context` 传下去。", "Cancellation: `const { context, cancel } = withCancel(parent)` and pass `context` down."),
 ],
 files=[
  (U + "api.ts", r"^export function defineService\(id: string", "defineService()", "服务令牌", "service tokens"),
  (U + "types.ts", r"^export type RemoteServiceContract<T>", "RemoteServiceContract", "远程约束", "the remote constraint"),
  (U + "services/provider.ts", r"^export function validateRemoteServiceImplementation\(", "validateRemoteServiceImplementation()", "运行时校验", "runtime check"),
  (U + "context/index.ts", r"^export function withCancel\(", "withCancel()", "取消", "cancellation"),
  (U + "context/index.ts", r"^export function awaitWithContext<", "awaitWithContext()", "只取消等待者", "cancel the waiter only"),
  (CAX + "transcript.ts", r"^export const Transcript = defineService", "pi.transcript", "一个真实的服务", "a real service"),
 ]),

dict(id="chord-remote", group="flows", layer="infra", diagram="chord_remote",
 title=("跨进程的服务", "Services across processes"),
 takeaway=("提供方一侧由 `RemoteServiceProvider` 执行调用、管理订阅，`createRemoteServiceEndpoint()` 处理 `$chord.service` 控制调用（catalogue、subscribe、unsubscribe）；使用方一侧的 `createRemoteServiceBinding()` 给出与本地一样的外观。中间的传输只要实现 `invoke` 与 `subscribe`，外层信封由应用决定。",
           "On the provider side, `RemoteServiceProvider` runs calls and manages subscriptions, and `createRemoteServiceEndpoint()` serves the `$chord.service` control calls (catalogue, subscribe, unsubscribe); on the consumer side, `createRemoteServiceBinding()` gives the same facade as a local service. The transport in between only implements `invoke` and `subscribe`; the outer envelope is up to the application."),
 points=[
  ("订阅更新有 6 种：`state`（某成员的一批 op）、`reset`、`unavailable`、`replaced`、`spawned`、`closed`。", "Subscription updates come in 6 kinds: `state` (a batch of ops for one member), `reset`, `unavailable`, `replaced`, `spawned`, `closed`."),
  ("背压：每个订阅最多 100 个待发更新；第 101 个到来时整个队列换成一个 `reset`，带着当前完整快照和新的 sequence 基线。", "Backpressure: at most 100 pending updates per subscription; when the 101st arrives the whole queue becomes one `reset` with a full current snapshot and new sequence baselines."),
  ("普通 `state` 更新绝不允许跳号；传输适配器必须保持快照 / reset / 更新的顺序，不能丢批。", "An ordinary `state` update never permits a gap; transport adapters must keep snapshot / reset / update order and must not drop batches."),
  ("能跨边界的错误只有 8 个 `service_*` 码，例如 `service_not_found`、`service_stale_instance`、`service_invalid_value`。", "Only 8 `service_*` codes may cross the boundary, e.g. `service_not_found`, `service_stale_instance`, `service_invalid_value`."),
 ],
 how=[
  ("提供方：用宿主的 provider 创建 `createRemoteServiceEndpoint(provider)`，把收到的调用交给它。", "Provider: create `createRemoteServiceEndpoint(provider)` from the host's provider and hand it incoming calls."),
  ("使用方：实现 `RemoteServiceTransport`；再实现一个 `RemoteServiceSource`（`catalogue()` + `open()`），在 `open()` 里用 `createRemoteServiceBinding({ services, transport })`，作为宿主的 `serviceSources` 传入——`coding-agent` 的 `experimental/services/connection.ts` 就是这样做的。", "Consumer: implement `RemoteServiceTransport`; then a `RemoteServiceSource` (`catalogue()` + `open()`) whose `open()` uses `createRemoteServiceBinding({ services, transport })`, passed to the host in `serviceSources` — as `coding-agent`'s `experimental/services/connection.ts` does."),
  ("同进程测试：`createLoopbackServiceTransport(provider)` 直接把两边接起来。", "In-process tests: `createLoopbackServiceTransport(provider)` wires both sides directly."),
 ],
 files=[
  (U + "services/provider.ts", r"^export class RemoteServiceProvider", "RemoteServiceProvider", "提供方", "the provider"),
  (U + "services/provider.ts", r"^\t#emit\(registration", "#emit()", "100 → reset", "100 → reset"),
  (U + "services/provider.ts", r"^export function createRemoteServiceEndpoint\(", "createRemoteServiceEndpoint()", "控制调用", "control calls"),
  (U + "services/consumer.ts", r"^export class RemoteServiceBindingImpl", "RemoteServiceBindingImpl", "使用方外观", "the consumer facade"),
  (U + "services/wire.ts", r"^const SERVICE_CONTROL_ID = ", "$chord.service", "控制服务 ID", "control service ID"),
  (U + "services/errors.ts", r"^export const REMOTE_SERVICE_ERROR_CODES", "REMOTE_SERVICE_ERROR_CODES", "8 个错误码", "8 error codes"),
  (U + "types.ts", r"^export interface RemoteServiceSource", "RemoteServiceSource", "外部服务来源", "external service sources"),
 ]),

dict(id="chord-state", group="flows", layer="infra", diagram="chord_state",
 title=("复制状态", "Replicated state"),
 takeaway=("`env.replicatedState(initial)` 返回一个可变的复制状态。`change(ctx, draft => …)` 在一个 Draft 上做普通的赋值，chord 算出 op、换上新的不可变版本、sequence 加一，然后发给两类订阅者：内部的精确订阅（同步拿到每个版本的 op，用来编码给远端）和公开的 `subscribe()`（每个订阅串行收到完整值）。",
           "`env.replicatedState(initial)` returns a mutable replicated state. `change(ctx, draft => …)` makes plain assignments on a Draft; chord computes the ops, swaps in the new immutable revision, increments the sequence and publishes to two kinds of subscriber: internal exact subscriptions (every revision's ops, synchronously, for encoding to remotes) and public `subscribe()` (complete values, serialized per subscription)."),
 points=[
  ("一次 `change()` 恰好发布一个原子版本；回调抛错时值和 sequence 都不变；没有产生 op 就不发布。", "A successful `change()` publishes exactly one atomic revision; if the callback throws, value and sequence stay unchanged; no ops, no publication."),
  ("回调必须同步，也不能在回调里再次 change（\"cannot be changed reentrantly\"）。", "The callback must be synchronous and cannot change the state again from inside (\"cannot be changed reentrantly\")."),
  ("公开订阅最多积压 100 个值，溢出时只留最新的——所以公开的 sequence 可能跳号；异步回调里应读捕获的 `value` 而不是 `state.value`。", "Public subscriptions keep at most 100 pending values and keep only the newest on overflow — so public sequences may skip; async callbacks should read the captured `value`, not `state.value`."),
  ("远端副本严格按序：`update` 要求 sequence 正好是上一个加一，否则清空并抛出 \"update sequence has a gap\"。", "The remote replica is strictly ordered: `update` requires exactly the previous sequence plus one, else it clears and throws \"update sequence has a gap\"."),
 ],
 how=[
  ("`status.change(ctx, d => { d.output += \"done\\n\"; d.count += 1 })`。", "`status.change(ctx, d => { d.output += \"done\\n\"; d.count += 1 })`."),
  ("内部：`tracker.beginChange()` → 回调 → `prepare()` → `adopt()` → `publisher.publish(value, ops, ctx)`。", "Internally: `tracker.beginChange()` → callback → `prepare()` → `adopt()` → `publisher.publish(value, ops, ctx)`."),
  ("远端：`ReplicatedStateReplica.hydrate(seq, ops)` 建立基线，之后每个 `update(seq, ops)` 用 `applyImmutable` 重放。", "Remote: `ReplicatedStateReplica.hydrate(seq, ops)` sets the baseline, then each `update(seq, ops)` replays with `applyImmutable`."),
 ],
 files=[
  (U + "services/state.ts", r"^export class MutableReplicatedStateImpl", "MutableReplicatedStateImpl", "可变状态", "mutable state"),
  (U + "services/state.ts", r"^\tchange\(context: Context", "change()", "一次变更", "one change"),
  (U + "services/state.ts", r"^export class ReplicatedStateReplica", "ReplicatedStateReplica", "远端副本", "the remote replica"),
  (U + "services/state.ts", r"^\tupdate\(sequence: number", "update()", "按序检查", "order check"),
  (U + "services/state-codec.ts", r"^export function createServiceStateEncoder\(", "createServiceStateEncoder()", "每个订阅的编码器", "per-subscription encoder"),
 ]),

dict(id="chord-delta", group="types", layer="infra", diagram="chord_delta",
 title=("JSON delta", "JSON deltas"),
 takeaway=("`./delta` 定义 7 种 op：`r` 替换根、`s` 设置、`d` 删除、`a` 字符串追加、`t` 字符串去头、`p` 数组 splice、`m` 数组重排。追踪器为字符串挑最省的写法（追加；或去头加追加——适合滚动日志；否则整体设置），op 太多时折叠成一个 `r`。线上格式 WireOp 只多两种压缩：路径编号和省略路径。",
           "`./delta` defines 7 ops: `r` replace root, `s` set, `d` delete, `a` string append, `t` string front-truncate, `p` array splice, `m` array permute. The tracker picks the cheapest string form (append; or truncate plus append — good for rolling logs; else a set) and folds into one `r` when there are too many ops. The wire format WireOp adds only two compressions: path ids and omitted paths."),
 points=[
  ("超过 4,096 个 op 时折叠成 `[\"r\", 整个根]`；去头 + 追加的重叠扫描最多 65,536 个字符。", "More than 4,096 ops fold into `[\"r\", whole root]`; the truncate-plus-append overlap scan covers up to 65,536 characters."),
  ("路径在**第二次**使用时才定义编号（`[\"#\", id, path]`），因为定义比路径本身还长，只用一次的路径内联更省。", "A path gets an id on its **second** use (`[\"#\", id, path]`), because a definition costs more than the path; paths used once stay inline."),
  ("省略路径只在同一批内有效；跨批的唯一状态是编号字典，遇到 `r` 就清空——每个 `r` 都是一个恢复点。", "Omitted paths only work within a batch; the only cross-batch state is the id dictionary, cleared at every `r` — each `r` is a recovery point."),
  ("值是不可变、结构共享的：没变的子树在版本之间共用，不做防御性拷贝也不冻结。", "Values are immutable and structurally shared: unchanged subtrees are reused across revisions, with no defensive copies and no freezing."),
 ],
 how=[
  ("`const tracker = track(initial)`；`const change = tracker.beginChange()`；改 `change.state`。", "`const tracker = track(initial)`; `const change = tracker.beginChange()`; mutate `change.state`."),
  ("`const prepared = change.prepare()`；`tracker.adopt(prepared)`；副本用 `applyImmutable(prepared.base, prepared.ops)`。", "`const prepared = change.prepare()`; `tracker.adopt(prepared)`; a replica uses `applyImmutable(prepared.base, prepared.ops)`."),
  ("跨边界：`encoder().encode(ops)` → 发送 → `decoder().decode(wire)`。", "Across a boundary: `encoder().encode(ops)` → send → `decoder().decode(wire)`."),
 ],
 files=[
  (U + "delta/index.ts", r"^export type Op =", "Op", "7 种 op", "the 7 ops"),
  (U + "delta/index.ts", r"^export type WireOp =", "WireOp", "线上格式", "the wire format"),
  (U + "delta/index.ts", r"^export function encoder\(\)", "encoder()", "第二次使用时编号", "ids on second use"),
  (U + "delta/tracker.ts", r"^const MAX_DELTA_OPERATIONS = ", "MAX_DELTA_OPERATIONS", "折叠上限", "fold limit"),
  (U + "delta/index.ts", r"^export function applyImmutable<", "applyImmutable()", "重放", "replay"),
  (U + "delta/diff.ts", r"^export function diffRevisions\(", "diffRevisions()", "两个版本的差异", "diffing two revisions"),
 ]),

dict(id="chord-bundle", group="flows", layer="infra", diagram="chord_bundle",
 title=("打包与加载插件", "Bundling and loading plugins"),
 takeaway=("`bundleFacetPackage()` 读插件包 `package.json` 里的 `chord.facets`，用 esbuild 打成 `.cjs`（peer 依赖和 chord 本身保持 external），写出 `chord-facets.json` 清单，每个入口带 SHA-256 完整性值。`createFacetBundleLoader()` 加载时先校验哈希，再用 `node:vm` 的 `compileFunction` 编译，只允许 require 清单里声明过的 external。",
           "`bundleFacetPackage()` reads `chord.facets` from a plugin's `package.json`, bundles it with esbuild into `.cjs` (peer dependencies and chord itself stay external) and writes a `chord-facets.json` manifest with a SHA-256 integrity value per entry. `createFacetBundleLoader()` verifies the hash at load time, compiles with `node:vm`'s `compileFunction`, and lets the code require only externals the manifest declares."),
 points=[
  ("输出先写到临时目录，再整体改名替换；旧目录先挪到 `.old-<uuid>`，替换失败就挪回来——加载方永远看不到写了一半的包。", "Output goes to a temporary directory and is renamed into place; the old directory is moved to `.old-<uuid>` first and moved back if the swap fails — a loader never sees a half-written bundle."),
  ("入口文件名带内容哈希（`facet-<短哈希>-[hash].cjs`），不同版本不会互相覆盖。", "Entry file names carry content hashes (`facet-<short hash>-[hash].cjs`), so versions never overwrite each other."),
  ("也可以把整个包读成一个 artifact（`readFacetBundleArtifact`）再加载，适合把插件作为一个值传递。", "A bundle can also be read as one artifact (`readFacetBundleArtifact`) and loaded from that, handy for passing a plugin around as one value."),
 ],
 how=[
  ("构建：`bundleFacetPackage({ packagePath, outdir })`。", "Build: `bundleFacetPackage({ packagePath, outdir })`."),
  ("加载：`createFacetBundleLoader({ manifestPath, entry, resolveExternal? })` → `load()` 得到 `LoadedFacets`；完整性校验默认开启（`verifyIntegrity`）。", "Load: `createFacetBundleLoader({ manifestPath, entry, resolveExternal? })` → `load()` gives `LoadedFacets`; the integrity check is on by default (`verifyIntegrity`)."),
  ("交给 `host.reload(loaded.facets)` 热替换，或作为新一代的 facets。", "Hand them to `host.reload(loaded.facets)` for a hot swap, or use them for a new generation."),
 ],
 files=[
  (U + "node/package.ts", r"^export async function bundleFacetPackage\(", "bundleFacetPackage()", "打包插件包", "bundling a package"),
  (U + "node/bundle.ts", r"^export async function bundleFacets\(", "bundleFacets()", "esbuild 与原子替换", "esbuild and the atomic swap"),
  (U + "node/manifest.ts", r"^export interface FacetBundleManifest", "FacetBundleManifest", "清单格式", "manifest format"),
  (U + "node/bundle-loader.ts", r"^export function createFacetBundleLoader\(", "createFacetBundleLoader()", "校验并加载", "verify and load"),
  (U + "node/bundle-loader.ts", r"^export async function readFacetBundleArtifact\(", "readFacetBundleArtifact()", "artifact 形式", "artifact form"),
 ]),
]

EXT_POINTS = [
 ("defineFacet({ id, setup })", ("写一个功能单元：在 setup 里声明 use / provide。", "Write a unit of functionality: declare use / provide in setup.")),
 ("defineService<T>(id, { local? })", ("定义一个服务契约，远程或本地。", "Define a service contract, remote or local.")),
 ("RemoteServiceTransport", ("实现 invoke / subscribe，把服务接到任何传输上。", "Implement invoke / subscribe to carry services over any transport.")),
 ("FacetLoader", ("load() 返回 LoadedFacets：静态、组合或从打包文件加载。", "load() returns LoadedFacets: static, combined or from bundles.")),
 ("RemoteServiceSource", ("catalogue() + open()：把另一个进程的服务目录接进宿主。", "catalogue() + open(): plug another process's service catalogue into a host.")),
 ("createContextKey<T>()", ("定义调用范围的值，随 Context 传下去。", "Define call-scoped values carried by a Context.")),
 ("track() · encoder() / decoder()", ("单独使用 delta 追踪与线上编码。", "Use delta tracking and wire encoding on their own.")),
]
XREF = [('durable', ('viewState / watch / 任务图都是 chord 复制状态；每个调用带 chord Context', 'viewState / watch / the task graph are chord replicated states; every call takes a chord Context')),
        ('coding-agent', ('src/experimental 里的服务（pi.transcript、pi.models …）', 'the services in src/experimental (pi.transcript, pi.models …)')),
        ('env', ('RemoteExecutionEnv 的方法都带 chord Context', 'RemoteExecutionEnv methods take a chord Context'))]
