# pi-env deep dive. Same section schema as deep_agent.py; files: (path, regex, symbol, zh, en)
from pkgsrc import Pkg
E_ = Pkg('packages/env/src/'); R_ = Pkg('packages/env/daemon/src/')
U = 'packages/env/src/'
RS = 'packages/env/daemon/src/'
DOC = 'packages/env/docs/'
SLIDE_KEYS = ['env_arch', 'env_split', 'env_ssh', 'env_frames', 'env_session', 'env_exec', 'env_files', 'env_watch']
_TS = E_.total(); _RS = R_.total(ext=('.rs',))

INTRO = dict(
 takeaway=("`pi-env` 让 agent 的工具在**另一台机器**上运行，而 Durable worker、它的存储和凭据留在本地。它由两半组成：远端的 `pi-env` 守护进程（Rust）在 stdin/stdout 上讲一个分帧协议、执行文件操作和命令；本地的 `RemoteExecutionEnv`（TypeScript）实现 Durable 的 `ExecutionEnv`，结果与在远端机器上运行 `NodeExecutionEnv` 一致——只有错误消息可以不同。连接通常走 SSH：信任主机密钥、探测平台、按 SHA-256 部署守护进程、启动。",
           "`pi-env` runs an agent's tools on **another machine** while the Durable worker, its storage and credentials stay local. It has two halves: the remote `pi-env` daemon (Rust) speaks a framed protocol on stdin/stdout and performs file operations and commands; the local `RemoteExecutionEnv` (TypeScript) implements Durable's `ExecutionEnv` with results that match `NodeExecutionEnv` running on the remote machine — only error messages may differ. Connections usually go over SSH: trust the host key, detect the platform, deploy the daemon by SHA-256, start it."),
 role=(f"{_TS:,} 行 TypeScript 客户端加 {_RS:,} 行 Rust 守护进程（`daemon/src`）。依赖 `chord` 与 `pi-durable`；只有一个导入路径；包里附带每个支持平台的守护进程二进制（`bin/`）。pi 仓库里目前没有其他包导入它。",
       f"A {_TS:,}-line TypeScript client plus a {_RS:,}-line Rust daemon (`daemon/src`). Depends on `chord` and `pi-durable`; one import path; the package ships a daemon binary for every supported platform (`bin/`). No other package in the pi repo imports it yet."),
)

SECTIONS = [
dict(id="env-arch", group="arch", layer="infra", diagram="env_arch",
 title=("两半：TypeScript 客户端与 Rust 守护进程", "Two halves: a TypeScript client and a Rust daemon"),
 takeaway=("本地：`remote-env.ts`（`RemoteExecutionEnv`）、`ssh.ts`（主机密钥、探测、部署、启动）、`connection.ts`（帧、请求 id、心跳、重启）、`watch.ts`（断线后重新打开监视）、`errors.ts`（错误码映射）。远端：`main.rs`（同步行、调度、工作线程池）、`exec.rs` 与 `window.rs`（命令与输出）、`fs.rs` 与 `scan.rs`（文件与行扫描）、`watch.rs`（Durable `NodeFileWatcher` 的移植）、`sys/`（Unix 与 Windows）。",
           "Local: `remote-env.ts` (`RemoteExecutionEnv`), `ssh.ts` (host keys, detection, deployment, launch), `connection.ts` (frames, request ids, pings, restarts), `watch.ts` (reopening watches after a loss) and `errors.ts` (error-code mapping). Remote: `main.rs` (sync line, scheduling, the worker pool), `exec.rs` and `window.rs` (commands and output), `fs.rs` and `scan.rs` (files and line scans), `watch.rs` (a port of Durable's `NodeFileWatcher`) and `sys/` (Unix and Windows)."),
 points=[
  ("支持的远端：Linux、macOS、Android（Termux）与 Windows，x86-64 与 arm64。Windows 上字符串命令像 `NodeExecutionEnv` 那样通过 Git Bash 运行，argv 命令直接运行。", "Supported remotes: Linux, macOS, Android (Termux) and Windows, on x86-64 and arm64. On Windows, string commands run through Git Bash as `NodeExecutionEnv` runs them; argv commands run directly."),
  ("测试对 `RemoteExecutionEnv` 跑 Durable 的 env 一致性套件，并把随机操作序列和 Durable 的工具与本机 `NodeExecutionEnv` 比对（differential 测试）。", "Tests run Durable's env conformance suite against `RemoteExecutionEnv` and compare random operation sequences and Durable's tools with `NodeExecutionEnv` on the same machine (differential tests)."),
  ("`RemoteExecutionEnv` 需要一个 `id`：相同 id 表示看到同样的文件，Durable 的 edit / write 按 id 加路径串行化修改。", "`RemoteExecutionEnv` takes an `id`: equal ids see the same files, and Durable's edit / write serialize changes by id plus path."),
 ],
 how=[
  ("`const { connection } = await connectSsh(target)`。", "`const { connection } = await connectSsh(target)`."),
  ("`new RemoteExecutionEnv({ connection, id: \"pi-env:gpu\", cwd: \"/home/me/project\" })`。", "`new RemoteExecutionEnv({ connection, id: \"pi-env:gpu\", cwd: \"/home/me/project\" })`."),
  ("交给 Durable：`Harness.open(storage, { …, env: () => remoteEnv }, ctx)`。", "Hand it to Durable: `Harness.open(storage, { …, env: () => remoteEnv }, ctx)`."),
 ],
 files=[
  (U + "index.ts", r"remote-env", "export …", "包入口", "package entry"),
  (U + "remote-env.ts", r"^export class RemoteExecutionEnv implements ExecutionEnv", "RemoteExecutionEnv", "客户端环境", "the client environment"),
  (U + "connection.ts", r"^export class Connection \{", "Connection", "一条连接", "one connection"),
  (RS + "main.rs", r"^fn serve\(token: &str\)", "serve()", "守护进程主循环", "the daemon main loop"),
  (RS + "exec.rs", r"^pub fn run\(", "exec::run()", "命令", "commands"),
 ]),

dict(id="env-split", group="arch", layer="infra", diagram="env_split",
 title=("分工与语义", "Split of work and semantics"),
 takeaway=("参照物是远端机器上的 Durable `NodeExecutionEnv`。凡是 Node 在 JavaScript 里做的事——路径解析、取消检查点、错误码映射、`readFile` 的分块与解码、`writeFile` 的 512 KiB 分块、行读取器、超时与结果优先级——都留在客户端；系统调用、进程、溢出文件、行扫描、输出解码和文件监视在守护进程里做。",
           "The reference is Durable's `NodeExecutionEnv` on the remote machine. Whatever Node does in JavaScript — path resolution, abort checkpoints, error-code mapping, `readFile` chunking and decoding, `writeFile`'s 512 KiB writes, the line reader, timeouts and result precedence — stays in the client; system calls, processes, spill files, line scans, output decoding and watching happen in the daemon."),
 points=[
  ("`docs/semantics.md` 记录了标准库不遵守、但这里必须遵守的规则：递归 mkdir 遇到已有文件报 `EEXIST`；`rm` 目录不带 recursive 报 `ERR_FS_EISDIR`；`listDir` 按字节序；`mkdtemp` 的前缀用 POSIX `path.join`……", "`docs/semantics.md` records rules the standard libraries do not follow but this must: a recursive mkdir over an existing file fails with `EEXIST`; `rm` of a directory without recursive gives `ERR_FS_EISDIR`; `listDir` is in byte order; `mkdtemp` joins its prefix with POSIX `path.join`…"),
  ("`tmpdir` 按 `TMPDIR`、`TMP`、`TEMP`、`/tmp` 的顺序（Termux 用 `$PREFIX/tmp`），与远端 Node 的 `os.tmpdir()` 一致。", "`tmpdir` follows `TMPDIR`, `TMP`, `TEMP`, then `/tmp` (Termux: `$PREFIX/tmp`), matching the remote Node's `os.tmpdir()`."),
  ("命令输出按流解码为 WHATWG UTF-8（`encoding_rs`），只丢掉开头的 BOM；文件读取保留 BOM——都和 Node 的行为对齐。", "Command output is decoded per stream as WHATWG UTF-8 (`encoding_rs`) with only a leading BOM dropped; file reads keep the BOM — both matching Node."),
 ],
 how=[
  ("改动任何一边的语义，都要跑 `test/differential.test.ts`：它在两种环境上执行同一串随机操作并比较结果。", "Changing semantics on either side means running `test/differential.test.ts`: it runs the same random operation sequence on both environments and compares results."),
  ("自定义环境可以用 Durable 的 `registerEnvConformance()` 自检。", "A custom environment can check itself with Durable's `registerEnvConformance()`."),
  ("真实 SSH：设置 `PI_ENV_SSH_HOST` 后 `test/ssh-external.test.ts` 在真正的服务器上跑套件。", "Real SSH: with `PI_ENV_SSH_HOST` set, `test/ssh-external.test.ts` runs the suite against a real server."),
 ],
 files=[
  (DOC + "semantics.md", r"^## Split of work", "semantics.md", "分工表", "the split table"),
  (DOC + "semantics.md", r"^## Rules the standard libraries do not follow", "semantics.md", "额外规则", "extra rules"),
  (U + "errors.ts", r"^export function toFileError\(", "toFileError()", "错误码映射", "error-code mapping"),
  (RS + "decode.rs", r"encoding_rs", "decode.rs", "输出解码", "output decoding"),
  ("packages/env/test/differential.test.ts", r"^import \{ NodeExecutionEnv \}", "differential.test.ts", "对比测试", "differential test"),
 ]),

dict(id="env-ssh", group="flows", layer="infra", diagram="env_ssh",
 title=("通过 SSH 连接", "Connecting over SSH"),
 takeaway=("一次性信任：`scanHostKey()` 用临时 known_hosts 抓到主机密钥，给用户看指纹，`acceptHostKey()` 存进应用自己的 known_hosts（固定的 `HostKeyAlias`）。之后每次连接：`detectPlatform()` 探测系统与架构，`deployDaemon()` 确保远端有内容哈希一致的守护进程，再经 ssh 启动 `pi-env serve --token <hex>`。",
           "Trust once: `scanHostKey()` captures the host key with a temporary known_hosts, the owner checks the fingerprints, and `acceptHostKey()` stores it in the application's own known_hosts (under a fixed `HostKeyAlias`). Then on each connection: `detectPlatform()` finds the system and architecture, `deployDaemon()` makes sure the remote has a daemon with the matching content hash, and ssh starts `pi-env serve --token <hex>`."),
 points=[
  ("守护进程放在 `~/.pi/mobile/tools/pi-env-<sha256 前 32 位>`：按内容命名，版本之间不会冲突；每次启动前都先校验哈希。", "The daemon lives at `~/.pi/mobile/tools/pi-env-<first 32 of sha256>`: named by content so versions never collide, and its hash is checked before every start."),
  ("上传写到同目录的 `mktemp` 临时文件，哈希一致才 `chmod 700` 并 `mv` 到位，然后删除其他版本（运行中的保持打开直到退出）。远端没有 sha256sum / shasum / openssl 时直接报错。", "The upload goes to a `mktemp` file in the same directory and is `chmod 700`-ed and `mv`-ed into place only if its hash matches; other versions are then removed (running ones stay open until they exit). A remote without sha256sum / shasum / openssl is an error."),
  ("ssh 选项锁死：`BatchMode=yes`、不转发任何东西、`ControlMaster=no`、`RemoteCommand=none`、`SendEnv=-*`、主机密钥按应用自己的 known-hosts 文件严格检查。ssh 配置仍决定路由（别名、跳板机），但加不进提示、转发或命令。", "ssh options are pinned: `BatchMode=yes`, no forwarding of any kind, `ControlMaster=no`, `RemoteCommand=none`, `SendEnv=-*`, host keys checked strictly against the application's own known-hosts file. The ssh config still picks the route (aliases, jump hosts) but cannot add prompts, forwarding or commands."),
  ("Windows 远端通过 PowerShell 探测与部署（base64 上传、`Get-FileHash`），守护进程通过服务器默认 shell 启动。", "Windows remotes are detected and deployed through PowerShell (base64 upload, `Get-FileHash`), and the daemon starts through the server's default shell."),
 ],
 how=[
  ("`const { lines, fingerprints } = await scanHostKey(target)` → 用户确认 → `await acceptHostKey(target, lines)`。", "`const { lines, fingerprints } = await scanHostKey(target)` → the owner confirms → `await acceptHostKey(target, lines)`."),
  ("立即连接：`await connectSsh(target)`；懒连接：`sshConnection(target)`，第一次操作时才探测、部署、连接，失败只是那次操作的错误。", "Eager: `await connectSsh(target)`; lazy: `sshConnection(target)` detects, deploys and connects on the first operation, and a failure is just that operation's error."),
  ("POSIX 上 `loginShell: true` 让守护进程经 `$SHELL -l` 启动，命令能看到 `~/.profile` 里的环境。", "On POSIX, `loginShell: true` starts the daemon through `$SHELL -l` so commands see the environment from `~/.profile`."),
 ],
 files=[
  (U + "ssh.ts", r"^export function sshArguments\(", "sshArguments()", "锁死的选项", "pinned options"),
  (U + "ssh.ts", r"^export async function scanHostKey\(", "scanHostKey()", "抓取主机密钥", "capturing the host key"),
  (U + "ssh.ts", r"^export async function detectPlatform\(", "detectPlatform()", "探测平台", "platform detection"),
  (U + "ssh.ts", r"^export async function deployDaemon\(", "deployDaemon()", "部署", "deployment"),
  (U + "ssh.ts", r"^export function sshConnection\(", "sshConnection()", "懒连接", "lazy connection"),
 ]),

dict(id="env-frames", group="types", layer="infra", diagram="env_frames",
 title=("线上协议", "The wire protocol"),
 takeaway=("协议版本 1。shell 启动文件可能先往 stdout 打印东西，所以守护进程的第一行输出是 `PI-ENV <token>`，客户端丢弃它之前的一切；之后 stdout 上只有帧：`u32 length`、`u8 type`、`u32 id`、`u32 jsonLength`、JSON、原始字节，全部大端序，单帧最多 16 MiB。帧类型有 6 种：request、result、error、event、cancel、ping。",
           "Protocol version 1. Shell startup files may print to stdout first, so the daemon's first output is the line `PI-ENV <token>` and the client discards everything before it; after that stdout carries only frames: `u32 length`, `u8 type`, `u32 id`, `u32 jsonLength`, JSON, raw bytes, all big-endian, at most 16 MiB a frame. There are 6 frame types: request, result, error, event, cancel, ping."),
 points=[
  ("文件内容和命令输出走原始字节负载，不做 base64；更大的传输由客户端拆分。", "File contents and output travel as raw payload bytes, not base64; larger transfers are split by the client."),
  ("错误是 `{ code, message, syscall?, path? }`，code 是 Node 风格的（`ENOENT`、`ERR_FS_EISDIR`…）或执行错误码；只有 code 属于契约，消息只用于诊断。", "Errors are `{ code, message, syscall?, path? }` with a Node-style code (`ENOENT`, `ERR_FS_EISDIR`…) or an execution code; only codes are part of the contract, messages are diagnostic."),
  ("路径都是绝对路径：客户端先解析相对路径、`~` 和 `file://`。字符串以合法 UTF-8 发送（孤立代理项变成 U+FFFD），和 Node 编码字符串参数的方式一致。", "Paths are absolute: the client resolves relative paths, `~` and `file://` first. Strings are sent as well-formed UTF-8 (lone surrogates become U+FFFD), as Node encodes string arguments."),
  ("第一个请求是 `hello { protocol }`，返回 os、arch、home、tmpdir、cwd、Windows 的 `driveCwds` 和 pid。", "The first request is `hello { protocol }`, which returns os, arch, home, tmpdir, cwd, Windows' `driveCwds` and the pid."),
 ],
 how=[
  ("客户端：`Connection.request(op, json, { payload, signal })` 分配 id、写帧、等 result 或 error。", "Client: `Connection.request(op, json, { payload, signal })` assigns an id, writes the frame, and waits for result or error."),
  ("守护进程：`serve_frames()` 读帧，按 type 分派；request 先登记再执行，所以紧随其后的 cancel 不会丢。", "Daemon: `serve_frames()` reads frames and dispatches by type; a request is registered before it runs, so a cancel right after it is never lost."),
  ("JSON 解析失败的请求得到 `EINVAL`；帧格式错误直接断开连接。", "A request whose JSON does not parse gets `EINVAL`; a framing error ends the connection."),
 ],
 files=[
  (DOC + "protocol.md", r"^## Frames", "protocol.md", "帧格式", "frame format"),
  (U + "connection.ts", r"^const MAX_FRAME = ", "MAX_FRAME", "16 MiB", "16 MiB"),
  (U + "connection.ts", r"^\tasync request\(op: string", "request()", "发出请求", "sending a request"),
  (RS + "frame.rs", r"^pub const MAX_FRAME: usize", "frame.rs", "守护进程的帧", "the daemon's frames"),
  (RS + "main.rs", r"^fn serve_frames\(", "serve_frames()", "读帧与分派", "reading and dispatching"),
 ]),

dict(id="env-session", group="flows", layer="infra", diagram="env_session",
 title=("连接的生命周期", "The connection lifecycle"),
 takeaway=("`Connection` 在第一个请求时懒启动守护进程，60 秒内必须完成同步行和 `hello`。之后双方每 5 秒发一次 ping；守护进程 30 秒收不到任何字节就杀掉它启动的所有进程组并退出（stdin 结束时也一样），所以断线会停止远端命令。客户端把丢失的连接上的请求以 `{ code: \"unknown\", lost: true }` 失败，并在下一个请求时启动新的守护进程。",
           "`Connection` starts the daemon lazily on the first request, and the sync line plus `hello` must finish within 60 seconds. After that both sides ping every 5 seconds; after 30 seconds without receiving any bytes the daemon kills every process group it started and exits (as it does when stdin ends), so a dropped link stops remote commands. The client fails requests of a lost connection with `{ code: \"unknown\", lost: true }` and starts a new daemon on the next request."),
 points=[
  ("丢失时正在进行的变更（写入、改名…）结果未知：可能执行了，也可能没有。", "For mutations in flight when the link is lost (writes, renames…), the outcome is unknown: they may or may not have happened."),
  ("句柄属于打开它的那个守护进程：旧句柄上的请求直接失败，绝不会落到新进程上。", "Handles belong to the daemon that opened them: requests on old handles fail instead of reaching the new one."),
  ("`isConnectionLost(err)` 区分\"断线\"与\"守护进程拒绝了请求\"；丢失的原因可能是进程退出、帧损坏、30 秒静默或协议版本不符。", "`isConnectionLost(err)` tells \"lost\" apart from \"the daemon refused the request\"; causes are a process exit, a corrupt frame, 30 seconds of silence or a protocol mismatch."),
 ],
 how=[
  ("`#start()`：启动进程 → 丢弃输出直到 `PI-ENV <token>` → 发 `hello { protocol: 1 }` → 检查版本。", "`#start()`: spawn → discard output until `PI-ENV <token>` → send `hello { protocol: 1 }` → check the version."),
  ("定时器每 5 秒发 ping，并检查 `lastSeen`：超过 30 秒就 `#teardown()`。", "A timer pings every 5 seconds and checks `lastSeen`: after 30 seconds it calls `#teardown()`."),
  ("监视器在新守护进程上重新打开并报告一次 overflow（见文件监视一节）。", "Watchers reopen on the new daemon and report one overflow (see the watching section)."),
 ],
 files=[
  (U + "connection.ts", r"^\tasync #start\(\)", "#start()", "启动与同步", "start and sync"),
  (U + "connection.ts", r"^const PING_INTERVAL_MS = ", "PING_INTERVAL_MS", "心跳", "heartbeat"),
  (U + "connection.ts", r"^const SILENCE_LIMIT_MS = ", "SILENCE_LIMIT_MS", "30 秒静默", "30 s of silence"),
  (U + "connection.ts", r"^export function isConnectionLost\(", "isConnectionLost()", "判断丢失", "detecting a loss"),
  (RS + "main.rs", r"^fn kill_all\(", "kill_all()", "杀掉所有进程组", "killing every group"),
 ]),

dict(id="env-exec", group="flows", layer="infra", diagram="env_exec",
 title=("命令与输出", "Commands and output"),
 takeaway=("`exec` 运行一个 shell 字符串或一个 argv 数组。每条命令有自己的会话（进程组）、默认信号处理和空信号掩码；输出以 `event` 帧按流发送。可选的输出窗口把输出合并并按调用方的提交节奏发送，超出窗口的部分在下一帧报告为 `skipped`；可选的 spill 在越线后把完整原始输出写进一个日志文件。",
           "`exec` runs a shell string or an argv array. Each command gets its own session (process group), default signal dispositions and an empty signal mask; output goes out as `event` frames per stream. An optional output window coalesces output and paces it like the caller's commits, reporting what overflowed as `skipped` in the next frame; an optional spill writes the complete raw output to a log file once a threshold is crossed."),
 points=[
  ("调度：结果、错误、ping 和 watch 事件排在命令输出之前，超过 64 KiB 的结果也排到输出后面——慢链路只延迟大块数据，不延迟回复。", "Scheduling: results, errors, pings and watch events go before queued command output, and results above 64 KiB queue behind output too — a slow link delays bulk data, not replies."),
  ("没有窗口的命令在未发输出超过 4 MiB 时等待，像写满的管道一样拖慢命令。", "A command without a window waits while more than 4 MiB of output is unsent, slowing it the way a full pipe would."),
  ("超时、cancel 与 `cleanup()` 都用 SIGKILL 杀整个进程组：取消以 `aborted` 结束；`cleanup()` 用 `{ mode: \"kill\" }`，命令以退出码 137 结束。", "Timeout, cancel and `cleanup()` all SIGKILL the process group: a cancel settles as `aborted`; `cleanup()` uses `{ mode: \"kill\" }`, so the command settles with exit code 137."),
  ("进程退出后继续收集输出，直到两个管道都关闭或 100 ms 没有输出；命令结束时管道一定关闭，即使后代进程还开着它们。", "After the process exits, output is still collected until both pipes end or 100 ms pass silently; the pipes are closed when the command settles, even if a descendant keeps them open."),
 ],
 how=[
  ("`env.exec(\"npm test\", { onOutput, timeout, spill, window }, ctx)`，或 argv：`env.exec([\"git\", \"status\"], …)`。", "`env.exec(\"npm test\", { onOutput, timeout, spill, window }, ctx)`, or argv: `env.exec([\"git\", \"status\"], …)`."),
  ("字符串命令：配置的 `shellPath`（不存在则 `shell_unavailable`），否则 `/bin/bash`、`which bash`、`sh`，加 `-c`。", "String commands: the configured `shellPath` (missing → `shell_unavailable`), else `/bin/bash`, `which bash`, `sh`, with `-c`."),
  ("环境变量：默认 `inheritEnv` 时依次叠加守护进程环境、`shellEnv`、`env`；否则只用 `env`。", "Environment: with `inheritEnv` (the default) the daemon's environment, then `shellEnv`, then `env`; without it, only `env`."),
 ],
 files=[
  (U + "remote-env.ts", r"^\tasync exec\(", "exec()", "客户端", "client side"),
  (RS + "exec.rs", r"^pub fn kill_group\(", "kill_group()", "杀进程组", "killing the group"),
  (RS + "exec.rs", r"^const EXIT_STDIO_GRACE", "EXIT_STDIO_GRACE", "退出后 100 ms", "100 ms after exit"),
  (RS + "window.rs", r"^//! Durable's output window", "window.rs", "输出窗口", "the output window"),
  (RS + "output.rs", r"^const BULK_LIMIT", "BULK_LIMIT", "4 MiB", "4 MiB"),
 ]),

dict(id="env-files", group="types", layer="infra", diagram="env_files",
 title=("文件操作", "File operations"),
 takeaway=("`RemoteExecutionEnv` 的文件方法都落在守护进程的 17 个文件 op 上：`lstat`、`realpath`、`write` / `writeChunk`、`truncate`、`fsync`、`rename`、`mkdir`、`rm`、`mkdtemp`、`open`、`pread`、`fstat`、`scanLines`、`opendir`、`readdir`、`close`。文件 op 在 16 个工作线程的固定池里运行；句柄是数字，最多 4096 个。客户端负责分块与流水线：二进制读 256 KiB × 8 个并发，写 512 KiB × 8 个并发。",
           "`RemoteExecutionEnv`'s file methods all map onto the daemon's 17 file ops: `lstat`, `realpath`, `write` / `writeChunk`, `truncate`, `fsync`, `rename`, `mkdir`, `rm`, `mkdtemp`, `open`, `pread`, `fstat`, `scanLines`, `opendir`, `readdir`, `close`. File ops run on a fixed pool of 16 worker threads; handles are numbers, at most 4096. The client does chunking and pipelining: binary reads 256 KiB × 8 in flight, writes 512 KiB × 8."),
 points=[
  ("`write` 默认像递归 mkdir 那样创建缺失的父目录；带 `keep` 时返回句柄供后续 `writeChunk`，一块失败后后续块都报 `EBADF`。", "`write` creates missing parents like a recursive mkdir by default; with `keep` it returns a handle for later `writeChunk`s, and after a failed chunk later chunks fail with `EBADF`."),
  ("`open` 有两种：给 `openBinaryReader` 的非阻塞、只限普通文件（`noFollow` 用 `O_NOFOLLOW`）；以及 `mode: \"read\"` 的阻塞打开，和 Node 的 `open(path, \"r\")` 一样能读 `/dev/null`、FIFO。", "`open` comes in two kinds: nonblocking and regular files only for `openBinaryReader` (`noFollow` uses `O_NOFOLLOW`), and `mode: \"read\"`, a blocking open like Node's `open(path, \"r\")` that reads `/dev/null` or a FIFO."),
  ("`readdir` 的名字按 UTF-8 解码（非法字节换成替换字符），原始字节放在 `raw` 里用于排序；`listDir` 每次读最多 1000 项。", "`readdir` decodes names as UTF-8 (invalid bytes become replacement characters) and keeps the original bytes in `raw` for sorting; `listDir` reads at most 1000 entries at a time."),
  ("错误映射与 `NodeExecutionEnv` 相同：`ENOENT` → not_found，`EACCES` / `EPERM` → permission_denied，`ENOTDIR`、`EISDIR`、`EINVAL` 等。", "Error mapping matches `NodeExecutionEnv`: `ENOENT` → not_found, `EACCES` / `EPERM` → permission_denied, `ENOTDIR`, `EISDIR`, `EINVAL` and so on."),
 ],
 how=[
  ("`env.readTextFile(path, ctx)` → `open(mode:\"read\")` → 按 512 KiB `pread` → `StringDecoder` 解码。", "`env.readTextFile(path, ctx)` → `open(mode:\"read\")` → `pread` in 512 KiB → decode with `StringDecoder`."),
  ("`env.writeFile(path, content, ctx)` → `write(keep)` + 多个 `writeChunk`，每块之前检查取消。", "`env.writeFile(path, content, ctx)` → `write(keep)` + `writeChunk`s, checking for abort before each."),
  ("`openBinaryReader(path).scanLines({ startLine, endLine })` 在守护进程里数行，只把结果传回来。", "`openBinaryReader(path).scanLines({ startLine, endLine })` counts lines in the daemon and sends back only the result."),
 ],
 files=[
  (U + "remote-env.ts", r"^const READ_CHUNK = ", "READ_CHUNK", "分块大小", "chunk sizes"),
  (U + "remote-env.ts", r"^\tasync readTextFile\(", "readTextFile()", "读文件", "reading a file"),
  (U + "remote-env.ts", r"^\twriteFile\(path: string", "writeFile()", "写文件", "writing a file"),
  (RS + "main.rs", r"^const WORKERS: usize", "WORKERS", "16 个工作线程", "16 workers"),
  (RS + "main.rs", r"^const MAX_HANDLES: usize", "MAX_HANDLES", "4096 个句柄", "4096 handles"),
  (RS + "fs.rs", r"^pub fn info\(path", "fs.rs", "文件信息与 op", "file info and ops"),
 ]),

dict(id="env-watch", group="flows", layer="infra", diagram="env_watch",
 title=("文件监视", "Watching"),
 takeaway=("`watch` 在守护进程里运行 Durable `NodeFileWatcher` 的移植，就在文件旁边：原生事件（inotify、FSEvents）只触发一次去抖的重新扫描，变化 = 快照之间的差异加上事件路径；读取不算事件。Windows 与网络、FUSE 文件系统改用轮询。请求一直持续到被取消，先发 `ready`，再发 `change`，或一个之后不再有任何事件的 `error`。",
           "`watch` runs a port of Durable's `NodeFileWatcher` in the daemon, next to the files: native events (inotify, FSEvents) only trigger a debounced rescan, and changes are the difference between snapshots plus the event paths; reads are not events. Windows and network or FUSE file systems poll instead. The request lasts until cancelled: first `ready`, then `change`s, or an `error` after which nothing follows."),
 points=[
  ("去抖 50 ms（FSEvents 再等 500 ms 稳定）；轮询默认每 2000 ms；最多 10,000 个目录；≤ 256 KiB 的文件比较哈希。", "Debounce 50 ms (FSEvents settles another 500 ms); polling every 2000 ms by default; at most 10,000 directories; files ≤ 256 KiB are compared by hash."),
  ("原生监视用尽时切换到轮询，并报告 `{ kind: \"change\", overflow: true, mode: \"polling\" }`。", "Running out of native watches switches to polling and reports `{ kind: \"change\", overflow: true, mode: \"polling\" }`."),
  ("连接丢失后，客户端的 `RemoteWatcher` 在新守护进程启动后重新打开监视并报告 overflow；重连退避从 1 秒到 30 秒。", "After a lost connection, the client's `RemoteWatcher` reopens the watch once a new daemon starts and reports overflow; reconnect back-off runs from 1 s to 30 s."),
 ],
 how=[
  ("`env.watch([{ path, recursive: true, exclude: { hidden, names } }], onChange, ctx)`。", "`env.watch([{ path, recursive: true, exclude: { hidden, names } }], onChange, ctx)`."),
  ("收到 `overflow` 时整体重新读取，不要只依赖路径列表。", "On `overflow`, re-read everything rather than trusting the path list."),
  ("关闭：`watcher.close(ctx)` 发 cancel，watch 以 `{}` 结束。", "Close: `watcher.close(ctx)` sends a cancel and the watch finishes with `{}`."),
 ],
 files=[
  (U + "watch.ts", r"^export class RemoteWatcher implements FileWatcher", "RemoteWatcher", "客户端监视", "client watcher"),
  (U + "watch.ts", r"^const RECONNECT_MAX_MS = ", "RECONNECT_MAX_MS", "重连退避", "reconnect back-off"),
  (RS + "watch.rs", r"^const DEBOUNCE: Duration", "DEBOUNCE", "去抖", "debounce"),
  (RS + "watch.rs", r"^const DEFAULT_MAX_DIRECTORIES", "DEFAULT_MAX_DIRECTORIES", "目录上限", "directory limit"),
  (RS + "watch.rs", r"^fn parse_targets\(", "parse_targets()", "监视目标", "watch targets"),
 ]),
]

EXT_POINTS = [
 ("RemoteExecutionEnv({ connection, id, cwd })", ("任何 Connection 都行：ssh、管道或测试里的本地进程。", "Any Connection works: ssh, a pipe or a local process in tests.")),
 ("sshConnection / connectSsh(options)", ("懒或立即；binary 可替换，loginShell 可选。", "Lazy or eager; the binary can be replaced, loginShell is optional.")),
 ("scanHostKey · acceptHostKey · forgetHostKey", ("把主机密钥信任交给你的 UI。", "Put host-key trust in your own UI.")),
 ("deployDaemon(target, remote, binary?)", ("单独部署，或部署自己构建的守护进程。", "Deploy on its own, or deploy a daemon you built.")),
 ("PI_ENV_DAEMON", ("测试时指定守护进程二进制（CI 用发布构建）。", "Point tests at a daemon binary (CI uses release builds).")),
]
XREF = [('durable', ('ExecutionEnv 接口与 NodeExecutionEnv 参照实现', 'the ExecutionEnv interface and the NodeExecutionEnv reference')),
        ('chord', ('每个方法都带 chord Context（取消）', 'every method takes a chord Context (cancellation)'))]
