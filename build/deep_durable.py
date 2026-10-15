# pi-durable deep dive. Same section schema as deep_agent.py; files: (path, regex, symbol, zh, en)
from pkgsrc import Pkg, users_of
D = Pkg('packages/durable/src/')
U = 'packages/durable/src/'
SLIDE_KEYS = ['dur_arch', 'dur_model', 'dur_run', 'dur_tasks', 'dur_inbox', 'dur_docs', 'dur_storage', 'dur_ext']
_LOC = D.total(); _H = D.total('harness/'); _US = users_of('@earendil-works/pi-durable')
_USZ = '、'.join(f'`{a}`（{b} 个文件）' for a, b in _US); _USE = ', '.join(f'`{a}` ({b} files)' for a, b in _US)

INTRO = dict(
 takeaway=("`pi-durable` 是一个**可持久化、可恢复**的 agent 运行时：会话的一切——转录条目、类型化文档、任务、排队的提交——都通过一条原子提交线写进存储；模型调用、工具调用和压缩都是每一步都存检查点的任务，进程崩溃后从最后一个检查点继续。UI 需要的一切都是已提交的状态，用 chord 的复制状态观察。",
           "`pi-durable` is a **persistent, resumable** agent runtime: everything about a conversation — transcript entries, typed documents, tasks, queued submissions — is written to storage through one line of atomic commits; model calls, tool calls and compactions are tasks that checkpoint every step, so after a crash a process continues from the last checkpoint. Everything a UI needs is committed state, watched as chord replicated state."),
 role=(f"共 {_LOC:,} 行 TypeScript，其中 harness（运行 agent 的部分）{_H:,} 行。依赖 `chord`、`pi-ai`、`diff` 与 `typebox`。导入它的包：{_USZ}——`coding-agent` 的用法都在 `src/experimental/` 下；`env` 实现了它的 `ExecutionEnv`。",
       f"{_LOC:,} lines of TypeScript, {_H:,} of them in the harness (the part that runs agents). Depends on `chord`, `pi-ai`, `diff` and `typebox`. Imported by {_USE} — `coding-agent`'s uses are all under `src/experimental/`; `env` implements its `ExecutionEnv`."),
)

SECTIONS = [
dict(id="dur-arch", group="arch", layer="infra", diagram="dur_arch",
 title=("模块结构", "Module structure"),
 takeaway=("自下而上：根目录的核心类型（`Storage`、`TaskState`、条目与文档定义）、`session/`（唯一的提交线与观察）、`harness/`（调度器和三个内置任务，最大的一块）、`storage/`（Memory、SQLite、JSONL 与 Cloudflare 后端）、`env/` 与 `tools/`（执行环境与 read / write / edit / bash），以及给自定义后端用的 `testing/` 一致性套件。",
           "Bottom up: core types at the root (`Storage`, `TaskState`, entry and document definitions), `session/` (the single commit line and observation), `harness/` (the scheduler and three built-in tasks, the biggest part), `storage/` (Memory, SQLite, JSONL and Cloudflare backends), `env/` and `tools/` (execution environments and read / write / edit / bash), and `testing/` conformance suites for custom backends."),
 points=[
  ("11 个导入路径让宿主只加载需要的部分：例如 `./storage/sqlite` 与 `./storage/jsonl` 的可移植核心不依赖 Node API，可以跑在 Bun 或 Cloudflare Durable Object 上。", "11 import paths let a host load only what it needs: the portable cores `./storage/sqlite` and `./storage/jsonl`, for example, need no Node APIs and run on Bun or in Cloudflare Durable Objects."),
  ("最大的文件是 `harness/scheduler.ts`：它拥有所有活任务的调度、恢复、所有权与中止。", "The largest file is `harness/scheduler.ts`: it owns scheduling, recovery, ownership and abort for every live task."),
  ("包根会加载 TypeBox（工具参数校验用 pi-ai 的 `validateToolArguments()`）；README 给出的代价约 23 MB 峰值 RSS，tree-shaken 打包后约 4 MB。", "The package root loads TypeBox (tool arguments are validated with pi-ai's `validateToolArguments()`); the README puts the cost at about 23 MB of peak RSS, about 4 MB tree-shaken."),
 ],
 how=[
  ("`const harness = await Harness.open(storage, { models, registry }, ctx)`。", "`const harness = await Harness.open(storage, { models, registry }, ctx)`."),
  ("`const root = await harness.root(ctx, { agent })`，然后 `root.submit({ type: \"input\", content }, ctx)`。", "`const root = await harness.root(ctx, { agent })`, then `root.submit({ type: \"input\", content }, ctx)`."),
  ("`await (await …submit(…)).wait(ctx)` 得到 `done` 或带原因的 `unanswered`。", "`await (await …submit(…)).wait(ctx)` gives `done` or `unanswered` with a reason."),
 ],
 files=[
  (U + "index.ts", r"^export \{ Harness \} from", "export …", "包入口", "package entry"),
  (U + "harness/harness.ts", r"^export const Harness = \{", "Harness", "Harness.open()", "Harness.open()"),
  (U + "types.ts", r"^export interface Storage \{", "Storage", "存储接口", "the storage interface"),
  (U + "session/session.ts", r"^export class SessionImpl", "SessionImpl", "提交线", "the commit line"),
  (U + "harness/scheduler.ts", r"^export class TaskScheduler", "TaskScheduler", "任务调度", "task scheduling"),
 ]),

dict(id="dur-model", group="types", layer="infra", diagram="dur_model",
 title=("概念模型", "The model"),
 takeaway=("Harness 打开一份存储；Session 是唯一的原子提交线，提交之前什么都不会被看到。一个 Conversation 由不可变的**条目**（`pi.user`、`pi.assistant`、`pi.system`、`pi.tool-result`、`pi.reset`、`pi.compaction`）、类型化的**文档**（`pi.agent`、`pi.provider`、`pi.live`、`pi.inbox`、`pi.usage` 与你自己的）、**任务**和**提交**组成；它用什么跑（模型、扩展、工具、cwd）存在 `pi.agent` 文档里，按名字对照 Registry 解析。",
           "A Harness opens one storage; the Session is the single line of atomic commits, and nothing is shown before it is stored. A Conversation is made of immutable **entries** (`pi.user`, `pi.assistant`, `pi.system`, `pi.tool-result`, `pi.reset`, `pi.compaction`), typed **documents** (`pi.agent`, `pi.provider`, `pi.live`, `pi.inbox`, `pi.usage` and your own), **tasks** and **submissions**; what it runs with (model, extensions, tools, cwd) is stored in the `pi.agent` document by name and resolved against the Registry."),
 points=[
  ("`conversation.commit(tx => …)` 可以在一次原子写入里追加条目、改文档、建任务——要么全部存下，要么全不存。", "`conversation.commit(tx => …)` can append entries, edit documents and create tasks in one atomic write — all of it is stored or none of it."),
  ("`Conversation` 句柄不持有状态，按 `id` 比较；模型只看到最新一个 `pi.reset` 之后的条目，旧条目仍留在存储里。", "A `Conversation` handle holds no state; compare by `id`. The model sees entries from the newest `pi.reset` on; older ones stay in storage."),
  ("Registry 不被存储：扩展被卸载后，选它的会话只是暂时拿不到它，名字仍保留，重新安装就恢复。", "The Registry is not stored: after an extension is uninstalled, conversations that select it just stop getting it; the name stays and reinstalling restores it."),
  ("`settings`（重试、压缩、进度间隔、排队模式…）每次使用时读取、从不存储，所以可以用 getter 让它实时生效。", "`settings` (retry, compaction, progress intervals, queue modes…) are read at every use and never stored, so getters make them live."),
 ],
 how=[
  ("`defineEntry(\"app.note\")`、`defineDoc({ kind, version, scope, history, fork, initial })` 定义你自己的记录。", "`defineEntry(\"app.note\")` and `defineDoc({ kind, version, scope, history, fork, initial })` define your own records."),
  ("`root.configure({ model, tools, cwd, … }, ctx)` 在一次提交里改 `pi.agent`；`null` 把字段清回宿主默认。", "`root.configure({ model, tools, cwd, … }, ctx)` changes `pi.agent` in one commit; `null` clears a field back to the host default."),
  ("`harness.createConversation()` / `root.fork(entryId, …)` 建更多会话；分叉拿到新的 provider 会话 ID。", "`harness.createConversation()` / `root.fork(entryId, …)` create more conversations; a fork gets a fresh provider session ID."),
 ],
 files=[
  (U + "entries.ts", r"^export const UserEntry = ", "UserEntry …", "内置条目", "built-in entries"),
  (U + "documents.ts", r"^export function defineDoc<T extends JsonObject>\(definition", "defineDoc()", "文档定义", "document definitions"),
  (U + "session/transaction.ts", r"^export class Transaction implements Tx", "Transaction", "一次提交", "one commit"),
  (U + "harness/agent.ts", r"^export const AgentDoc = defineDoc", "AgentDoc", "pi.agent", "pi.agent"),
  (U + "harness/agent.ts", r"^export function resolveSettings\(", "resolveSettings()", "settings 默认值", "settings defaults"),
 ]),

dict(id="dur-run", group="flows", layer="infra", diagram="dur_run",
 title=("回答一次输入", "Answering one input"),
 takeaway=("`submit(input)` 先提交一个 `pi.user` 条目，再由内置的 `pi.generation` 任务调用模型：它在提示词或工具变化时写 `pi.system`，写下带工具调用的 `pi.assistant`，为每个调用建一个归它所有的 `pi.tool` 任务并等待；工具结果写成 `pi.tool-result` 后，下一个 generation 接手，直到模型给出最终回答，submission 变为 done。",
           "`submit(input)` first commits a `pi.user` entry; the built-in `pi.generation` task then calls the model: it writes `pi.system` when the prompt or tools changed, writes the `pi.assistant` with tool calls, creates one owned `pi.tool` task per call and waits; once results are written as `pi.tool-result`, the next generation takes over until the model answers and the submission is done."),
 points=[
  ("generation 的检查点阶段：prepare → request → retry（退避重试，默认最多 3 次）→ poll（延迟回答，默认每 5000 ms）→ tools。", "Generation checkpoint phases: prepare → request → retry (back-off, up to 3 by default) → poll (deferred answers, every 5000 ms by default) → tools."),
  ("pi.tool 在运行 `execute()` 前先提交意图。崩溃后只有声明 `replay: \"safe\"` 的工具会重跑；其余给模型一个 interrupted 错误结果，附带已提交的输出。", "pi.tool commits its intent before `execute()` runs. After a crash only tools declared `replay: \"safe\"` rerun; others give the model an interrupted error result with the output committed so far."),
  ("部分回答和工具输出默认最多每 100 ms 提交一次，所以崩溃最多丢这么一个窗口。", "Partial answers and tool output are committed at most every 100 ms by default, so a crash loses at most that window."),
  ("上下文过长被拒时，generation 先压缩再重试一次；`reserveTokens` 之上的请求会等一次压缩完成。", "When a provider rejects a request for being too long, generation compacts and retries once; above `reserveTokens`, the next request waits for a compaction."),
 ],
 how=[
  ("重启：用同一个存储 `Harness.open()`，`harness.root(ctx)` 拿到同一个根会话，`harness.resume()` 启动调度器。", "Restart: `Harness.open()` on the same storage, `harness.root(ctx)` returns the same root, `harness.resume()` starts the scheduler."),
  ("提交时带 `requestId`：重启后同一个请求再提交会拿到原来那个 submission，不会提交两次。", "Submit with a `requestId`: after a restart the same request returns the existing submission instead of submitting twice."),
  ("`harness.submission(id)` 按 ID 重新拿到一个 submission，再 `wait()`。", "`harness.submission(id)` reacquires a submission by ID; then `wait()`."),
 ],
 files=[
  (U + "harness/generation.ts", r"^export const GenerationTask = defineTask", "GenerationTask", "pi.generation", "pi.generation"),
  (U + "harness/generation.ts", r"^export type GenerationCheckpoint =", "GenerationCheckpoint", "5 个阶段", "the 5 phases"),
  (U + "harness/tool.ts", r"^export const ToolTask = defineTask", "ToolTask", "pi.tool", "pi.tool"),
  (U + "harness/tool.ts", r"was interrupted and may have partially run", "interrupted", "崩溃后的工具", "a tool after a crash"),
  (U + "harness/agent.ts", r"^export const DEFAULT_RETRY_POLICY", "DEFAULT_RETRY_POLICY", "重试默认值", "retry defaults"),
  (U + "harness/harness.ts", r"^\tresume\(\): void \{", "resume()", "启动调度器", "starting the scheduler"),
 ]),

dict(id="dur-tasks", group="types", layer="infra", diagram="dur_tasks",
 title=("任务：状态机与所有权", "Tasks: state machine and ownership"),
 takeaway=("任务状态只有 5 种：`pending`（可调度）、`running`（一次内存中的调用）、`waiting`（等 `on` 里的任务，策略 failFast 或 allSettled）、`completing`（结果已定，等它拥有的工作结束）、`terminal`（永久结果）。结果也只有 5 种：completed、failed、aborted、orphaned、faulted。每个任务都有主人：它的会话，或另一个任务。",
           "A task has only 5 states: `pending` (eligible), `running` (one in-memory invocation), `waiting` (on the tasks in `on`, policy failFast or allSettled), `completing` (outcome decided, waiting for owned work) and `terminal` (a permanent receipt). Outcomes are also 5: completed, failed, aborted, orphaned, faulted. Every task has an owner: its conversation, or another task."),
 points=[
  ("每次状态转换都在 Session 的提交线上串行完成；重启后 `running` 的任务显示为 `pending`，直到再次运行。", "Every transition is serialized on the Session's commit line; after a restart, tasks that were `running` show as `pending` until they run again."),
  ("`orphaned` 表示定义或迁移不可用（例如扩展没装回来）；`faulted` 是运行时发现的违约，如未捕获的异常或没有持久进展。", "`orphaned` means the definition or migration is unavailable (e.g. the extension was not reinstalled); `faulted` is a contract failure the runtime detects, such as an uncaught throw or no durable progress."),
  ("中止自下而上：先中止它拥有的工作，等那些结束后才运行它自己的 abort 处理——每个任务只撤销自己的效果。", "Abort runs bottom-up: owned work is aborted first and the task's own abort handler runs only once that is done — each task undoes its own effects."),
  ("`{ background: true }` 的任务是边界：它拥有的工作不受父中止影响，也不让父会话忙碌（subagent 的后台模式就靠它）。", "A `{ background: true }` task is a boundary: its work survives the parent's abort and does not keep the parent busy (background subagents rely on it)."),
 ],
 how=[
  ("`defineTask({ name, version, initial, phases, abort, migrate? })` 定义任务：每个阶段返回下一个状态（running / waiting / terminal）；`abort` 在中止标记后必须提交一个终态结果。", "`defineTask({ name, version, initial, phases, abort, migrate? })` defines a task: each phase returns the next state (running / waiting / terminal); `abort` must commit a terminal outcome after an abort mark."),
  ("在 `runtime.commit()` 里 `tx.createTask(Kind, input, { ownership: { kind: \"task\", taskId } })` 建子任务，再返回 `{ status: \"waiting\", on, policy }`。", "Inside `runtime.commit()`, `tx.createTask(Kind, input, { ownership: { kind: \"task\", taskId } })` creates children; then return `{ status: \"waiting\", on, policy }`."),
  ("`harness.taskGraph(ctx)` 把所有活任务显示为一个 chord state；`harness.inspect()` 报告被缺失定义阻塞的任务。", "`harness.taskGraph(ctx)` shows every live task as one chord state; `harness.inspect()` reports tasks blocked by a missing definition."),
 ],
 files=[
  (U + "types.ts", r"^export type TaskState<S, R> =", "TaskState", "5 种状态", "the 5 states"),
  (U + "types.ts", r"^export type TaskOutcome<R> =", "TaskOutcome", "5 种结果", "the 5 outcomes"),
  (U + "harness/scheduler.ts", r"^const LIVE_STATUSES = ", "LIVE_STATUSES", "活状态", "live states"),
  (U + "tasks.ts", r"^export function defineTask<", "defineTask()", "定义任务", "defining a task"),
  (U + "harness/task-graph.ts", r"^export class TaskGraphView", "TaskGraphView", "任务图", "the task graph"),
 ]),

dict(id="dur-inbox", group="flows", layer="infra", diagram="dur_inbox",
 title=("会话忙时的提交", "Submitting to a busy conversation"),
 takeaway=("run 进行时会话是忙的。这时的输入进入 `pi.inbox` 文档：`whenBusy: \"steer\"` 在当前工具轮之后放入并加入正在跑的工作；默认的 followUp 在 run 回答后放入并开启下一个 run；`\"reject\"` 直接抛 `ConversationBusy`。`{ type: \"write\", entry }` 只追加条目，不问模型。",
           "A conversation is busy while a run is going. Input then goes into the `pi.inbox` document: `whenBusy: \"steer\"` is placed after the current tool round and joins the running work; the default followUp is placed when the run answers and starts the next run; `\"reject\"` throws `ConversationBusy`. `{ type: \"write\", entry }` only appends an entry without asking the model."),
 points=[
  ("`steeringMode` / `followUpMode` 默认 `\"one-at-a-time\"`：每轮放一条；设为 `\"all\"` 时一次放入全部排队项。", "`steeringMode` / `followUpMode` default to `\"one-at-a-time\"`: one per turn; `\"all\"` places every queued item at once."),
  ("run 失败时排队项留在 inbox，等下一次提交时按先后放入。", "If a run fails, queued items stay in the inbox until the next submission places them, oldest first."),
  ("`root.abort(ctx)` 撤回排队的输入（排队的写入保留）、中止当前工作的所有任务，并在会话空闲时返回。", "`root.abort(ctx)` withdraws queued inputs (queued writes stay), aborts every task of the current work and resolves once the conversation is idle."),
  ("`reset()` 忙时也像写入一样排队；在工具轮中放入时会结束当前 run。工具可以用 `control: { handoff }` 请求同样的事。", "`reset()` is queued like a write while busy; placed during a tool round, it ends the current run. A tool can request the same with `control: { handoff }`."),
 ],
 how=[
  ("`root.submit({ type: \"input\", content, whenBusy: \"steer\" }, ctx)`。", "`root.submit({ type: \"input\", content, whenBusy: \"steer\" }, ctx)`."),
  ("UI 直接从 `view.docs[\"pi.inbox\"]` 画出排队区；`submission.abort(ctx)` 撤回一条。", "A UI draws its queue straight from `view.docs[\"pi.inbox\"]`; `submission.abort(ctx)` withdraws one."),
  ("内部：`admitSubmission()` 判断忙闲 → 写入 inbox；每个轮次边界 `prepareBoundary()` / `applyBoundary()` 决定放入哪些。", "Internally: `admitSubmission()` checks busy → writes the inbox; at each turn boundary `prepareBoundary()` / `applyBoundary()` decide what is placed."),
 ],
 files=[
  (U + "harness/submissions.ts", r"^export async function admitSubmission\(", "admitSubmission()", "接收提交", "admitting a submission"),
  (U + "harness/inbox.ts", r"^export const InboxDoc = defineDoc", "InboxDoc", "pi.inbox", "pi.inbox"),
  (U + "harness/inbox.ts", r"^export async function applyBoundary\(", "applyBoundary()", "轮次边界", "turn boundaries"),
  (U + "harness/inbox.ts", r"^export async function withdrawQueuedInputs\(", "withdrawQueuedInputs()", "abort 时撤回", "withdrawal on abort"),
  (U + "harness/types.ts", r"^export type QueueMode = ", "QueueMode", "排队模式", "queue modes"),
 ]),

dict(id="dur-docs", group="types", layer="infra", diagram="dur_docs",
 title=("文档与观察", "Documents and watching"),
 takeaway=("文档是和条目一起提交的类型化 JSON。内置的 5 个都按会话存放：`pi.agent`（可回溯，分叉时取分叉点的值）、`pi.provider`（每个会话一个 UUIDv7 的 `sessionId`，转给 pi-ai 用于提示缓存与会话亲和）、`pi.live`、`pi.inbox`、`pi.usage`。UI 用 `viewState()` 拿到 entries + docs 的只读 chord state，或用 `watch()` 拿到每次提交的精确 op。",
           "Documents are typed JSON committed together with entries. The 5 built-in ones are per conversation: `pi.agent` (rewindable; a fork takes the value at the fork entry), `pi.provider` (one UUIDv7 `sessionId` per conversation, forwarded to pi-ai for prompt caching and session affinity), `pi.live`, `pi.inbox` and `pi.usage`. A UI gets entries + docs as a read-only chord state with `viewState()`, or each commit's exact ops with `watch()`."),
 points=[
  ("`history: \"rewindable\"` 的文档可以用 `snapshotAsOf()` 读旧值；`fork` 决定分叉时的初值：initial、current 或 asOf。", "Documents with `history: \"rewindable\"` can be read as of the past with `snapshotAsOf()`; `fork` decides a fork's start value: initial, current or asOf."),
  ("慢的 `watch()` 消费者最多积压 100 帧，之后整队换成一帧完整的最新视图；迟到或重连的客户端从当前视图开始，不重放历史。", "A slow `watch()` consumer keeps at most 100 undelivered frames, then they become one frame with the whole newest view; late or reconnecting clients start from the current view, nothing is replayed."),
  ("`watchEvents()`（实验性）把提交转换成 coding-agent 风格的事件（message_start、tool_execution_start…）；落后超过 100 批时收到一个新的 snapshot 事件。", "`watchEvents()` (experimental) turns commits into coding-agent style events (message_start, tool_execution_start…); more than 100 batches behind, it delivers a fresh snapshot event."),
  ("`HarnessOptions.conversationCreated(tx, conversation)` 在每个创建或分叉会话的提交里运行，适合给每个会话放上你自己的文档。", "`HarnessOptions.conversationCreated(tx, conversation)` runs in every commit that creates or forks a conversation — the place to give every conversation your own documents."),
 ],
 how=[
  ("`const view = await root.viewState(ctx); view.subscribe(v => render(v))`。", "`const view = await root.viewState(ctx); view.subscribe(v => render(v))`."),
  ("`const w = await root.watch(ctx); render(w.value); w.start(async (value, ops) => send(ops))`——把 op 发给远端客户端重放。", "`const w = await root.watch(ctx); render(w.value); w.start(async (value, ops) => send(ops))` — ship ops to a remote client to replay."),
  ("自己的文档：`(await tx.doc(Todos, root.id)).items.push(\"…\")`；读：`harness.snapshot(Todos, root.id, ctx)`。", "Your own document: `(await tx.doc(Todos, root.id)).items.push(\"…\")`; read: `harness.snapshot(Todos, root.id, ctx)`."),
 ],
 files=[
  (U + "harness/view.ts", r"^export class ConversationViews", "ConversationViews", "viewState / watch", "viewState / watch"),
  (U + "session/observation.ts", r"^const MAX_PENDING_WATCH_FRAMES = ", "MAX_PENDING_WATCH_FRAMES", "100 帧", "100 frames"),
  (U + "session/observation.ts", r"^export class CommittedWatch", "CommittedWatch", "精确 op 的观察", "exact-op watching"),
  (U + "harness/events.ts", r"^export async function watchEvents\(", "watchEvents()", "agent 事件", "agent events"),
  (U + "harness/live.ts", r"kind: \"pi\.live\",", "pi.live", "运行中的工作", "running work"),
  (U + "harness/provider.ts", r"kind: \"pi\.provider\",", "pi.provider", "会话身份", "session identity"),
 ]),

dict(id="dur-storage", group="arch", layer="infra", diagram="dur_storage",
 title=("存储后端", "Storage backends"),
 takeaway=("所有后端实现同一个 `Storage` 接口：`commit(writes, ctx)` 原子地写入一批 `StorageWrite`（8 种：conversation、entry、task、submission 与 document 的 create / copy / change / retire），返回单调递增的 Seq；其余都是按 ID 读取或分页扫描。Memory 不持久化；SQLite 是一个 WAL 模式的数据库文件；JSONL 是一个目录里的追加文件；Cloudflare 版本用一个 Durable Object 的 SQLite。",
           "Every backend implements one `Storage` interface: `commit(writes, ctx)` atomically writes a batch of `StorageWrite`s (8 kinds: conversation, entry, task, submission, and document create / copy / change / retire) and returns an increasing Seq; everything else is reads by ID or paged scans. Memory persists nothing; SQLite is one WAL-mode database file; JSONL is append-only files in a directory; the Cloudflare one uses a Durable Object's SQLite."),
 points=[
  ("SQLite：`journal_mode = WAL`、`synchronous = NORMAL`、`wal_autocheckpoint` 1000 页、busy 超时 5000 ms——提交能挺过进程崩溃，断电可能丢最新一个。", "SQLite: `journal_mode = WAL`, `synchronous = NORMAL`, `wal_autocheckpoint` 1000 pages, a 5000 ms busy timeout — commits survive process crashes; power loss may drop the newest."),
  ("JSONL：每次提交在 `main.jsonl` 追加一行 `{ format: 1, type: \"commit\", seq, writes }` 标记；任务与文档的大内容写进 `task-<id>.jsonl` / `doc-<id>.jsonl` 旁路文件；`{ fsync: true }` 在标记前刷盘。", "JSONL: each commit appends one `{ format: 1, type: \"commit\", seq, writes }` marker to `main.jsonl`; task and document payloads go to `task-<id>.jsonl` / `doc-<id>.jsonl` sidecars; `{ fsync: true }` flushes before the marker."),
  ("同一时刻只有一个进程拥有一个存储，没有跨进程锁。", "One process owns a storage at a time; there is no cross-process locking."),
  ("自定义后端可以用 `registerStorageConformance()` 跑共享的一致性套件，任何 Vitest / Jest 兼容的 runner 都行。", "A custom backend can run the shared suite with `registerStorageConformance()` under any Vitest- or Jest-compatible runner."),
 ],
 how=[
  ("`openNodeSqliteStorage(\"./session.sqlite\")` 或 `openNodeJsonlStorage(dir, ctx)`，交给 `Harness.open()`。", "`openNodeSqliteStorage(\"./session.sqlite\")` or `openNodeJsonlStorage(dir, ctx)`, passed to `Harness.open()`."),
  ("非 Node 环境：给可移植核心一个异步的 `SqliteDatabase` 外观（exec / run / get / all / transaction / close）或一个 `FileSystem`。", "Outside Node: give a portable core an async `SqliteDatabase` facade (exec / run / get / all / transaction / close) or a `FileSystem`."),
  ("Cloudflare：`openDurableObjectSqliteStorage(ctx.storage)`。", "Cloudflare: `openDurableObjectSqliteStorage(ctx.storage)`."),
 ],
 files=[
  (U + "types.ts", r"^export type StorageWrite =", "StorageWrite", "8 种写入", "the 8 writes"),
  (U + "storage/memory.ts", r"^export class MemoryStorage implements Storage", "MemoryStorage", "内存", "memory"),
  (U + "storage/sqlite/node.ts", r"^export async function openNodeSqliteStorage\(", "openNodeSqliteStorage()", "SQLite（Node）", "SQLite (Node)"),
  (U + "storage/sqlite/migrations.ts", r"CREATE TABLE entries \(", "entries", "SQLite 表结构", "SQLite schema"),
  (U + "storage/jsonl/storage.ts", r"^export class JsonlStorage implements Storage", "JsonlStorage", "JSONL", "JSONL"),
  (U + "storage/sqlite/cloudflare.ts", r"^export function openDurableObjectSqliteStorage\(", "openDurableObjectSqliteStorage()", "Cloudflare", "Cloudflare"),
 ]),

dict(id="dur-ext", group="arch", layer="infra", diagram="dur_ext",
 title=("扩展、钩子与重载", "Extensions, hooks and reload"),
 takeaway=("Harness 运行的代码（内置任务之外）都来自安装在 Registry 里的命名扩展。一个扩展可以带 `tools`、`sections`（系统提示词段）、`hooks`（挂在 GenerationTask、ToolTask、CompactionTask 上）、`wraps`（按名字装饰工具或段）和 `tasks`。默认每个会话按安装顺序选用全部扩展。",
           "Code the Harness runs, other than its built-in tasks, comes from named extensions installed in a Registry. An extension may bring `tools`, `sections` (system-prompt sections), `hooks` (on GenerationTask, ToolTask, CompactionTask), `wraps` (decorating a tool or section by name) and `tasks`. By default every conversation selects every installed extension, in install order."),
 points=[
  ("钩子：generation 有 `beforeRequest`、`afterResponse`、`onYield`（`{ continue }` 让 run 继续）、`afterTools`；工具有 `beforeTool`（`{ block }` 或改参数）、`afterTool`；压缩有 `beforeCompact`。", "Hooks: generation has `beforeRequest`, `afterResponse`, `onYield` (`{ continue }` keeps the run going), `afterTools`; tools have `beforeTool` (`{ block }` or rewrite arguments), `afterTool`; compaction has `beforeCompact`."),
  ("段与工具的变化存成转录里按位置的 `pi.system` 条目，只重发变化的部分，让 provider 的提示缓存保持命中；每次都变的段会破坏缓存。", "Section and tool changes are stored as positional `pi.system` entries, and only changes are resent, keeping provider prompt caches warm; a section that changes every time defeats that."),
  ("同名工具后安装的覆盖先安装的；`wrapTool()` 装饰最后胜出的那个。工具结果带 `control: { terminate: true }` 且整轮都这样时，run 不再请求模型就结束。", "A later extension's same-name tool replaces an earlier one; `wrapTool()` decorates whichever won. When every result of a round returns `control: { terminate: true }`, the run ends without another model request."),
  ("重载：同名 `install()` 原地替换。已开始的工作保留它拿到的代码；每个任务阶段开始时从 Registry 解析一次钩子与 agent，下一阶段才用新代码。", "Reload: `install()` with an installed name replaces in place. Started work keeps the code it took; each task phase resolves hooks and the agent once at its start, and the next phase uses the new code."),
 ],
 how=[
  ("`defineExtension({ name, tools: [defineTool({ name, parameters, execute })], sections: [section(\"cwd\", i => i.env?.cwd)] })`。", "`defineExtension({ name, tools: [defineTool({ name, parameters, execute })], sections: [section(\"cwd\", i => i.env?.cwd)] })`."),
  ("`registry.install(ext)`；只想在部分会话生效时，用 `configure({ extensions: { add: [Ext] } })` 选上。", "`registry.install(ext)`; to limit it to some conversations, select it with `configure({ extensions: { add: [Ext] } })`."),
  ("`@earendil-works/pi-durable/tools` 的 `CodingTools` 一次装上 read、write、edit、bash，它们只通过调用的执行环境访问文件与进程。", "`CodingTools` from `@earendil-works/pi-durable/tools` installs read, write, edit and bash at once; they touch files and processes only through the call's environment."),
 ],
 files=[
  (U + "harness/define.ts", r"^export function defineExtension<", "defineExtension()", "定义扩展", "defining an extension"),
  (U + "harness/define.ts", r"^export function hook<", "hook()", "钩子", "hooks"),
  (U + "harness/registry.ts", r"^export function createRegistry<", "createRegistry()", "Registry", "the Registry"),
  (U + "harness/registry.ts", r"^export const BUILTIN_TASKS", "BUILTIN_TASKS", "三个内置任务", "the three built-in tasks"),
  (U + "harness/prompt.ts", r"^export function planSystemEntries\(", "planSystemEntries()", "按位置的系统条目", "positional system entries"),
  (U + "tools/index.ts", r"^export const CodingTools = defineExtension", "CodingTools", "内置工具", "built-in tools"),
 ]),
]

EXT_POINTS = [
 ("defineExtension({ tools, sections, hooks, wraps, tasks })", ("把功能打包成一个可安装、可重载的扩展。", "Package functionality as an installable, reloadable extension.")),
 ("defineTool({ parameters, execute, replay })", ("TypeBox 参数；replay: \"safe\" 让崩溃后重跑。", "TypeBox parameters; replay: \"safe\" reruns after a crash.")),
 ("hook(Task, { … })", ("观察或调整内置任务：beforeTool、onYield、beforeCompact…", "Observe or adjust built-in tasks: beforeTool, onYield, beforeCompact…")),
 ("defineDoc / defineEntry / defineTask", ("你自己的文档、条目和持久任务。", "Your own documents, entries and durable tasks.")),
 ("Storage", ("实现 commit + 读取接口，用一致性套件验证。", "Implement commit + the read interface, verify with the conformance suite.")),
 ("ExecutionEnv", ("FileSystem + exec：例如 env 包的 RemoteExecutionEnv。", "FileSystem + exec: e.g. the env package's RemoteExecutionEnv.")),
 ("HarnessOptions.env / settings", ("每次调用构建环境；实时读取的运行策略。", "Build the environment per call; run policy read live.")),
]
XREF = [('chord', ('viewState / watch 返回 chord 复制状态；每个调用带 chord Context', 'viewState / watch return chord replicated states; every call takes a chord Context')),
        ('env', ('在另一台机器上实现 ExecutionEnv', 'implements ExecutionEnv on another machine')),
        ('pi-ai', ('generation 通过 pi-ai 调用模型，并转发 sessionId', 'generation calls models through pi-ai and forwards the sessionId')),
        ('coding-agent', ('src/experimental 下的 durable 运行时与 vacation 模式', 'the durable runtime and vacation mode under src/experimental'))]
