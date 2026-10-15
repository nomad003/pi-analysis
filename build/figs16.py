"""pi-evals deep-dive diagrams (ev_*). Facts read from /workspace/pi-src/packages/evals at build time."""
import re, json
from svgkit import Fig, maxw, pair
from figs import reg
from figkit import SRC, uml, codebox, bar, dot, hline, vline, chiprow, lines_of
from pkgsrc import Pkg

E_ = Pkg('packages/evals/src/')
EV = SRC / 'packages/evals'
README = (EV / 'README.md').read_text()

def doc(*needles):
    for n in needles: assert n in README, n

def evsrc(p): return (EV / p).read_text()

def suites():
    """[(file, eval set, [case names], kind)] for every eval file, parsed from describeEval / it."""
    out = []
    for p in sorted((EV / 'evals').glob('*.eval.ts')):
        s = p.read_text()
        m = re.search(r'describeEval\(\s*"([^"]+)"', s)
        cases = re.findall(r'\bit(?:\.for\([^)]*\))?\(\s*"([^"]+)"', s)
        out.append((p.name, m.group(1), cases, 'docs' if p.name.endswith('.docs.eval.ts') else 'host'))
    return out

def docs_pages():
    return sorted(p for p in (SRC / 'packages/coding-agent/docs').rglob('*.md'))

# ============================================================== ev_arch
@reg
def ev_arch():
    j = json.loads(evsrc('package.json'))
    assert j['private'] is True and 'exports' not in j and 'main' not in j
    sc = j['scripts']
    assert sc['eval'] == 'npm run eval:host && npm run eval:docs --' and sc['eval:docs'] == 'node --experimental-strip-types src/cli.ts'
    assert sc['eval:host'] == 'vitest run --config vitest.evals.config.ts --project host'
    dev = j['devDependencies']
    assert {'@earendil-works/pi-ai', '@earendil-works/pi-coding-agent', 'vitest-evals', '@vitest-evals/core', 'autoevals'} <= set(dev)
    E_.has('cli.ts', 'import { buildImages, createDockerContext, discoverCases, requireEvalAuthFile, runTask } from "./docker.ts";', 'from "./plan.ts";', 'from "./report.ts";')
    E_.has('harness.ts', 'import { PI_SESSION_SNAPSHOT_ARTIFACT } from "./report.ts";', 'from "@earendil-works/pi-coding-agent";')
    S = suites(); host = [s for s in S if s[3] == 'host']; docs = [s for s in S if s[3] == 'docs']
    assert len(host) == 2 and len(docs) == 5, S
    fx = sorted(p.name for p in (EV / 'evals').glob('*.ts') if not p.name.endswith('.eval.ts'))
    assert fx == ['acme-server.ts', 'configured-runtime.ts'], fx
    tot = E_.total()
    f = Fig('ev_arch', 1120, 580, (f'pi-evals：私有包，{tot:,} 行运行器 + {len(S)} 个评测文件 + 一个多阶段 Docker 镜像', f'pi-evals: a private package — a {tot:,}-line runner, {len(S)} eval files and a multi-stage Docker image'))
    E = f.edge
    f.group(16, 52, 504, 284, 'infra', 'src/', ('运行器', 'the runner'), 'layers', gid='src')
    f.node('cli', 32, 92, 472, 46, 'infra', 'cli.ts', ('eval:docs 的主程序：解析参数 → 镜像 → 发现 → 计划 → 逐个运行 → 报告', 'eval:docs main: parse args → images → discover → plan → run each → report'), None, tsize=10.6, ssize=8.6, tag=f'{E_.loc("cli.ts")}', strong=True)
    R2 = [('plan', 'plan.ts', ('(case, variant, run) 任务', '(case, variant, run) tasks')), ('report', 'report.ts', ('配对与提升', 'pairing and lift')), ('docker', 'docker.ts', ('镜像与一次隔离运行', 'images, one isolated run'))]
    for i, (k, p, d) in enumerate(R2):
        x = 32 + i * 164
        f.node(k, x, 172, 148, 56, 'infra', p, d, None, tsize=10.4, ssize=8.4, tag=f'{E_.loc(p)}')
        E([(x + 74, 138), (x + 74, 172)], 'cli', k, 'dep', 'infra')
    f.node('har', 32, 266, 472, 50, 'coding', 'harness.ts', ('vitest-evals 适配器：在隔离目录里跑一个真实的 AgentSession', 'the vitest-evals adapter: runs a real AgentSession in an isolated directory'), None, tsize=10.6, ssize=8.6, tag=f'{E_.loc("harness.ts")}')
    E([(270, 266), (270, 228)], 'har', 'report', 'dep', 'coding', label='PI_SESSION_SNAPSHOT_ARTIFACT', lpos=(270, 247), lsize=8.6)
    f.group(16, 352, 504, 140, 'modes', 'evals/', ('评测定义与夹具', 'eval definitions and fixtures'), 'check', gid='ev')
    E([(140, 316), (140, 352)], 'har', 'ev', 'dep', 'coding', label=('createPi*Harness', 'createPi*Harness'), lpos=(140, 334), lsize=8.6)
    f.text(32, 400, (f'host（{len(host)}）', f'host ({len(host)})'), 9.2, 650, cls='faint', layer='label')
    chiprow(f, 100, 388, [s[0] for s in host], 'modes', size=8.8, h=18, gap=5)
    f.text(32, 428, (f'docs（{len(docs)}）', f'docs ({len(docs)})'), 9.2, 650, cls='faint', layer='label')
    chiprow(f, 100, 416, [s[0].replace('.docs.eval.ts', '') for s in docs], 'ext', size=8.8, h=18, gap=5)
    f.text(32, 456, ('夹具', 'fixtures'), 9.2, 650, cls='faint', layer='label')
    chiprow(f, 100, 444, fx, 'tui', size=8.8, h=18, gap=5)
    f.text(32, 482, ('docs 评测文件名省略了 .docs.eval.ts', 'docs file names shown without .docs.eval.ts'), 8.4, 450, cls='faint', layer='label')
    # docker
    f.group(536, 52, 568, 170, 'ext', 'docker/', ('镜像构建', 'image build'), 'box', gid='dg')
    DK = [('Dockerfile', ('5 个阶段 · 2 个目标', '5 stages · 2 targets')), ('entrypoint.ts', ('容器内的检查与 vitest', 'in-container checks, vitest')), ('install-runtime.mjs', ('打包并安装工作区', 'pack + install workspace'))]
    for i, (p, d) in enumerate(DK):
        f.node(f'k{i}', 552 + i * 178, 100, 174, 56, 'ext', p, d, None, tsize=9.6, ssize=8.4, tag=f'{lines_of("packages/evals/docker/" + p)}')
    f.text(552, 190, ('镜像里只有运行时：评测源码对模型用户不可读。', 'The image holds only the runtime: eval sources are unreadable to the model user.'), 8.8, 450, cls='muted', layer='label')
    f.text(552, 206, ('Dockerfile.dockerignore 排除 .git、node_modules、dist、.env*。', 'Dockerfile.dockerignore drops .git, node_modules, dist, .env*.'), 8.8, 450, cls='muted', layer='label')
    E([(508, 200), (536, 200)], 'docker', 'dg', 'dep', 'ext')
    # package.json
    f.group(536, 238, 568, 254, 'infra', 'package.json', ('private: true · 没有 exports', 'private: true · no exports'), 'file', gid='pj')
    SC = [('test', ('vitest：test/ 里的单元测试', 'vitest: the unit tests in test/')),
          ('eval:host', ('vitest --project host：在本机跑 host 评测', 'vitest --project host: host evals on this machine')),
          ('eval:docs', ('node src/cli.ts：容器里的文档提升对比', 'node src/cli.ts: the documentation-lift comparison in containers')),
          ('eval', ('eval:host，然后 eval:docs', 'eval:host, then eval:docs')),
          ('clean', ('删除 .eval/ 产物目录', 'delete the .eval/ artifacts'))]
    assert set(sc) == {k for k, _ in SC}, sc
    assert sc['clean'] == 'shx rm -rf .eval'
    for i, (k, d) in enumerate(SC):
        y = 288 + i * 22
        f.text(552, y, k, 9.6, 650, True, cls='strongt', layer='label')
        f.text(640, y, d, 8.8, 450, cls='muted', layer='label')
    f.text(552, 408, ('devDependencies', 'devDependencies'), 9.2, 650, cls='faint', layer='label')
    chiprow(f, 552, 418, ['pi-ai', 'pi-coding-agent'], 'coding', size=8.8, h=18, gap=5)
    chiprow(f, 552, 442, ['vitest-evals', '@vitest-evals/core', 'autoevals', 'vitest'], 'infra', size=8.8, h=18, gap=5)
    f.text(552, 480, ('工作区内的 pi 包都来自当前仓库（npm overrides）。', 'Internal pi packages come from this repository (npm overrides).'), 8.6, 450, cls='muted', layer='label')
    doc('Existing npm overrides ensure coding-agent\'s internal Pi dependencies also come from the current repository rather than the registry.')
    f.text(16, 518, ('评测的对象是 coding-agent 本身：host 评测在本机检验行为；docs 评测在容器里比较“有文档 / 没文档”两种安装，测量文档带来的提升。', 'The subject is coding-agent itself: host evals check behaviour on this machine; docs evals compare a with-docs and a without-docs install in containers to measure documentation lift.'), 9.0, 450, cls='muted', layer='label')
    f.legend(24, 556, [('layer:infra', ('运行器', 'runner')), ('layer:coding', ('harness', 'harness')), ('layer:modes', ('评测', 'evals')), ('layer:ext', ('Docker', 'Docker')), ('dep', ('使用', 'uses'))])
    f.note(1096, 556, ('标签 = 行数', 'tag = lines'), 10.5, anchor='end')
    return f

# ============================================================== ev_suites : what is evaluated
@reg
def ev_suites():
    S = suites()
    cfg = evsrc('vitest.evals.config.ts')
    for n in ['name: "docs",\n\t\t\t\t\t\tinclude: ["evals/**/*.docs.eval.ts"],', 'name: "host",', 'exclude: ["evals/**/*.docs.eval.ts"],', 'testTimeout: 300_000,', 'maxWorkers: 1,', 'fileParallelism: false,']:
        assert n in cfg, n
    pages = docs_pages()
    au = evsrc('evals/documentation-audit.eval.ts')
    assert 'it.for(pages)("$path matches the implementation"' in au and 'tools: ["read", "grep", "find", "ls", TOOL_NAME],' in au and '.toBe("match");' in au
    sm = evsrc('evals/smoke.eval.ts')
    assert 'createPiCodingAgentHarness({ noTools: "all" })' in sm and 'expect(result.output.trim()).toBe("Paris");' in sm
    judges = {}
    for fn, es, cs, k in S:
        s = evsrc('evals/' + fn)
        judges[fn] = ' + '.join(x for x in ['StructuredOutputJudge', 'ToolCallJudge'] if x + '(' in s) or ('createJudge' if 'createJudge<' in s else 'expect(…)')
    assert judges['tui.docs.eval.ts'] == 'createJudge' and judges['extensions.docs.eval.ts'] == 'StructuredOutputJudge + ToolCallJudge'
    for fn, es, cs, k in S:
        if k == 'docs': assert 'judgeThreshold: null' in evsrc('evals/' + fn) and '{ type: "reload" }' in evsrc('evals/' + fn), fn
    f = Fig('ev_suites', 1120, 570, (f'评测了什么：2 个 host 套件（含 {len(pages)} 页文档审计），5 个文档提升套件', f'What is evaluated: 2 host suites (including a {len(pages)}-page documentation audit) and 5 documentation-lift suites'))
    f.group(16, 52, 420, 400, 'modes', ('host 评测 · eval:host', 'Host evals · eval:host'), ('本机运行', 'on this machine'), 'monitor', title_mono=False, gid='h')
    hy = 112
    for fn, es, cs, k in [s for s in S if s[3] == 'host']:
        f.text(32, hy, fn, 9.8, 650, True, cls='strongt', layer='label')
        f.text(32, hy + 18, f'“{es}”', 9.0, 600, cls='strongt', layer='label')
        f.text(32, hy + 34, f'> {cs[0]}', 8.8, 450, True, cls='muted', layer='label')
        hy += 60
    f.text(32, hy + 6, ('smoke：没有工具；答案必须正好是 "Paris"，', 'smoke: no tools; the answer must be exactly "Paris",'), 8.8, 450, cls='muted', layer='label')
    f.text(32, hy + 22, ('且 usage 的 provider / model 与环境变量一致。', 'and usage must match PI_PROVIDER / PI_MODEL.'), 8.8, 450, cls='muted', layer='label')
    f.text(32, hy + 50, (f'documentation-audit：it.for 遍历 coding-agent/docs', f'documentation-audit: it.for over the {len(pages)} pages'), 8.8, 450, cls='muted', layer='label')
    f.text(32, hy + 66, (f'下的 {len(pages)} 页；只读工具 + 一个提交工具，', 'in coding-agent/docs; read-only tools plus a submit'), 8.8, 450, cls='muted', layer='label')
    f.text(32, hy + 82, ('verdict 必须是 "match"（mismatch / inconclusive', 'tool; the verdict must be "match" (mismatch /'), 8.8, 450, cls='muted', layer='label')
    f.text(32, hy + 98, ('都让用例失败）。', 'inconclusive fail the case).'), 8.8, 450, cls='muted', layer='label')
    chiprow(f, 32, hy + 116, ['read', 'grep', 'find', 'ls', 'submit_documentation_audit'], 'modes', size=8.6, h=18, gap=4)
    # docs
    f.group(452, 52, 652, 400, 'ext', ('文档提升评测 · eval:docs', 'Documentation-lift evals · eval:docs'), ('每个用例 × 两种镜像', 'each case × both images'), 'box', title_mono=False, gid='d')
    dy = 112
    for fn, es, cs, k in [s for s in S if s[3] == 'docs']:
        f.text(468, dy, es, 9.8, 650, cls='strongt', layer='label')
        f.chip(1088 - maxw(judges[fn], 8.6, 550, True) - 14, dy - 13, judges[fn], 'ext', size=8.6, h=17)
        f.text(468, dy + 17, f'> {cs[0]}', 8.8, 450, True, cls='muted', layer='label')
        f.text(468, dy + 33, fn, 8.4, 450, True, cls='faint', layer='label')
        dy += 58
    f.text(468, dy + 4, ('每个都是 [prompt, reload]：先让 Pi 改配置或写扩展，重载后再检查结果。', 'Each is [prompt, reload]: Pi changes its config or writes an extension, then reloads and is checked.'), 8.8, 450, cls='muted', layer='label')
    f.text(468, dy + 20, ('judgeThreshold: null：低分是数据，不是失败；分数参与配对比较。', 'judgeThreshold: null: a low score is data, not a failure; scores feed the paired comparison.'), 8.8, 450, cls='muted', layer='label')
    f.text(468, dy + 36, ('acme-server.ts 提供假的 OpenAI 兼容 / NDJSON 流式 API 供 provider 用例调用。', 'acme-server.ts serves fake OpenAI-compatible / NDJSON streaming APIs for the provider cases.'), 8.8, 450, cls='muted', layer='label')
    codebox(f, 16, 468, 1088, [(0, 'vitest.evals.config.ts · projects: docs = evals/**/*.docs.eval.ts · host = evals/**/*.eval.ts minus docs · testTimeout 300_000 · pool forks · maxWorkers 1 · fileParallelism false', 'muted')], None, size=9.0, lh=16)
    f.text(16, 520, ('createPiDocumentationEvalHarness() 在容器沙箱外直接抛错，所以 docs 评测只能经 eval:docs 运行。', 'createPiDocumentationEvalHarness() throws outside the container sandbox, so docs evals only run through eval:docs.'), 9.0, 450, cls='muted', layer='label')
    E_.has('harness.ts', 'throw new Error("Documentation evals must run in the isolated container sandbox.");')
    f.legend(24, 550, [('layer:modes', ('host 评测', 'host evals')), ('layer:ext', ('docs 评测（标签 = 评分器）', 'docs evals (tag = judge)'))])
    return f

# ============================================================== ev_pipeline : one eval:docs invocation
@reg
def ev_pipeline():
    c = E_.src('cli.ts')
    for n in ['const authPath = requireEvalAuthFile(selectedModel.provider);', 'const images = buildImages();', 'throw new Error("Documentation variants resolved to the same image.");',
              'compareDiscovery(discoveries[0], discoveries[1]);', 'const tasks = createTaskPlan(cases, modelIdentity, cli.runsPerVariant);',
              'const protocolDigest = createHash("sha256").update(protocolText).digest("hex");', '"expected-runs.json"', '"observations.jsonl"',
              ': erroredObservation(task);', 'if (report.blockedPairs.length > 0) process.exitCode = 1;', 'resolve(packageRoot, ".eval", artifactRunId())']:
        assert n in c, n
    doc('`protocol.json`: model, image IDs, cases, tasks, and protocol digest.', '`report.json` and `report.txt`: paired comparisons.', '`<variant>/sessions/*/session.jsonl`: native Pi sessions.')
    f = Fig('ev_pipeline', 1120, 600, ('一次 eval:docs：先把整个实验计划写下来，再逐个在新容器里运行', 'One eval:docs run: write down the whole experiment first, then run each arm in a fresh container'))
    E = f.edge
    ST = [('parseEvalCli', ('--provider --model · -t · 文件', '--provider --model · -t · files'), 'terminal'),
          ('requireEvalAuthFile', ('auth.json 里必须有该 provider', 'auth.json must hold the provider'), 'key'),
          ('buildImages', ('without_docs / with_docs，id 必须不同', 'without_docs / with_docs, ids must differ'), 'box'),
          ('discoverCases × 2', ('两种镜像里发现的用例必须完全相同', 'both images must discover identical cases'), 'filter')]
    ST2 = [('createTaskPlan', ('(case, variant, model, run) 全部任务', 'every (case, variant, model, run) task'), 'queue'),
           ('protocol.json', ('+ sha256 协议摘要 · expected-runs.json', '+ sha256 protocol digest · expected-runs.json'), 'file'),
           ('for task: runTask', ('docker run 一个全新容器 → vitest.json', 'docker run a fresh container → vitest.json'), 'play'),
           ('summarize + format', ('report.json / report.txt；有阻塞对 → 退出码 1', 'report.json / report.txt; blocked pairs → exit 1'), 'flag')]
    for i, (t, d, ic) in enumerate(ST):
        f.node(f'a{i}', 16 + i * 274, 72, 250, 58, 'infra', t, d, ic, tsize=10.4, ssize=8.4)
        f.step(str(i + 1), 16 + i * 274 + 12, 72, 'infra', onnode=True)
        if i: E([(16 + i * 274 - 24, 101), (16 + i * 274, 101)], f'a{i-1}', f'a{i}', 'main', 'infra')
    for i, (t, d, ic) in enumerate(ST2):
        x = 16 + (3 - i) * 274
        f.node(f'b{i}', x, 176, 250, 58, 'infra' if i != 2 else 'ext', t, d, ic, tsize=10.4, ssize=8.4, strong=(i == 2))
        f.step(str(i + 5), x + 12, 176, 'infra', onnode=True)
        if i: E([(x + 274, 205), (x + 250, 205)], f'b{i-1}', f'b{i}', 'main', 'infra')
    E([(963, 130), (963, 176)], 'a3', 'b0', 'main', 'infra')
    # per task detail
    f.group(16, 266, 1088, 150, 'ext', ('第 7 步，对每个任务', 'Step 7, for each task'), None, 'loop', title_mono=False, gid='pt')
    PT = [('runTask(docker, task)', ('--project docs 文件 --testNamePattern ^<集> <用例>$', '--project docs file --testNamePattern ^<set> <case>$')),
          (('有 vitest.json？', 'vitest.json?'), ('有 → readTaskObservation；没有 → erroredObservation', 'yes → readTaskObservation; no → erroredObservation')),
          ('observations.jsonl', ('每个任务之后整体重写：中途崩溃也留下已完成的观测', 'rewritten after every task: a crash keeps what finished')),
          (('失败不中断', 'Failures don\'t stop it'), ('失败或缺失的一侧被记下，计划内的其余任务照常继续', 'a failed or missing arm is recorded; the rest of the plan continues'))]
    for i, (a, b) in enumerate(PT):
        x = 32 + (i % 2) * 540; y = 314 + (i // 2) * 52
        f.text(x, y, a, 9.8, 650, isinstance(a, str), cls='strongt', layer='label')
        f.text(x, y + 18, b, 8.8, 450, cls='muted', layer='label')
    # artifacts
    f.group(16, 432, 1088, 104, 'infra', ('.eval/<时间戳>_<uuid>/（0700）', '.eval/<timestamp>_<uuid>/ (0700)'), None, 'db', title_mono=False, gid='ar')
    AR = ['protocol.json', 'expected-runs.json', 'discovery/<variant>/', 'tasks/<sha256>/vitest.json', 'observations.jsonl', '<variant>/sessions/<sha256>/session.jsonl', 'report.json', 'report.txt']
    x = 32; y = 478
    for a in AR:
        w = maxw(a, 8.8, 550, True) + 14
        if x + w > 1088: x = 32; y += 26
        f.chip(x, y, a, 'infra', size=8.8, h=19); x += w + 6
    f.text(16, 562, ('产物可能包含提示词、回答、生成的代码与工具输出；目录被 .gitignore 忽略。重复次数按运行序号交替顺序，减少顺序偏差。', 'Artifacts may contain prompts, responses, generated code and tool output; the directory is git-ignored. Repetitions alternate order by run number to reduce order bias.'), 9.0, 450, cls='muted', layer='label')
    f.legend(24, 586, [('step', ('步骤', 'step')), ('main', ('顺序', 'order')), ('layer:ext', ('容器里执行', 'runs in a container'))])
    return f

# ============================================================== ev_plan : createTaskPlan
@reg
def ev_plan():
    p = E_.src('plan.ts')
    for n in ['export const DOCUMENTATION_VARIANTS = ["without_docs", "with_docs"] as const;', 'item.name.split(" > ")', 'throw new TypeError(`Duplicate eval case identity: ${item.name}`);',
              'runNumber % 2 === 1 ? ["without_docs", "with_docs"] : ["with_docs", "without_docs"];', 'if (!model.includes("/") || model.startsWith("/") || model.endsWith("/")) {',
              'if (!Number.isSafeInteger(runsPerVariant) || runsPerVariant < 1) {']:
        assert n in p, n
    E_.has('docker.ts', 'const identity = JSON.stringify([task.evalSet, task.caseId, task.variant, task.model, task.runNumber]);', 'return createHash("sha256").update(identity).digest("hex");')
    # emulate createTaskPlan for 2 cases × 3 runs
    cases = [('Add model to existing provider', 'adds the model …'), ('Create and use a tool extension', 'creates, reloads …')]
    tasks = []
    for c in cases:
        for r in range(1, 4):
            for v in (['without_docs', 'with_docs'] if r % 2 == 1 else ['with_docs', 'without_docs']):
                tasks.append((c, r, v))
    assert len(tasks) == 12
    f = Fig('ev_plan', 1120, 560, ('createTaskPlan：用例 × 运行序号 × 两种变体；奇数次先跑 without_docs，偶数次反过来', 'createTaskPlan: case × run number × both variants; odd runs start with without_docs, even runs flip'))
    f.group(16, 52, 340, 420, 'infra', ('身份与校验', 'Identity and checks'), 'plan.ts', 'shield', gid='id')
    ID = [('parseDiscoveredCases', ('vitest list 的 JSON → 用例', 'vitest list JSON → cases')),
          ('"<eval set> > <case>"', ('全名必须恰好两段，否则报错', 'the full name must have exactly two parts')),
          (('身份不能重复', 'No duplicate identities'), ('JSON.stringify([evalSet, caseId])', 'JSON.stringify([evalSet, caseId])')),
          (('模型身份', 'Model identity'), ('"provider/model"：必须含 "/"，且不在两端', '"provider/model": must contain "/", not at either end')),
          ('runsPerVariant', ('正整数；默认 1 · --runs-per-variant · PI_EVAL_RUNS_PER_VARIANT', 'positive integer; default 1 · --runs-per-variant · PI_EVAL_RUNS_PER_VARIANT')),
          (('任务目录', 'Task directory'), ('sha256([set, case, variant, model, run])', 'sha256([set, case, variant, model, run])'))]
    for i, (a, b) in enumerate(ID):
        y = 112 + i * 58
        f.text(32, y, a, 9.8, 650, isinstance(a, str), cls='strongt', layer='label')
        f.text(32, y + 18, b, 8.4, 450, cls='muted', layer='label')
    f.group(372, 52, 732, 420, 'ext', ('例子：2 个用例，--runs-per-variant 3 → 12 个任务（按执行顺序）', 'Example: 2 cases, --runs-per-variant 3 → 12 tasks (in execution order)'), None, 'queue', title_mono=False, gid='ex')
    k = 0
    for ci, c in enumerate(cases):
        y0 = 112 + ci * 178
        f.text(388, y0, c[0], 9.8, 650, cls='strongt', layer='label')
        f.text(388, y0 + 16, f'> {c[1]}', 8.6, 450, True, cls='muted', layer='label')
        for r in range(1, 4):
            y = y0 + 30 + (r - 1) * 44
            f.text(388, y + 20, f'run {r}', 9.2, 600, True, cls='strongt', layer='label')
            for j in range(2):
                _, rr, v = tasks[k]; k += 1
                x = 448 + j * 316
                f.node(f't{k}', x, y, 300, 32, 'ext' if v == 'with_docs' else 'infra', f'#{k} · {v}', None, None, tsize=9.6, strong=(j == 0))
    f.text(16, 500, ('每个 (用例, 模型, 运行序号) 组成一对：without_docs 是对照组，with_docs 是实验组。所有任务在运行前就写进 expected-runs.json。', 'Each (case, model, run number) forms a pair: without_docs is the control and with_docs the treatment. Every task is written to expected-runs.json before anything runs.'), 9.0, 450, cls='muted', layer='label')
    f.legend(24, 536, [('layer:infra', ('without_docs（对照）', 'without_docs (control)')), ('layer:ext', ('with_docs（实验）', 'with_docs (treatment)'))])
    f.note(1096, 536, ('加粗 = 这一轮先跑的一侧', 'bold = the arm that runs first in its round'), 10.5, anchor='end')
    return f

# ============================================================== ev_docker : Dockerfile stages + docker run
@reg
def ev_docker():
    df = evsrc('docker/Dockerfile')
    for n in ['FROM node:24-slim AS builder', 'npm ci --ignore-scripts', 'npm run build:offline', 'node packages/evals/docker/install-runtime.mjs /opt/evaluator',
              'FROM builder AS without-docs-install', 'pi-coding-agent/README.md', 'pi-coding-agent/CHANGELOG.md', 'pi-coding-agent/docs', 'pi-coding-agent/examples',
              'FROM node:24-slim AS evaluator', 'COPY --from=builder /opt/evaluator/root /repo', 'RUN chmod -R go-rwx', 'ENTRYPOINT ["node", "--experimental-strip-types", "docker/entrypoint.ts"]',
              'FROM evaluator AS without_docs', 'COPY --from=without-docs-install /opt/evaluator/install/node_modules /repo/node_modules', 'ENV PI_EVAL_VARIANT=without_docs',
              'FROM evaluator AS with_docs', 'COPY --from=builder /opt/evaluator/install/node_modules /repo/node_modules', 'ENV PI_EVAL_VARIANT=with_docs']:
        assert n in df, n
    assert len(re.findall(r'^FROM ', df, re.M)) == 5
    ign = evsrc('docker/Dockerfile.dockerignore').split()
    assert ign == ['.git', '**/.eval', '**/node_modules', '**/dist', '**/coverage', '**/.env', '**/.env.*'], ign
    d = E_.src('docker.ts')
    for n in ['`pi-evals-${createHash("sha256").update(repositoryRoot).digest("hex").slice(0, 12)}`', '"--rm",', '"--read-only",', '"/tmp:rw,exec,mode=1777",', '"/repo/node_modules/.vite-temp:rw,exec,mode=1777",',
              '`type=bind,source=${outputDirectory},target=/artifacts`', 'environment("PI_EVAL_SANDBOX_UID", "65532")', 'environment("PI_EVAL_RUNS_PER_VARIANT", String(context.runsPerVariant))',
              'target=/run/pi-eval-secrets/auth.json,readonly`', '"image", "inspect", "--format", "{{.Id}}"', 'environment("PI_EVAL_ARTIFACT_UID"']:
        assert n in d, n
    E_.has('cli.ts', 'throw new Error("Documentation variants resolved to the same image.");')
    ir = evsrc('docker/install-runtime.mjs')
    assert 'installConsumer({ artifactSet, directory: installDirectory, packageNames: [codingAgentName] });' in ir and 'const runtimeRoot = join(outputDirectory, "root");' in ir
    f = Fig('ev_docker', 1120, 608, ('Dockerfile：一次构建，两个只差文档的目标；docker run 只读、一次一个任务', 'The Dockerfile: one build, two targets that differ only in docs; docker run is read-only, one task each'))
    E = f.edge
    f.group(16, 52, 840, 400, 'ext', 'docker/Dockerfile', ('5 个阶段 · 2 个构建目标', '5 stages · 2 build targets'), 'box', gid='df')
    f.node('bld', 72, 96, 360, 84, 'ext', 'builder', ('FROM node:24-slim · 挂载仓库 · npm ci --ignore-scripts', 'FROM node:24-slim · repo bind mount · npm ci --ignore-scripts'), 'layers', tsize=10.8, ssize=8.4,
           sub2=('build:offline → install-runtime.mjs /opt/evaluator', 'build:offline → install-runtime.mjs /opt/evaluator'))
    f.node('wdi', 480, 96, 360, 84, 'ext', 'without-docs-install', ('FROM builder', 'FROM builder'), 'filter', tsize=10.8, ssize=8.4,
           sub2=('删掉 coding-agent 的 README.md CHANGELOG.md docs/ examples/', 'rm coding-agent README.md CHANGELOG.md docs/ examples/'))
    f.node('evl', 72, 228, 360, 84, 'infra', 'evaluator', ('FROM node:24-slim · COPY builder 的 root → /repo', 'FROM node:24-slim · COPY builder root → /repo'), 'shield', tsize=10.8, ssize=8.4,
           sub2=('chmod go-rwx src evals docker · ENTRYPOINT entrypoint.ts', 'chmod go-rwx src evals docker · ENTRYPOINT entrypoint.ts'))
    f.node('twd', 72, 372, 360, 64, 'ext', 'with_docs', ('+ builder 的 node_modules · PI_EVAL_VARIANT=with_docs', '+ builder node_modules · PI_EVAL_VARIANT=with_docs'), None, tsize=10.8, ssize=8.4, strong=True)
    f.node('tnd', 480, 372, 360, 64, 'infra', 'without_docs', ('+ 去掉文档的 node_modules · PI_EVAL_VARIANT=without_docs', '+ docs-free node_modules · PI_EVAL_VARIANT=without_docs'), None, tsize=10.8, ssize=8.4, strong=True)
    E([(432, 138), (480, 138)], 'bld', 'wdi', 'main', 'ext', label='FROM', lpos=(456, 128), lsize=8.4)
    E([(252, 180), (252, 228)], 'bld', 'evl', 'main', 'infra', label='COPY root', lpos=(252, 204), lsize=8.4)
    E([(192, 312), (192, 372)], 'evl', 'twd', 'main', 'infra', label='FROM', lpos=(192, 342), lsize=8.4)
    E([(372, 312), (372, 342), (600, 342), (600, 372)], 'evl', 'tnd', 'main', 'infra', label='FROM', lpos=(486, 342), lsize=8.4)
    E([(760, 180), (760, 372)], 'wdi', 'tnd', 'dev', 'ext', label='node_modules', lpos=(760, 276), lsize=8.4)
    E([(100, 180), (100, 204), (44, 204), (44, 404), (72, 404)], 'bld', 'twd', 'dev', 'ext')
    # buildImages
    f.group(872, 52, 232, 400, 'infra', 'buildImages()', 'docker.ts', 'terminal', gid='bi')
    BI = [(('镜像名', 'Image name'), 'pi-evals-<hash>-<variant>:local'), (('hash', 'hash'), 'sha256(repoRoot)[:12]'),
          (('构建', 'Build'), 'docker build --target <variant>'), (('然后', 'Then'), 'docker image inspect → Id'),
          (('cli.ts', 'cli.ts'), ('两个 Id 相同 → 报错', 'equal Ids → error')), (('上下文排除', 'Context ignores'), '.git .eval node_modules'), (None, 'dist coverage .env .env.*')]
    y = 100
    for a, b in BI:
        if not a: y -= 14
        if a: f.text(888, y, a, 9.4, 650, isinstance(a, tuple) is False, cls='strongt', layer='label'); y += 17
        f.text(888, y, b, 8.4, 450, isinstance(b, str), cls='muted', layer='label'); y += 30 if a or True else 0
    f.text(888, 432, ('install-runtime.mjs 只把运行器需要的文件拷进 root/', 'install-runtime.mjs copies only runner files into root/'), 7.8, 450, cls='faint', layer='label')
    codebox(f, 16, 468, 1088, [
        (0, 'docker run --rm --read-only  --tmpfs /tmp:rw,exec,mode=1777  --tmpfs /repo/node_modules/.vite-temp:rw,exec,mode=1777', 'strongt'),
        (1, '--mount type=bind,source=<.eval/…/tasks/<sha256>>,target=/artifacts   --env PI_EVAL_ARTIFACT_DIR=/artifacts   --env PI_EVAL_RUNS_PER_VARIANT=<n>', 'muted'),
        (1, '--env PI_EVAL_SANDBOX_UID=65532  --env PI_EVAL_SANDBOX_GID=65532  --env PI_PROVIDER  --env PI_MODEL  [--env PI_EVAL_ARTIFACT_UID/GID = host user]', 'muted'),
        (1, '--mount type=bind,source=<auth.json>,target=/run/pi-eval-secrets/auth.json,readonly   <image>   <entrypoint args>', 'muted')],
        ('docker.ts · 每个任务一次', 'docker.ts · once per task'), size=9.0, lh=16)
    f.legend(24, 592, [('main', ('FROM / COPY 阶段', 'FROM / COPY stage')), ('dev', ('COPY node_modules', 'COPY node_modules')), ('layer:ext', ('带文档', 'with docs')), ('layer:infra', ('无文档 / 评测器', 'no docs / evaluator'))])
    return f

# ============================================================== ev_sandbox : three nested guards
@reg
def ev_sandbox():
    ep = evsrc('docker/entrypoint.ts')
    for n in ['assertDirectoryEntries("/repo", ["node_modules", "package.json", "packages", "vitest.base.ts"]);', '["docs", "examples", "src", "test", "tests"].includes(entry.name)',
              'throw new Error(`without_docs contains coding-agent ${name}.`);', 'join(codingAgentDir, "docs/models.md"),', 'assertRootOnly(path);', 'assertSandboxCannotRead(path);',
              'if (codingAgentEntry !== "/repo/node_modules/@earendil-works/pi-coding-agent/dist/index.js") {', 'const agentDir = "/tmp/pi-eval-host-agent";', 'chownTree(agentDir, sandboxUid, sandboxGid);',
              'process.env.PI_EVAL_CONTAINER = "1";', 'throw new Error("The container runner requires an explicit eval file.");']:
        assert n in ep, n
    h = E_.src('harness.ts')
    for n in ['const root = await mkdtemp(join(tmpdir(), "pi-eval-"));', 'if (!name.startsWith("PI_EVAL_")) continue;', 'const credentials = new InMemoryCredentialStore();',
              'await rm(authPath, { force: true });', 'delete process.env[auth.source];', 'throw new Error(`Isolated eval loaded unexpected extensions: ${unexpectedExtensions.join(", ")}`);',
              'await chmod(path, 0o600);', 'process.setgroups([]);', 'process.setgid(identity.gid);', 'process.setuid(identity.uid);',
              'throw new Error(`The unprivileged eval process can read a transformed eval module: ${path}`);', 'export const DOCUMENTATION_EVAL_TOOLS = ["read", "write", "edit", "grep", "find", "ls"] as const;']:
        assert n in h, n
    doc('Provider traffic still requires container network access, so Docker alone cannot prove that arbitrary code written by an agent never uses the network.')
    f = Fig('ev_sandbox', 1120, 612, ('三层防护：容器只读 → 入口脚本以 root 自检 → 测试框架降权到 UID 65532 后才让模型用工具', 'Three guards: a read-only container → the entrypoint self-checks as root → the harness drops to UID 65532 before the model gets tools'))
    E = f.edge
    G = [('dr', 16, 'ext', 'docker run', ('宿主 → 容器', 'host → container'), 'box', [
            (('只读根文件系统', 'Read-only root filesystem'), ('--read-only；可写的只有两个 tmpfs', '--read-only; only two tmpfs mounts are writable')),
            (('每个任务一个新容器', 'A fresh container per task'), ('--rm：上一个任务的痕迹不会留下', '--rm: nothing carries over between tasks')),
            ('/artifacts', ('绑定到 .eval/…/tasks/<sha256>', 'bound to .eval/…/tasks/<sha256>')),
            ('/run/pi-eval-secrets/auth.json', ('只读挂载；目录在镜像里是 0700', 'read-only mount; the directory is 0700 in the image')),
            (('源码 root 专属', 'Root-only sources'), ('镜像构建时 chmod go-rwx src evals docker', 'chmod go-rwx src evals docker at build time')),
            ('PI_EVAL_SANDBOX_UID/GID', ('= 65532，交给后面两层', '= 65532, handed to the next two layers'))]),
         ('en', 388, 'infra', 'entrypoint.ts', ('以 root 运行', 'runs as root'), 'shield', [
            (('/repo 内容完全符合清单', '/repo matches an exact allowlist'), ('node_modules · package.json · packages · vitest.base.ts', 'node_modules · package.json · packages · vitest.base.ts')),
            (('内部依赖不带文档', 'Internal deps carry no docs'), ('无 docs/ examples/ src/ test/ README CHANGELOG', 'no docs/ examples/ src/ test/ README CHANGELOG')),
            (('变体与文档一致', 'Variant matches its docs'), ('without_docs 必须没有；with_docs 必须有 docs/models.md', 'without_docs: none; with_docs: docs/models.md exists')),
            (('评测源码：root 专属 + 探测', 'Eval sources: root-only + probe'), ('以 65532 身份尝试读取，必须失败', 'a read attempted as 65532 must fail')),
            (('coding-agent 来自 dist', 'coding-agent resolves from dist'), ('…/pi-coding-agent/dist/index.js', '…/pi-coding-agent/dist/index.js')),
            (('凭据交给沙箱用户', 'Credentials handed over'), ('auth.json → /tmp/pi-eval-host-agent，chown 65532', 'auth.json → /tmp/pi-eval-host-agent, chown 65532')),
            (('只跑指定的评测文件', 'Only an explicit eval file'), ('PI_EVAL_CONTAINER=1 · vitest run / list', 'PI_EVAL_CONTAINER=1 · vitest run / list'))]),
         ('hn', 760, 'coding', 'runPiCodingAgent', ('harness.ts · 每个用例', 'harness.ts · each case'), 'cpu', [
            ('mkdtemp pi-eval-*', ('workspace/ · home/ · sessions/', 'workspace/ · home/ · sessions/')),
            ('applyIsolatedEnvironment', ('HOME / PI_CODING_AGENT_DIR 指向临时目录；清掉 PI_EVAL_*', 'HOME / PI_CODING_AGENT_DIR → temp dir; PI_EVAL_* removed')),
            ('InMemoryCredentialStore', ('凭据只在内存里；随后删除 auth.json', 'credential in memory only; auth.json is then deleted')),
            (('隐藏凭据环境变量', 'Credential env var hidden'), ('运行期间 delete，结束后恢复', 'deleted for the run, restored afterwards')),
            (('不许有意外扩展', 'No unexpected extensions'), ('只允许 <inline:…> 的隐藏扩展', 'only hidden <inline:…> extensions')),
            ('enterToolSandbox', ('转换后的模块 0600；setgroups([]) → setgid → setuid', 'transformed modules 0600; setgroups([]) → setgid → setuid')),
            (('确认读不到', 'Confirm it cannot read'), ('读到任何受保护模块 → 报错', 'any readable protected module → error'))])]
    for gid, x, layer, t, sub, ic, items in G:
        f.group(x, 52, 344, 360, layer, t, sub, ic, gid=gid)
        for i, (a, b) in enumerate(items):
            y = 108 + i * 42
            f.text(x + 16, y, a, 9.4, 650, isinstance(a, str), cls='strongt', layer='label')
            f.text(x + 16, y + 16, b, 8.2, 450, cls='muted', layer='label')
    E([(360, 232), (388, 232)], 'dr', 'en', 'main', 'infra')
    E([(732, 232), (760, 232)], 'en', 'hn', 'main', 'coding')
    f.group(16, 428, 1088, 112, 'modes', ('模型的工具以 UID 65532 运行', "The model's tools run as UID 65532"), ('read · write · edit · grep · find · ls；没有 shell、没有联网搜索', 'read · write · edit · grep · find · ls; no shell, no web search'), 'user', title_mono=False, gid='md')
    f.text(32, 488, ('看得到', 'can see'), 9.2, 650, cls='faint', layer='label')
    chiprow(f, 120, 476, ['workspace/ (rw)', 'isolated home/', 'pi-coding-agent dist', 'README · docs/ · examples/ (with_docs)'], 'modes', size=8.8, h=19, gap=6)
    f.text(32, 518, ('看不到', 'cannot see'), 9.2, 650, cls='faint', layer='label')
    chiprow(f, 120, 506, ['src/', 'evals/ (judges, fixtures)', 'docker/', 'vitest configs', 'auth.json', 'credential env var', 'other packages\' docs'], 'err', size=8.8, h=19, gap=6)
    f.text(16, 564, ('README 坦白说明：调用 provider 仍需要容器联网，所以单靠 Docker 不能证明模型写的代码从不联网。', 'The README is explicit: provider traffic still needs container network access, so Docker alone cannot prove agent-written code never uses the network.'), 9.0, 450, cls='muted', layer='label')
    f.legend(24, 594, [('main', ('下一层', 'next layer')), ('layer:ext', ('容器', 'container')), ('layer:infra', ('入口（root）', 'entrypoint (root)')), ('layer:coding', ('测试框架', 'harness'))])
    return f

# ============================================================== ev_harness : one case through runPiCodingAgent
@reg
def ev_harness():
    h = E_.src('harness.ts')
    for n in ['const selection = resolveModelSelection(options.model);', 'const modelRuntime = await ModelRuntime.create({ credentials });', 'throw new Error(`Eval model has no configured authentication: ${selection.provider}/${selection.id}`);',
              'resourceLoaderOptions: { extensionFactories },', 'sessionManager = SessionManager.create(workspace, join(root, "sessions"));', 'thinkingLevel: "off",',
              'await enterToolSandbox(root, sandboxIdentity);', 'if (step.type === "reload") {', 'await session.reload();', 'response = await promptAgent(session, step.content, signal);',
              'metadata: { systemPromptSha256: createHash("sha256").update(systemPrompt).digest("hex") },', '...(hasPricing ? { estimatedCostUsd: stats.cost } : {}),',
              'verifySystemPrompt(systemPrompt, options);', '"output" in options ? await options.output({ response, session, systemPrompt, agentDir }) : response;',
              'setArtifact(PI_SESSION_SNAPSHOT_ARTIFACT, await readFile(sessionPath, "utf8"));', 'await rm(root, { recursive: true, force: true });', 'restoreEnvironment();',
              'throw attachHarnessRunToError(failure, partialRun);', 'new AggregateError([runError, ...cleanupErrors], "Agent run failed and cleanup also failed.");',
              'if (assistant.stopReason !== "stop" && assistant.stopReason !== "toolUse") {', 'throw new Error("Agent run produced no assistant text.");', 'return output ?? "";',
              'throw new Error("Documentation evals must run in the isolated container sandbox.");', 'name: variant,', 'tools: options.tools ?? [...DOCUMENTATION_EVAL_TOOLS],',
              '...(variant === "without_docs" ? { transformSystemPrompt: excludePiDocumentation } : {}),', 'expectedPiDocumentation: variant === "with_docs",',
              'if (cwdStart < documentationEnd) throw new Error("Default Pi system prompt has no working-directory section.");']:
        assert n in h, n
    sp = (SRC / 'packages/coding-agent/src/core/system-prompt.ts').read_text()
    order = [sp.index(f'promptSections.{k} =') for k in ['preamble', 'tools', 'rules', 'docs', 'cwd']]
    assert order == sorted(order), order
    assert 'sections[name] = `<${name}>\\n${content}\\n</${name}>`;' in sp
    f = Fig('ev_harness', 1120, 660, ('一个用例的一次运行：真实的 AgentSession，跑完就拆；两种变体只差系统提示词里的 <docs>', 'One run of one case: a real AgentSession, torn down afterwards; the two variants differ only in the <docs> of the system prompt'))
    E = f.edge
    f.group(16, 52, 640, 470, 'coding', 'runPiCodingAgent(input, signal, setArtifact, options)', None, 'cpu', gid='rp')
    ST = [('resolveModelSelection · mkdtemp', ('provider/model；root/ 下 workspace、home、sessions（见 ev_sandbox）', 'provider/model; workspace, home, sessions under root/ (see ev_sandbox)')),
          ('ModelRuntime.create({ credentials })', ('getModel → getAuth；没有认证就直接报错', 'getModel → getAuth; no auth → error')),
          ('createAgentSessionServices', ('cwd = workspace · extensionFactories（隐藏的提示词变换）', 'cwd = workspace · extensionFactories (hidden prompt transform)')),
          ('createAgentSessionFromServices', ('thinkingLevel "off" · tools / noTools / customTools', 'thinkingLevel "off" · tools / noTools / customTools')),
          ('enterToolSandbox → for step of input', ('prompt → promptAgent；reload → session.reload()', 'prompt → promptAgent; reload → session.reload()')),
          (('诊断数据', 'Diagnostics'), ('转录事件 · systemPromptSha256 · tokens / toolCalls · 有定价才算 cost', 'transcript events · systemPromptSha256 · tokens / toolCalls · cost only if priced')),
          ('verifySystemPrompt → output()', ('有 output 选项就交给它（评分器用），否则就是回答文本', 'an output option shapes the result for judges; otherwise the response text')),
          ('finally', ('session.jsonl → PI_SESSION_SNAPSHOT_ARTIFACT · dispose · rm root · 还原环境', 'session.jsonl → PI_SESSION_SNAPSHOT_ARTIFACT · dispose · rm root · restore env'))]
    for i, (t, d) in enumerate(ST):
        y = 96 + i * 52
        f.node(f's{i}', 64, y, 576, 38, 'coding' if i != 7 else 'infra', t, d, None, tsize=9.8, ssize=8.2, mono=isinstance(t, str), strong=(i == 4))
        f.step(str(i + 1), 44, y + 19, 'coding')
        if i: E([(352, y - 14), (352, y)], f's{i-1}', f's{i}', 'main', 'coding')
    # promptAgent
    f.group(672, 52, 432, 140, 'coding', 'promptAgent', ('每个 prompt 步骤', 'each prompt step'), 'msg', gid='pa')
    PA = [('stopReason ∈ { stop, toolUse }', ('否则抛出 errorMessage 或 "unexpected stop reason"', 'otherwise throw errorMessage or "unexpected stop reason"')),
          ('stop && !text → error', ('"Agent run produced no assistant text."', '"Agent run produced no assistant text."')),
          ('getLastAssistantText() ?? ""', ('最后一个 prompt 的回答就是 response', 'the last prompt\'s answer becomes the response'))]
    for i, (a, b) in enumerate(PA):
        y = 110 + i * 28
        f.text(688, y, a, 9.2, 650, True, cls='strongt', layer='label'); f.text(688, y + 14, b, 8.2, 450, cls='muted', layer='label')
    # documentation harness
    f.group(672, 208, 432, 200, 'ext', 'createPiDocumentationEvalHarness', None, 'box', gid='dh', title_mono=True)
    f.text(688, 248, ('须 PI_EVAL_CONTAINER=1 且有沙箱 UID/GID，否则直接报错', 'needs PI_EVAL_CONTAINER=1 and a sandbox UID/GID, or it throws'), 8.4, 450, cls='faint', layer='label')
    f.text(820, 274, 'without_docs', 9.2, 650, True, cls='strongt', layer='label')
    f.text(962, 274, 'with_docs', 9.2, 650, True, cls='strongt', layer='label')
    hline(f, 688, 1088, 283)
    ROWS = [('name', 'without_docs', 'with_docs'), ('tools', 'read…ls (6)', 'read…ls (6)'), ('transform', 'excludePiDocumentation', '—'), ('expect <docs>', 'false', 'true')]
    for i, (a, b, c) in enumerate(ROWS):
        y = 304 + i * 24
        f.text(688, y, a, 8.8, 600, True, cls='faint', layer='label'); f.text(820, y, b, 8.6, 450, True, cls='muted', layer='label'); f.text(962, y, c, 8.6, 450, True, cls='muted', layer='label')
    f.text(688, 398, ('两种变体共用同一个用例定义和同一个评分器。', 'Both variants share one case definition and one judge.'), 8.4, 450, cls='faint', layer='label')
    # failure
    f.group(672, 424, 432, 98, 'err', ('失败时', 'On failure'), None, 'x', title_mono=False, gid='fl')
    f.text(688, 472, ('已有诊断 → attachHarnessRunToError：带 errors 与耗时的部分结果', 'diagnostics exist → attachHarnessRunToError: a partial run with errors + timings'), 8.4, 450, cls='muted', layer='label')
    f.text(688, 490, ('运行与清理都失败 → AggregateError', 'run and cleanup both fail → AggregateError'), 8.4, 450, cls='muted', layer='label')
    f.text(688, 508, ('报告据此把这一侧记为 errored', 'the report then records that arm as errored'), 8.4, 450, cls='muted', layer='label')
    # system prompt strip
    f.text(16, 552, ('系统提示词的分段（coding-agent 的 system-prompt.ts）', 'System prompt sections (coding-agent system-prompt.ts)'), 9.4, 650, cls='strongt', layer='label')
    f.text(16, 580, 'with_docs', 9.0, 600, True, cls='faint', layer='label')
    chiprow(f, 110, 568, [('preamble', 'infra'), ('<tools>', 'infra'), ('<rules>', 'infra'), ('<docs> Pi documentation (read only …', 'ext'), ('…', 'infra'), ('<cwd>', 'infra')], size=8.8, h=19, gap=6)
    f.text(16, 606, 'without_docs', 9.0, 600, True, cls='faint', layer='label')
    chiprow(f, 110, 594, [('preamble', 'infra'), ('<tools>', 'infra'), ('<rules>', 'infra'), ('…', 'infra'), ('<cwd>', 'infra')], size=8.8, h=19, gap=6)
    f.text(560, 606, ('excludePiDocumentation 剪掉 <docs>…</docs>；verifySystemPrompt 要求 <rules> 还在、<docs> 有无与变体一致', 'excludePiDocumentation cuts <docs>…</docs>; verifySystemPrompt requires <rules> and a <docs> matching the variant'), 8.4, 450, cls='muted', layer='label')
    f.legend(24, 644, [('step', ('步骤', 'step')), ('main', ('顺序', 'order')), ('layer:ext', ('只在 with_docs', 'with_docs only'))])
    return f

# ============================================================== ev_report : observations → pairs → comparison → report.txt
def report_example():
    """Re-implements summarizeEvalObservations + formatEvalComparisonReport (report.ts) on a small illustrative data set."""
    M = 'provider/model'
    S = {s[1]: s[2][0] for s in suites()}
    A, B = 'Add model to existing provider', 'Create and use a tool extension'
    # (set, run, variant, outcome, score, tokens, tools, ms, cost)
    obs = []
    def add(st, v, outs, tok, tl, ms, cost):
        for r in range(3):
            o = outs[r]
            obs.append(dict(set=st, case=S[st], run=r + 1, variant=v, outcome='scored' if o is not None else 'errored', score=o, tok=tok[r], tools=tl[r], ms=ms[r], cost=cost[r]))
    add(A, 'without_docs', [1, 0, 1], [18400, 21050, 17920], [9, 12, 8], [41200, 52800, 39900], [.0412, .0475, .0401])
    add(A, 'with_docs', [1, 1, 1], [15210, 16030, 14880], [5, 6, 5], [30100, 33400, 29800], [.0350, .0368, .0342])
    add(B, 'without_docs', [0, 1, 1], [30500, 28800, 29900], [14, 13, 15], [70100, 66300, 68800], [.0690, .0651, .0672])
    add(B, 'with_docs', [1, None, 1], [24100, 26400, 23500], [9, 11, 8], [55200, 61000, 54000], [.0544, .0590, .0531])
    def fx(v, d):  # JS toFixed for these non-tie values
        return f'{v:.{d}f}'
    def signed(v, d): return ('+' if v >= 0 else '') + fx(v, d)
    def pct(v): return f'{fx(v * 100, 1)}%'
    out = [('Documentation Eval Comparisons', 'strongt')]
    blocked = []
    for st in sorted({o['set'] for o in obs}):
        pairs = []
        for r in (1, 2, 3):
            c = next(o for o in obs if o['set'] == st and o['run'] == r and o['variant'] == 'without_docs')
            t = next(o for o in obs if o['set'] == st and o['run'] == r and o['variant'] == 'with_docs')
            rs = [f"{o['variant']}: {o['outcome']}" for o in (c, t) if o['outcome'] != 'scored']
            if rs: blocked.append((st, c['case'], r, rs))
            else: pairs.append((c, t))
        total = 3; head = len(pairs) == total
        out.append((f'  {st}', 'strongt'))
        out.append(f'         Pairs  {len(pairs)}/{total} eligible')
        flags = []
        if head:
            cr = sum(c['score'] >= 1 for c, _ in pairs) / len(pairs); tr = sum(t['score'] >= 1 for _, t in pairs) / len(pairs)
            out.append(f'     Pass rate  {signed(float(f"{tr - cr:.15g}") * 100, 1)} pp (with {pct(tr)}, without {pct(cr)})')
            if cr == tr: flags.append('no-lift')
            if tr < cr: flags.append('negative-delta')
            if cr == 1: flags.append('control-saturated')
            if tr == 1: flags.append('treatment-saturated')
        else:
            out.append('     Pass rate  withheld because pairs are blocked')
        if len({c['score'] >= 1 for c, _ in pairs}) > 1 or len({t['score'] >= 1 for _, t in pairs}) > 1: flags.append('flaky')
        if flags: out.append(f'         Flags  {", ".join(flags)}')
        n = len(pairs)
        for lab, k, unit in [('Tokens', 'tok', ''), ('Tools', 'tools', ''), ('Latency', 'ms', 'ms')]:
            cm = sum(c[k] for c, _ in pairs) / n; tm = sum(t[k] for _, t in pairs) / n
            out.append(f'    {lab:>10}  {signed(tm - cm, 1)}{unit} (with {fx(tm, 1)}{unit}, without {fx(cm, 1)}{unit}, {n} pairs)')
        cm = sum(c['cost'] for c, _ in pairs) / n; tm = sum(t['cost'] for _, t in pairs) / n; d = tm - cm
        out.append(f'     Est. cost  {"+" if d >= 0 else "-"}${fx(abs(d), 4)} (with ${fx(tm, 4)}, without ${fx(cm, 4)}, {n} pairs)')
    out.append(('  Operational totals', 'strongt'))
    for v in ('without_docs', 'with_docs'):
        rs = [o for o in obs if o['variant'] == v]
        out.append(f"    {v}: {len(rs)} runs, {sum(o['tok'] for o in rs)} tokens, {sum(o['tools'] for o in rs)} tools, {fx(sum(o['ms'] for o in rs) / 1000, 2)}s, ${fx(sum(o['cost'] for o in rs), 4)} cost")
    out.append(('  Blocked pairs', 'strongt'))
    for st, case, r, rs in blocked:
        out.append(f'    {st}/{case}/')
        out.append(f'      {M}/run-{r}: {"; ".join(rs)}')
    return out

@reg
def ev_report():
    r = E_.src('report.ts')
    for n in ['if (status === "failed") return "errored";', 'if (status === "skipped" || status === "todo" || status === "disabled") return "skipped";', 'if (assertions.length !== 1) return { ...identity, outcome: "errored" };',
              'if (actualModel !== task.model) return { ...identity, outcome: "errored" };', 'if (statusOutcome === "errored" || run.errors.length > 0) {', 'if (score === undefined) return { ...identity, ...metrics, outcome: "unscored" };',
              'return { ...identity, ...metrics, outcome: "scored", score };', 'if (expected !== 1) reasons.push(`${variant}: design expected 1 run, found ${expected}`);',
              '`${variant}: expected ${expected} observation${expected === 1 ? "" : "s"}, found ${observed.length}`,', 'reasons.push(`${variant}: ${observed[0].outcome}`);',
              'const publishHeadline = blockedPairCount === 0 && pairs.length > 0;', 'pairs.filter(({ control }) => control.score >= 1).length / pairs.length', 'return Number((treatment - control).toPrecision(15));',
              'if (controlPassRate === treatmentPassRate) flags.push("no-lift");', 'if (treatmentPassRate < controlPassRate) flags.push("negative-delta");', 'if (controlPassRate === 1) flags.push("control-saturated");',
              'if (treatmentPassRate === 1) flags.push("treatment-saturated");', 'if ([...outcomes.values()].some((values) => values.size > 1)) flags.push("flaky");', 'schemaVersion: 3,',
              '"     Pass rate  withheld because pairs are blocked"', 'lines.push("  Operational totals");', 'lines.push("  Blocked pairs");', 'lines.push(`         Pairs  ${comparison.eligiblePairs}/${comparison.totalPairs} eligible`);',
              'return `    ${label.padStart(10)}  ${signed(metric.meanDelta, 1)}${unit} (with ${metric.treatmentMean.toFixed(1)}${unit}, without ${metric.controlMean.toFixed(1)}${unit}, ${metric.eligiblePairs} pairs)`;']:
        assert n in r, n
    f = Fig('ev_report', 1120, 668, ('报告：先判定每一侧的结果，再成对比较；只要有一对不完整，就不公布通过率', 'The report: classify each arm, then compare in pairs; if any pair is incomplete, no pass rate is published'))
    E = f.edge
    f.group(16, 52, 340, 270, 'infra', 'readTaskObservation', ('每个任务一个结果', 'one outcome per task'), 'eye', gid='ob')
    OB = [(('vitest.json 读不了', 'vitest.json unreadable'), 'errored'), (('断言不是恰好 1 条 / 名字不符', 'not exactly 1 assertion / name mismatch'), 'errored'),
          (('skipped · todo · disabled · pending', 'skipped · todo · disabled · pending'), 'skipped / pending'), (('没有 harness 运行 / 模型不符', 'no harness run / wrong model'), 'errored'),
          (('failed 或运行里有错误', 'failed, or run has errors'), 'errored'), (('没有分数', 'no score'), 'unscored'), (('有分数（0 也算）', 'a score (0 counts)'), 'scored')]
    for i, (a, o) in enumerate(OB):
        y = 104 + i * 30
        f.text(32, y + 13, a, 8.6, 450, cls='muted', layer='label')
        f.chip(340 - maxw(o, 8.6, 550, True) - 14, y, o, 'modes' if o == 'scored' else ('infra' if o == 'unscored' or '/' in o else 'err'), size=8.6, h=18)
    f.group(372, 52, 340, 270, 'ext', 'resolvePair', ('(集, 用例, 模型, 运行序号)', '(set, case, model, run)'), 'branch', gid='pr')
    PR = [(('每一侧在计划里恰好 1 次', 'each arm planned exactly once'), 'design expected 1 run, found N'), (('观测数 = 计划数', 'observations = planned'), 'expected 1 observation, found N'),
          (('结果是 scored', 'outcome is scored'), '<variant>: <outcome>')]
    for i, (a, b) in enumerate(PR):
        y = 108 + i * 46
        f.text(388, y, a, 9.4, 650, cls='strongt', layer='label'); f.text(388, y + 16, b, 8.4, 450, True, cls='err', layer='label')
    f.text(388, 254, ('全部满足 → Pair { control, treatment }', 'all hold → Pair { control, treatment }'), 9.0, 600, cls='strongt', layer='label')
    f.text(388, 274, ('否则 → BlockedPair，带上面的原因（红色）', 'otherwise → BlockedPair with the reasons above (red)'), 8.6, 450, cls='muted', layer='label')
    f.text(388, 300, ('without_docs = 对照 · with_docs = 实验', 'without_docs = control · with_docs = treatment'), 8.4, 450, cls='faint', layer='label')
    f.group(728, 52, 376, 270, 'modes', ('每个评测集的比较', 'Comparison per eval set'), 'summarize…', 'flag', title_mono=False, gid='cm')
    CM = [(('通过', 'Pass'), 'score ≥ 1'), (('通过率', 'Pass rate'), 'passes / eligible pairs'), (('提升', 'Lift'), 'treatment − control (toPrecision 15)'), (('不公布', 'Withheld'), ('任何一对被阻塞时', 'if any pair is blocked'))]
    for i, (a, b) in enumerate(CM):
        y = 104 + i * 22
        f.text(744, y, a, 9.0, 650, cls='strongt', layer='label'); f.text(830, y, b, 8.6, 450, isinstance(b, str), cls='muted', layer='label')
    hline(f, 744, 1088, 186)
    FL = [('no-lift', ('两组通过率相同', 'equal pass rates')), ('negative-delta', ('实验组更低', 'treatment is lower')), ('control-saturated', ('对照组 100%', 'control at 100%')),
          ('treatment-saturated', ('实验组 100%', 'treatment at 100%')), ('flaky', ('同一用例同一侧跨运行结果不同', 'same case + arm passes in some runs only'))]
    for i, (a, b) in enumerate(FL):
        y = 206 + i * 20
        f.text(744, y, a, 8.6, 600, True, cls='strongt', layer='label'); f.text(894, y, b, 8.4, 450, cls='muted', layer='label')
    f.text(744, 310, ('另有 tokens / tools / latency / cost 的配对均值差', 'plus paired mean deltas for tokens / tools / latency / cost'), 8.2, 450, cls='faint', layer='label')
    E([(356, 187), (372, 187)], 'ob', 'pr', 'main', 'infra')
    E([(712, 187), (728, 187)], 'pr', 'cm', 'main', 'ext')
    # report.txt
    L = report_example()
    split = next(i for i, l in enumerate(L) if isinstance(l, tuple) and l[0].startswith('  Create'))
    nb = lambda t: t.replace(' ', '\u00a0')  # keep report.ts column alignment (SVG collapses spaces)
    def cb(lines): return [(0, nb(l[0]), l[1]) if isinstance(l, tuple) else (0, nb(l), 'muted') for l in lines]
    f.group(16, 340, 1088, 268, 'infra', ('formatEvalComparisonReport → report.txt', 'formatEvalComparisonReport → report.txt'), ('示例数据：2 个评测集 × 3 次运行，第二个集里有一侧出错', 'illustrative data: 2 eval sets × 3 runs, one arm errored in the second set'), 'file', title_mono=True, gid='rt')
    E([(916, 322), (916, 340)], 'cm', 'rt', 'main', 'modes')
    codebox(f, 32, 384, 528, cb(L[:split]), None, size=8.4, lh=14)
    codebox(f, 568, 384, 520, cb(L[split:]), None, size=8.4, lh=14)
    f.text(16, 632, ('通过率、提升与标记按 report.ts 的规则从示例数据算出（构建时计算）。有阻塞对时 eval:docs 退出码为 1；report.json 是 schemaVersion 3。', 'Pass rates, lift and flags are computed from the example data with the report.ts rules at build time. With blocked pairs eval:docs exits 1; report.json is schemaVersion 3.'), 8.8, 450, cls='muted', layer='label')
    f.legend(24, 656, [('main', ('数据流', 'data flow')), ('layer:modes', ('scored', 'scored')), ('layer:err', ('阻塞 / 出错', 'blocked / errored'))])
    return f
