# pi-server deep dive. Same section schema as deep_agent.py; files: (path, regex, symbol, zh, en)
from pkgsrc import Pkg
S_ = Pkg('packages/server/src/')
U = 'packages/server/src/'
UX = U + 'transports/unix/'
CA = 'packages/coding-agent/src/experimental/'
SLIDE_KEYS = ['srv_arch', 'srv_host', 'srv_conn', 'srv_request', 'srv_router', 'srv_release', 'srv_unix', 'srv_errors']
_TS = S_.total()

INTRO = dict(
 takeaway=("`pi-server` 是远程 pi 会话的服务端一端：它接受任何 `ServerListener` 交来的字节连接，完成握手，核对每个请求的路由，再把调用原样交给应用——服务器级调用交给 `serverServices`，Session 调用交给应用打开的 `RoutedSessionHandle` 为这次附着发的租约。它不解析服务契约、不保存 Session；它负责的是路由、附着的生命周期、取消、订阅更新的顺序，以及关闭时的清理。",
           "`pi-server` is the server end of remote pi sessions: it accepts byte connections from any `ServerListener`, completes the handshake, checks every request's route and hands the call to the application unchanged; server-wide calls go to `serverServices`, Session calls to the lease that the app's `RoutedSessionHandle` issued for this attachment. It parses no service contract and stores no Session; it owns routing, the attachment lifecycle, cancellation, the order of subscription updates, and cleanup on shutdown."),
 role=(f"{_TS:,} 行 TypeScript，三个导入路径：根入口 `\".\"`、Unix socket 传输 `\"./unix\"` 和测试工具 `\"./testing\"`。依赖 `chord` 与 `pi-protocol`；用到 `node:crypto`（attachmentId）。唯一的使用者是 coding-agent 的 `experimental/` 服务器：每个 Session 跑在自己的 worker 进程里。",
       f"{_TS:,} lines of TypeScript, three import paths: the root `\".\"`, the Unix-socket transport `\"./unix\"` and the testing kit `\"./testing\"`. Depends on `chord` and `pi-protocol`; uses `node:crypto` (attachment ids). Its only user is coding-agent's `experimental/` server, where every Session runs in its own worker process."),
)

SECTIONS = [
dict(id="srv-arch", group="arch", layer="modes", diagram="srv_arch",
 title=("Server、SessionRouter 与可替换的监听器", "Server, SessionRouter and pluggable listeners"),
 takeaway=("`Server`（server.ts）管连接、握手和请求分派；内部的 `SessionRouter`（session-router.ts）管托管的 Session、每个连接的附着和释放；`ServerListener` 只负责把已建立的字节连接交给 `server.accept()`。根入口用 `export *` 公开 errors、listener、server、types 四个模块；`SessionRouter` 与 `ByteConnection` 不公开。",
           "`Server` (server.ts) owns connections, the handshake and request dispatch; the internal `SessionRouter` (session-router.ts) owns hosted Sessions, each connection's attachment and its release; a `ServerListener` only hands established byte connections to `server.accept()`. The root uses `export *` to publish four modules: errors, listener, server and types; `SessionRouter` and `ByteConnection` stay private."),
 points=[
  ("监听器负责传输层的认证；实验性的 Unix 监听器不做认证，只依靠文件权限。", "Listeners own transport-level authentication; the experimental Unix listener does none and relies on file permissions."),
  ("coding-agent 的 radius-relay.ts 只用到 `Pick<Server, \"accept\">`：中继来的连接与本地 socket 进入同一个 Server。", "coding-agent's radius-relay.ts only needs `Pick<Server, \"accept\">`: relayed connections enter the same Server as local sockets."),
  ("`Server.closed` 在关闭后 resolve，监听器或 Session 清理失败时 reject。", "`Server.closed` resolves after shutdown and rejects when listener or Session cleanup fails."),
 ],
 how=[
  ("`const server = new Server(host, { listeners, serverId })`，然后 `await server.start()`。", "`const server = new Server(host, { listeners, serverId })`, then `await server.start()`."),
  ("本机：`createUnixServer(host, { serverId, path: getUnixSocketPath(serverId, dir) })`。", "Locally: `createUnixServer(host, { serverId, path: getUnixSocketPath(serverId, dir) })`."),
  ("`onConnectionCountChanged(count)` 观察连接数，`onError(error)` 收集诊断。", "Observe connections with `onConnectionCountChanged(count)`, collect diagnostics with `onError(error)`."),
 ],
 files=[
  (U + "index.ts", r'^export \* from "./server.ts"', "export *", "根入口", "the root entry"),
  (U + "server.ts", r"^export class Server", "Server", "连接与分派", "connections and dispatch"),
  (U + "session-router.ts", r"^export class SessionRouter", "SessionRouter", "Session 与附着", "Sessions and attachments"),
  (U + "listener.ts", r"^export interface ServerListener", "ServerListener", "监听器契约", "the listener contract"),
  (UX + "preset.ts", r"^export function createUnixServer", "createUnixServer()", "Unix 预设", "the Unix preset"),
 ]),

dict(id="srv-host", group="types", layer="modes", diagram="srv_host",
 title=("ServerHost：应用提供的能力", "ServerHost: capabilities the app provides"),
 takeaway=("应用只实现三样东西：`serverServices`（握手时为每个连接建一个服务器级端点）、`resolveSession(id)`（把 id 解析成元数据，或抛出有界的路由错误）和 `openSession(metadata)`（返回一个 `RoutedSessionHandle`）。句柄的 `attachClient()` 为每次附着发一个租约，租约的 `invokeService()` 接收不透明的服务调用。",
           "The app implements just three things: `serverServices` (one server-wide endpoint per connection, built at the handshake), `resolveSession(id)` (resolve an id to metadata, or throw a bounded routing error) and `openSession(metadata)` (return a `RoutedSessionHandle`). The handle's `attachClient()` issues one lease per attachment, and the lease's `invokeService()` takes opaque service calls."),
 points=[
  ("服务器级端点拿到一个 `RoutedServerPresentation`：`attachSession`、`detachSession`、`prepareSessionRemoval`——应用的管理服务就是用它们 attach 的。", "The server-wide endpoint receives a `RoutedServerPresentation`: `attachSession`, `detachSession`, `prepareSessionRemoval`; the app's management service attaches through these."),
  ("`terminated` 是可选的 Promise：意外退出时以错误 resolve，Server 随即让该 Session 的附着全部失效。", "`terminated` is an optional promise: it resolves with an error on unexpected exit, and the Server then invalidates every attachment to that Session."),
  ("`SessionMetadata` 只要求 `id`；应用可以扩展它（coding-agent 带上了 `path`）。", "`SessionMetadata` only requires an `id`; apps may extend it (coding-agent adds a `path`)."),
 ],
 how=[
  ("`const host: ServerHost<StoredSession> = { serverServices, resolveSession, openSession }`。", "`const host: ServerHost<StoredSession> = { serverServices, resolveSession, openSession }`."),
  ("找不到时 `throw new SessionNotFoundError(`Unknown session: ${id}`)`。", "When missing, `throw new SessionNotFoundError(`Unknown session: ${id}`)`."),
  ("`invokeService(call, publish, ctx)`：订阅的更新经 `publish(subscriptionId, update)` 回到 Server。", "`invokeService(call, publish, ctx)`: subscription updates return through `publish(subscriptionId, update)`."),
 ],
 files=[
  (U + "types.ts", r"^export interface ServerHost", "ServerHost", "应用能力", "app capabilities"),
  (U + "types.ts", r"^export interface RoutedSessionHandle", "RoutedSessionHandle", "每个 Session", "per Session"),
  (U + "types.ts", r"^export interface RoutedSessionAttachment", "RoutedSessionAttachment", "每次附着的租约", "per-attachment lease"),
  (U + "types.ts", r"^export interface RoutedServerPresentation", "RoutedServerPresentation", "交给应用的附着能力", "attach capabilities for the app"),
  (CA + "session-worker-manager.ts", r"#routedHandle\(worker: WorkerRecord\): RoutedSessionHandle", "#routedHandle()", "coding-agent：worker 句柄", "coding-agent: the worker handle"),
 ]),

dict(id="srv-conn", group="flows", layer="modes", diagram="srv_conn",
 title=("连接的五个阶段", "Five connection stages"),
 takeaway=("每条连接经历 `awaitingHello → handshaking → ready → closing → closed`。第一条消息必须是 `hello`，而且整个握手要在 5 s 内完成；`finishHandshake()` 检查版本、为连接建服务器级端点、发回 `hello { version, serverId }`，然后才进入 ready。协议错误走 `failProtocol()`：把 `hello_error` 作为最后一帧发出，再关闭。",
           "Every connection goes `awaitingHello → handshaking → ready → closing → closed`. The first message must be `hello` and the whole handshake must finish within 5 s; `finishHandshake()` checks the version, builds the connection's server-wide endpoint and sends back `hello { version, serverId }` before entering ready. Protocol errors go through `failProtocol()`: `hello_error` is sent as the final frame, then the connection closes."),
 points=[
  ("握手期间到达的请求挂在 `state.handshake` 之后，ready 时才处理，不会丢。", "Requests that arrive during the handshake wait on `state.handshake` and run once ready; none are lost."),
  ("`disconnect()` 只执行一次：abort 所有进行中的请求、清空订阅编码器，并行释放 Session 附着与服务器级端点。", "`disconnect()` runs once: it aborts every active request, clears subscription encoders, and releases the Session attachment and server-wide endpoint in parallel."),
  ("关闭中的 Server 对新连接直接 close，不建任何状态。", "A closing Server closes new connections at once without creating any state."),
 ],
 how=[
  ("`handshakeTimeoutMs` 与 `maxFrameLength` 都是 1 … 上限之间的整数，构造时检查。", "`handshakeTimeoutMs` and `maxFrameLength` are integers within bounds, checked by the constructor."),
  ("`await server.close()`：先关监听器，再关连接，最后关所有托管的 Session。", "`await server.close()`: listeners first, then connections, then every hosted Session."),
  ("自定义监听器：`start(accept)` 里对每个连接调用 `accept(connection)`，把返回的 handler 接到传输事件上。", "A custom listener: in `start(accept)`, call `accept(connection)` per connection and wire the returned handler to transport events."),
 ],
 files=[
  (U + "server.ts", r"^\taccept\(connection: ByteConnection\)", "accept()", "新连接与握手定时器", "new connection, handshake timer"),
  (U + "server.ts", r"^\tprivate dispatchMessage", "dispatchMessage()", "按阶段分派", "dispatch by stage"),
  (U + "server.ts", r"^\tprivate async finishHandshake", "finishHandshake()", "完成握手", "finish the handshake"),
  (U + "server.ts", r"^\tprivate async failProtocol", "failProtocol()", "hello_error 作最后一帧", "hello_error as final frame"),
  (U + "server.ts", r"^\tprivate disconnect\(connection: ConnectionState\)", "disconnect()", "断开清理", "disconnect cleanup"),
  (U + "connection.ts", r"^export type ConnectionStage", "ConnectionStage", "五个阶段", "five stages"),
 ]),

dict(id="srv-request", group="flows", layer="modes", diagram="srv_request",
 title=("一个请求的处理", "Handling one request"),
 takeaway=("`handleRequest()` 先拒绝重复的请求 id 和不合法的调用，再登记一个 `AbortController`；然后核对 `serverId`，按 target 是否带 `sessionId` 路由到 `SessionRouter` 或服务器级端点。订阅必须返回快照：Server 为它装上 `ServiceStateEncoder`，先发回应，再冲刷期间排队的更新。",
           "`handleRequest()` first rejects duplicate request ids and invalid calls, then registers an `AbortController`; it checks the `serverId` and routes to the `SessionRouter` or the server-wide endpoint depending on whether the target has a `sessionId`. A subscription must return a snapshot: the Server installs a `ServiceStateEncoder` for it, sends the response first, then flushes the updates queued meanwhile."),
 points=[
  ("错误回应用 `toProtocolError()` 映射：`ServerError` / `RemoteServiceError` 原样，`ProtocolValidationError` → `invalid_request`，其它 → `internal_error`。", "Error responses are mapped by `toProtocolError()`: `ServerError` / `RemoteServiceError` as is, `ProtocolValidationError` → `invalid_request`, anything else → `internal_error`."),
  ("已 abort 的请求一律回应 `cancelled`；`cancel` 本身从不单独回应。", "An aborted request always answers `cancelled`; a `cancel` never gets its own response."),
  ("回应已发出后才出错（例如冲刷更新时），Server 关闭这条连接：订阅流不能半途断掉。", "If something fails after the response was sent (flushing updates, say), the Server closes the connection: a stream must not break halfway."),
 ],
 how=[
  ("同一连接上的请求并发处理；需要顺序时由应用在服务里自己排队。", "Requests on one connection run concurrently; apps that need ordering queue inside their services."),
  ("在服务里尊重 `context` 的 abort 信号，取消才会尽快生效。", "Honour the `context` abort signal in services so cancellation takes effect quickly."),
  ("退订成功后编码器被删掉，之后对该订阅的 `publish` 静默丢弃。", "After a successful unsubscribe the encoder is deleted, and later `publish` calls for it are silently dropped."),
 ],
 files=[
  (U + "server.ts", r"^\tprivate async handleRequest", "handleRequest()", "核对、路由、回应", "check, route, respond"),
  (U + "server.ts", r"^\tprivate handleCancel", "handleCancel()", "按 id 与 target 取消", "cancel by id and target"),
  (U + "server.ts", r"^\tprivate async sendServiceUpdate", "sendServiceUpdate()", "编码更新", "encode an update"),
  (U + "server.ts", r"^\tprivate toProtocolError", "toProtocolError()", "错误映射", "error mapping"),
  (U + "server.ts", r"^function sameTarget", "sameTarget()", "target 比较", "target comparison"),
 ]),

dict(id="srv-router", group="flows", layer="modes", diagram="srv_router",
 title=("SessionRouter：attach 与准入", "SessionRouter: attach and admission"),
 takeaway=("attach 按连接串行（`runForClient`）：已附着同一 Session 就直接返回；否则 `acquire()`——已托管、正在打开或新打开（`resolveSession` + `openSession`）——释放当前附着、为新附着生成 `randomUUID()` 并向句柄取租约，最后带外推送 `attachment` 路由。Session 调用也在同一队列里“准入”：路由必须与本连接的当前附着完全一致。",
           "Attach is serialised per connection (`runForClient`): if already attached to that Session it returns at once; otherwise `acquire()`s it (hosted, opening, or freshly opened via `resolveSession` + `openSession`), releases the current attachment, generates a `randomUUID()` for the new one, takes a lease from the handle, and finally pushes the `attachment` route out of band. Session calls are admitted through the same queue: the route must exactly match this connection's current attachment."),
 points=[
  ("只有准入排队；调用结果在队列外等待，所以同一 Session 上的调用可以并发。", "Only admission is queued; results are awaited outside the queue, so calls on one Session run concurrently."),
  ("`openingSessions` 让并发的 attach 共享同一次打开；失败时一起失败，之后可以重试。", "`openingSessions` lets concurrent attaches share one open; on failure they fail together, and a later retry may succeed."),
  ("打开期间服务器开始关闭：立即 `handle.close()` 并以 `server_draining` 拒绝。", "If the server starts closing during an open, `handle.close()` runs at once and the attach rejects with `server_draining`."),
 ],
 how=[
  ("应用的管理服务调用 `presentation.attachSession(sessionId, ctx)`；结果里不带任何路由 id。", "The app's management service calls `presentation.attachSession(sessionId, ctx)`; its result carries no route ids."),
  ("一个 Session 可以有多个连接的附着；每个附着各自有租约。", "One Session may have attachments from several connections, each with its own lease."),
  ("要彻底删除 Session，先调用 `prepareSessionRemoval(sessionId)`，再删应用自己的元数据。", "To delete a Session, call `prepareSessionRemoval(sessionId)` first, then delete the app's own metadata."),
 ],
 files=[
  (U + "session-router.ts", r"^\tprivate runForClient", "runForClient()", "按连接串行", "per-connection queue"),
  (U + "session-router.ts", r"^\tprivate async attachClientNow", "attachClientNow()", "attach 的步骤", "the attach steps"),
  (U + "session-router.ts", r"^\tprivate async acquire", "acquire()", "共享打开", "shared opening"),
  (U + "session-router.ts", r"^\tprivate async open\(", "open()", "resolve + open", "resolve + open"),
  (U + "session-router.ts", r"^\tprivate requireAttachment", "requireAttachment()", "路由核对", "route check"),
 ]),

dict(id="srv-release", group="flows", layer="modes", diagram="srv_release",
 title=("附着的结束", "How attachments end"),
 takeaway=("detach、切换 Session、连接断开、句柄 `terminated`、`prepareSessionRemoval()` 和 `Server.close()` 最终都走 `releaseAttachment()`：同一附着只释放一次，先等已准入的调用结算，再 `lease.release()`，最后摘掉路由——只有 detach 与失效会推送 `attachment: null`。删除和关闭服务器还会 `handle.close()`。",
           "Detach, switching Sessions, a dropped connection, a `terminated` handle, `prepareSessionRemoval()` and `Server.close()` all end in `releaseAttachment()`: each attachment is released once, admitted calls settle first, then `lease.release()`, then the route is cleared; only detach and invalidation push `attachment: null`. Removal and shutdown also call `handle.close()`."),
 points=[
  ("连接断开只释放附着，Session 仍被托管；什么时候让 worker 退役由应用决定。", "A dropped connection only releases the attachment; the Session stays hosted, and the app decides when its worker retires."),
  ("句柄终止后 Session 从 `hostedSessions` 删除；下次 attach 会重新打开它。", "After a handle terminates, the Session leaves `hostedSessions`; the next attach reopens it."),
  ("释放失败也一定清掉路由（finally），否则连接会永远占着它。", "The route is cleared even if release fails (finally); otherwise the connection would hold it forever."),
 ],
 how=[
  ("在租约的 `release(ctx)` 里放掉 Session 级资源；它可能在调用仍在完成时被等待。", "Free Session-level resources in the lease's `release(ctx)`; it may be awaited while calls are still completing."),
  ("用 `terminated` 报告 worker 意外退出，让客户端尽快看到 `attachment: null`。", "Report unexpected worker exits through `terminated` so clients see `attachment: null` quickly."),
  ("关闭失败时 `server.close()` 与 `server.closed` 以 AggregateError 拒绝。", "On cleanup failure `server.close()` and `server.closed` reject with an AggregateError."),
 ],
 files=[
  (U + "session-router.ts", r"^\tprivate releaseAttachment", "releaseAttachment()", "唯一的释放路径", "the one release path"),
  (U + "session-router.ts", r"^\tprivate async clearAttachment", "clearAttachment()", "摘掉路由", "clear the route"),
  (U + "session-router.ts", r"^\tprivate invalidate", "invalidate()", "句柄终止", "handle termination"),
  (U + "session-router.ts", r"^\tasync removeSession", "removeSession()", "删除前释放", "release before removal"),
  (U + "session-router.ts", r"^\tprivate async closeInternal", "closeInternal()", "关闭全部", "close everything"),
 ]),

dict(id="srv-unix", group="flows", layer="modes", diagram="srv_unix",
 title=("Unix 监听器", "The Unix listener"),
 takeaway=("`UnixListener.start()` 建 0700 目录，清理陈旧 socket（还活着就拒绝启动），先在 `bind-<sha256 前 8 位>` 上监听，记下 socket 的 dev/ino，再用 `link()` 原子地发布到公共路径、`chmod 0600`、删掉 bind 路径。关闭时只删除身份仍然匹配的 socket，所以接替它的新服务器不会被误删。",
           "`UnixListener.start()` creates a 0700 directory, cleans up stale sockets (refusing to start if one is alive), listens first on `bind-<first 8 hex of sha256>`, records the socket's dev/ino, then publishes it atomically to the public path with `link()`, `chmod 0600`s it and unlinks the bind path. On close it removes the socket only while its identity still matches, so a server that replaced it is never removed by mistake."),
 points=[
  ("活性探测：连得上或 1000 ms 没反应都算“还活着”——宁可启动失败，也不删别人的 socket。", "Liveness probe: connecting, or no answer within 1000 ms, both count as alive; better to fail start-up than delete another server's socket."),
  ("删除前总是先改名（stale- / cleanup-）再核对 dev/ino：避免与并发的替换竞争。", "Removal always renames first (stale- / cleanup-) and then checks dev/ino, to avoid racing a concurrent replacement."),
  ("`UnixByteConnection` 把排队字节限制在 `maxPendingBytes`（默认 4 × 帧上限，至少帧上限 + 4），超过就断开慢的对端。", "`UnixByteConnection` caps queued bytes at `maxPendingBytes` (4 × the frame limit by default, at least limit + 4) and drops a slow peer beyond it."),
 ],
 how=[
  ("`getUnixSocketPath(serverId, dir)` 得到 `<dir>/<serverId>.sock`；README 建议用一个短的私有运行时目录。", "`getUnixSocketPath(serverId, dir)` gives `<dir>/<serverId>.sock`; the README recommends a short private runtime directory."),
  ("`createUnixListener({ path, mode, maxPendingBytes, gracefulCloseTimeoutMs })` 可以和其它监听器一起交给 `new Server()`。", "`createUnixListener({ path, mode, maxPendingBytes, gracefulCloseTimeoutMs })` can go to `new Server()` alongside other listeners."),
  ("coding-agent：目录默认 `~/.pi/server`，可用 `PI_SERVER_DIR` 覆盖。", "coding-agent: the directory defaults to `~/.pi/server`, overridable with `PI_SERVER_DIR`."),
 ],
 files=[
  (UX + "listener.ts", r"^\tasync start\(accept: ByteConnectionAcceptor\)", "start()", "绑定与发布", "bind and publish"),
  (UX + "listener.ts", r"^async function removeStaleSocket", "removeStaleSocket()", "陈旧 socket", "stale sockets"),
  (UX + "listener.ts", r"^\tprivate async cleanupOwnedSocket", "cleanupOwnedSocket()", "按身份清理", "identity-checked cleanup"),
  (UX + "listener.ts", r"^export class UnixByteConnection", "UnixByteConnection", "写队列与优雅关闭", "write queue, graceful close"),
  (UX + "address.ts", r"^export function getUnixSocketPath", "getUnixSocketPath()", "路径约定", "path convention"),
 ]),

dict(id="srv-errors", group="types", layer="modes", diagram="srv_errors",
 title=("错误码与测试工具", "Error codes and the testing kit"),
 takeaway=("能越过协议边界的错误都是 `ServerError`：五个子类覆盖 `wrong_server`、`session_not_found`、`session_ambiguous`、`session_not_attached` 和 `server_draining`，应用也可以用 Chord 的 `RemoteServiceErrorCode`。其它异常一律变成 `internal_error \"Internal server error\"`，细节只交给 `onError`。`./testing` 提供测试服务器、内存宿主与帧级协议客户端。",
           "Errors that may cross the protocol boundary are `ServerError`s: five subclasses cover `wrong_server`, `session_not_found`, `session_ambiguous`, `session_not_attached` and `server_draining`, and apps may also use Chord's `RemoteServiceErrorCode`s. Any other exception becomes `internal_error \"Internal server error\"`, with details only in `onError`. `./testing` provides a test server, an in-memory host and a frame-level protocol client."),
 points=[
  ("`wrong_server` 在访问任何仓库之前检查：发错服务器的请求不会触发 `resolveSession`。", "`wrong_server` is checked before any repository access: a request for another server never triggers `resolveSession`."),
  ("只有 `ServerError` 与 `RemoteServiceError` 的消息会被转发；其它异常的消息和堆栈不会离开服务器。", "Only `ServerError` and `RemoteServiceError` messages are forwarded; other exceptions' messages and stacks never leave the server."),
  ("conformance.test.ts 是最大的测试文件：多附着、过期路由、未知 / 有歧义的 Session、Harness 终止与关闭时的清理。", "conformance.test.ts is the largest test file: multiple attachments, stale routes, unknown / ambiguous Sessions, Harness termination and shutdown cleanup."),
 ],
 how=[
  ("在 `resolveSession` 里 `throw new SessionNotFoundError()` 或 `new SessionAmbiguousError()`。", "In `resolveSession`, `throw new SessionNotFoundError()` or `new SessionAmbiguousError()`."),
  ("`const { server, host } = createTestServer({ listeners })` 得到一个未启动的测试服务器。", "`const { server, host } = createTestServer({ listeners })` gives an unstarted test server."),
  ("`const c = await connectUnixTestClient(path)`，用 `ProtocolTestClient` 按帧断言。", "`const c = await connectUnixTestClient(path)`, then assert frame by frame with `ProtocolTestClient`."),
 ],
 files=[
  (U + "errors.ts", r"^export class ServerError", "ServerError", "可越界的错误", "boundary-safe errors"),
  (U + "errors.ts", r"^export class WrongServerError", "WrongServerError", "wrong_server", "wrong_server"),
  (U + "errors.ts", r"^export const INTERNAL_SERVER_ERROR_MESSAGE", "INTERNAL_SERVER_ERROR_MESSAGE", "内部错误的固定消息", "the fixed internal message"),
  (U + "testing/server.ts", r"^export function createTestServer", "createTestServer()", "测试服务器", "the test server"),
  (U + "testing/client.ts", r"^export class ProtocolTestClient", "ProtocolTestClient", "帧级客户端", "frame-level client"),
 ]),
]

EXT_POINTS = [
 ("ServerHost", ("应用接入点：serverServices、resolveSession、openSession。", "The app's entry point: serverServices, resolveSession, openSession.")),
 ("RoutedSessionHandle · RoutedSessionAttachment", ("把 Session 放在任何地方：同进程、worker 进程或远端。", "Host a Session anywhere: in process, in a worker process, or remotely.")),
 ("ServerListener", ("接入新的传输：start(accept) 交出已认证的字节连接。", "Add a transport: start(accept) hands over authenticated byte connections.")),
 ("ServerError(code, message)", ("给客户端一个可识别的错误码和消息。", "Give clients a recognisable error code and message.")),
 ("./testing", ("用 createTestServer 与 ProtocolTestClient 测试你的宿主或传输。", "Test your host or transport with createTestServer and ProtocolTestClient.")),
]
XREF = [('protocol', ('线上格式：信封、分帧与 CBOR', 'the wire format: envelopes, framing and CBOR')),
        ('client', ('另一端：握手、请求、订阅与附着', 'the other end: handshake, requests, subscriptions, attachments')),
        ('chord', ('服务控制调用、状态编码器与 RemoteServiceError', 'service-control calls, the state encoder and RemoteServiceError')),
        ('coding-agent', ('experimental/ 下的服务器与 Session worker', 'the server and Session workers under experimental/'))]
