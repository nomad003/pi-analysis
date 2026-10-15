# pi-evals deep dive. Same section schema as deep_agent.py; files: (path, regex, symbol, zh, en)
from pkgsrc import Pkg
E_ = Pkg('packages/evals/src/')
U = 'packages/evals/src/'
V = 'packages/evals/evals/'
D = 'packages/evals/docker/'
SLIDE_KEYS = ['ev_arch', 'ev_suites', 'ev_pipeline', 'ev_plan', 'ev_docker', 'ev_sandbox', 'ev_harness', 'ev_report']
_TS = E_.total()

INTRO = dict(
 takeaway=("`pi-evals` 是一个**私有**包，用来回答一个具体问题：pi 自带的文档到底有没有帮模型把事做对？它用 `vitest-evals` 写行为评测，主角是“文档提升”评测：同一个用例在两个只差文档的 Docker 镜像里各跑一遍（`without_docs` 是对照组，`with_docs` 是实验组），每次都是一个新容器、一个真实的 `AgentSession`，模型的工具在 UID 65532 下运行、读不到评分器和夹具；最后成对比较通过率，任何一对不完整就不公布结果。另有两个直接在本机跑的 host 评测（冒烟、文档审计）。",
           "`pi-evals` is a **private** package that answers one concrete question: does pi's bundled documentation actually help a model get things right? It writes behavioural evals with `vitest-evals`, and its centrepiece is the documentation-lift eval: each case runs in two Docker images that differ only in the docs (`without_docs` is the control, `with_docs` the treatment), every time in a fresh container with a real `AgentSession`, the model's tools running as UID 65532 unable to read judges or fixtures; the arms are then compared in pairs, and nothing is published if any pair is incomplete. Two host evals (smoke, documentation audit) run directly on the machine."),
 role=(f"{_TS:,} 行 TypeScript 运行器（`src/` 的 5 个文件）、7 个评测文件与 2 个夹具（`evals/`）、一个 5 阶段的 Dockerfile 与容器入口（`docker/`）。`private: true`，没有 `exports`，不发布到 npm；通过 `npm run eval -w packages/evals` 使用。被测对象是 `pi-coding-agent`（容器里用 `dist/`，本机通过别名指向源码），用到 `pi-ai` 的 `InMemoryCredentialStore`。包没有 CHANGELOG。",
       f"A {_TS:,}-line TypeScript runner (5 files in `src/`), 7 eval files and 2 fixtures (`evals/`), and a 5-stage Dockerfile plus container entrypoint (`docker/`). `private: true`, no `exports`, never published to npm; you use it through `npm run eval -w packages/evals`. The subject under test is `pi-coding-agent` (from `dist/` in containers, aliased to source on the host), and it uses `pi-ai`'s `InMemoryCredentialStore`. The package has no CHANGELOG."),
)

SECTIONS = [
dict(id="ev-arch", group="arch", layer="infra", diagram="ev_arch",
 title=("运行器、评测定义与镜像：三个目录", "Runner, eval definitions and image: three directories"),
 takeaway=("`src/` 是运行器：`cli.ts` 编排一次对比，`docker.ts` 构建两个镜像并运行一侧，`plan.ts` 展开任务，`report.ts` 读 Vitest JSON、配对、算提升，`harness.ts` 是 vitest-evals 适配器。`evals/` 放评测定义和夹具；`docker/` 放镜像构建文件。package.json 只有五个脚本：`test`、`eval:host`、`eval:docs`、`eval` 与 `clean`。",
           "`src/` is the runner: `cli.ts` orchestrates one comparison, `docker.ts` builds the two images and runs one arm, `plan.ts` expands tasks, `report.ts` reads Vitest JSON, pairs arms and computes lift, and `harness.ts` is the vitest-evals adapter. `evals/` holds eval definitions and fixtures; `docker/` holds the image build files. package.json has just five scripts: `test`, `eval:host`, `eval:docs`, `eval` and `clean`."),
 points=[
  ("`*.docs.eval.ts` 是文档提升评测，由 `eval:docs` 在容器里成对运行；其余 `*.eval.ts` 是普通的 host 评测，由 `eval:host` 在本机运行。", "`*.docs.eval.ts` files are documentation-lift evals, run in pairs in containers by `eval:docs`; other `*.eval.ts` files are ordinary host evals run on the machine by `eval:host`."),
  ("评测文件只依赖 `harness.ts` 的两个工厂：`createPiCodingAgentHarness()`（host）与 `createPiDocumentationEvalHarness()`（docs）。", "Eval files depend only on two factories in `harness.ts`: `createPiCodingAgentHarness()` (host) and `createPiDocumentationEvalHarness()` (docs)."),
  ("`harness.ts` 只从 `report.ts` 拿一个常量 `PI_SESSION_SNAPSHOT_ARTIFACT`：会话快照随结果一起写进 Vitest JSON。", "`harness.ts` takes just one constant from `report.ts`, `PI_SESSION_SNAPSHOT_ARTIFACT`: the session snapshot travels with the result inside the Vitest JSON."),
 ],
 how=[
  ("全部评测：`PI_PROVIDER=… PI_MODEL=… npm run eval -w packages/evals`（先 host，再 docs）。", "Everything: `PI_PROVIDER=… PI_MODEL=… npm run eval -w packages/evals` (host first, then docs)."),
  ("只跑 host：`npm run eval:host -w packages/evals`；`--` 之后的参数只传给 `eval:docs`。", "Host only: `npm run eval:host -w packages/evals`; flags after `--` go to `eval:docs` only."),
  ("运行器自身的单元测试：`npm test -w packages/evals`（test/ 下 6 个文件）。", "The runner's own unit tests: `npm test -w packages/evals` (6 files under test/)."),
 ],
 files=[
  (U + "cli.ts", r"const images = buildImages\(\);", "cli.ts", "编排一次对比", "orchestrates a comparison"),
  (U + "docker.ts", r"^export function buildImages", "buildImages", "两个镜像", "the two images"),
  (U + "harness.ts", r"^export function createPiCodingAgentHarness", "createPiCodingAgentHarness", "vitest-evals 适配器", "the vitest-evals adapter"),
  ("packages/evals/package.json", r'"private": true', "private", "不发布", "not published"),
  ("packages/evals/vitest.evals.config.ts", r'name: "docs"', "projects", "docs / host 两个项目", "docs / host projects"),
 ]),

dict(id="ev-suites", group="types", layer="infra", diagram="ev_suites",
 title=("7 个评测：2 个 host，5 个文档提升", "Seven evals: two host, five documentation-lift"),
 takeaway=("host 评测是普通的 vitest-evals 套件：`smoke` 不给工具，只问一个固定答案；`documentation-audit` 用 `it.for` 遍历 coding-agent 的 40 页文档，让模型只读核对实现并提交一个结构化结论。5 个 docs 评测都是“改配置/写扩展 → reload → 检查结果”的真实任务，由 `StructuredOutputJudge`、`ToolCallJudge` 或自定义 `createJudge` 评分，`judgeThreshold: null` 让低分成为数据而不是失败。",
           "Host evals are ordinary vitest-evals suites: `smoke` gives no tools and asks for one fixed answer; `documentation-audit` uses `it.for` over coding-agent's 40 doc pages, having the model check the implementation read-only and submit a structured verdict. The five docs evals are real tasks — change config or write an extension → reload → inspect the result — scored by `StructuredOutputJudge`, `ToolCallJudge` or a custom `createJudge`; `judgeThreshold: null` makes a low score data rather than a failure."),
 points=[
  ("每个 docs 用例的输入都是 `[prompt, reload]` 两步：模型改完配置后，harness 调 `session.reload()`，评分器再从运行时里读出真实状态。", "Every docs case takes two steps, `[prompt, reload]`: after the model edits config the harness calls `session.reload()`, and the judge reads the real state back from the runtime."),
  ("`acme-server.ts` 是本地的 OpenAI 兼容 / NDJSON 流式夹具服务器，供 provider 类用例调用；`configured-runtime.ts` 把运行时状态整理成评分器要比较的结构。", "`acme-server.ts` is a local OpenAI-compatible / NDJSON streaming fixture server for the provider cases; `configured-runtime.ts` shapes runtime state into what judges compare."),
  ("`vitest.evals.config.ts` 分 `docs` 与 `host` 两个项目：串行、单 worker、5 分钟超时；容器外它把 coding-agent 别名到源码。", "`vitest.evals.config.ts` defines `docs` and `host` projects: sequential, one worker, 5-minute timeouts; outside containers it aliases coding-agent to source."),
 ],
 how=[
  ("新增 docs 评测：写 `evals/<name>.docs.eval.ts`，用 `createPiDocumentationEvalHarness({ output })` 把结果整理成可比较的 JSON。", "A new docs eval: write `evals/<name>.docs.eval.ts` and use `createPiDocumentationEvalHarness({ output })` to shape the result into comparable JSON."),
  ("评分：确定的结构用 `StructuredOutputJudge({ expected, match: 'strict' })`；还要求某次工具调用就加 `ToolCallJudge`。", "Scoring: use `StructuredOutputJudge({ expected, match: 'strict' })` for a fixed structure, and add `ToolCallJudge` when a specific tool call is required."),
  ("docs 评测不能在本机直接跑：工厂在容器沙箱外会抛错。", "Docs evals cannot run directly on the host: the factory throws outside the container sandbox."),
 ],
 files=[
  (V + "smoke.eval.ts", r"createPiCodingAgentHarness\(\{ noTools: \"all\" \}\)", "smoke", "不给工具", "no tools"),
  (V + "documentation-audit.eval.ts", r"describeEval\(\"Audit documentation", "documentation-audit", "40 页文档", "40 doc pages"),
  (V + "models.docs.eval.ts", r"^describeEval\(", "models", "StructuredOutputJudge", "StructuredOutputJudge"),
  (V + "extensions.docs.eval.ts", r"ToolCallJudge\(\{", "extensions", "ToolCallJudge", "ToolCallJudge"),
  (V + "tui.docs.eval.ts", r"createJudge<", "tui", "自定义评分器", "a custom judge"),
  (V + "acme-server.ts", r"^export", "acme-server", "夹具服务器", "fixture server"),
 ]),

dict(id="ev-pipeline", group="flows", layer="infra", diagram="ev_pipeline",
 title=("eval:docs：先写下实验计划，再逐个运行", "eval:docs: write the plan down first, then run each arm"),
 takeaway=("`cli.ts` 依次解析参数、确认 `auth.json` 里有该 provider 的凭据、构建两个镜像（id 必须不同）、在两个镜像里分别发现用例（必须完全相同）、生成任务计划，并把 `protocol.json`（含 sha256 协议摘要）和 `expected-runs.json` 写盘；然后对每个任务启动一个新容器，读回 vitest.json，最后汇总成 report.json / report.txt。",
           "`cli.ts` parses arguments, checks `auth.json` holds the provider's credential, builds the two images (whose ids must differ), discovers cases in both images (which must be identical), builds the task plan, and writes `protocol.json` (with a sha256 protocol digest) and `expected-runs.json`; it then starts a fresh container per task, reads the vitest.json back, and finally summarises into report.json / report.txt."),
 points=[
  ("实验设计在运行前就固定：报告按 `expected-runs.json` 检查每一对，而不是只看实际跑出了什么。", "The design is fixed before anything runs: the report checks each pair against `expected-runs.json`, not just against what happened to run."),
  ("`observations.jsonl` 每个任务之后重写：中途崩溃也保留已完成的观测。一侧失败不会中断计划。", "`observations.jsonl` is rewritten after every task, so a crash keeps what finished. One failed arm does not stop the plan."),
  ("存在阻塞对时进程退出码为 1；产物目录 `.eval/<时间戳>_<uuid>/` 权限 0700，且被 git 忽略。", "With blocked pairs the process exits 1; the artifact directory `.eval/<timestamp>_<uuid>/` is 0700 and git-ignored."),
 ],
 how=[
  ("限定用例：`npm run eval:docs -w packages/evals -- -t \"<名字>\" <文件>`。", "Narrow it: `npm run eval:docs -w packages/evals -- -t \"<name>\" <file>`."),
  ("重复次数：`--runs-per-variant 3` 或 `PI_EVAL_RUNS_PER_VARIANT=3`。", "Repetitions: `--runs-per-variant 3` or `PI_EVAL_RUNS_PER_VARIANT=3`."),
  ("复查一次运行：看 `.eval/…/report.txt`，再到 `<variant>/sessions/` 打开原生的 Pi 会话。", "Review a run: read `.eval/…/report.txt`, then open the native Pi sessions under `<variant>/sessions/`."),
 ],
 files=[
  (U + "cli.ts", r"const authPath = requireEvalAuthFile", "requireEvalAuthFile", "凭据", "credentials"),
  (U + "cli.ts", r"Documentation variants resolved to the same image", "same image", "镜像必须不同", "images must differ"),
  (U + "cli.ts", r"compareDiscovery\(discoveries\[0\], discoveries\[1\]\)", "compareDiscovery", "发现结果必须一致", "discoveries must match"),
  (U + "cli.ts", r"const protocolDigest = ", "protocolDigest", "协议摘要", "protocol digest"),
  (U + "cli.ts", r"process.exitCode = 1", "exitCode", "阻塞即失败", "blocked means failure"),
 ]),

dict(id="ev-plan", group="flows", layer="ext", diagram="ev_plan",
 title=("任务计划：用例 × 运行序号 × 两种变体", "The task plan: case × run number × both variants"),
 takeaway=("`createTaskPlan()` 把每个 (用例, 模型, 运行序号) 展开成一对任务：`without_docs` 与 `with_docs`。奇数次运行先跑对照组，偶数次反过来，以减少顺序偏差。用例身份是 `\"<评测集> > <用例>\"` 两段全名，不允许重复；模型身份是 `provider/model`；每个任务的目录名是身份元组的 sha256。",
           "`createTaskPlan()` expands each (case, model, run number) into a pair of tasks, `without_docs` and `with_docs`. Odd runs start with the control and even runs flip, to reduce order bias. A case's identity is its two-part full name `\"<eval set> > <case>\"`, which must be unique; the model identity is `provider/model`; each task's directory name is the sha256 of its identity tuple."),
 points=[
  ("用例来自 `vitest list --json`：`parseDiscoveredCases()` 拒绝不是恰好两段的名字和重复身份。", "Cases come from `vitest list --json`: `parseDiscoveredCases()` rejects names that are not exactly two parts and duplicate identities."),
  ("`runsPerVariant` 必须是正整数，默认 1；模型字符串必须含 `/` 且不在两端。", "`runsPerVariant` must be a positive integer, default 1; the model string must contain `/`, not at either end."),
  ("每个 (用例, 模型, 运行序号) 就是报告里的一“对”：对照组与实验组共享同一个用例定义和评分器。", "Each (case, model, run number) is one \"pair\" in the report: control and treatment share one case definition and one judge."),
 ],
 how=[
  ("想要更稳的结论：提高 `--runs-per-variant`，让 flaky 标记有机会出现。", "For steadier conclusions: raise `--runs-per-variant` so the flaky flag has a chance to show up."),
  ("在单元测试里验证计划：`test/plan.test.ts` 覆盖展开顺序与身份校验。", "Check the plan in unit tests: `test/plan.test.ts` covers expansion order and identity checks."),
 ],
 files=[
  (U + "plan.ts", r"^export const DOCUMENTATION_VARIANTS", "DOCUMENTATION_VARIANTS", "两种变体", "the two variants"),
  (U + "plan.ts", r"^export function createTaskPlan", "createTaskPlan", "展开任务", "expands tasks"),
  (U + "plan.ts", r"runNumber % 2 === 1", "order", "交替顺序", "alternating order"),
  (U + "plan.ts", r"Duplicate eval case identity", "identity", "身份不能重复", "no duplicate identities"),
  (U + "docker.ts", r"const identity = JSON.stringify\(\[task.evalSet", "taskDirectoryName", "任务目录", "task directory"),
 ]),

dict(id="ev-docker", group="arch", layer="ext", diagram="ev_docker",
 title=("一个 Dockerfile，两个只差文档的目标", "One Dockerfile, two targets that differ only in docs"),
 takeaway=("`builder` 阶段挂载整个仓库，`npm ci --ignore-scripts`、离线构建，再用 `install-runtime.mjs` 把 coding-agent 打包安装到 `/opt/evaluator`；`without-docs-install` 删掉 coding-agent 的 README、CHANGELOG、docs/ 与 examples/。`evaluator` 从干净的 node:24-slim 开始，只拷运行器需要的文件并把评测源码设成 root 专属；两个最终目标只在 `node_modules` 的来源和 `PI_EVAL_VARIANT` 上不同。",
           "The `builder` stage mounts the whole repository, runs `npm ci --ignore-scripts` and an offline build, then uses `install-runtime.mjs` to pack and install coding-agent into `/opt/evaluator`; `without-docs-install` deletes coding-agent's README, CHANGELOG, docs/ and examples/. `evaluator` starts from a clean node:24-slim, copies only runner files and makes eval sources root-only; the two final targets differ only in where `node_modules` comes from and in `PI_EVAL_VARIANT`."),
 points=[
  ("两个变体用同一份安装结果：对照组只是在其上删除文档，所以差异只有文档本身。", "Both variants share one installation: the control merely deletes docs from it, so the only difference is the documentation."),
  ("镜像名是 `pi-evals-<仓库路径 sha256 前 12 位>-<variant>:local`；构建后用 `docker image inspect` 取 id，两个 id 相同则直接报错。", "Images are named `pi-evals-<first 12 hex of sha256(repo path)>-<variant>:local`; after building, `docker image inspect` reads the id, and equal ids are an error."),
  ("每个任务一次 `docker run --rm --read-only`：只有 `/tmp` 与 `.vite-temp` 两个 tmpfs 可写，产物目录与只读的 `auth.json` 通过 bind mount 进入。", "Each task is one `docker run --rm --read-only`: only the `/tmp` and `.vite-temp` tmpfs mounts are writable, and the artifact directory and a read-only `auth.json` come in as bind mounts."),
 ],
 how=[
  ("构建上下文是仓库根；`Dockerfile.dockerignore` 排除 `.git`、`.eval`、`node_modules`、`dist`、`coverage` 与 `.env*`。", "The build context is the repo root; `Dockerfile.dockerignore` excludes `.git`, `.eval`, `node_modules`, `dist`, `coverage` and `.env*`."),
  ("改了 coding-agent 之后重新跑 `eval:docs` 即可：每次都会重新构建两个镜像。", "After changing coding-agent just rerun `eval:docs`: it rebuilds both images every time."),
 ],
 files=[
  (D + "Dockerfile", r"^FROM node:24-slim AS builder", "builder", "构建阶段", "build stage"),
  (D + "Dockerfile", r"^FROM builder AS without-docs-install", "without-docs-install", "删文档", "deletes docs"),
  (D + "Dockerfile", r"^FROM node:24-slim AS evaluator", "evaluator", "运行时镜像", "runtime image"),
  (D + "Dockerfile", r"^FROM evaluator AS with_docs", "with_docs", "实验组目标", "treatment target"),
  (D + "install-runtime.mjs", r"installConsumer\(", "install-runtime.mjs", "打包安装", "pack and install"),
  (U + "docker.ts", r'"--read-only",', "docker run", "只读容器", "read-only container"),
 ]),

dict(id="ev-sandbox", group="flows", layer="coding", diagram="ev_sandbox",
 title=("三层防护：模型读不到评分器", "Three guards: the model cannot read its judges"),
 takeaway=("容器以 root 启动：`entrypoint.ts` 先核对 `/repo` 的内容完全符合清单、内部依赖不带文档、变体与文档一致、评测源码只属于 root 并实际以 UID 65532 探测读不到、coding-agent 从 `dist/` 解析，然后把凭据交给沙箱用户并启动 vitest。每个用例里 harness 再建临时目录、隔离环境变量、把凭据放进内存、删除 `auth.json`，最后 `setgroups([])` → `setgid` → `setuid(65532)`，此后模型的工具才开始运行。",
           "The container starts as root: `entrypoint.ts` checks that `/repo` matches an exact allowlist, internal deps carry no docs, the variant matches its docs, eval sources are root-only and an actual read probe as UID 65532 fails, and coding-agent resolves from `dist/`; it then hands credentials to the sandbox user and starts vitest. Inside each case the harness creates a temp root, isolates environment variables, keeps the credential in memory, deletes `auth.json`, and finally `setgroups([])` → `setgid` → `setuid(65532)` — only then do the model's tools run."),
 points=[
  ("docs 评测只给 `read`、`write`、`edit`、`grep`、`find`、`ls` 六个工具：没有 shell，也没有联网搜索。", "Docs evals get only six tools — `read`, `write`, `edit`, `grep`, `find`, `ls`: no shell and no web search."),
  ("Vitest 转换后的评测模块缓存被设成 0600，降权后 harness 再确认一个也读不到。", "Vitest's transformed eval modules are set to 0600, and after dropping privileges the harness confirms none of them is readable."),
  ("README 明确承认边界：调用 provider 需要联网，因此单靠 Docker 不能证明模型写的代码从不联网。", "The README states the limit plainly: provider calls need the network, so Docker alone cannot prove agent-written code never uses it."),
 ],
 how=[
  ("评测要在沙箱外跑会失败：`createPiDocumentationEvalHarness()` 要求 `PI_EVAL_CONTAINER=1` 与沙箱 UID/GID。", "Running outside the sandbox fails: `createPiDocumentationEvalHarness()` requires `PI_EVAL_CONTAINER=1` and a sandbox UID/GID."),
  ("加新夹具时放在 `evals/` 下：它会自动成为 root 专属、对模型不可读。", "Put new fixtures under `evals/`: they automatically become root-only and unreadable to the model."),
 ],
 files=[
  (D + "entrypoint.ts", r"^function assertWorkspace", "assertWorkspace", "镜像清单", "image allowlist"),
  (D + "entrypoint.ts", r"^function assertSandboxCannotRead", "assertSandboxCannotRead", "读取探测", "read probe"),
  (D + "entrypoint.ts", r"Eval does not resolve pi-coding-agent from dist", "dist", "必须用 dist", "must use dist"),
  (U + "harness.ts", r"^export function applyIsolatedEnvironment", "applyIsolatedEnvironment", "环境隔离", "environment isolation"),
  (U + "harness.ts", r"^async function enterToolSandbox", "enterToolSandbox", "降权", "privilege drop"),
  (U + "harness.ts", r"^export const DOCUMENTATION_EVAL_TOOLS", "DOCUMENTATION_EVAL_TOOLS", "六个工具", "six tools"),
 ]),

dict(id="ev-harness", group="flows", layer="coding", diagram="ev_harness",
 title=("一次运行：真实的 AgentSession，跑完即拆", "One run: a real AgentSession, torn down afterwards"),
 takeaway=("`runPiCodingAgent()` 用 `ModelRuntime` 和内存凭据创建服务与会话（`thinkingLevel: \"off\"`），降权后按输入逐步执行 prompt 或 reload，收集转录事件、系统提示词的 sha256、token、工具调用与（有定价时的）成本，校验系统提示词，再交给 `output()` 或直接返回回答。`finally` 里总是保存 session.jsonl、释放会话、删掉临时目录并还原环境。",
           "`runPiCodingAgent()` creates services and a session (`thinkingLevel: \"off\"`) with a `ModelRuntime` and in-memory credentials, drops privileges, runs each input step as a prompt or a reload, collects transcript events, the system prompt's sha256, tokens, tool calls and (when priced) cost, verifies the system prompt, and hands off to `output()` or returns the response. `finally` always saves session.jsonl, disposes the session, removes the temp root and restores the environment."),
 points=[
  ("两种变体的唯一区别：`without_docs` 注册一个隐藏的 `before_agent_start` 扩展，用 `excludePiDocumentation` 剪掉系统提示词里的 `<docs>…</docs>`。", "The only difference between variants: `without_docs` registers a hidden `before_agent_start` extension that cuts `<docs>…</docs>` out of the system prompt with `excludePiDocumentation`."),
  ("`verifySystemPrompt()` 防止实验悄悄失效：`<rules>` 必须还在，`<docs>` 的有无必须与变体一致。", "`verifySystemPrompt()` keeps the experiment from silently breaking: `<rules>` must survive and the presence of `<docs>` must match the variant."),
  ("会话里出现任何意外扩展都会报错：只允许 `<inline:…>` 的隐藏扩展。", "Any unexpected extension in the session is an error: only hidden `<inline:…>` extensions are allowed."),
  ("失败时如果已有诊断数据，错误会带上部分结果（`attachHarnessRunToError`），报告据此把这一侧记为 errored。", "On failure with diagnostics already collected, the error carries a partial run (`attachHarnessRunToError`), and the report records that arm as errored."),
 ],
 how=[
  ("host 评测直接用 `createPiCodingAgentHarness({ tools, noTools, workspaceFiles, output })`。", "Host evals use `createPiCodingAgentHarness({ tools, noTools, workspaceFiles, output })` directly."),
  ("评分器需要的东西放进 `output({ response, session, systemPrompt, agentDir })` 的返回值。", "Put whatever the judge needs into the return value of `output({ response, session, systemPrompt, agentDir })`."),
 ],
 files=[
  (U + "harness.ts", r"^async function runPiCodingAgent", "runPiCodingAgent", "一次运行", "one run"),
  (U + "harness.ts", r"^async function promptAgent", "promptAgent", "一个 prompt 步骤", "one prompt step"),
  (U + "harness.ts", r"^export function verifySystemPrompt", "verifySystemPrompt", "提示词校验", "prompt check"),
  (U + "harness.ts", r"^export function excludePiDocumentation", "excludePiDocumentation", "剪掉 <docs>", "cuts <docs>"),
  (U + "harness.ts", r"^export function createPiDocumentationEvalHarness", "createPiDocumentationEvalHarness", "docs 评测工厂", "docs eval factory"),
 ]),

dict(id="ev-report", group="types", layer="infra", diagram="ev_report",
 title=("报告：结果 → 配对 → 比较", "The report: outcomes → pairs → comparison"),
 takeaway=("`readTaskObservation()` 把每个任务归为 scored、unscored、skipped、pending 或 errored；`resolvePair()` 要求每一侧在计划里恰好一次、恰好观测到一次且已评分，否则这一对被阻塞并写明原因。每个评测集的通过率按 score ≥ 1 计算，提升 = 实验组 − 对照组；只要有一对被阻塞就不公布通过率。另有 5 个标记和 tokens / 工具 / 耗时 / 成本的配对均值差。",
           "`readTaskObservation()` classifies each task as scored, unscored, skipped, pending or errored; `resolvePair()` requires each arm to be planned exactly once, observed exactly once and scored, otherwise the pair is blocked with its reasons. Per eval set, pass rate counts score ≥ 1 and lift = treatment − control; if any pair is blocked, no pass rate is published. There are also five flags and paired mean deltas for tokens / tools / latency / cost."),
 points=[
  ("0 分也是 scored：它是数据。只有没有分数才是 unscored。", "A score of 0 is still scored — it is data. Only a missing score is unscored."),
  ("标记：`no-lift`、`negative-delta`、`control-saturated`、`treatment-saturated`，以及同一用例同一侧跨运行结果不同的 `flaky`。", "Flags: `no-lift`, `negative-delta`, `control-saturated`, `treatment-saturated`, and `flaky` when the same case and arm passes in only some runs."),
  ("运行总量（每个变体的 runs、tokens、工具、耗时、成本）包含出错的运行，并标出有多少次有测量值。", "Operational totals (runs, tokens, tools, latency, cost per variant) include errored runs and say how many were measured."),
 ],
 how=[
  ("先看 `report.txt` 的 Pass rate 行；出现 withheld 时到 Blocked pairs 一节找原因。", "Read the Pass rate line in `report.txt` first; when it says withheld, the Blocked pairs section gives the reasons."),
  ("机器读取用 `report.json`（`schemaVersion: 3`），它带协议摘要，可以和 `protocol.json` 对上。", "For machines use `report.json` (`schemaVersion: 3`); it carries the protocol digest that matches `protocol.json`."),
 ],
 files=[
  (U + "report.ts", r"^export async function readTaskObservation", "readTaskObservation", "每个任务一个结果", "one outcome per task"),
  (U + "report.ts", r"^function resolvePair", "resolvePair", "配对", "pairing"),
  (U + "report.ts", r"^function comparisonFlags", "comparisonFlags", "5 个标记", "five flags"),
  (U + "report.ts", r"^export function summarizeEvalObservations", "summarizeEvalObservations", "比较", "comparison"),
  (U + "report.ts", r"^export function formatEvalComparisonReport", "formatEvalComparisonReport", "report.txt", "report.txt"),
 ]),
]

EXT_POINTS = [
 ("evals/<name>.docs.eval.ts", ("新增一个文档提升评测：自动在两个变体里成对运行并进入报告。", "Add a documentation-lift eval: it runs in pairs in both variants and lands in the report automatically.")),
 ("evals/<name>.eval.ts", ("新增一个 host 评测：普通的 vitest-evals 套件，由 eval:host 在本机运行。", "Add a host eval: an ordinary vitest-evals suite run on the machine by eval:host.")),
 ("createPiDocumentationEvalHarness({ output })", ("把运行后的状态整理成评分器可比较的 JSON。", "Shape the post-run state into JSON a judge can compare.")),
 ("judges: StructuredOutputJudge / ToolCallJudge / createJudge", ("选择或编写评分器；judgeThreshold: null 让分数成为数据。", "Pick or write judges; judgeThreshold: null makes the score data.")),
 ("--runs-per-variant · -t · PI_PROVIDER / PI_MODEL", ("控制重复次数、选择用例和被测模型。", "Control repetitions, select cases and choose the model under test.")),
]
XREF = [('coding-agent', ('被测对象：容器里用 dist/，评测创建真实的 AgentSession', 'the subject under test: dist/ in containers, evals create real AgentSessions')),
        ('pi-ai', ('InMemoryCredentialStore 与 ModelRuntime 的模型与认证', 'InMemoryCredentialStore and ModelRuntime models and auth')),
        ('telemetry', ('另一种观测方式：结构化的 span，而不是评测指标', 'a different kind of observation: structured spans rather than eval metrics'))]
