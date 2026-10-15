"""pi-client deep-dive diagrams (cli_*). Facts read from /workspace/pi-src/packages/client at build time."""
import re
from svgkit import Fig
from figs import reg
from figkit import SRC, codebox, bar, hline, vline, chiprow
from pkgsrc import Pkg, MiB, users_of

C_ = Pkg('packages/client/src/')
README = (SRC / 'packages/client/README.md').read_text()
CA = 'packages/coding-agent/src/experimental/'
def ca(rel): return (SRC / (CA + rel)).read_text()

def doc(text, *needles):
    for n in needles: assert n in text, n

# ============================================================== cli_arch
@reg
def cli_arch():
    tot = C_.total()
    j = C_.pkg()
    assert [k for k in j['exports']] == ['.', './unix', './package.json'], j['exports']
    deps = j['dependencies']; assert set(deps) == {'@earendil-works/chord', '@earendil-works/pi-protocol'}, deps
    users = dict(users_of('@earendil-works/pi-client')); assert set(users) == {'coding-agent'}, users
    C_.has('index.ts', 'export { Client, createClientServiceTransport } from "./client.ts";', 'export { ClientDisposedError, DisconnectedError, ServerError } from "./errors.ts";')
    doc(ca('client-runtime.ts'), 'discoverUnixServers({ directory })', 'client = await Client.connect({')
    doc(ca('services/connection.ts'), 'createClientServiceTransport(client, () => ({ serverId: client.serverId }))', 'createClientServiceTransport(client, () => client.attachment)')
    doc(ca('server.ts'), 'transportFactory: createUnixTransportFactory({ path: route.path }),')
    doc(ca('radius-relay.ts'), 'class RadiusClientByteTransport implements ByteTransport {', 'import { WebSocket } from "undici";')
    f = Fig('cli_arch', 1120, 560, (f'pi-client：{tot:,} 行——一个 Client、一个 Connection、一个可替换的字节传输', f'pi-client: {tot:,} lines — one Client, one Connection, a pluggable byte transport'))
    E = f.edge
    f.group(16, 52, 660, 420, 'modes', 'packages/client/src', None, 'layers', gid='l')
    f.node('ix', 32, 92, 628, 44, 'modes', 'index.ts', ('根入口 "."：Client、createClientServiceTransport、3 个错误类、传输与选项类型', 'root entry ".": Client, createClientServiceTransport, 3 error classes, transport and option types'), None, tsize=10.8, ssize=8.8, tag=f'{C_.loc("index.ts")}')
    f.node('cl', 32, 168, 300, 66, 'modes', 'client.ts', ('Client：请求关联、订阅、附着', 'Client: correlation, subscriptions, attachment'), None, tsize=10.8, ssize=8.8, sub2=('createClientServiceTransport', 'createClientServiceTransport'), tag=f'{C_.loc("client.ts")}', strong=True)
    f.node('cn', 360, 168, 300, 66, 'modes', 'connection.ts', ('Connection：状态机、握手、解码', 'Connection: state machine, handshake'), None, tsize=10.8, ssize=8.8, sub2=('ServerMessageDecoder', 'ServerMessageDecoder'), tag=f'{C_.loc("connection.ts")}')
    SM = [('errors.ts', ('3 个错误类', '3 error classes')), ('types.ts', ('选项与订阅类型', 'options, subscriptions')), ('transport.ts', ('ByteTransport 契约', 'ByteTransport contract')), ('promise.ts', ('Promise 解析器', 'promise resolvers'))]
    for i, (p, d) in enumerate(SM):
        f.node(f's{i}', 32 + i * 161, 262, 145, 50, 'modes', p, d, None, tsize=10.2, ssize=8.6, tag=f'{C_.loc(p)}')
    f.group(32, 336, 628, 120, 'coding', ('unix.ts → 子路径 "./unix"（仅 Node / Bun）', 'unix.ts → subpath "./unix" (Node / Bun only)'), None, 'plug', dashed=True, title_mono=False, gid='ux')
    f.node('u0', 48, 380, 290, 60, 'coding', 'createUnixTransportFactory', ('UnixByteTransport · maxPendingBytes', 'UnixByteTransport · maxPendingBytes'), None, mono=True, tsize=10.2, ssize=8.6)
    f.node('u1', 354, 380, 290, 60, 'coding', 'discoverUnixServers', ('readdir → lstat → 握手探测', 'readdir → lstat → handshake probe'), None, mono=True, tsize=10.2, ssize=8.6, tag=f'{C_.loc("unix.ts")}')
    E([(182, 136), (182, 168)], 'ix', 'cl', 'main', 'modes')
    E([(332, 201), (360, 201)], 'cl', 'cn', 'dep', 'modes')
    E([(510, 136), (510, 168)], 'ix', 'cn', 'faint', 'modes')
    # right
    f.group(692, 52, 412, 420, 'infra', ('依赖与使用者', 'Dependencies and users'), None, 'hub', title_mono=False, gid='r')
    f.text(708, 100, ('依赖', 'Depends on'), 9.6, 650, cls='faint', layer='label', ls='.04em')
    f.node('d0', 708, 110, 380, 40, 'infra', f'@earendil-works/chord {deps["@earendil-works/chord"]}', ('服务调用解析、订阅状态解码、RemoteServiceTransport', 'service-call parsers, state decoder, RemoteServiceTransport'), None, tsize=10.2, ssize=8.6)
    f.node('d1', 708, 158, 380, 40, 'infra', f'@earendil-works/pi-protocol {deps["@earendil-works/pi-protocol"]}', ('encodeClientMessage · ServerMessageDecoder · isServerId', 'encodeClientMessage · ServerMessageDecoder · isServerId'), None, tsize=10.2, ssize=8.6)
    f.text(708, 226, ('使用者：coding-agent 的 experimental/（%d 个文件导入它）' % users['coding-agent'], 'Used by: coding-agent experimental/ (%d importing files)' % users['coding-agent']), 9.6, 650, cls='faint', layer='label', ls='.04em')
    U = [('client-runtime.ts', ('发现 Unix 服务器，Client.connect', 'discover Unix servers, Client.connect')),
         ('services/connection.ts', ('createClientServiceTransport → 类型化服务', 'createClientServiceTransport → typed services')),
         ('server.ts', ('确认刚启动的服务器能握手', 'check a freshly started server handshakes')),
         ('radius-relay.ts', ('自定义 ByteTransport：WebSocket 中继', 'a custom ByteTransport over a WebSocket relay'))]
    for i, (k, d) in enumerate(U):
        f.node(f'k{i}', 708, 236 + i * 52, 380, 44, 'coding', k, d, None, mono=True, tsize=10.2, ssize=8.6)
    doc(README, 'It never reconnects or replays requests automatically.')
    f.text(16, 498, ('README：断开或 dispose 后，挂起的请求在本地 reject；Client 不会自动重连，也不会重放请求。', 'README: on disconnect or disposal, pending requests reject locally; the Client never reconnects or replays requests automatically.'), 9.4, 450, cls='muted', layer='label')
    f.legend(24, 532, [('layer:modes', ('核心', 'core')), ('layer:coding', ('Unix 传输 / 使用方', 'Unix transport / users')), ('layer:infra', ('依赖', 'dependencies')), ('main', ('入口', 'entry')), ('dep', ('使用', 'uses'))])
    f.note(1096, 532, ('标签 = 行数', 'tag = lines'), 10.5, anchor='end')
    return f

# ============================================================== cli_lifecycle : Connection state machine
@reg
def cli_lifecycle():
    s = C_.src('connection.ts')
    C_.has('connection.ts', 'state: "connecting",', 'Received server data before the client hello was sent', 'Expected server hello as first message',
           'does not match', 'Received server hello before the client hello was sent', 'Unexpected handshake message', 'let error: Error = new DisconnectedError("Byte transport closed");',
           'return Promise.reject(new DisconnectedError(`Client is already ${this.#lifecycle.state}`));', 'transport.close();\n\t\t\treturn;', 'if (this.#isCurrent(id))')
    C_.has('types.ts', 'export type ConnectionState = "disconnected" | "connecting" | "connected";')
    C_.has('client.ts', 'this.#rejectPendingRequests(change.error ?? new DisconnectedError());', 'this.#serviceListeners.clear();', 'this.#setAttachment(undefined);')
    f = Fig('cli_lifecycle', 1120, 600, ('Connection 的三个状态：每次 connect() 都是一次新的尝试', 'Connection in three states: every connect() is a fresh attempt'))
    E = f.edge
    f.group(16, 52, 700, 470, 'modes', ('ConnectionState', 'ConnectionState'), 'connection.ts', 'loop', gid='sm')
    f.node('dc', 40, 120, 190, 48, 'infra', 'disconnected', None, None, kind='pill', align='center', tsize=12, strong=True)
    f.node('cg', 500, 120, 190, 48, 'modes', 'connecting', None, None, kind='pill', align='center', tsize=12)
    f.node('cd', 500, 400, 190, 48, 'coding', 'connected', None, None, kind='pill', align='center', tsize=12, strong=True)
    E([(230, 136), (500, 136)], 'dc', 'cg', 'main', 'modes', label=('connect()：新的 id、新解码器', 'connect(): new id, new decoder'), lpos=(365, 126), lmono=False, lsize=9.2)
    E([(595, 168), (595, 400)], 'cg', 'cd', 'main', 'coding', label=('收到匹配的 hello', 'matching hello'), lpos=(640, 284), lmono=False, lsize=9.2)
    E([(500, 156), (230, 156)], 'cg', 'dc', 'err', 'err')
    E([(500, 424), (135, 424), (135, 168)], 'cd', 'dc', 'err', 'err', label=('关闭 · 出错 · disconnect()', 'close · error · disconnect()'), lpos=(318, 414), lmono=False, lsize=9.2, lcls='err')
    f.text(250, 186, ('握手失败（见右侧）', 'handshake failure (right)'), 9.0, 450, cls='cf c-err', layer='label')
    # inside: what connecting does
    f.text(176, 224, ('connecting 期间', 'While connecting'), 10.0, 700, cls='strongt', layer='label')
    ST = [('transportFactory(handlers)', ('打开一个全新的 ByteTransport', 'open a fresh ByteTransport')),
          (f'send hello {{ version }}', ('第一帧总是客户端的 hello', 'the first frame is always the client hello')),
          ('decoder.push(chunk)', ('ServerMessageDecoder 增量解码', 'ServerMessageDecoder decodes incrementally')),
          ('hello.serverId === options.serverId', ('物理端点必须是预期的逻辑服务器', 'the endpoint must be the expected logical server'))]
    for i, (a, b) in enumerate(ST):
        y = 252 + i * 36
        f.step(str(i + 1), 186, y, 'modes')
        f.text(204, y + 4, a, 9.4, 600, True, cls='strongt', layer='label')
        f.text(204, y + 19, b, 8.8, 450, cls='muted', layer='label')
    f.text(40, 470, ('旧尝试的回调带着旧 id：#isCurrent(id) 为假就被忽略；迟到的 transport 直接 close()。', 'Callbacks from an old attempt carry its id: #isCurrent(id) is false, so they are ignored; a late transport is closed.'), 9.0, 450, cls='muted', layer='label')
    f.text(40, 488, ('非 disconnected 时再 connect() → DisconnectedError("Client is already …")。', 'connect() while not disconnected → DisconnectedError("Client is already …").'), 9.0, 450, cls='muted', layer='label')
    # right: failures
    f.group(732, 52, 372, 280, 'err', ('握手阶段的失败', 'Handshake failures'), None, 'shield', title_mono=False, gid='hf')
    HF = [('hello_error', ('→ ServerError(code)，例如 version', '→ ServerError(code), e.g. version')),
          ('first ≠ hello', ('Expected server hello as first message', 'Expected server hello as first message')),
          ('serverId ≠', ('Connected server … does not match …', 'Connected server … does not match …')),
          ('data before hello', ('客户端 hello 发出前就收到数据', 'data before the client hello was sent')),
          ('factory throws', ('→ DisconnectedError(cause)', '→ DisconnectedError(cause)'))]
    for i, (c_, d) in enumerate(HF):
        y = 94 + i * 48
        f.chip(748, y, c_, 'err', size=9.2, h=20)
        f.text(748, y + 33, d, 8.8, 450, cls='muted', layer='label')
    f.group(732, 348, 372, 174, 'ext', ('进入 disconnected 时，Client 会', 'Entering disconnected, the Client'), None, 'x', title_mono=False, gid='cl')
    CL = [('清空 hello 与 attachment', 'clear hello and attachment'), ('以该错误 reject 所有挂起请求', 'reject every pending request with that error'), ('丢弃全部服务订阅', 'drop every service subscription'), ('通知 onConnectionStateChange', 'notify onConnectionStateChange')]
    for i, t in enumerate(CL):
        f.step(str(i + 1), 760, 400 + i * 28, 'ext')
        f.text(778, 404 + i * 28, t, 9.2, 500, cls='strongt', layer='label')
    f.text(16, 548, ('connected 之后再收到 hello / hello_error 也是协议错误；解码器在关闭时 end()，半帧会变成截断错误。', 'A hello / hello_error after connecting is a protocol error too; on close the decoder end()s, so a partial frame becomes a truncation error.'), 9.4, 450, cls='muted', layer='label')
    f.legend(24, 580, [('main', ('前进', 'advance')), ('err', ('失败 / 关闭', 'failure / close')), ('layer:err', ('握手错误', 'handshake errors')), ('layer:ext', ('清理', 'cleanup'))])
    return f

# ============================================================== cli_request : one request from guard to settlement
@reg
def cli_request():
    C_.has('client.ts', 'if (this.#disposed) return Promise.reject(new ClientDisposedError());', 'if (!this.connected) return Promise.reject(new DisconnectedError());',
           'if (signal?.aborted) return Promise.reject(abortError(signal));', 'const id = `request-${++this.#requestSequence}`;', 'this.#takePendingRequest(id)?.reject(toError(error));',
           'sent = true;\n\t\tif (aborted) sendCancel();', 'encodeClientMessage({ type: "cancel", id, target }', 'pending.reject(new ServerError(message.error));',
           'new ProtocolValidationError("Response has no matching request")', 'if (!sent || !this.connected) return;', 'call: parseServiceCall(call) as unknown as JsonValue')
    f = Fig('cli_request', 1120, 580, ('一个请求：先过守卫，再登记、编码、发送；按 id 结算', 'One request: guards, then register, encode, send; settled by id'))
    f.group(16, 52, 560, 440, 'modes', '#request(target, call, signal)', 'client.ts', 'msg', gid='rq')
    ST = [('if (this.#disposed)', None, 'ClientDisposedError'),
          ('if (!this.connected)', None, 'DisconnectedError'),
          ('if (signal?.aborted)', ('直接拒绝，什么也不发送', 'reject at once, send nothing'), 'AbortError'),
          ('id = `request-${++seq}`', ('#pendingRequests.set(id, { resolve, reject, cleanup })', '#pendingRequests.set(id, { resolve, reject, cleanup })'), None),
          ('encodeClientMessage(request)', ('parseServiceCall + maxFrameLength；失败则取回条目并拒绝', 'parseServiceCall + maxFrameLength; on failure take back and reject'), 'encode error'),
          ('connection.send(frame); sent = true', ('发送前就已 abort → 发送后立刻补发 cancel', 'aborted before the send → the cancel follows at once'), None)]
    for i, (a, b, err) in enumerate(ST):
        y = 104 + i * 62
        f.step(str(i + 1), 40, y, 'modes')
        f.text(60, y + 4, a, 9.8, 600, True, cls='strongt', layer='label')
        if b: f.text(60, y + 21, b, 8.8, 450, cls='muted', layer='label')
        if err: f.chip(424, y - 10, err, 'err', size=9.0, h=20)
    f.text(40, 470, ('前三个守卫失败时没有 id、没有条目，也没有任何字节离开客户端。', 'When one of the first three guards fails there is no id, no entry, and no byte leaves the client.'), 9.0, 450, cls='muted', layer='label')
    # right: pending map
    f.group(592, 52, 512, 124, 'infra', ('#pendingRequests：按 id 关联', '#pendingRequests: correlated by id'), 'Map<string, PendingRequest>', 'queue', title_mono=False, gid='pm')
    codebox(f, 608, 92, 480, [(0, '"request-1" → { resolve, reject, cleanup }', ''),
                              (0, '"request-2" → { resolve, reject, cleanup }', ''),
                              (0, ('// 回应可以乱序到达；取出时 cleanup 移除 abort 监听', '// responses may arrive out of order; cleanup removes the abort listener'), 'muted')], None, size=9.6, lh=16)
    f.group(592, 192, 512, 300, 'ext', ('一个回应或事件到达之后', 'When a response or event arrives'), None, 'flag', title_mono=False, gid='oc')
    OC = [('ok: true', 'ext', ('resolve(result)；订阅时先经 transform 解码快照', 'resolve(result); a subscription decodes its snapshot in transform')),
          ('ok: false', 'err', ('reject(new ServerError(error))：带 code 与 message', 'reject(new ServerError(error)): carries code and message')),
          ('abort()', 'modes', ('本地立刻 reject；已发送则补发 cancel { id, target }', 'reject locally now; if sent, send cancel { id, target }')),
          ('no match', 'err', ('Response has no matching request → 断开连接', 'Response has no matching request → disconnect')),
          ('transform throws', 'err', ('ProtocolValidationError → 断开连接', 'ProtocolValidationError → disconnect')),
          ('disconnected', 'infra', ('所有条目一次性以断开原因 reject', 'every entry rejects with the disconnect reason'))]
    for i, (c_, ly, d) in enumerate(OC):
        y = 236 + i * 42
        f.chip(608, y, c_, ly, size=9.0, h=20)
        f.text(744, y + 14, d, 8.8, 450, cls='muted', layer='label')
    f.text(16, 520, ('abort 之后条目仍留在表里，直到服务端的 cancelled 回应到来——所以那条回应不会被当成“没有匹配的请求”。', 'After abort the entry stays in the map until the server\'s cancelled response arrives, so that response is never a "no matching request".'), 9.4, 450, cls='muted', layer='label')
    f.legend(24, 556, [('layer:modes', ('请求路径', 'request path')), ('layer:ext', ('成功', 'success')), ('layer:err', ('失败', 'failure')), ('layer:infra', ('关联表', 'correlation map'))])
    return f

# ============================================================== cli_subscribe : buffered until start()
@reg
def cli_subscribe():
    C_.has('client.ts', 'const subscriptionId = `service-${++this.#serviceSubscriptionSequence}`;', 'active.queuedWireUpdates.push(message.update);', 'active.hydrated = true;',
           'if (active.ready) this.#deliverServiceUpdate(active, update);', 'active.ready = true;', 'if (this.connected && this.#targetIsCurrent(target)) {',
           'await active.deliveryTail;', '.catch((error: unknown) => this.#reportListenerError(error));', 'createServiceUnsubscribeCall(subscriptionId)')
    C_.has('types.ts', '/** Begin ordered update delivery after the caller has installed the snapshot. */')
    f = Fig('cli_subscribe', 1120, 720, ('一个服务订阅：快照之前的更新先缓冲，start() 之后才按序交付', 'One service subscription: updates buffer before the snapshot and flow in order only after start()'))
    E = f.edge
    SX, CX, AX = 150, 560, 970
    f.node('s', SX - 100, 56, 200, 40, 'infra', 'Server', ('pi-server', 'pi-server'), 'cpu', tsize=11, ssize=8.8, strong=True)
    f.node('c', CX - 100, 56, 200, 40, 'modes', 'Client', ('#serviceListeners', '#serviceListeners'), 'monitor', tsize=11, ssize=8.8, strong=True)
    f.node('a', AX - 100, 56, 200, 40, 'coding', ('应用 / 绑定', 'App / binding'), ('Chord 服务绑定', 'Chord service binding'), 'user', tsize=11, ssize=8.8, strong=True)
    for x in (SX, CX, AX): vline(f, x, 96, 652)
    M = [('ac', 130, 'subscribeService(target, serviceId, mode, listener)', 'main', ('service-N · hydrated = false · ready = false', 'service-N · hydrated = false · ready = false')),
         ('cs', 178, 'request { call: subscribe(service-N, serviceId, mode) }', 'main', None),
         ('sc', 226, ('service_update（早于快照）', 'service_update (before the snapshot)'), 'event', ('原始 JSON → queuedWireUpdates', 'raw JSON → queuedWireUpdates')),
         ('sc', 274, 'response { ok: true, result: snapshot }', 'event', ('decodeSnapshot → hydrated = true → 解码积压', 'decodeSnapshot → hydrated = true → decode backlog')),
         ('ca', 322, '{ id, target, snapshot, start, dispose }', 'event', ('应用先装好快照', 'the app installs the snapshot first')),
         ('sc', 370, 'service_update', 'event', ('ready = false → queued', 'ready = false → queued')),
         ('ac', 418, 'start()', 'main', ('ready = true，按序冲刷 queued', 'ready = true, flush queued in order')),
         ('sc', 466, 'service_update', 'event', ('已就绪：解码后直接交付', 'ready: decode and deliver')),
         ('ca', 514, 'listener(update)', 'event', ('经 deliveryTail 串行，异步监听器也不乱序', 'chained on deliveryTail: async listeners stay ordered')),
         ('ac', 562, 'dispose()', 'main', ('已连接且 target 仍有效时才退订', 'unsubscribe only while connected and the target is current')),
         ('cs', 610, 'request { call: unsubscribe(service-N) }', 'main', ('然后 await deliveryTail，清空缓冲', 'then await deliveryTail and clear the buffers'))]
    X = {'s': SX, 'c': CX, 'a': AX}
    for d, y, lab, kind, note in M:
        a, b = d[0], d[1]
        ly = {'s': 'infra', 'c': 'modes', 'a': 'coding'}[a]
        E([(X[a], y), (X[b], y)], {'s': 's', 'c': 'c', 'a': 'a'}[a], {'s': 's', 'c': 'c', 'a': 'a'}[b], kind, ly, label=lab, lsize=9.2, lmono=isinstance(lab, str))
        if note:
            left = 's' in d
            f.text(CX - 12 if left else CX + 12, y + 21, note, 8.8, 450, cls='muted', layer='label', anchor='end' if left else 'start')
    f.text(16, 678, ('监听器抛出的错误只交给 onListenerError，不会影响连接；断开时 #serviceListeners 被整体清空，订阅不会自动恢复。', 'Listener errors only reach onListenerError and never affect the connection; on disconnect #serviceListeners is cleared and subscriptions are not restored.'), 9.4, 450, cls='muted', layer='label')
    f.legend(24, 704, [('main', ('调用 / 请求', 'call / request')), ('event', ('回应 / 更新', 'response / update'))])
    return f

# ============================================================== cli_attach : out-of-band attachment and the Chord transport
@reg
def cli_attach():
    C_.has('client.ts', 'new ProtocolValidationError("Attachment update belongs to another server")', 'this.#setAttachment(message.attachment ?? undefined);',
           'previous?.attachmentId === attachment?.attachmentId', 'if (resolved === undefined) throw new Error("Remote service target is unavailable");',
           'invoke: async (call, context) => client.request(target(), call, context.abortSignal),', 'activate: () => subscription.start(),', 'close: () => subscription.dispose(),',
           '(update) => listener(update, BACKGROUND_CONTEXT),', 'if (!("sessionId" in target)) return this.#hello?.serverId === target.serverId;')
    f = Fig('cli_attach', 1120, 600, ('附着由服务器带外推送；createClientServiceTransport 每次调用时才解析路由', 'The server pushes attachments out of band; createClientServiceTransport resolves the route on every call'))
    E = f.edge
    f.group(16, 52, 1088, 158, 'ext', ('带外附着：Client.attachment', 'Out-of-band attachment: Client.attachment'), None, 'plug', title_mono=False, gid='at')
    A = [('n1', ('attachment 信封', 'attachment envelope'), ('{ attachment: SessionTarget | null }', '{ attachment: SessionTarget | null }')),
         ('n2', ('serverId 检查', 'serverId check'), ('属于别的服务器 → 断开连接', 'another server → disconnect')),
         ('n3', '#setAttachment', ('三个字段都相同 → 忽略', 'all three fields equal → ignored')),
         ('n4', 'onAttachmentChange', ('通知监听器；undefined = 未附着', 'notify; undefined = not attached'))]
    for i, (k, t, d) in enumerate(A):
        f.node(k, 32 + i * 276, 100, 228, 56, 'ext', t, d, None, mono=isinstance(t, str), tsize=10.6, ssize=8.6, strong=(k == 'n3'))
    for i in range(3):
        E([(260 + i * 276, 128), (308 + i * 276, 128)], f'n{i + 1}', f'n{i + 2}', 'main', 'ext')
    f.text(32, 186, ('null、断开或 dispose → attachment 回到 undefined；附着信封在 attach 的回应之前送达，所以回应到来时路由已可用。', 'null, a disconnect or dispose → attachment returns to undefined; the envelope arrives before the attach response, so the route is ready when it resolves.'), 9.0, 450, cls='muted', layer='label')
    # bottom left: the adapter
    f.group(16, 228, 640, 300, 'modes', 'createClientServiceTransport(client, getTarget)', 'client.ts', 'braces', gid='ad')
    codebox(f, 32, 270, 608, [(0, ('// 返回 Chord 的 RemoteServiceTransport', '// returns a Chord RemoteServiceTransport'), 'muted'),
                              (0, 'invoke(call, context)', 'strongt'),
                              (1, '→ client.request(target(), call, context.abortSignal)', ''),
                              (0, 'subscribe(serviceId, mode, listener, context)', 'strongt'),
                              (1, '→ client.subscribeService(target(), serviceId, mode, …)', ''),
                              (1, '→ { snapshot, activate: start(), close: dispose() }', ''),
                              (0, ('// 更新以 BACKGROUND_CONTEXT 交给 Chord 监听器', '// updates reach the Chord listener with BACKGROUND_CONTEXT'), 'muted'),
                              (0, ('// target() 在每次调用时求值；undefined →', '// target() is evaluated per call; undefined →'), 'muted'),
                              (1, 'Error("Remote service target is unavailable")', 'cf c-err')], None, size=9.6, lh=17)
    f.text(32, 508, ('只做适配：类型化服务代理与应用契约由应用自己的 Chord 绑定提供。', 'An adapter only: typed service proxies and application contracts come from the app\'s own Chord bindings.'), 9.0, 450, cls='faint', layer='label')
    # bottom right: coding-agent
    f.group(672, 228, 432, 300, 'coding', 'services/connection.ts', 'coding-agent', 'hub', gid='ca')
    doc(ca('services/connection.ts'), 'createClientServiceTransport(client, () => ({ serverId: client.serverId }))', 'createClientServiceTransport(client, () => client.attachment)')
    f.node('sv', 688, 346, 400, 52, 'coding', ('服务器级服务', 'Server-wide services'), ('() => ({ serverId: client.serverId })', '() => ({ serverId: client.serverId })'), 'cpu', tsize=10.6, ssize=8.8)
    f.node('ss', 688, 276, 400, 52, 'coding', ('Session 服务', 'Session services'), ('() => client.attachment', '() => client.attachment'), 'db', tsize=10.6, ssize=8.8, strong=True)
    E([(974, 156), (974, 276)], 'n4', 'ss', 'event', 'ext', label='client.attachment', lpos=(974, 214), lsize=9.0)
    f.text(688, 426, ('dispose() 只在 #targetIsCurrent 时退订：', 'dispose() unsubscribes only while #targetIsCurrent:'), 9.2, 600, cls='strongt', layer='label')
    f.text(688, 446, ('{ serverId } → 与 hello.serverId 相同', '{ serverId } → equals hello.serverId'), 8.8, 450, cls='muted', layer='label')
    f.text(688, 464, ('Session 目标 → 三个字段都等于当前附着', 'Session target → all three equal the attachment'), 8.8, 450, cls='muted', layer='label')
    f.text(688, 490, ('过期的附着不再发退订：服务器早已丢弃它。', 'A stale attachment sends no unsubscribe: the server dropped it.'), 8.8, 450, cls='faint', layer='label')
    f.legend(24, 572, [('layer:ext', ('附着状态', 'attachment state')), ('layer:modes', ('适配器', 'adapter')), ('layer:coding', ('coding-agent', 'coding-agent')), ('event', ('读取路由', 'reads the route'))])
    return f

# ============================================================== cli_transport : the ByteTransport contract and the Unix implementation
@reg
def cli_transport():
    C_.has('transport.ts', '/** Sends one byte chunk. Calls must be delivered in invocation order. */', '/** Closes the transport. Implementations must make repeated calls harmless. */',
           '/** Creates a fresh connected, authenticated transport. Exactly one terminal handler is expected. */')
    C_.has('unix.ts', 'const maxPendingBytes = options.maxPendingBytes ?? DEFAULT_MAX_FRAME_LENGTH * 4;', 'if (this.#pendingBytes + chunk.byteLength > this.#maxPendingBytes) {',
           'const bytes = chunk.slice();', 'const write = this.#writeTail.then(() => this.#write(bytes));', 'this.#pendingBytes -= bytes.byteLength;', 'requiresDrain = !accepted;',
           'new Error("Unix transport closed during write")', 'else reject(new Error("Unix transport closed before connecting"));', 'throw new Error("Unix transport is not supported on Windows");')
    R_ = Pkg(CA)
    ri, rm = R_.num('radius-relay.ts', 'CLIENT_RETRY_INITIAL_MS'), R_.num('radius-relay.ts', 'CLIENT_RETRY_MAX_MS'); assert (ri, rm) == (1000, 30000)
    doc(ca('radius-relay.ts'), 'class OrderedWebSocketWriter {', 'class RadiusClientByteTransport implements ByteTransport {')
    mf = 16 * 1024 * 1024
    f = Fig('cli_transport', 1120, 600, ('字节传输是可替换的：契约只有 send / close 与三个回调', 'The byte transport is pluggable: the contract is send / close and three callbacks'))
    E = f.edge
    f.group(16, 52, 470, 300, 'modes', ('契约', 'The contract'), 'transport.ts', 'plug', title_mono=False, gid='ct')
    codebox(f, 32, 92, 438, [(0, 'interface ByteTransport {', 'strongt'),
                             (1, 'send(chunk): Promise<void>', ''), (1, 'close(): void', ''), (0, '}', 'strongt'),
                             (0, 'interface ByteTransportHandlers {', 'strongt'),
                             (1, 'onData(chunk) · onClose() · onError(error)', ''), (0, '}', 'strongt'),
                             (0, 'type ByteTransportFactory =', 'strongt'),
                             (1, '(handlers) => ByteTransport | Promise<…>', '')], None, size=9.6, lh=16)
    RU = [('send 必须按调用顺序送达，并遵守背压', 'send must deliver in call order and honor backpressure'), ('close() 可重复调用', 'close() must be safe to repeat'), ('恰好一个终止回调：onClose 或 onError', 'exactly one terminal callback: onClose or onError'), ('每次连接尝试都由工厂新建并完成认证', 'the factory builds and authenticates one per attempt')]
    for i, t in enumerate(RU):
        f.step(str(i + 1), 40, 260 + i * 22, 'modes')
        f.text(58, 264 + i * 22, t, 8.8, 500, cls='strongt', layer='label')
    # right: Unix write path
    f.group(502, 52, 602, 476, 'coding', 'UnixByteTransport.send(chunk)', 'unix.ts', 'queue', gid='ux')
    SN = [('ck', ('检查', 'Checks'), ('Uint8Array？未关闭？pending + 长度 ≤ maxPendingBytes？', 'a Uint8Array? not closed? pending + length ≤ maxPendingBytes?')),
          ('cp', ('登记并复制', 'Count and copy'), ('#pendingBytes += 长度 · chunk.slice()', '#pendingBytes += length · chunk.slice()')),
          ('ch', ('排进写队列', 'Chain on the write queue'), ('#writeTail.then(() => #write(bytes))', '#writeTail.then(() => #write(bytes))')),
          ('wr', 'socket.write(bytes, callback)', ('返回 false → 还要等 "drain"', 'returned false → also wait for "drain"')),
          ('dn', ('完成', 'Settle'), ('finally：#pendingBytes −= 长度', 'finally: #pendingBytes −= length'))]
    for i, (k, t, d) in enumerate(SN):
        f.node(k, 518, 96 + i * 70, 330, 52, 'coding', t, d, None, mono=isinstance(t, str), tsize=10.4, ssize=8.6, strong=(k == 'wr'))
        if i: E([(683, 96 + i * 70 - 18), (683, 96 + i * 70)], SN[i - 1][0], k, 'main', 'coding')
    ER = [(96, ('超限 → reject', 'over limit → reject')), (306, ('写入中 socket 关闭', 'socket closed mid-write')), (306 + 24, ('write 回调带错误', 'write callback error'))]
    for y, t in ER:
        f.text(864, y + 18, t, 8.8, 600, cls='cf c-err', layer='label')
    f.text(518, 466, (f'maxPendingBytes 默认 = 4 × {mf // 1024 // 1024} MiB 帧上限 = {4 * mf // 1024 // 1024} MiB', f'maxPendingBytes defaults to 4 × the {mf // 1024 // 1024} MiB frame limit = {4 * mf // 1024 // 1024} MiB'), 9.0, 600, cls='strongt', layer='label')
    f.text(518, 484, ('失败的写不会卡住队列：#writeTail 吞掉错误，只有调用方的 Promise 被拒绝。', 'A failed write never blocks the queue: #writeTail swallows it; only the caller\'s promise rejects.'), 8.8, 450, cls='muted', layer='label')
    f.text(518, 502, ('Windows 上不支持；连接前关闭 → "closed before connecting"。', 'Not supported on Windows; closing before connect → "closed before connecting".'), 8.8, 450, cls='muted', layer='label')
    # bottom left: another implementation
    f.group(16, 368, 470, 160, 'ext', ('另一个实现', 'Another implementation'), 'coding-agent radius-relay.ts', 'globe', title_mono=False, gid='rr')
    f.node('rr1', 32, 412, 438, 44, 'ext', 'RadiusClientByteTransport', ('同一契约，跑在 WebSocket 中继上；OrderedWebSocketWriter 保序', 'same contract over a WebSocket relay; OrderedWebSocketWriter keeps order'), None, mono=True, tsize=10.2, ssize=8.6)
    f.text(32, 482, (f'RadiusClientReconnect：断开后 {ri // 1000} s 起指数退避（上限 {rm // 1000} s），', f'RadiusClientReconnect: after a disconnect, back off from {ri // 1000} s (max {rm // 1000} s),'), 8.8, 450, cls='muted', layer='label')
    f.text(32, 500, ('reconnect() 后重新附着原 Session——这是应用的策略，不是 Client 的。', 'reconnect(), then reattach the same Session: app policy, not the Client\'s.'), 8.8, 450, cls='muted', layer='label')
    f.text(16, 556, ('Connection 只依赖这个契约：Unix socket、WebSocket 中继或测试替身都能接上。', 'Connection depends only on this contract: a Unix socket, a WebSocket relay or a test double all plug in.'), 9.4, 450, cls='muted', layer='label')
    f.legend(24, 584, [('layer:modes', ('契约', 'contract')), ('layer:coding', ('Unix 实现', 'Unix implementation')), ('layer:ext', ('中继实现', 'relay implementation')), ('layer:err', ('失败', 'failure'))])
    return f

# ============================================================== cli_discover : discoverUnixServers
@reg
def cli_discover():
    to = C_.num('unix.ts', 'DEFAULT_DISCOVERY_TIMEOUT_MS'); mx = C_.num('unix.ts', 'MAX_CONCURRENT_DISCOVERY_PROBES'); assert (to, mx) == (1000, 16)
    C_.has('unix.ts', 'const UNIX_SOCKET_SUFFIX = ".sock";', 'if (isErrorCode(error, "ENOENT")) return [];', 'return isServerId(serverId) ? [{ serverId, path: join(directory, name) }] : [];',
           'const workerCount = Math.min(MAX_CONCURRENT_DISCOVERY_PROBES, candidates.length);', 'if (!(await lstat(candidate.path)).isSocket()) continue;', 'failure ??= { error };',
           'return routes.sort((left, right) => left.serverId.localeCompare(right.serverId));', 'reject(new UnixDiscoveryTimeoutError());', 'await client.dispose();',
           'error instanceof ProtocolValidationError ||', '(error instanceof ServerError && error.code === "version") ||', '(error instanceof DisconnectedError && error.cause === undefined) ||')
    IG = re.findall(r'isErrorCode\(error, "([A-Z]+)"\) \|\|', C_.src('unix.ts')) + re.findall(r'isErrorCode\(error, "([A-Z]+)"\)\n\t\t\) \{', C_.src('unix.ts'))
    assert IG == ['ENOENT', 'ECONNREFUSED', 'ECONNRESET', 'EPIPE', 'ETIMEDOUT'], IG
    doc(README, 'Discovery is read-only and probes at most 16 sockets concurrently.')
    f = Fig('cli_discover', 1120, 600, (f'discoverUnixServers：读目录、按文件名定 serverId、最多 {mx} 路并发握手探测', f'discoverUnixServers: read a directory, take serverIds from file names, probe up to {mx} at a time'))
    E = f.edge
    f.node('rd', 16, 64, 230, 56, 'coding', 'readdir(directory)', ('目录不存在 → 返回 []', 'missing directory → []'), 'file', mono=True, tsize=10.4, ssize=8.8)
    f.node('fl', 290, 64, 250, 56, 'coding', ('文件名过滤', 'Filter names'), ('<serverId>.sock 且 isServerId', '<serverId>.sock with isServerId'), 'filter', tsize=10.4, ssize=8.8)
    f.node('wk', 584, 64, 250, 56, 'modes', ('工作者池', 'Worker pool'), (f'min({mx}, 候选数) 个，共享 nextIndex', f'min({mx}, candidates), shared nextIndex'), 'queue', tsize=10.4, ssize=8.8, strong=True)
    f.node('so', 878, 64, 226, 56, 'ext', ('结果', 'Result'), ('按 serverId 排序的 { serverId, path }', '{ serverId, path } sorted by serverId'), 'check', tsize=10.4, ssize=8.8)
    E([(246, 92), (290, 92)], 'rd', 'fl', 'main', 'coding')
    E([(540, 92), (584, 92)], 'fl', 'wk', 'main', 'coding')
    E([(834, 92), (878, 92)], 'wk', 'so', 'main', 'ext')
    # one probe
    f.group(16, 148, 700, 360, 'modes', ('每个候选：probeUnixServer', 'Per candidate: probeUnixServer'), 'unix.ts', 'eye', title_mono=False, gid='pb')
    PS = [('lstat(path).isSocket()', ('不是 socket → 跳过；已消失（ENOENT）→ 跳过', 'not a socket → skip; vanished (ENOENT) → skip')),
          ('new Client({ serverId, transportFactory })', ('期望的 serverId 来自文件名', 'the expected serverId comes from the file name')),
          (f'race(client.connect(), {to} ms)', ('完整握手：版本与 serverId 都要对', 'a full handshake: version and serverId must match')),
          ('finally: client.dispose()', ('销毁 socket 并等它真正 close', 'destroy the socket and wait for its close'))]
    for i, (a, b) in enumerate(PS):
        y = 200 + i * 62
        f.step(str(i + 1), 40, y, 'modes')
        f.text(60, y + 4, a, 9.8, 600, True, cls='strongt', layer='label')
        f.text(60, y + 21, b, 8.8, 450, cls='muted', layer='label')
    f.text(40, 466, ('只读：从不删除任何文件——陈旧 socket 的清理归服务器端的监听器。', 'Read-only: it never deletes anything; stale-socket cleanup belongs to the server\'s listener.'), 9.0, 600, cls='strongt', layer='label')
    f.text(40, 486, ('timeoutMs 必须是 1 … 2,147,483,647 的整数；Windows 上直接报错。', 'timeoutMs must be an integer from 1 to 2,147,483,647; Windows throws.'), 8.8, 450, cls='muted', layer='label')
    # right: outcome classes
    f.group(732, 148, 372, 196, 'infra', ('安静地忽略（不算这台服务器）', 'Quietly ignored (not this server)'), None, 'x', title_mono=False, gid='ig')
    chiprow(f, 748, 196, ['timeout', 'ProtocolValidationError'], 'infra', size=9.0, h=20, gap=6)
    chiprow(f, 748, 224, ['DisconnectedError', 'ServerError(version)'], 'infra', size=9.0, h=20, gap=6)
    chiprow(f, 748, 252, IG[:3], 'infra', size=9.0, h=20, gap=6)
    chiprow(f, 748, 280, IG[3:], 'infra', size=9.0, h=20, gap=6)
    f.text(748, 328, ('DisconnectedError 只在没有 cause 时忽略', 'DisconnectedError is ignored only without a cause'), 8.8, 450, cls='muted', layer='label')
    f.group(732, 360, 372, 148, 'err', ('其它错误：整个发现失败', 'Anything else: discovery fails'), None, 'shield', title_mono=False, gid='fx')
    f.text(748, 408, ('failure ??= { error }：记下第一个错误，', 'failure ??= { error }: remember the first error,'), 9.0, 500, cls='strongt', layer='label')
    f.text(748, 426, ('所有工作者停止领取新候选，', 'every worker stops taking candidates,'), 9.0, 500, cls='strongt', layer='label')
    f.text(748, 444, ('Promise.all 之后抛出它。', 'and it is thrown after Promise.all.'), 9.0, 500, cls='strongt', layer='label')
    f.text(748, 476, ('例如目录不可读（EACCES）。', 'For example an unreadable directory (EACCES).'), 8.8, 450, cls='muted', layer='label')
    doc(ca('client-runtime.ts'), 'routes = (await discoverUnixServers({ directory })).map((route) => ({ transport: "unix", ...route }));')
    f.text(16, 540, ('coding-agent 的 client-runtime.ts 用它列出本机的服务器，再对选中的路由 Client.connect。', 'coding-agent\'s client-runtime.ts uses it to list local servers, then Client.connects to the chosen route.'), 9.4, 450, cls='muted', layer='label')
    f.legend(24, 578, [('layer:coding', ('文件系统', 'filesystem')), ('layer:modes', ('探测', 'probing')), ('layer:infra', ('忽略', 'ignored')), ('layer:err', ('失败', 'failure'))])
    return f

# ============================================================== cli_errors : failure semantics and recovery
@reg
def cli_errors():
    C_.has('errors.ts', 'export class ServerError extends Error {', 'readonly code: ProtocolErrorCode;', 'export class DisconnectedError extends Error {', 'constructor(message = "Client is disconnected", cause?: Error) {',
           'export class ClientDisposedError extends Error {', 'super("Client is disposed");')
    C_.has('client.ts', 'reconnect(): Promise<ServerHello> {\n\t\treturn this.connect();', '// Diagnostics cannot affect protocol or transport state.', 'const error = new ClientDisposedError();',
           'return reason instanceof Error ? reason : new DOMException("The operation was aborted", "AbortError");')
    doc(README, 'pending requests reject locally, but accepted work may still complete remotely before the attachment is released.', 'After disconnection, call `reconnect()`, attach through the application\'s management service again, and explicitly repeat only operations known to be safe.')
    S_ = Pkg('packages/server/src/'); S_.has('errors.ts', 'INTERNAL_SERVER_ERROR_MESSAGE = "Internal server error"')
    S_.has('errors.ts', '"session_not_attached"', '"wrong_server"')
    f = Fig('cli_errors', 1120, 620, ('失败语义：五种错误，没有自动重连', 'Failure semantics: five errors and no automatic reconnection'))
    E = f.edge
    f.group(16, 52, 640, 470, 'err', ('Promise 会以什么拒绝', 'What a promise can reject with'), None, 'shield', title_mono=False, gid='er')
    ER = [('ServerError', 'errors.ts', ('服务器说“不”：hello_error 或 ok: false', 'the server said no: hello_error or ok: false'), ('.code：version · invalid_request · wrong_server · session_not_attached · cancelled …', '.code: version · invalid_request · wrong_server · session_not_attached · cancelled …')),
          ('DisconnectedError', 'errors.ts', ('没连上 / 连接没了', 'not connected, or the connection is gone'), ('传输错误包成 cause；"Byte transport closed"；已在连接中', 'transport errors as cause; "Byte transport closed"; already connecting')),
          ('ClientDisposedError', 'errors.ts', ('dispose() 之后的任何调用', 'any call after dispose()'), ('dispose 时所有挂起请求都以它拒绝', 'every pending request rejects with it on dispose')),
          ('ProtocolValidationError', 'pi-protocol', ('对端违反协议：同时断开连接', 'the peer broke the protocol: also disconnects'), ('坏帧 · serverId 不符 · 无主回应 · 他人的附着', 'bad frame · serverId mismatch · orphan response · foreign attachment')),
          ('AbortError', 'signal.reason', ('调用方 abort', 'the caller aborted'), ('只拒绝这一个请求；连接保持', 'rejects just this request; the connection stays'))]
    for i, (n, src, a, b) in enumerate(ER):
        y = 96 + i * 82
        f.node(f'e{i}', 32, y, 608, 68, 'err', n, a, None, mono=True, tsize=10.8, ssize=9.0, sub2=b, tag=src)
    # right: recovery
    f.group(672, 52, 432, 300, 'modes', ('断开之后：由应用决定', 'After a disconnect: the app decides'), None, 'loop', title_mono=False, gid='rc')
    RC = [('client.reconnect()', ('新的传输、新的握手（等同 connect）', 'a fresh transport and handshake (same as connect)')),
          (('重新 attach', 'attach again'), ('经应用的管理服务；得到新的 attachmentId', 'through the app\'s management service; a new attachmentId')),
          (('重新订阅', 'subscribe again'), ('旧订阅在断开时已全部丢弃', 'old subscriptions were all dropped on disconnect')),
          (('只重放安全的操作', 'replay only safe operations'), ('已被接受的工作可能仍在远端完成', 'accepted work may still complete remotely'))]
    for i, (a, b) in enumerate(RC):
        y = 104 + i * 58
        f.step(str(i + 1), 692, y, 'modes')
        f.text(712, y + 4, a, 9.8, 600, isinstance(a, str), cls='strongt', layer='label')
        f.text(712, y + 21, b, 8.8, 450, cls='muted', layer='label')
    f.group(672, 368, 432, 154, 'infra', ('监听器的错误', 'Listener errors'), None, 'eye', title_mono=False, gid='le')
    f.text(688, 416, ('onConnectionStateChange、onAttachmentChange 与订阅', 'Exceptions from onConnectionStateChange, onAttachmentChange'), 9.0, 500, cls='strongt', layer='label')
    f.text(688, 434, ('监听器抛出的异常只交给 ClientOptions.onListenerError；', 'and subscription listeners only reach ClientOptions.onListenerError;'), 9.0, 500, cls='strongt', layer='label')
    f.text(688, 452, ('它自己再抛也会被吞掉。', 'if that throws too, it is swallowed.'), 9.0, 500, cls='strongt', layer='label')
    f.text(688, 484, ('诊断不能影响协议或传输状态。', 'Diagnostics cannot affect protocol or transport state.'), 8.8, 450, cls='muted', layer='label')
    f.text(16, 552, ('ServerError 的 code 与 message 都来自服务器；pi-server 只转发 ServerError 的消息，其它内部异常一律是 "Internal server error"。', 'A ServerError\'s code and message come from the server; pi-server forwards only ServerError messages, other internal failures are always "Internal server error".'), 9.4, 450, cls='muted', layer='label')
    f.legend(24, 596, [('layer:err', ('错误类', 'error classes')), ('layer:modes', ('恢复步骤', 'recovery steps')), ('layer:infra', ('诊断', 'diagnostics'))])
    return f
