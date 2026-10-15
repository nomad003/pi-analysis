# pi-protocol deep dive. Same section schema as deep_agent.py; files: (path, regex, symbol, zh, en)
from pkgsrc import Pkg
P_ = Pkg('packages/protocol/src/')
U = 'packages/protocol/src/'
SRV = 'packages/server/src/'
CLI = 'packages/client/src/'
SLIDE_KEYS = ['proto_arch', 'proto_pipe', 'proto_messages', 'proto_targets', 'proto_handshake', 'proto_frame', 'proto_cbor', 'proto_chord']
_TS = P_.total()

INTRO = dict(
 takeaway=("`pi-protocol` 是远程 pi 会话的线上格式，且只有格式：协议版本 8 定义了 3 种客户端消息和 5 种服务端消息、把调用围在一台逻辑服务器 / 一个 Session / 一个实时附着里的路由、一个严格的 CBOR 子集，以及“4 字节大端长度 + 一个 CBOR 项”的分帧。它不懂任何服务契约：`call`、`result`、`update` 只被检查为严格 JSON，其语义归 `chord`，数据归应用。`pi-client` 与 `pi-server` 是它的两端。",
           "`pi-protocol` is the wire format for remote pi sessions, and only the format: protocol version 8 defines 3 client messages and 5 server messages, routes that fence a call to one logical server / one Session / one live attachment, a strict CBOR subset, and framing as “a 4-byte big-endian length + one CBOR item”. It knows no service contract: `call`, `result` and `update` are only checked to be strict JSON, their meaning belongs to `chord` and the data to the application. `pi-client` and `pi-server` are its two ends."),
 role=(f"{_TS:,} 行 TypeScript，运行时无关（不依赖 Node API），一个导入路径。依赖 `chord`（`JsonValue` / `isJsonValue`）与 `typebox`（schema）。被 `pi-client`、`pi-server` 以及 coding-agent 的实验性 server / client 运行时使用。README 明确写着：实验性，不保证兼容。",
       f"{_TS:,} lines of TypeScript, runtime-neutral (no Node APIs), one import path. Depends on `chord` (`JsonValue` / `isJsonValue`) and `typebox` (schemas). Used by `pi-client`, `pi-server` and coding-agent's experimental server / client runtime. The README is explicit: experimental, no compatibility guarantees."),
)

SECTIONS = [
dict(id="proto-arch", group="arch", layer="modes", diagram="proto_arch",
 title=("三层：信封、编解码、分帧", "Three layers: envelopes, codec, framing"),
 takeaway=("`protocol.ts` 用 TypeBox 声明信封 schema；`codec.ts` 把“校验 → CBOR → 分帧”串成 `encodeClientMessage()` / `encodeServerMessage()`，反向是增量的 `ClientMessageDecoder` / `ServerMessageDecoder`；`framing.ts` 只管长度前缀；`cbor/` 是一个手写的、只支持定长项的 CBOR 编解码器。`index.ts` 把这些全部从一个导入路径导出。",
           "`protocol.ts` declares the envelope schemas with TypeBox; `codec.ts` chains “validate → CBOR → frame” into `encodeClientMessage()` / `encodeServerMessage()`, and the incremental `ClientMessageDecoder` / `ServerMessageDecoder` run it backwards; `framing.ts` only handles the length prefix; `cbor/` is a hand-written CBOR codec for definite-length items only. `index.ts` exports all of it from one import path."),
 points=[
  ("没有任何 Node 专用 API：同一份代码可以用在浏览器、Bun 或 worker 里；传输（Unix socket、WebSocket…）由 client / server 提供。", "No Node-only APIs: the same code works in a browser, Bun or a worker; transports (Unix sockets, WebSockets…) come from client / server."),
  ("schema 是 `additionalProperties: false` 的 StrictObject，所以多一个字段也会被拒绝。", "Schemas are StrictObjects with `additionalProperties: false`, so even one extra field is rejected."),
  ("coding-agent 把 protocol、client、server 三个包都只列为 devDependencies，供 `experimental/` 下的 server 与 client 运行时使用。", "coding-agent lists protocol, client and server only as devDependencies, for the server and client runtime under `experimental/`."),
 ],
 how=[
  ("发送：`transport.send(encodeClientMessage({ type: \"hello\", version: PROTOCOL_VERSION }))`。", "Send: `transport.send(encodeClientMessage({ type: \"hello\", version: PROTOCOL_VERSION }))`."),
  ("接收：`const decoder = new ServerMessageDecoder({ maxFrameLength })`，然后 `for (const m of decoder.push(chunk)) …`，流结束时 `decoder.end()`。", "Receive: `const decoder = new ServerMessageDecoder({ maxFrameLength })`, then `for (const m of decoder.push(chunk)) …`, and `decoder.end()` when the stream ends."),
  ("两端的 `maxFrameLength` 要一致（默认 16 MiB）。", "Both peers must use the same `maxFrameLength` (16 MiB by default)."),
 ],
 files=[
  (U + "index.ts", r'export \* from "./codec.ts"', "export *", "唯一入口", "the only entry"),
  (U + "protocol.ts", r"^export const PROTOCOL_VERSION", "PROTOCOL_VERSION", "协议版本", "protocol version"),
  (U + "codec.ts", r"^export function encodeClientMessage", "encodeClientMessage()", "校验并编码一帧", "validate and encode one frame"),
  (U + "framing.ts", r"^export class FrameDecoder", "FrameDecoder", "拆帧", "frame splitting"),
  (U + "cbor/encoder.ts", r"^export function encodeCbor", "encodeCbor()", "CBOR 编码", "CBOR encoding"),
 ]),

dict(id="proto-pipe", group="flows", layer="modes", diagram="proto_pipe",
 title=("一条消息的往返", "One message, there and back"),
 takeaway=("编码先校验：`parseClientMessage()` 用 TypeBox `Check` 检查 schema，再用 chord 的 `isJsonValue` 递归检查严格 JSON；然后 `encodeCbor()`（上限 = `maxFrameLength`）和 `encodeFrame()`。接收方把任意切分的字节交给 `push()`：`FrameDecoder` 产出完整负载，`decodeCbor()` 解出恰好一个项，同一套 schema 再检查一次。",
           "Encoding validates first: `parseClientMessage()` checks the schema with TypeBox `Check`, then strict JSON recursively with chord's `isJsonValue`; then `encodeCbor()` (limit = `maxFrameLength`) and `encodeFrame()`. The receiver hands arbitrarily split bytes to `push()`: `FrameDecoder` yields complete payloads, `decodeCbor()` decodes exactly one item, and the same schemas are checked again."),
 points=[
  ("任何失败都变成 `ProtocolValidationError`：CborError 与 FrameError 被包装，错误消息截断到 500 个字符。", "Every failure becomes a `ProtocolValidationError`: CborError and FrameError are wrapped and the message is cut to 500 characters."),
  ("解码器失败后进入 failed：之后的 `push()` 和 `end()` 都直接抛错，没有“跳过坏帧”这回事——调用方应该断开连接。", "A failed decoder stays failed: every later `push()` and `end()` throws; there is no “skip the bad frame” — the caller should drop the connection."),
  ("被拒绝的非 JSON 值：`Uint8Array`、非有限数、`undefined`、带原型的对象和环。", "Rejected non-JSON values: `Uint8Array`, non-finite numbers, `undefined`, objects with prototypes, and cycles."),
 ],
 how=[
  ("`encodeProtocolMessage(value, parse, kind)`：先 `parse(value)`，再 `encodeFrame(encodeCbor(validated, { maxByteLength }))`。", "`encodeProtocolMessage(value, parse, kind)`: `parse(value)` first, then `encodeFrame(encodeCbor(validated, { maxByteLength }))`."),
  ("`ValidatedMessageDecoder.push(chunk)`：对每个完整帧 `parse(decodeCbor(frame))`，返回 0..n 条消息。", "`ValidatedMessageDecoder.push(chunk)`: `parse(decodeCbor(frame))` for every complete frame, returning 0..n messages."),
  ("流结束时调用 `end()`：还有半帧就报 \"Truncated frame at end of stream\"。", "Call `end()` when the stream ends: a partial frame reports \"Truncated frame at end of stream\"."),
 ],
 files=[
  (U + "codec.ts", r"^export function parseClientMessage", "parseClientMessage()", "schema + 严格 JSON", "schema + strict JSON"),
  (U + "codec.ts", r"^function encodeProtocolMessage", "encodeProtocolMessage()", "编码流水线", "the encode pipeline"),
  (U + "codec.ts", r"^class ValidatedMessageDecoder", "ValidatedMessageDecoder", "增量解码", "incremental decoding"),
  (U + "codec.ts", r"^function boundedErrorMessage", "boundedErrorMessage()", "500 字符", "500 characters"),
  (U + "codec.ts", r"^export class ProtocolValidationError", "ProtocolValidationError", "唯一的错误类型", "the one error type"),
 ]),

dict(id="proto-messages", group="types", layer="modes", diagram="proto_messages",
 title=("8 种信封", "The 8 envelopes"),
 takeaway=("客户端发 `hello`（必须是第一帧）、`request`、`cancel`；服务端发 `hello`（带 `serverId`）、`hello_error`（终止）、`response`（`ok: true` 带可选 `result`，或 `ok: false` 带 `error`）、`service_update`（某个订阅的更新）和 `attachment`（带外的路由变化）。错误是 `{ code, message }`，code 是非空字符串，对协议不透明。",
           "The client sends `hello` (must be the first frame), `request` and `cancel`; the server sends `hello` (with `serverId`), `hello_error` (terminal), `response` (`ok: true` with an optional `result`, or `ok: false` with `error`), `service_update` (an update for one subscription) and `attachment` (an out-of-band route change). Errors are `{ code, message }`, the code a non-empty string that is opaque to the protocol."),
 points=[
  ("客户端 `hello` 的 `version` 是任意非负整数，服务端的则是字面量 8：版本不符由服务端用 `hello_error { code: \"version\" }` 回答。", "The client's `hello.version` is any non-negative integer, the server's the literal 8: a mismatch is answered by the server with `hello_error { code: \"version\" }`."),
  ("请求 id 是客户端选的非空字符串（pi-client 用 `request-1`、`request-2`…），回应用同一个 id 关联。", "Request ids are non-empty strings chosen by the client (pi-client uses `request-1`, `request-2`…); responses correlate by the same id."),
  ("`service_update` 只按 `subscriptionId` 寻址，不带 target：订阅已经属于某个连接和附着。", "`service_update` is addressed by `subscriptionId` only, without a target: the subscription already belongs to a connection and attachment."),
 ],
 how=[
  ("所有消息都是 `Type.Union`：`ClientMessageSchema` 有 3 个成员，`ServerMessageSchema` 有 5 个（`ResponseEnvelope` 自身又是 ok / not-ok 的联合）。", "All messages are a `Type.Union`: `ClientMessageSchema` has 3 members and `ServerMessageSchema` 5 (`ResponseEnvelope` is itself an ok / not-ok union)."),
  ("类型从 schema 推导：`type ClientMessage = Static<typeof ClientMessageSchema>`。", "Types are derived from the schemas: `type ClientMessage = Static<typeof ClientMessageSchema>`."),
  ("void 回应：`{ type: \"response\", id, ok: true }`，没有 `result` 字段。", "A void response: `{ type: \"response\", id, ok: true }`, without a `result` field."),
 ],
 files=[
  (U + "protocol.ts", r"^const ClientHelloSchema", "ClientHelloSchema", "客户端 hello", "client hello"),
  (U + "protocol.ts", r"^const RequestEnvelopeSchema", "RequestEnvelopeSchema", "请求", "request"),
  (U + "protocol.ts", r"^const ResponseEnvelopeSchema", "ResponseEnvelopeSchema", "回应", "response"),
  (U + "protocol.ts", r"^const ServiceEventEnvelopeSchema", "ServiceEventEnvelopeSchema", "订阅更新", "subscription update"),
  (U + "protocol.ts", r"^export const ServerMessageSchema", "ServerMessageSchema", "5 种服务端消息", "5 server messages"),
 ]),

dict(id="proto-targets", group="types", layer="modes", diagram="proto_targets",
 title=("路由：serverId、sessionId、attachmentId", "Routes: serverId, sessionId, attachmentId"),
 takeaway=("每个 `request` 与 `cancel` 都带一个 `RpcTarget`：服务器级调用是 `{ serverId }`，Session 调用是 `{ serverId, sessionId, attachmentId }`。`serverId` 是规范的小写 UUIDv4，是逻辑身份而不是 socket 地址；`attachmentId` 由服务器在每次成功 attach 时生成，只通过带外的 `attachment` 消息告诉客户端。三者合起来防止跨服务器、跨 Session 和过期的调用。",
           "Every `request` and `cancel` carries an `RpcTarget`: server-wide calls use `{ serverId }`, Session calls `{ serverId, sessionId, attachmentId }`. `serverId` is a canonical lowercase UUIDv4, a logical identity rather than a socket address; `attachmentId` is generated by the server on every successful attach and reaches the client only through the out-of-band `attachment` message. Together they prevent cross-server, cross-Session and stale calls."),
 points=[
  ("管理服务的 `attach()` / `detach()` 不返回任何路由 id：服务器装好路由后才发 `attachment`，解除时发 `attachment: null`。", "Management `attach()` / `detach()` return no route ids: the server sends `attachment` once the route is installed, and `attachment: null` when it is cleared."),
  ("切换或重新附着后，带旧 `attachmentId` 的延迟帧被拒绝（`session_not_attached`）。", "After switching or reattaching, delayed frames with an old `attachmentId` are rejected (`session_not_attached`)."),
  ("一个 Session 可以同时被多个 presentation 附着；同一连接重复 attach 同一个 Session 是幂等的。", "A Session can have several presentation attachments at once; repeating attach for the same Session on one connection is idempotent."),
  ("`isServerId()` 是导出的校验函数；client 与 server 的构造函数都用它拒绝非规范的 id。", "`isServerId()` is the exported check; the client and server constructors both use it to reject non-canonical ids."),
 ],
 how=[
  ("服务器级：`client.request({ serverId: client.hello.serverId }, call)`。", "Server-wide: `client.request({ serverId: client.hello.serverId }, call)`."),
  ("Session：`client.request(client.attachment, call)`——attachment 是最近一次带外消息给出的完整路由。", "Session: `client.request(client.attachment, call)` — the attachment is the full route from the latest out-of-band message."),
  ("服务端先比较 `target.serverId`（`wrong_server`），再在 SessionRouter 里比较 sessionId 与 attachmentId。", "The server compares `target.serverId` first (`wrong_server`), then sessionId and attachmentId in the SessionRouter."),
 ],
 files=[
  (U + "protocol.ts", r"^const ServerIdSchema", "ServerIdSchema", "UUIDv4 正则", "the UUIDv4 pattern"),
  (U + "protocol.ts", r"^const SessionTargetSchema", "SessionTargetSchema", "Session 路由", "Session route"),
  (U + "protocol.ts", r"^const AttachmentEnvelopeSchema", "AttachmentEnvelopeSchema", "带外路由变化", "out-of-band route change"),
  (SRV + "session-router.ts", r"id: randomUUID\(\),", "attachment.id", "服务器生成 attachmentId", "the server generates attachmentId"),
  (SRV + "session-router.ts", r"^\tprivate requireAttachment\(", "requireAttachment()", "检查路由", "checking the route"),
 ]),

dict(id="proto-handshake", group="flows", layer="modes", diagram="proto_handshake",
 title=("一条连接上的消息顺序", "Message order on one connection"),
 takeaway=("客户端先发 `hello { version: 8 }`；服务端检查版本、为这个连接准备服务器级服务，然后回 `hello { version, serverId }`——或者 `hello_error` 并关闭。之后客户端发 `request` / `cancel`，服务端发 `response`、`service_update` 和 `attachment`。订阅的快照在回应里，在快照之前产生的更新在服务端排队，回应之后才发出。",
           "The client sends `hello { version: 8 }` first; the server checks the version, prepares the server-scoped services for this connection, then answers `hello { version, serverId }` — or `hello_error` and closes. After that the client sends `request` / `cancel` and the server sends `response`, `service_update` and `attachment`. A subscription's snapshot is in its response; updates produced before it queue on the server and go out after the response."),
 points=[
  ("服务端握手超时默认 5 秒；第一条消息不是 hello、或之后再发 hello，都会以 `hello_error { code: \"invalid_request\" }` 结束连接。", "The server's handshake timeout is 5 seconds by default; a first message that is not hello, or a later hello, ends the connection with `hello_error { code: \"invalid_request\" }`."),
  ("客户端检查服务端报告的 `serverId` 是否就是它期望的那台逻辑服务器，不符就断开。", "The client checks that the reported `serverId` is the logical server it expects, and disconnects otherwise."),
  ("握手期间到达的请求不会丢：服务端在握手完成后再处理它们。", "Requests arriving during the handshake are not lost: the server handles them once the handshake completes."),
  ("`cancel` 只取消同一连接上、同一 id 且同一 target 的活动请求；被取消的请求以 `cancelled` 回应。", "`cancel` only cancels an active request with the same id and the same target on the same connection; the cancelled request answers `cancelled`."),
 ],
 how=[
  ("`Server.dispatchMessage()`：awaitingHello → handshaking → ready；ready 之后按类型调用 `handleRequest` 或 `handleCancel`。", "`Server.dispatchMessage()`: awaitingHello → handshaking → ready; after that it calls `handleRequest` or `handleCancel` by type."),
  ("`Connection.#handleMessage()`（客户端）：连接中只接受 hello / hello_error；连上后 hello 类消息都是协议错误。", "`Connection.#handleMessage()` (client): while connecting only hello / hello_error are accepted; once connected, any hello-type message is a protocol error."),
  ("attach 的顺序：路由安装 → 带外 `attachment` → attach 调用的 `response`。", "Attach ordering: route installed → out-of-band `attachment` → the attach call's `response`."),
 ],
 files=[
  (SRV + "server.ts", r"^const DEFAULT_HANDSHAKE_TIMEOUT_MS", "DEFAULT_HANDSHAKE_TIMEOUT_MS", "5 秒", "5 seconds"),
  (SRV + "server.ts", r"^\tprivate async finishHandshake\(", "finishHandshake()", "版本检查与服务器 hello", "version check and server hello"),
  (SRV + "server.ts", r"^\tprivate handleCancel\(", "handleCancel()", "取消", "cancellation"),
  (CLI + "connection.ts", r"^\t#handleMessage\(message: ServerMessage\)", "#handleMessage()", "客户端握手", "client handshake"),
  (U + "codec.ts", r"^export function isSupportedProtocolVersion", "isSupportedProtocolVersion()", "版本判断", "version check"),
 ]),

dict(id="proto-frame", group="flows", layer="modes", diagram="proto_frame",
 title=("分帧与 FrameDecoder", "Framing and FrameDecoder"),
 takeaway=("一帧 = 4 字节无符号大端长度 + 恰好一个定长 CBOR 项。`FrameDecoder.push(chunk)` 接受任意切分与合并：它先凑齐 4 字节头，长度超过 `maxFrameLength` 时立刻失败（不等负载到达），长度为 0 时产出空帧，否则按 64 KiB 的块收集负载，收满后返回。状态只有 open、ended、failed 三个。",
           "A frame = a 4-byte unsigned big-endian length + exactly one definite-length CBOR item. `FrameDecoder.push(chunk)` accepts any splitting and coalescing: it fills the 4-byte header, fails at once if the length exceeds `maxFrameLength` (without waiting for the payload), yields an empty frame for length 0, and otherwise collects the payload in 64 KiB blocks and returns it when complete. There are only three states: open, ended and failed."),
 points=[
  ("负载总是被复制：返回的帧不引用调用方传入的 chunk，调用方可以复用自己的缓冲区。", "Payloads are always copied: returned frames never alias the caller's chunks, so callers may reuse their buffers."),
  ("按 64 KiB 分块分配，所以一个声明很大但迟迟不到的帧不会一次性占用全部内存。", "Allocation is in 64 KiB blocks, so a frame that declares a large size but arrives slowly does not reserve all of its memory up front."),
  ("`maxFrameLength` 可以是 0 到 0xffffffff；客户端与服务端还要求它 ≥ 1。", "`maxFrameLength` may be 0 to 0xffffffff; the client and server additionally require at least 1."),
 ],
 how=[
  ("`encodeFrame(payload)`：分配 4 + n 字节，写长度，复制负载。", "`encodeFrame(payload)`: allocate 4 + n bytes, write the length, copy the payload."),
  ("`push()` 的外层循环：头还没齐就继续读头；齐了就检查长度并开始收集负载；负载齐了就产出一帧并重置。", "`push()`'s outer loop: keep reading the header until complete; then check the length and start collecting; when the payload is complete, emit a frame and reset."),
  ("`end()`：头或负载只读了一部分 → failed + FrameError。", "`end()`: a partially read header or payload → failed + FrameError."),
 ],
 files=[
  (U + "framing.ts", r"^const PAYLOAD_BLOCK_SIZE", "PAYLOAD_BLOCK_SIZE", "64 KiB 块", "64 KiB blocks"),
  (U + "framing.ts", r"^export const DEFAULT_MAX_FRAME_LENGTH", "DEFAULT_MAX_FRAME_LENGTH", "16 MiB", "16 MiB"),
  (U + "framing.ts", r"^export function encodeFrame", "encodeFrame()", "加长度前缀", "add the length prefix"),
  (U + "framing.ts", r"^\tpush\(chunk: Uint8Array\)", "push()", "增量拆帧", "incremental splitting"),
  (U + "framing.ts", r"^\tend\(\): void \{", "end()", "截断检查", "truncation check"),
 ]),

dict(id="proto-cbor", group="types", layer="modes", diagram="proto_cbor",
 title=("严格的 CBOR 子集", "A strict CBOR subset"),
 takeaway=("`cbor/` 实现 RFC 8949 的一个严格子集：主类型 0–5 与 7 中的 false、true、null 和 float64；tag（主类型 6）、不定长项、半精度与单精度浮点一律拒绝。映射的键必须是字符串且不重复。默认上限：16 MiB、1,000,000 个元素、64 层嵌套（可配置到 512 层），长度与深度在遍历之前就检查。",
           "`cbor/` implements a strict subset of RFC 8949: major types 0–5 plus false, true, null and float64 from type 7; tags (major type 6), indefinite-length items and half / single floats are always rejected. Map keys must be unique strings. Default limits: 16 MiB, 1,000,000 elements and 64 nesting levels (configurable up to 512), with lengths and depth checked before traversal."),
 points=[
  ("编码器为整数选最短的参数；非整数与 `-0` 写成 float64（`0xfb`）；非有限数、非安全整数直接报错。", "The encoder picks the shortest argument for integers; non-integers and `-0` are written as float64 (`0xfb`); non-finite numbers and unsafe integers are errors."),
  ("文本按 fatal UTF-8 解码并保留开头的 BOM；编码时孤立代理项会被检测并拒绝。", "Text is decoded as fatal UTF-8 and keeps a leading BOM; lone surrogates are detected and rejected on encode."),
  ("解码出的对象用 `defineProperty` 设置属性，所以 `__proto__` 只是普通的数据键。", "Decoded objects set properties with `defineProperty`, so `__proto__` is just a data key."),
  ("字节串（主类型 2）在 CBOR 层是合法的，但信封层的严格 JSON 检查会拒绝它。", "Byte strings (major type 2) are legal at the CBOR layer but rejected by the envelope's strict-JSON check."),
 ],
 how=[
  ("`encodeCbor(value, { maxByteLength, maxContainerLength, maxDepth })` → `Uint8Array`。", "`encodeCbor(value, { maxByteLength, maxContainerLength, maxDepth })` → `Uint8Array`."),
  ("`decodeCbor(bytes, options)` → 恰好一个值；尾随数据是错误。", "`decodeCbor(bytes, options)` → exactly one value; trailing data is an error."),
  ("`hello` 的编码是 25 字节：4 字节长度 + 21 字节 CBOR（见图中的例子）。", "`hello` encodes to 25 bytes: a 4-byte length + 21 bytes of CBOR (see the example in the diagram)."),
 ],
 files=[
  (U + "cbor/options.ts", r"^export const DEFAULT_MAX_CBOR_BYTE_LENGTH", "DEFAULT_MAX_CBOR_*", "默认上限", "default limits"),
  (U + "cbor/decoder.ts", r"^\tprivate readItem\(", "readItem()", "按主类型解码", "decoding by major type"),
  (U + "cbor/decoder.ts", r"^\tprivate readLength\(", "readLength()", "拒绝不定长", "indefinite lengths refused"),
  (U + "cbor/encoder.ts", r"^function writeArgument\(", "writeArgument()", "最短参数", "shortest argument"),
  (U + "cbor/encoder.ts", r"^function encodeValue\(", "encodeValue()", "按值类型编码", "encoding by value type"),
 ]),

dict(id="proto-chord", group="arch", layer="modes", diagram="proto_chord",
 title=("protocol、chord 与应用的分界", "Where protocol, chord and the application meet"),
 takeaway=("protocol 只拥有信封：类型、id、路由和“负载是严格 JSON”这条规则。`call` 的语法 `{ serviceId, instance?, member, args }`、`$chord.service` 控制词汇（目录、订阅、退订）、订阅快照与更新、服务错误码以及复制状态的 Delta 编解码都属于 chord；Session 目录、管理结果、transcript、模型、插件这些值属于应用。",
           "The protocol owns only the envelope: types, ids, routes and the rule “payloads are strict JSON”. The `call` grammar `{ serviceId, instance?, member, args }`, the `$chord.service` control vocabulary (catalogue, subscribe, unsubscribe), subscription snapshots and updates, service error codes and the Delta codecs for replicated state belong to chord; the Session directory, management results, transcripts, models and plugins belong to the application."),
 points=[
  ("因此服务端可以把 Session 调用原样转发给 Session worker，而不需要加载那个服务的契约。", "So the server can forward a Session call to the Session worker as is, without loading that service's contract."),
  ("client 在服务适配边界用 chord 的解析器（`parseServiceCall`、`parseServiceCatalogue`、`createServiceStateDecoder`），server 用 `decodeServiceControlCall` 与 `createServiceStateEncoder`。", "At the service-adapter boundary the client uses chord's parsers (`parseServiceCall`, `parseServiceCatalogue`, `createServiceStateDecoder`), the server `decodeServiceControlCall` and `createServiceStateEncoder`."),
  ("不在公共协议里：服务器与 worker 的生命周期（实验性的本地协调器只是不透明的消息路由），以及对端认证。", "Not in the public protocol: server and worker lifecycle (the experimental local coordinator is just an opaque message router), and peer authentication."),
 ],
 how=[
  ("coding-agent：`createClientServiceTransport(client, () => client.attachment)` 把 Session 路由变成一个 chord 传输，再交给应用的类型化服务绑定。", "coding-agent: `createClientServiceTransport(client, () => client.attachment)` turns the Session route into a chord transport for the application's typed service bindings."),
  ("服务端收到订阅时为它建一个 `ServiceStateEncoder`，之后的更新都经它编码。", "On a subscription the server creates a `ServiceStateEncoder` for it, and later updates are encoded through it."),
  ("应用的 payload 语义校验在 chord 服务里完成，而不是在协议层。", "Semantic payload validation happens in the chord services, not in the protocol."),
 ],
 files=[
  ("packages/protocol/README.md", r"^Chord owns the payload semantics", "README.md", "分界的原文", "the boundary, as written"),
  (U + "protocol.ts", r"^const OpaqueJsonValueSchema", "OpaqueJsonValueSchema", "不透明 JSON", "opaque JSON"),
  (CLI + "client.ts", r"^export function createClientServiceTransport", "createClientServiceTransport()", "路由 → chord 传输", "route → chord transport"),
  (SRV + "server.ts", r"const control = decodeServiceControlCall\(call\);", "decodeServiceControlCall", "服务端识别控制调用", "the server recognises control calls"),
 ]),
]

EXT_POINTS = [
 ("maxFrameLength", ("每一端的帧上限（默认 16 MiB）；两端必须一致。", "Each peer's frame limit (16 MiB by default); both peers must match.")),
 ("encodeCbor / decodeCbor(…, CborOptions)", ("单独使用 CBOR 编解码，配置字节、容器与深度上限。", "Use the CBOR codec on its own, with byte, container and depth limits.")),
 ("FrameDecoder / encodeFrame", ("只用分帧，承载你自己的负载。", "Use only the framing, carrying your own payloads.")),
 ("parseClientMessage / parseServerMessage", ("校验从别的通道得到的消息对象。", "Validate message objects obtained through another channel.")),
 ("ByteTransport (client) · ServerListener (server)", ("任何保持字节顺序的流都能承载协议：Unix socket、WebSocket 中继、管道。", "Any order-preserving byte stream can carry the protocol: Unix sockets, a WebSocket relay, pipes.")),
]
XREF = [('client', ('协议的客户端一端：握手、请求、订阅', 'the client end: handshake, requests, subscriptions')),
        ('server', ('协议的服务端一端：路由到 Session', 'the server end: routing to Sessions')),
        ('chord', ('payload 的语义：服务调用、订阅与错误码', 'payload semantics: service calls, subscriptions and error codes')),
        ('coding-agent', ('experimental/ 下的 server 与 client 运行时', 'the server and client runtime under experimental/'))]
