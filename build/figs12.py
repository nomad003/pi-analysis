"""pi-protocol deep-dive diagrams (proto_*). Facts read from /workspace/pi-src/packages/protocol at build time."""
import re
from svgkit import Fig, maxw, pair
from figs import reg
from figkit import SRC, uml, codebox, bar, dot, hline, vline, chiprow, lines_of
from pkgsrc import Pkg, MiB, users_of

P_ = Pkg('packages/protocol/src/')
README = (SRC / 'packages/protocol/README.md').read_text()

def doc(text, *needles):
    for n in needles: assert n in text, n

def proto_version():
    return int(re.search(r'export const PROTOCOL_VERSION = (\d+) as const;', P_.src('protocol.ts')).group(1))

def union_members(name):
    blk = re.search(r'export const ' + name + r' = Type\.Union\(\[(.*?)\]\);', P_.src('protocol.ts'), re.S).group(1)
    return [x.strip() for x in blk.split(',') if x.strip()]

# ============================================================== proto_arch
@reg
def proto_arch():
    tot = P_.total()
    j = P_.pkg()
    assert list(j['exports']) == ['.'], j['exports']
    deps = j['dependencies']; assert set(deps) == {'@earendil-works/chord', 'typebox'}, deps
    users = dict(users_of('@earendil-works/pi-protocol'))
    assert set(users) >= {'client', 'server', 'coding-agent'}, users
    P_.has('index.ts', 'export * from "./cbor/index.ts";', 'export * from "./codec.ts";', 'export * from "./framing.ts";')
    f = Fig('proto_arch', 1120, 560, (f'pi-protocol：{tot:,} 行，三层——信封、编解码、分帧', f'pi-protocol: {tot:,} lines in three layers — envelopes, codec, framing'))
    E = f.edge
    f.group(16, 52, 660, 420, 'modes', 'packages/protocol/src', None, 'layers', gid='l')
    f.node('ix', 32, 92, 628, 44, 'modes', 'index.ts', ('唯一导入路径 "."：cbor、codec、framing 全部导出，protocol.ts 导出类型与 PROTOCOL_VERSION', 'the only import path ".": all of cbor, codec, framing; types and PROTOCOL_VERSION from protocol.ts'), None, tsize=10.8, ssize=9.0, tag=f'{P_.loc("index.ts")}')
    f.node('cd', 32, 168, 628, 50, 'modes', 'codec.ts', ('parse* · encodeClientMessage / encodeServerMessage · ClientMessageDecoder / ServerMessageDecoder · ProtocolValidationError', 'parse* · encodeClient/ServerMessage · Client/ServerMessageDecoder · ProtocolValidationError'), None, tsize=10.8, ssize=8.8, tag=f'{P_.loc("codec.ts")}', strong=True)
    f.node('pr', 32, 256, 200, 76, 'modes', 'protocol.ts', ('TypeBox 信封 schema', 'TypeBox envelope schemas'), None, tsize=10.8, ssize=9.0, sub2=('PROTOCOL_VERSION = %d' % proto_version(), 'PROTOCOL_VERSION = %d' % proto_version()), tag=f'{P_.loc("protocol.ts")}')
    f.node('fr', 246, 256, 200, 76, 'modes', 'framing.ts', ('u32 大端长度前缀', 'u32 big-endian prefix'), None, tsize=10.8, ssize=9.0, sub2=('FrameDecoder · 16 MiB', 'FrameDecoder · 16 MiB'), tag=f'{P_.loc("framing.ts")}')
    f.group(460, 248, 200, 212, 'coding', 'cbor/', None, None, dashed=True, gid='cb')
    for i, (p, d) in enumerate([('encoder.ts', ('encodeCbor：定长子集', 'encodeCbor: definite subset')), ('decoder.ts', ('decodeCbor：严格解码', 'decodeCbor: strict decode')), ('options.ts', ('上限默认值 · CborError', 'default limits · CborError'))]):
        f.node(f'c{i}', 472, 288 + i * 56, 176, 48, 'coding', p, d, None, tsize=10.4, ssize=8.8, tag=f'{P_.loc("cbor/" + p)}')
    E([(346, 136), (346, 168)], 'ix', 'cd', 'main', 'modes')
    E([(132, 218), (132, 256)], 'cd', 'pr', 'dep', 'modes', label=('校验', 'validate'), lpos=(132, 237), lmono=False, lsize=9.5)
    E([(346, 218), (346, 256)], 'cd', 'fr', 'dep', 'modes', label=('分帧', 'frame'), lpos=(346, 237), lmono=False, lsize=9.5)
    E([(560, 218), (560, 248)], 'cd', 'cb', 'dep', 'coding')
    MT = union_members('ClientMessageSchema'); ST = union_members('ServerMessageSchema')
    assert len(MT) == 3 and len(ST) == 5, (MT, ST)
    f.text(32, 360, ('客户端消息（%d）' % len(MT), 'Client messages (%d)' % len(MT)), 9.6, 650, cls='strongt', layer='label')
    chiprow(f, 32, 370, ['hello', 'request', 'cancel'], 'modes', size=9.4, h=20, gap=5)
    f.text(32, 412, ('服务端消息（%d）' % len(ST), 'Server messages (%d)' % len(ST)), 9.6, 650, cls='strongt', layer='label')
    chiprow(f, 32, 422, ['hello', 'hello_error', 'response', 'service_update', 'attachment'], 'infra', size=9.4, h=20, gap=5)
    # right: deps & users
    f.group(692, 52, 412, 420, 'infra', ('依赖与使用者', 'Dependencies and users'), None, 'hub', title_mono=False, gid='r')
    f.text(708, 100, ('依赖', 'Depends on'), 9.6, 650, cls='faint', layer='label', ls='.04em')
    f.node('d0', 708, 110, 380, 40, 'infra', f'@earendil-works/chord {deps["@earendil-works/chord"]}', ('JsonValue · isJsonValue：严格 JSON 边界', 'JsonValue · isJsonValue: the strict-JSON boundary'), None, tsize=10.2, ssize=8.8)
    f.node('d1', 708, 158, 380, 40, 'infra', f'typebox {deps["typebox"]}', ('Type.Object(additionalProperties: false) + Check', 'Type.Object(additionalProperties: false) + Check'), None, tsize=10.2, ssize=8.8)
    f.text(708, 226, ('被导入（src 中导入它的文件数）', 'Imported by (files in src)'), 9.6, 650, cls='faint', layer='label', ls='.04em')
    U = [('client', ('pi-client：Connection 握手、请求信封', 'pi-client: Connection handshake, request envelopes')),
         ('server', ('pi-server：ClientMessageDecoder、回应与更新', 'pi-server: ClientMessageDecoder, responses, updates')),
         ('coding-agent', ('experimental/：ServerId、DEFAULT_MAX_FRAME_LENGTH', 'experimental/: ServerId, DEFAULT_MAX_FRAME_LENGTH'))]
    for i, (k, d) in enumerate(U):
        f.node(f'u{i}', 708, 236 + i * 52, 380, 44, 'modes' if k != 'coding-agent' else 'coding', k, d, None, tsize=10.4, ssize=8.8, tag=f'{users[k]}')
    f.text(708, 410, ('coding-agent 只把三个包列为 devDependencies，', 'coding-agent lists all three packages only as'), 9.2, 450, cls='muted', layer='label')
    f.text(708, 426, ('供实验性的 server / client 运行时使用。', 'devDependencies, for its experimental server / client runtime.'), 9.2, 450, cls='muted', layer='label')
    doc(README, 'Default limits are 16 MiB per CBOR payload/frame, 1,000,000 array elements or map entries, and 64 nested item levels. The protocol is experimental and has no compatibility guarantees.')
    f.text(16, 498, ('README：默认上限 16 MiB / 帧、1,000,000 个数组元素或映射项、64 层嵌套；协议是实验性的，不保证兼容。', 'README: default limits 16 MiB per frame, 1,000,000 array elements or map entries, 64 nesting levels; experimental, no compatibility guarantees.'), 9.4, 450, cls='muted', layer='label')
    f.legend(24, 532, [('layer:modes', ('信封与编解码', 'envelopes & codec')), ('layer:coding', ('CBOR', 'CBOR')), ('layer:infra', ('依赖', 'dependencies')), ('main', ('入口', 'entry')), ('dep', ('使用', 'uses'))])
    f.note(1096, 532, ('标签 = 行数 / 文件数', 'tag = lines / files'), 10.5, anchor='end')
    return f

# ============================================================== proto_pipe : encode / decode path
@reg
def proto_pipe():
    c = P_.src('codec.ts')
    P_.has('codec.ts', 'if (!Check(ClientMessageSchema, value) || !isJsonValue(value)) {', 'return encodeFrame(encodeCbor(validated, { maxByteLength: maxFrameLength }));',
           'messages.push(this.parse(decodeCbor(frame, { maxByteLength: this.maxFrameLength })));', 'this.failed = true;', 'error.message.length <= 500')
    f = Fig('proto_pipe', 1120, 580, ('一条消息的往返：校验 → CBOR → 分帧 → 字节 → 拆帧 → 解码 → 校验', 'One message: validate → CBOR → frame → bytes → split → decode → validate'))
    E = f.edge
    f.text(16, 72, ('发送方（encodeClientMessage / encodeServerMessage）', 'Sender (encodeClientMessage / encodeServerMessage)'), 10.5, 650, cls='strongt', layer='label')
    S = [('ClientMessage', ('普通 JS 对象', 'a plain JS object'), 'braces'),
         ('parseClientMessage', ('TypeBox Check + isJsonValue', 'TypeBox Check + isJsonValue'), 'shield'),
         ('encodeCbor', ('上限 = maxFrameLength', 'limit = maxFrameLength'), 'code'),
         ('encodeFrame', ('前缀 u32 大端长度', 'prefix a u32 big-endian length'), 'stack'),
         ('Uint8Array', ('一整帧，交给传输', 'one whole frame, to the transport'), 'box')]
    for i, (t, d, ic) in enumerate(S):
        f.node(f'e{i}', 16 + i * 222, 88, 200, 60, 'modes', t, d, ic, tsize=10.6, ssize=8.8, strong=(i == 1))
        if i: E([(16 + i * 222 - 22, 118), (16 + i * 222, 118)], f'e{i-1}', f'e{i}', 'main', 'modes')
    f.node('tr', 16, 184, 1088, 40, 'infra', ('ByteTransport / ByteConnection：可以任意切分、合并字节，但必须保持顺序', 'ByteTransport / ByteConnection: may split and coalesce bytes arbitrarily, but must preserve their order'), None, mono=False, tsize=10.4, align='center')
    E([(1004, 148), (1004, 184)], 'e4', 'tr', 'main', 'infra')
    f.text(16, 262, ('接收方（ClientMessageDecoder / ServerMessageDecoder）', 'Receiver (ClientMessageDecoder / ServerMessageDecoder)'), 10.5, 650, cls='strongt', layer='label')
    R = [('chunk, chunk, …', ('任意大小的片段', 'fragments of any size'), 'stream'),
         ('FrameDecoder.push', ('凑齐 4 字节头 → 负载', '4-byte header → payload'), 'filter'),
         ('decodeCbor', ('恰好一个定长 CBOR 项', 'exactly one definite-length item'), 'code'),
         ('parseServerMessage', ('同一套 schema 再校验一次', 'the same schemas, checked again'), 'shield'),
         ('ServerMessage[]', ('push() 返回 0..n 条消息', 'push() returns 0..n messages'), 'queue')]
    for i, (t, d, ic) in enumerate(R):
        f.node(f'd{i}', 16 + i * 222, 278, 200, 60, 'modes', t, d, ic, tsize=10.6, ssize=8.8, strong=(i == 3))
        if i: E([(16 + i * 222 - 22, 308), (16 + i * 222, 308)], f'd{i-1}', f'd{i}', 'main', 'modes')
    E([(116, 224), (116, 278)], 'tr', 'd0', 'main', 'infra')
    f.group(16, 370, 1088, 156, 'err', ('任何一步失败都是 ProtocolValidationError', 'Any failure along the way is a ProtocolValidationError'), 'codec.ts', 'x', title_mono=False, gid='er')
    L = [(('schema 不符或含非 JSON 值', 'Schema mismatch or a non-JSON value'), ('未知字段、Uint8Array、NaN、undefined、原型、环', 'unknown fields, Uint8Array, NaN, undefined, prototypes, cycles')),
         (('CBOR 或分帧出错', 'Malformed CBOR or framing'), ('CborError / FrameError 被包装，消息截断到 500 字符', 'CborError / FrameError are wrapped, messages cut to 500 chars')),
         (('解码器一旦失败', 'Once a decoder fails'), ('之后的 push() / end() 都直接抛错', 'every later push() / end() throws')),
         (('end() 时仍有半帧', 'end() with a partial frame'), ('"Truncated frame at end of stream"', '"Truncated frame at end of stream"'))]
    for i, (a, b) in enumerate(L):
        cx = 32 + (i % 2) * 540; y = 424 + (i // 2) * 46
        f.text(cx, y, a, 10, 650, cls='strongt', layer='label')
        f.text(cx, y + 17, b, 9.2, 450, cls='muted', layer='label')
    f.legend(24, 554, [('layer:modes', ('协议代码', 'protocol code')), ('layer:infra', ('传输', 'transport')), ('main', ('数据流', 'data flow')), ('layer:err', ('失败', 'failure'))])
    return f

# ============================================================== proto_messages : the 8 envelopes
@reg
def proto_messages():
    s = P_.src('protocol.ts')
    v = proto_version()
    for needle in ['type: Type.Literal("hello"),\n\tversion: Type.Integer({ minimum: 0 }),', 'version: Type.Literal(PROTOCOL_VERSION),', 'type: Type.Literal("hello_error"),',
                   'type: Type.Literal("service_update"),', 'subscriptionId: IdSchema,', 'attachment: Type.Union([SessionTargetSchema, Type.Null()]),',
                   'result: Type.Optional(OpaqueJsonValueSchema),', 'Type.Object(properties, { additionalProperties: false })', 'const IdSchema = Type.String({ minLength: 1 });']:
        assert needle in s, needle
    f = Fig('proto_messages', 1120, 600, (f'协议版本 {v} 的 8 种信封：3 种客户端消息、5 种服务端消息', f'Protocol version {v}: 8 envelopes — 3 client messages, 5 server messages'))
    f.group(16, 52, 340, 440, 'modes', 'ClientMessage', ('客户端 → 服务端', 'client → server'), 'monitor', gid='c')
    uml(f, 'ch', 32, 92, 308, 'modes', 'ClientHello', '«first»', [['type: "hello"', 'version: integer ≥ 0']])
    uml(f, 'rq', 32, 192, 308, 'modes', 'RequestEnvelope', None, [['type: "request"', 'id: string (non-empty)', 'target: RpcTarget', 'call: JSON (opaque)']])
    uml(f, 'cn', 32, 326, 308, 'modes', 'CancelEnvelope', None, [['type: "cancel"', 'id: string', 'target: RpcTarget']])
    f.group(372, 52, 732, 440, 'infra', 'ServerMessage', ('服务端 → 客户端', 'server → client'), 'cpu', gid='s')
    uml(f, 'sh', 388, 92, 340, 'infra', 'ServerHello', '«first»', [['type: "hello"', f'version: {v} (literal)', 'serverId: ServerId']])
    uml(f, 'se', 388, 210, 340, 'infra', 'ServerHelloError', '«terminal»', [['type: "hello_error"', 'error: ProtocolError']])
    uml(f, 'rs', 388, 311, 340, 'infra', 'ResponseEnvelope', None, [['type: "response"', 'id · ok: true', 'result?: JSON (opaque)'], ['type: "response"', 'id · ok: false', 'error: ProtocolError']])
    uml(f, 'su', 748, 92, 340, 'infra', 'ServiceEventEnvelope', None, [['type: "service_update"', 'subscriptionId: string', 'update: JSON (opaque)']])
    uml(f, 'at', 748, 210, 340, 'infra', 'AttachmentEnvelope', '«out of band»', [['type: "attachment"', 'attachment: SessionTarget | null']])
    uml(f, 'pe', 748, 311, 340, 'err', 'ProtocolError', None, [['code: string (non-empty)', 'message: string']])
    f.text(748, 430, ('错误码对协议是不透明的：', 'Codes are opaque to the protocol:'), 9.2, 450, cls='muted', layer='label')
    f.text(748, 446, ('version、invalid_request、cancelled、wrong_server …', 'version, invalid_request, cancelled, wrong_server …'), 9.2, 500, True, cls='muted', layer='label')
    f.text(748, 462, ('由 server 与 chord 定义。', 'are defined by the server and chord.'), 9.2, 450, cls='muted', layer='label')
    f.text(16, 520, ('所有信封都是 additionalProperties: false 的 StrictObject；id 是非空字符串；call、result、update 只校验为严格 JSON（Type.Unknown + isJsonValue）。', 'Every envelope is a StrictObject with additionalProperties: false; ids are non-empty strings; call, result and update are only checked to be strict JSON (Type.Unknown + isJsonValue).'), 9.4, 450, cls='muted', layer='label')
    f.text(16, 540, ('response 的 ok: true 可以没有 result 字段（void 回应）。', 'A response with ok: true may omit result (a void response).'), 9.4, 450, cls='muted', layer='label')
    f.legend(24, 576, [('layer:modes', ('客户端发送', 'sent by the client')), ('layer:infra', ('服务端发送', 'sent by the server')), ('layer:err', ('错误', 'error'))])
    return f

# ============================================================== proto_targets : routing fences
@reg
def proto_targets():
    s = P_.src('protocol.ts')
    m = re.search(r'const ServerIdSchema = Type\.String\(\{\n\tpattern: "([^"]+)",', s); rx = m.group(1)
    assert rx == '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', rx
    P_.has('protocol.ts', 'const RpcTargetSchema = Type.Union([ServerTargetSchema, SessionTargetSchema]);', 'sessionId: IdSchema,\n\tattachmentId: IdSchema,')
    (SRC / 'packages/server/src/session-router.ts').read_text().index('id: randomUUID(),')
    doc(README, 'The combined route fences calls to one logical server, durable Session, and live presentation attachment.', 'Management `attach()` and `detach()` return no routing identifiers')
    f = Fig('proto_targets', 1120, 560, ('RpcTarget：把一次调用围在一台逻辑服务器、一个 Session、一个实时附着里', 'RpcTarget: fencing a call to one logical server, one Session, one live attachment'))
    f.group(16, 52, 560, 420, 'modes', ('逻辑服务器', 'Logical server'), 'serverId', 'cpu', gid='g1')
    f.text(32, 102, ('规范的小写 UUIDv4；是逻辑身份，不是 socket 地址', 'a canonical lowercase UUIDv4; a logical identity, not a socket address'), 9.2, 450, cls='muted', layer='label')
    f.node('sv', 32, 114, 260, 44, 'modes', '{ serverId }', ('服务器级调用：目录、管理', 'server-wide calls: directory, management'), None, tsize=10.6, ssize=8.8)
    f.group(40, 176, 520, 280, 'ext', ('持久 Session', 'Durable Session'), 'sessionId', 'db', gid='g2')
    f.text(56, 226, ('Session 与它的 Harness 留在 Session worker 进程里', 'the Session and its Harness stay in the Session worker process'), 9.2, 450, cls='muted', layer='label')
    f.group(64, 244, 480, 196, 'coding', ('实时附着', 'Live attachment'), 'attachmentId', 'plug', gid='g3')
    f.text(80, 294, ('每次成功 attach 由服务器生成（randomUUID）', 'generated by the server on every successful attach (randomUUID)'), 9.2, 450, cls='muted', layer='label')
    f.node('ss', 80, 310, 448, 48, 'coding', '{ serverId, sessionId, attachmentId }', ('Session 调用：每个请求都带完整路由', 'Session calls: every request carries the full route'), None, tsize=10.6, ssize=8.8, strong=True)
    f.text(80, 386, ('一个 Session 可以有多个 presentation 附着；', 'A Session may have several presentation attachments;'), 9.2, 450, cls='muted', layer='label')
    f.text(80, 402, ('同一连接重复 attach 同一 Session 是幂等的。', 'repeating attach for the same Session on one connection is idempotent.'), 9.2, 450, cls='muted', layer='label')
    f.text(80, 424, rx, 8.6, 500, True, cls='faint', layer='label')
    # right side
    f.group(592, 52, 512, 172, 'infra', ('路由怎样到达客户端', 'How the route reaches the client'), None, 'msg', title_mono=False, gid='rt')
    codebox(f, 608, 92, 480, [(0, ('// 管理调用的结果里没有任何路由 id', '// management results carry no route ids'), 'muted'),
                              (0, 'await sessions.attach(sessionId)', 'strongt'),
                              (0, ('// 服务器装好路由后，带外发送：', '// once installed, the server sends out of band:'), 'muted'),
                              (0, '{ type: "attachment",', ''),
                              (1, 'attachment: { serverId, sessionId, attachmentId } }', ''),
                              (0, ('// detach / 断开 / 失效 → attachment: null', '// detach / disconnect / invalidation → attachment: null'), 'muted')], None, size=9.6, lh=15)
    f.group(592, 240, 512, 232, 'err', ('服务器拒绝的路由', 'Routes the server rejects'), None, 'shield', title_mono=False, gid='rj')
    RJ = [('wrong_server', ('target.serverId 不是这台服务器（在访问仓库之前）', 'target.serverId is another server (before any repository access)')),
          ('session_not_attached', ('本连接没有附着该 Session，或 attachmentId 已过期', 'this connection holds no such attachment, or the id is stale')),
          ('server_draining', ('服务器正在关闭', 'the server is shutting down')),
          ('invalid_request', ('信封本身不合法', 'the envelope itself is invalid'))]
    for i, (c_, d) in enumerate(RJ):
        y = 290 + i * 44
        f.chip(608, y, c_, 'err', size=9.6, h=20)
        f.text(788, y + 14, d, 9.0, 450, cls='muted', layer='label')
    f.text(16, 500, ('切换或重新附着之后，带旧 attachmentId 的延迟帧会被拒绝：路由同时防止跨服务器、跨 Session 和过期的调用。', 'After switching or reattaching, delayed frames with an old attachmentId are rejected: the route prevents cross-server, cross-Session and stale calls alike.'), 9.4, 450, cls='muted', layer='label')
    f.legend(24, 536, [('layer:modes', ('服务器级', 'server-wide')), ('layer:ext', ('Session', 'Session')), ('layer:coding', ('附着', 'attachment')), ('layer:err', ('拒绝', 'rejected'))])
    return f

# ============================================================== proto_handshake : one connection as a sequence
@reg
def proto_handshake():
    v = proto_version()
    S_ = Pkg('packages/server/src/'); C_ = Pkg('packages/client/src/')
    assert S_.num('server.ts', 'DEFAULT_HANDSHAKE_TIMEOUT_MS') == 5000
    S_.has('server.ts', 'code: "version",', 'message: "The first client message must be hello",', 'message: "hello may only be sent as the first message",', '? { code: "cancelled", message: "RPC request cancelled" }', 'if (active !== undefined && sameTarget(active.target, envelope.target)) {')
    C_.has('connection.ts', 'does not match', 'Received server data before the client hello was sent', 'Unexpected handshake message')
    C_.has('client.ts', 'const id = `request-${++this.#requestSequence}`;')
    (SRC / 'packages/server/src/session-router.ts').read_text().index('await this.options.publishAttachment(\n\t\t\tclient,\n\t\t\t{ serverId: this.options.serverId, sessionId, attachmentId: attachment.id },')
    f = Fig('proto_handshake', 1120, 640, ('一条连接上的消息顺序：握手、请求、带外附着、订阅、取消', 'Message order on one connection: handshake, requests, out-of-band attachment, subscriptions, cancellation'))
    E = f.edge
    CX, SX = 330, 830
    f.node('c', CX - 100, 56, 200, 40, 'modes', 'Client', ('pi-client', 'pi-client'), 'monitor', tsize=11, ssize=8.8, strong=True)
    f.node('s', SX - 100, 56, 200, 40, 'infra', 'Server', ('pi-server', 'pi-server'), 'cpu', tsize=11, ssize=8.8, strong=True)
    vline(f, CX, 96, 572); vline(f, SX, 96, 572)
    M = [(1, 128, f'hello {{ version: {v} }}', 'main'),
         (0, 164, f'hello {{ version: {v}, serverId }}', 'event'),
         (1, 222, 'request { id: "request-1", target, call: attach }', 'main'),
         (0, 258, 'attachment { attachment: { serverId, sessionId, attachmentId } }', 'event'),
         (0, 294, 'response { id: "request-1", ok: true }', 'event'),
         (1, 352, 'request { id: "request-2", call: subscribe }', 'main'),
         (0, 388, 'response { id: "request-2", ok: true, result: snapshot }', 'event'),
         (0, 424, 'service_update { subscriptionId, update }', 'event'),
         (1, 482, 'cancel { id: "request-3", target }', 'main'),
         (0, 518, 'response { id: "request-3", ok: false, error: { code: "cancelled" } }', 'err')]
    for up, y, lab, kind in M:
        pts = [(CX, y), (SX, y)] if up else [(SX, y), (CX, y)]
        E(pts, 'c' if up else 's', 's' if up else 'c', kind, 'modes' if up else 'infra', label=lab, lsize=9.4)
    PH = [(128, ('① 握手', '① Handshake'), ('第一帧必须是 hello', 'the first frame must be hello')),
          (222, ('② 管理调用', '② A management call'), ('attach 的结果里没有路由 id', 'attach returns no route ids')),
          (352, ('③ 订阅', '③ A subscription'), ('先快照，再更新', 'snapshot first, then updates')),
          (482, ('④ 取消', '④ Cancellation'), ('同一 id、同一 target', 'same id, same target'))]
    for y, a, b in PH:
        f.text(16, y - 2, a, 10.2, 700, cls='strongt', layer='label')
        f.text(16, y + 14, b, 9.0, 450, cls='muted', layer='label')
    R = [(128, ('服务端 5 s 内没完成握手', 'No handshake within 5 s'), ('→ hello_error，关闭连接', '→ hello_error, close')),
         (164, ('版本不符 → hello_error { version }', 'Wrong version → hello_error { version }'), ('serverId 不符 → 客户端断开', 'serverId mismatch → client drops')),
         (258, ('带外：在 attach 的回应之前', 'Out of band: before the attach'), ('送达，路由已经装好', 'response, route already installed')),
         (424, ('快照之前产生的更新', 'Updates produced before the'), ('在服务端排队，回应之后才发', 'snapshot queue until after it')),
         (518, ('请求在服务端被 abort', 'The request is aborted on the'), ('客户端早已在本地 reject', 'server; the client rejected locally'))]
    for y, a, b in R:
        f.text(SX + 18, y - 2, a, 9.2, 600, cls='strongt', layer='label')
        f.text(SX + 18, y + 13, b, 9.0, 450, cls='muted', layer='label')
    f.text(16, 600, ('握手之后再发 hello、或在客户端发出 hello 之前收到服务端数据，都是协议错误：连接被关闭。', 'A second hello after the handshake, or server data before the client\'s hello was sent, is a protocol error: the connection closes.'), 9.4, 450, cls='muted', layer='label')
    f.legend(24, 626, [('main', ('客户端 → 服务端', 'client → server')), ('event', ('服务端 → 客户端', 'server → client')), ('err', ('错误回应', 'error response'))])
    return f

# ============================================================== proto_frame : the length-prefixed framing
@reg
def proto_frame():
    assert P_.num('framing.ts', 'FRAME_HEADER_LENGTH') == 4 and P_.num('framing.ts', 'PAYLOAD_BLOCK_SIZE') == 64 * 1024
    mf = P_.num('framing.ts', 'DEFAULT_MAX_FRAME_LENGTH'); assert mf == 16 * 1024 * 1024
    P_.has('framing.ts', 'type DecoderState = "open" | "ended" | "failed";', 'this.fail("Truncated frame at end of stream");', 'if (frameLength === 0) {', 'Frame decoder has ended', 'Frame decoder has failed',
           'if (frameLength > this.maxFrameLength) {', 'if (this.payloadBlocks.length === 1) {')
    f = Fig('proto_frame', 1120, 580, (f'分帧：u32 大端长度 + 一个 CBOR 项；默认上限 {MiB(mf)}', f'Framing: a u32 big-endian length + one CBOR item; {MiB(mf)} by default'))
    E = f.edge
    f.group(16, 52, 1088, 150, 'coding', ('一段字节流（chunk 边界可以落在任何地方）', 'A byte stream (chunk boundaries may fall anywhere)'), None, 'stream', title_mono=False, gid='bs')
    B = [(32, 130, '00 00 00 15', False), (166, 200, ('CBOR · 21 字节', 'CBOR · 21 bytes'), False), (370, 130, '00 00 00 00', False), (504, 130, '00 02 00 00', False), (638, 450, ('负载 · 131,072 字节 …', 'payload · 131,072 bytes …'), True)]
    for x, w, t, d in B:
        bar(f, x, 118, w, 'coding', t, h=26, size=9.6, mono=isinstance(t, str), dashed=d)
    for x in (110, 300, 706):
        f.raw(f'<line class="rule-d" x1="{x}" y1="100" x2="{x}" y2="152" style="stroke-dasharray:3 3"/>', 'label')
    for x, t in [(36, 'chunk 1'), (116, 'chunk 2'), (306, 'chunk 3'), (712, 'chunk 4 …')]:
        f.text(x, 112, t, 8.8, 600, True, cls='faint', layer='label')
    for x, t in [(32, ('长度 = 21', 'length = 21')), (166, ('{ type: "hello", version: 8 }', '{ type: "hello", version: 8 }')), (370, ('空帧 → Uint8Array(0)', 'empty frame → Uint8Array(0)')), (504, ('长度 = 131,072', 'length = 131,072')), (638, ('= 2 个 64 KiB 块，收满后拼接', '= two 64 KiB blocks, joined when complete'))]:
        f.text(x, 166, t, 9.0, 450, cls='muted', layer='label')
    f.text(32, 188, ('编码：encodeFrame(payload) 只加 4 字节头；负载超过 0xffffffff 字节 → RangeError。', 'Encoding: encodeFrame(payload) only adds the 4-byte header; a payload above 0xffffffff bytes → RangeError.'), 9.0, 450, cls='faint', layer='label')
    # state machine
    f.group(16, 218, 520, 310, 'modes', ('FrameDecoder 的状态', 'FrameDecoder states'), 'framing.ts', 'loop', title_mono=False, gid='sm')
    f.node('op', 40, 344, 150, 44, 'modes', 'open', None, None, kind='pill', align='center', tsize=12, strong=True)
    f.node('en', 330, 270, 180, 44, 'ext', 'ended', None, None, kind='pill', align='center', tsize=12)
    f.node('fa', 330, 420, 180, 44, 'err', 'failed', None, None, kind='pill', align='center', tsize=12)
    E([(115, 344), (115, 292), (330, 292)], 'op', 'en', 'main', 'ext', label=('end()：没有半帧', 'end(): no partial frame'), lpos=(222, 292), lmono=False, lsize=9.2)
    E([(115, 388), (115, 442), (330, 442)], 'op', 'fa', 'err', 'err', label=('超限 · 截断', 'too long · truncated'), lpos=(222, 442), lmono=False, lsize=9.2, lcls='err')
    f.text(206, 362, ('push(chunk) → Uint8Array[]', 'push(chunk) → Uint8Array[]'), 9.2, 600, True, cls='strongt', layer='label')
    f.text(206, 378, ('留在 open', 'stays open'), 9.0, 450, cls='muted', layer='label')
    f.text(330, 336, ('之后的 push / end → FrameError', 'later push / end → FrameError'), 9.0, 450, cls='muted', layer='label')
    f.text(330, 486, ('清空缓冲；之后一律 FrameError', 'buffers cleared; FrameError from then on'), 9.0, 450, cls='muted', layer='label')
    f.text(40, 512, ('Client/ServerMessageDecoder 把它包装成 ProtocolValidationError。', 'Client/ServerMessageDecoder wrap it as ProtocolValidationError.'), 9.0, 450, cls='faint', layer='label')
    # steps
    f.group(552, 218, 552, 310, 'infra', ('push(chunk) 做的事', 'What push(chunk) does'), None, 'filter', title_mono=False, gid='st')
    ST = [(('凑齐 4 字节头，可以跨多个 chunk', 'Fill the 4-byte header, across chunks if needed'), None),
          (('长度 > maxFrameLength → 立即失败', 'Length > maxFrameLength → fail at once'), ('不等负载到达', 'without waiting for the payload')),
          (('长度 0 → 立刻产出一个空帧', 'Length 0 → emit an empty frame now'), None),
          (('负载按 64 KiB 的块收集', 'Collect the payload in 64 KiB blocks'), ('PAYLOAD_BLOCK_SIZE', 'PAYLOAD_BLOCK_SIZE')),
          (('收满：单块直接返回，否则拼成一个数组', 'Complete: one block as is, else joined'), None),
          (('总是复制字节，不引用输入 chunk', 'Bytes are always copied, never aliased'), None)]
    for i, (a, b) in enumerate(ST):
        y = 266 + i * 42
        f.step(str(i + 1), 580, y, 'infra')
        f.text(600, y + 4, a, 9.8, 600, cls='strongt', layer='label')
        if b: f.text(600, y + 20, b, 9.0, 450, isinstance(b[0], str) and b[0].isupper() and '_' in b[0], cls='muted', layer='label')
    f.legend(24, 556, [('layer:coding', ('帧', 'frames')), ('layer:modes', ('解码器', 'decoder')), ('main', ('正常结束', 'clean end')), ('err', ('失败', 'failure'))])
    return f

# ============================================================== proto_cbor : the strict CBOR subset
def _cbor(v):
    def arg(mt, n):
        if n < 24: return bytes([mt << 5 | n])
        if n <= 0xff: return bytes([mt << 5 | 24, n])
        if n <= 0xffff: return bytes([mt << 5 | 25]) + n.to_bytes(2, 'big')
        return bytes([mt << 5 | 26]) + n.to_bytes(4, 'big')
    if isinstance(v, bool): return b'\xf5' if v else b'\xf4'
    if isinstance(v, int): return arg(0, v) if v >= 0 else arg(1, -1 - v)
    if isinstance(v, str): b = v.encode(); return arg(3, len(b)) + b
    if isinstance(v, dict): return arg(5, len(v)) + b''.join(_cbor(k) + _cbor(x) for k, x in v.items())
    raise TypeError(v)

@reg
def proto_cbor():
    O = {n: P_.num('cbor/options.ts', n) for n in ['DEFAULT_MAX_CBOR_BYTE_LENGTH', 'DEFAULT_MAX_CBOR_CONTAINER_LENGTH', 'DEFAULT_MAX_CBOR_DEPTH', 'MAX_CONFIGURED_DEPTH']}
    assert O == {'DEFAULT_MAX_CBOR_BYTE_LENGTH': 16 * 1024 * 1024, 'DEFAULT_MAX_CBOR_CONTAINER_LENGTH': 1_000_000, 'DEFAULT_MAX_CBOR_DEPTH': 64, 'MAX_CONFIGURED_DEPTH': 512}, O
    P_.has('cbor/decoder.ts', 'throw new CborError("CBOR tags are not supported");', 'Indefinite-length CBOR ${kind}s are not supported', 'throw new CborError("CBOR map keys must be strings");', 'throw new CborError("CBOR map contains a duplicate key");',
           'throw new CborError("CBOR payload contains trailing data");', 'Unsupported CBOR simple value or floating-point width', 'case 20:\n\t\t\t\treturn false;', 'case 27: {', 'new TextDecoder' if False else 'textDecoder.decode(bytes)')
    P_.has('cbor/encoder.ts', 'if (Number.isInteger(value) && !Object.is(value, -0)) {', 'writer.writeFloat64(value);', 'CBOR values must not contain cycles', 'CBOR arrays must not contain holes or undefined values', 'if (entryValue !== undefined) entries.push([key, entryValue]);', 'CBOR text strings must contain valid Unicode scalar values')
    P_.has('cbor/options.ts', 'new TextDecoder("utf-8", { fatal: true, ignoreBOM: true })')
    f = Fig('proto_cbor', 1120, 640, ('严格的 RFC 8949 子集：只有定长项，没有 tag', 'A strict RFC 8949 subset: definite-length items only, no tags'))
    f.group(16, 52, 700, 428, 'coding', ('8 种主类型（major type）', 'The 8 major types'), 'cbor/decoder.ts · encoder.ts', 'braces', title_mono=False, gid='mt')
    ROWS = [('0', ('无符号整数', 'unsigned int'), ('number（安全整数）', 'number (safe integer)'), True),
            ('1', ('负整数', 'negative int'), ('number，-1 − n 必须安全', 'number; -1 − n must be safe'), True),
            ('2', ('字节串', 'byte string'), ('Uint8Array；信封层再拒绝（非 JSON）', 'Uint8Array; refused later by the envelope check'), True),
            ('3', ('文本串', 'text string'), ('fatal UTF-8；保留开头的 BOM', 'fatal UTF-8; a leading BOM is kept'), True),
            ('4', ('数组', 'array'), ('不能有空洞或 undefined', 'no holes or undefined'), True),
            ('5', ('映射', 'map'), ('键必须是字符串且不重复；__proto__ 是普通数据', 'string keys, no duplicates; __proto__ is data'), True),
            ('6', ('tag', 'tag'), ('一律拒绝', 'always rejected'), False),
            ('7', ('简单值 / 浮点', 'simple / float'), ('只有 false、true、null 与有限的 float64', 'only false, true, null and finite float64'), True),
            ('31', ('不定长（附加信息 31）', 'indefinite length (info 31)'), ('一律拒绝，break 也是', 'always rejected, break too'), False)]
    for i, (n, nm, js, ok) in enumerate(ROWS):
        y = 96 + i * 42
        if i: hline(f, 32, 700, y - 8)
        f.chip(32, y, n, 'coding' if ok else 'err', size=10, h=22)
        f.text(76, y + 15, nm, 10, 650, cls='strongt', layer='label')
        f.text(250, y + 15, js, 9.4, 450, cls='muted', layer='label')
        f.chip(626, y, '✓' if ok else '✕', 'ext' if ok else 'err', size=10, h=22)
    f.group(732, 52, 372, 428, 'infra', ('CborOptions 与规则', 'CborOptions and rules'), 'options.ts', 'gear', title_mono=False, gid='lm')
    LM = [('maxByteLength', MiB(O['DEFAULT_MAX_CBOR_BYTE_LENGTH']), ('输入 / 输出与单个串的长度', 'input / output and any one string')),
          ('maxContainerLength', f'{O["DEFAULT_MAX_CBOR_CONTAINER_LENGTH"]:,}', ('数组元素或映射项', 'array elements or map entries')),
          ('maxDepth', f'{O["DEFAULT_MAX_CBOR_DEPTH"]} (≤ {O["MAX_CONFIGURED_DEPTH"]})', ('嵌套层数', 'nesting levels'))]
    for i, (k, v, d) in enumerate(LM):
        f.node(f'l{i}', 748, 92 + i * 52, 340, 44, 'infra', k, d, None, tsize=10.4, ssize=8.8, tag=v)
    f.text(748, 268, ('编码器', 'Encoder'), 9.8, 700, cls='strongt', layer='label')
    EN = [('整数用最短的参数；-0 与小数写成 float64', 'shortest argument for integers; -0 and fractions as float64'),
          ('值为 undefined 的属性被省略，假值保留', 'undefined properties are omitted, falsy values kept'),
          ('环、符号键、非普通对象 → CborError', 'cycles, symbol keys, non-plain objects → CborError'),
          ('字符串必须是合法的 Unicode 标量序列', 'strings must be valid Unicode scalar values')]
    for i, t in enumerate(EN):
        f.text(748, 288 + i * 18, t, 9.0, 450, cls='muted', layer='label')
    f.text(748, 380, ('解码器', 'Decoder'), 9.8, 700, cls='strongt', layer='label')
    DE = [('先检查声明的长度与深度，再遍历', 'checks declared lengths and depth before traversing'),
          ('恰好一个项：尾随字节 → 错误', 'exactly one item: trailing bytes → error'),
          ('整数超出安全范围 → 错误', 'integers outside the safe range → error')]
    for i, t in enumerate(DE):
        f.text(748, 400 + i * 18, t, 9.0, 450, cls='muted', layer='label')
    # worked example
    hello = {'type': 'hello', 'version': proto_version()}
    cb = _cbor(hello); fr = len(cb).to_bytes(4, 'big') + cb
    hx = ' '.join(f'{b:02x}' for b in fr)
    f.group(16, 496, 1088, 104, 'modes', ('例子：encodeClientMessage({ type: "hello", version: %d })' % proto_version(), 'Example: encodeClientMessage({ type: "hello", version: %d })' % proto_version()), None, 'code', title_mono=False, gid='ex')
    f.text(32, 548, hx, 10.2, 600, True, cls='strongt', layer='label')
    f.text(32, 572, (f'{len(fr)} 字节：4 字节长度（{len(cb)}）· a2 = 2 项映射 · 64 "type" · 65 "hello" · 67 "version" · {cb[-1]:02x} = {proto_version()}', f'{len(fr)} bytes: 4-byte length ({len(cb)}) · a2 = map of 2 · 64 "type" · 65 "hello" · 67 "version" · {cb[-1]:02x} = {proto_version()}'), 9.2, 450, cls='muted', layer='label')
    f.legend(24, 620, [('layer:coding', ('支持', 'supported')), ('layer:err', ('拒绝', 'rejected')), ('layer:infra', ('上限', 'limits'))])
    return f

# ============================================================== proto_chord : who owns which part of a message
@reg
def proto_chord():
    C_ = Pkg('packages/client/src/'); S_ = Pkg('packages/server/src/')
    CL = ['parseServiceCall', 'parseServiceCatalogue', 'createServiceStateDecoder', 'parseWireServiceSubscriptionSnapshot', 'createServiceSubscribeCall']
    SV = ['parseServiceCall', 'decodeServiceControlCall', 'parseServiceSubscriptionSnapshot', 'createServiceStateEncoder', 'RemoteServiceError']
    imp = lambda s: re.search(r'import \{(.*?)\} from "@earendil-works/chord";', s, re.S).group(1)
    for n in CL: assert re.search(r'\b' + n + r'\b', imp(C_.src('client.ts'))), n
    for n in SV: assert re.search(r'\b' + n + r'\b', imp(S_.src('server.ts'))), n
    assert 'createClientServiceTransport(client, () => client.attachment)' in (SRC / 'packages/coding-agent/src/experimental/services/connection.ts').read_text()
    doc(README, '`{ serviceId, instance?, member, args }` calls, the `$chord.service` control vocabulary', '`pi-protocol` validates that each opaque payload is strict JSON but does not validate or export its Chord grammar.',
        'Server and worker lifecycle is intentionally outside this public protocol.', 'Peer authentication and authenticated service contexts are not implemented by the experimental transport.')
    f = Fig('proto_chord', 1120, 560, ('谁负责消息的哪一层：信封归 protocol，调用归 chord，数据归应用', 'Who owns which layer: the envelope is protocol\'s, the call is chord\'s, the data is the application\'s'))
    E = f.edge
    f.group(16, 52, 620, 420, 'modes', ('pi-protocol 校验的信封', 'The envelope pi-protocol validates'), 'RequestEnvelope', 'shield', title_mono=False, gid='a')
    chiprow(f, 32, 100, ['type: "request"', 'id', 'target: RpcTarget', 'call: …'], 'modes', size=9.8, h=22, gap=6)
    f.group(40, 140, 572, 320, 'ext', ('chord 解释的 call', 'The call chord interprets'), 'ServiceCall', 'hub', title_mono=False, gid='b')
    chiprow(f, 56, 186, ['serviceId', 'instance?', 'member', 'args'], 'ext', size=9.8, h=22, gap=6)
    f.text(56, 232, ('或者一个 $chord.service 控制调用：', 'or a $chord.service control call:'), 9.4, 600, cls='strongt', layer='label')
    chiprow(f, 56, 242, ['catalogue', 'subscribe', 'unsubscribe'], 'ext', size=9.4, h=20, gap=6)
    f.text(56, 284, ('回应里的服务目录、订阅快照与更新、服务错误码、复制状态的 Delta 路径编解码都属于 chord。', 'Catalogues, subscription snapshots and updates, service error codes and Delta path codecs belong to chord.'), 8.8, 450, cls='muted', layer='label')
    f.group(64, 300, 524, 146, 'coding', ('应用自己的数据', 'Application data'), 'args · result · update', 'db', title_mono=False, gid='c')
    chiprow(f, 80, 346, [('Session 目录状态', 'Session directory state'), ('管理结果', 'management results'), ('transcript', 'transcripts')], 'coding', size=9.4, h=22, gap=6)
    chiprow(f, 80, 376, [('模型', 'models'), ('插件', 'plugins'), ('其他服务值', 'other service values')], 'coding', size=9.4, h=22, gap=6)
    f.text(80, 420, ('对 protocol 与 server 都是不透明的 JSON；', 'Opaque JSON to both the protocol and the server;'), 9.0, 450, cls='muted', layer='label')
    f.text(80, 436, ('由 chord 绑定与应用在服务边界上校验。', 'validated by chord bindings and the app at the service boundary.'), 9.0, 450, cls='muted', layer='label')
    f.group(652, 52, 452, 284, 'infra', ('谁在哪里解析 chord 语法', 'Who parses the chord grammar, where'), None, 'code', title_mono=False, gid='d')
    f.node('cl', 668, 92, 420, 68, 'modes', 'pi-client · client.ts', ('parseServiceCall · parseServiceCatalogue', 'parseServiceCall · parseServiceCatalogue'), 'monitor', tsize=10.6, ssize=9.0,
           sub2=('createServiceStateDecoder · parseWire…Snapshot', 'createServiceStateDecoder · parseWire…Snapshot'))
    f.node('sv', 668, 172, 420, 68, 'infra', 'pi-server · server.ts', ('decodeServiceControlCall · parseServiceCall', 'decodeServiceControlCall · parseServiceCall'), 'cpu', tsize=10.6, ssize=9.0,
           sub2=('createServiceStateEncoder · RemoteServiceError', 'createServiceStateEncoder · RemoteServiceError'))
    f.node('ca', 668, 252, 420, 68, 'coding', 'coding-agent · services/connection.ts', ('createClientServiceTransport(client, route)', 'createClientServiceTransport(client, route)'), 'plug', tsize=10.6, ssize=9.0,
           sub2=('→ 应用自己的类型化 chord 服务绑定', '→ the app\'s own typed chord service bindings'))
    E([(878, 160), (878, 172)], 'cl', 'sv', 'event', 'infra', arrow=False)
    E([(878, 240), (878, 252)], 'sv', 'ca', 'event', 'infra', arrow=False)
    f.group(652, 352, 452, 120, 'err', ('不在公共协议里', 'Not in the public protocol'), None, 'x', title_mono=False, gid='e')
    f.text(668, 400, ('服务器与 worker 的生命周期：协调器只转发不透明消息', 'Server and worker lifecycle: the coordinator only relays opaque messages'), 9.0, 450, cls='muted', layer='label')
    f.text(668, 420, ('对端认证与已认证的服务上下文：实验性传输没有实现', 'Peer authentication and authenticated contexts: not implemented'), 9.0, 450, cls='muted', layer='label')
    f.text(668, 440, ('兼容性保证：协议是实验性的', 'Compatibility guarantees: the protocol is experimental'), 9.0, 450, cls='muted', layer='label')
    f.text(16, 500, ('protocol 只检查 call、result、update 是严格 JSON；它不导出、也不校验 chord 的语法——这让信封层可以在不了解任何服务契约的情况下路由。', 'The protocol only checks that call, result and update are strict JSON; it neither exports nor validates chord\'s grammar — so the envelope layer routes without knowing any service contract.'), 9.4, 450, cls='muted', layer='label')
    f.legend(24, 536, [('layer:modes', ('protocol', 'protocol')), ('layer:ext', ('chord', 'chord')), ('layer:coding', ('应用', 'application')), ('layer:err', ('范围之外', 'out of scope'))])
    return f
