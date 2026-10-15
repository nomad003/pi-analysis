"""pi-env deep-dive diagrams (env_*). Facts read from /workspace/pi-src/packages/env at build time."""
import re
from svgkit import Fig, maxw, pair
from figs import reg
from figkit import SRC, uml, codebox, bar, dot, hline, vline, chiprow, lines_of
from pkgsrc import Pkg, MiB

E_ = Pkg('packages/env/src/')
R_ = Pkg('packages/env/daemon/src/')
PROTO = (SRC / 'packages/env/docs/protocol.md').read_text()
SEM = (SRC / 'packages/env/docs/semantics.md').read_text()
ENVREADME = (SRC / 'packages/env/README.md').read_text()

def doc(text, *needles):
    for n in needles: assert n in text, n

# ============================================================== env_arch
@reg
def env_arch():
    ts, rs = E_.total(), R_.total(ext=('.rs',))
    deps = E_.pkg()['dependencies']
    assert list(E_.exports()) == ['.'], E_.exports()
    assert 'bin' in E_.pkg()['files']
    f = Fig('env_arch', 1120, 600, (f'pi-env：{ts:,} 行 TypeScript 客户端 + {rs:,} 行 Rust 守护进程', f'pi-env: a {ts:,}-line TypeScript client + a {rs:,}-line Rust daemon'))
    E = f.edge
    f.group(16, 52, 520, 360, 'modes', ('本地：Durable worker 所在的机器', 'Local: where the Durable worker runs'), 'src/*.ts', 'monitor', title_mono=False, gid='l')
    TSF = [('remote-env.ts', ('RemoteExecutionEnv：实现 Durable 的 ExecutionEnv', 'RemoteExecutionEnv: a Durable ExecutionEnv')),
           ('ssh.ts', ('主机密钥 · 探测平台 · 部署 · 启动', 'host keys · detect · deploy · launch')),
           ('connection.ts', ('Connection：帧、请求 id、心跳、重连', 'Connection: frames, request ids, ping, restart')),
           ('watch.ts', ('RemoteWatcher：断线后重新打开', 'RemoteWatcher: reopens after a lost link')),
           ('errors.ts', ('toFileError：错误码映射', 'toFileError: error-code mapping')),
           ('index.ts', ('公开 API', 'public API'))]
    for i, (p, d) in enumerate(TSF):
        f.node(f't{i}', 32, 96 + i * 50, 488, 42, 'modes', p, d, None, tsize=10.8, ssize=9.2, tag=f'{E_.loc(p):,}', strong=(i in (0, 1)))
    f.group(584, 52, 520, 360, 'infra', ('远端：工具真正运行的机器', 'Remote: where the tools actually run'), 'daemon/src/*.rs', 'cpu', title_mono=False, gid='r')
    RSF = [('main.rs', ('serve：同步行、调度、工作线程', 'serve: sync line, scheduling, workers')), ('watch.rs', ('NodeFileWatcher 的移植', 'a port of NodeFileWatcher')),
           ('exec.rs', ('命令、进程组、超时、溢出文件', 'commands, process groups, timeouts, spill')), ('window.rs', ('输出窗口与节流', 'output window and pacing')),
           ('fs.rs · scan.rs', ('文件操作 · 行扫描', 'file ops · line scans')), ('sys/unix.rs · sys/windows.rs', ('平台差异', 'platform specifics'))]
    for i, (p, d) in enumerate(RSF):
        loc = sum(R_.loc(x.strip()) for x in p.split('·'))
        f.node(f'r{i}', 600, 96 + i * 50, 488, 42, 'infra', p, d, None, tsize=10.8, ssize=9.2, tag=f'{loc:,}', strong=(i == 0))
    E([(536, 200), (584, 200)], 'l', 'r', 'main', 'modes', label='ssh', lpos=(560, 186))
    E([(584, 240), (536, 240)], 'r', 'l', 'event', 'infra')
    f.text(560, 264, 'stdin/stdout', 8.8, 500, True, cls='faint', layer='label', anchor='middle')
    f.group(16, 428, 1088, 128, 'infra', ('包与平台', 'Package and platforms'), None, 'box', title_mono=False, gid='p')
    x = 32
    x += f.chip(x, 470, '@earendil-works/pi-env', 'modes', size=9.8, h=22) + 10
    for k, v in deps.items():
        x += f.chip(x, 470, f'{k.replace("@earendil-works/", "")} {v}', 'infra', size=9.8, h=22) + 6
    x += 10
    f.text(x, 485, ('随包附带 bin/pi-env-{platform}-{arch}/pi-env', 'ships bin/pi-env-{platform}-{arch}/pi-env'), 9.6, 600, True, cls='faint', layer='label')
    x = 32
    for p in ['Linux', 'macOS', 'Android (Termux)', 'Windows', 'x86-64', 'arm64']:
        x += f.chip(x, 508, p, 'ext', size=9.8, h=22) + 6
    f.text(x + 10, 523, ('README：Durable worker、存储与凭据留在本地', 'README: the Durable worker, storage and credentials stay local'), 9.6, 450, cls='muted', layer='label')
    doc(ENVREADME, 'while the Durable worker, its storage and credentials stay local', 'Supported remote systems: Linux, macOS, Android (Termux) and Windows, on x86-64 and arm64.')
    f.legend(24, 580, [('layer:modes', ('本地 TypeScript', 'local TypeScript')), ('layer:infra', ('远端 Rust', 'remote Rust')), ('main', ('请求', 'requests')), ('event', ('结果与事件', 'results & events'))])
    f.note(1096, 580, ('标签 = 行数', 'tag = lines'), 10.5, anchor='end')
    return f

# ============================================================== env_split : who does what
@reg
def env_split():
    doc(SEM, 'The reference is Durable\'s `NodeExecutionEnv`', '| Path resolution:', '| Abort checkpoints of each method | client', '| Error code mapping (`ENOENT` → `not_found`, ...) | client',
        '| Watching: snapshots, native events, polling | daemon', '| System calls, processes, spill files, line scans | daemon', 'daemon (`encoding_rs`)', '`writeFile` in 512 KiB writes')
    f = Fig('env_split', 1120, 560, ('分工：结果要和远端机器上的 NodeExecutionEnv 一致', 'Split of work: results must match NodeExecutionEnv on the remote machine'))
    f.group(16, 52, 536, 400, 'modes', ('客户端（TypeScript，本地）', 'Client (TypeScript, local)'), None, 'monitor', title_mono=False, gid='c')
    C = [(('路径解析', 'Path resolution'), ('~（远端 home）、file://、相对 cwd；Windows 驱动器相对路径', '~ (remote home), file://, relative to cwd; Windows drive-relative')),
         (('取消检查点', 'Abort checkpoints'), ('每个方法的检查点与 NodeExecutionEnv 相同', 'each method\'s checkpoints, as NodeExecutionEnv')),
         (('错误码映射', 'Error-code mapping'), ('ENOENT → not_found …（toFileError）', 'ENOENT → not_found … (toFileError)')),
         (('readFile 的分块与解码', 'readFile chunking & decoding'), ('StringDecoder，保留 BOM', 'StringDecoder, BOM kept')),
         (('writeFile', 'writeFile'), ('512 KiB 一块，每块前检查取消', '512 KiB writes, abort check before each')),
         (('行读取器', 'Line reader'), ('定位读取 + Durable 的 StreamDecoder', 'positional reads + Durable\'s StreamDecoder')),
         (('超时与结果优先级', 'Timeouts & result precedence'), ('回调错误 > 超时 > 取消 > 溢出失败 > 退出码', 'callback error > timeout > abort > spill failure > exit code'))]
    for i, (a, b) in enumerate(C):
        y = 96 + i * 50
        f.text(32, y + 8, a, 10.2, 650, cls='strongt', layer='label')
        f.text(32, y + 26, b, 9.2, 450, cls='muted', layer='label')
        if i: hline(f, 32, 536, y - 8)
    f.group(568, 52, 536, 400, 'infra', ('守护进程（Rust，远端）', 'Daemon (Rust, remote)'), None, 'cpu', title_mono=False, gid='d')
    Dm = [(('系统调用', 'System calls'), ('lstat、open、pread、rename、rm …', 'lstat, open, pread, rename, rm …')),
          (('进程', 'Processes'), ('每条命令一个新会话（进程组）', 'a new session (process group) per command')),
          (('溢出文件', 'Spill files'), ('pi-output-<uuid>.log，在新的 tmp- 目录里', 'pi-output-<uuid>.log in a fresh tmp- directory')),
          (('行扫描', 'Line scans'), ('scanLines：在文件旁边数行', 'scanLines: counted next to the file')),
          (('输出解码', 'Output decoding'), ('每个流独立，WHATWG UTF-8（encoding_rs）', 'per stream, WHATWG UTF-8 (encoding_rs)')),
          (('文件监视', 'Watching'), ('快照、原生事件、轮询：NodeFileWatcher 的移植', 'snapshots, native events, polling: a NodeFileWatcher port'))]
    for i, (a, b) in enumerate(Dm):
        y = 96 + i * 50
        f.text(584, y + 8, a, 10.2, 650, cls='strongt', layer='label')
        f.text(584, y + 26, b, 9.2, 450, cls='muted', layer='label')
        if i: hline(f, 584, 1088, y - 8)
    f.text(16, 480, ('两边由 Durable 的 env 一致性套件和 test/differential.test.ts 一起检查：随机操作序列在 RemoteExecutionEnv 与本机 NodeExecutionEnv 上比对。', 'Both sides are checked by Durable\'s env conformance suite and test/differential.test.ts: random operation sequences compared with NodeExecutionEnv.'), 9.5, 450, cls='muted', layer='label')
    f.text(16, 502, ('只有错误消息可以不同；错误码才是契约。', 'Only error messages may differ; codes are the contract.'), 9.5, 600, cls='strongt', layer='label')
    f.legend(24, 540, [('layer:modes', ('客户端', 'client')), ('layer:infra', ('守护进程', 'daemon'))])
    return f

# ============================================================== env_ssh : connect & deploy
@reg
def env_ssh():
    s = E_.src('ssh.ts')
    OPTS = re.findall(r'option\("([A-Za-z0-9]+=[^"$]+)"\)', s)
    for o in ['BatchMode=yes', 'ClearAllForwardings=yes', 'ForwardAgent=no', 'ForwardX11=no', 'ControlMaster=no', 'ControlPath=none', 'RemoteCommand=none', 'SendEnv=-*', 'ServerAliveInterval=15']:
        assert o in OPTS, (o, OPTS)
    E_.has('ssh.ts', 'StrictHostKeyChecking=${strictHostKeys ? "yes" : "accept-new"}', 'UserKnownHostsFile=', 'HostKeyAlias=${target.hostKeyAlias}',
           'const name = `pi-env-${sha256.slice(0, 32)}`;', '/.pi/mobile/tools/${name}', 't=$(mktemp "$d/.pi-env.XXXXXX")', 'chmod 700 "$t"', 'mv -f "$t" "$f"',
           'for old in "$d"/pi-env-*; do [ "$old" = "$f" ] || rm -f "$old"; done', 'echo nohash', 'uname -s; uname -m',
           'export async function scanHostKey(', 'export async function acceptHostKey(', 'export async function forgetHostKey(', 'export function sshConnection(', 'export async function connectSsh(')
    f = Fig('env_ssh', 1120, 620, ('通过 SSH 连上一台机器：信任 → 探测 → 部署 → 启动', 'Reaching a machine over SSH: trust → detect → deploy → start'))
    E = f.edge
    S = [('scanHostKey', ('用临时 known_hosts 抓取主机密钥，给用户比对指纹', 'capture the host key with a temp known_hosts; owner checks fingerprints'), 'shield'),
         ('acceptHostKey', ('写进应用自己的 known_hosts，固定别名', 'store it in the app\'s own known_hosts, under a fixed alias'), 'key'),
         ('detectPlatform', ('POSIX：sh -c uname …；Windows：PowerShell', 'POSIX: sh -c uname …; Windows: PowerShell'), 'eye'),
         ('deployDaemon', ('按 SHA-256 命名、校验后才放到位', 'named by SHA-256, verified before it is put in place'), 'box'),
         ('pi-env serve --token <hex>', ('经 ssh 启动；等到 "PI-ENV <token>" 这一行', 'started over ssh; wait for the "PI-ENV <token>" line'), 'play')]
    for i, (t, d, ic) in enumerate(S):
        y = 64 + i * 72
        f.node(f's{i}', 52, y, 470, 56, 'modes' if i < 2 else 'infra', t, d, ic, tsize=11.5, ssize=9.2, strong=(i == 3))
        f.step(str(i + 1), 30, y + 28, 'modes' if i < 2 else 'infra')
        if i: E([(287, y - 16), (287, y)], f's{i-1}', f's{i}', 'main', 'infra')
    f.text(52, 440, ('connectSsh()：立即探测与部署（3–4），守护进程在第一个请求时启动；sshConnection()：全部懒执行，', 'connectSsh(): detects and deploys now (3–4), the daemon starts on the first request; sshConnection(): all lazily;'), 9.4, 450, cls='muted', layer='label')
    f.text(52, 458, ('失败就是该操作的错误，下一次操作再试。forgetHostKey() 删除已存的密钥。', 'a failure is that operation\'s error and the next one retries. forgetHostKey() removes a key.'), 9.4, 450, cls='muted', layer='label')
    # deploy detail
    f.group(548, 52, 556, 252, 'infra', ('deployDaemon 的细节（POSIX）', 'deployDaemon in detail (POSIX)'), 'src/ssh.ts', 'box', title_mono=False, gid='dp')
    codebox(f, 564, 92, 524, [(0, ('f=~/.pi/mobile/tools/pi-env-{sha256 前 32 位}', 'f=~/.pi/mobile/tools/pi-env-{first 32 of sha256}'), 'strongt'),
                              (0, ('# 检查：present → 直接用 · missing → 上传 · nohash → 报错', '# check: present → use it · missing → upload · nohash → error'), 'muted'),
                              (0, 't=$(mktemp "$d/.pi-env.XXXXXX"); cat > "$t"', ''),
                              (0, ('[ "$(hash "$t")" = {sha256} ] || 删除并报 corrupt', '[ "$(hash "$t")" = {sha256} ] || rm, "upload is corrupt"'), ''),
                              (0, 'chmod 700 "$t"; mv -f "$t" "$f"', ''),
                              (0, ('# 删除其他 pi-env-*（运行中的保持打开直到退出）', '# remove other pi-env-* (running ones stay open until exit)'), 'muted')], None)
    f.text(564, 290, ('hash 依次尝试 sha256sum、shasum、openssl；Windows 用 Get-FileHash 与 base64 上传。', 'hash tries sha256sum, shasum, openssl; Windows uses Get-FileHash and a base64 upload.'), 9.0, 450, cls='faint', layer='label')
    # ssh args
    f.group(548, 320, 556, 236, 'modes', ('sshArguments()：每次调用都锁死这些选项', 'sshArguments(): these options on every call'), None, 'shield', title_mono=False, gid='ar')
    x, y = 564, 362
    for o in OPTS + ['StrictHostKeyChecking=yes', 'UserKnownHostsFile=<app file>', 'HostKeyAlias=<alias>']:
        w = maxw(o, 9.4, 500, True) + 16
        if x + w > 1092: x, y = 564, y + 28
        x += f.chip(x, y, o, 'modes', size=9.4, h=22) + 6
    f.text(564, y + 48, ('不转发任何东西、不复用连接、不执行配置的命令、不发送本地 locale。', 'No forwarding of any kind, no shared connections, no configured commands, no local locale.'), 9.2, 450, cls='muted', layer='label')
    f.text(564, y + 66, ('accept-new 只在 scanHostKey 的临时文件里使用。', 'accept-new is used only against scanHostKey\'s temporary file.'), 9.2, 450, cls='muted', layer='label')
    f.legend(24, 596, [('layer:modes', ('信任', 'trust')), ('layer:infra', ('部署与启动', 'deploy & start')), ('main', ('顺序', 'order'))])
    return f

# ============================================================== env_frames : wire format
@reg
def env_frames():
    T = {E_.num('connection.ts', n): n for n in ['REQUEST', 'RESULT', 'ERROR', 'EVENT', 'CANCEL', 'PING']}
    assert sorted(T) == [1, 2, 3, 4, 5, 6], T
    for n, v in [('REQUEST', 1), ('RESULT', 2), ('ERROR', 3), ('EVENT', 4), ('CANCEL', 5), ('PING', 6)]:
        R_.has('frame.rs', f'pub const {n}: u8 = {v};')
    mf = E_.num('connection.ts', 'MAX_FRAME'); assert mf == 16 * 1024 * 1024
    doc(PROTO, 'All integers are big-endian. A frame is at most 16 MiB', '`PI-ENV <token>\\n`', 'u32 length      bytes after this field', 'u8  type', 'u32 id', 'u32 jsonLength')
    f = Fig('env_frames', 1120, 580, ('线上格式：同步行之后只有帧', 'The wire format: after the sync line, only frames'))
    # sync
    f.group(16, 52, 1088, 104, 'modes', ('同步', 'Sync'), None, 'play', title_mono=False, gid='sy')
    x = 32
    for t, lay, w in [(('shell 启动文件可能打印的杂项…', 'whatever shell startup files print…'), 'infra', 300), ('PI-ENV 3f9a…c1\\n', 'modes', 200), ('frame', 'coding', 110), ('frame', 'coding', 110), ('frame …', 'coding', 110)]:
        f.node(f'y{x}', x, 94, w, 40, lay, t, None, None, mono=not isinstance(t, tuple), tsize=10.2, strong=(lay == 'modes'))
        x += w + 8
    f.text(908, 112, ('客户端丢弃同步行之前的', 'The client discards'), 9.2, 450, cls='muted', layer='label')
    f.text(908, 128, ('一切输出', 'everything before it'), 9.2, 450, cls='muted', layer='label')
    # frame layout
    f.group(16, 172, 1088, 160, 'coding', ('一帧（两个方向都一样，大端序，最多 16 MiB）', 'One frame (both directions, big-endian, at most 16 MiB)'), None, 'stack', title_mono=False, gid='fr')
    FL = [('u32', 'length', ('之后的字节数', 'bytes after this field'), 130), ('u8', 'type', ('1–6', '1–6'), 100), ('u32', 'id', ('请求 id；0 = 不属于请求', 'request id; 0 = none'), 190),
          ('u32', 'jsonLength', '', 130), ('UTF-8', 'json', ('JSON 对象', 'a JSON object'), 220), ('raw', 'bytes', ('文件内容 / 输出', 'file contents / output'), 270)]
    x = 32
    for k, n, d, w in FL:
        f.node(f'f{n}', x, 214, w - 4, 52, 'coding', n, d if d else None, None, tsize=11, ssize=9, strong=(n == 'type'))
        f.text(x + 6, 284, k, 9.2, 600, True, cls='faint', layer='label')
        x += w
    f.text(32, 312, ('bytes 长度 = length − 9 − jsonLength；JSON 解析失败 → EINVAL；帧格式错误 → 断开连接。', 'bytes length = length − 9 − jsonLength; unparsable JSON → EINVAL; a framing error ends the connection.'), 9.3, 450, cls='muted', layer='label')
    # types table
    f.group(16, 348, 1088, 196, 'infra', ('6 种帧类型', 'The 6 frame types'), 'connection.ts · frame.rs', 'layers', title_mono=False, gid='ty')
    TY = [(1, 'request', ('客户端 → 守护进程', 'client → daemon'), ('json.op 指明操作', 'json.op names the operation')),
          (2, 'result', ('守护进程 → 客户端', 'daemon → client'), ('请求成功并结束', 'success; the request is finished')),
          (3, 'error', ('守护进程 → 客户端', 'daemon → client'), ('{ code, message, syscall?, path? }', '{ code, message, syscall?, path? }')),
          (4, 'event', ('守护进程 → 客户端', 'daemon → client'), ('进度：exec 输出、watch 变化；不结束请求', 'progress: exec output, watch changes; not finishing')),
          (5, 'cancel', ('客户端 → 守护进程', 'client → daemon'), ('取消请求 id', 'cancel request id')),
          (6, 'ping', ('双向', 'both'), ('心跳；接收方忽略', 'liveness; ignored by the receiver'))]
    for i, (n, nm, dirn, m) in enumerate(TY):
        cx = 32 + (i % 2) * 540
        y = 388 + (i // 2) * 48
        f.chip(cx, y, str(n), 'infra', size=10.5, h=24)
        f.text(cx + 34, y + 11, nm, 10.5, 650, True, cls='err' if nm == 'error' else 'strongt', layer='label')
        f.text(cx + 120, y + 11, dirn, 9.2, 600, cls='faint', layer='label')
        f.text(cx + 34, y + 28, m, 9.2, 450, cls='muted', layer='label')
    f.legend(24, 566, [('layer:modes', ('同步行', 'sync line')), ('layer:coding', ('帧字段', 'frame fields')), ('layer:infra', ('帧类型', 'frame types'))])
    return f

# ============================================================== env_session : connection lifecycle
@reg
def env_session():
    assert E_.num('connection.ts', 'PING_INTERVAL_MS') == 5000 and E_.num('connection.ts', 'SILENCE_LIMIT_MS') == 30000 and E_.num('connection.ts', 'START_TIMEOUT_MS') == 60000
    R_.has('main.rs', 'const PING_INTERVAL: Duration = Duration::from_secs(5);', 'const SILENCE_LIMIT_MS: u64 = 30_000;', 'const PROTOCOL: u64 = 1;')
    E_.has('connection.ts', 'return new RemoteError({ code: "unknown", message, lost: true });', 'this.#send(session, "hello", { protocol: 1 }, {})', 'const marker = Buffer.from(`PI-ENV ${session.token}\\n`, "utf8");')
    doc(PROTO, 'handles belong to the daemon that opened them, so requests on them fail instead of reaching the new one.', 'The daemon kills every process group it started and exits after 30 seconds')
    f = Fig('env_session', 1120, 600, ('一条连接的一生：懒启动、心跳、丢失后重启', 'The life of a connection: lazy start, heartbeats, restart after loss'))
    E = f.edge
    lanes = [(('客户端 Connection', 'client Connection'), 'modes', 96), (('守护进程', 'daemon'), 'infra', 236)]
    for t, lay, y in lanes:
        f.text(16, y + 4, t, 10.5, 650, cls='strongt', layer='label')
    vline(f, 140, 70, 300)
    ev = [(150, 130, 'modes', ('第一个请求', 'first request'), ('懒启动', 'lazy start'), 76),
          (300, 150, 'modes', 'ssh … serve', ('--token <hex>', '--token <hex>'), 76),
          (300, 150, 'infra', 'PI-ENV <token>', ('同步行', 'sync line'), 216),
          (470, 170, 'modes', 'hello { protocol: 1 }', ('60 s 内必须完成', 'within 60 s'), 76),
          (470, 170, 'infra', '{ os, arch, home, … }', None, 216),
          (660, 200, 'modes', ('请求 / 结果 / 事件', 'requests / results / events'), None, 76),
          (660, 200, 'infra', ('工作线程 · exec · watch', 'workers · exec · watch'), None, 216)]
    for i, (x, w, lay, t, s_, y) in enumerate(ev):
        f.node(f'e{i}', x, y, w, 48, lay, t, s_, None, mono=not isinstance(t, tuple), tsize=10.2, ssize=9)
    E([(280, 100), (300, 100)], 'e0', 'e1', 'main', 'modes')
    E([(340, 124), (340, 216)], 'e1', 'e2', 'main', 'modes', label='ssh', lpos=(360, 170))
    E([(420, 216), (420, 124)], 'e2', 'e1', 'event', 'infra')
    E([(530, 124), (530, 216)], 'e3', 'e4', 'main', 'modes')
    E([(600, 216), (600, 124)], 'e4', 'e3', 'event', 'infra')
    E([(730, 124), (730, 216)], 'e5', 'e6', 'main', 'modes')
    E([(800, 216), (800, 124)], 'e6', 'e5', 'event', 'infra')
    # ping
    f.node('png', 880, 76, 224, 48, 'ext', ('双向 ping，每 5 s', 'ping both ways, every 5 s'), None, 'clock', mono=False, tsize=10.5)
    f.node('sil', 880, 216, 224, 48, 'err', ('30 s 没收到任何字节', '30 s without any bytes'), ('杀掉所有进程组并退出', 'kill every process group, exit'), None, mono=False, tsize=10.5, ssize=9)
    f.text(880, 160, ('stdin 结束时守护进程也退出：', 'The daemon also exits when stdin'), 9.2, 450, cls='muted', layer='label')
    f.text(880, 176, ('断线 = 远端命令停止。', 'ends: a dropped link stops commands.'), 9.2, 450, cls='muted', layer='label')
    # loss panel
    f.group(16, 320, 540, 236, 'err', ('连接丢失时（客户端）', 'When the connection is lost (client)'), 'connection.ts', 'x', title_mono=False, gid='lo')
    L = [(('进行中的请求失败', 'Requests in flight fail'), '{ code: "unknown", lost: true }'),
         (('变更类请求的结果因此未知', 'A mutation\'s outcome is then unknown'), ('写入可能已发生，也可能没有', 'the write may or may not have happened')),
         (('下一个请求启动新的守护进程', 'The next request starts a new daemon'), ('再次同步 + hello', 'sync line + hello again')),
         (('旧会话的句柄不会落到新进程上', 'Old handles never reach the new daemon'), ('它们的请求直接失败', 'their requests fail instead'))]
    for i, (a, b) in enumerate(L):
        y = 366 + i * 42
        f.text(32, y, a, 10, 600, cls='strongt', layer='label')
        f.text(32, y + 18, b, 9.3, 500, isinstance(b, str), cls='err' if isinstance(b, str) else 'muted', layer='label')
    f.text(32, 540, ('原因：进程退出、帧损坏（"Corrupt frame from pi-env"）、30 s 静默、hello 协议不符。', 'Causes: process exit, a corrupt frame, 30 s of silence, a hello protocol mismatch.'), 9.0, 450, cls='faint', layer='label')
    f.group(572, 320, 532, 236, 'ext', ('上层如何感知', 'What the layers above see'), None, 'eye', title_mono=False, gid='up')
    U = [('isConnectionLost(err)', ('区分"断线"和"守护进程拒绝了请求"', 'tells "lost" apart from "the daemon refused"')),
         ('RemoteExecutionEnv', ('把丢失映射成 FileError / ExecutionError 的 unknown', 'maps a loss to FileError / ExecutionError unknown')),
         ('RemoteWatcher', ('新守护进程启动后重新打开监视并报告 overflow', 'reopens the watch on the new daemon, reports overflow')),
         ('sshConnection()', ('懒连接：网络或密钥错误只是那一次操作的错误', 'lazy: a network or key failure fails that operation only'))]
    for i, (a, b) in enumerate(U):
        y = 364 + i * 44
        f.text(588, y, a, 10, 650, True, cls='strongt', layer='label')
        f.text(588, y + 18, b, 9.2, 450, cls='muted', layer='label')
    E_.has('connection.ts', 'export function isConnectionLost(')
    doc(SEM, 'When the connection is lost, the client opens the watcher again once a new daemon starts and reports `overflow`.')
    f.legend(24, 580, [('main', ('请求', 'request')), ('event', ('回应', 'reply')), ('layer:err', ('丢失', 'loss'))])
    return f

# ============================================================== env_exec : commands & output
@reg
def env_exec():
    assert R_.num('output.rs', 'BULK_LIMIT') == 4 * 1024 * 1024 and R_.num('main.rs', 'CONTROL_PAYLOAD') == 64 * 1024
    R_.has('exec.rs', 'const EXIT_STDIO_GRACE: Duration = Duration::from_millis(100);')
    doc(PROTO, 'Results, errors, pings and `watch` events are sent before queued command output, and', 'results with payloads above 64 KiB queue behind output too',
        'Output of a\ncommand without an output window waits while more than 4 MiB of output is unsent', '`exec` kills the command\'s process group and finishes with `aborted`; `{ mode: "kill" }` kills',
        'replaced by `skipped { bytes, newlines, endsWithNewline }`')
    doc(SEM, 'An abort settles as `aborted`; `cleanup()` kills without aborting, so the command settles with exit code 137.', 'otherwise `/bin/bash`, `which bash`, then `sh`, with `-c`.',
        'Spill: once the output crosses `spill.afterBytes` or `spill.afterLines`', 'A process killed by a signal reports `128 + signal`.')
    f = Fig('env_exec', 1120, 620, ('exec：命令、输出窗口、溢出文件与取消', 'exec: commands, output windows, spill files and cancellation'))
    E = f.edge
    f.node('rq', 16, 64, 330, 64, 'modes', 'exec { command | argv, cwd, env, … }', ('timeoutMs? · spill? · window?', 'timeoutMs? · spill? · window?'), 'terminal', tsize=10.5, ssize=9.2, strong=True)
    f.node('sh', 400, 52, 330, 44, 'infra', ('字符串 → shell', 'string → shell'), ('shellPath，否则 /bin/bash、which bash、sh；-c', 'shellPath, else /bin/bash, which bash, sh; -c'), None, mono=False, tsize=10.5, ssize=8.8)
    f.node('av', 400, 104, 330, 44, 'infra', ('argv 数组 → 直接运行', 'argv array → run directly'), ('Windows 按 libuv 规则搜索，拒绝批处理', 'Windows: libuv search, batch files refused'), None, mono=False, tsize=10.5, ssize=8.8)
    E([(346, 84), (373, 84), (373, 74), (400, 74)], 'rq', 'sh', 'main', 'modes', r=4)
    E([(346, 108), (373, 108), (373, 126), (400, 126)], 'rq', 'av', 'main', 'modes', r=4)
    f.node('pg', 784, 64, 320, 64, 'infra', ('新会话（进程组）', 'new session (process group)'), ('默认信号处理 · 空信号掩码', 'default signal dispositions · empty mask'), 'cpu', mono=False, tsize=10.5, ssize=9.2)
    E([(730, 96), (784, 96)], 'sh', 'pg', 'main', 'infra')
    # output
    f.group(16, 156, 540, 220, 'coding', ('输出：event { kind: "output", stream }', 'Output: event { kind: "output", stream }'), None, 'stream', title_mono=False, gid='out')
    f.text(32, 200, ('每个流独立解码为 UTF-8，作为负载字节发送。', 'Each stream is decoded to UTF-8 and sent as payload bytes.'), 9.4, 450, cls='muted', layer='label')
    f.text(32, 226, 'window { maxBytes, maxLines, minIntervalMs, bytesPerSecond }', 9.4, 650, True, cls='strongt', layer='label')
    f.text(32, 244, ('合并并按调用方的提交节奏发送；每条命令最多一帧未发出；', 'coalesced and paced like the caller\'s commits; at most one unsent frame;'), 9.2, 450, cls='muted', layer='label')
    f.text(32, 260, ('超出窗口的部分在下一帧里变成 skipped { bytes, newlines, … }', 'output beyond the window becomes skipped { bytes, newlines, … }'), 9.2, 450, cls='muted', layer='label')
    f.text(32, 290, 'spill { afterBytes, afterLines }', 9.4, 650, True, cls='strongt', layer='label')
    f.text(32, 308, ('越线后完整原始输出写入 tmp-…/pi-output-<uuid>.log；', 'once crossed, the full raw output goes to tmp-…/pi-output-<uuid>.log;'), 9.2, 450, cls='muted', layer='label')
    f.text(32, 324, ('结果带 spillPath（超时 / 取消时也带）。', 'the result carries spillPath (also on timeout / abort).'), 9.2, 450, cls='muted', layer='label')
    f.text(32, 354, ('进程退出后继续收集输出，直到两个管道都关闭或 100 ms 无输出。', 'After exit, output is collected until both pipes end or 100 ms pass silently.'), 9.0, 450, cls='faint', layer='label')
    # scheduling
    f.group(572, 156, 532, 220, 'ext', ('调度：回复先于大块数据', 'Scheduling: replies before bulk data'), None, 'queue', title_mono=False, gid='sc')
    f.node('ctl', 588, 200, 230, 54, 'ext', ('控制队列', 'control queue'), ('结果 · 错误 · ping · watch 事件', 'results · errors · pings · watch'), None, mono=False, tsize=10.5, ssize=8.8, strong=True)
    f.node('blk', 588, 270, 230, 54, 'infra', ('大块队列', 'bulk queue'), ('命令输出 · > 64 KiB 的结果', 'command output · results > 64 KiB'), None, mono=False, tsize=10.5, ssize=8.8)
    f.node('so', 886, 236, 200, 54, 'infra', 'stdout', ('→ ssh → 客户端', '→ ssh → client'), None, tsize=10.5, ssize=8.8)
    E([(818, 227), (852, 227), (852, 254), (886, 254)], 'ctl', 'so', 'main', 'ext', r=4)
    E([(818, 297), (852, 297), (852, 272), (886, 272)], 'blk', 'so', 'dep', 'infra', r=4)
    f.text(588, 346, ('没有 window 的命令：未发输出超过 4 MiB 就等待——像管道写满一样拖慢命令。', 'Without a window: output waits while more than 4 MiB is unsent, slowing the command like a full pipe.'), 9.0, 450, cls='muted', layer='label')
    # settle
    f.group(16, 392, 1088, 180, 'err', ('命令怎样结束', 'How a command settles'), None, 'flag', title_mono=False, gid='st')
    S = [('{ exitCode }', ('正常退出；被信号杀死报告 128 + 信号', 'normal exit; killed by a signal → 128 + signal')),
         ('timeout', ('超时：SIGKILL 整个进程组', 'timeoutMs passed: SIGKILL the group')),
         ('aborted', ('cancel 帧：杀进程组，以 aborted 结束', 'a cancel frame: kill the group, settle aborted')),
         ('137', ('cleanup()：cancel { mode: "kill" }，不 abort', 'cleanup(): cancel { mode: "kill" }, no abort')),
         ('spawn_error', ('cwd 不存在等', 'missing cwd, etc.')),
         ('shell_unavailable', ('配置的 shellPath 不存在', 'the configured shellPath is missing'))]
    for i, (a, b) in enumerate(S):
        cx = 32 + (i % 3) * 360
        y = 436 + (i // 3) * 56
        f.chip(cx, y, a, 'err' if i else 'coding', size=10, h=22)
        f.text(cx, y + 40, b, 9.2, 450, cls='muted', layer='label')
    f.legend(24, 600, [('layer:modes', ('请求', 'request')), ('layer:coding', ('输出', 'output')), ('layer:ext', ('控制优先', 'control first')), ('layer:err', ('结束方式', 'settlements'))])
    return f

# ============================================================== env_files : ExecutionEnv over the wire
@reg
def env_files():
    blk = re.search(r'export interface FileSystem \{(.*?)^\}', (SRC / 'packages/durable/src/env/index.ts').read_text(), re.S | re.M).group(1)
    FS = re.findall(r'^\t([a-zA-Z]+)\(', blk, re.M)
    for m in ['readTextFile', 'openBinaryReader', 'writeFile', 'listDir', 'openDirReader', 'watch', 'remove', 'createTempDir', 'cleanup']: assert m in FS, m
    ops = re.findall(r'^\| `(\w+)` \|', PROTO, re.M)
    assert ops == ['lstat', 'realpath', 'write', 'writeChunk', 'truncate', 'fsync', 'rename', 'mkdir', 'rm', 'mkdtemp', 'open', 'pread', 'fstat', 'scanLines', 'opendir', 'readdir', 'close'], ops
    C = {n: E_.num('remote-env.ts', n) for n in ['READ_CHUNK', 'READ_DEPTH', 'WRITE_CHUNK', 'WRITE_DEPTH', 'READ_FILE_CHUNK', 'LINE_CHUNK']}
    assert C == {'READ_CHUNK': 262144, 'READ_DEPTH': 8, 'WRITE_CHUNK': 524288, 'WRITE_DEPTH': 8, 'READ_FILE_CHUNK': 524288, 'LINE_CHUNK': 65536}, C
    W = {n: R_.num('main.rs', n) for n in ['WORKERS', 'MAX_HANDLES']}
    assert W == {'WORKERS': 16, 'MAX_HANDLES': 4096}, W
    f = Fig('env_files', 1120, 640, ('文件操作：ExecutionEnv 方法 → 守护进程的 17 个文件 op', 'File operations: ExecutionEnv methods → the daemon\'s 17 file ops'))
    E = f.edge
    f.group(16, 52, 330, 420, 'modes', 'RemoteExecutionEnv', None, 'monitor', title_mono=True, gid='m')
    MAP = [('readTextFile / readBinaryFile', 'open(mode:"read") → pread…'), ('openBinaryReader', 'open(noFollow) · pread · fstat'), ('openTextLineReader', 'pread + StreamDecoder'),
           ('writeFile / appendFile', 'write(keep) · writeChunk…'), ('listDir / openDirReader', 'opendir · readdir(max)'), ('fileInfo / exists', 'lstat'),
           ('canonicalPath', 'realpath'), ('renameFile / remove', 'rename · rm'), ('createDir / createTempDir', 'mkdir · mkdtemp'), ('truncateFile / flushFile', 'truncate · fsync'), ('watch', 'watch')]
    for i, (a, b) in enumerate(MAP):
        y = 100 + i * 33.5
        f.text(32, y + 4, a, 9.6, 600, True, cls='strongt', layer='label')
        f.text(32, y + 19, '→ ' + b, 9.0, 500, True, cls='muted', layer='label')
    f.group(362, 52, 360, 420, 'infra', ('守护进程的文件 op', 'The daemon\'s file ops'), 'protocol.md', 'cpu', title_mono=False, gid='o')
    for i, o in enumerate(ops):
        f.chip(378 + (i % 3) * 112, 96 + (i // 3) * 34, o, 'infra', size=9.8, h=22)
    f.text(378, 330, ('全部在 16 个工作线程的固定池里运行；', 'All run on a fixed pool of 16 worker threads;'), 9.2, 450, cls='muted', layer='label')
    f.text(378, 347, ('同一句柄的分块写按到达顺序执行。', 'chunk writes to one handle run in order.'), 9.2, 450, cls='muted', layer='label')
    f.text(378, 376, ('句柄是数字，close 或连接结束前有效；', 'Handles are numbers, valid until close or'), 9.2, 450, cls='muted', layer='label')
    f.text(378, 393, ('打开超过 4096 个 → EMFILE。', 'the connection ends; over 4096 → EMFILE.'), 9.2, 450, cls='muted', layer='label')
    f.text(378, 422, ('路径在客户端解析成绝对路径后再发送。', 'Paths are made absolute by the client.'), 9.2, 450, cls='faint', layer='label')
    E([(346, 260), (362, 260)], 'm', 'o', 'main', 'modes')
    # chunk sizes
    f.group(738, 52, 366, 228, 'coding', ('客户端的分块与流水线', 'Client chunking and pipelining'), 'remote-env.ts', 'compress', title_mono=False, gid='c')
    CH = [('READ_CHUNK', f'{MiB(C["READ_CHUNK"])} × {C["READ_DEPTH"]}', ('二进制读，8 个并发', 'binary reads, 8 in flight')),
          ('WRITE_CHUNK', f'{MiB(C["WRITE_CHUNK"])} × {C["WRITE_DEPTH"]}', ('writeFile，8 个并发', 'writeFile, 8 in flight')),
          ('READ_FILE_CHUNK', MiB(C['READ_FILE_CHUNK']), ('readFile 每次读', 'each readFile read')),
          ('LINE_CHUNK', MiB(C['LINE_CHUNK']), ('行读取器每次读', 'each line-reader read'))]
    for i, (n, v, d) in enumerate(CH):
        y = 98 + i * 44
        f.text(754, y + 4, n, 9.8, 650, True, cls='strongt', layer='label')
        f.text(1088, y + 4, v, 9.8, 650, True, cls='strongt', layer='label', anchor='end')
        f.text(754, y + 21, d, 9.0, 450, cls='muted', layer='label')
    # error mapping
    f.group(738, 296, 366, 176, 'err', ('错误码映射（toFileError）', 'Error mapping (toFileError)'), 'errors.ts', 'x', title_mono=False, gid='e')
    s = E_.src('errors.ts')
    for c in ['ENOENT', 'EACCES', 'EPERM', 'ENOTDIR', 'EISDIR', 'EINVAL']: assert f'"{c}"' in s, c
    EM = [('ENOENT', 'not_found'), ('EACCES · EPERM', 'permission_denied'), ('ENOTDIR', 'not_directory'), ('EISDIR', 'is_directory'), ('EINVAL …', 'invalid')]
    for i, (a, b) in enumerate(EM):
        y = 340 + i * 24
        f.text(754, y, a, 9.6, 600, True, cls='strongt', layer='label')
        f.text(900, y, '→ ' + b, 9.6, 500, True, cls='muted', layer='label')
    # bottom: semantics rules
    f.group(16, 488, 1088, 112, 'agent', ('标准库不遵守、但这里遵守的规则（节选）', 'Rules the standard libraries do not follow (excerpt)'), 'semantics.md', 'check', title_mono=False, gid='r')
    doc(SEM, 'an existing file fails with `EEXIST`', 'a directory without `recursive` fails with `ERR_FS_EISDIR`', '`listDir`: names in byte order', '`noFollow` refuses a final symbolic link (`O_NOFOLLOW`).')
    RU = [('mkdir -p：已有文件 → EEXIST', 'recursive mkdir: an existing file → EEXIST'), ('rm 目录不带 recursive → ERR_FS_EISDIR', 'rm of a dir without recursive → ERR_FS_EISDIR'),
          ('listDir：按字节序排序名字', 'listDir: names in byte order'), ('openBinaryReader：noFollow → O_NOFOLLOW', 'openBinaryReader: noFollow → O_NOFOLLOW')]
    for i, r in enumerate(RU):
        f.text(32 + (i % 2) * 540, 538 + (i // 2) * 24, '· ', 9.4, 600, cls='strongt', layer='label')
        f.text(44 + (i % 2) * 540, 538 + (i // 2) * 24, r, 9.4, 450, cls='muted', layer='label')
    f.legend(24, 624, [('layer:modes', ('客户端方法', 'client methods')), ('layer:infra', ('守护进程 op', 'daemon ops')), ('layer:err', ('错误映射', 'error mapping'))])
    return f

# ============================================================== env_watch
@reg
def env_watch():
    WC = {n: R_.const('watch.rs', n) for n in ['DEBOUNCE', 'FSEVENTS_SETTLE', 'DEFAULT_POLL_MS', 'DEFAULT_MAX_DIRECTORIES', 'HASH_MAX_BYTES']}
    assert 'from_millis(50)' in WC['DEBOUNCE'] and 'from_millis(500)' in WC['FSEVENTS_SETTLE'] and WC['DEFAULT_POLL_MS'] == '2000' and WC['DEFAULT_MAX_DIRECTORIES'] == '10_000' and WC['HASH_MAX_BYTES'] == '256 * 1024', WC
    assert E_.num('watch.ts', 'RECONNECT_FIRST_MS') == 1000 and E_.num('watch.ts', 'RECONNECT_MAX_MS') == 30000
    doc(PROTO, 'an event `{ kind: "ready", mode }`', '`{ kind: "change", paths }` or `{ kind: "change", overflow: true, mode: "polling" }`', '`{ kind: "error", code, message }`, after which nothing follows')
    doc(SEM, 'native events (inotify, FSEvents) only trigger a\n  debounced rescan', 'Reads are not events.', 'Windows and network or FUSE file systems poll')
    f = Fig('env_watch', 1120, 580, ('文件监视：在文件旁边运行的 NodeFileWatcher', 'Watching: NodeFileWatcher running next to the files'))
    E = f.edge
    f.node('w', 16, 64, 300, 64, 'modes', 'env.watch(targets, …)', ('RemoteWatcher（客户端）', 'RemoteWatcher (client)'), 'eye', tsize=11, ssize=9.2)
    f.node('rq', 370, 64, 360, 64, 'infra', 'watch { targets, mode?, pollIntervalMs?, … }', ('targets：{ path, recursive, exclude }', 'targets: { path, recursive, exclude }'), None, tsize=10, ssize=9)
    f.node('dw', 784, 64, 320, 64, 'infra', ('守护进程 watch.rs', 'daemon watch.rs'), ('Durable NodeFileWatcher 的移植', 'a port of Durable\'s NodeFileWatcher'), 'cpu', mono=False, tsize=11, ssize=9.2, strong=True)
    E([(316, 96), (370, 96)], 'w', 'rq', 'main', 'modes')
    E([(730, 96), (784, 96)], 'rq', 'dw', 'main', 'infra')
    # pipeline
    f.group(16, 152, 1088, 168, 'infra', ('变化怎样被发现', 'How changes are found'), None, 'filter', title_mono=False, gid='p')
    P = [(('原生事件', 'native events'), ('inotify / FSEvents', 'inotify / FSEvents')), (('去抖 50 ms', 'debounce 50 ms'), ('FSEvents 再等 500 ms', 'FSEvents settles 500 ms')),
         (('重新扫描', 'rescan'), ('最多 10,000 个目录', 'up to 10,000 directories')), (('比较快照', 'diff snapshots'), ('≤ 256 KiB 的文件比哈希', 'hash files ≤ 256 KiB')),
         ('change { paths }', ('快照差异 + 事件路径', 'snapshot diff + event paths'))]
    for i, (t, s) in enumerate(P):
        x = 32 + i * 214
        f.node(f'p{i}', x, 196, 190, 56, 'infra', t, s, None, mono=not isinstance(t, tuple), tsize=10.8, ssize=9, strong=(i == 4))
        if i: E([(x - 24, 224), (x, 224)], f'p{i-1}', f'p{i}', 'main', 'infra')
    f.text(32, 284, ('原生事件只触发重新扫描；读取不算事件。Windows、网络与 FUSE 文件系统改用轮询（默认 2000 ms）。', 'Native events only trigger a rescan; reads are not events. Windows, network and FUSE file systems poll instead (2000 ms by default).'), 9.4, 450, cls='muted', layer='label')
    # events
    f.group(16, 336, 540, 208, 'coding', ('event 帧（请求一直持续到被取消）', 'Event frames (the request lasts until cancelled)'), None, 'stream', title_mono=False, gid='ev')
    EV = [('{ kind: "ready", mode }', ('覆盖范围建立；之后才有变化', 'coverage established; changes follow')),
          ('{ kind: "change", paths }', ('一批变化的路径', 'a batch of changed paths')),
          ('{ kind: "change", overflow: true, mode: "polling" }', ('原生监视用尽 → 转轮询', 'native watches ran out → polling')),
          ('{ kind: "error", code, message }', ('之后不再有任何事件', 'nothing follows'))]
    for i, (a, b) in enumerate(EV):
        y = 380 + i * 38
        f.text(32, y, a, 9.6, 600, True, cls='err' if 'error' in a else 'strongt', layer='label')
        f.text(32, y + 17, b, 9.2, 450, cls='muted', layer='label')
    f.group(572, 336, 532, 208, 'modes', ('断线之后（客户端 watch.ts）', 'After a lost link (client watch.ts)'), None, 'loop', title_mono=False, gid='rc')
    f.text(588, 380, ('新守护进程启动后，RemoteWatcher 重新打开同样的监视，', 'Once a new daemon starts, RemoteWatcher reopens the same watch'), 9.4, 450, cls='muted', layer='label')
    f.text(588, 398, ('并报告一次 overflow——期间可能漏掉了变化。', 'and reports overflow: changes may have been missed meanwhile.'), 9.4, 450, cls='muted', layer='label')
    f.text(588, 430, ('重连退避：1 s 起，最多 30 s。', 'Reconnect backoff: from 1 s up to 30 s.'), 9.4, 600, cls='strongt', layer='label')
    f.text(588, 462, ('cancel 帧让 watch 以 {} 结束。', 'A cancel frame finishes the watch with {}.'), 9.4, 450, cls='muted', layer='label')
    f.text(588, 494, ('收到 overflow 的使用方应当整体重新读取，', 'A consumer that sees overflow should re-read'), 9.4, 450, cls='faint', layer='label')
    f.text(588, 512, ('而不是只看路径列表。', 'everything rather than trust the path list.'), 9.4, 450, cls='faint', layer='label')
    doc(PROTO, '`watch` stops and finishes with `{}`.')
    f.legend(24, 566, [('layer:modes', ('客户端', 'client')), ('layer:infra', ('守护进程', 'daemon')), ('layer:coding', ('事件', 'events'))])
    return f
