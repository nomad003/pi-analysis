"""pi-server deep-dive diagrams (srv_*). Facts read from /workspace/pi-src/packages/server at build time."""
import re
from svgkit import Fig
from figs import reg
from figkit import SRC, uml, codebox, bar, hline, vline, chiprow
from pkgsrc import Pkg, users_of

S_ = Pkg('packages/server/src/')
README = (SRC / 'packages/server/README.md').read_text()
CA = 'packages/coding-agent/src/experimental/'
def ca(rel): return (SRC / (CA + rel)).read_text()

def doc(text, *needles):
    for n in needles: assert n in text, n

# ============================================================== srv_arch
@reg
def srv_arch():
    tot = S_.total()
    j = S_.pkg()
    assert list(j['exports']) == ['.', './testing', './unix'], j['exports']
    deps = j['dependencies']; assert set(deps) == {'@earendil-works/chord', '@earendil-works/pi-protocol'}, deps
    users = dict(users_of('@earendil-works/pi-server')); assert set(users) == {'coding-agent'}, users
    S_.has('index.ts', 'export * from "./errors.ts";', 'export * from "./listener.ts";', 'export * from "./server.ts";', 'export * from "./types.ts";')
    doc(ca('server.ts'), 'const server = createUnixServer(host, {', 'join(homedir(), ".pi", "server")', 'export const ENV_SERVER_DIR = "PI_SERVER_DIR";')
    doc(ca('radius-relay.ts'), 'readonly server: Pick<Server, "accept">;')
    doc(ca('session-worker-manager.ts'), '#routedHandle(worker: WorkerRecord): RoutedSessionHandle {')
    doc(ca('services/server.ts'), 'import type { RoutedServerServiceAttachment, RoutedServerServiceHost } from "@earendil-works/pi-server";')
    f = Fig('srv_arch', 1120, 580, (f'pi-server：{tot:,} 行——握手、按路由分派、把附着交给应用的 Session', f'pi-server: {tot:,} lines — handshake, route-based dispatch, attachments to the app\'s Sessions'))
    E = f.edge
    f.group(16, 52, 660, 440, 'modes', 'packages/server/src', None, 'layers', gid='l')
    f.node('ix', 32, 92, 628, 44, 'modes', 'index.ts', ('根入口 "."：export * 自 errors、listener、server、types', 'root ".": export * from errors, listener, server, types'), None, tsize=10.8, ssize=8.8, tag=f'{S_.loc("index.ts")}')
    f.node('sv', 32, 168, 300, 66, 'modes', 'server.ts', ('Server：连接、握手、请求分派', 'Server: connections, handshake, dispatch'), None, tsize=10.8, ssize=8.8, sub2=('toProtocolError · failProtocol', 'toProtocolError · failProtocol'), tag=f'{S_.loc("server.ts")}', strong=True)
    f.node('sr', 360, 168, 300, 66, 'ext', 'session-router.ts', ('SessionRouter：Session 与附着（内部）', 'SessionRouter: Sessions, attachments (internal)'), None, tsize=10.8, ssize=8.8, sub2=('runForClient · releaseAttachment', 'runForClient · releaseAttachment'), tag=f'{S_.loc("session-router.ts")}')
    SM = [('types.ts', ('ServerHost 契约', 'ServerHost contract')), ('errors.ts', ('5 个错误子类', '5 error subclasses')), ('listener.ts', ('ServerListener', 'ServerListener')), ('connection.ts', ('ByteConnection（内部）', 'ByteConnection (internal)'))]
    for i, (p, d) in enumerate(SM):
        f.node(f's{i}', 32 + i * 161, 262, 145, 50, 'modes', p, d, None, tsize=10.2, ssize=8.6, tag=f'{S_.loc(p)}')
    E([(182, 136), (182, 168)], 'ix', 'sv', 'main', 'modes')
    E([(332, 201), (360, 201)], 'sv', 'sr', 'dep', 'ext')
    ut = sum(S_.loc('transports/unix/' + p) for p in ('address.ts', 'index.ts', 'listener.ts', 'preset.ts', 'types.ts'))
    tt = sum(S_.loc('testing/' + p) for p in ('client.ts', 'host.ts', 'index.ts', 'server.ts'))
    f.group(32, 336, 306, 140, 'coding', ('transports/unix → "./unix"', 'transports/unix → "./unix"'), None, 'plug', dashed=True, title_mono=False, gid='ux')
    f.node('u0', 48, 380, 274, 80, 'coding', 'createUnixServer', ('getUnixSocketPath · createUnixListener', 'getUnixSocketPath · createUnixListener'), None, mono=True, tsize=10.2, ssize=8.6, sub2=('绑定、发布、身份校验', 'bind, publish, identity checks'), tag=f'{ut}')
    f.group(354, 336, 306, 140, 'infra', ('testing/ → "./testing"', 'testing/ → "./testing"'), None, 'check', dashed=True, title_mono=False, gid='tk')
    f.node('t0', 370, 380, 274, 80, 'infra', 'createTestServer', ('TestServerHost · TestHarness', 'TestServerHost · TestHarness'), None, mono=True, tsize=10.2, ssize=8.6, sub2=('ProtocolTestClient · Deferred', 'ProtocolTestClient · Deferred'), tag=f'{tt}')
    # right
    f.group(692, 52, 412, 440, 'infra', ('依赖与使用者', 'Dependencies and users'), None, 'hub', title_mono=False, gid='r')
    f.text(708, 100, ('依赖', 'Depends on'), 9.6, 650, cls='faint', layer='label', ls='.04em')
    f.node('d0', 708, 110, 380, 40, 'infra', f'@earendil-works/chord {deps["@earendil-works/chord"]}', ('服务控制解码、状态编码器、Context 与取消', 'service-control decoding, state encoder, Context and abort'), None, tsize=10.2, ssize=8.6)
    f.node('d1', 708, 158, 380, 40, 'infra', f'@earendil-works/pi-protocol {deps["@earendil-works/pi-protocol"]}', ('ClientMessageDecoder · encodeServerMessage · isServerId', 'ClientMessageDecoder · encodeServerMessage · isServerId'), None, tsize=10.2, ssize=8.6)
    f.text(708, 226, ('使用者：coding-agent 的 experimental/（%d 个文件导入它）' % users['coding-agent'], 'Used by: coding-agent experimental/ (%d importing files)' % users['coding-agent']), 9.6, 650, cls='faint', layer='label', ls='.04em')
    U = [('server.ts', ('createUnixServer：~/.pi/server/<id>.sock', 'createUnixServer: ~/.pi/server/<id>.sock')),
         ('services/server.ts', ('RoutedServerServiceHost：服务器级服务', 'RoutedServerServiceHost: server-wide services')),
         ('session-worker-manager.ts', ('RoutedSessionHandle：每个 Session 一个 worker', 'RoutedSessionHandle: one worker per Session')),
         ('radius-relay.ts', ('中继来的连接交给 server.accept()', 'relayed connections go to server.accept()'))]
    for i, (k, d) in enumerate(U):
        f.node(f'k{i}', 708, 236 + i * 52, 380, 44, 'coding', k, d, None, mono=True, tsize=10.2, ssize=8.6)
    f.text(708, 460, ('目录可用 PI_SERVER_DIR 覆盖。', 'PI_SERVER_DIR overrides the directory.'), 9.0, 450, cls='muted', layer='label')
    f.text(16, 520, ('Server 本身不懂任何服务契约，也不保存 Session：它只核对路由，把调用交给应用通过 ServerHost 提供的能力。', 'The Server knows no service contract and stores no Session: it checks routes and hands calls to capabilities the app supplies through ServerHost.'), 9.4, 450, cls='muted', layer='label')
    f.legend(24, 556, [('layer:modes', ('核心', 'core')), ('layer:ext', ('Session 路由', 'Session routing')), ('layer:coding', ('Unix / 使用方', 'Unix / users')), ('layer:infra', ('测试与依赖', 'testing & deps'))])
    f.note(1096, 556, ('标签 = 行数', 'tag = lines'), 10.5, anchor='end')
    return f

# ============================================================== srv_host : the ServerHost contract
@reg
def srv_host():
    S_.has('types.ts', 'export interface ServerHost<TMetadata extends SessionMetadata = SessionMetadata> {', 'readonly serverServices: RoutedServerServiceHost;',
           'resolveSession(sessionId: string, context: Context): Promise<TMetadata>;', 'openSession(metadata: TMetadata, context: Context): Promise<RoutedSessionHandle>;',
           'attachClient(presentation: RoutedServerPresentation, context: Context): MaybePromise<RoutedServerServiceAttachment>;', 'readonly terminated?: Promise<Error | undefined>;',
           'prepareSessionRemoval(sessionId: string, context: Context): Promise<void>;', 'release(context: Context): MaybePromise<void>;')
    S_.has('server.ts', 'const services = await this.host.serverServices.attachClient(')
    S_.has('session-router.ts', 'const metadata = await this.options.host.resolveSession(sessionId, context);', 'const handle = await this.options.host.openSession(metadata, context);', 'const acquiring = Promise.resolve(hosted.handle.attachClient(context));')
    doc(ca('server.ts'), 'serverServices: serverServices.host,', 'return workers.openSession(metadata, context, selected.manifestPaths);')
    f = Fig('srv_host', 1120, 620, ('ServerHost：应用交给 Server 的全部能力', 'ServerHost: every capability the app hands to the Server'))
    E = f.edge
    uml(f, 'host', 16, 60, 440, 'modes', 'ServerHost<TMetadata>', '«app»', [['+serverServices: RoutedServerServiceHost', '+resolveSession(sessionId, ctx): TMetadata', '+openSession(metadata, ctx): RoutedSessionHandle']])
    uml(f, 'ssh', 16, 210, 440, 'modes', 'RoutedServerServiceHost', '«app»', [['+attachClient(presentation, ctx)']])
    uml(f, 'rsa', 16, 340, 440, 'modes', 'RoutedServerServiceAttachment', '«per conn»', [['+invokeService(call, publish, ctx)', '+release(ctx)']])
    uml(f, 'rsh', 620, 60, 484, 'ext', 'RoutedSessionHandle', '«per Session»', [['+attachClient(ctx): RoutedSessionAttachment', '+terminated?: Promise<Error | undefined>', '+close(ctx): Promise<void>']])
    uml(f, 'rss', 620, 210, 484, 'ext', 'RoutedSessionAttachment', '«per attach»', [['+invokeService(call, publish, ctx)', '+release(ctx)']])
    uml(f, 'pr', 620, 340, 484, 'coding', 'RoutedServerPresentation', '«from Server»', [['+attachSession(sessionId, ctx)', '+detachSession(ctx)', '+prepareSessionRemoval(sessionId, ctx)']])
    E([(236, 156), (236, 210)], 'host', 'ssh', 'dep', 'modes', label='serverServices', lpos=(236, 183), lsize=9.0)
    E([(236, 272), (236, 340)], 'ssh', 'rsa', 'main', 'modes', label=('握手时', 'at handshake'), lpos=(236, 306), lmono=False, lsize=9.0)
    E([(456, 108), (620, 108)], 'host', 'rsh', 'main', 'ext', label='openSession()', lpos=(538, 98), lsize=9.0)
    E([(862, 156), (862, 210)], 'rsh', 'rss', 'main', 'ext', label=('每次 attach', 'per attach'), lpos=(862, 183), lmono=False, lsize=9.0)
    E([(620, 388), (538, 388), (538, 241), (456, 241)], 'pr', 'ssh', 'event', 'coding', label=('作为参数', 'passed in'), lpos=(538, 316), lmono=False, lsize=9.0)
    LN = [(('握手时：', 'At handshake: '), ('serverServices.attachClient(presentation) 为每个连接建一个服务器级端点；连接断开时 release()。', 'serverServices.attachClient(presentation) builds one server-wide endpoint per connection; release() when it drops.')),
          (('attach 时：', 'On attach: '), ('resolveSession → openSession（同一 Session 只开一次）→ handle.attachClient() 为这次附着取得一个租约。', 'resolveSession → openSession (once per Session) → handle.attachClient() takes a lease for this attachment.')),
          (('terminated：', 'terminated: '), ('意外退出时以错误 resolve，正常关闭时以 undefined resolve；Server 随即让该 Session 的所有附着失效。', 'resolves with an error on unexpected exit, undefined after a normal close; the Server then invalidates every attachment.')),
          (('publish：', 'publish: '), ('invokeService 的第二个参数；订阅的更新经它回到 Server，再编码成 service_update。', 'invokeService\'s second argument; subscription updates come back through it and become service_update.'))]
    for i, (a, b) in enumerate(LN):
        y = 470 + i * 22
        f.text(16, y, a, 9.4, 700, cls='strongt', layer='label')
        f.text(112, y, b, 9.2, 450, cls='muted', layer='label')
    f.text(16, 568, ('coding-agent：serverServices 来自 services/server.ts；openSession 交给 SessionWorkerManager，每个 Session 跑在自己的 worker 进程里。', 'coding-agent: serverServices comes from services/server.ts; openSession goes to SessionWorkerManager, each Session running in its own worker process.'), 9.2, 450, cls='faint', layer='label')
    f.legend(24, 600, [('layer:modes', ('服务器级', 'server-wide')), ('layer:ext', ('Session 级', 'Session level')), ('layer:coding', ('Server 提供给应用', 'Server → app')), ('main', ('返回', 'returns')), ('event', ('参数', 'argument'))])
    return f

# ============================================================== srv_conn : connection stages and the handshake
@reg
def srv_conn():
    st = re.search(r'export type ConnectionStage = (.*);', S_.src('connection.ts')).group(1)
    ST = re.findall(r'"(\w+)"', st); assert ST == ['awaitingHello', 'handshaking', 'ready', 'closing', 'closed'], ST
    hs = S_.num('server.ts', 'DEFAULT_HANDSHAKE_TIMEOUT_MS'); assert hs == 5000
    S_.has('server.ts', 'message: "Handshake timeout",', 'state.stage = "handshaking";', 'state.stage = "ready";\n\t\t\tclearTimeout(state.handshakeTimeout);', 'await services.release(TODO_CONTEXT);',
           'void handshake.then(() => {', 'const message: ServerHelloError = { type: "hello_error", error };', 'await this.closeConnection(connection.connection, finalFrame);',
           'controller.abort(new Error("Client disconnected"));', 'connection.serviceStateEncoders.clear();', 'this.sessions.disconnect(connection, TODO_CONTEXT),', 'serverServices?.release(TODO_CONTEXT),',
           'message: `Unsupported protocol version ${hello.version}; expected ${PROTOCOL_VERSION}`,', 'if (this.connections.delete(connection)) this.notifyConnectionCountChanged();')
    f = Fig('srv_conn', 1120, 620, (f'一条服务器连接的五个阶段：握手要在 {hs // 1000} s 内完成', f'Five stages of a server connection: the handshake must finish within {hs // 1000} s'))
    E = f.edge
    X = [32, 248, 464, 680, 896]
    LY = ['modes', 'modes', 'coding', 'err', 'infra']
    for i, (s_, x) in enumerate(zip(ST, X)):
        f.node(f'p{i}', x, 120, 176, 44, LY[i], s_, None, None, kind='pill', align='center', tsize=12, strong=(s_ == 'ready'))
    E([(208, 142), (248, 142)], 'p0', 'p1', 'main', 'modes')
    E([(424, 142), (464, 142)], 'p1', 'p2', 'main', 'coding')
    E([(640, 142), (680, 142)], 'p2', 'p3', 'err', 'err')
    E([(856, 142), (896, 142)], 'p3', 'p4', 'main', 'infra')
    E([(120, 120), (120, 84), (768, 84), (768, 120)], 'p0', 'p3', 'err', 'err', label=(f'超时 {hs // 1000} s · 首条不是 hello · 坏帧', f'timeout {hs // 1000} s · first is not hello · bad frame'), lpos=(444, 84), lmono=False, lsize=9.0, lcls='err')
    E([(552, 164), (552, 200), (984, 200), (984, 164)], 'p2', 'p4', 'err', 'infra', label=('传输 onClose / onError', 'transport onClose / onError'), lpos=(768, 200), lmono=False, lsize=9.0)
    f.text(214, 186, ('收到 hello', 'got hello'), 8.8, 450, cls='muted', layer='label')
    f.text(430, 186, ('hello 已发出', 'hello sent'), 8.8, 450, cls='muted', layer='label')
    # finishHandshake
    f.group(16, 228, 540, 300, 'modes', 'finishHandshake(state, hello)', 'server.ts', 'key', gid='fh')
    FH = [(('版本检查', 'Version check'), ('不支持 → hello_error { code: "version" }', 'unsupported → hello_error { code: "version" }')),
          ('serverServices.attachClient(presentation)', ('presentation = { attachSession, detachSession, prepareSessionRemoval }', 'presentation = { attachSession, detachSession, prepareSessionRemoval }')),
          (('再检查一次', 'Check again'), ('期间关闭或断开 → release() 刚得到的端点，就此结束', 'closed or dropped meanwhile → release() the new endpoint and stop')),
          ('send hello { version, serverId }', ('发送成功 → stage = ready，清掉握手定时器', 'sent → stage = ready, clear the handshake timer'))]
    for i, (a, b) in enumerate(FH):
        y = 278 + i * 58
        f.step(str(i + 1), 40, y, 'modes')
        f.text(60, y + 4, a, 9.8, 600, isinstance(a, str), cls='strongt', layer='label')
        f.text(60, y + 21, b, 8.8, 450, cls='muted', layer='label')
    f.text(40, 512, ('握手期间到达的请求挂在 state.handshake 之后，ready 时才处理，不会丢。', 'Requests arriving during the handshake wait on state.handshake and run once ready: none are lost.'), 8.8, 450, cls='faint', layer='label')
    # failProtocol
    f.group(572, 228, 532, 130, 'err', 'failProtocol(state, error)', 'server.ts', 'shield', gid='fp')
    f.text(588, 276, ('stage = closing；把 hello_error { error } 编码成最后一帧，', 'stage = closing; encode hello_error { error } as the final frame,'), 9.0, 500, cls='strongt', layer='label')
    f.text(588, 294, ('connection.close(finalFrame) 发完它再关闭，然后 disconnect。', 'connection.close(finalFrame) sends it, then closes; then disconnect.'), 9.0, 500, cls='strongt', layer='label')
    f.text(588, 320, ('握手之后的协议错误（例如第二个 hello）也走这条路。', 'Protocol errors after the handshake (a second hello) take this path too.'), 8.8, 450, cls='muted', layer='label')
    f.text(588, 338, ('ProtocolValidationError → invalid_request。', 'ProtocolValidationError → invalid_request.'), 8.8, 450, cls='muted', layer='label')
    # disconnect
    f.group(572, 374, 532, 154, 'infra', ('disconnect(state)：只做一次', 'disconnect(state): runs once'), None, 'x', title_mono=False, gid='dc')
    DC = [('stage = closed，清掉握手定时器', 'stage = closed, clear the handshake timer'), ('abort 所有进行中的请求："Client disconnected"', 'abort every active request: "Client disconnected"'),
          ('清空订阅编码器；连接数变化 → onConnectionCountChanged', 'clear subscription encoders; onConnectionCountChanged'), ('sessions.disconnect() 与 serverServices.release() 并行', 'sessions.disconnect() and serverServices.release() in parallel')]
    for i, t in enumerate(DC):
        f.step(str(i + 1), 596, 420 + i * 26, 'infra')
        f.text(614, 424 + i * 26, t, 8.9, 500, cls='strongt', layer='label')
    f.text(16, 560, ('Server.close()：先关所有监听器，再把每个连接置为 closing 并关闭，最后 SessionRouter.close() 关闭所有托管的 Session。', 'Server.close(): close every listener, set each connection to closing and close it, then SessionRouter.close() closes every hosted Session.'), 9.4, 450, cls='muted', layer='label')
    f.legend(24, 598, [('main', ('前进', 'advance')), ('err', ('协议失败', 'protocol failure')), ('layer:coding', ('可以处理请求', 'serving requests')), ('layer:infra', ('清理', 'cleanup'))])
    return f

# ============================================================== srv_request : handleRequest
@reg
def srv_request():
    S_.has('server.ts', 'error: { code: "invalid_request", message: "Request ID is already active" },', 'error: { code: "invalid_request", message: "Invalid service call" },',
           'if (envelope.target.serverId !== this.serverId) throw new WrongServerError();', 'throw new ProtocolValidationError(`Duplicate service subscription ${subscribing.subscriptionId}`);',
           'result = await this.sessions.executeServiceCall(call, envelope.target, state, publish, context);', 'result = await state.serverServices.invokeService(call, publish, context);',
           'throw new ProtocolValidationError("Service subscription did not return a snapshot");', 'state.serviceStateEncoders.set(subscribing.subscriptionId, stateEncoder);',
           'pendingUpdates.push({ update });', '? { code: "cancelled", message: "RPC request cancelled" }', 'return { code: "internal_error", message: INTERNAL_SERVER_ERROR_MESSAGE };',
           'if (error instanceof ServerError || error instanceof RemoteServiceError) {', 'return { code: "invalid_request", message: error.message };',
           'if (envelope.target.serverId !== this.serverId) return;', 'if (active !== undefined && sameTarget(active.target, envelope.target)) {', 'state.serviceStateEncoders.delete(control.subscriptionId);')
    f = Fig('srv_request', 1120, 640, ('handleRequest：先核对，再路由到 Session 或服务器级服务，订阅的更新排在回应之后', 'handleRequest: check, route to a Session or server-wide services, and send subscription updates after the response'))
    f.group(16, 52, 580, 500, 'modes', 'handleRequest(state, envelope)', 'server.ts', 'msg', gid='hr')
    ST = [('activeRequests.has(id)', None, 'invalid_request'),
          ('parseServiceCall(envelope.call)', ('Chord 校验调用的形状', 'Chord checks the call\'s shape'), 'invalid_request'),
          ('activeRequests.set(id, { controller, target })', ('context = withAbortSignal(controller.signal)', 'context = withAbortSignal(controller.signal)'), None),
          ('target.serverId !== this.serverId', None, 'wrong_server'),
          (('订阅 id 已有编码器', 'subscription id already has an encoder'), None, 'invalid_request'),
          (('路由', 'Route'), ('"sessionId" in target ? sessions.executeServiceCall : serverServices.invokeService', '"sessionId" in target ? sessions.executeServiceCall : serverServices.invokeService'), None),
          (('订阅：必须返回快照', 'Subscribe: a snapshot is required'), ('encodeSnapshot，安装 ServiceStateEncoder', 'encodeSnapshot, install a ServiceStateEncoder'), None),
          (('发送回应，再冲刷 pendingUpdates', 'Send the response, then flush pendingUpdates'), ('之后的更新直接编码成 service_update', 'later updates go straight out as service_update'), None)]
    for i, (a, b, err) in enumerate(ST):
        y = 102 + i * 54
        f.step(str(i + 1), 40, y, 'modes')
        f.text(60, y + 4, a, 9.6, 600, isinstance(a, str), cls='strongt', layer='label')
        if b: f.text(60, y + 21, b, 8.6, 450, cls='muted', layer='label')
        if err: f.chip(462, y - 10, err, 'err', size=8.8, h=20)
    f.text(40, 538, ('finally：从 activeRequests 删掉自己（只删自己那一项）。', 'finally: remove its own entry from activeRequests.'), 8.8, 450, cls='faint', layer='label')
    # right: failures
    f.group(612, 52, 492, 196, 'err', ('失败时', 'On failure'), None, 'shield', title_mono=False, gid='fl')
    f.text(628, 100, ('还没回应：', 'Not yet responded:'), 9.4, 700, cls='strongt', layer='label')
    f.text(628, 118, ('response { ok: false, error }；已 abort → cancelled，否则 toProtocolError', 'response { ok: false, error }; aborted → cancelled, else toProtocolError'), 8.8, 450, cls='muted', layer='label')
    f.text(628, 146, ('已经回应（冲刷更新时出错）：', 'Already responded (failed while flushing):'), 9.4, 700, cls='strongt', layer='label')
    f.text(628, 164, ('onError，然后关闭这条连接——订阅流不能半途断掉', 'onError, then close the connection: a stream must not break halfway'), 8.8, 450, cls='muted', layer='label')
    f.text(628, 192, ('安装了编码器却没回应成功 → 移除编码器。', 'Encoder installed but no response → the encoder is removed.'), 8.8, 450, cls='muted', layer='label')
    f.text(628, 222, ('退订成功 → 删掉对应的编码器，之后的更新被丢弃。', 'A successful unsubscribe deletes the encoder; later updates are dropped.'), 8.8, 450, cls='muted', layer='label')
    f.group(612, 264, 492, 156, 'infra', 'toProtocolError(error)', 'server.ts', 'filter', gid='tp')
    TP = [('ServerError · RemoteServiceError', ('原样：code + message', 'as is: code + message')),
          ('ProtocolValidationError', ('invalid_request + message', 'invalid_request + message')),
          (('其它任何错误', 'anything else'), ('internal_error "Internal server error" + onError', 'internal_error "Internal server error" + onError'))]
    for i, (a, b) in enumerate(TP):
        y = 312 + i * 34
        f.text(628, y, a, 9.2, 600, isinstance(a, str), cls='strongt', layer='label')
        f.text(628, y + 16, b, 8.8, 450, cls='muted', layer='label')
    f.group(612, 436, 492, 116, 'coding', 'handleCancel(state, envelope)', 'server.ts', 'x', gid='hc')
    f.text(628, 482, ('serverId 不是本服务器 → 忽略；id 与 target 都相同 →', 'serverId of another server → ignored; same id and target →'), 8.8, 500, cls='strongt', layer='label')
    f.text(628, 500, ('controller.abort(AbortError)；处理器看到 abort 后回应 cancelled。', 'controller.abort(AbortError); the handler then answers cancelled.'), 8.8, 500, cls='strongt', layer='label')
    f.text(628, 526, ('取消从不单独回应：它只影响原请求的回应。', 'A cancel never gets its own response; it only shapes the original one.'), 8.8, 450, cls='muted', layer='label')
    f.text(16, 584, ('同一连接上的请求并发处理；只有 attach / detach 与 Session 调用的“准入”按连接串行（见 SessionRouter）。', 'Requests on one connection run concurrently; only attach / detach and the admission of Session calls are serialised per connection (see SessionRouter).'), 9.4, 450, cls='muted', layer='label')
    f.legend(24, 618, [('layer:modes', ('请求路径', 'request path')), ('layer:err', ('错误回应', 'error responses')), ('layer:infra', ('错误映射', 'error mapping')), ('layer:coding', ('取消', 'cancellation'))])
    return f

# ============================================================== srv_router : SessionRouter attach and admission
@reg
def srv_router():
    S_.has('session-router.ts', 'if (this.options.isClosing()) return Promise.reject(new ServerDrainingError());', 'const previous = this.clientOperations.get(client) ?? Promise.resolve();',
           'if (current?.session.id === sessionId) return;', 'const hosted = await this.acquire(sessionId, context);', 'if (current) await this.releaseAttachment(current, context, false);',
           'id: randomUUID(),', 'attachment.lease = await acquiring;', 'this.attachmentsByClient.set(client, attachment);', 'const opening = this.openingSessions.get(sessionId);',
           'const hosted: HostedSession = { id: metadata.id, handle, attachments: new Set() };', 'void handle.terminated.then(', 'throw new ServerDrainingError();',
           'if (!attachment || attachment.session.id !== target.sessionId || attachment.id !== target.attachmentId) {', 'this.trackOperation(attachment, result);', 'return admitted.result;',
           '"Failed to close routed Session acquired while draining",')
    doc(README, 'Repeating `attach` from one connection is idempotent')
    f = Fig('srv_router', 1120, 640, ('SessionRouter：按连接串行地 attach，按附着核对每个 Session 调用', 'SessionRouter: attach serialised per connection, every Session call checked against its attachment'))
    E = f.edge
    A = [('a1', 'attachClient(client, sessionId)', ('正在关闭 → ServerDrainingError', 'closing → ServerDrainingError'), 'modes'),
         ('a2', 'runForClient(client, op)', ('按连接排队：前一个操作结束后才开始', 'queued per connection: starts after the previous op'), 'modes'),
         ('a3', ('已附着同一个 Session？', 'Already attached to this Session?'), ('是 → 直接返回（幂等）', 'yes → return at once (idempotent)'), 'modes'),
         ('a4', 'acquire(sessionId)', ('已托管 → 正在打开 → open()', 'hosted → opening → open()'), 'ext'),
         ('a5', ('释放当前附着', 'Release the current attachment'), ('publish = false：新路由马上会推送', 'publish = false: the new route follows'), 'ext'),
         ('a6', 'handle.attachClient(ctx)', ('新附着 id = randomUUID()，拿到租约', 'new attachment id = randomUUID(), take the lease'), 'ext'),
         ('a7', 'publishAttachment(client, target)', ('attachment { serverId, sessionId, attachmentId }', 'attachment { serverId, sessionId, attachmentId }'), 'coding')]
    for i, (k, t, d, ly) in enumerate(A):
        f.node(k, 16, 60 + i * 72, 430, 52, ly, t, d, None, mono=isinstance(t, str), tsize=10.4, ssize=8.6, strong=(k == 'a6'))
        if i: E([(231, 60 + i * 72 - 20), (231, 60 + i * 72)], A[i - 1][0], k, 'main', ly)
    f.text(16, 586, ('拿到租约后再查一次：Session 已失效、连接已断或服务器在关闭 → 释放租约并 ServerDrainingError。', 'After the lease, check again: Session invalidated, client gone or server closing → release it and ServerDrainingError.'), 9.0, 450, cls='muted', layer='label')
    # right top: acquire/open
    f.group(476, 52, 628, 214, 'ext', 'acquire → open(sessionId)', 'session-router.ts', 'db', gid='op')
    OP = [('host.resolveSession(sessionId)', ('得到元数据；找不到 / 有歧义由应用抛 SessionNotFound / Ambiguous', 'metadata; the app throws SessionNotFound / Ambiguous')),
          ('host.openSession(metadata)', ('得到 RoutedSessionHandle；期间开始关闭 → handle.close() 并拒绝', 'a RoutedSessionHandle; closing meanwhile → handle.close() and reject')),
          ('hostedSessions.set(metadata.id, …)', ('并监听 handle.terminated → invalidate()', 'and watch handle.terminated → invalidate()'))]
    for i, (a, b) in enumerate(OP):
        y = 100 + i * 46
        f.step(str(i + 1), 498, y, 'ext')
        f.text(518, y + 4, a, 9.6, 600, True, cls='strongt', layer='label')
        f.text(518, y + 21, b, 8.6, 450, cls='muted', layer='label')
    f.text(498, 246, ('openingSessions 让并发的 attach 共享同一次打开；打开失败时所有人一起失败，之后可以重试。', 'openingSessions lets concurrent attaches share one open; a failure fails them all, and a later retry may succeed.'), 8.6, 450, cls='faint', layer='label')
    # right middle: session calls
    f.group(476, 282, 628, 176, 'coding', 'executeServiceCall(call, target, client, …)', 'session-router.ts', 'msg', gid='ex')
    EX = [('runForClient → requireAttachment', ('sessionId 与 attachmentId 都要等于本连接的当前附着', 'sessionId and attachmentId must equal this connection\'s attachment')),
          ('lease.invokeService(call, publish, ctx)', ('只在队列里“准入”；结果在队列外等待，所以调用可以并发', 'only admission is queued; the result is awaited outside, so calls run concurrently')),
          ('trackOperation(attachment, result)', ('释放附着前会等这些调用结算', 'release waits for these calls to settle'))]
    for i, (a, b) in enumerate(EX):
        y = 330 + i * 42
        f.step(str(i + 1), 498, y, 'coding')
        f.text(518, y + 4, a, 9.6, 600, True, cls='strongt', layer='label')
        f.text(518, y + 20, b, 8.6, 450, cls='muted', layer='label')
    chiprow(f, 498, 474, ['session_not_attached', 'server_draining'], 'err', size=9.0, h=20, gap=8)
    f.text(498, 512, ('不匹配、过期或服务器级 target → session_not_attached；关闭中或连接已断 → server_draining。', 'mismatched, stale or server-level target → session_not_attached; closing or client gone → server_draining.'), 8.6, 450, cls='muted', layer='label')
    # state
    f.text(498, 548, ('内部状态', 'Internal state'), 9.4, 700, cls='strongt', layer='label')
    chiprow(f, 498, 558, ['hostedSessions', 'openingSessions', 'attachmentsByClient', 'clientOperations'], 'infra', size=9.0, h=20, gap=8)
    f.legend(24, 620, [('layer:modes', ('排队', 'queueing')), ('layer:ext', ('Session 与租约', 'Session and lease')), ('layer:coding', ('路由', 'route')), ('layer:err', ('拒绝', 'rejections'))])
    return f

# ============================================================== srv_release : every way an attachment ends
@reg
def srv_release():
    S_.has('session-router.ts', 'attachment.releasing ??= (async () => {', 'await Promise.allSettled(attachment.operations);', 'const lease = attachment.lease ?? (await attachment.acquiring);',
           'if (lease) await lease.release(context);', 'if (publish) await this.options.publishAttachment(attachment.client, undefined, context);',
           'if (attachment) await this.releaseAttachment(attachment, context, false);', 'await hosted.handle.close(context);', 'const closeResults = await Promise.allSettled(hosted.map(({ handle }) => handle.close(context)));',
           'this.hostedSessions.delete(hosted.id);', 'throw new AggregateError(closeErrors, "Failed to close routed Sessions");')
    doc(README, 'Losing a connection rejects its local responses but releases its attachment only after admitted service calls settle.', 'Server shutdown closes every routed Session handle')
    f = Fig('srv_release', 1120, 600, ('一个附着结束的六种方式，共用同一条释放路径', 'Six ways an attachment ends, all through one release path'))
    E = f.edge
    f.group(16, 52, 356, 470, 'modes', ('触发', 'Triggers'), None, 'flag', title_mono=False, gid='tg')
    TG = [('detachSession()', ('推送 attachment: null', 'pushes attachment: null'), 'modes'),
          (('attach 另一个 Session', 'attach another Session'), ('不推送 null，随后推送新路由', 'no null; the new route follows'), 'modes'),
          (('连接断开', 'connection lost'), ('不推送（已经没有连接）', 'no push (no connection left)'), 'modes'),
          ('handle.terminated', ('invalidate：所有附着，推送 null', 'invalidate: every attachment, push null'), 'err'),
          ('prepareSessionRemoval()', ('所有附着 + handle.close()', 'every attachment + handle.close()'), 'ext'),
          ('Server.close()', ('全部附着 + 全部 handle.close()', 'all attachments + every handle.close()'), 'ext')]
    for i, (t, d, ly) in enumerate(TG):
        f.node(f't{i}', 32, 96 + i * 68, 324, 52, ly, t, d, None, mono=isinstance(t, str), tsize=10.4, ssize=8.6)
    # pipeline
    f.group(404, 52, 360, 470, 'ext', 'releaseAttachment(attachment)', None, 'loop', gid='rl')
    RL = [('r0', 'releasing ??= …', ('只释放一次；并发调用共享这个 Promise', 'released once; concurrent callers share the promise')),
          ('r1', 'allSettled(attachment.operations)', ('先等已准入的调用结算', 'wait for admitted calls to settle')),
          ('r2', 'lease.release(ctx)', ('租约仍在获取中 → 先等 acquiring', 'still acquiring → await it first')),
          ('r3', 'clearAttachment(…, publish)', ('从 Session 与连接上摘掉；publish 时推送 null', 'detach from Session and client; null if publish'))]
    for i, (k, t, d) in enumerate(RL):
        f.node(k, 420, 100 + i * 100, 328, 60, 'ext', t, d, None, mono=True, tsize=10.4, ssize=8.6, strong=(k == 'r1'))
        if i: E([(584, 100 + i * 100 - 40), (584, 100 + i * 100)], RL[i - 1][0], k, 'main', 'ext')
    f.text(420, 504, ('release 失败也一定 clearAttachment（finally）。', 'clearAttachment runs even if release fails (finally).'), 8.6, 450, cls='muted', layer='label')
    E([(372, 287), (404, 287)], 'tg', 'rl', 'main', 'modes')
    # right
    f.group(780, 52, 324, 230, 'infra', ('之后：Session 本身', 'Afterwards: the Session itself'), None, 'db', title_mono=False, gid='af')
    AF = [(('断开 / detach / 切换', 'drop / detach / switch'), ('Session 仍被托管；是否退役由应用决定', 'stays hosted; the app decides on retirement')),
          (('terminated', 'terminated'), ('从 hostedSessions 删掉；下次 attach 重新打开', 'removed from hostedSessions; reopened on next attach')),
          (('删除 / 关闭服务器', 'removal / shutdown'), ('handle.close()：释放 worker 与写入权', 'handle.close(): frees the worker and writer'))]
    for i, (a, b) in enumerate(AF):
        y = 100 + i * 58
        f.text(796, y, a, 9.4, 700, cls='strongt', layer='label')
        f.text(796, y + 18, b, 8.6, 450, cls='muted', layer='label')
    f.group(780, 298, 324, 224, 'err', ('关闭服务器时', 'On shutdown'), 'SessionRouter.close()', 'shield', title_mono=False, gid='sd')
    SD = [('等进行中的连接操作和打开', 'wait for client ops and opens'), ('释放每个 Session 的每个附着', 'release every attachment'), ('关闭每个 handle', 'close every handle'), ('有失败 → AggregateError', 'failures → AggregateError')]
    for i, t in enumerate(SD):
        f.step(str(i + 1), 802, 346 + i * 30, 'err')
        f.text(820, 350 + i * 30, t, 9.0, 500, cls='strongt', layer='label')
    f.text(796, 480, ('Server.closed 因此 reject。', 'so Server.closed rejects.'), 8.6, 450, cls='muted', layer='label')
    f.text(16, 552, ('README：连接断开时，本地的回应立即拒绝，但附着要等已准入的服务调用结算后才释放。', 'README: losing a connection rejects its local responses, but the attachment is released only after admitted service calls settle.'), 9.4, 450, cls='muted', layer='label')
    f.legend(24, 584, [('layer:modes', ('连接触发', 'connection triggers')), ('layer:err', ('Session 失效', 'Session failure')), ('layer:ext', ('释放与关闭', 'release and close'))])
    return f

# ============================================================== srv_unix : the Unix listener
@reg
def srv_unix():
    import hashlib
    U_ = Pkg('packages/server/src/transports/unix/')
    assert U_.num('listener.ts', 'DEFAULT_GRACEFUL_CLOSE_TIMEOUT_MS') == 5000 and U_.num('listener.ts', 'SOCKET_PROBE_TIMEOUT_MS') == 1000
    assert re.search(r'const DEFAULT_SOCKET_MODE = 0o600;', U_.src('listener.ts'))
    U_.has('listener.ts', 'await mkdir(dirname(this.path), { recursive: true, mode: 0o700 });', 'await removeStaleSocket(this.path);\n\t\tawait removeStaleSocket(ownedBindPath);',
           'server.listen(ownedBindPath);', 'this.socketIdentity = { dev: stats.dev, ino: stats.ino };', 'await link(ownedBindPath, this.path);', 'await setSocketMode(this.path, this.mode);',
           'await removePath(ownedBindPath);', 'const suffix = createHash("sha256").update(path).digest("hex").slice(0, 8);', 'return join(dirname(path), `bind-${suffix}`);',
           'throw new Error(`Refusing to remove non-socket Unix listener path: ${path}`);', 'throw new Error(`Unix listener is already running: ${path}`);',
           'timer = setTimeout(() => finish(true), SOCKET_PROBE_TIMEOUT_MS);', 'const preserved = join(dirname(path), `stale-${randomUUID().slice(0, 6)}`);',
           'if (!current.isSocket() || current.dev !== identity.dev || current.ino !== identity.ino) return;', 'const preserved = join(dirname(this.path), `cleanup-${randomUUID().slice(0, 6)}`);',
           'const maxPendingBytes = options.maxPendingBytes ?? maxFrameLength * 4;', 'maxPendingBytes < maxFrameLength + 4', 'if (finalBytes) this.socket.end(finalBytes);')
    U_.has('address.ts', 'return join(serverDirectory, `${serverId}.sock`);')
    doc(README, 'peer authentication remains application policy and is not implemented by the experimental Unix transport.', 'getUnixSocketPath(serverId, "/run/user/1000/pi")')
    U_.has('types.ts', '/** Maximum framed bytes queued per connection before a slow peer is disconnected. */')
    sid = '0f8fad5b-d9cb-469f-a165-70867728950e'; d = '/run/user/1000/pi'
    pub = f'{d}/{sid}.sock'; bind = 'bind-' + hashlib.sha256(pub.encode()).hexdigest()[:8]
    f = Fig('srv_unix', 1120, 620, ('Unix 监听器：先绑到私有路径，再用硬链接原子地发布，关闭时只删自己的 socket', 'The Unix listener: bind privately, publish atomically with a hard link, remove only its own socket'))
    E = f.edge
    f.group(16, 52, 600, 420, 'coding', 'UnixListener.start(accept)', 'transports/unix/listener.ts', 'play', gid='st')
    ST = [('mkdir(dir, { recursive, mode: 0o700 })', ('私有目录', 'a private directory')),
          ('removeStaleSocket(path) · (bindPath)', ('不是 socket → 拒绝；还活着 → "already running"', 'not a socket → refuse; alive → "already running"')),
          ('listen(bindPath)', ('bind-<sha256(path) 前 8 位>，与公共路径同目录', 'bind-<first 8 hex of sha256(path)>, same directory')),
          ('lstat(bindPath) → { dev, ino }', ('记住自己 socket 的身份', 'remember the identity of its own socket')),
          ('link(bindPath, path)', ('硬链接发布：原子，且目标已存在时失败', 'publish by hard link: atomic, fails if the target exists')),
          ('chmod(path, 0o600)', ('只有属主能连接（Windows 上跳过）', 'owner-only connections (skipped on Windows)')),
          ('unlink(bindPath)', ('只留下公共路径', 'only the public path remains'))]
    for i, (a, b) in enumerate(ST):
        y = 100 + i * 50
        f.step(str(i + 1), 40, y, 'coding')
        f.text(60, y + 4, a, 9.6, 600, True, cls='strongt', layer='label')
        f.text(60, y + 20, b, 8.6, 450, cls='muted', layer='label')
    f.text(40, 456, ('任何一步失败：关闭 net.Server，删掉未发布的 bind 路径，再按身份清理。', 'Any step fails: close the net.Server, remove the unpublished bind path, clean up by identity.'), 8.6, 450, cls='faint', layer='label')
    # right: example directory
    f.group(632, 52, 472, 196, 'infra', ('例子：README 的目录', 'Example: the README\'s directory'), None, 'file', title_mono=False, gid='ex')
    codebox(f, 648, 92, 440, [(0, d + '/', 'strongt'),
                              (1, bind, ''),
                              (1, sid + '.sock', 'strongt'),
                              (0, ('// ⑤ link 之后两者是同一个 inode，⑦ 删掉 bind', '// ⑤ after link both are one inode; ⑦ drops bind'), 'muted'),
                              (0, ('// getUnixSocketPath(serverId, dir)', '// getUnixSocketPath(serverId, dir)'), 'muted')], None, size=9.4, lh=17)
    f.text(648, 232, (f'{bind} = sha256("{d}/<id>.sock") 的前 8 位（构建时计算）', f'{bind} = first 8 hex of sha256 of the public path (computed at build time)'), 8.4, 450, cls='faint', layer='label')
    # stale check
    f.group(632, 264, 472, 208, 'ext', 'removeStaleSocket / isSocketLive', None, 'eye', gid='sc')
    SC = [(('连得上', 'connects'), ('活着 → 拒绝启动', 'alive → refuse to start')),
          (('1000 ms 没反应', 'no answer in 1000 ms'), ('也当作活着（宁可不删）', 'treated as alive too (never delete)')),
          ('ECONNREFUSED · ENOENT · …', ('陈旧：改名 stale-xxxxxx，核对 dev/ino 后才 unlink', 'stale: rename to stale-xxxxxx, unlink after a dev/ino check'))]
    for i, (a, b) in enumerate(SC):
        y = 310 + i * 48
        f.text(648, y, a, 9.4, 700, isinstance(a, str), cls='strongt', layer='label')
        f.text(648, y + 18, b, 8.6, 450, cls='muted', layer='label')
    f.text(648, 456, ('改名期间路径被换掉 → 换回去并报错。', 'If the path changed meanwhile, put it back and fail.'), 8.6, 450, cls='faint', layer='label')
    # bottom: close and connection
    f.group(16, 488, 600, 84, 'err', ('close()：只删自己的 socket', 'close(): remove only its own socket'), None, 'x', title_mono=False, gid='cl')
    f.text(32, 534, ('lstat(path) 的 dev/ino 等于记下的身份 → 改名 cleanup-xxxxxx → 再核对 → unlink；', 'lstat(path) dev/ino equals the remembered identity → rename to cleanup-xxxxxx → recheck → unlink;'), 8.8, 500, cls='strongt', layer='label')
    f.text(32, 552, ('否则保留（可能是接替它的新服务器的 socket）。', 'otherwise leave it (it may belong to the server that replaced this one).'), 8.8, 450, cls='muted', layer='label')
    f.group(632, 488, 472, 84, 'modes', 'UnixByteConnection', None, 'queue', gid='bc')
    f.text(648, 534, ('maxPendingBytes 默认 4 × 帧上限，且必须 ≥ 帧上限 + 4；超过 → 断开慢的对端。', 'maxPendingBytes: 4 × the frame limit by default, ≥ limit + 4; beyond → drop the slow peer.'), 8.6, 500, cls='strongt', layer='label')
    f.text(648, 552, ('close(final)：写完队列，end(final)；5000 ms 后强制 destroy。', 'close(final): drain the queue, end(final); force destroy after 5000 ms.'), 8.6, 450, cls='muted', layer='label')
    f.text(16, 596, ('README：对端认证是应用的策略，实验性的 Unix 传输不做认证——依靠 0700 目录与 0600 socket 的文件权限。', 'README: peer authentication is application policy and not implemented by the experimental Unix transport; it relies on 0700 / 0600 file permissions.'), 9.2, 450, cls='muted', layer='label')
    return f

# ============================================================== srv_errors : error codes and the testing kit
@reg
def srv_errors():
    e = S_.src('errors.ts')
    ER = re.findall(r'export class (\w+) extends ServerError \{\n\tconstructor\((?:message = "([^"]+)")?\) \{\n\t\tsuper\("(\w+)", (?:"([^"]+)"|message)\);', e)
    assert [x[0] for x in ER] == ['WrongServerError', 'SessionNotFoundError', 'SessionAmbiguousError', 'SessionNotAttachedError', 'ServerDrainingError'], ER
    S_.has('errors.ts', 'export class ServerError extends Error {', '| RemoteServiceErrorCode')
    rc = re.findall(r'^\t"(\w+)",$', (SRC / 'packages/chord/src/services/errors.ts').read_text(), re.M); assert len(rc) == 8, rc
    T_ = Pkg('packages/server/test/')
    tests = {p: len(re.findall(r'^\s*test\(', T_.src(p), re.M)) for p in ['conformance.test.ts', 'protocol.test.ts', 'server.test.ts', 'unix.test.ts', 'listener.test.ts', 'unix-connection.test.ts']}
    assert sum(tests.values()) == 41, tests
    S_.has('testing/index.ts', 'export { connectUnixTestClient, ProtocolTestClient } from "./client.ts";', 'export { createTestServerServices, Deferred, TestHarness, TestServerHost } from "./host.ts";', 'export { createTestServer } from "./server.ts";')
    S_.has('testing/server.ts', 'serverId: options.serverId ?? "00000000-0000-4000-8000-000000000001",', '/** Create an unstarted Server with deterministic defaults for transport conformance tests. */')
    WH = {'WrongServerError': ('handleRequest：在访问任何仓库之前', 'handleRequest: before any repository access'),
          'SessionNotFoundError': ('应用的 resolveSession 抛出', 'thrown by the app\'s resolveSession'),
          'SessionAmbiguousError': ('应用的 resolveSession 抛出（一个 id 对应多个）', 'thrown by the app\'s resolveSession (one id, several)'),
          'SessionNotAttachedError': ('requireAttachment：路由不匹配或已过期', 'requireAttachment: mismatched or stale route'),
          'ServerDrainingError': ('关闭中 attach / 调用 / 删除，或连接已断', 'attach / call / removal while closing, or client gone')}
    f = Fig('srv_errors', 1120, 640, ('能越过协议边界的错误，以及 ./testing 里的测试工具', 'Errors that may cross the protocol boundary, and the ./testing kit'))
    f.group(16, 52, 680, 420, 'err', ('ServerError 的子类（errors.ts）', 'ServerError subclasses (errors.ts)'), None, 'shield', title_mono=False, gid='er')
    f.text(32, 106, ('类', 'Class'), 9.0, 650, cls='faint', layer='label', ls='.04em')
    f.text(230, 106, 'code', 9.0, 650, True, cls='faint', layer='label')
    f.text(400, 106, ('在哪里产生', 'Where it arises'), 9.0, 650, cls='faint', layer='label', ls='.04em')
    hline(f, 32, 680, 114)
    for i, (cls_, dmsg, code, msg) in enumerate(ER):
        y = 138 + i * 56
        f.text(32, y, cls_, 9.6, 650, True, cls='strongt', layer='label')
        f.text(32, y + 18, '"' + (msg or dmsg) + '"', 8.4, 450, True, cls='muted', layer='label')
        f.chip(230, y - 14, code, 'err', size=8.8, h=20)
        f.text(400, y, WH[cls_], 8.8, 450, cls='strongt', layer='label')
    f.text(32, 428, ('应用也可以直接 throw new ServerError(code, message)：code 还可以是 Chord 的 %d 个 RemoteServiceErrorCode 之一。' % len(rc), 'Apps may also throw new ServerError(code, message); code may also be one of Chord\'s %d RemoteServiceErrorCodes.' % len(rc)), 8.8, 450, cls='muted', layer='label')
    f.text(32, 450, ('其它任何异常 → internal_error "Internal server error"，细节只交给 onError。', 'Anything else → internal_error "Internal server error"; details go only to onError.'), 8.8, 450, cls='muted', layer='label')
    # right: testing kit
    f.group(712, 52, 392, 420, 'infra', ('./testing：测试工具', './testing: the testing kit'), 'src/testing', 'check', title_mono=False, gid='tk')
    TK = [('createTestServer(options)', ('未启动的 Server，默认 serverId …0001', 'an unstarted Server, default serverId …0001')),
          ('TestServerHost', ('内存 ServerHost', 'an in-memory ServerHost')),
          ('TestHarness · createTestServerServices', ('假的 Session 与服务器级服务', 'fake Sessions and server-wide services')),
          ('ProtocolTestClient', ('按帧收发、断言的协议客户端', 'a frame-level client for assertions')),
          ('connectUnixTestClient(path)', ('经真实 Unix socket 连接', 'connect over a real Unix socket')),
          ('Deferred<T>', ('手动控制时序', 'control timing by hand'))]
    for i, (a, b) in enumerate(TK):
        y = 110 + i * 52
        f.text(728, y, a, 9.6, 600, True, cls='strongt', layer='label')
        f.text(728, y + 18, b, 8.6, 450, cls='muted', layer='label')
    f.text(728, 432, ('传输实现可以拿它跑同一套一致性测试。', 'Transport implementations can run the same conformance tests.'), 8.6, 450, cls='faint', layer='label')
    # bottom: tests
    f.text(16, 506, ('测试（共 %d 个 test）' % sum(tests.values()), 'Tests (%d test cases)' % sum(tests.values())), 9.6, 700, cls='strongt', layer='label')
    x = 16
    for p, n in tests.items():
        lab = f'{p.replace(".test.ts", "")} · {n}'
        f.chip(x, 518, lab, 'infra', size=9.0, h=20)
        x += int(len(lab) * 5.6 + 28)
    f.text(16, 568, ('conformance.test.ts 覆盖多附着、过期路由、跨服务器请求、未知 / 有歧义的 Session、Harness 终止与重开、关闭时的清理失败。', 'conformance.test.ts covers multiple attachments, stale routes, cross-server requests, unknown / ambiguous Sessions, Harness termination and reopening, and cleanup failures on shutdown.'), 9.0, 450, cls='muted', layer='label')
    f.legend(24, 616, [('layer:err', ('错误', 'errors')), ('layer:infra', ('测试', 'testing'))])
    return f
