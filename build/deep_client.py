# pi-client deep dive. Same section schema as deep_agent.py; files: (path, regex, symbol, zh, en)
from pkgsrc import Pkg
C_ = Pkg('packages/client/src/')
U = 'packages/client/src/'
CA = 'packages/coding-agent/src/experimental/'
SLIDE_KEYS = ['cli_arch', 'cli_lifecycle', 'cli_request', 'cli_subscribe', 'cli_attach', 'cli_transport', 'cli_discover', 'cli_errors']
_TS = C_.total()

INTRO = dict(
 takeaway=("`pi-client` 是远程 pi 会话的客户端一端，且与传输无关：你给它一个 `ByteTransportFactory`，它负责握手（并核对物理端点报告的逻辑 `serverId`）、按 id 关联请求、取消、带外附着和带缓冲的服务订阅。它不构造类型化的服务代理——`createClientServiceTransport()` 把一个按需解析的路由适配成 Chord 的 `RemoteServiceTransport`，类型由应用的 Chord 绑定提供。它从不自动重连。",
           "`pi-client` is the client end of remote pi sessions, and transport-neutral: give it a `ByteTransportFactory` and it handles the handshake (checking the logical `serverId` the physical endpoint reports), id-correlated requests, cancellation, out-of-band attachments and buffered service subscriptions. It builds no typed service proxies: `createClientServiceTransport()` adapts a lazily resolved route into a Chord `RemoteServiceTransport`, and types come from the application's Chord bindings. It never reconnects on its own."),
 role=(f"{_TS:,} 行 TypeScript，两个导入路径：运行时无关的根入口 `\".\"`，以及只在 Node / Bun 上可用的 `\"./unix\"`（Unix socket 传输与发现）。依赖 `chord` 与 `pi-protocol`。唯一的使用者是 coding-agent 的 `experimental/` 运行时。",
       f"{_TS:,} lines of TypeScript, two import paths: the runtime-neutral root `\".\"` and the Node / Bun-only `\"./unix\"` (Unix-socket transport and discovery). Depends on `chord` and `pi-protocol`. Its only user is coding-agent's `experimental/` runtime."),
)

SECTIONS = [
dict(id="cli-arch", group="arch", layer="modes", diagram="cli_arch",
 title=("一个 Client、一个 Connection、一个可替换的传输", "One Client, one Connection, a pluggable transport"),
 takeaway=("`Client`（client.ts）面向调用方：请求、订阅、附着与监听器；它内部的 `Connection`（connection.ts）管状态机、握手和 `ServerMessageDecoder`；字节的进出全部经过 `ByteTransport` 契约（transport.ts）。`unix.ts` 是一个独立子路径，提供 Unix socket 传输与本机服务器发现。",
           "`Client` (client.ts) faces the caller: requests, subscriptions, attachments and listeners; its internal `Connection` (connection.ts) owns the state machine, the handshake and the `ServerMessageDecoder`; every byte goes through the `ByteTransport` contract (transport.ts). `unix.ts` is a separate subpath with a Unix-socket transport and local server discovery."),
 points=[
  ("根入口不碰 Node API：浏览器或 worker 也可以用，只要提供自己的传输（例如 WebSocket）。", "The root entry touches no Node APIs: a browser or worker can use it with its own transport (a WebSocket, say)."),
  ("`Client` 只认 `@earendil-works/chord` 的服务控制调用（目录、订阅、退订）和状态解码器，不解释任何应用契约。", "`Client` knows only `@earendil-works/chord`'s service-control calls (catalogue, subscribe, unsubscribe) and state decoder; it interprets no application contract."),
  ("coding-agent 里有两种传输：`createUnixTransportFactory()` 和 radius-relay.ts 的 WebSocket 中继传输。", "coding-agent uses two transports: `createUnixTransportFactory()` and the WebSocket relay transport in radius-relay.ts."),
 ],
 how=[
  ("`const client = await Client.connect({ serverId, transportFactory })`：失败时它会自己 `dispose()`。", "`const client = await Client.connect({ serverId, transportFactory })`: on failure it disposes itself."),
  ("低层调用：`client.request({ serverId: client.serverId }, { serviceId, member, args })`。", "A low-level call: `client.request({ serverId: client.serverId }, { serviceId, member, args })`."),
  ("类型化调用：把 `createClientServiceTransport(client, getTarget)` 交给 Chord 绑定。", "Typed calls: hand `createClientServiceTransport(client, getTarget)` to a Chord binding."),
 ],
 files=[
  (U + "index.ts", r"^export \{ Client, createClientServiceTransport \}", "index.ts", "根入口", "the root entry"),
  (U + "client.ts", r"^export class Client", "Client", "面向调用方", "the caller-facing class"),
  (U + "connection.ts", r"^export class Connection", "Connection", "状态机与握手", "state machine and handshake"),
  (U + "transport.ts", r"^export interface ByteTransport \{", "ByteTransport", "传输契约", "the transport contract"),
  (U + "unix.ts", r"^export function createUnixTransportFactory", "createUnixTransportFactory()", "Unix 传输", "the Unix transport"),
 ]),

dict(id="cli-lifecycle", group="flows", layer="modes", diagram="cli_lifecycle",
 title=("连接的三个状态", "Three connection states"),
 takeaway=("`Connection` 在 `disconnected → connecting → connected` 之间切换。每次 `connect()` 都是一次带新序号的尝试：调用工厂得到一个全新的传输，先发客户端 `hello`，再等待服务端 `hello`，并要求其中的 `serverId` 与期望值完全一致。任何失败、关闭或 `disconnect()` 都回到 `disconnected`。",
           "`Connection` moves between `disconnected → connecting → connected`. Every `connect()` is an attempt with a new sequence number: the factory builds a fresh transport, the client `hello` goes first, then the server `hello` must arrive with exactly the expected `serverId`. Any failure, close or `disconnect()` returns to `disconnected`."),
 points=[
  ("旧尝试的回调带着旧 id，被 `#isCurrent(id)` 过滤掉；工厂迟到返回的传输会被直接 `close()`。", "Callbacks from an old attempt carry its id and are filtered by `#isCurrent(id)`; a transport the factory returns late is simply closed."),
  ("握手前的数据、第一条不是 `hello`、握手后再来 `hello` / `hello_error`，都是协议错误。", "Data before the client hello, a first message other than `hello`, or another `hello` / `hello_error` after connecting are all protocol errors."),
  ("进入 `disconnected` 时 `Client` 清空 hello 与附着、拒绝全部挂起请求、丢弃全部订阅，再通知 `onConnectionStateChange`。", "Entering `disconnected`, the `Client` clears hello and the attachment, rejects every pending request, drops every subscription, then notifies `onConnectionStateChange`."),
 ],
 how=[
  ("`client.onConnectionStateChange(({ state, error }) => …)` 观察状态；`client.connectionState` 读取当前值。", "Observe with `client.onConnectionStateChange(({ state, error }) => …)`; read `client.connectionState` for the current value."),
  ("`maxFrameLength` 必须是 1 到 0xffffffff 的安全整数，否则构造时抛 TypeError。", "`maxFrameLength` must be a safe integer from 1 to 0xffffffff, or the constructor throws a TypeError."),
  ("关闭时解码器 `end()`：残留半帧会变成截断错误，作为断开原因上报。", "On close the decoder `end()`s: a leftover partial frame becomes a truncation error, reported as the disconnect reason."),
 ],
 files=[
  (U + "connection.ts", r"^\tconnect\(\): Promise<ServerHello>", "connect()", "开始一次尝试", "start an attempt"),
  (U + "connection.ts", r"^\tasync #openTransport", "#openTransport()", "打开传输并发 hello", "open the transport, send hello"),
  (U + "connection.ts", r"^\t#handleMessage\(message: ServerMessage\)", "#handleMessage()", "握手校验", "handshake checks"),
  (U + "connection.ts", r"^\t#fail\(error: Error\)", "#fail()", "回到 disconnected", "back to disconnected"),
  (U + "client.ts", r"^\t#handleConnectionStateChange", "#handleConnectionStateChange()", "断开时的清理", "cleanup on disconnect"),
 ]),

dict(id="cli-request", group="flows", layer="modes", diagram="cli_request",
 title=("一个请求的一生", "The life of one request"),
 takeaway=("`#request()` 先过三道守卫（已 dispose、未连接、已 abort），通过后才分配 `request-N` 并登记到 `#pendingRequests`，再编码、发送。回应按 id 取回条目：`ok: true` 解析结果，`ok: false` 变成带 code 的 `ServerError`。abort 立即在本地拒绝，并在已发送时补发一条 `cancel`。",
           "`#request()` passes three guards first (disposed, not connected, already aborted), and only then allocates `request-N`, registers it in `#pendingRequests`, encodes and sends. A response takes the entry back by id: `ok: true` resolves the result, `ok: false` becomes a `ServerError` with a code. An abort rejects locally at once and, if the request was sent, follows up with a `cancel`."),
 points=[
  ("回应可以乱序到达；没有对应条目的回应是协议错误，会断开连接。", "Responses may arrive out of order; a response with no matching entry is a protocol error and drops the connection."),
  ("abort 之后条目留在表里，直到服务端的 `cancelled` 回应到来，所以那条回应不算“无主”。", "After an abort the entry stays until the server's `cancelled` response arrives, so that response is not an orphan."),
  ("调用在发送前用 Chord 的 `parseServiceCall()` 校验；编码失败会取回条目并拒绝，什么也不发送。", "The call is validated with Chord's `parseServiceCall()` before sending; an encoding failure takes back the entry and rejects without sending anything."),
 ],
 how=[
  ("`await client.request(target, call, signal)`：`signal` 是普通的 `AbortSignal`。", "`await client.request(target, call, signal)`: `signal` is an ordinary `AbortSignal`."),
  ("`client.serviceCatalogue(target)` 是同一路径上的一个预置调用，结果用 `parseServiceCatalogue()` 校验。", "`client.serviceCatalogue(target)` is a preset call on the same path, checked with `parseServiceCatalogue()`."),
  ("错误处理：`catch (e) { if (e instanceof ServerError && e.code === \"cancelled\") … }`。", "Error handling: `catch (e) { if (e instanceof ServerError && e.code === \"cancelled\") … }`."),
 ],
 files=[
  (U + "client.ts", r"^\t#request<T = ServiceResult>", "#request()", "守卫、登记、发送", "guard, register, send"),
  (U + "client.ts", r"const sendCancel = \(\): void =>", "sendCancel()", "补发 cancel", "the follow-up cancel"),
  (U + "client.ts", r"^\t#handleMessage\(message: ResponseEnvelope", "#handleMessage()", "按 id 结算", "settle by id"),
  (U + "client.ts", r"^\t#rejectPendingRequests", "#rejectPendingRequests()", "断开时全部拒绝", "reject all on disconnect"),
  (U + "client.ts", r"^\tasync serviceCatalogue", "serviceCatalogue()", "预置调用", "a preset call"),
 ]),

dict(id="cli-subscribe", group="flows", layer="modes", diagram="cli_subscribe",
 title=("订阅：先快照，后更新", "Subscriptions: snapshot first, then updates"),
 takeaway=("`subscribeService()` 先登记一个 `service-N` 监听器（`hydrated = false, ready = false`），再发订阅请求。快照之前到达的更新原样缓存；快照解码后 `hydrated = true` 并解码积压；调用方装好快照、调用 `start()` 之后，缓冲的更新才按序交付。交付经 `deliveryTail` 串行，异步监听器也不会乱序。",
           "`subscribeService()` registers a `service-N` listener first (`hydrated = false, ready = false`), then sends the subscribe request. Updates arriving before the snapshot are cached raw; once the snapshot decodes, `hydrated = true` and the backlog is decoded; only after the caller installs the snapshot and calls `start()` do buffered updates flow, in order. Delivery is chained on `deliveryTail`, so async listeners stay ordered too."),
 points=[
  ("每个订阅有自己的 Chord 状态解码器（`createServiceStateDecoder()`）：快照和更新都经过它。", "Every subscription has its own Chord state decoder (`createServiceStateDecoder()`); snapshots and updates both go through it."),
  ("`dispose()` 只在仍连接且路由仍是当前路由时发退订；随后等待 `deliveryTail` 并清空缓冲。", "`dispose()` sends the unsubscribe only while connected and while the route is current; then it awaits `deliveryTail` and clears the buffers."),
  ("断开时 `#serviceListeners` 整体清空；订阅不会自动恢复。", "On disconnect `#serviceListeners` is cleared wholesale; subscriptions are not restored."),
 ],
 how=[
  ("`const sub = await client.subscribeService(target, serviceId, mode, listener)`；装好 `sub.snapshot` 后调用 `sub.start()`。", "`const sub = await client.subscribeService(target, serviceId, mode, listener)`; install `sub.snapshot`, then call `sub.start()`."),
  ("监听器抛出的错误只交给 `ClientOptions.onListenerError`。", "Listener errors only reach `ClientOptions.onListenerError`."),
  ("通过 Chord 绑定使用时，`activate` 对应 `start()`、`close` 对应 `dispose()`。", "Through a Chord binding, `activate` maps to `start()` and `close` to `dispose()`."),
 ],
 files=[
  (U + "client.ts", r"^\tasync subscribeService", "subscribeService()", "登记并订阅", "register and subscribe"),
  (U + "client.ts", r"if \(!active\.hydrated\) \{", "hydrated", "快照前缓存", "cache before the snapshot"),
  (U + "client.ts", r"^\t\t\tstart: \(\) => \{", "start()", "开始交付", "begin delivery"),
  (U + "client.ts", r"^\t#deliverServiceUpdate", "#deliverServiceUpdate()", "串行交付", "ordered delivery"),
  (U + "types.ts", r"^export interface ServiceSubscription", "ServiceSubscription", "订阅句柄", "the subscription handle"),
 ]),

dict(id="cli-attach", group="arch", layer="modes", diagram="cli_attach",
 title=("附着与 Chord 传输适配器", "Attachments and the Chord transport adapter"),
 takeaway=("附着由服务器带外推送：`attachment` 信封里的 `serverId` 必须是本服务器，否则断开；三个字段都相同的更新被忽略，其余通知 `onAttachmentChange`。`createClientServiceTransport(client, getTarget)` 在每次调用时才求值 `getTarget()`，所以 Session 服务可以直接传 `() => client.attachment`。",
           "The server pushes attachments out of band: the `serverId` in an `attachment` envelope must be this server's or the connection drops; an update with all three fields equal is ignored, anything else notifies `onAttachmentChange`. `createClientServiceTransport(client, getTarget)` evaluates `getTarget()` on every call, so Session services can pass `() => client.attachment` directly."),
 points=[
  ("附着信封先于 attach 的回应送达：回应 resolve 时 `client.attachment` 已经可用。", "The attachment envelope arrives before the attach response: when it resolves, `client.attachment` is already set."),
  ("路由不存在时，适配器抛 \"Remote service target is unavailable\"，不会发出请求。", "Without a route the adapter throws \"Remote service target is unavailable\" and sends nothing."),
  ("`#targetIsCurrent()`：服务器级目标与 hello 的 `serverId` 比较，Session 目标与当前附着的三个字段比较。", "`#targetIsCurrent()`: a server target is compared with the hello's `serverId`, a Session target with all three fields of the current attachment."),
 ],
 how=[
  ("服务器级服务：`createClientServiceTransport(client, () => ({ serverId: client.serverId }))`。", "Server-wide services: `createClientServiceTransport(client, () => ({ serverId: client.serverId }))`."),
  ("Session 服务：`createClientServiceTransport(client, () => client.attachment)`。", "Session services: `createClientServiceTransport(client, () => client.attachment)`."),
  ("`client.onAttachmentChange((a) => …)`：`undefined` 表示没有附着。", "`client.onAttachmentChange((a) => …)`: `undefined` means no attachment."),
 ],
 files=[
  (U + "client.ts", r"^export function createClientServiceTransport", "createClientServiceTransport()", "Chord 适配器", "the Chord adapter"),
  (U + "client.ts", r"^\t#setAttachment", "#setAttachment()", "去重并通知", "dedupe and notify"),
  (U + "client.ts", r"^\t#targetIsCurrent", "#targetIsCurrent()", "路由是否仍有效", "is the route current"),
  (CA + "services/connection.ts", r"createClientServiceTransport\(client, \(\) => client\.attachment\)", "connection.ts", "coding-agent 的 Session 服务", "coding-agent's Session services"),
 ]),

dict(id="cli-transport", group="types", layer="modes", diagram="cli_transport",
 title=("字节传输契约与 Unix 实现", "The byte-transport contract and the Unix implementation"),
 takeaway=("`ByteTransport` 只有 `send(chunk): Promise<void>` 和 `close()`；工厂收到 `onData` / `onClose` / `onError` 三个回调，每次连接尝试新建一个已认证的传输。`UnixByteTransport` 用一条 Promise 链保序，按 `maxPendingBytes` 限制排队字节，写入返回 false 时等待 `drain`。",
           "`ByteTransport` is just `send(chunk): Promise<void>` and `close()`; the factory receives three callbacks, `onData` / `onClose` / `onError`, and builds one authenticated transport per attempt. `UnixByteTransport` keeps order with a promise chain, caps queued bytes with `maxPendingBytes`, and waits for `drain` when a write returns false."),
 points=[
  ("`maxPendingBytes` 默认是帧上限的 4 倍（64 MiB）；超过就拒绝这次 `send`，`Connection` 随之断开。", "`maxPendingBytes` defaults to 4 × the frame limit (64 MiB); beyond it the `send` rejects and the `Connection` drops."),
  ("每个 chunk 都先 `slice()` 复制，调用方之后修改缓冲也不影响写出的字节。", "Every chunk is copied with `slice()` first, so later changes to the caller's buffer cannot affect what is written."),
  ("失败的写不会堵住队列：`#writeTail` 吞掉错误，只有该次调用的 Promise 被拒绝。", "A failed write never blocks the queue: `#writeTail` swallows it, and only that call's promise rejects."),
 ],
 how=[
  ("`createUnixTransportFactory({ path, maxPendingBytes })`：path 不能为空，Windows 上不可用。", "`createUnixTransportFactory({ path, maxPendingBytes })`: the path must not be empty; unavailable on Windows."),
  ("自定义传输：实现 `send` / `close`，并且恰好调用一次 `onClose` 或 `onError`。", "A custom transport: implement `send` / `close` and call exactly one of `onClose` or `onError`."),
  ("两端配置相同的 `maxFrameLength`，并让 `maxPendingBytes` 至少容得下一帧。", "Configure the same `maxFrameLength` on both peers, with `maxPendingBytes` large enough for one frame."),
 ],
 files=[
  (U + "transport.ts", r"^export type ByteTransportFactory", "ByteTransportFactory", "工厂契约", "the factory contract"),
  (U + "unix.ts", r"^class UnixByteTransport", "UnixByteTransport", "写队列", "the write queue"),
  (U + "unix.ts", r"^function connectUnixSocket", "connectUnixSocket()", "连接与终止回调", "connect and terminal callbacks"),
  (U + "unix.ts", r"^function validateUnixTransportOptions", "validateUnixTransportOptions()", "默认值与检查", "defaults and checks"),
  (CA + "radius-relay.ts", r"^class RadiusClientByteTransport", "RadiusClientByteTransport", "WebSocket 中继传输", "the WebSocket relay transport"),
 ]),

dict(id="cli-discover", group="flows", layer="modes", diagram="cli_discover",
 title=("发现本机服务器", "Discovering local servers"),
 takeaway=("`discoverUnixServers({ directory })` 读一个目录，只保留名为 `<serverId>.sock` 且 serverId 是规范 UUIDv4 的条目，然后用最多 16 个工作者并发探测：确认是 socket、用一个临时 `Client` 完成握手（默认 1000 ms 超时），最后按 serverId 排序返回 `{ serverId, path }`。",
           "`discoverUnixServers({ directory })` reads a directory, keeps only entries named `<serverId>.sock` whose serverId is a canonical UUIDv4, then probes them with up to 16 concurrent workers: check it is a socket, complete a handshake with a temporary `Client` (1000 ms timeout by default), and return `{ serverId, path }` sorted by serverId."),
 points=[
  ("只读：陈旧或无响应的 socket 只会被忽略，从不删除——清理归服务器端的监听器。", "Read-only: stale or unresponsive sockets are just ignored, never deleted; cleanup belongs to the server's listener."),
  ("超时、协议错误、版本不符、无 cause 的断开以及 ENOENT / ECONNREFUSED / ECONNRESET / EPIPE / ETIMEDOUT 都算“不是这台服务器”。", "Timeouts, protocol errors, version mismatches, cause-less disconnects and ENOENT / ECONNREFUSED / ECONNRESET / EPIPE / ETIMEDOUT all count as “not this server”."),
  ("其它错误让整个发现失败：第一个错误被记下，工作者停止领取新候选。", "Any other error fails discovery: the first one is remembered and workers stop taking candidates."),
 ],
 how=[
  ("`const routes = await discoverUnixServers({ directory })`，directory 用绝对路径，例如展开后的 `~/.pi/server`。", "`const routes = await discoverUnixServers({ directory })` with an absolute directory such as the expanded `~/.pi/server`."),
  ("`timeoutMs` 覆盖每次探测的超时（1 … 2,147,483,647）。", "`timeoutMs` overrides the per-probe timeout (1 … 2,147,483,647)."),
  ("然后 `Client.connect({ serverId: route.serverId, transportFactory: createUnixTransportFactory({ path: route.path }) })`。", "Then `Client.connect({ serverId: route.serverId, transportFactory: createUnixTransportFactory({ path: route.path }) })`."),
 ],
 files=[
  (U + "unix.ts", r"^export async function discoverUnixServers", "discoverUnixServers()", "读目录与工作者池", "directory and worker pool"),
  (U + "unix.ts", r"^async function probeUnixServer", "probeUnixServer()", "一次握手探测", "one handshake probe"),
  (U + "unix.ts", r"^const MAX_CONCURRENT_DISCOVERY_PROBES", "MAX_CONCURRENT_DISCOVERY_PROBES", "并发上限 16", "concurrency 16"),
  (CA + "client-runtime.ts", r"discoverUnixServers\(\{ directory \}\)", "client-runtime.ts", "coding-agent 的使用", "coding-agent's use"),
 ]),

dict(id="cli-errors", group="types", layer="modes", diagram="cli_errors",
 title=("失败语义与恢复", "Failure semantics and recovery"),
 takeaway=("调用方会看到五种拒绝：`ServerError`（服务器拒绝，带 `code`）、`DisconnectedError`（没连上或连接断了，传输错误放在 `cause`）、`ClientDisposedError`、`ProtocolValidationError`（对端违反协议，并且断开）和 `AbortError`。`Client` 从不自动重连或重放：断开之后 `reconnect()`、重新 attach、重新订阅，只重放已知安全的操作——这是应用的策略。",
           "Callers see five kinds of rejection: `ServerError` (the server refused, with a `code`), `DisconnectedError` (not connected or the connection dropped; transport errors in `cause`), `ClientDisposedError`, `ProtocolValidationError` (the peer broke the protocol, and the connection drops) and `AbortError`. The `Client` never reconnects or replays on its own: after a disconnect, `reconnect()`, attach again, subscribe again, and replay only operations known to be safe; that is the application's policy."),
 points=[
  ("断开时挂起的请求在本地拒绝，但已被服务器接受的工作仍可能在远端完成。", "On disconnect pending requests reject locally, but work the server accepted may still complete remotely."),
  ("coding-agent 的 `RadiusClientReconnect` 就是这样一种应用策略：指数退避重连并重新附着原来的 Session。", "coding-agent's `RadiusClientReconnect` is one such application policy: reconnect with exponential backoff and reattach the same Session."),
  ("监听器的异常只交给 `onListenerError`，诊断不能影响协议或传输状态。", "Listener exceptions only reach `onListenerError`; diagnostics cannot affect protocol or transport state."),
 ],
 how=[
  ("`e instanceof ServerError` → 看 `e.code`；`e instanceof DisconnectedError` → 看 `e.cause`。", "`e instanceof ServerError` → inspect `e.code`; `e instanceof DisconnectedError` → inspect `e.cause`."),
  ("`await using client = …` 或 `await client.dispose()`：两者等价（`Symbol.asyncDispose`）。", "`await using client = …` or `await client.dispose()`: equivalent (`Symbol.asyncDispose`)."),
  ("`client.reconnect()` 只是再走一次 `connect()`：新传输、新握手。", "`client.reconnect()` is just another `connect()`: a new transport and a new handshake."),
 ],
 files=[
  (U + "errors.ts", r"^export class ServerError", "ServerError", "带 code 的服务器错误", "server error with a code"),
  (U + "errors.ts", r"^export class DisconnectedError", "DisconnectedError", "断开，带 cause", "disconnected, with cause"),
  (U + "errors.ts", r"^export class ClientDisposedError", "ClientDisposedError", "已 dispose", "disposed"),
  (U + "client.ts", r"^\treconnect\(\): Promise<ServerHello>", "reconnect()", "显式重连", "explicit reconnection"),
  (CA + "radius-relay.ts", r"^export class RadiusClientReconnect", "RadiusClientReconnect", "一种应用策略", "one application policy"),
 ]),
]

EXT_POINTS = [
 ("ByteTransportFactory", ("接入任何保序字节流：WebSocket、管道、测试替身。", "Plug in any order-preserving byte stream: a WebSocket, a pipe, a test double.")),
 ("createClientServiceTransport(client, getTarget)", ("把路由交给 Chord 绑定，得到类型化的远程服务。", "Hand a route to a Chord binding to get typed remote services.")),
 ("ClientOptions.onListenerError", ("收集监听器异常，而不影响连接。", "Collect listener exceptions without affecting the connection.")),
 ("ClientOptions.maxFrameLength · maxPendingBytes", ("帧上限与 Unix 传输的排队上限；两端配置一致。", "The frame limit and the Unix transport's queue limit; configure both peers alike.")),
 ("discoverUnixServers({ directory, timeoutMs })", ("列出某个目录里可以握手的本机服务器。", "List the local servers in a directory that complete a handshake.")),
]
XREF = [('protocol', ('线上格式：信封、分帧与 CBOR', 'the wire format: envelopes, framing and CBOR')),
        ('server', ('另一端：握手、路由到 Session、推送附着', 'the other end: handshake, Session routing, attachment pushes')),
        ('chord', ('服务控制调用、状态解码器与 RemoteServiceTransport', 'service-control calls, the state decoder and RemoteServiceTransport')),
        ('coding-agent', ('experimental/ 下的 client 运行时与中继传输', 'the client runtime and relay transport under experimental/'))]
