# pi-telemetry deep dive. Same section schema as deep_agent.py; files: (path, regex, symbol, zh, en)
from pkgsrc import Pkg
T_ = Pkg('packages/telemetry/src/')
U = 'packages/telemetry/src/'
AI = 'packages/ai/src/'
SLIDE_KEYS = ['tel_arch', 'tel_model', 'tel_lifecycle', 'tel_contract', 'tel_memory', 'tel_schema', 'tel_typed', 'tel_pi']
_TS = T_.total()

INTRO = dict(
 takeaway=("`pi-telemetry` 是 pi 的遥测**契约**，而不是遥测系统：一个回调式的 `TelemetryContext.startSpan(options, callback)`，一个同时充当子上下文的 `TelemetrySpan`（属性、事件、状态），两个参考实现（共享的 `NOOP_TELEMETRY_CONTEXT` 与确定性的 `InMemoryTelemetryContext`），一套与测试框架无关的适配器一致性用例，以及把可序列化 schema 变成精确 TypeScript 类型的工具。它不导出任何数据、没有运行时依赖、不用环境上下文；真正对接 OpenTelemetry 或 Sentry 的是适配器。",
           "`pi-telemetry` is pi's telemetry **contract**, not a telemetry system: a callback-style `TelemetryContext.startSpan(options, callback)`, a `TelemetrySpan` that doubles as the child context (attributes, events, status), two reference implementations (the shared `NOOP_TELEMETRY_CONTEXT` and the deterministic `InMemoryTelemetryContext`), a runner-independent adapter conformance suite, and utilities that turn serializable schemas into exact TypeScript types. It exports no data, has no runtime dependencies and uses no ambient context; adapters do the actual OpenTelemetry or Sentry work."),
 role=(f"{_TS:,} 行 TypeScript，两个导入路径（`.` 与 `./testing`），零运行时依赖。在 v1.1.0 里唯一的使用者是 `pi-ai`：它在 `ProviderRequestOptions` 上接受 `telemetryContext` 并原样传给 provider。README 提到的 agent-core schema（`AGENT_TELEMETRY_SCHEMAS`）在这个标签上还不存在。整个包在 0.84.0 一次性加入，1.1.0 没有变化。",
       f"{_TS:,} lines of TypeScript, two import paths (`.` and `./testing`), zero runtime dependencies. At v1.1.0 its only user is `pi-ai`, which accepts `telemetryContext` on `ProviderRequestOptions` and hands it to providers unchanged. The agent-core schemas the README mentions (`AGENT_TELEMETRY_SCHEMAS`) do not exist at this tag yet. The whole package arrived in 0.84.0; 1.1.0 changes nothing."),
)

SECTIONS = [
dict(id="tel-arch", group="arch", layer="infra", diagram="tel_arch",
 title=("一个契约、两个参考实现、一套一致性测试", "One contract, two reference contexts, one conformance suite"),
 takeaway=("`index.ts` 声明契约类型、schema 定义与全部类型推导，以及 `createTypedSpanStarter()`；`noop.ts` 是一个冻结的惰性 span；`memory.ts` 是记录到内存的参考适配器，在父 span 已结束或记录失败时退回 no-op。`./testing` 子路径放适配器一致性套件，它是包里唯一使用 Node API（`node:assert/strict`）的部分。",
           "`index.ts` declares the contract types, the schema definitions with all their type inference, and `createTypedSpanStarter()`; `noop.ts` is one frozen inert span; `memory.ts` is the reference adapter that records in memory and falls back to the no-op when the parent has settled or recording fails. The `./testing` subpath holds the adapter conformance suite, the only part of the package that uses a Node API (`node:assert/strict`)."),
 points=[
  ("根入口只有 4 个值导出：`defineTelemetrySchema`、`createTypedSpanStarter`、`NOOP_TELEMETRY_CONTEXT` 与 `InMemoryTelemetryContext`，其余全是类型。", "The root has only 4 value exports — `defineTelemetrySchema`, `createTypedSpanStarter`, `NOOP_TELEMETRY_CONTEXT` and `InMemoryTelemetryContext`; everything else is a type."),
  ("没有运行时依赖：package.json 只有 `@types/node` 与 `vitest` 两个 devDependencies。", "No runtime dependencies: package.json has just two devDependencies, `@types/node` and `vitest`."),
  ("别和 coding-agent 的 `core/telemetry.ts` 混淆：那是“安装遥测”开关（`PI_TELEMETRY` 或设置项），与这个包无关。", "Don't confuse it with coding-agent's `core/telemetry.ts`: that is the install-telemetry switch (`PI_TELEMETRY` or a setting) and has nothing to do with this package."),
 ],
 how=[
  ("可选遥测：函数参数默认 `telemetryContext = NOOP_TELEMETRY_CONTEXT`，调用方想要时再传真实的上下文。", "Optional telemetry: default a parameter to `telemetryContext = NOOP_TELEMETRY_CONTEXT` and let callers pass a real context when they want one."),
  ("测试：`new InMemoryTelemetryContext()`，跑被测代码，再断言 `getSpans()`。", "Tests: `new InMemoryTelemetryContext()`, run the code under test, then assert on `getSpans()`."),
  ("写适配器：实现 `TelemetryContext`，再用 `./testing` 的 `createTelemetryAdapterConformance()` 验证。", "Writing an adapter: implement `TelemetryContext`, then verify it with `createTelemetryAdapterConformance()` from `./testing`."),
 ],
 files=[
  (U + "index.ts", r"^export interface TelemetryContext", "TelemetryContext", "契约", "the contract"),
  (U + "noop.ts", r"^export const NOOP_TELEMETRY_CONTEXT", "NOOP_TELEMETRY_CONTEXT", "共享的惰性上下文", "the shared inert context"),
  (U + "memory.ts", r"^export class InMemoryTelemetryContext", "InMemoryTelemetryContext", "参考适配器", "the reference adapter"),
  (U + "testing/index.ts", r"createTelemetryAdapterConformance", "./testing", "一致性套件入口", "conformance entry"),
  ("packages/telemetry/package.json", r'"exports"', "exports", "两个导入路径", "two import paths"),
 ]),

dict(id="tel-model", group="types", layer="infra", diagram="tel_model",
 title=("span、属性、事件、状态与上下文", "Spans, attributes, events, status and context"),
 takeaway=("一个 span 是一次操作的计时记录，带属性（事实）、事件（时刻）和状态（`ok` / `error`）。`TelemetryContext` 只有一个方法 `startSpan()`；回调拿到的 `TelemetrySpan` 继承自 `TelemetryContext`，所以它本身就是子 span 的父上下文。属性值只能是字符串、数字、布尔或它们的只读数组。",
           "A span is a timed record of one operation, carrying attributes (facts), events (moments) and a status (`ok` / `error`). `TelemetryContext` has a single method, `startSpan()`; the `TelemetrySpan` the callback receives extends `TelemetryContext`, so it is itself the parent context for child spans. Attribute values are strings, numbers, booleans or readonly arrays of them."),
 points=[
  ("没有 `end()`：`startSpan()` 拥有结束时机，回调的返回值或 promise 落定时 span 才结束。", "There is no `end()`: `startSpan()` owns settlement, and the span ends when the callback's value or promise settles."),
  ("父子关系完全靠显式传参：把回调里的 span 传给下层代码。包里没有 `AsyncLocalStorage`。", "Parentage is purely explicit: pass the callback's span down to lower-level code. There is no `AsyncLocalStorage` in the package."),
  ("span 是诊断数据而不是业务状态：记录与否不能改变操作是否执行、成功或失败。", "A span is diagnostic data, not business state: recording must not change whether an operation runs, succeeds or fails."),
 ],
 how=[
  ("`ctx.startSpan({ name, attributes }, async (span) => { … span.setAttributes({ found }) … })`。", "`ctx.startSpan({ name, attributes }, async (span) => { … span.setAttributes({ found }) … })`."),
  ("子 span：在回调里 `span.startSpan({ name: 'child' }, …)`。", "A child: `span.startSpan({ name: 'child' }, …)` inside the callback."),
  ("预期失败（返回 `{ ok: false }`）要显式 `span.setStatus({ status: 'error', error: { name, message } })`。", "An expected failure (returning `{ ok: false }`) needs an explicit `span.setStatus({ status: 'error', error: { name, message } })`."),
 ],
 files=[
  (U + "index.ts", r"^export type AttributeValue", "AttributeValue", "属性值", "attribute values"),
  (U + "index.ts", r"^export interface SpanOptions", "SpanOptions", "名字与开始属性", "name and start attributes"),
  (U + "index.ts", r"^export type SpanStatus", "SpanStatus", "ok / error", "ok / error"),
  (U + "index.ts", r"^export interface TelemetrySpan extends TelemetryContext", "TelemetrySpan", "span 即上下文", "a span is a context"),
 ]),

dict(id="tel-lifecycle", group="flows", layer="infra", diagram="tel_lifecycle",
 title=("一次 startSpan() 的生命周期", "The life of one startSpan()"),
 takeaway=("`startSpan()` 同步调用回调恰好一次。回调正常返回或 promise 兑现 → 状态保持 `ok`；同步抛错或 promise 拒绝 → 自动设为 `error { name, message }`——除非回调已经显式 `setStatus()`。`settleSpan()` 只执行一次，记下结束序号；返回的 promise 以同一个值兑现或拒绝。结束之后的记录调用全部静默无效。",
           "`startSpan()` calls the callback synchronously, exactly once. A normal return or a resolved promise keeps the status `ok`; a synchronous throw or a rejection sets `error { name, message }` automatically — unless the callback already called `setStatus()`. `settleSpan()` runs once and records the end sequence; the returned promise resolves or rejects with the same value. Recording calls after settlement are silent no-ops."),
 points=[
  ("显式状态优先于自动状态：先 `setStatus({ status: 'ok' })` 再抛错，span 仍是 `ok`。", "Explicit status beats the automatic one: `setStatus({ status: 'ok' })` and then throw, and the span stays `ok`."),
  ("父 span 已结束时再开子 span，或创建记录本身失败，都会走 `NOOP_TELEMETRY_CONTEXT`：业务回调照常执行，只是不记录。", "Starting a child under a settled parent, or a failure while creating the record, goes through `NOOP_TELEMETRY_CONTEXT`: the business callback still runs, it just isn't recorded."),
  ("错误详情的读取是被动的：读 `error.name` 抛错时，状态退回为不带详情的 `error`。", "Reading error details is passive: if reading `error.name` throws, the status falls back to `error` without details."),
 ],
 how=[
  ("`startInMemorySpan()`：检查父 span → `createSpan()` → `callback(span)` → `Promise.resolve(result).then(settle ok, settle error)`。", "`startInMemorySpan()`: check the parent → `createSpan()` → `callback(span)` → `Promise.resolve(result).then(settle ok, settle error)`."),
  ("同步抛错：先 `settleSpan(…, true, error)`，再 `return Promise.reject(error)`。", "A synchronous throw: `settleSpan(…, true, error)` first, then `return Promise.reject(error)`."),
  ("每个记录方法开头都是 `if (recordedSpan.settled) return;`，主体包在 `try { … } catch {}` 里。", "Every recording method starts with `if (recordedSpan.settled) return;` and wraps its body in `try { … } catch {}`."),
 ],
 files=[
  (U + "memory.ts", r"^function startInMemorySpan", "startInMemorySpan()", "一次 span 的全过程", "one span, start to end"),
  (U + "memory.ts", r"^function settleSpan", "settleSpan()", "只结束一次", "settles once"),
  (U + "memory.ts", r"^function automaticErrorStatus", "automaticErrorStatus()", "自动 error 状态", "automatic error status"),
  (U + "noop.ts", r"^function startNoopSpan", "startNoopSpan()", "no-op 的同一套语义", "the same semantics, no recording"),
 ]),

dict(id="tel-contract", group="flows", layer="infra", diagram="tel_contract",
 title=("适配器契约与一致性套件", "The adapter contract and its conformance suite"),
 takeaway=("README 为适配器列出 9 条规则：同步且只调用一次回调、保留返回值与拒绝值、promise 落定前保持 span 打开、自动与显式状态、`setStatus` 最后一次生效、`setAttributes` 合并、记录方法被动不抛错、结束后调用无效、失败的记录调用整体忽略。`./testing` 的 `createTelemetryAdapterConformance(factory)` 把这些写成 5 组共 9 个与测试框架无关的用例。",
           "The README lists 9 rules for adapters: call the callback synchronously and once, preserve return and rejection values, keep the span open until the promise settles, automatic and explicit status, last-write-wins `setStatus`, merging `setAttributes`, passive non-throwing recording, inert calls after settlement, and ignoring a failed recording call whole. `createTelemetryAdapterConformance(factory)` in `./testing` turns them into 9 runner-independent cases in 5 groups."),
 points=[
  ("用例是普通对象 `{ group, name, run() }`，可以注册进 vitest、node:test 或任何框架；pi 自己的测试把它们挂到 `InMemoryTelemetryContext` 上。", "Cases are plain `{ group, name, run() }` objects you can register with vitest, node:test or any runner; pi's own tests run them against `InMemoryTelemetryContext`."),
  ("被动性用 `Proxy` 检验：读取、枚举、取原型时都抛错的载荷不能让适配器抛错，也不能留下半条记录。", "Passivity is tested with a `Proxy` that throws on read, enumeration and prototype access: the adapter must not throw and must not keep half a record."),
  ("fixture 的 `getSpans()` 返回规范化的 `RecordedTelemetrySpan[]`，可以先 flush 异步导出器。", "A fixture's `getSpans()` returns normalized `RecordedTelemetrySpan[]` and may flush an async exporter first."),
 ],
 how=[
  ("`createTelemetryAdapterConformance(async () => ({ context, getSpans, [Symbol.asyncDispose] }))`。", "`createTelemetryAdapterConformance(async () => ({ context, getSpans, [Symbol.asyncDispose] }))`."),
  ("`for (const group of new Set(cases.map(c => c.group))) describe(group, () => …it(c.name, () => c.run()))`。", "`for (const group of new Set(cases.map(c => c.group))) describe(group, () => …it(c.name, () => c.run()))`."),
  ("每个用例 `await using fixture = await factory()`：一个用例一个全新的适配器，结束时自动释放。", "Each case does `await using fixture = await factory()`: a fresh adapter per case, disposed automatically."),
 ],
 files=[
  ("packages/telemetry/README.md", r"^## Adapter Contract", "README · Adapter Contract", "9 条规则", "the 9 rules"),
  (U + "testing/conformance.ts", r"^export function createTelemetryAdapterConformance", "createTelemetryAdapterConformance()", "9 个用例", "the 9 cases"),
  (U + "testing/conformance.ts", r"^function unreadable", "unreadable()", "读取即抛错的载荷", "payloads that throw on read"),
  (U + "testing/types.ts", r"^export interface TelemetryAdapterFixture", "TelemetryAdapterFixture", "fixture 契约", "the fixture contract"),
  ("packages/telemetry/test/conformance.test.ts", r"^const conformance = createTelemetryAdapterConformance", "conformance.test.ts", "跑在内存适配器上", "run against the in-memory adapter"),
 ]),

dict(id="tel-memory", group="flows", layer="infra", diagram="tel_memory",
 title=("内存参考适配器", "The in-memory reference adapter"),
 takeaway=("`InMemoryTelemetryContext` 每个实例有一份状态：span 数组、`nextSpanId` 与 `nextEndSequence`。id 按开始顺序分配，`endSequence` 按结束顺序分配，所以嵌套与并发的结果是确定的，不需要时间戳。`getSpans()` 返回分离的快照：属性、数组、事件和状态全部复制，内部的 `explicitStatus` 不暴露。",
           "Each `InMemoryTelemetryContext` instance has one state: the span array, `nextSpanId` and `nextEndSequence`. Ids follow start order and `endSequence` follows end order, so nesting and concurrency produce deterministic results without timestamps. `getSpans()` returns detached snapshots: attributes, arrays, events and status are all copied, and the internal `explicitStatus` stays hidden."),
 points=[
  ("一致性用例里，`second-child` 同步返回、先结束（endSequence 1），`first-child` 等闸门打开才结束（2），`parent` 最后（3）。", "In the conformance case, `second-child` returns synchronously and ends first (endSequence 1), `first-child` ends once its gate opens (2), and `parent` last (3)."),
  ("回调运行中调用 `getSpans()`：看到 `settled: false` 且没有 `endSequence`。", "Calling `getSpans()` while a callback runs shows `settled: false` and no `endSequence`."),
  ("存储无上限且只在本进程内：用于测试与本地诊断，每个测试 new 一个实例。", "Storage is unbounded and process-local: it is meant for tests and local diagnostics, one fresh instance per test."),
 ],
 how=[
  ("`createSpan()`：`id: state.nextSpanId++`、`parentId: parent?.id ?? null`、复制开始属性（丢弃 `undefined`）。", "`createSpan()`: `id: state.nextSpanId++`, `parentId: parent?.id ?? null`, copied start attributes (dropping `undefined`)."),
  ("`mergeAttributes()` 先复制再合并；中途抛错时整个调用被忽略，原属性不变。", "`mergeAttributes()` copies, then merges; if it throws midway the whole call is ignored and the attributes stay unchanged."),
  ("`getSpans()` 只在结束过的 span 上加 `endSequence` 字段。", "`getSpans()` adds the `endSequence` field only to settled spans."),
 ],
 files=[
  (U + "memory.ts", r"^export interface RecordedTelemetrySpan", "RecordedTelemetrySpan", "快照形状", "the snapshot shape"),
  (U + "memory.ts", r"^function createSpan", "createSpan()", "分配 id", "assigns ids"),
  (U + "memory.ts", r"^function mergeAttributes", "mergeAttributes()", "合并属性", "merges attributes"),
  (U + "memory.ts", r"^\tgetSpans\(\)", "getSpans()", "分离的快照", "detached snapshots"),
  ("packages/telemetry/test/conformance.test.ts", r"returns detached snapshots", "detached snapshots test", "快照不可变", "snapshots don't leak"),
 ]),

dict(id="tel-schema", group="types", layer="agent", diagram="tel_schema",
 title=("可序列化的 schema", "Serializable schemas"),
 takeaway=("`TelemetrySchemaDefinition` 是普通 JSON：`version` 加 `spans` 表。每个 span 定义描述、父子规则（`any` / `root_or_external` / 列出的 span）、开始属性（每个都声明 `required`）、结束属性（总是可选）、事件（属性声明 `required`）以及状态规则 `{ default: 'ok', errorWhen }`。属性有 6 种类型，可带封闭集合、示例、`sensitive` 与 `cardinality`。",
           "A `TelemetrySchemaDefinition` is plain JSON: a `version` plus a `spans` table. Each span declares a description, a parent rule (`any` / `root_or_external` / listed spans), start attributes (each declares `required`), end attributes (always optional), events (whose attributes declare `required`) and a status rule `{ default: 'ok', errorWhen }`. Attributes have 6 types and may carry closed sets, examples, `sensitive` and `cardinality`."),
 points=[
  ("`defineTelemetrySchema()` 是类型化的恒等函数：原样返回参数，不做运行时校验，也不强制父子规则。", "`defineTelemetrySchema()` is a typed identity function: it returns its argument, with no runtime validation and no parent-rule enforcement."),
  ("start 与 end 只说明值“何时可知”，最后都落在同一个后端 span 的同一个属性袋里。", "start vs end only says when a value is known; both end up in the same attribute bag of the same backend span."),
  ("父子规则、`sensitive`、`cardinality` 都是描述性元数据：适配器不需要理解 schema 对象。", "Parent rules, `sensitive` and `cardinality` are descriptive metadata: adapters never need to understand schema objects."),
 ],
 how=[
  ("用 `as const` 写 schema（或内联），让字面量类型保留下来。", "Write the schema `as const` (or inline) so the literal types survive."),
  ("`values: ['account', 'project']` 让这个属性的类型变成 `'account' | 'project'`；数组用 `elementValues`。", "`values: ['account', 'project']` types the attribute as `'account' | 'project'`; arrays use `elementValues`."),
  ("因为是 JSON，schema 可以导出给文档或外部校验工具。", "Being JSON, a schema can be exported to documentation or external validators."),
 ],
 files=[
  (U + "index.ts", r"^export interface TelemetrySchemaDefinition", "TelemetrySchemaDefinition", "顶层形状", "top-level shape"),
  (U + "index.ts", r"^export interface TelemetrySpanDefinition", "TelemetrySpanDefinition", "一个 span 的定义", "one span's definition"),
  (U + "index.ts", r"^export type TelemetryAttributeDefinition", "TelemetryAttributeDefinition", "6 种属性类型", "6 attribute types"),
  (U + "index.ts", r"^export type TelemetryParentDefinition", "TelemetryParentDefinition", "父子规则", "parent rules"),
  (U + "index.ts", r"^export function defineTelemetrySchema", "defineTelemetrySchema()", "恒等函数", "identity function"),
 ]),

dict(id="tel-typed", group="flows", layer="agent", diagram="tel_typed",
 title=("类型化的 span 启动器", "Typed span starters"),
 takeaway=("`createTypedSpanStarter(ctx, [A, B])` 把一个父上下文绑定到若干 schema 的合并词汇上。编译期：每个 span 名一个重载，开始属性必须精确（缺 required、多余的键、封闭集合外的值都报错），跨 schema 的重名 span 直接让参数类型失效。运行时它只是 `ctx.startSpan({ name, attributes }, …)`，再把绑定到子 span 的新启动器交给回调。",
           "`createTypedSpanStarter(ctx, [A, B])` binds one parent context to the combined vocabulary of several schemas. At compile time there is one overload per span name and start attributes must be exact (missing required keys, extra keys and values outside a closed set all fail), while a span name present in two schemas breaks the argument type outright. At run time it is just `ctx.startSpan({ name, attributes }, …)`, handing the callback a new starter bound to the child span."),
 points=[
  ("回调签名是 `(span, startChildSpan)`：`span` 只接受这个 span 声明的事件和结束属性，`startChildSpan` 已绑定到 `span`。", "The callback signature is `(span, startChildSpan)`: `span` accepts only this span's declared events and end attributes, and `startChildSpan` is already bound to `span`."),
  ("类型为联合的名字（`'operation' | 'request'`）必须先收窄，名字与属性的对应关系才不会丢。", "A union-typed name (`'operation' | 'request'`) must be narrowed first, so the name ↔ attributes correlation is never lost."),
  ("schema 值只参与类型推导：运行时不检查、不合并、不保留；传一个读取即抛错的数组也不会出错（有测试）。", "Schema values only drive inference: never inspected, merged or kept at run time; even an array that throws on read is fine (tested)."),
 ],
 how=[
  ("`const start = createTypedSpanStarter(ctx, [operationSchema, requestSchema])`。", "`const start = createTypedSpanStarter(ctx, [operationSchema, requestSchema])`."),
  ("`await start('operation', { kind: 'read' }, (_op, child) => child('request', { provider: 'example' }, (req) => …))`。", "`await start('operation', { kind: 'read' }, (_op, child) => child('request', { provider: 'example' }, (req) => …))`."),
  ("单独声明的 schema 数组要加 `as const`，才能保持元组类型。", "A separately declared schema array needs `as const` to keep its tuple type."),
 ],
 files=[
  (U + "index.ts", r"^export function createTypedSpanStarter", "createTypedSpanStarter()", "入口", "entry point"),
  (U + "index.ts", r"^function bindTypedSpanStarter", "bindTypedSpanStarter()", "运行时的全部实现", "the whole run-time part"),
  (U + "index.ts", r"^export type TypedSpanStarter", "TypedSpanStarter", "按名重载", "per-name overloads"),
  (U + "index.ts", r"^type UniqueTelemetrySchemas", "UniqueTelemetrySchemas", "拒绝重名 span", "rejects duplicate names"),
  (U + "index.ts", r"^export type ExactTelemetryAttributes", "ExactTelemetryAttributes", "拒绝多余的键", "rejects extra keys"),
 ]),

dict(id="tel-pi", group="arch", layer="ai", diagram="tel_pi",
 title=("在 pi 里的位置", "Where it sits in pi"),
 takeaway=("README 规定的分工是：pi-telemetry 拥有契约，pi-ai 只接受并传递 `telemetryContext`，pi-agent-core 拥有 `pi.ai.*` / `pi.harness.*` / `pi.session.*` 的 schema。在 v1.1.0 里前两条已经实现——`ProviderRequestOptions.telemetryContext` 经 `buildBaseOptions()` 原样到达每条分派路径——第三条还没有：agent-core 既不依赖这个包，也没有这些 schema。",
           "The README's division of labour: pi-telemetry owns the contract, pi-ai only accepts and propagates `telemetryContext`, and pi-agent-core owns the `pi.ai.*` / `pi.harness.*` / `pi.session.*` schemas. At v1.1.0 the first two are in place — `ProviderRequestOptions.telemetryContext` reaches every dispatch path unchanged through `buildBaseOptions()` — but the third is not: agent-core neither depends on the package nor has those schemas."),
 points=[
  ("pi-ai 的 src 里没有一处 `startSpan`：开 span 的是拿到上下文的 provider 实现或更上层的代码。", "There is no `startSpan` anywhere in pi-ai's src: spans are opened by the provider implementation or higher-level code that receives the context."),
  ("pi-ai 的测试检查了 8 条流式 / 延迟分派路径（provider 与 Models 各 4 条）和图像分派，拿到的都是同一个对象。", "pi-ai's tests check 8 streaming / deferred dispatch paths (4 each on the provider and on Models) plus image dispatch, and all receive the very same object."),
  ("安全规则：不要把上下文或 span 存进记录、消息、快照或 deferred handle；属性避开提示词、输出、文件内容与凭据。", "Security rules: never store a context or span in records, messages, snapshots or deferred handles; keep prompts, outputs, file contents and credentials out of attributes."),
 ],
 how=[
  ("`streamSimple(model, context, { telemetryContext: span })`：把当前 span 作为这次请求的父上下文。", "`streamSimple(model, context, { telemetryContext: span })`: make the current span the parent of this request."),
  ("自定义 provider 在 `stream(model, context, options)` 里读 `options.telemetryContext`，自己决定开哪些子 span。", "A custom provider reads `options.telemetryContext` in `stream(model, context, options)` and decides which child spans to open."),
  ("适配器可以在内部激活后端的环境上下文以便自动埋点，但 pi 代码始终显式传递父上下文。", "An adapter may activate its backend's ambient context internally for auto-instrumentation, but pi code always passes the parent explicitly."),
 ],
 files=[
  (AI + "types.ts", r"telemetryContext\?: TelemetryContext;", "ProviderRequestOptions.telemetryContext", "选项字段", "the option field"),
  (AI + "api/simple-options.ts", r"telemetryContext: options\?\.telemetryContext", "buildBaseOptions()", "原样传递", "passed through as is"),
  ("packages/ai/test/telemetry-options.test.ts", r"survives provider and Models stream/deferred dispatch", "telemetry-options.test.ts", "每条分派路径", "every dispatch path"),
  ("packages/telemetry/README.md", r"^## Pi Package Integration", "README · Pi Package Integration", "分工", "ownership"),
  ("packages/telemetry/README.md", r"^## Security and Portability", "README · Security and Portability", "安全与可移植性", "security and portability"),
 ]),
]

EXT_POINTS = [
 ("TelemetryContext", ("实现它就是一个适配器：把 startSpan 映射到 OpenTelemetry、Sentry、日志或任何后端。", "Implementing it makes an adapter: map startSpan onto OpenTelemetry, Sentry, logs or any backend.")),
 ("createTelemetryAdapterConformance(factory)", ("用 9 个一致性用例验证你的适配器，可注册到任何测试框架。", "Verify your adapter with the 9 conformance cases, registered with any test runner.")),
 ("defineTelemetrySchema + createTypedSpanStarter", ("为自己的领域定义封闭的 span 词汇，在编译期检查名字与属性。", "Define a closed span vocabulary for your domain, with names and attributes checked at compile time.")),
 ("ProviderRequestOptions.telemetryContext", ("把父 span 交给 pi-ai 的一次请求；provider 实现决定开哪些子 span。", "Hand a parent span to one pi-ai request; the provider implementation decides which child spans to open.")),
 ("InMemoryTelemetryContext", ("在测试里断言你的代码产生了哪些 span、属性、事件与状态。", "Assert in tests which spans, attributes, events and statuses your code produced.")),
]
XREF = [('pi-ai', ('在请求选项上接受并传递 telemetryContext', 'accepts and propagates telemetryContext on request options')),
        ('agent-core', ('README 计划由它拥有 pi 的 AI 请求与 Harness schema', 'the README plans for it to own pi\'s AI-request and harness schemas')),
        ('coding-agent', ('同名但无关的“安装遥测”开关', 'the unrelated install-telemetry switch of the same name')),
        ('evals', ('另一种观测方式：评测运行的 token、工具调用、耗时与成本', 'another kind of observation: tokens, tool calls, latency and cost of eval runs'))]
