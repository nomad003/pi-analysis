# pi-mcp deep dive. Same section schema as deep_agent.py; files: (path, regex, symbol, zh, en)
from figs7 import total_loc, versions, num, CAM
U = 'packages/mcp/src/'
CA = 'packages/coding-agent/src/'
SLIDE_KEYS = ['mcp_arch', 'mcp_lifecycle', 'mcp_requests', 'mcp_stdio', 'mcp_http', 'mcp_oauth', 'mcp_content', 'mcp_pi']
_LOC = total_loc(); _V = versions(); _TO = num('client.ts', 'DEFAULT_REQUEST_TIMEOUT_MS'); _CAL = total_loc(CAM + 'extensions/mcp')

INTRO = dict(
 takeaway=("`pi-mcp` 是一个独立、无依赖于其他 pi 包的 Model Context Protocol 客户端：`McpClient` 负责 initialize 握手、请求簿记（超时、进度、取消）和分页；两种传输——本地子进程的 stdio 与远程的 Streamable HTTP（POST + SSE、会话、断线续传）；`./oauth` 子入口实现完整的 MCP 授权流程（元数据发现、PKCE、动态注册、刷新与 step-up）。",
           "`pi-mcp` is a standalone Model Context Protocol client that depends on no other pi package: `McpClient` handles the initialize handshake, request bookkeeping (timeouts, progress, cancellation) and paging; two transports — stdio for local child processes and Streamable HTTP for remote servers (POST + SSE, sessions, resumable streams); and the `./oauth` entry implements the full MCP authorization flow (metadata discovery, PKCE, dynamic registration, refresh and step-up)."),
 role=(f"共 {_LOC:,} 行 TypeScript，唯一的运行时依赖是 `cross-spawn`。默认协议版本 `{_V[0]}`，兼容 {len(_V)} 个版本。pi 内部只有 `coding-agent` 的内置 MCP 扩展（{_CAL:,} 行）使用它。",
       f"{_LOC:,} lines of TypeScript; the only runtime dependency is `cross-spawn`. Default protocol version `{_V[0]}`, {len(_V)} versions supported. Inside pi, only `coding-agent`'s built-in MCP extension ({_CAL:,} lines) uses it."),
)

SECTIONS = [
dict(id="mcp-arch", group="arch", layer="ext", diagram="mcp_arch",
 title=("模块结构", "Module structure"),
 takeaway=("三块：客户端与协议（`client.ts` 加上 `protocol/` 下的 JSON-RPC、类型与内容转换）、传输（`transports/` 下的统一接口与三种实现）、OAuth（`oauth/`，作为 `./oauth` 单独导出）。`./testing` 只导出一对内存传输。",
           "Three blocks: client & protocol (`client.ts` plus JSON-RPC, types and content conversion in `protocol/`), transports (one interface and three implementations in `transports/`), and OAuth (`oauth/`, exported separately as `./oauth`). `./testing` exports only an in-memory transport pair."),
 points=[
  ("最大的文件是 `client.ts`；其次是 `transports/streamable-http.ts`——HTTP 传输要处理会话、SSE 解析、认证重试和断线续传。", "The largest file is `client.ts`, followed by `transports/streamable-http.ts` — the HTTP transport handles sessions, SSE parsing, auth retries and stream resumption."),
  ("客户端只依赖 `McpTransport` 接口：`start` / `send` / `close` 加三个监听（message、error、close）。换传输不用改客户端。", "The client depends only on the `McpTransport` interface: `start` / `send` / `close` plus three listeners (message, error, close). Swapping transports never touches the client."),
  ("认证通过一个很小的 `AuthProvider` 接口注入：`token()` 与可选的 `onUnauthorized()`。OAuth 只是它的一种实现（`adaptOAuthProvider`）。", "Auth is injected through a tiny `AuthProvider` interface: `token()` and an optional `onUnauthorized()`. OAuth is just one implementation of it (`adaptOAuthProvider`)."),
 ],
 how=[
  ("创建 `StdioTransport({ command, args })` 或 `StreamableHttpTransport({ url, authProvider })`。", "Create a `StdioTransport({ command, args })` or a `StreamableHttpTransport({ url, authProvider })`."),
  ("`new McpClient({ name, version })`，再 `await client.connect(transport)`。", "`new McpClient({ name, version })`, then `await client.connect(transport)`."),
  ("`listTools()` / `callTool()` / `readResource()`；把结果交给 `toLlmContent()` 变成模型能读的内容。", "`listTools()` / `callTool()` / `readResource()`; pass results to `toLlmContent()` to get model-ready content."),
 ],
 files=[
  (U + "index.ts", r"client\.ts", "export …", "包入口", "package entry"),
  (U + "client.ts", r"^export class McpClient", "McpClient", "客户端", "the client"),
  (U + "transports/transport.ts", r"^export interface McpTransport", "McpTransport", "传输接口", "transport interface"),
  (U + "auth-provider.ts", r"^export interface AuthProvider", "AuthProvider", "认证接口", "auth interface"),
  (U + "oauth/index.ts", r"authorizeMcp", "./oauth", "OAuth 入口", "OAuth entry"),
 ]),

dict(id="mcp-lifecycle", group="flows", layer="ext", diagram="mcp_lifecycle",
 title=("连接与握手", "Connecting and the handshake"),
 takeaway=(f"`connect(transport)` 只能调用一次：状态从 `idle` 到 `connecting`，启动传输，发送 `initialize`（默认协议版本 `{_V[0]}`），校验服务器选定的版本是否在支持列表中，再发 `notifications/initialized`，状态变为 `connected`。任何一步失败都会 `close()`，状态进入不可逆的 `closed`。",
           f"`connect(transport)` can be called once: the state goes from `idle` to `connecting`, the transport starts, `initialize` is sent (default protocol version `{_V[0]}`), the server's chosen version is checked against the supported list, `notifications/initialized` is sent, and the state becomes `connected`. Any failure calls `close()` and the state becomes the final `closed`."),
 points=[
  (f"支持的版本：{'、'.join(f'`{v}`' for v in _V)}。服务器选了别的版本时连接直接失败，而不是“尽量兼容”。", f"Supported versions: {', '.join(f'`{v}`' for v in _V)}. A server that picks another version fails the connection outright instead of a best-effort fallback."),
  ("协商出的版本通过 `setProtocolVersion()` 交给传输：HTTP 传输此后在每个请求上带 `MCP-Protocol-Version` 头。", "The negotiated version goes to the transport via `setProtocolVersion()`: from then on the HTTP transport sends an `MCP-Protocol-Version` header on every request."),
  ("配置了 `roots` 时自动声明 `roots` 能力，并响应服务器的 `roots/list` 请求；`ping` 永远内置。", "With a `roots` option the `roots` capability is declared automatically and the server's `roots/list` requests are answered; `ping` is always built in."),
  ("握手结果保存在 `serverInfo`、`serverCapabilities`、`instructions` 与 `protocolVersion` 上，供宿主展示或决策。", "Handshake results are kept on `serverInfo`, `serverCapabilities`, `instructions` and `protocolVersion` for the host to show or act on."),
 ],
 how=[
  ("订阅传输的 message / error / close；传输错误只上报，真正让请求失败的是传输关闭。", "Subscribe to the transport's message / error / close; transport errors are only reported — what fails requests is the transport closing."),
  ("`transport.start()` → `initialize` 请求（不可取消）→ `validateInitializeResult()` → 版本检查。", "`transport.start()` → the `initialize` request (not cancellable) → `validateInitializeResult()` → version check."),
  ("`setProtocolVersion?.(v)` → `notifications/initialized` → `state = \"connected\"`。", "`setProtocolVersion?.(v)` → `notifications/initialized` → `state = \"connected\"`."),
 ],
 files=[
  (U + "client.ts", r"^\tasync connect\(transport", "connect()", "握手", "the handshake"),
  (U + "client.ts", r"^type ClientState = ", "ClientState", "4 个状态", "four states"),
  (U + "protocol/types.ts", r"^export const SUPPORTED_PROTOCOL_VERSIONS", "SUPPORTED_PROTOCOL_VERSIONS", "支持的版本", "supported versions"),
  (U + "protocol/types.ts", r"^export interface ClientCapabilities", "ClientCapabilities", "客户端能力", "client capabilities"),
  (U + "protocol/types.ts", r"^export interface ServerCapabilities", "ServerCapabilities", "服务器能力", "server capabilities"),
 ]),

dict(id="mcp-requests", group="flows", layer="ext", diagram="mcp_requests",
 title=("请求、超时与取消", "Requests, timeouts and cancellation"),
 takeaway=(f"每个请求拿到一个递增的整数 id，记进 `pending` 表并启动超时（默认 {_TO:,} ms）。响应、超时、`signal` 中止与传输关闭是四种结局；后两者之外的取消都会通知服务器 `notifications/cancelled`。反方向，服务器发来的请求交给注册的处理器，每个都有自己的 `AbortSignal`。",
           f"Each request gets an increasing integer id, an entry in the `pending` map and a timeout (default {_TO:,} ms). A response, a timeout, a `signal` abort and the transport closing are the four endings; timeouts and aborts also tell the server with `notifications/cancelled`. In the other direction, server requests go to registered handlers, each with its own `AbortSignal`."),
 points=[
  ("传了 `onProgress` 时，请求的 `_meta.progressToken` 就是它的 id；每条 `notifications/progress` 都会重新计时——持续报进度的长任务不会超时。", "With `onProgress`, the request's `_meta.progressToken` is its id; every `notifications/progress` re-arms the timeout — long tasks that keep reporting never time out."),
  ("`initialize` 例外：规范禁止取消它，所以中止或超时只在本地 reject。", "`initialize` is the exception: the spec forbids cancelling it, so an abort or timeout only rejects locally."),
  ("没有处理器的服务器请求得到 `-32601 Method not found`；处理器抛出 `McpError` 时原样返回 code 与 data，其他异常变成 `-32603`。", "Server requests without a handler get `-32601 Method not found`; a handler that throws `McpError` returns its code and data as is, any other exception becomes `-32603`."),
  ("`listTools()` 等方法跟着 `nextCursor` 自动翻页：重复的 cursor 抛错，最多 1,000 页。", "`listTools()` and friends follow `nextCursor` automatically: a repeated cursor throws, and there are at most 1,000 pages."),
 ],
 how=[
  ("`request(method, params, { signal, timeoutMs, onProgress })` → `requestInternal()`。", "`request(method, params, { signal, timeoutMs, onProgress })` → `requestInternal()`."),
  ("`pending.set(id, entry)` → `armTimeout()` → `transport.send()`；发送失败立即 reject。", "`pending.set(id, entry)` → `armTimeout()` → `transport.send()`; a failed send rejects at once."),
  ("`handleMessage()` 按响应 / 请求 / 通知分派；`handleResponse()` 删除 pending 并 resolve 或 reject `McpError`。", "`handleMessage()` dispatches responses / requests / notifications; `handleResponse()` removes the pending entry and resolves or rejects with `McpError`."),
 ],
 files=[
  (U + "client.ts", r"^\tprivate requestInternal\(|^\tprivate async requestInternal\(", "requestInternal()", "发出请求", "sending a request"),
  (U + "client.ts", r"^\tprivate armTimeout\(", "armTimeout()", "超时与重新计时", "timeouts and re-arming"),
  (U + "client.ts", r"^\tprivate cancelPending\(", "cancelPending()", "notifications/cancelled", "notifications/cancelled"),
  (U + "client.ts", r"^\tprivate async handleRequest\(", "handleRequest()", "服务器请求", "server requests"),
  (U + "client.ts", r"MAX_LIST_PAGES = ", "MAX_LIST_PAGES", "分页上限", "paging limit"),
  (U + "protocol/jsonrpc.ts", r"^export const JSON_RPC_ERROR_CODES", "JSON_RPC_ERROR_CODES", "错误码", "error codes"),
 ]),

dict(id="mcp-stdio", group="arch", layer="ext", diagram="mcp_stdio",
 title=("stdio 传输", "The stdio transport"),
 takeaway=("`StdioTransport` 用 `cross-spawn` 启动服务器进程（非 Windows 上放进独立的进程组），每条消息是一行 JSON。关闭遵循规范：先关 stdin 让服务器自己退出，500 ms 后对整个进程组发 SIGTERM，再过 2 秒发 SIGKILL。",
           "`StdioTransport` starts the server with `cross-spawn` (in its own process group on non-Windows), one JSON message per line. Shutdown follows the spec: close stdin and let the server exit, SIGTERM the whole process group after 500 ms, SIGKILL two seconds later."),
 points=[
  ("用进程组是为了 `npx`、`uvx` 这类包装命令：只杀包装进程会留下真正的服务器。Windows 上改用 `taskkill /T /F`。", "Process groups exist for wrapper commands such as `npx` and `uvx`: killing only the wrapper would leave the real server running. Windows uses `taskkill /T /F` instead."),
  ("宿主进程退出时，退出钩子对所有仍存活的进程组发 SIGTERM——即使宿主忘了关闭传输。", "When the host exits, an exit hook SIGTERMs every live process group — even if the host forgot to close the transport."),
  ("stdout 按 0x0a 切分；单行超过 16 MiB 丢弃并报错；stderr 只保留最后 64 KiB，同时回调 `onStderr`。", "stdout is split at 0x0a; a line over 16 MiB is dropped with an error; stderr keeps only its last 64 KiB and also goes to `onStderr`."),
  ("默认继承宿主的环境变量再叠加 `env`；`inheritEnv: false` 时只用 `env`。", "By default the host's environment is inherited and `env` layered on top; `inheritEnv: false` uses `env` alone."),
 ],
 how=[
  ("`start()`：`crossSpawn()` → 登记进程组 → 等待 `spawn` 或 `error` 事件。", "`start()`: `crossSpawn()` → register the process group → wait for `spawn` or `error`."),
  ("`send()`：写入 `JSON.stringify(message) + \"\\n\"`。", "`send()`: write `JSON.stringify(message) + \"\\n\"`."),
  ("`close()`：`stdin.end()` → SIGTERM（宽限期后）→ SIGKILL（`closeTimeoutMs` 后）；子进程 close 后再对进程组补一次 SIGTERM。", "`close()`: `stdin.end()` → SIGTERM (after the grace period) → SIGKILL (after `closeTimeoutMs`); after the child closes, the group gets one more SIGTERM."),
 ],
 files=[
  (U + "transports/stdio.ts", r"^export class StdioTransport", "StdioTransport", "stdio 传输", "the stdio transport"),
  (U + "transports/stdio.ts", r"^function killProcessTree\(", "killProcessTree()", "杀进程组", "killing the group"),
  (U + "transports/stdio.ts", r"^const STDIN_CLOSE_GRACE_MS", "STDIN_CLOSE_GRACE_MS", "宽限期", "grace period"),
  (U + "transports/stdio.ts", r"^\tprivate handleStdout\(", "handleStdout()", "按行分帧", "line framing"),
  (U + "transports/transport.ts", r"DEFAULT_MAX_MESSAGE_BYTES = ", "DEFAULT_MAX_MESSAGE_BYTES", "16 MiB", "16 MiB"),
 ]),

dict(id="mcp-http", group="flows", layer="ext", diagram="mcp_http",
 title=("Streamable HTTP 传输", "The Streamable HTTP transport"),
 takeaway=("所有消息都 POST 到同一个 URL。通知和响应得到 202；请求的回复要么是 JSON（单条或一批），要么是一条 SSE 流。握手完成后再打开一条 GET 的 SSE 流接收服务器主动发来的消息。两种流断开时按退避策略重连，并用 `Last-Event-ID` 续传。",
           "Every message is POSTed to the same URL. Notifications and responses get 202; a request is answered with JSON (one message or a batch) or an SSE stream. After the handshake a GET SSE stream is opened for messages the server initiates. Both kinds of stream reconnect with back-off when they drop, resuming with `Last-Event-ID`."),
 points=[
  ("会话：服务器在响应头里给出 `Mcp-Session-Id`，之后每个请求都带上；带着会话 id 收到 404 → `McpSessionExpiredError`。", "Sessions: the server returns `Mcp-Session-Id` in a response header and every later request carries it; a 404 with a session id → `McpSessionExpiredError`."),
  ("401（或 403 且 `error=\"insufficient_scope\"`）先交给 `authProvider.onUnauthorized()` 一次，然后用新凭据重发；仍失败就抛 `McpAuthRequiredError`。", "A 401 (or a 403 with `error=\"insufficient_scope\"`) goes to `authProvider.onUnauthorized()` once, then the request is retried with the new credentials; if it still fails, `McpAuthRequiredError` is thrown."),
  ("重试只针对 408、429、5xx 与网络错误；认证、会话和协议错误不重试。响应流无法续传时，只为那一个请求合成一条 `-32603` 错误响应。", "Only 408, 429, 5xx and network errors are retried; auth, session and protocol errors are not. When a response stream cannot resume, a synthetic `-32603` error response fails just that one request."),
  ("`close()` 带会话 id 发 `DELETE`（1 秒超时，复用最后一个 token，不触发刷新）。", "`close()` sends `DELETE` with the session id (1-second timeout, reusing the last token so no refresh is triggered)."),
 ],
 how=[
  ("`send()`：`authorizedFetch(\"POST\")` → `checkResponse()` → `captureSession()` → 按消息类型和 Content-Type 分支。", "`send()`: `authorizedFetch(\"POST\")` → `checkResponse()` → `captureSession()` → branch on message kind and Content-Type."),
  ("`consumeSseStream()` 解析 `data:` / `event:` / `id:` / `retry:`，单个事件同样限制在 16 MiB。", "`consumeSseStream()` parses `data:` / `event:` / `id:` / `retry:`; a single event is capped at 16 MiB too."),
  ("`runGetStream()` 循环：`openSseStream(lastEventId)`（405 = 服务器不提供）→ 读到断开 → `reconnectDelay()` → 重连。", "`runGetStream()` loops: `openSseStream(lastEventId)` (405 = server offers none) → read until it drops → `reconnectDelay()` → reconnect."),
 ],
 files=[
  (U + "transports/streamable-http.ts", r"^export class StreamableHttpTransport", "StreamableHttpTransport", "HTTP 传输", "the HTTP transport"),
  (U + "transports/streamable-http.ts", r"^export async function consumeSseStream\(", "consumeSseStream()", "SSE 解析", "SSE parsing"),
  (U + "transports/streamable-http.ts", r"^\tprivate async authorizedFetch\(", "authorizedFetch()", "认证重试", "auth retry"),
  (U + "transports/streamable-http.ts", r"^\tprivate async consumeResponseStream\(", "consumeResponseStream()", "响应流续传", "response-stream resumption"),
  (U + "transports/streamable-http.ts", r"^\tprivate async runGetStream\(", "runGetStream()", "GET 流", "the GET stream"),
  (U + "transports/streamable-http.ts", r"^function isTransientStatus\(", "isTransientStatus()", "可重试状态", "retryable statuses"),
 ]),

dict(id="mcp-oauth", group="flows", layer="ext", diagram="mcp_oauth",
 title=("OAuth 授权", "OAuth authorization"),
 takeaway=("`authorizeMcp()` 是整个 MCP 授权规范的实现：从 401 的 `WWW-Authenticate` 出发发现受保护资源与授权服务器的元数据，确定 resource 与 scope，取得客户端身份（已存、Client ID Metadata Document 或动态注册），能刷新就刷新，否则发起 PKCE 授权跳转；回调带回 code 后再调用一次完成换取。",
           "`authorizeMcp()` implements the whole MCP authorization spec: starting from a 401's `WWW-Authenticate`, it discovers protected-resource and authorization-server metadata, settles resource and scope, obtains a client identity (stored, a Client ID Metadata Document, or dynamic registration), refreshes if it can, and otherwise starts a PKCE redirect; when the callback brings back a code, a second call completes the exchange."),
 points=[
  ("`adaptOAuthProvider()` 把它包装成传输用的 `AuthProvider`：并发的 401 共用一次授权；如果出错请求用的 token 已经被别人换掉了，就直接重试——轮换的 refresh token 不能用两次。", "`adaptOAuthProvider()` wraps it as the transport's `AuthProvider`: concurrent 401s share one authorization; if the failing request's token was already replaced, it simply retries — a rotating refresh token cannot be used twice."),
  ("403 `insufficient_scope` 是 step-up：跳过刷新，请求“已授予 ∪ 挑战要求”的 scope。", "A 403 `insufficient_scope` is a step-up: refresh is skipped and the scope requested is “granted ∪ challenged”."),
  ("出错恢复：`invalid_client` / `unauthorized_client` 清空所有凭据重来一次；`invalid_grant` 只清令牌重来一次。", "Recovery: `invalid_client` / `unauthorized_client` wipe all credentials and rerun once; `invalid_grant` wipes the tokens only and reruns once."),
  ("安全检查：授权服务器必须支持 PKCE S256；带 code 回来时校验 `iss`（RFC 9207）；protected resource 必须与服务器 URL 匹配；状态按精确的 serverUrl 存取。", "Safety checks: the authorization server must support PKCE S256; `iss` is checked when a code comes back (RFC 9207); the protected resource must match the server URL; state is stored per exact serverUrl."),
 ],
 how=[
  ("宿主实现或使用 `McpOAuthProvider`（可注入持久化的 `McpOAuthStateStore`）。", "The host implements or uses `McpOAuthProvider` (optionally with a persistent `McpOAuthStateStore`)."),
  ("传输里用 `adaptOAuthProvider(provider)`；需要用户登录时请求以 `McpOAuthAuthorizationRequiredError` 失败。", "Use `adaptOAuthProvider(provider)` in the transport; when the user must sign in, requests fail with `McpOAuthAuthorizationRequiredError`."),
  ("登录：`OAuthCallbackServer.listen()` → `authorizeMcp()` 返回 \"REDIRECT\" 并打开浏览器 → 拿到回调 → 带 `authorizationCode` 再调一次 `authorizeMcp()`。", "Sign-in: `OAuthCallbackServer.listen()` → `authorizeMcp()` returns \"REDIRECT\" and opens the browser → receive the callback → call `authorizeMcp()` again with `authorizationCode`."),
 ],
 files=[
  (U + "oauth/flow.ts", r"^export async function authorizeMcp\(", "authorizeMcp()", "入口与错误恢复", "entry and recovery"),
  (U + "oauth/flow.ts", r"^async function runFlow\(", "runFlow()", "完整流程", "the full flow"),
  (U + "oauth/flow.ts", r"^export function adaptOAuthProvider\(", "adaptOAuthProvider()", "接到传输上", "plugging into transports"),
  (U + "oauth/discovery.ts", r"^export async function discoverOAuthServerInfo\(", "discoverOAuthServerInfo()", "元数据发现", "metadata discovery"),
  (U + "oauth/provider.ts", r"^export class McpOAuthProvider", "McpOAuthProvider", "默认 provider", "default provider"),
  (U + "oauth/callback.ts", r"^export class OAuthCallbackServer", "OAuthCallbackServer", "本地回调", "loopback callback"),
 ]),

dict(id="mcp-content", group="types", layer="ext", diagram="mcp_content",
 title=("内容转换与错误类型", "Content conversion and error types"),
 takeaway=("`toLlmContent()` 把 `CallToolResult` 变成模型 API 接受的两种块：文本与图片。文本、图片和内嵌的文本 / 图片资源原样转换；音频、资源链接和其他二进制资源变成一行占位文字；没有内容块却有 `structuredContent` 时输出它的 JSON。",
           "`toLlmContent()` turns a `CallToolResult` into the two block kinds model APIs accept: text and images. Text, images and embedded text / image resources convert directly; audio, resource links and other binary resources become a one-line placeholder; a result with no content blocks but `structuredContent` yields its JSON."),
 points=[
  ("`LlmContent` 的形状与 `pi-ai` 的 `TextContent` / `ImageContent` 一致，但 `pi-mcp` 并不依赖 `pi-ai`。", "`LlmContent` has the same shape as `pi-ai`'s `TextContent` / `ImageContent`, yet `pi-mcp` does not depend on `pi-ai`."),
  ("错误按类型区分：超时、中止、连接关闭、HTTP 状态（及其两个子类：需要认证、会话过期）与需要登录。除这两个子类外都直接继承 `Error`。", "Errors are told apart by type: timeouts, aborts, closed connections, HTTP statuses (with two subclasses: auth required and session expired) and required sign-in. Apart from those two subclasses, all extend `Error` directly."),
  ("`McpError` 携带 JSON-RPC 的 `code` 与 `data`，处理器抛出它可以向服务器返回任意错误码。", "`McpError` carries the JSON-RPC `code` and `data`; a handler that throws it can return any error code to the server."),
 ],
 how=[
  ("`callTool()` 校验结果形状，缺失的 `content` 补成 `[]`。", "`callTool()` validates the result shape and defaults a missing `content` to `[]`."),
  ("`toLlmContent(result)` 逐块转换；`isError` 由调用方自行决定如何呈现。", "`toLlmContent(result)` converts block by block; how to present `isError` is up to the caller."),
  ("用 `instanceof` 区分错误：例如 `McpSessionExpiredError` 时重新连接。", "Tell errors apart with `instanceof`: e.g. reconnect on `McpSessionExpiredError`."),
 ],
 files=[
  (U + "protocol/content.ts", r"^export function toLlmContent\(", "toLlmContent()", "结果 → 模型内容", "result → model content"),
  (U + "protocol/content.ts", r"^export type ContentBlock = ", "ContentBlock", "5 种内容块", "five block kinds"),
  (U + "protocol/jsonrpc.ts", r"^export class McpError ", "McpError", "JSON-RPC 错误", "JSON-RPC error"),
  (U + "transports/streamable-http.ts", r"^export class McpHttpError ", "McpHttpError", "HTTP 错误", "HTTP errors"),
  (U + "oauth/errors.ts", r"^export class McpOAuthAuthorizationRequiredError", "McpOAuthAuthorizationRequiredError", "需要登录", "sign-in required"),
 ]),

dict(id="mcp-pi", group="arch", layer="ext", diagram="mcp_pi",
 title=("在 pi 中的使用", "How pi uses it"),
 takeaway=("`coding-agent` 的内置 MCP 扩展读取全局和受信任项目的 `mcp.json`（格式与其他 MCP 客户端相同），以及扩展用 `pi.registerMcpServer()` 注册的服务器，在后台连接，并把工具注册为 `mcp__<server>__<tool>`。默认的 exposure 是 `codemode`：MCP 工具不进模型的工具声明，只能在 codemode 脚本里调用。",
           "`coding-agent`'s built-in MCP extension reads the global and trusted-project `mcp.json` (same shape as other MCP clients) plus servers extensions register with `pi.registerMcpServer()`, connects in the background, and registers tools as `mcp__<server>__<tool>`. The default exposure is `codemode`: MCP tools stay out of the model's tool declarations and are called from codemode scripts."),
 points=[
  ("四种 exposure：`codemode`（默认）、`deferred`（`tool_search` 加载后才声明）、`direct`（立即声明）、`hidden`；`toolExposure` 可以按工具覆盖。", "Four exposures: `codemode` (default), `deferred` (declared once `tool_search` loads them), `direct` (declared right away) and `hidden`; `toolExposure` overrides per tool."),
  ("项目的 `mcp.json` 不能设置 `auth`——仓库不能决定凭据发往哪里。只写 enabled / exposure 的项目条目只覆盖全局同名服务器的这几项。", "A project `mcp.json` cannot set `auth` — a repository must not choose where credentials go. A project entry with only enabled / exposure just overrides those fields of the global server of the same name."),
  ("连接从不自己弹浏览器：只用存下的 token 和 refresh token；需要登录时在 `/mcp` 中完成，凭据存在 `<agent-dir>/mcp-auth.json`。", "Connections never open a browser on their own: they use the stored token and refresh token; sign-in happens in `/mcp`, and credentials live in `<agent-dir>/mcp-auth.json`."),
  ("每次 MCP 调用都走 pi 的工具管线，`tool_call` / `tool_result` 钩子和权限扩展照常生效。", "Every MCP call runs through pi's tool pipeline, so `tool_call` / `tool_result` hooks and permission extensions apply as usual."),
 ],
 how=[
  ("`loadMcpConfig()`：全局 `mcp.json` → 受信任项目的 `.pi/mcp.json` → 合并与校验。", "`loadMcpConfig()`: global `mcp.json` → the trusted project's `.pi/mcp.json` → merge and validate."),
  ("`runtime.ts`：有 `command` → `StdioTransport`，有 `url` → `StreamableHttpTransport`；`new McpClient()` 并 `connect()`。", "`runtime.ts`: `command` → `StdioTransport`, `url` → `StreamableHttpTransport`; `new McpClient()` and `connect()`."),
  ("`createMcpToolName()` 生成工具名（超过 64 字符或冲突时加 8 位哈希）；资源通过 `list_mcp_resources` 等 3 个工具访问。", "`createMcpToolName()` builds tool names (an 8-hex hash suffix when longer than 64 characters or clashing); resources go through `list_mcp_resources` and two other tools."),
 ],
 files=[
  (CA + "extensions/mcp/index.ts", r"^export function createMcpExtension\(", "createMcpExtension()", "扩展入口", "extension entry"),
  (CA + "extensions/mcp/config.ts", r"^export function loadMcpConfig\(", "loadMcpConfig()", "读取 mcp.json", "reading mcp.json"),
  (CA + "extensions/mcp/runtime.ts", r"new StdioTransport\(\{", "StdioTransport", "选择传输", "choosing a transport"),
  (CA + "extensions/mcp/tools.ts", r"^export function createMcpToolName\(", "createMcpToolName()", "工具命名", "tool naming"),
  (CA + "core/mcp-servers.ts", r"^export type McpExposure", "McpExposure", "4 种 exposure", "four exposures"),
  (CA + "extensions/mcp/oauth.ts", r"new FileAuthStorageBackend\(join\(getAgentDir\(\), \"mcp-auth\.json\"\)\)", "mcp-auth.json", "凭据存储", "credential storage"),
 ]),
]

EXT_POINTS = [
 ("McpTransport", ("实现 start / send / close 与三个监听即可接入新的传输。", "Implement start / send / close and three listeners to add a transport.")),
 ("AuthProvider", ("token() 加可选的 onUnauthorized()：任何认证方案。", "token() plus an optional onUnauthorized(): any auth scheme.")),
 ("OAuthClientProvider · McpOAuthStateStore", ("自定义 OAuth 状态的存储与跳转方式。", "Customise how OAuth state is stored and how redirects happen.")),
 ("client.setRequestHandler(method, fn)", ("响应服务器发来的请求（如 sampling、elicitation）。", "Answer requests from the server (e.g. sampling, elicitation).")),
 ("client.onNotification(method, fn)", ("监听 list_changed 等通知。", "Listen for notifications such as list_changed.")),
 ("McpClientOptions.roots", ("声明 roots 能力并提供根目录列表。", "Declare the roots capability and provide the roots.")),
 ("createInMemoryTransportPair()", ("./testing：在同一进程里测试客户端与服务器。", "./testing: test a client and a server in one process.")),
]
XREF = [('coding-agent', ('内置 MCP 扩展：mcp.json、exposure、/mcp 与 OAuth 登录', 'the built-in MCP extension: mcp.json, exposure, /mcp and OAuth sign-in')),
        ('codemode', ('MCP 工具默认在 codemode 脚本里调用', 'MCP tools are called from codemode scripts by default'))]
