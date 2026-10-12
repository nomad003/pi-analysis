# pi-agent-core (packages/agent) deep dive. Same section schema as content.py; files: (path, regex, symbol, zh, en)
A = 'packages/agent/src/'
SLIDE_KEYS = ['ac_arch', 'ac_state', 'ac_turn', 'ac_events', 'ac_queues', 'ac_parallel', 'ac_proxy', 'ac_types']

INTRO = dict(
 takeaway=("`pi-agent-core` 是一个与“编码”无关的通用 Agent 内核：一个 `Agent` 类管状态和队列，一个 `runLoop()` 驱动“请求 → 工具 → 下一轮”，所有策略（上下文变换、权限、压缩、何时停）都通过 `AgentLoopConfig` 钩子注入。",
           "`pi-agent-core` is a general agent kernel that knows nothing about coding: an `Agent` class owns state and queues, `runLoop()` drives request → tools → next turn, and every policy (context transforms, permissions, compaction, when to stop) is injected through `AgentLoopConfig` hooks."),
 role=("位于 `pi-ai`（模型与流）之上、`pi-coding-agent`（产品）之下。只有一个运行时依赖：`pi-ai`。", "Sits above `pi-ai` (models and streams) and below `pi-coding-agent` (the product). One runtime dependency: `pi-ai`."),
)

SECTIONS = [
dict(id="ac-arch", group="arch", layer="agent", diagram="ac_arch",
 title=("模块结构", "Module structure"),
 takeaway=("6 个源文件、单一导出入口：`agent.ts`（有状态的外壳）调用 `agent-loop.ts`（无状态的循环），两者共享 `types.ts`；`proxy.ts` 与 `stream-fn.ts` 提供可替换的 `StreamFn`。",
           "Six source files and a single export entry: `agent.ts` (the stateful shell) calls `agent-loop.ts` (the stateless loop), both share `types.ts`; `proxy.ts` and `stream-fn.ts` provide swappable `StreamFn`s."),
 points=[
  ("`index.ts` 只有 5 行：`export *` 四个模块，再单独导出 `setDefaultStreamFn`（`getDefaultStreamFn` 不导出）。", "`index.ts` is five lines: `export *` from four modules plus `setDefaultStreamFn` alone (`getDefaultStreamFn` stays internal)."),
  ("循环本身不持有状态：`agentLoop()` 返回 `EventStream<AgentEvent, AgentMessage[]>`，`runAgentLoop()` 接受一个 `emit` 回调——`Agent` 用的是后者。", "The loop holds no state: `agentLoop()` returns an `EventStream<AgentEvent, AgentMessage[]>`, `runAgentLoop()` takes an `emit` callback — `Agent` uses the latter."),
  ("对 `pi-ai` 的依赖集中在四处：transcript 工具（工具声明 / system 基线）、`validateToolArguments`、`EventStream` 与类型。", "The `pi-ai` dependency is concentrated in four places: transcript helpers (tool declarations, system baseline), `validateToolArguments`, `EventStream`, and types."),
 ],
 how=[
  ("宿主构造 `new Agent({ initialState, streamFn, convertToLlm, … })`。", "The host constructs `new Agent({ initialState, streamFn, convertToLlm, … })`."),
  ("`prompt()` / `continue()` 把当前状态拍成 `AgentContext` 快照，连同由选项组装的 `AgentLoopConfig` 交给 `runAgentLoop()`。", "`prompt()` / `continue()` snapshot state into an `AgentContext` and pass it, with an `AgentLoopConfig` assembled from the options, to `runAgentLoop()`."),
  ("循环通过 `emit` 发出 `AgentEvent`；`Agent.processEvents()` 先更新自身状态，再依次 await 订阅者。", "The loop emits `AgentEvent`s via `emit`; `Agent.processEvents()` updates its own state first, then awaits subscribers in order."),
 ],
 files=[
  (A + "index.ts", r"setDefaultStreamFn", "export *", "唯一入口", "the only entry point"),
  (A + "agent.ts", r"^export class Agent\b", "Agent", "状态、队列、生命周期", "state, queues, lifecycle"),
  (A + "agent-loop.ts", r"^export async function runAgentLoop\(", "runAgentLoop", "循环入口（emit 版本）", "loop entry (emit flavour)"),
  (A + "stream-fn.ts", r"^export function setDefaultStreamFn", "setDefaultStreamFn", "全局默认 StreamFn", "global default StreamFn"),
  (A + "types.ts", r"^export interface AgentLoopConfig", "AgentLoopConfig", "所有钩子的定义", "every hook's definition"),
 ]),

dict(id="ac-lifecycle", group="flows", layer="agent", diagram="ac_state",
 title=("运行生命周期", "Run lifecycle"),
 takeaway=("同一时刻最多一个活动运行：`runWithLifecycle()` 建立 `AbortController` 与 `isStreaming`，执行失败会被转换成一条合成的 error 助手消息而不是向上抛出，`finishRun()` 总在最后清理。",
           "At most one active run at a time: `runWithLifecycle()` sets up the `AbortController` and `isStreaming`; executor failures become a synthesized error assistant message instead of propagating, and `finishRun()` always cleans up."),
 points=[
  ("`prompt()` 在运行中调用会抛错，提示改用 `steer()` 或 `followUp()`——这是唯一的并发入口约束。", "`prompt()` throws while a run is active, pointing at `steer()` or `followUp()` — the single concurrency rule at the entry."),
  ("`isStreaming` 在 `agent_end` 监听器全部完成后才变回 false，所以 `waitForIdle()` 返回时 UI 一定已经处理完最后的事件。", "`isStreaming` turns false only after all `agent_end` listeners settle, so when `waitForIdle()` resolves the UI has handled the final events."),
  ("`handleRunFailure()` 依次发出 `message_start/end`（error 消息）、`turn_end`、`agent_end`，订阅者看到的事件序列与正常结束同构。", "`handleRunFailure()` emits `message_start/end` (the error message), `turn_end` and `agent_end`, so subscribers see the same event shape as a normal ending."),
  ("`reset()` 运行中抛错；空闲时清空消息与队列，但保留 system 基线消息。", "`reset()` throws while running; when idle it clears messages and queues but keeps the system baseline message."),
 ],
 how=[
  ("`prompt(input)` 把字符串 / 图像规范化成 user 消息，调用 `runPromptMessages()`。", "`prompt(input)` normalizes string / images into user messages and calls `runPromptMessages()`."),
  ("`runWithLifecycle(executor)` 创建 `AbortController`，置 `isStreaming = true`，执行 `executor(signal)`。", "`runWithLifecycle(executor)` creates an `AbortController`, sets `isStreaming = true`, runs `executor(signal)`."),
  ("异常 → `handleRunFailure(error, aborted)`；`stopReason` 取 `aborted` 或 `error`。", "On exception → `handleRunFailure(error, aborted)`; `stopReason` becomes `aborted` or `error`."),
  ("`finally` → `finishRun()`：`isStreaming = false`、清 `streamingMessage` / `pendingToolCalls`、resolve 空闲等待者。", "`finally` → `finishRun()`: `isStreaming = false`, clear `streamingMessage` / `pendingToolCalls`, resolve idle waiters."),
 ],
 files=[
  (A + "agent.ts", r"async prompt\(input: string \| AgentMessage", "prompt()", "入口与并发检查", "entry and concurrency check"),
  (A + "agent.ts", r"async continue\(\): Promise<void>", "continue()", "从现有上下文恢复", "resume from existing context"),
  (A + "agent.ts", r"private async runWithLifecycle\(", "runWithLifecycle()", "AbortController 与 isStreaming", "AbortController and isStreaming"),
  (A + "agent.ts", r"private async handleRunFailure\(", "handleRunFailure()", "合成 error 消息", "synthesize the error message"),
  (A + "agent.ts", r"private finishRun\(\)", "finishRun()", "清理并唤醒等待者", "cleanup and wake waiters"),
  (A + "agent.ts", r"^\treset\(\): void", "reset()", "保留 system 基线", "keeps the system baseline"),
 ]),

dict(id="ac-turn", group="flows", layer="agent", diagram="ac_turn",
 title=("钩子调用顺序", "Hook call order"),
 takeaway=("一轮 = 一次 LLM 响应 + 它请求的工具。钩子的调用顺序是固定的：`prepareRequest → transformContext → convertToLlm → getApiKey → streamFn`，工具侧 `prepareArguments → validate → beforeToolCall → execute → afterToolCall`，轮末 `finishTurn → getSteeringMessages → prepareNextTurn`。",
           "A turn = one LLM response + the tools it asks for. Hooks fire in a fixed order: `prepareRequest → transformContext → convertToLlm → getApiKey → streamFn`; for tools `prepareArguments → validate → beforeToolCall → execute → afterToolCall`; at turn end `finishTurn → getSteeringMessages → prepareNextTurn`."),
 points=[
  ("`transformContext` 作用于 `AgentMessage[]`（可含自定义消息），`convertToLlm` 再把它们转成 pi-ai 的 `Message[]`——压缩、裁剪放前者，格式转换放后者。", "`transformContext` works on `AgentMessage[]` (custom messages included); `convertToLlm` then turns them into pi-ai `Message[]` — pruning belongs in the former, format conversion in the latter."),
  ("`getApiKey` 每次请求都调用，让短期 OAuth token 在长时间工具执行期间也能刷新。", "`getApiKey` is called on every request, so short-lived OAuth tokens can refresh during long tool runs."),
  ("`finishTurn` 返回 `{ action: \"end\" }` 可以在本轮后直接结束（跳过 steering 轮询）；`prepareNextTurn` 可以替换模型、工具、上下文。", "`finishTurn` returning `{ action: \"end\" }` stops after this turn (skipping the steering poll); `prepareNextTurn` can swap model, tools or context."),
  ("工具集合变化时，`declareToolChanges` 在发送前插入带 `toolsAdded/Removed` 的 system 消息，保证 transcript 自描述。", "When the tool set changes, `declareToolChanges` inserts a system message with `toolsAdded/Removed` before sending, keeping the transcript self-describing."),
 ],
 how=[
  ("开始：发 `agent_start`、`turn_start`，把提示消息作为 `message_start/end` 发出。", "Start: emit `agent_start`, `turn_start`, then the prompt messages as `message_start/end`."),
  ("请求：`streamAssistantResponse()` 依次调用请求侧钩子，把 pi-ai 事件映射为 `message_*`。", "Request: `streamAssistantResponse()` runs the request-side hooks and maps pi-ai events onto `message_*`."),
  ("工具：每个 toolCall 经 `prepareToolCall()` → `executePreparedToolCall()` → `finalizeExecutedToolCall()`。", "Tools: each toolCall goes through `prepareToolCall()` → `executePreparedToolCall()` → `finalizeExecutedToolCall()`."),
  ("轮末：`turn_end`，轮询 steering；有消息或有工具结果就进入下一轮，否则检查 follow-up，最后 `agent_end`。", "Turn end: `turn_end`, poll steering; continue if there are messages or tool results, else check follow-ups, then `agent_end`."),
 ],
 files=[
  (A + "agent-loop.ts", r"^async function runLoop\(", "runLoop()", "内外两层循环", "the inner and outer loop"),
  (A + "agent-loop.ts", r"^async function streamAssistantResponse\(", "streamAssistantResponse()", "请求侧钩子与事件映射", "request hooks and event mapping"),
  (A + "agent-loop.ts", r"^function declareToolChanges\(", "declareToolChanges()", "工具变化写入 transcript", "tool changes into the transcript"),
  (A + "agent-loop.ts", r"^async function prepareToolCall\(", "prepareToolCall()", "查找 · 参数 · 校验 · beforeToolCall", "find · args · validate · beforeToolCall"),
  (A + "agent-loop.ts", r"^async function finalizeExecutedToolCall\(", "finalizeExecutedToolCall()", "afterToolCall 字段合并", "afterToolCall field merge"),
  (A + "types.ts", r"^export type FinishTurn = ", "FinishTurn", "end | continue", "end | continue"),
 ]),

dict(id="ac-events", group="flows", layer="agent", diagram="ac_events",
 title=("AgentEvent 事件流", "The AgentEvent stream"),
 takeaway=("所有可观察的行为都是事件：运行、轮次、消息、工具执行四个层次，严格嵌套。pi-ai 的 12 种流事件在这一层被压缩成 `message_start / update / end` 三种。",
           "Everything observable is an event, in four strictly nested levels: run, turn, message, tool execution. pi-ai's 12 stream event types collapse into `message_start / update / end` here."),
 points=[
  ("`message_update` 同时携带 `assistantMessageEvent`（原始 pi-ai 事件），UI 可以按 delta 精细渲染。", "`message_update` also carries `assistantMessageEvent` (the raw pi-ai event), so a UI can render per delta."),
  ("并行工具模式下 `tool_execution_end` 按完成顺序发出，但 toolResult 消息按调用的原始顺序发出。", "In parallel tool mode `tool_execution_end` fires in completion order, but toolResult messages are emitted in source order."),
  ("`Agent` 的归约器在调用订阅者之前更新状态，所以监听器里读 `agent.state` 总是最新的。", "`Agent`'s reducer updates state before calling subscribers, so `agent.state` read inside a listener is always current."),
 ],
 how=[
  ("流开始（`start`）：把 partial 推入上下文并发 `message_start`。", "Stream start (`start`): push the partial into context and emit `message_start`."),
  ("每个 delta：用新的 partial 替换上下文末尾，发 `message_update`。", "Each delta: replace the context tail with the new partial and emit `message_update`."),
  ("`done` / `error`：取 `result()`，盖上 `thinkingLevel`，发 `message_end`。", "`done` / `error`: take `result()`, stamp `thinkingLevel`, emit `message_end`."),
 ],
 files=[
  (A + "types.ts", r"^export type AgentEvent =", "AgentEvent", "全部事件联合类型", "the full event union"),
  (A + "agent.ts", r"private async processEvents\(", "processEvents()", "状态归约器", "the state reducer"),
  (A + "agent.ts", r"^\tsubscribe\(listener", "subscribe()", "按顺序 await 的监听器", "listeners awaited in order"),
  (A + "agent-loop.ts", r"^function createAgentStream\(", "createAgentStream()", "agentLoop() 的 EventStream", "the EventStream behind agentLoop()"),
 ]),

dict(id="ac-queues", group="flows", layer="coding", diagram="ac_queues",
 title=("Steering 与 Follow-up", "Steering and follow-up"),
 takeaway=("运行中用户的新输入有两种语义：`steer()` 在当前轮工具结束后、下一次请求前插入；`followUp()` 等到 Agent 本来要停下时才开始新一轮。两个队列都可以一次取一条或全部。",
           "New input during a run has two meanings: `steer()` lands after the current turn's tools and before the next request; `followUp()` waits until the agent would otherwise stop. Each queue drains one-at-a-time or all at once."),
 points=[
  ("默认模式都是 `one-at-a-time`：每个轮询点只取一条，剩下的留到下一轮，避免一次塞入大量插话。", "Both default to `one-at-a-time`: each poll takes one message and leaves the rest for later turns, so a burst of nudges doesn't arrive at once."),
  ("steering 有三个轮询点：运行开始、`turn_end` 之后、`prepareNextTurn` 之后（仅当前一次为空）。", "Steering is polled at three points: run start, after `turn_end`, and after `prepareNextTurn` (only if the previous poll was empty)."),
  ("`continue()` 遇到末尾是 assistant 时会先消费 steering，否则消费 follow-up，两者都空则抛错。", "`continue()` with an assistant tail consumes steering first, then follow-ups, and throws if both are empty."),
 ],
 how=[
  ("`steer(m)` / `followUp(m)` 只是 `enqueue`，不会打断正在进行的流或工具。", "`steer(m)` / `followUp(m)` just `enqueue`; they never interrupt the in-flight stream or tool."),
  ("循环通过 `getSteeringMessages` / `getFollowUpMessages` 钩子拉取，`Agent` 用两个私有 `PendingMessageQueue` 实现它们。", "The loop pulls through the `getSteeringMessages` / `getFollowUpMessages` hooks, which `Agent` implements with two private `PendingMessageQueue`s."),
  ("取到的消息作为 user 消息写入上下文并发出 `message_start/end`，然后开始新一轮请求。", "Drained messages enter the context as user messages with `message_start/end`, then a new request starts."),
 ],
 files=[
  (A + "agent.ts", r"^class PendingMessageQueue", "PendingMessageQueue", "one-at-a-time | all", "one-at-a-time | all"),
  (A + "agent.ts", r"^\tsteer\(message", "steer()", "运行中插话", "nudge mid-run"),
  (A + "agent.ts", r"^\tfollowUp\(message", "followUp()", "停下之后再做", "after it stops"),
  (A + "types.ts", r"^export type QueueMode", "QueueMode", "队列模式", "queue mode"),
 ]),

dict(id="ac-parallel", group="flows", layer="agent", diagram="ac_parallel",
 title=("工具批的并发与顺序", "Tool batches: concurrency and order"),
 takeaway=("默认并行：准备阶段按顺序（含 `beforeToolCall`），执行并发，`afterToolCall` 后逐个发 `tool_execution_end`，所有结果到齐再按原顺序写 toolResult。任一工具声明 `executionMode: \"sequential\"` 时整批退化为顺序执行。",
           "Parallel by default: preparation runs in order (including `beforeToolCall`), execution is concurrent, `tool_execution_end` fires as each finalizes, and toolResults are written in source order once all settle. If any tool declares `executionMode: \"sequential\"` the whole batch runs sequentially."),
 points=[
  ("立即结果（未知工具、参数校验失败、被 `beforeToolCall` 阻止）不进入执行，直接得到 error 结果。", "Immediate outcomes (unknown tool, failed validation, blocked by `beforeToolCall`) skip execution and get an error result directly."),
  ("1.1.0 新增：每个结果带 `durationMs`（`performance.now()` 计时），出现在 `AgentToolCallOutcome` 与 `tool_execution_end` 上。", "New in 1.1.0: every result carries `durationMs` (timed with `performance.now()`), on `AgentToolCallOutcome` and `tool_execution_end`."),
  ("只有批内每个最终结果都 `terminate: true` 时，循环才会在本批后停止——一个工具不能单方面结束对话。", "The loop stops after a batch only if every finalized result has `terminate: true` — a single tool can't end the conversation on its own."),
  ("输出被截断（`stopReason: \"length\"`）时，不执行任何工具调用，而是为每个调用写入失败结果。", "When output was truncated (`stopReason: \"length\"`), no tool call runs; each gets a failure result instead."),
 ],
 how=[
  ("`executeToolCalls()` 根据 `config.toolExecution` 与各工具的 `executionMode` 选择顺序或并行。", "`executeToolCalls()` picks sequential or parallel from `config.toolExecution` and each tool's `executionMode`."),
  ("并行：逐个 `prepareToolCall()`，把可执行的放入 `Promise.all`。", "Parallel: `prepareToolCall()` one by one, putting runnable calls into `Promise.all`."),
  ("每个完成后 `finalizeExecutedToolCall()` 并立即发 `tool_execution_end`。", "Each completion is finalized and immediately emits `tool_execution_end`."),
  ("全部完成后按原顺序 `createToolResultMessage()` 并发出消息事件。", "After all settle, `createToolResultMessage()` in source order and emit the message events."),
 ],
 files=[
  (A + "agent-loop.ts", r"^async function executeToolCalls\(", "executeToolCalls()", "选择执行模式", "chooses the execution mode"),
  (A + "agent-loop.ts", r"^async function executeToolCallsParallel\(", "executeToolCallsParallel()", "并行批", "the parallel batch"),
  (A + "agent-loop.ts", r"^async function executeToolCallsSequential\(", "executeToolCallsSequential()", "顺序批", "the sequential batch"),
  (A + "agent-loop.ts", r"^function shouldTerminateToolBatch\(", "shouldTerminateToolBatch()", "全体 terminate 才停止", "stop only if all terminate"),
  (A + "agent-loop.ts", r"^async function failToolCallsFromTruncatedMessage\(", "failToolCallsFromTruncatedMessage()", "截断时的处理", "handling truncation"),
  (A + "agent-loop.ts", r"^export async function runToolCall\(", "runToolCall()", "无事件地复用同一管道", "reuse the pipeline without events"),
 ]),

dict(id="ac-proxy", group="flows", layer="agent", diagram="ac_proxy",
 title=("StreamFn 与代理", "StreamFn and the proxy"),
 takeaway=("Agent 从不直接依赖某个 provider：它只调用一个 `StreamFn`。可以传入 `models.streamSimple`，也可以用 `streamProxy` 把请求转发到你自己的服务端——客户端从 SSE 事件重建 partial，得到与直连相同的 `AssistantMessageEventStream`。",
           "The agent never depends on a provider directly: it only calls a `StreamFn`. Pass `models.streamSimple`, or use `streamProxy` to forward requests to your own server — the client rebuilds the partial from SSE events and gets the same `AssistantMessageEventStream` as a direct call."),
 points=[
  ("解析顺序：`AgentOptions.streamFn` → `setDefaultStreamFn()` 安装的全局默认 → 都没有则抛出 “No default stream function configured”。", "Resolution: `AgentOptions.streamFn` → the global default from `setDefaultStreamFn()` → otherwise throw “No default stream function configured”."),
  ("1.1.0 破坏性变更：`streamProxy` 与所有 `StreamFn` 必须返回 `AssistantMessageEventStream`（以便统一计时 `durationMs`）。", "Breaking in 1.1.0: `streamProxy` and every `StreamFn` must return `AssistantMessageEventStream` (so `durationMs` is timed uniformly)."),
  ("代理只序列化 11 个可序列化选项；服务端发的事件不含 partial，以节省带宽。", "The proxy serializes only 11 serializable options; server events omit the partial to save bandwidth."),
 ],
 how=[
  ("`streamProxy(model, ctx, { proxyUrl, authToken })` 向 `{proxyUrl}/api/stream` 发 POST。", "`streamProxy(model, ctx, { proxyUrl, authToken })` POSTs to `{proxyUrl}/api/stream`."),
  ("读取 SSE `data:` 行，`processProxyEvent()` 把每个事件应用到本地 partial 上并推入流。", "Read SSE `data:` lines; `processProxyEvent()` applies each event to the local partial and pushes it."),
  ("HTTP 错误、EOF 无终止事件、abort 都被编码成 error 事件，不会抛出。", "HTTP errors, EOF without a terminal event, and aborts are all encoded as error events — never thrown."),
 ],
 files=[
  (A + "proxy.ts", r"^export function streamProxy\(", "streamProxy()", "代理 StreamFn", "the proxy StreamFn"),
  (A + "proxy.ts", r"^function processProxyEvent\(", "processProxyEvent()", "客户端重建 partial", "rebuild the partial client-side"),
  (A + "proxy.ts", r"^function buildProxyRequestOptions\(", "buildProxyRequestOptions()", "可序列化选项", "serializable options"),
  (A + "stream-fn.ts", r"^export function getDefaultStreamFn", "getDefaultStreamFn()", "未配置时抛错", "throws when unset"),
  (A + "types.ts", r"^export type StreamFn = ", "StreamFn", "不抛异常的约定", "the never-throw contract"),
 ]),

dict(id="ac-types", group="types", layer="agent", diagram="ac_types",
 title=("数据类型", "Data types"),
 takeaway=("`AgentMessage` 是 pi-ai `Message` 与可声明合并的 `CustomAgentMessages` 的联合：宿主可以把自己的消息类型（如 artifact、通知）放进会话，只要 `convertToLlm` 知道如何把它们转成 LLM 消息。",
           "`AgentMessage` is the union of pi-ai `Message` and the declaration-mergeable `CustomAgentMessages`: hosts can put their own message kinds (artifacts, notifications) into the session, as long as `convertToLlm` knows how to turn them into LLM messages."),
 points=[
  ("`AgentState` 的 `tools` 与 `messages` 赋值时复制数组；`pendingToolCalls` 每次替换为新的 `Set`，方便 UI 做引用比较。", "`AgentState.tools` and `messages` copy on assignment; `pendingToolCalls` is replaced with a new `Set` each time so UIs can compare by reference."),
  ("`AgentTool` 继承 pi-ai `Tool`，增加 `label`、`execute()`、可选 `prepareArguments()` 与 `executionMode`。", "`AgentTool` extends pi-ai `Tool` with `label`, `execute()`, optional `prepareArguments()` and `executionMode`."),
  ("`AfterToolCallResult` 按字段合并：替换 `content` 但不给 `structuredContent` 时，旧的 `structuredContent` 会被丢弃，避免两者不一致。", "`AfterToolCallResult` merges field by field: replacing `content` without `structuredContent` drops the old `structuredContent`, so the two never disagree."),
 ],
 how=[
  ("扩展消息类型：`declare module \"@earendil-works/pi-agent-core\" { interface CustomAgentMessages { … } }`。", "Extend messages: `declare module \"@earendil-works/pi-agent-core\" { interface CustomAgentMessages { … } }`."),
  ("工具返回 `AgentToolResult<T>`：`content` 给模型，`details` 给 UI / 日志。", "Tools return `AgentToolResult<T>`: `content` for the model, `details` for UI / logs."),
 ],
 files=[
  (A + "types.ts", r"^export interface AgentState", "AgentState", "公开状态", "public state"),
  (A + "types.ts", r"^export interface CustomAgentMessages", "CustomAgentMessages", "声明合并扩展点", "declaration-merge extension point"),
  (A + "types.ts", r"^export interface AgentTool<", "AgentTool", "工具定义", "tool definition"),
  (A + "types.ts", r"^export interface AgentToolResult<", "AgentToolResult", "content + details", "content + details"),
  (A + "types.ts", r"^export interface AgentToolCallOutcome", "AgentToolCallOutcome", "含 durationMs", "with durationMs"),
  (A + "types.ts", r"^export interface BeforeToolCallResult", "BeforeToolCallResult", "block / terminate", "block / terminate"),
 ]),
]

EXT_POINTS = [
 ("streamFn", ("替换模型调用：直连、代理、录制回放、测试桩。", "Swap the model call: direct, proxy, record/replay, test stubs.")),
 ("convertToLlm · transformContext", ("自定义消息 → LLM 消息；压缩、裁剪、注入上下文。", "Custom messages → LLM messages; compaction, pruning, context injection.")),
 ("beforeToolCall · afterToolCall", ("权限审批、阻止、改写结果、终止。", "Approval, blocking, rewriting results, terminating.")),
 ("prepareRequest · prepareNextTurn · finishTurn", ("每轮改模型 / 工具 / 选项，决定是否继续。", "Change model / tools / options per turn and decide whether to continue.")),
 ("getApiKey", ("每次请求取凭据（短期 OAuth token）。", "Fetch credentials per request (short-lived OAuth tokens).")),
 ("CustomAgentMessages", ("声明合并，增加会话里的消息种类。", "Declaration merging adds message kinds to the session.")),
 ("AgentTool.prepareArguments · executionMode", ("修正模型给出的参数；强制顺序执行。", "Repair model-supplied args; force sequential execution.")),
 ("subscribe()", ("按顺序 await 的事件监听器，拿到运行的 AbortSignal。", "In-order awaited listeners that receive the run's AbortSignal.")),
]
XREF = [('pi-ai', ('流与模型来自 pi-ai：StreamFn 背后的完整链路', 'streams and models come from pi-ai: the full chain behind a StreamFn')),
        ('coding-agent', ('AgentSession 如何用 Agent 组装编码智能体', 'how AgentSession assembles a coding agent from Agent'))]
