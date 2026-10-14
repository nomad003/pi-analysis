# pi-codemode deep dive. Same section schema as deep_agent.py; files: (path, regex, symbol, zh, en)
from figs8 import total_loc, num, CAC, _ca
U = 'packages/codemode/src/'
CA = 'packages/coding-agent/src/extensions/codemode/'
SLIDE_KEYS = ['cm_arch', 'cm_sandbox', 'cm_exec', 'cm_bridge', 'cm_prelude', 'cm_types', 'cm_decl', 'cm_pi']
_LOC = total_loc(); _CAL = total_loc(CAC); _TO = num('runtime/host.ts', 'DEFAULT_TIMEOUT_MS')

INTRO = dict(
 takeaway=("`pi-codemode` 让模型写一段 JavaScript 来调用工具，而不是一次调用一个工具。脚本跑在 worker 线程里的 QuickJS 虚拟机（独立的 wasm 实例）中，唯一的能力就是宿主注入的工具与 globals——没有计时器、网络、文件系统或模块。包里还有把 JSON Schema 渲染成 TypeScript 声明的工具，好让模型知道怎么调用。",
           "`pi-codemode` lets the model write a piece of JavaScript that calls tools, instead of calling one tool at a time. The script runs in a QuickJS VM (a separate wasm instance) inside a worker thread, and its only capability is the tools and globals the host injects — no timers, network, filesystem or modules. The package also renders JSON Schemas as TypeScript declarations so the model knows how to call them."),
 role=(f"共 {_LOC:,} 行 TypeScript，唯一的运行时依赖是 `quickjs-wasi`；不依赖其他 pi 包。pi 内只有 `coding-agent` 的 `codemode` 工具（{_CAL:,} 行）使用它，而它又是 MCP 工具的默认调用方式。",
       f"{_LOC:,} lines of TypeScript; the only runtime dependency is `quickjs-wasi`, and no other pi package. Inside pi, only `coding-agent`'s `codemode` tool ({_CAL:,} lines) uses it — which in turn is the default way MCP tools are called."),
)

SECTIONS = [
dict(id="cm-arch", group="arch", layer="ext", diagram="cm_arch",
 title=("模块结构", "Module structure"),
 takeaway=("三块：宿主侧（`runtime/host.ts` 的 `CodemodeSandbox` 与 `Execution`、消息协议、wasm 加载）、沙箱内（`runtime/worker.ts` 与在 VM 里执行的 `prelude-source.ts`）、给模型看的文本（`declarations.ts`、`source.ts`、`identifier.ts`）。四个导入路径分别对应整体、声明渲染、源码解析与 worker 入口。",
           "Three blocks: the host side (`CodemodeSandbox` and `Execution` in `runtime/host.ts`, the message protocol, wasm loading), the sandbox (`runtime/worker.ts` and `prelude-source.ts`, which runs inside the VM), and model-facing text (`declarations.ts`, `source.ts`, `identifier.ts`). Four import paths cover the whole package, declaration rendering, source parsing and the worker entry."),
 points=[
  ("最大的文件是 `runtime/prelude-source.ts`：它是一段字符串形式的 JavaScript，在 VM 里搭出 `tools`、`text()`、`store()` 等全部脚本 API。", "The largest file is `runtime/prelude-source.ts`: JavaScript held in a string that builds the whole script API — `tools`, `text()`, `store()` and the rest — inside the VM."),
  ("`./declarations` 与 `./source` 不加载 wasm，宿主可以只用它们生成工具描述或校验脚本，而不启动沙箱。", "`./declarations` and `./source` do not load wasm, so a host can generate tool descriptions or validate scripts without starting a sandbox."),
  ("`./worker` 单独导出，是为了打包场景：打包后的宿主把它作为独立入口，再通过 `workerUrl` 传给沙箱。", "`./worker` is exported separately for bundling: a bundled host makes it a separate entry and passes it to the sandbox as `workerUrl`."),
 ],
 how=[
  ("`new CodemodeSandbox({ tools, globals, timeoutMs, memoryLimitBytes })`。", "`new CodemodeSandbox({ tools, globals, timeoutMs, memoryLimitBytes })`."),
  ("`renderDeclarations({ tools, globals })` 生成放进工具描述的 TypeScript。", "`renderDeclarations({ tools, globals })` produces the TypeScript that goes into the tool description."),
  ("`parseCodemodeSource(input)` 拆出可选的 `// @options:` 行，再 `sandbox.execute(code, { signal, store })`。", "`parseCodemodeSource(input)` splits off an optional `// @options:` line, then `sandbox.execute(code, { signal, store })`."),
 ],
 files=[
  (U + "index.ts", r"runtime/host\.ts", "export …", "包入口", "package entry"),
  (U + "runtime/host.ts", r"^export class CodemodeSandbox", "CodemodeSandbox", "沙箱", "the sandbox"),
  (U + "runtime/worker.ts", r"^async function main\(data: WorkerData\)", "worker main()", "worker 入口", "worker entry"),
  (U + "runtime/prelude-source.ts", r"^export const PRELUDE_SOURCE", "PRELUDE_SOURCE", "VM 内的 API", "the in-VM API"),
  (U + "wasm.ts", r"^export function loadQuickJSWasm\(", "loadQuickJSWasm()", "wasm 加载", "wasm loading"),
 ]),

dict(id="cm-sandbox", group="arch", layer="ext", diagram="cm_sandbox",
 title=("三层隔离", "Three layers of isolation"),
 takeaway=("宿主线程只持有工具表；每次 `execute()` 新建一个 worker 线程，worker 里再创建一个 QuickJS 虚拟机。VM 是独立的 wasm 实例，和宿主的 JavaScript 世界没有共享对象——脚本能做的唯一一件事，就是通过 prelude 闭包里的 `bridge` 请求宿主调用某个工具。",
           "The host thread holds only the tool table; each `execute()` creates a worker thread, and the worker creates a QuickJS VM. The VM is a separate wasm instance with no objects shared with the host's JavaScript world — the only thing a script can do is ask the host, through the `bridge` hidden in the prelude's closure, to call a tool."),
 points=[
  ("worker 的存在是为了不让空转的脚本卡住宿主线程；每次执行都用新 worker，失控的脚本直接被 `terminate()`，不会影响下一次。", "The worker exists so that a spinning script never blocks the host thread; a fresh worker per run means a runaway script is simply `terminate()`d and cannot affect the next run."),
  ("结束时宿主先把共享的 4 字节 `interrupt` 置 1，再 `terminate()`：VM 的中断处理器轮询这个标志，在 wasm 里空转的脚本也能停下。", "On finish the host sets the shared 4-byte `interrupt` to 1 before `terminate()`: the VM's interrupt handler polls that flag, so a script spinning inside wasm stops too."),
  ("`maxStackSize` 让深递归变成可捕获的 `RangeError` 而不是 wasm 陷阱；QuickJS 自己写到 fd 1/2 的诊断被丢弃，不会弄乱宿主的 TUI。", "`maxStackSize` turns deep recursion into a catchable `RangeError` instead of a wasm trap; QuickJS's own diagnostics on fd 1/2 are discarded so they never garble the host's TUI."),
  ("prelude 在脚本运行前冻结所有内建对象，因为它和脚本共用这些对象：被篡改的 `toJSON` 否则可能让 prelude 向宿主发出错误的数据。", "The prelude freezes every built-in before the script runs because it shares them with the script: a patched `toJSON` could otherwise make the prelude send the host malformed data."),
 ],
 how=[
  ("宿主：`new Worker(workerUrl, { workerData })`，workerData 带上编译好的 wasm 模块（结构化克隆时共享代码）。", "Host: `new Worker(workerUrl, { workerData })`; workerData carries the compiled wasm module (structured clone shares the code)."),
  ("worker：`QuickJS.create({ memoryLimit, maxStackSize, interruptHandler, wasi })` → `vm.newFunction(\"bridge\")` → 求值 prelude。", "Worker: `QuickJS.create({ memoryLimit, maxStackSize, interruptHandler, wasi })` → `vm.newFunction(\"bridge\")` → evaluate the prelude."),
  ("prelude 返回 `{ settle, run, stalled }`，worker 用它们驱动脚本。", "The prelude returns `{ settle, run, stalled }`, which the worker uses to drive the script."),
 ],
 files=[
  (U + "runtime/host.ts", r"^class Execution", "Execution", "一次执行", "one run"),
  (U + "runtime/host.ts", r"Atomics\.store\(new Int32Array\(this\.interrupt\), 0, 1\)", "interrupt", "中断标志", "interrupt flag"),
  (U + "runtime/worker.ts", r"const vm = await QuickJS\.create\(\{", "QuickJS.create()", "创建 VM", "creating the VM"),
  (U + "runtime/worker.ts", r"^function discardOutput\(", "discardOutput()", "丢弃引擎输出", "discarding engine output"),
  (U + "runtime/prelude-source.ts", r"\(function lockdown\(\) \{", "lockdown()", "冻结内建对象", "freezing built-ins"),
 ]),

dict(id="cm-exec", group="flows", layer="ext", diagram="cm_exec",
 title=("一次执行", "One execution"),
 takeaway=(f"`execute(code)` 复制当前的工具表，启动计时器（默认 {_TO:,} ms，包括工具耗时），加载 wasm，再启动 worker。worker 创建 VM、求值 prelude、把脚本包进 `async` 函数后运行。结局只有五种：成功，或 `script`、`timeout`、`aborted`、`sandbox` 四类错误；`finish()` 只执行一次。",
           f"`execute(code)` copies the current tool table, starts the timer (default {_TO:,} ms, tool time included), loads wasm and starts the worker. The worker creates the VM, evaluates the prelude, wraps the script in an `async` function and runs it. There are only five endings: success, or one of four errors — `script`, `timeout`, `aborted`, `sandbox`; `finish()` runs exactly once."),
 points=[
  ("VM 里没有计时器和 I/O：如果脚本没结束、又没有挂起的工具调用，它就永远不会结束——`stalled()` 在每次 drain 后检查这种情况并立即判失败。", "The VM has no timers or I/O: if the script has not finished and no tool call is pending, it never will — `stalled()` checks for this after every drain and fails it at once."),
  ("脚本包装成 `(async (tools, console) => {<code>\\n})`，前缀和脚本同在第一行，所以报错的行号与脚本原文一致。", "The script is wrapped as `(async (tools, console) => {<code>\\n})`, with the prefix on the script's first line so reported line numbers match the script as written."),
  ("`execute()` 不会因为脚本失败而 reject，失败以 `{ ok: false }` 返回，并保留失败前的 output 与 calls。", "`execute()` never rejects for script failures; they come back as `{ ok: false }` with the output and calls up to the failure."),
  ("`loadQuickJSWasm()` 每个路径只读取并编译一次；加载失败的 Promise 会被移出缓存，下次重试。", "`loadQuickJSWasm()` reads and compiles once per path; a failed load is evicted from the cache and retried next time."),
 ],
 how=[
  ("`execute(code, { signal, timeoutMs, store })` → `new Execution(…)`：计时器、abort 监听、等待 wasm。", "`execute(code, { signal, timeoutMs, store })` → `new Execution(…)`: timer, abort listener, wait for wasm."),
  ("`start()` → `new Worker()`；监听 message / error / exit。", "`start()` → `new Worker()`; listen for message / error / exit."),
  ("收到 `done` 后先解码值与 store 写入，再 `finish()`：中止 pending 调用 → 置 interrupt → terminate → resolve。", "On `done`, decode the value and store writes first, then `finish()`: abort pending calls → set interrupt → terminate → resolve."),
 ],
 files=[
  (U + "runtime/host.ts", r"^\texecute\(code: string", "execute()", "入口", "entry"),
  (U + "runtime/host.ts", r"^const DEFAULT_TIMEOUT_MS", "DEFAULT_TIMEOUT_MS", "默认截止时间", "default deadline"),
  (U + "runtime/host.ts", r"^\tprivate finish\(", "finish()", "唯一的结束点", "the single exit"),
  (U + "runtime/worker.ts", r"\(async \(tools, console\) =>", "async wrapper", "脚本包装", "script wrapper"),
  (U + "runtime/prelude-source.ts", r"^\t\tstalled\(\) \{", "stalled()", "死等检测", "stall detection"),
  (U + "types.ts", r"^export type CodemodeErrorKind", "CodemodeErrorKind", "4 类错误", "four error kinds"),
 ]),

dict(id="cm-bridge", group="flows", layer="ext", diagram="cm_bridge",
 title=("一次工具调用的往返", "One tool call round trip"),
 takeaway=("`await tools.x(args)` 在 VM 里变成 `bridge(\"call\", id, name, argsJson)`，worker 把它转成 `postMessage`，宿主的 `Execution` 查到工具、执行、把结果以 `result` 消息送回，worker 调用 `settle(id)` 并运行挂起的任务，脚本从 `await` 处继续。两边之间只有 JSON 字符串。",
           "`await tools.x(args)` becomes `bridge(\"call\", id, name, argsJson)` in the VM; the worker turns it into a `postMessage`; the host's `Execution` finds the tool, runs it and sends the result back as a `result` message; the worker calls `settle(id)` and runs pending jobs, and the script resumes after `await`. Only JSON strings cross between them."),
 points=[
  ("工具抛出的错误在脚本里变成同一条消息的 `Error`；返回值必须可 JSON 序列化。", "An error thrown by a tool becomes an `Error` with the same message in the script; return values must be JSON-serializable."),
  ("`result.calls` 记录每次工具调用：先记为 `cancelled`，完成后改成 `ok` 或 `error` 并记下耗时——脚本结束时仍未完成的调用保持 `cancelled`。", "`result.calls` records every tool call: it starts as `cancelled` and becomes `ok` or `error` with its duration — calls still running when the script ends stay `cancelled`."),
  ("`tools` 是一个代理：访问不存在的工具名会抛 `TypeError`，列出相近的名字（或在不超过 20 个工具时列出全部）。", "`tools` is a proxy: an unknown tool name throws a `TypeError` that lists near misses (or, with 20 tools or fewer, all of them)."),
  ("globals（如 `searchTools`）走同一条路径，只是 `target: \"global\"`，且不记入 `calls`。", "Globals (such as `searchTools`) take the same path with `target: \"global\"` and are not recorded in `calls`."),
 ],
 how=[
  ("prelude：`caller(\"call\", name)` 生成函数 → JSON.stringify 参数 → `bridge()` → 返回挂进 `pending` 的 Promise。", "Prelude: `caller(\"call\", name)` builds the function → JSON.stringify the args → `bridge()` → return a Promise kept in `pending`."),
  ("宿主：`handleCall()` → `tool.execute(JSON.parse(args), { signal })` → `post({ type: \"result\", id, ok, payload })`。", "Host: `handleCall()` → `tool.execute(JSON.parse(args), { signal })` → `post({ type: \"result\", id, ok, payload })`."),
  ("worker：`settle(id, ok, payload)` → `drain()`。", "Worker: `settle(id, ok, payload)` → `drain()`."),
 ],
 files=[
  (U + "runtime/protocol.ts", r"^export type WorkerToHostMessage", "WorkerToHostMessage", "worker → 宿主", "worker → host"),
  (U + "runtime/protocol.ts", r"^export type HostToWorkerMessage", "HostToWorkerMessage", "宿主 → worker", "host → worker"),
  (U + "runtime/host.ts", r"^\tprivate async handleCall\(", "handleCall()", "执行工具", "running the tool"),
  (U + "runtime/worker.ts", r"vm\.newFunction\(\"bridge\"", "bridge", "VM 内的桥", "the in-VM bridge"),
  (U + "runtime/prelude-source.ts", r"^\t\tsettle\(id, ok, payload\)", "settle()", "恢复脚本", "resuming the script"),
 ]),

dict(id="cm-prelude", group="types", layer="ext", diagram="cm_prelude",
 title=("脚本 API 与限额", "The script API and its limits"),
 takeaway=("脚本能用的只有：`tools` 与 `ALL_TOOLS`、输出函数 `text()` / `image()` / `console.*`、`exit()`、同步的 `store()` / `load()`、宿主配置的 globals，以及 `return`。输出、store 都有硬限额，超出时在脚本里抛错——宿主会一直保存输出直到脚本结束，没有限额的循环打印会拖垮宿主内存。",
           "All a script gets: `tools` and `ALL_TOOLS`, the output functions `text()` / `image()` / `console.*`, `exit()`, synchronous `store()` / `load()`, host-configured globals, and `return`. Output and the store have hard limits that throw inside the script — the host keeps all output until the script ends, so an unbounded print loop would exhaust host memory."),
 points=[
  ("`image()` 接受 base64 的 `data:` URL、`{ image_url }` 对象或 MCP 的 `ImageContent` 块。", "`image()` accepts a base64 `data:` URL, an `{ image_url }` object or an MCP `ImageContent` block."),
  ("`store()` / `load()` 作用于传入的 JSON 快照；成功的执行把写入作为 `storeWrites` 交还宿主，持久化由宿主决定。", "`store()` / `load()` work on the JSON snapshot passed in; successful runs hand writes back as `storeWrites`, and persisting them is up to the host."),
  ("冻结内建对象会破坏“在实例上覆盖原型属性”的普通写法，所以 `name`、`message`、`toJSON` 等常见属性被改成访问器，`this.name = …` 依然可用。", "Freezing built-ins would break ordinary code that overrides prototype properties on instances, so common ones such as `name`, `message` and `toJSON` become accessors and `this.name = …` still works."),
 ],
 how=[
  ("宿主注册 globals 时，名字必须是标识符或 `ns.member`，且不能与保留名冲突。", "When the host registers globals, names must be identifiers or `ns.member`, and may not clash with the reserved names."),
  ("`ns.member` 形式的 globals 被收进一个冻结的 `ns` 对象。", "Globals named `ns.member` are grouped into a frozen `ns` object."),
  ("`spread: true` 的 global 收到全部参数组成的数组，而不是第一个参数。", "A `spread: true` global receives all arguments as an array instead of the first one."),
 ],
 files=[
  (U + "runtime/prelude-source.ts", r"^export const MAX_OUTPUT_CHARS", "MAX_OUTPUT_CHARS", "输出上限", "output limit"),
  (U + "runtime/prelude-source.ts", r"^export const MAX_STORE_VALUE_CHARS", "MAX_STORE_VALUE_CHARS", "store 上限", "store limit"),
  (U + "runtime/prelude-source.ts", r"^\tfunction image\(value\)", "image()", "图片输出", "image output"),
  (U + "runtime/prelude-source.ts", r"^\tfunction store\(key, value\)", "store()", "store", "store"),
  (U + "runtime/host.ts", r"^const RESERVED_GLOBALS", "RESERVED_GLOBALS", "保留名", "reserved names"),
 ]),

dict(id="cm-types", group="types", layer="ext", diagram="cm_types",
 title=("公共类型与源码格式", "Public types and the source format"),
 takeaway=("`CodemodeTool` 只要 `name` 和 `execute(args, { signal })`；schema 只用来渲染声明，值不会被校验。`CodemodeResult` 是一个按 `ok` 区分的联合：成功带 `value` 与 `storeWrites`，失败带 `CodemodeError`；两者都带 `output` 与 `calls`。脚本源码可以以一行 `// @options:` 开头。",
           "`CodemodeTool` needs only `name` and `execute(args, { signal })`; schemas are used to render declarations, values are not validated against them. `CodemodeResult` is a union on `ok`: success carries `value` and `storeWrites`, failure a `CodemodeError`; both carry `output` and `calls`. Script source may start with a `// @options:` line."),
 points=[
  ("`@options` 只认 `max_output_tokens` 与 `timeout_ms` 两个字段；该行被替换为空行，行号不变。", "`@options` accepts only `max_output_tokens` and `timeout_ms`; the line is replaced with a blank one so line numbers stay put."),
  ("`CODEMODE_SOURCE_GRAMMAR` 是一份 Lark 语法，给支持语法约束采样的模型：脚本可以直接按原文生成，而不是转义成 JSON 字符串。", "`CODEMODE_SOURCE_GRAMMAR` is a Lark grammar for models with grammar-constrained sampling: the script is generated as raw text instead of an escaped JSON string."),
  ("工具的 `signal` 在脚本结束（包括没被 await 的调用）、超时、调用方中止或沙箱关闭时触发。", "A tool's `signal` fires when the script finishes (including unawaited calls), times out, the caller aborts, or the sandbox closes."),
 ],
 how=[
  ("`parseCodemodeSource(input)` → `{ code, options }`；坏的 options → `CodemodeSourceError`。", "`parseCodemodeSource(input)` → `{ code, options }`; bad options → `CodemodeSourceError`."),
  ("把 `options.timeoutMs` 传给 `execute()`，`maxOutputTokens` 由宿主自己执行截断。", "Pass `options.timeoutMs` to `execute()`; `maxOutputTokens` is enforced by the host's own truncation."),
  ("检查 `result.ok`，再读 `value` / `error`、`output` 与 `calls`。", "Check `result.ok`, then read `value` / `error`, `output` and `calls`."),
 ],
 files=[
  (U + "types.ts", r"^export interface CodemodeTool \{", "CodemodeTool", "工具", "a tool"),
  (U + "types.ts", r"^export type CodemodeResult", "CodemodeResult", "结果", "the result"),
  (U + "types.ts", r"^export interface CodemodeSandboxOptions", "CodemodeSandboxOptions", "沙箱选项", "sandbox options"),
  (U + "source.ts", r"^export function parseCodemodeSource\(", "parseCodemodeSource()", "源码解析", "source parsing"),
  (U + "source.ts", r"^export const CODEMODE_SOURCE_GRAMMAR", "CODEMODE_SOURCE_GRAMMAR", "Lark 语法", "Lark grammar"),
 ]),

dict(id="cm-decl", group="types", layer="ext", diagram="cm_decl",
 title=("TypeScript 声明", "TypeScript declarations"),
 takeaway=("模型通过 TypeScript 声明学会调用工具：`renderDeclarations()` 把每个工具渲染成 `declare const tools` 的一个成员 `name(args: T): Promise<R>;`，描述变成文档注释，`schemaToType()` 把 JSON Schema 转成类型。MCP 风格的输出 schema 渲染成 `CallToolResult<T>`。",
           "The model learns to call tools from TypeScript declarations: `renderDeclarations()` renders each tool as a member `name(args: T): Promise<R>;` of `declare const tools`, descriptions become doc comments, and `schemaToType()` turns JSON Schema into types. MCP-style output schemas render as `CallToolResult<T>`."),
 points=[
  ("工具名中不合法的标识符字符变成 `_`（`toCodemodeIdentifier`），所以 `my-tool` 在脚本里是 `tools.my_tool`；原名 `tools[\"my-tool\"]` 同样可用。", "Characters that are not valid in identifiers become `_` (`toCodemodeIdentifier`), so `my-tool` is `tools.my_tool` in scripts; the original `tools[\"my-tool\"]` works too."),
  ("渲染有上限：输入类型超过 16,000 个字符整个变成 `unknown`；本地 `$ref` 每个 schema 最多展开 32 次，递归引用变成 `unknown`。", "Rendering is bounded: an input type over 16,000 characters becomes `unknown`; local `$ref`s expand at most 32 times per schema, and recursive references become `unknown`."),
  ("用到 `CallToolResult<T>` 时要把 `MCP_TYPESCRIPT_PREAMBLE`（MCP 结果类型的定义）一起放进描述。", "When `CallToolResult<T>` is used, `MCP_TYPESCRIPT_PREAMBLE` (the MCP result type definitions) must go into the description too."),
 ],
 how=[
  ("`renderToolSignature(tool)`：输入类型 + `renderToolOutputType(outputSchema)`。", "`renderToolSignature(tool)`: the input type + `renderToolOutputType(outputSchema)`."),
  ("`mcpStructuredContentSchema()` 识别 MCP 结果 schema（content 数组、布尔 isError、对象 _meta）。", "`mcpStructuredContentSchema()` recognises MCP result schemas (a content array, boolean isError, object _meta)."),
  ("`renderToolSample()` 输出“描述 + 单个工具的声明”，用于工具列表与 `ALL_TOOLS` 条目。", "`renderToolSample()` outputs “description + that tool's declaration”, used for tool listings and `ALL_TOOLS` entries."),
 ],
 files=[
  (U + "declarations.ts", r"^export function renderDeclarations\(", "renderDeclarations()", "整体声明", "all declarations"),
  (U + "declarations.ts", r"^export function renderToolSignature\(", "renderToolSignature()", "单个工具", "one tool"),
  (U + "declarations.ts", r"^export function schemaToType\(", "schemaToType()", "Schema → 类型", "schema → type"),
  (U + "declarations.ts", r"^export const MCP_TYPESCRIPT_PREAMBLE", "MCP_TYPESCRIPT_PREAMBLE", "MCP 类型", "MCP types"),
  (U + "identifier.ts", r"^export function toCodemodeIdentifier\(", "toCodemodeIdentifier()", "名字 → 标识符", "name → identifier"),
 ]),

dict(id="cm-pi", group="arch", layer="ext", diagram="cm_pi",
 title=("在 pi 中的使用", "How pi uses it"),
 takeaway=("`coding-agent` 把它包装成 `codemode` 工具：模型写脚本，脚本里的每次嵌套调用都经过 agent 循环的工具管线（校验、钩子、权限），而只有脚本自己的输出回到模型。pi 还注入 `searchTools()`、`describeTool()`、`describeNamespace()` 与 `models.*`，并把 `store()` 写入保存为会话条目。",
           "`coding-agent` wraps it as the `codemode` tool: the model writes a script, every nested call goes through the agent loop's tool pipeline (validation, hooks, permissions), and only the script's own output returns to the model. pi also injects `searchTools()`, `describeTool()`, `describeNamespace()` and `models.*`, and saves `store()` writes as session entries."),
 points=[
  ("脚本可调用 loadout 中所有可调用的工具（包括 deferred 与 codemode 曝光的工具——MCP 工具默认在此），只有 `codemode` 自己除外。它是 `model-only`，脚本不能再启动脚本。", "Scripts can call every callable tool in the loadout (deferred and codemode-exposure tools included — where MCP tools go by default), except `codemode` itself. It is `model-only`: scripts cannot start scripts."),
  ("嵌套结果交给脚本时：有 `outputSchema` 的工具给 `structuredContent`（带 `isError` 的 MCP 结果也一样），其他工具给文本，失败则 reject。", "Nested results reach the script as: `structuredContent` for tools with an `outputSchema` (MCP results with `isError` too), text for other tools, and a rejection on failure."),
  ("`store()` 写入成为 `codemode-store` 自定义条目；下次执行前从根到当前叶子重放，所以每个分支只看到自己路径上的值。", "`store()` writes become `codemode-store` custom entries; before the next run they are replayed from root to the current leaf, so each branch sees only values from its own path."),
  ("沙箱在第一次调用时才加载（worker 与 wasm），启动时没有成本；超时只来自脚本的 `timeout_ms`，否则不限。", "The sandbox (worker and wasm) loads on the first call, so start-up pays nothing; the only timeout is the script's `timeout_ms`, otherwise none."),
 ],
 how=[
  ("`createCodemodeExtension()` 注册不激活的 `codemode` 工具；`--tools`、`defaultTools`、`setActiveTools()` 或 MCP 扩展激活它。", "`createCodemodeExtension()` registers the inactive `codemode` tool; `--tools`, `defaultTools`, `setActiveTools()` or the MCP extension activate it."),
  ("激活时 `prepareCodemodeLoadout()` 用可调用工具的声明替换描述（`inlineBudget` 控制内联多少；`mode: \"only\"` 列出全部可调用工具，并从请求中去掉激活的 direct 工具的声明）。", "On activation, `prepareCodemodeLoadout()` replaces the description with the callable tools' declarations (`inlineBudget` limits how much is inlined; `mode: \"only\"` lists every callable tool and leaves active direct tools' declarations out of requests)."),
  ("`executeCodemode()`：解析源码 → `new CodemodeSandbox({ tools, globals })` → `execute(code, { signal, store })` → 截断输出、追加 store 条目。", "`executeCodemode()`: parse the source → `new CodemodeSandbox({ tools, globals })` → `execute(code, { signal, store })` → truncate output, append store entries."),
 ],
 files=[
  (CA + "index.ts", r"^export function createCodemodeExtension\(", "createCodemodeExtension()", "扩展入口", "extension entry"),
  (CA + "tool.ts", r"^export function createCodemodeToolDefinition\(", "createCodemodeToolDefinition()", "工具定义", "tool definition"),
  (CA + "tool.ts", r"^function prepareCodemodeLoadout\(", "prepareCodemodeLoadout()", "描述与模式", "description and modes"),
  (CA + "execute.ts", r"await ctx\.executeTool\(tool\.name, args", "ctx.executeTool()", "嵌套调用", "nested calls"),
  (CA + "execute.ts", r"^function createDiscoveryGlobals\(", "createDiscoveryGlobals()", "searchTools 等", "searchTools and friends"),
  (CA + "tool.ts", r"^export const CODEMODE_STORE_ENTRY_TYPE", "CODEMODE_STORE_ENTRY_TYPE", "store 条目", "store entries"),
 ]),
]

EXT_POINTS = [
 ("CodemodeTool", ("name + execute(args, { signal })：脚本里的 tools.<id>。", "name + execute(args, { signal }): tools.<id> in scripts.")),
 ("globals", ("顶层函数或 ns.member，如 pi 的 searchTools、models.*。", "Top-level functions or ns.member, like pi's searchTools and models.*.")),
 ("execute(code, { store })", ("传入 load() 的快照，取回 storeWrites 自行持久化。", "Pass the load() snapshot in, take storeWrites out and persist them yourself.")),
 ("renderDeclarations() · renderToolSample()", ("自己组织给模型的工具描述。", "Build your own tool descriptions for the model.")),
 ("CODEMODE_SOURCE_GRAMMAR", ("给支持语法约束的 provider，让脚本按原文生成。", "For providers with grammar sampling, so scripts come out as raw text.")),
 ("wasm · workerUrl", ("打包或 Bun 编译时自带 wasm 与 worker 入口。", "Ship your own wasm and worker entry when bundling or compiling with Bun.")),
 ("timeoutMs · memoryLimitBytes", ("每个沙箱或每次执行的资源上限。", "Resource limits per sandbox or per run.")),
]
XREF = [('coding-agent', ('codemode 工具：嵌套调用、globals、store 条目与模式', 'the codemode tool: nested calls, globals, store entries and modes')),
        ('mcp', ('MCP 工具默认只能从 codemode 脚本调用', 'MCP tools are callable only from codemode scripts by default'))]
