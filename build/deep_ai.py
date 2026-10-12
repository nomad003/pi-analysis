# pi-ai (packages/ai) deep dive. Same section schema as content.py.
S = 'packages/ai/src/'
SLIDE_KEYS = ['ai_entry', 'ai_registry', 'ai_pipeline', 'ai_events', 'ai_convert', 'ai_anthropic', 'ai_budget', 'ai_oneshot']

INTRO = dict(
 takeaway=("`pi-ai` 把 42 个 provider 统一成一个 `Models` 集合与一种事件流：provider 负责目录与认证，10 种对话 API 实现负责协议，二者都按需懒加载；任何失败都编码成流中的 `error` 事件，而不是异常。",
           "`pi-ai` unifies 42 providers behind one `Models` collection and one event stream: providers own catalogs and auth, 10 chat API implementations own the wire protocol, both load lazily, and every failure is an `error` event in the stream rather than an exception."),
 role=("整个栈的最底层（仅依赖 `pi-telemetry`）。被 `pi-agent-core`、`pi-coding-agent`、`pi-durable` 使用。", "The bottom of the stack (depends only on `pi-telemetry`). Used by `pi-agent-core`, `pi-coding-agent` and `pi-durable`."),
)

SECTIONS = [
dict(id="ai-entry", group="arch", layer="ai", diagram="ai_entry",
 title=("入口与打包", "Entry points and bundling"),
 takeaway=("导入路径决定打包体积：根入口只给核心类型与工厂；`/providers/<id>` 只带一个 provider 的目录，SDK 首次请求时才加载；`/providers/all` 带全部目录但 SDK 依旧懒加载；`/api/<id>` 会立即加载 SDK。",
           "The import path decides bundle size: the root entry gives core types and factories; `/providers/<id>` brings one provider's catalog and loads its SDK on first request; `/providers/all` bundles every catalog but SDKs stay lazy; `/api/<id>` loads the SDK eagerly."),
 points=[
  ("每个 API 都有一个 `*.lazy.ts`：`lazyApi(() => import(\"./x.ts\"))`，provider 只引用这个包装。", "Every API has a `*.lazy.ts`: `lazyApi(() => import(\"./x.ts\"))`; providers only reference that wrapper."),
  ("`/compat` 保留旧的全局 API（`stream`、`complete`、`getModel`），已弃用。", "`/compat` keeps the old global API (`stream`, `complete`, `getModel`) and is deprecated."),
  ("`bin: pi-ai` 提供 CLI（OAuth 登录、模型列表）。", "`bin: pi-ai` ships a CLI (OAuth login, model listing)."),
 ],
 how=[
  ("应用导入 `builtinModels()` 或若干 `xxxProvider()`。", "The app imports `builtinModels()` or a few `xxxProvider()` factories."),
  ("`createProvider({ api: anthropicMessagesApi() })` 只保存懒包装。", "`createProvider({ api: anthropicMessagesApi() })` stores only the lazy wrapper."),
  ("第一次 `stream` 时 `import()` 实现模块（及其 SDK），之后由模块缓存去重。", "The first `stream` call `import()`s the implementation (and its SDK); the module cache dedupes later loads."),
 ],
 files=[
  ("packages/ai/package.json", r'"exports"', "exports", "9 个导出路径", "nine export paths"),
  (S + "api/lazy.ts", r"^export function lazyApi\(", "lazyApi()", "懒加载 API 模块", "lazily loads an API module"),
  (S + "api/anthropic-messages.lazy.ts", r"lazyApi", "anthropicMessagesApi", "懒包装示例", "an example lazy wrapper"),
  (S + "providers/all.ts", r"^export function builtinProviders\(", "builtinProviders()", "全部内置 provider", "all built-in providers"),
  (S + "providers/all.ts", r"^export function builtinModels\(", "builtinModels()", "一行得到完整集合", "the whole collection in one call"),
 ]),

dict(id="ai-registry", group="arch", layer="ai", diagram="ai_registry",
 title=("Models 与 Provider", "Models and providers"),
 takeaway=("`Models` 是 provider 的集合，也是所有调用的门面：查模型同步完成，凭据存在 `CredentialStore`，动态目录通过 `refresh()` 先发布缓存、再联网更新。`createProvider()` 把一个或多个 API 实现、图像与分类器能力组装成 `Provider`。",
           "`Models` is a collection of providers and the facade for every call: model lookup is synchronous, credentials live in a `CredentialStore`, and dynamic catalogs `refresh()` by publishing the cache first and then updating from the network. `createProvider()` assembles one or more API implementations plus image and classifier capabilities into a `Provider`."),
 points=[
  ("一个 provider 可以按 `model.api` 分派到多个 API（如 Fireworks 同时用 OpenAI 与 Anthropic 兼容 API）。", "One provider can dispatch to several APIs by `model.api` (e.g. Fireworks uses both OpenAI- and Anthropic-compatible APIs)."),
  ("缺少对应 API 时 `dispatch()` 返回一个以 error 结束的流，而不是抛出。", "With no matching API, `dispatch()` returns a stream that ends in error instead of throwing."),
  ("`getModels()` 只返回对话模型；图像与分类器模型通过 `getAllModels()` 查到。", "`getModels()` returns chat models only; image and classifier models are found via `getAllModels()`."),
 ],
 how=[
  ("`createModels({ providers })` 构造 `ModelsImpl`，以 id 为键注册 provider。", "`createModels({ providers })` builds a `ModelsImpl` keyed by provider id."),
  ("`refresh()` 对每个有 `fetchModels` 的 provider 调用 `refreshModels(ctx)`。", "`refresh()` calls `refreshModels(ctx)` on every provider with `fetchModels`."),
  ("动态模型按 (type, id) 覆盖基线目录，`getModels()` 始终同步返回合并结果。", "Dynamic models override baseline entries by (type, id); `getModels()` always returns the merge synchronously."),
 ],
 files=[
  (S + "models.ts", r"^export interface Models\b", "Models", "集合接口", "the collection interface"),
  (S + "models.ts", r"^class ModelsImpl", "ModelsImpl", "实现", "the implementation"),
  (S + "models.ts", r"^export interface Provider<", "Provider", "provider 接口", "the provider interface"),
  (S + "models.ts", r"^export function createProvider<", "createProvider()", "组装 provider", "assembles a provider"),
  (S + "models.ts", r"^export function createModels\(", "createModels()", "构造集合", "builds the collection"),
 ]),

dict(id="ai-pipeline", group="flows", layer="ai", diagram="ai_pipeline",
 title=("一次 streamSimple 调用", "One streamSimple call"),
 takeaway=("`models.streamSimple()` 同步返回一个外层流，真正的工作（找 provider、解析认证、加载 API 模块、发请求）在它背后异步进行；任何一步失败都会变成外层流的最后一个 `error` 事件。",
           "`models.streamSimple()` returns an outer stream synchronously while the real work (find the provider, resolve auth, load the API module, send the request) happens behind it; a failure at any step becomes the outer stream's final `error` event."),
 points=[
  ("认证解析顺序：调用方的 `apiKey` 覆盖 → 已存凭据（OAuth 会先刷新）→ 环境变量。", "Auth resolution order: caller `apiKey` override → stored credential (OAuth refreshed first) → environment."),
  ("`auth.baseUrl` 会覆盖模型的 `baseUrl`（如企业网关）；`transformHeaders` 最后执行。", "`auth.baseUrl` overrides the model's `baseUrl` (e.g. enterprise gateways); `transformHeaders` runs last."),
  ("`forwardStream()` 把内层事件逐个转发，最后用内层的 `result()` 结束外层流。", "`forwardStream()` forwards inner events one by one and ends the outer stream with the inner `result()`."),
 ],
 how=[
  ("`normalizeContext(context)` 同步生成 `TranscriptContext`。", "`normalizeContext(context)` builds a `TranscriptContext` synchronously."),
  ("`lazyStream(model, setup)` 立即返回外层 `AssistantMessageEventStream`。", "`lazyStream(model, setup)` immediately returns the outer `AssistantMessageEventStream`."),
  ("`setup()`：`requireChatProvider` → `applyAuth` → `provider.streamSimple` → `dispatch` → `lazyApi` 导入 → `api.streamSimple`。", "`setup()`: `requireChatProvider` → `applyAuth` → `provider.streamSimple` → `dispatch` → `lazyApi` import → `api.streamSimple`."),
  ("成功则转发；失败则 push 一个 `{ type: \"error\" }` 并 `end(message)`。", "On success, forward; on failure, push `{ type: \"error\" }` and `end(message)`."),
 ],
 files=[
  (S + "models.ts", r"^\tstreamSimple\(model: Model<Api>", "ModelsImpl.streamSimple", "门面方法", "the facade method"),
  (S + "models.ts", r"private async applyAuth<", "applyAuth()", "认证、headers、baseUrl", "auth, headers, baseUrl"),
  (S + "auth/resolve.ts", r"^export function resolveProviderAuth\(", "resolveProviderAuth()", "凭据优先级", "credential precedence"),
  (S + "api/lazy.ts", r"^export function lazyStream\(", "lazyStream()", "外层流 + 异步 setup", "outer stream + async setup"),
  (S + "api/lazy.ts", r"^async function forwardStream\(", "forwardStream()", "转发并结束", "forward and end"),
  (S + "utils/transcript.ts", r"^export function normalizeContext\(", "normalizeContext()", "规范化上下文", "normalize the context"),
 ]),

dict(id="ai-events", group="flows", layer="ai", diagram="ai_events",
 title=("事件语法与 EventStream", "Event grammar and EventStream"),
 takeaway=("每个响应都是 `start → (内容块的 start/delta*/end)* → done | error`，每个事件都带当前 partial。`EventStream` 是一个极小的推拉队列：生产者 `push`，消费者 `for await`，`result()` 在终止事件时 resolve。",
           "Every response is `start → (block start / delta* / end)* → done | error`, and every event carries the current partial. `EventStream` is a tiny push/pull queue: producers `push`, consumers `for await`, and `result()` resolves on the terminal event."),
 points=[
  ("7 种 `StopReason`：`pending` 只出现在 partial 上；`deferred` 表示异步任务，之后用 `streamDeferred(handle)` 取结果。", "Seven `StopReason`s: `pending` appears only on partials; `deferred` means an async job, fetched later with `streamDeferred(handle)`."),
  ("1.1.0：`AssistantMessageEventStream` 自动为最终消息写入 `durationMs`（单调时钟，从流创建开始计时）。", "1.1.0: `AssistantMessageEventStream` stamps `durationMs` on the final message (monotonic clock from stream creation)."),
  ("终止后 `push` 被忽略——迟到的事件不会污染已完成的消息。", "After termination, `push` is ignored — late events cannot corrupt a finished message."),
 ],
 how=[
  ("API 实现创建 `AssistantMessageEventStream`，边解析 SSE 边 `push`。", "API implementations create an `AssistantMessageEventStream` and `push` while parsing SSE."),
  ("有等待中的消费者就直接交付，否则进入 FIFO 队列。", "If a consumer is waiting, hand off directly; otherwise enqueue FIFO."),
  ("`done` / `error` 时 `isComplete` 为真，`result()` 得到最终 `AssistantMessage`。", "On `done` / `error`, `isComplete` is true and `result()` yields the final `AssistantMessage`."),
 ],
 files=[
  (S + "types.ts", r"^export type AssistantMessageEvent =", "AssistantMessageEvent", "12 种事件", "12 event types"),
  (S + "types.ts", r"^export type StopReason = ", "StopReason", "7 种停止原因", "seven stop reasons"),
  (S + "utils/event-stream.ts", r"^export class EventStream<", "EventStream", "推拉队列", "the push/pull queue"),
  (S + "utils/event-stream.ts", r"^export class AssistantMessageEventStream", "AssistantMessageEventStream", "durationMs 计时", "durationMs timing"),
 ]),

dict(id="ai-convert", group="flows", layer="ai", diagram="ai_convert",
 title=("跨模型消息转换", "Cross-model message transform"),
 takeaway=("每次请求前，`transformMessages()` 把任意 provider 产生的历史改写成目标模型能接受的形式：降级图像、处理 thinking 签名、规范化工具调用 id、跳过失败消息、补齐孤立的工具结果。这就是会话中途换模型仍然可行的原因。",
           "Before every request, `transformMessages()` rewrites history produced by any provider into something the target model accepts: downgrade images, handle thinking signatures, normalize tool-call ids, skip failed messages, fill in orphaned tool results. This is why switching models mid-session works."),
 points=[
  ("thinking 签名只在同一模型之间有效；跨模型时 thinking 转成普通文本，redacted thinking 直接丢弃。", "Thinking signatures are only valid on the same model; across models thinking becomes plain text and redacted thinking is dropped."),
  ("工具调用 id 的映射同时应用到对应的 toolResult，保证配对关系不被破坏。", "The tool-call id map is applied to matching toolResults too, so pairs stay intact."),
  ("没有结果的工具调用会得到合成的 `isError` 结果——多数 API 要求每个调用都有结果。", "Tool calls without a result get a synthesized `isError` result — most APIs require one per call."),
 ],
 how=[
  ("各 API 的 `convertMessages()` 先调用 `transformMessages(messages, model, normalizeToolCallId)`。", "Each API's `convertMessages()` first calls `transformMessages(messages, model, normalizeToolCallId)`."),
  ("然后才把统一消息映射成该 API 的请求格式。", "Only then are unified messages mapped to that API's request format."),
 ],
 files=[
  (S + "api/transform-messages.ts", r"^export function transformMessages<", "transformMessages()", "跨模型转换", "cross-model transform"),
  (S + "utils/transcript.ts", r"^export function getToolStateChanges\(", "getToolStateChanges()", "工具声明的增删", "tool declaration diffs"),
  (S + "utils/validation.ts", r"^export function validateToolArguments\(", "validateToolArguments()", "TypeBox 参数校验", "TypeBox argument validation"),
 ]),

dict(id="ai-anthropic", group="flows", layer="ai", diagram="ai_anthropic",
 title=("一个 API 实现：anthropic-messages", "One API implementation: anthropic-messages"),
 takeaway=("一个 API 实现的全部工作就是：把 SSE 事件翻译成统一事件，维护内容块的 partial，最后映射停止原因并计算成本。`streamSimple` 额外负责把统一的 `reasoning` 等级换算成该 API 的 thinking 参数。",
           "An API implementation's whole job: translate SSE events into unified events, maintain content-block partials, then map the stop reason and compute cost. `streamSimple` additionally turns the unified `reasoning` level into this API's thinking parameters."),
 points=[
  ("工具参数用 `parseStreamingJson` 增量解析，UI 可以在参数流式到达时就显示。", "Tool arguments are parsed incrementally with `parseStreamingJson`, so a UI can show them while they stream."),
  ("`refusal` 与 `sensitive` 被映射为 `error`，`pause_turn` 视为正常 `stop`。", "`refusal` and `sensitive` map to `error`; `pause_turn` is treated as a normal `stop`."),
  ("请求经过 `retryProviderRequest`，并提供 `onPayload` / `onResponse` 钩子用于调试与改写。", "Requests go through `retryProviderRequest` and expose `onPayload` / `onResponse` hooks for debugging and rewriting."),
 ],
 how=[
  ("`message_start` → `start`；每个 `content_block_start` → `*_start`；delta → `*_delta`；stop → `*_end`。", "`message_start` → `start`; each `content_block_start` → `*_start`; deltas → `*_delta`; stop → `*_end`."),
  ("`message_delta` 带 `stop_reason` 与 usage；结束时 `calculateCost()` 并 push `done`。", "`message_delta` carries `stop_reason` and usage; at the end `calculateCost()` and push `done`."),
 ],
 files=[
  (S + "api/anthropic-messages.ts", r"^export const stream: StreamFunction", "stream", "SSE → 事件", "SSE → events"),
  (S + "api/anthropic-messages.ts", r"^export const streamSimple: StreamFunction", "streamSimple", "thinking 配置", "thinking configuration"),
  (S + "api/anthropic-messages.ts", r"^function mapStopReason\(", "mapStopReason()", "停止原因映射", "stop-reason mapping"),
  (S + "utils/provider-retry.ts", r"^export async function retryProviderRequest", "retryProviderRequest()", "重试", "retries"),
 ]),

dict(id="ai-budget", group="types", layer="ai", diagram="ai_budget",
 title=("思考等级、预算与成本", "Thinking levels, budgets and cost"),
 takeaway=("统一的思考等级 `off … max` 按模型裁剪；token 型 API 用默认预算表换算，并保证 `maxTokens` 留出至少 1024 个回答 token、不超过上下文窗口。每次响应的 `Usage` 都按模型目录价格（含分层与 1h 缓存写入）计算美元成本。",
           "Unified thinking levels `off … max` are clamped per model; token-budget APIs convert them with a default budget table while keeping `maxTokens` at least 1024 answer tokens and within the context window. Every response's `Usage` is priced in USD from the catalog (tiers and 1h cache writes included)."),
 points=[
  ("`xhigh` 与 `max` 只有在模型的 `thinkingLevelMap` 明确声明时才可用；`null` 表示该等级被禁用。", "`xhigh` and `max` exist only if the model's `thinkingLevelMap` declares them; `null` disables a level."),
  ("分层定价：输入 token（含缓存）超过某层阈值时整次请求按该层计价。", "Tiered pricing: when input tokens (cache included) exceed a tier threshold, the whole request uses that tier."),
  ("`isContextOverflow()` 识别各家的“上下文过长”错误，coding-agent 据此压缩后重试。", "`isContextOverflow()` recognises each provider's context-overflow error; coding-agent compacts and retries on it."),
 ],
 how=[
  ("`clampThinkingLevel(model, level)` 找到最近的受支持等级。", "`clampThinkingLevel(model, level)` finds the nearest supported level."),
  ("`adjustMaxTokensForThinking` + `clampMaxTokensToContext` 计算最终 `maxTokens` 与思考预算。", "`adjustMaxTokensForThinking` + `clampMaxTokensToContext` compute the final `maxTokens` and thinking budget."),
  ("响应结束时 `calculateCost(model, usage)` 填充 `usage.cost`。", "At the end of a response `calculateCost(model, usage)` fills `usage.cost`."),
 ],
 files=[
  (S + "models.ts", r"^export function calculateCost\(", "calculateCost()", "成本计算", "cost calculation"),
  (S + "models.ts", r"^export function getSupportedThinkingLevels<", "getSupportedThinkingLevels()", "可用思考等级", "available thinking levels"),
  (S + "api/simple-options.ts", r"^export const DEFAULT_THINKING_BUDGETS", "DEFAULT_THINKING_BUDGETS", "默认预算表", "default budget table"),
  (S + "api/simple-options.ts", r"^export function clampMaxTokensToContext\(", "clampMaxTokensToContext()", "不超过上下文窗口", "stay within the context window"),
  (S + "types.ts", r"^export interface Usage\b", "Usage", "token 与成本", "tokens and cost"),
  (S + "utils/overflow.ts", r"^export function isContextOverflow\(", "isContextOverflow()", "上下文溢出识别", "context-overflow detection"),
 ]),

dict(id="ai-oneshot", group="flows", layer="ai", diagram="ai_oneshot",
 title=("图像与分类器", "Images and classifiers"),
 takeaway=("除对话流之外，`Models` 还有两种一次性 API：`generateImages()` 与 `classify()`。它们返回 Promise 但从不 reject——失败同样编码为结果里的 `stopReason: \"error\"`。",
           "Beyond chat streams, `Models` has two one-shot APIs: `generateImages()` and `classify()`. They return Promises but never reject — failures are again encoded as `stopReason: \"error\"` in the result."),
 points=[
  ("分类器 API 有 4 种；1.1.0 新增 `openai-decisions`，以及 `ClassifierContext.images`。", "There are four classifier APIs; 1.1.0 adds `openai-decisions` and `ClassifierContext.images`."),
  ("问题有三种：`choice`（带概率分布）、`score`、`bool`，每个答案都带置信度或概率。", "Questions come in three kinds: `choice` (with a probability distribution), `score` and `bool`; each answer carries confidence or probability."),
 ],
 how=[
  ("`createProvider({ images, classifiers })` 按 API 名注册实现。", "`createProvider({ images, classifiers })` registers implementations by API name."),
  ("`models.classify(model, context)` 走与流相同的认证路径，然后调用 provider。", "`models.classify(model, context)` follows the same auth path as streams, then calls the provider."),
 ],
 files=[
  (S + "types.ts", r"^export interface ClassifierContext", "ClassifierContext", "state · images · questions", "state · images · questions"),
  (S + "types.ts", r"^export interface ClassifierResult", "ClassifierResult", "answers · usage", "answers · usage"),
  (S + "types.ts", r"^export interface AssistantImages", "AssistantImages", "图像结果", "image results"),
  (S + "api/openai-decisions.ts", r"^export const classify", "openai-decisions", "1.1.0 新增", "new in 1.1.0"),
 ]),
]

EXT_POINTS = [
 ("createProvider()", ("注册自定义 provider：任意 baseUrl、自己的目录与认证。", "Register a custom provider: any baseUrl, your own catalog and auth.")),
 ("ProviderStreams", ("实现 `stream` / `streamSimple` 即可接入一种新的线协议。", "Implement `stream` / `streamSimple` to add a new wire protocol.")),
 ("Model.compat", ("为 OpenAI / Anthropic 兼容服务声明差异（字段名、能力开关）。", "Declare quirks of OpenAI / Anthropic-compatible servers (field names, capability flags).")),
 ("ApiKeyAuth · OAuth auth", ("自定义登录与凭据解析；`CredentialStore` 可替换为持久化存储。", "Custom login and credential resolution; swap `CredentialStore` for persistent storage.")),
 ("ModelsStore", ("持久化动态目录，启动时先发布缓存。", "Persist dynamic catalogs and publish the cache at start-up.")),
 ("onPayload · onResponse · transformHeaders", ("在发送前检查或改写请求与响应。", "Inspect or rewrite requests and responses on the way.")),
]
XREF = [('agent-core', ('StreamFn 的使用方：Agent 循环如何消费这些事件', 'the StreamFn consumer: how the agent loop consumes these events')),
        ('telemetry', ('pi-ai 唯一的运行时依赖', "pi-ai's only runtime dependency")),
        ('coding-agent', ('ModelRuntime、模型选择与 /login', 'ModelRuntime, model selection and /login'))]
