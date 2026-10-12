# pi-coding-agent deep dive. Same section schema as deep_agent.py; files: (path, regex, symbol, zh, en)
from figs5 import ext_events, ext_interceptable, api_methods, iface_members, rpc_commands, entry_types
C = 'packages/coding-agent/src/'
SLIDE_KEYS = ['ca_startup', 'ca_session', 'ca_runtime', 'ca_tools', 'ca_jsonl', 'ca_extapi', 'ca_rpc', 'ca_config']

_EV = len(ext_events()); _IC = len(ext_interceptable()); _AM = len(api_methods()) + 1
_RPC = sum(len(c) for _, c in rpc_commands()); _RG = len(rpc_commands()); _ET = len(entry_types())
_CTX = len(iface_members('ExtensionContext')); _UI = len(iface_members('ExtensionUIContext'))

INTRO = dict(
 takeaway=("`pi-coding-agent` 是产品本身：`pi` 命令、SDK 与 RPC 服务器都从这里出来。它把 `pi-agent-core` 的通用 `Agent` 装配成一个编码智能体——加上会话树（JSONL）、内置工具、扩展系统、设置与资源加载，以及 interactive / print / json / rpc 四种运行模式。",
           "`pi-coding-agent` is the product: the `pi` command, the SDK and the RPC server all come from here. It turns the generic `Agent` from `pi-agent-core` into a coding agent — adding the session tree (JSONL), built-in tools, the extension system, settings and resource loading, and four run modes: interactive, print, json and rpc."),
 role=("位于最上层：依赖 `pi-agent-core`、`pi-ai`、`pi-tui`，以及 `pi-mcp`、`pi-codemode`、`chord`。这里的核心类是 `AgentSession`（一次会话）和 `AgentSessionRuntime`（可替换会话的宿主）。", "The top layer: depends on `pi-agent-core`, `pi-ai`, `pi-tui`, plus `pi-mcp`, `pi-codemode` and `chord`. The central classes are `AgentSession` (one session) and `AgentSessionRuntime` (the host that can swap sessions)."),
)

SECTIONS = [
dict(id="ca-arch", group="arch", layer="coding", diagram="ca_arch",
 title=("模块结构", "Module structure"),
 takeaway=("四个入口共用一个内核：`cli.ts`（`pi` 命令）与 `rpc-entry.ts` 都进入 `main.ts`；`index.ts` 是 SDK 入口。真正的逻辑在 `core/`，三种 UI 形态在 `modes/`。",
           "Four entry points share one core: `cli.ts` (the `pi` command) and `rpc-entry.ts` both enter `main.ts`; `index.ts` is the SDK entry. The real logic lives in `core/`; the three UI shapes live in `modes/`."),
 points=[
  ("`core/agent-session.ts` 是 core/ 里最大的文件（interactive 模式的 `interactive-mode.ts` 更大）：它持有 `Agent`、`SessionManager`、`ExtensionRunner` 与模型运行时，并负责重试、压缩和排队消息。", "`core/agent-session.ts` is the largest file in core/ (only interactive mode's `interactive-mode.ts` is bigger): it owns the `Agent`, the `SessionManager`, the `ExtensionRunner` and the model runtime, and handles retry, compaction and queued messages."),
  ("`rpc-entry.ts` 只做一件事：调用 `main([\"--mode\", \"rpc\", …])`，并通过 `./rpc-entry` 导出路径对外提供。", "`rpc-entry.ts` does one thing: call `main([\"--mode\", \"rpc\", …])`; it is published as the `./rpc-entry` export path."),
  ("`src/extensions/` 里是随包附带的内置扩展（MCP、codemode、tool-search 等），走的是和用户扩展相同的 API。", "`src/extensions/` holds the bundled built-in extensions (MCP, codemode, tool-search …); they use the same API as user extensions."),
 ],
 how=[
  ("`pi` → `setupCli()` → `main(argv)`：解析参数、决定模式、建会话。", "`pi` → `setupCli()` → `main(argv)`: parse args, pick a mode, build the session."),
  ("SDK 用户直接调用 `createAgentSession()` 或 `createAgentSessionRuntime()`，跳过 CLI。", "SDK users call `createAgentSession()` or `createAgentSessionRuntime()` directly and skip the CLI."),
  ("所有模式拿到的都是同一个 `AgentSessionRuntime`，区别只在输入输出方式。", "Every mode receives the same `AgentSessionRuntime`; they differ only in how input and output flow."),
 ],
 files=[
  (C + "cli/setup.ts", r"^export function setupCli\(", "setupCli()", "bin 入口的准备工作", "bin-entry setup"),
  (C + "main.ts", r"^export async function main\(", "main()", "CLI 主流程", "the CLI main flow"),
  (C + "rpc-entry.ts", r"--mode", "main([\"--mode\",\"rpc\"])", "RPC 入口", "RPC entry"),
  (C + "index.ts", r"createAgentSession", "export …", "SDK 入口", "SDK entry"),
  (C + "core/agent-session.ts", r"^export class AgentSession\b", "AgentSession", "一次会话的全部状态", "all state of one session"),
 ]),

dict(id="ca-startup", group="flows", layer="modes", diagram="ca_startup",
 title=("CLI 启动流程", "CLI start-up"),
 takeaway=("`main()` 是一条直线：先处理一次性命令，再解析参数、决定模式、跑迁移、读设置、建 `SessionManager`、确认项目信任、创建 runtime，最后把 runtime 交给 RPC、interactive 或 print 模式。",
           "`main()` is a straight line: handle one-shot commands, then parse args, resolve the mode, run migrations, load settings, create the `SessionManager`, settle project trust, create the runtime, and hand it to RPC, interactive or print mode."),
 points=[
  ("`resolveAppMode()` 同时看参数和 stdin/stdout 是否为 TTY：`-p`、或 stdin / stdout 任一不是 TTY 时走 print，`--mode json` / `--mode rpc` 显式指定。", "`resolveAppMode()` looks at both args and whether stdin/stdout are TTYs: `-p`, or a non-TTY stdin or stdout, means print; `--mode json` / `--mode rpc` are explicit."),
  ("`runMigrations(cwd)` 在任何会话读写之前执行，迁移旧的认证文件、会话目录、工具目录、按键配置与扩展布局。", "`runMigrations(cwd)` runs before any session I/O and migrates old auth files, session directories, tool dirs, keybinding config and extension layout."),
  ("项目信任（`ProjectTrustStore`）决定是否加载 `<cwd>/.pi/` 下的设置与扩展；它在创建 runtime 之前确定。", "Project trust (`ProjectTrustStore`) decides whether settings and extensions under `<cwd>/.pi/` load at all; it is settled before the runtime is created."),
  ("`prepareInitialMessage()` 把命令行里的文字、`@file` 附件和管道输入合成第一条用户消息。", "`prepareInitialMessage()` combines command-line text, `@file` attachments and piped stdin into the first user message."),
 ],
 how=[
  ("`parseArgs(argv)` → `resolveAppMode(parsed, stdinIsTTY, stdoutIsTTY)`。", "`parseArgs(argv)` → `resolveAppMode(parsed, stdinIsTTY, stdoutIsTTY)`."),
  ("`createSessionManager()`：按 `--no-session` / `--fork` / `--session` / `--resume` / `--continue` 选择内存会话、分叉、打开指定会话或选择器。", "`createSessionManager()`: in-memory, fork, open a given session or show the picker according to `--no-session` / `--fork` / `--session` / `--resume` / `--continue`."),
  ("`createAgentSessionRuntime()` 构造 services 与第一个 `AgentSession`。", "`createAgentSessionRuntime()` builds the services and the first `AgentSession`."),
  ("按模式分派：`runRpcMode(runtime)`、`new InteractiveMode(runtime).run()` 或 `runPrintMode(runtime, …)`。", "Dispatch by mode: `runRpcMode(runtime)`, `new InteractiveMode(runtime).run()` or `runPrintMode(runtime, …)`."),
 ],
 files=[
  (C + "cli/args.ts", r"^export function parseArgs\(", "parseArgs()", "参数解析", "argument parsing"),
  (C + "main.ts", r"^function resolveAppMode\(", "resolveAppMode()", "选择运行模式", "pick the run mode"),
  (C + "main.ts", r"^async function prepareInitialMessage\(", "prepareInitialMessage()", "第一条消息", "the first message"),
  (C + "main.ts", r"^export async function createSessionManager\(", "createSessionManager()", "打开 / 新建会话", "open / create a session"),
  (C + "migrations.ts", r"^export function runMigrations\(", "runMigrations()", "布局迁移", "layout migrations"),
  (C + "core/trust-manager.ts", r"^export class ProjectTrustStore", "ProjectTrustStore", "项目信任", "project trust"),
 ]),

dict(id="ca-session", group="arch", layer="coding", diagram="ca_session",
 title=("AgentSession 如何装配 Agent", "How AgentSession wires the Agent"),
 takeaway=("`AgentSession` 不改写 `Agent` 的循环，而是把每个钩子接到编码场景的实现上：`streamFn` 走 `ModelRuntime`，`transformContext` 交给扩展的 `context` 事件，`beforeToolCall` / `afterToolCall` 交给 `tool_call` / `tool_result` 事件，`subscribe()` 把每条消息写进会话文件。",
           "`AgentSession` does not rewrite the `Agent` loop; it plugs each hook into a coding-specific implementation: `streamFn` goes through `ModelRuntime`, `transformContext` to the extensions' `context` event, `beforeToolCall` / `afterToolCall` to the `tool_call` / `tool_result` events, and `subscribe()` writes every message into the session file."),
 points=[
  ("事件先交给扩展、再交给 UI 监听器（`_handleAgentEvent`），所以扩展总能先看到并改写。", "Events reach extensions before UI listeners (`_handleAgentEvent`), so extensions always see and rewrite first."),
  ("一次运行结束后由 `_handlePostAgentRun()` 决定是否再跑一次：可重试错误 → 退避重试；超出上下文或超过阈值 → 压缩；还有排队消息 → `continue()`。", "After a run, `_handlePostAgentRun()` decides whether to go again: retryable error → back off and retry; context overflow or over threshold → compact; queued messages → `continue()`."),
  ("扩展的 `tool_call` 处理器出错时，工具调用会被阻止，而不是放行。", "If an extension's `tool_call` handler throws, the tool call is blocked rather than allowed."),
  ("`turn_end` 是边界点：扩展可以在两轮之间往会话里追加条目。", "`turn_end` is a boundary: extensions may append entries to the session between turns."),
 ],
 how=[
  ("`createAgentSession()`（sdk.ts）构造 `new Agent({ streamFn, convertToLlm, … })`，再把它交给 `new AgentSession(…)`。", "`createAgentSession()` (sdk.ts) builds `new Agent({ streamFn, convertToLlm, … })` and passes it to `new AgentSession(…)`."),
  ("`AgentSession` 构造时安装其余钩子并 `agent.subscribe()`。", "The `AgentSession` constructor installs the remaining hooks and calls `agent.subscribe()`."),
  ("`prompt(text)`：运行中按 `streamingBehavior` 转成 `steer()` / `followUp()`，空闲时开始新一轮。", "`prompt(text)`: while running it becomes `steer()` / `followUp()` per `streamingBehavior`; when idle it starts a run."),
  ("运行结束 → `_handlePostAgentRun()` → 必要时再次 `continue()`，直到 `agent_settled`。", "Run ends → `_handlePostAgentRun()` → `continue()` again if needed, until `agent_settled`."),
 ],
 files=[
  (C + "core/sdk.ts", r"^export async function createAgentSession\(", "createAgentSession()", "构造 Agent 与 AgentSession", "build Agent and AgentSession"),
  (C + "core/agent-session.ts", r"^export class AgentSession\b", "AgentSession", "钩子与状态", "hooks and state"),
  (C + "core/agent-session.ts", r"async prompt\(text: string", "prompt()", "入口", "entry point"),
  (C + "core/agent-session.ts", r"private async _handlePostAgentRun\(", "_handlePostAgentRun()", "重试 · 压缩 · 排队", "retry · compact · queue"),
  (C + "core/agent-session.ts", r"private async _checkCompaction\(", "_checkCompaction()", "自动压缩判断", "auto-compaction check"),
  (C + "core/agent-session.ts", r"^\tsubscribe\(listener", "subscribe()", "UI 监听", "UI listeners"),
 ]),

dict(id="ca-runtime", group="flows", layer="coding", diagram="ca_runtime",
 title=("AgentSessionRuntime：替换会话", "AgentSessionRuntime: replacing the session"),
 takeaway=("`/new`、`/resume`、`/fork`、导入都不是在原会话上“改”，而是整个换掉：先问扩展是否取消，再关闭旧 `AgentSession`，用新的 `SessionManager` 和新的 services 建一个新 `AgentSession`，最后让 UI 和扩展重新绑定。",
           "`/new`, `/resume`, `/fork` and import never edit the current session; they replace it: ask extensions whether to cancel, shut down the old `AgentSession`, build a fresh one with a new `SessionManager` and fresh services, then let the UI and extensions rebind."),
 points=[
  ("`session_before_switch` / `session_before_fork` 返回 `{ cancel: true }` 时，整个替换中止，方法返回 `{ cancelled: true }`。", "If `session_before_switch` / `session_before_fork` returns `{ cancel: true }`, the replacement stops and the method returns `{ cancelled: true }`."),
  ("旧会话按 abort → `session_shutdown` → `dispose()` 的顺序关闭；扩展的 TUI 组件被同步卸下。", "The old session closes in the order abort → `session_shutdown` → `dispose()`; extension TUI widgets are detached synchronously."),
  ("扩展中捕获的旧 `ctx` 在替换后失效；需要在替换后继续工作的扩展应使用 `withSession` 回调里的新 `ctx`。", "A captured `ctx` goes stale after replacement; extensions that must keep working should use the fresh `ctx` passed to `withSession`."),
 ],
 how=[
  ("`switchSession()` / `newSession()` / `fork()` 先触发对应的 `session_before_*` 事件。", "`switchSession()` / `newSession()` / `fork()` first emit the matching `session_before_*` event."),
  ("打开或新建 `SessionManager`（fork 时 `newSession({ parentSession })` 记录来源）。", "Open or create a `SessionManager` (fork records the origin via `newSession({ parentSession })`)."),
  ("`createAgentSessionServices()` + `createAgentSessionFromServices()` 建新会话。", "`createAgentSessionServices()` + `createAgentSessionFromServices()` build the new session."),
  ("替换 runtime 内的 session / services / diagnostics，再 `rebindSession()`。", "Swap session / services / diagnostics inside the runtime, then `rebindSession()`."),
 ],
 files=[
  (C + "core/agent-session-runtime.ts", r"^export class AgentSessionRuntime", "AgentSessionRuntime", "可替换会话的宿主", "the host that swaps sessions"),
  (C + "core/agent-session-runtime.ts", r"^\tasync switchSession\(", "switchSession()", "切换 / 恢复", "switch / resume"),
  (C + "core/agent-session-runtime.ts", r"^\tasync fork\(", "fork()", "分叉", "fork"),
  (C + "core/agent-session-runtime.ts", r"^export async function createAgentSessionRuntime\(", "createAgentSessionRuntime()", "首次创建", "first creation"),
  (C + "core/agent-session-services.ts", r"^export async function createAgentSessionServices\(", "createAgentSessionServices()", "模型运行时 · 设置 · 资源", "model runtime · settings · resources"),
 ]),

dict(id="ca-tools", group="arch", layer="coding", diagram="ca_tools",
 title=("内置工具", "Built-in tools"),
 takeaway=("8 个内置工具（read、bash、powershell、edit、write、grep、find、ls），默认启用 read / bash / edit / write。所有输出都经过统一截断（2000 行或 50KB），文件与进程操作通过可替换的 `*Operations` 接口完成。",
           "Eight built-in tools (read, bash, powershell, edit, write, grep, find, ls), with read / bash / edit / write on by default. All output goes through one truncation policy (2000 lines or 50 KB), and file and process access goes through swappable `*Operations` interfaces."),
 points=[
  ("`read` 从头截断（`truncateHead`），`bash` 从尾截断（`truncateTail`）——命令最后的输出通常最重要。", "`read` truncates from the head (`truncateHead`), `bash` from the tail (`truncateTail`) — the end of a command's output usually matters most."),
  ("`*Operations` 接口让 SDK 宿主把文件系统和 shell 换成远程、容器或测试实现，而不改工具逻辑。", "The `*Operations` interfaces let SDK hosts swap the filesystem and shell for remote, container or test implementations without touching tool logic."),
  ("扩展用 `pi.registerTool()` 注册的工具与内置工具并列，可通过 `setActiveTools()` 开关。", "Tools registered by extensions via `pi.registerTool()` sit alongside the built-ins and are toggled with `setActiveTools()`."),
 ],
 how=[
  ("`createAllTools(cwd, options)` 返回 `Record<ToolName, Tool>`；`createCodingTools()` / `createReadOnlyTools()` 是常用子集。", "`createAllTools(cwd, options)` returns `Record<ToolName, Tool>`; `createCodingTools()` / `createReadOnlyTools()` are the common subsets."),
  ("工具执行结果 → 截断 → 必要时写临时文件并在结果里给出路径。", "Tool result → truncation → when needed, the full output goes to a temp file and the result names its path."),
  ("`afterToolCall` 再把结果交给扩展的 `tool_result` 事件。", "`afterToolCall` then hands the result to the extensions' `tool_result` event."),
 ],
 files=[
  (C + "core/tools/index.ts", r"^export type ToolName = ", "ToolName", "8 个工具名", "the eight tool names"),
  (C + "core/tools/index.ts", r"^export function createAllTools\(", "createAllTools()", "工具工厂", "tool factory"),
  (C + "core/tools/truncate.ts", r"^export const DEFAULT_MAX_LINES", "DEFAULT_MAX_LINES", "2000 行 / 50KB", "2000 lines / 50 KB"),
  (C + "core/tools/truncate.ts", r"^export function truncateTail\(", "truncateTail()", "bash 的尾部截断", "tail truncation for bash"),
  (C + "core/tools/edit.ts", r"^export ", "edit", "精确替换", "exact replacement"),
 ]),

dict(id="ca-jsonl", group="types", layer="coding", diagram="ca_jsonl",
 title=("会话文件：JSONL 格式", "The session file: JSONL format"),
 takeaway=(f"每个会话是一个追加写入的 JSONL 文件：第 1 行是会话头（`version: 3`），之后每行一个条目，共 {_ET} 种条目类型。条目用 `id` / `parentId` 组成树，分支、标签和压缩摘要都只是新的条目。",
           f"Each session is an append-only JSONL file: line 1 is the header (`version: 3`), then one entry per line across {_ET} entry types. Entries form a tree through `id` / `parentId`; branches, labels and compaction summaries are just more entries."),
 points=[
  ("文件按 cwd 分目录存放在 `~/.pi/agent/sessions/` 下，文件名带时间戳与 UUIDv7。", "Files live under `~/.pi/agent/sessions/`, one directory per cwd, named with a timestamp and a UUIDv7."),
  ("写入是惰性的：出现第一条 user 或 assistant 消息之前不落盘，首次写入用 `wx` 标志，避免并发覆盖。", "Writes are lazy: nothing hits disk before the first user or assistant message, and the first write uses the `wx` flag to avoid clobbering."),
  ("读取时按版本迁移（v1 → v2 → v3），必要时整文件重写，然后从叶子沿 `parentId` 回溯得到当前上下文。", "On load, entries migrate by version (v1 → v2 → v3), the file is rewritten if needed, and the current context is rebuilt by walking `parentId` back from the leaf."),
 ],
 how=[
  ("`SessionManager.create()` / `open()` → `loadEntriesFromFile()`。", "`SessionManager.create()` / `open()` → `loadEntriesFromFile()`."),
  ("`migrateSessionEntries()` 原地升级到 `CURRENT_SESSION_VERSION`。", "`migrateSessionEntries()` upgrades in place to `CURRENT_SESSION_VERSION`."),
  ("`buildSessionContext()` 处理压缩条目与分支摘要，产出发给模型的消息列表。", "`buildSessionContext()` applies compaction entries and branch summaries to produce the messages sent to the model."),
 ],
 files=[
  (C + "core/session-manager.ts", r"^export const CURRENT_SESSION_VERSION", "CURRENT_SESSION_VERSION", "= 3", "= 3"),
  (C + "core/session-manager.ts", r"^export type SessionEntry =", "SessionEntry", f"{_ET} 种条目", f"{_ET} entry types"),
  (C + "core/session-manager.ts", r"^export function migrateSessionEntries\(", "migrateSessionEntries()", "版本迁移", "version migration"),
  (C + "core/session-manager.ts", r"^export function buildSessionContext\(", "buildSessionContext()", "树 → 上下文", "tree → context"),
  (C + "core/session-manager.ts", r"^export class SessionManager", "SessionManager", "读写与分支", "I/O and branching"),
 ]),

dict(id="ca-extapi", group="arch", layer="ext", diagram="ca_extapi",
 title=("扩展 API：能力面与事件", "The extension API: capabilities and events"),
 takeaway=(f"扩展是一个默认导出函数 `(pi) => {{ … }}`。`pi` 上有 {_AM} 个方法（注册工具 / 命令 / 快捷键 / provider / 渲染器，行动，读取），`pi.on()` 可以订阅 {_EV} 种事件，其中 {_IC} 种的处理器可以返回结果来改写或拦截。",
           f"An extension is a default-exported function `(pi) => {{ … }}`. `pi` has {_AM} methods (register tools / commands / shortcuts / providers / renderers, act, read), and `pi.on()` subscribes to {_EV} events, {_IC} of which let handlers return a result that rewrites or intercepts."),
 points=[
  (f"每个处理器的第二个参数是 `ctx`：`ExtensionContext` 有 {_CTX} 个成员（cwd、模型、会话、`ui` …），命令处理器拿到的 `ExtensionCommandContext` 还能新建 / 分叉 / 切换会话。", f"Every handler's second argument is `ctx`: `ExtensionContext` has {_CTX} members (cwd, model, session, `ui` …); command handlers get `ExtensionCommandContext`, which can also create / fork / switch sessions."),
  (f"`ctx.ui` 有 {_UI} 个成员：对话框、通知、状态栏、widget、自定义组件；在 RPC 模式下它们变成 `extension_ui_request`。", f"`ctx.ui` has {_UI} members: dialogs, notifications, status, widgets, custom components; in RPC mode they become `extension_ui_request`s."),
  ("可拦截事件的典型用法：`input` 改写或接管输入，`tool_call` 阻止工具，`context` 替换本次上下文，`session_before_*` 取消会话操作。", "Typical interceptions: `input` rewrites or handles input, `tool_call` blocks a tool, `context` replaces this request's context, `session_before_*` cancels a session operation."),
 ],
 how=[
  ("加载器用 jiti 导入扩展文件，调用工厂函数，把注册内容收集到 `ExtensionRunner`。", "The loader imports extension files with jiti, calls the factory, and collects registrations into the `ExtensionRunner`."),
  ("`AgentSession` 在各个时机调用 `runner.emit*()`；有结果的事件按扩展顺序依次处理。", "`AgentSession` calls `runner.emit*()` at each point; result-returning events run through extensions in order."),
  ("`/reload` 重新执行整个加载过程；旧的 `pi` 与 `ctx` 随之失效。", "`/reload` reruns the whole load; the old `pi` and `ctx` become stale."),
 ],
 files=[
  (C + "core/extensions/types.ts", r"^export interface ExtensionAPI\b", "ExtensionAPI", "pi 对象", "the pi object"),
  (C + "core/extensions/types.ts", r"^export interface ExtensionContext\b", "ExtensionContext", "处理器的 ctx", "the handler ctx"),
  (C + "core/extensions/types.ts", r"^export interface ExtensionUIContext\b", "ExtensionUIContext", "ctx.ui", "ctx.ui"),
  (C + "core/extensions/types.ts", r"^export interface ToolDefinition<", "ToolDefinition", "registerTool 的参数", "registerTool's argument"),
  (C + "core/extensions/runner.ts", r"^export class ExtensionRunner", "ExtensionRunner", "事件分发", "event dispatch"),
  (C + "core/extensions/loader.ts", r"^export async function loadExtensions\(", "loadExtensions()", "加载", "loading"),
 ]),

dict(id="ca-rpc", group="flows", layer="modes", diagram="ca_rpc",
 title=("RPC 协议", "The RPC protocol"),
 takeaway=(f"`pi --mode rpc` 把智能体变成一个子进程服务：stdin 每行一个 JSON 命令（{_RPC} 种，分 {_RG} 组），stdout 每行一个 JSON——命令响应、会话事件流、扩展 UI 请求混在同一条流里，靠 `type` 字段区分。",
           f"`pi --mode rpc` turns the agent into a subprocess service: one JSON command per stdin line ({_RPC} types in {_RG} groups), one JSON value per stdout line — command responses, the session event stream and extension UI requests share one stream, told apart by `type`."),
 points=[
  ("`prompt` 不等运行结束：预检通过就回响应（带 `disposition`），之后的一切以事件到达。", "`prompt` does not wait for the run: it responds once preflight passes (with a `disposition`), and everything after arrives as events."),
  ("需要回答的扩展 UI（select / confirm / input / editor）发出 `extension_ui_request`，宿主用同一个 `id` 回 `extension_ui_response`；通知类请求不需要回答。", "Extension UI that needs an answer (select / confirm / input / editor) emits an `extension_ui_request`; the host replies with an `extension_ui_response` carrying the same `id`. Notification-style requests need no answer."),
  ("JSONL 读取器只按 `\\n` 切分：JSON 字符串里合法的 U+2028 / U+2029 不会把一行切断（Node 的 readline 会）。", "The JSONL reader splits on `\\n` only: U+2028 / U+2029, legal inside JSON strings, never break a line (Node's readline would)."),
  ("TypeScript 宿主可以直接用 `RpcClient`，它负责启动子进程、配对请求与响应。", "TypeScript hosts can use `RpcClient`, which spawns the process and pairs requests with responses."),
 ],
 how=[
  ("`runRpcMode(runtime)` 接管 stdout，订阅会话事件并逐条输出 `toJsonEvent(event)`。", "`runRpcMode(runtime)` takes over stdout, subscribes to session events and writes `toJsonEvent(event)` for each."),
  ("`attachJsonlLineReader(stdin)` 逐行解析命令，`handleCommand()` 按 `type` 分派。", "`attachJsonlLineReader(stdin)` parses commands line by line; `handleCommand()` dispatches on `type`."),
  ("响应形如 `{ type: \"response\", id, command, success, data | error }`。", "Responses look like `{ type: \"response\", id, command, success, data | error }`."),
 ],
 files=[
  (C + "modes/rpc/rpc-types.ts", r"^export type RpcCommand =", "RpcCommand", f"{_RPC} 种命令", f"{_RPC} commands"),
  (C + "modes/rpc/rpc-types.ts", r"^export type RpcResponse =", "RpcResponse", "响应", "responses"),
  (C + "modes/rpc/rpc-mode.ts", r"^export async function runRpcMode\(", "runRpcMode()", "服务循环", "the service loop"),
  (C + "modes/rpc/jsonl.ts", r"^export function attachJsonlLineReader\(", "attachJsonlLineReader()", "按 \\n 切行", "split on \\n"),
  (C + "modes/rpc/rpc-client.ts", r"^export class RpcClient", "RpcClient", "TS 客户端", "TS client"),
 ]),

dict(id="ca-config", group="flows", layer="coding", diagram="ca_config",
 title=("设置、资源与 system prompt", "Settings, resources and the system prompt"),
 takeaway=("配置分全局（`~/.pi/agent/`）和项目（`<cwd>/.pi/`）两层，项目层只在项目受信任时生效。`DefaultResourceLoader.reload()` 依次确定信任、重读设置、解析 pi 包、加载扩展与其余资源；system prompt 由一组有序、可单独替换的分段组成。",
           "Configuration has a global layer (`~/.pi/agent/`) and a project layer (`<cwd>/.pi/`); the project layer applies only to trusted projects. `DefaultResourceLoader.reload()` settles trust, re-reads settings, resolves pi packages, then loads extensions and the other resources; the system prompt is a set of ordered, independently replaceable sections."),
 points=[
  ("`deepMergeSettings(global, project)`：项目值覆盖全局值，嵌套对象逐键合并。", "`deepMergeSettings(global, project)`: project values win, nested objects merge key by key."),
  ("pi 包可以来自 `npm:`、`git:` 或本地路径，一个包里可以同时带扩展、技能、提示模板和主题。", "pi packages come from `npm:`, `git:` or local paths; one package can ship extensions, skills, prompt templates and themes together."),
  ("`SYSTEM.md` 整段替换默认开头，并去掉 tools / rules / docs 分段；`APPEND_SYSTEM.md` 只追加 `<addendum>`。两者都是项目优先于全局。", "`SYSTEM.md` replaces the default preamble and drops the tools / rules / docs sections; `APPEND_SYSTEM.md` only adds `<addendum>`. For both, project beats global."),
  ("上下文文件（AGENTS.md、CLAUDE.md …）从全局目录和 cwd 的每一级祖先目录收集，放进 `<project_context>`。", "Context files (AGENTS.md, CLAUDE.md …) are collected from the global dir and every ancestor of cwd into `<project_context>`."),
 ],
 how=[
  ("`createAgentSessionServices()` 创建 `SettingsManager`、`ModelRuntime` 与 `DefaultResourceLoader`，并调用 `reload()`。", "`createAgentSessionServices()` creates the `SettingsManager`, `ModelRuntime` and `DefaultResourceLoader`, and calls `reload()`."),
  ("`reload()`：`resolveProjectTrust` → `settingsManager.reload()` → `packageManager.resolve()` → CLI 路径 → `loadFinalExtensionSet()` → 技能 / 提示 / 主题。", "`reload()`: `resolveProjectTrust` → `settingsManager.reload()` → `packageManager.resolve()` → CLI paths → `loadFinalExtensionSet()` → skills / prompts / themes."),
  ("`buildSystemPromptSections()` 组装 preamble、tools、rules、docs、addendum、project_context、skills、cwd 与扩展追加的分段。", "`buildSystemPromptSections()` assembles preamble, tools, rules, docs, addendum, project_context, skills, cwd and extension-added sections."),
 ],
 files=[
  (C + "core/settings-manager.ts", r"^function deepMergeSettings\(", "deepMergeSettings()", "两层合并", "two-layer merge"),
  (C + "core/settings-manager.ts", r"^export class SettingsManager", "SettingsManager", "设置读写", "settings I/O"),
  (C + "core/resource-loader.ts", r"^\tasync reload\(options", "reload()", "资源加载流程", "the load pipeline"),
  (C + "core/resource-loader.ts", r"\"SYSTEM.md\"", "SYSTEM.md", "项目优先", "project first"),
  (C + "core/system-prompt.ts", r"^export function buildSystemPromptSections\(", "buildSystemPromptSections()", "分段组装", "section assembly"),
 ]),
]

EXT_POINTS = [
 ("pi.registerTool()", ("增加模型可调用的工具，与内置工具并列。", "Add tools the model can call, alongside the built-ins.")),
 ("pi.on(event, handler)", (f"{_EV} 种事件，{_IC} 种可返回结果来改写或拦截。", f"{_EV} events; {_IC} can return a result to rewrite or intercept.")),
 ("pi.registerCommand() · registerShortcut()", ("斜杠命令与快捷键。", "Slash commands and keyboard shortcuts.")),
 ("pi.registerProvider() · registerVirtualModel()", ("接入新的模型 provider 或虚拟模型路由。", "Add model providers or virtual-model routing.")),
 ("ctx.ui.custom() · setWidget()", ("在 TUI 中放入自定义组件。", "Put custom components into the TUI.")),
 ("*Operations", ("SDK 宿主替换文件系统与 shell 的实现。", "SDK hosts swap the filesystem and shell implementations.")),
 ("SYSTEM.md · APPEND_SYSTEM.md · AGENTS.md", ("不写代码也能改 system prompt。", "Change the system prompt without code.")),
 ("--mode rpc", (f"作为子进程嵌入任何语言的宿主：{_RPC} 种 JSONL 命令。", f"Embed as a subprocess from any language: {_RPC} JSONL commands.")),
]
XREF = [('agent-core', ('AgentSession 装配的 Agent 与循环', 'the Agent and loop that AgentSession wires up')),
        ('pi-ai', ('ModelRuntime 背后的模型与流', 'the models and streams behind ModelRuntime')),
        ('tui', ('interactive 模式用的终端 UI 库', 'the terminal UI library used by interactive mode'))]
