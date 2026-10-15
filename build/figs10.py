"""pi-durable deep-dive diagrams (dur_*). Facts read from /workspace/pi-src/packages/durable at build time."""
import re
from svgkit import Fig, maxw, pair
from figs import reg
from figkit import SRC, uml, codebox, bar, dot, hline, vline, chiprow, lines_of
from pkgsrc import Pkg, users_of

D = Pkg('packages/durable/src/')
README = (SRC / 'packages/durable/README.md').read_text()

def readme(*needles):
    for n in needles: assert n in README, n

# ============================================================== dur_arch
@reg
def dur_arch():
    ex = D.exports(); deps = D.pkg()['dependencies']
    assert len(ex) == 11, ex
    f = Fig('dur_arch', 1120, 666, (f'pi-durable 模块结构（{D.total():,} 行 TypeScript）', f'pi-durable modules ({D.total():,} lines of TypeScript)'))
    root_files = ['types.ts', 'documents.ts', 'entries.ts', 'tasks.ts', 'errors.ts', 'truncate.ts', 'ids.ts', 'index.ts']
    root_tot = sum(D.loc(p) for p in root_files)
    COLS = [('', ('核心类型', 'Core types'), 'infra', 'braces', root_tot, [
                ('types.ts', ('Storage · TaskState · 记录', 'Storage · TaskState · records')), ('documents.ts', ('defineDoc', 'defineDoc')),
                ('entries.ts', ('pi.user … pi.compaction', 'pi.user … pi.compaction')), ('tasks.ts', ('defineTask', 'defineTask'))]),
            ('session/', ('Session', 'Session'), 'agent', 'db', D.total('session/'), [
                ('session/transaction.ts', ('一次原子提交', 'one atomic commit')), ('session/session.ts', ('唯一的提交线', 'the single commit line')),
                ('session/observation.ts', ('view · watch', 'view · watch'))]),
            ('harness/', ('Harness', 'Harness'), 'coding', 'cpu', D.total('harness/'), [
                ('harness/scheduler.ts', ('任务调度与恢复', 'task scheduling & recovery')), ('harness/generation.ts', ('pi.generation 任务', 'the pi.generation task')),
                ('harness/tool.ts', ('pi.tool 任务', 'the pi.tool task')), ('harness/compaction.ts', ('pi.compaction 任务', 'the pi.compaction task')),
                ('harness/harness.ts', ('Harness.open() · root()', 'Harness.open() · root()')), ('harness/events.ts', ('watchEvents()', 'watchEvents()'))]),
            ('storage/', ('存储后端', 'Storage backends'), 'ext', 'stack', D.total('storage/'), [
                ('storage/sqlite/storage.ts', ('SQLite 核心', 'SQLite core')), ('storage/jsonl/storage.ts', ('JSONL 核心', 'JSONL core')),
                ('storage/memory.ts', ('MemoryStorage', 'MemoryStorage'))]),
            ('env/', ('执行环境', 'Execution env'), 'modes', 'terminal', D.total('env/'), [
                ('env/index.ts', ('ExecutionEnv 接口', 'the ExecutionEnv interface')), ('env/node.ts', ('NodeExecutionEnv', 'NodeExecutionEnv')),
                ('env/node-watch.ts', ('文件监视', 'file watching'))]),
            ('tools/', ('内置工具', 'Built-in tools'), 'tui', 'tool', D.total('tools/'), [
                ('tools/edit-diff.ts', ('edit 的匹配与差异', 'edit matching & diffs')), ('tools/read.ts', ('read 工具', 'the read tool')), ('tools/index.ts', ('CodingTools：4 个工具', 'CodingTools: 4 tools'))]),
            ('testing/', ('一致性测试套件', 'Conformance suites'), 'infra', 'check', D.total('testing/'), [
                ('testing/runner.ts', ('register…Conformance()', 'register…Conformance()')), ('testing/storage-conformance.ts', ('存储用例', 'storage cases')), ('testing/env-conformance.ts', ('环境用例', 'environment cases'))])]
    D.has('tools/index.ts', 'CodingTools'); D.has('testing/runner.ts', 'export function registerStorageConformance(', 'export function registerEnvConformance(')
    # layout: 4 columns top, 3 below
    POS = [(16, 52, 262, 250), (290, 52, 262, 250), (564, 52, 540, 250), (16, 318, 262, 190), (290, 318, 262, 190), (564, 318, 262, 190), (838, 318, 266, 190)]
    for ci, ((sub, title, lay, ic, tot, rows), (x, y, w, h)) in enumerate(zip(COLS, POS)):
        f.group(x, y, w, h, lay, title, f'{sub or "src/*.ts"} · {tot:,}', ic, title_mono=False, gid=f'g{ci}')
        two = w > 400
        for ri, (p, role) in enumerate(rows):
            cx = x + 12 + (ri % 2) * ((w - 36) // 2 + 12) if two else x + 12
            cy = y + 44 + (ri // 2 if two else ri) * 48
            cw = (w - 36) // 2 if two else w - 24
            f.node(f'n{ci}{ri}', cx, cy, cw, 40, lay, p[len(sub):] if sub else p, role, None, tsize=10.3, ssize=8.8, tag=f'{D.loc(p):,}',
                   strong=p in ('harness/scheduler.ts', 'session/transaction.ts'))
    f.group(16, 524, 1088, 104, 'infra', ('11 个导入路径与依赖', '11 import paths and dependencies'), None, 'box', title_mono=False, gid='bot')
    x, y = 32, 560
    for k in ex:
        s = k[1:] or '.'
        x += f.chip(x, y, s, 'infra', size=9.4, h=20) + 6
    x, y = 32 + maxw(('依赖：', 'deps:'), 10, 600) + 8, 590
    f.text(32, y + 14, ('依赖：', 'deps:'), 10, 600, cls='faint', layer='label')
    for k, v in deps.items():
        x += f.chip(x, y, f'{k.replace("@earendil-works/", "")} {v}', 'modes', size=9.4, h=20) + 6
    U = users_of('@earendil-works/pi-durable')
    f.note(1096, 650, ('被导入：' + ' · '.join(f'{a} {b} 个文件' for a, b in U), 'imported by: ' + ' · '.join(f'{a} ({b} files)' for a, b in U)), 10.5, anchor='end')
    f.legend(24, 650, [('layer:agent', 'session'), ('layer:coding', 'harness'), ('layer:ext', ('存储', 'storage')), ('layer:modes', 'env')])
    return f

# ============================================================== dur_model : concepts & layering
@reg
def dur_model():
    readme('All changes go through one line of atomic commits, and nothing is shown before its commit is stored.',
           'A `Conversation` handle holds no state; compare handles by `id`.', 'Nothing in the registry is stored; conversations store extension names.')
    f = Fig('dur_model', 1120, 600, ('概念模型：一切都是提交到存储里的记录', 'The model: everything is a record committed to storage'))
    E = f.edge
    f.node('host', 16, 60, 250, 64, 'infra', ('宿主程序', 'Host program'), ('submit · wait · viewState · watch', 'submit · wait · viewState · watch'), 'user', mono=False, tsize=12, ssize=9.2)
    f.node('h', 300, 60, 370, 64, 'coding', 'Harness', ('一份打开的存储 + 运行 agent 的机制', 'one open storage + the machinery that runs agents'), 'cpu', tsize=13, ssize=9.4, strong=True)
    f.node('reg', 704, 60, 400, 64, 'tui', 'Registry', ('本进程安装的 extension（不存储，可随时变）', 'extensions this process installed (not stored, may change)'), 'layers', tsize=12, ssize=9.2)
    E([(266, 92), (300, 92)], 'host', 'h', 'main', 'infra')
    E([(704, 92), (670, 92)], 'reg', 'h', 'dep', 'tui')
    f.node('sess', 300, 150, 370, 56, 'agent', ('Session：唯一的原子提交线', 'Session: the single line of atomic commits'), ('提交前什么都不会被看到', 'nothing is shown before it is stored'), 'db', mono=False, tsize=11.5, ssize=9.2)
    E([(485, 124), (485, 150)], 'h', 'sess', 'main', 'coding')
    # conversation big group
    f.group(16, 232, 760, 300, 'agent', ('一个 Conversation（句柄不持有状态，按 id 比较）', 'One Conversation (handles hold no state; compare by id)'), None, 'msg', title_mono=False, gid='conv')
    f.group(32, 276, 236, 240, 'agent', ('Entry：不可变记录', 'Entries: immutable'), None, 'file', title_mono=False, gid='en')
    for i, (k, d) in enumerate([('pi.user', ('用户输入', 'user input')), ('pi.system', ('提示词变化', 'prompt changes')), ('pi.assistant', ('模型回答', 'model answer')),
                                ('pi.tool-result', ('工具结果', 'tool result')), ('pi.reset', ('新上下文起点', 'new context start')), ('pi.compaction', ('摘要', 'summary'))]):
        f.chip(46, 316 + i * 31, k, 'agent', size=9.6, h=20)
        f.text(160, 330 + i * 31, d, 9.2, 450, cls='muted', layer='label')
    f.group(282, 276, 236, 240, 'ext', ('Document：类型化 JSON', 'Documents: typed JSON'), None, 'braces', title_mono=False, gid='dc')
    for i, (k, d) in enumerate([('pi.agent', ('模型 · 工具 · cwd', 'model · tools · cwd')), ('pi.provider', ('sessionId', 'sessionId')), ('pi.live', ('运行中的生成与工具', 'running work')),
                                ('pi.inbox', ('排队的提交', 'queued submissions')), ('pi.usage', ('花费', 'spend')), ('app.*', ('你自己的', 'your own'))]):
        f.chip(296, 316 + i * 31, k, 'ext', size=9.6, h=20)
        f.text(392, 330 + i * 31, d, 9.2, 450, cls='muted', layer='label')
    f.group(532, 276, 228, 240, 'coding', ('Task 与 Submission', 'Tasks & submissions'), None, 'queue', title_mono=False, gid='tk')
    for i, (k, d) in enumerate([('pi.generation', ('调用模型', 'calls the model')), ('pi.tool', ('一次工具调用', 'one tool call')), ('pi.compaction', ('做摘要', 'summarizes'))]):
        f.chip(546, 316 + i * 31, k, 'coding', size=9.6, h=20)
        f.text(656, 330 + i * 31, d, 9.2, 450, cls='muted', layer='label')
    f.text(546, 430, ('Task 每一步都存检查点，', 'A task checkpoints every step,'), 9.2, 450, cls='muted', layer='label')
    f.text(546, 446, ('重启后从最后一步继续。', 'so a restart continues from it.'), 9.2, 450, cls='muted', layer='label')
    f.text(546, 476, ('Submission：交给会话的', 'A submission: input or an entry'), 9.2, 450, cls='muted', layer='label')
    f.text(546, 492, ('输入或条目，可以 wait()。', 'handed over; you can wait().'), 9.2, 450, cls='muted', layer='label')
    E([(485, 206), (485, 232)], 'sess', None, 'main', 'agent', label=('要么全存，要么全不存', 'all of it or none'), lpos=(560, 220))
    # right column
    f.group(792, 148, 312, 384, 'tui', ('Agent：会话用什么跑', 'Agent: what a conversation runs with'), None, 'gear', title_mono=False, gid='ag')
    A = [('model · thinkingLevel', ('模型与思考强度', 'model and thinking')), ('extensions · tools', ('按名字存储', 'stored by name')),
         ('instructions', ('最后渲染的提示词段', 'rendered as the last section')), ('cwd', ('环境由它构建', 'the env is built from it'))]
    for i, (a, b) in enumerate(A):
        f.text(808, 204 + i * 40, a, 10.2, 600, True, cls='strongt', layer='label')
        f.text(808, 221 + i * 40, b, 9.2, 450, cls='muted', layer='label')
    f.text(808, 370, ('存在 pi.agent 文档里；每次使用', 'Stored in the pi.agent document;'), 9.3, 450, cls='muted', layer='label')
    f.text(808, 387, ('时对照 Registry 解析。', 'resolved against the registry'), 9.3, 450, cls='muted', layer='label')
    f.text(808, 404, ('', 'at each use.'), 9.3, 450, cls='muted', layer='label')
    f.text(808, 436, ('扩展被卸载后，选它的会话只是', 'After an extension is uninstalled,'), 9.3, 450, cls='muted', layer='label')
    f.text(808, 453, ('暂时拿不到它，名字仍保留。', 'conversations just stop getting it;'), 9.3, 450, cls='muted', layer='label')
    f.text(808, 470, ('', 'the stored name stays.'), 9.3, 450, cls='muted', layer='label')
    f.text(808, 500, ('settings：每次使用时读取，从不存储', 'settings: read at every use, never stored'), 9.3, 600, cls='faint', layer='label')
    f.legend(24, 576, [('layer:agent', ('条目与会话', 'entries & conversations')), ('layer:ext', ('文档', 'documents')), ('layer:coding', ('任务', 'tasks')), ('layer:tui', ('扩展与 agent', 'extensions & agent'))])
    return f

# ============================================================== dur_run : one answered input
@reg
def dur_run():
    readme('submit(input) → pi.user', 'pi.generation → pi.system (only if the prompt or tools changed), pi.assistant (tool calls)',
           'pi.tool × n → pi.tool-result × n   (owned by the generation, which waits for them)', 'pi.generation → pi.assistant (answer) → submission done')
    D.has('harness/tool.ts', '| { phase: "call" }', 'replay: "safe" | "unsafe"', 'was interrupted and may have partially run')
    D.has('harness/generation.ts', 'phase: "prepare";', 'phase: "request";', '{ phase: "retry"; attempt: number;', 'phase: "poll";', 'phase: "tools";', 'const DEFAULT_POLL_AFTER_MS = 5000;')
    f = Fig('dur_run', 1120, 640, ('回答一次输入：条目与任务按时间排开', 'One answered input, as entries and tasks over time'))
    E = f.edge
    lanes = [('host', ('宿主', 'Host'), 'infra', 80), ('task', ('任务', 'Tasks'), 'coding', 170), ('entry', ('提交的条目', 'Committed entries'), 'agent', 260)]
    for k, t, lay, y in lanes:
        f.text(16, y + 4, t, 10.5, 650, cls='strongt', layer='label')
        hline(f, 120, 1104, y + 30)
    X = [140, 300, 460, 640, 820, 970]
    f.node('sub', X[0], 64, 140, 40, 'infra', 'submit(input)', None, None, tsize=10.5)
    f.node('u', X[0], 244, 140, 40, 'agent', 'pi.user', None, None, tsize=10.5)
    f.node('g1', X[1], 154, 140, 40, 'coding', 'pi.generation', ('第 1 轮', 'turn 1'), None, tsize=10.5, ssize=9)
    f.node('s', X[1] - 10, 244, 80, 40, 'agent', 'pi.system', None, None, tsize=9.8)
    f.node('a1', X[1] + 76, 244, 104, 40, 'agent', 'pi.assistant', ('工具调用', 'tool calls'), None, tsize=9.8, ssize=8.6)
    f.node('t1', X[2] + 30, 130, 130, 34, 'coding', 'pi.tool #1', None, None, tsize=10)
    f.node('t2', X[2] + 30, 176, 130, 34, 'coding', 'pi.tool #2', None, None, tsize=10)
    f.node('r', X[3], 244, 150, 40, 'agent', 'pi.tool-result × 2', None, None, tsize=10)
    f.node('g2', X[4], 154, 130, 40, 'coding', 'pi.generation', ('第 2 轮', 'turn 2'), None, tsize=10.5, ssize=9)
    f.node('a2', X[4], 244, 130, 40, 'agent', 'pi.assistant', ('回答', 'answer'), None, tsize=10, ssize=9)
    f.node('done', X[5], 64, 134, 40, 'infra', 'wait() → done', None, None, tsize=10.5, strong=True)
    E([(210, 104), (210, 244)], 'sub', 'u', 'main', 'infra')
    E([(250, 244), (250, 174), (300, 174)], 'u', 'g1', 'dep', 'agent', r=4)
    E([(370, 194), (370, 244)], 'g1', 'a1', 'main', 'coding')
    E([(440, 174), (465, 174), (465, 147), (490, 147)], 'g1', 't1', 'main', 'coding', r=4)
    E([(440, 174), (465, 174), (465, 193), (490, 193)], 'g1', 't2', 'main', 'coding', r=4)
    E([(620, 193), (715, 193), (715, 244)], 't2', 'r', 'main', 'coding', r=4)
    E([(620, 147), (715, 147), (715, 193)], 't1', None, 'main', 'coding', r=4)
    E([(790, 264), (805, 264), (805, 174), (820, 174)], 'r', 'g2', 'dep', 'agent', r=4)
    E([(885, 194), (885, 244)], 'g2', 'a2', 'main', 'coding')
    E([(950, 264), (1037, 264), (1037, 104)], 'a2', 'done', 'main', 'agent', r=4)
    f.text(300, 312, ('pi.system 只在提示词或工具变化时写入', 'pi.system only when the prompt or tools changed'), 9.2, 450, cls='faint', layer='label')
    f.text(490, 228, ('generation 拥有并等待它们', 'owned and awaited by the generation'), 9.2, 450, cls='faint', layer='label')
    # phases
    f.group(16, 340, 540, 236, 'coding', ('pi.generation 的检查点阶段', 'pi.generation checkpoint phases'), 'harness/generation.ts', 'loop', title_mono=False, gid='gp')
    P = [('prepare', ('组装请求；需要时先等一次压缩', 'build the request; wait for a compaction if needed')),
         ('request', ('流式调用模型（部分回答每 100 ms 提交）', 'stream the model (partials committed every 100 ms)')),
         ('retry', ('退避后重试：最多 3 次，基数 2000 ms', 'back off and retry: up to 3, base 2000 ms')),
         ('poll', ('延迟的回答：默认每 5000 ms 轮询', 'deferred answers: poll every 5000 ms by default')),
         ('tools', ('拥有本轮的 pi.tool 任务并等待', 'own this round\'s pi.tool tasks and wait'))]
    for i, (a, b) in enumerate(P):
        y = 384 + i * 36
        f.chip(32, y, a, 'coding', size=9.8, h=22)
        f.text(118, y + 15, b, 9.4, 450, cls='muted', layer='label')
    # crash recovery
    f.group(572, 340, 532, 236, 'err', ('进程崩溃之后', 'After a crash'), 'harness/tool.ts', 'shield', title_mono=False, gid='cr')
    f.text(588, 394, ('pi.tool 先提交意图（phase "execute"），再运行 execute()。', 'pi.tool commits its intent (phase "execute") before execute() runs.'), 9.4, 450, cls='muted', layer='label')
    f.text(588, 424, ('replay: "safe"', 'replay: "safe"'), 10, 650, True, cls='strongt', layer='label')
    f.text(700, 424, ('重新打开时重跑', 'rerun on reopen'), 9.4, 450, cls='muted', layer='label')
    f.text(588, 450, ('默认 "unsafe"', 'default "unsafe"'), 10, 650, True, cls='strongt', layer='label')
    f.text(700, 450, ('模型收到 interrupted 错误结果：', 'the model gets an interrupted error:'), 9.4, 450, cls='muted', layer='label')
    f.text(700, 468, '"Tool … was interrupted and may have partially run"', 9.2, 500, True, cls='err', layer='label')
    f.text(588, 502, ('其余工作保持 pending；resume()（或下一次 submit / wait）启动调度器，', 'Everything else stays pending; resume() (or the next submit / wait) starts the'), 9.4, 450, cls='muted', layer='label')
    f.text(588, 520, ('从最后的检查点继续。', 'scheduler, which continues from the last checkpoints.'), 9.4, 450, cls='muted', layer='label')
    f.text(588, 550, ('同一个 requestId 的重复 submit 返回原来的 submission。', 'A resubmit with the same requestId returns the existing submission.'), 9.4, 600, cls='strongt', layer='label')
    f.legend(24, 612, [('layer:agent', ('条目', 'entries')), ('layer:coding', ('任务', 'tasks')), ('main', ('产生', 'produces')), ('dep', ('作为输入', 'feeds'))])
    return f

# ============================================================== dur_tasks : task state machine & ownership
@reg
def dur_tasks():
    st = re.findall(r'readonly status: "(\w+)";', re.search(r'export type TaskState<S, R> =(.*?)\n\n', D.src('types.ts'), re.S).group(1))
    oc = re.findall(r'readonly status: "(\w+)";', re.search(r'export type TaskOutcome<R> =(.*?)\n\n', D.src('types.ts'), re.S).group(1))
    assert st == ['pending', 'running', 'waiting', 'completing', 'terminal'], st
    assert oc == ['completed', 'failed', 'aborted', 'orphaned', 'faulted'], oc
    D.has('harness/scheduler.ts', 'const LIVE_STATUSES = ["pending", "running", "waiting", "completing"] as const;')
    readme('A task created with `{ background: true }` is a boundary', 'abort runs bottom-up', 'with `failFast` the first failed child also aborts the others')
    f = Fig('dur_tasks', 1120, 600, ('Task：可恢复的状态机与所有权', 'Tasks: a resumable state machine with ownership'))
    E = f.edge
    f.node('pe', 32, 100, 150, 56, 'coding', 'pending', ('可被调度', 'eligible to run'), None, tsize=12, ssize=9.2)
    f.node('ru', 252, 100, 150, 56, 'coding', 'running', ('一次内存中的调用', 'one in-memory invocation'), None, tsize=12, ssize=9.2, strong=True)
    f.node('wa', 252, 224, 150, 56, 'agent', 'waiting', ('on: [...] · policy', 'on: [...] · policy'), None, tsize=12, ssize=9.2)
    f.node('co', 472, 100, 150, 56, 'modes', 'completing', ('结果已定，等下属工作', 'outcome held'), None, tsize=12, ssize=9.2)
    f.node('te', 692, 100, 150, 56, 'infra', 'terminal', ('永久结果', 'permanent receipt'), None, tsize=12, ssize=9.2, strong=True)
    E([(182, 128), (252, 128)], 'pe', 'ru', 'main', 'coding')
    E([(312, 156), (312, 224)], 'ru', 'wa', 'main', 'coding', label=('提交 waiting', 'commit waiting'), lpos=(270, 192))
    E([(342, 224), (342, 156)], 'wa', 'ru', 'dep', 'agent', label=('on 都结束', 'all of on done'), lpos=(390, 192))
    E([(402, 128), (472, 128)], 'ru', 'co', 'main', 'coding')
    E([(622, 128), (692, 128)], 'co', 'te', 'main', 'modes')
    E([(402, 112), (437, 112), (437, 76), (727, 76), (727, 100)], 'ru', 'te', 'dep', 'coding', label=('没有下属工作时直接结束', 'straight to terminal when nothing below is live'), lpos=(582, 68), r=6)
    E([(252, 140), (217, 140), (217, 150), (182, 150)], 'ru', 'pe', 'event', 'err', r=4)
    f.text(32, 186, ('重启后，running', 'After a restart, running'), 9.2, 450, cls='err', layer='label')
    f.text(32, 202, ('显示为 pending', 'shows as pending'), 9.2, 450, cls='err', layer='label')
    f.text(472, 192, ('每次状态转换都在 Session 的', 'Every transition is serialized'), 9.3, 450, cls='muted', layer='label')
    f.text(472, 209, ('提交线上串行完成。', 'on the Session\'s commit line.'), 9.3, 450, cls='muted', layer='label')
    f.text(472, 240, ('活状态：pending · running ·', 'Live: pending · running ·'), 9.3, 600, cls='faint', layer='label')
    f.text(472, 257, ('waiting · completing', 'waiting · completing'), 9.3, 600, cls='faint', layer='label')
    # outcomes
    f.group(864, 52, 240, 248, 'infra', ('TaskOutcome', 'TaskOutcome'), None, 'flag', title_mono=False, gid='oc')
    OD = {'completed': ('带 result', 'carries result'), 'failed': ('实现主动提交的失败', 'failure the task committed'), 'aborted': ('走了 abort 协议', 'handled abort'),
          'orphaned': ('定义或迁移不可用', 'definition / migration missing'), 'faulted': ('运行时检测到违约', 'runtime contract failure')}
    for i, o in enumerate(oc):
        y = 96 + i * 40
        f.text(880, y + 4, o, 10.3, 650, True, cls='err' if o in ('faulted', 'orphaned') else 'strongt', layer='label')
        f.text(880, y + 21, OD[o], 9.2, 450, cls='muted', layer='label')
    # ownership
    f.group(16, 316, 640, 240, 'agent', ('所有权：每个任务都有主人', 'Ownership: every task has an owner'), None, 'tree', title_mono=False, gid='own')
    f.node('cv', 32, 360, 150, 40, 'agent', ('会话', 'conversation'), None, 'msg', mono=False, tsize=10.5)
    f.node('gen', 216, 360, 150, 40, 'coding', 'pi.generation', None, None, tsize=10.5)
    f.node('tl', 400, 360, 110, 40, 'coding', 'pi.tool', ('subagent', 'subagent'), None, tsize=10.5, ssize=8.8)
    f.node('ch', 544, 360, 100, 40, 'agent', ('子会话', 'child conv'), None, None, mono=False, tsize=10.5)
    E([(182, 380), (216, 380)], 'cv', 'gen', 'main', 'agent')
    E([(366, 380), (400, 380)], 'gen', 'tl', 'main', 'coding')
    E([(510, 380), (544, 380)], 'tl', 'ch', 'main', 'coding')
    f.text(32, 428, ('· 中止调用会中止子会话；父会话要等子会话空闲才算空闲。', '· Aborting the call aborts the child; the parent is idle only once the child is.'), 9.4, 450, cls='muted', layer='label')
    f.text(32, 452, ('· 中止自下而上：先中止它拥有的工作，再运行它自己的 abort 处理。', '· Abort runs bottom-up: owned work first, then the task\'s own abort handler.'), 9.4, 450, cls='muted', layer='label')
    f.text(32, 476, ('· { background: true } 的任务是边界：它拥有的工作不受父中止影响，也不让父忙碌。', '· A { background: true } task is a boundary: its work survives the parent\'s abort and keeps it idle.'), 9.4, 450, cls='muted', layer='label')
    f.text(32, 500, ('· 等待策略：failFast（第一个失败就中止其余）或 allSettled。', '· Join policy: failFast (the first failure aborts the rest) or allSettled.'), 9.4, 450, cls='muted', layer='label')
    f.text(32, 532, ('harness.taskGraph() 把所有活任务显示为一个 Chord state（例：24-child-tasks.ts）', 'harness.taskGraph() shows every live task as one Chord state (example: 24-child-tasks.ts)'), 9.3, 600, cls='faint', layer='label')
    codebox(f, 672, 316, 432, [(0, ('// 子任务：创建后进入 waiting', '// child tasks: create, then wait'), 'muted'),
                               (0, 'pay: async (task, runtime, ctx) => {', ''),
                               (1, 'await runtime.commit(async tx => {', ''),
                               (2, 'const ids = [...] // tx.createTask(…)', ''),
                               (2, 'return { status: "waiting",', 'strongt'),
                               (3, 'checkpoint: { phase: "decide", ids },', ''),
                               (3, 'on: ids, policy: "failFast" };', 'strongt'),
                               (1, '}, ctx);', ''), (0, '},', '')], ('README：子任务', 'README: child tasks'))
    f.legend(24, 580, [('main', ('转换', 'transition')), ('dep', ('恢复 / 捷径', 'resume / shortcut')), ('event', ('重启', 'restart')), ('layer:modes', 'completing')])
    return f

# ============================================================== dur_inbox : busy conversations
@reg
def dur_inbox():
    D.has('harness/submissions.ts', 'if (busy && draft.type === "input" && draft.whenBusy === "reject") throw new ConversationBusy(conversationId);',
          'const mode = draft.whenBusy === "steer" ? "steer" : "followUp";')
    D.has('harness/types.ts', 'export type QueueMode = "all" | "one-at-a-time";')
    D.has('harness/agent.ts', 'steeringMode: settings?.steeringMode ?? "one-at-a-time",', 'followUpMode: settings?.followUpMode ?? "one-at-a-time",')
    D.has('harness/inbox.ts', 'kind: "pi.inbox",')
    readme('**Steers** are placed after the current tool round and join the running work.', '**Follow-ups** are placed when the run answers, and start the next run.',
           'If a run fails, queued items stay in the inbox until the next submission places them, oldest first.')
    f = Fig('dur_inbox', 1120, 580, ('会话忙时的提交：steer · followUp · reject · write', 'Submitting to a busy conversation: steer · followUp · reject · write'))
    E = f.edge
    f.node('sub', 16, 120, 196, 64, 'infra', 'root.submit(x, ctx)', ('会话正在跑一个 run', 'a run is in progress'), None, tsize=11, ssize=9.2)
    R = [('rej', 'whenBusy: "reject"', ('立即抛出 ConversationBusy', 'throws ConversationBusy at once'), 'err', 56),
         ('st', 'whenBusy: "steer"', ('进 pi.inbox，mode steer', 'into pi.inbox as steer'), 'modes', 128),
         ('fu', ('默认：followUp', 'default: followUp'), ('进 pi.inbox，mode followUp', 'into pi.inbox as followUp'), 'agent', 200),
         ('wr', '{ type: "write", entry }', ('排队写条目，不问模型', 'queue an entry, no model call'), 'ext', 272)]
    for n, t, s, lay, y in R:
        f.node(n, 270, y, 236, 52, lay, t, s, None, mono=not isinstance(t, tuple), tsize=10.5, ssize=9.2, strong=(n == 'fu'))
        E([(212, 152), (240, 152), (240, y + 26), (270, y + 26)], 'sub', n, 'err' if lay == 'err' else 'main', lay, r=6)
    # run timeline
    f.group(540, 52, 564, 280, 'coding', ('它们什么时候被放进转录', 'When they are placed into the transcript'), None, 'clock', title_mono=False, gid='tl')
    hline(f, 560, 1088, 200)
    T = [(580, ('第 1 轮', 'turn 1')), (700, ('工具轮', 'tool round')), (830, ('第 2 轮', 'turn 2')), (960, ('回答', 'answer'))]
    for x, t in T:
        f.node(f't{x}', x, 180, 100, 40, 'coding', t, None, None, mono=False, tsize=10.2)
    f.text(800, 248, ('steer：当前工具轮之后，加入正在跑的工作', 'steer: after the current tool round, joins the running work'), 9.4, 600, cls='strongt', layer='label', anchor='middle')
    E([(815, 236), (815, 220)], None, 't830', 'main', 'modes')
    f.text(1010, 112, ('followUp：run 回答后放入，', 'followUp: placed when the run'), 9.4, 600, cls='strongt', layer='label', anchor='middle')
    f.text(1010, 128, ('开启下一个 run', 'answers; starts the next run'), 9.4, 600, cls='strongt', layer='label', anchor='middle')
    E([(1010, 138), (1010, 180)], None, 't960', 'main', 'agent')
    f.text(560, 290, ('steeringMode / followUpMode 默认 "one-at-a-time"：每轮放一条；"all"：一次全放。', 'steeringMode / followUpMode default "one-at-a-time": one per turn; "all": every queued item at once.'), 9.2, 450, cls='muted', layer='label')
    f.text(560, 310, ('run 失败时，排队项留在 inbox，等下一次提交时按先后放入。', 'If a run fails, queued items stay until the next submission places them, oldest first.'), 9.2, 450, cls='muted', layer='label')
    # bottom panels
    f.group(16, 348, 540, 196, 'ext', ('pi.inbox 文档', 'The pi.inbox document'), 'harness/inbox.ts', 'inbox', title_mono=False, gid='ib')
    codebox(f, 32, 388, 508, [(0, '{ items: [', ''), (1, '{ id, mode: "steer",    content },', ''), (1, '{ id, mode: "followUp", content },', ''), (1, '… writes and resets queue here too', 'muted'), (0, '] }', '')], None)
    f.text(32, 528, ('UI 从 view.docs["pi.inbox"] 直接画出排队区。', 'A UI draws its queue straight from view.docs["pi.inbox"].'), 9.3, 450, cls='faint', layer='label')
    f.group(572, 348, 532, 196, 'agent', ('撤回、重置与幂等', 'Withdraw, reset and idempotency'), None, 'key', title_mono=False, gid='id')
    L = [('submission.abort(ctx)', ('撤回仍在排队的提交', 'withdraw a queued submission')),
         ('root.abort(ctx)', ('撤回排队输入（写入保留），中止当前工作', 'withdraw queued inputs (writes stay), abort work')),
         ('root.reset(note?, ctx)', ('忙时像写入一样排队', 'queued like a write while busy')),
         ('requestId', ('同一 ID 重复提交 → 原来那个 submission', 'same ID again → the existing submission'))]
    for i, (a, b) in enumerate(L):
        y = 402 + i * 34
        f.text(588, y, a, 10, 600, True, cls='strongt', layer='label')
        f.text(588, y + 16, b, 9.2, 450, cls='muted', layer='label')
    f.legend(24, 564, [('layer:modes', 'steer'), ('layer:agent', 'followUp'), ('layer:ext', 'write'), ('layer:err', 'reject')])
    return f

# ============================================================== dur_docs : documents & watching
@reg
def dur_docs():
    DOCS = []
    for p in ['harness/agent.ts', 'harness/provider.ts', 'harness/live.ts', 'harness/inbox.ts', 'harness/usage.ts']:
        s = D.src(p)
        m = re.search(r'kind: "(pi\.[\w-]+)",.*?history: "(\w+)",\s*fork: "(\w+)"', s, re.S)
        DOCS.append((m.group(1), m.group(2), m.group(3), p))
    assert [d[0] for d in DOCS] == ['pi.agent', 'pi.provider', 'pi.live', 'pi.inbox', 'pi.usage'], DOCS
    assert DOCS[0][1:3] == ('rewindable', 'asOf'), DOCS[0]
    D.has('session/observation.ts', 'const MAX_PENDING_WATCH_FRAMES = 100;')
    readme('When a consumer falls more than 100 batches behind, it receives a fresh `snapshot` event instead.', 'history: "latest", // or "rewindable" to read old values with snapshotAsOf()')
    f = Fig('dur_docs', 1120, 600, ('文档与观察：UI 需要的一切都是已提交的状态', 'Documents and watching: everything a UI needs is committed state'))
    E = f.edge
    f.group(16, 52, 520, 300, 'ext', ('内置文档（scope: conversation）', 'Built-in documents (scope: conversation)'), None, 'braces', title_mono=False, gid='bd')
    hdr = [(32, ('文档', 'document')), (150, ('内容', 'holds')), (360, 'history'), (448, 'fork')]
    for x, t in hdr: f.text(x, 98, t, 9.3, 650, cls='faint', layer='label')
    WHAT = {'pi.agent': ('模型 · 扩展 · 工具 · cwd', 'model · extensions · tools · cwd'), 'pi.provider': ('sessionId = UUIDv7', 'sessionId = UUIDv7'),
            'pi.live': ('运行中的生成、工具、压缩', 'running generation, tools, compactions'), 'pi.inbox': ('排队的提交', 'queued submissions'), 'pi.usage': ('按模型 / 工具的花费', 'spend per model / tool')}
    for i, (k, h, fk, p) in enumerate(DOCS):
        y = 112 + i * 44
        hline(f, 32, 520, y)
        f.chip(32, y + 10, k, 'ext', size=9.6, h=20)
        f.text(150, y + 24, WHAT[k], 9.2, 450, cls='muted', layer='label')
        f.text(360, y + 24, h, 9.4, 600, True, cls='strongt' if h != 'latest' else 'muted', layer='label')
        f.text(448, y + 24, fk, 9.4, 600, True, cls='strongt' if fk != 'initial' else 'muted', layer='label')
    f.text(32, 340, ('pi.agent 可回溯：分叉拿到分叉点那一刻的 agent；其余分叉时从初始值开始。', 'pi.agent is rewindable: a fork gets the agent as of the fork entry; the rest start fresh.'), 9.0, 450, cls='faint', layer='label')
    codebox(f, 552, 52, 552, [(0, 'const Todos = defineDoc<{ items: string[] }>({', ''),
                              (1, 'kind: "app.todos", version: 1,', ''),
                              (1, 'scope: "conversation",', ''),
                              (1, ('history: "latest",  // 或 "rewindable"', 'history: "latest",  // or "rewindable"'), 'muted'),
                              (1, 'fork: "initial",    // "current" | "asOf"', 'muted'),
                              (1, 'initial: () => ({ items: [] }),', ''),
                              (0, '});', ''),
                              (0, 'await root.commit(async tx =>', ''),
                              (1, '(await tx.doc(Todos, root.id)).items.push("write docs"), ctx);', 'strongt')], ('你自己的文档（README）', 'Your own document (README)'))
    # watching
    f.group(16, 368, 1088, 188, 'agent', ('三种观察方式', 'Three ways to watch'), None, 'eye', title_mono=False, gid='w')
    W = [('viewState(ctx)', ('只读 Chord state：entries + docs', 'read-only Chord state: entries + docs'), ('每次相关提交后更新', 'updated after every commit that touches it')),
         ('watch(ctx)', ('同一个视图 + 每次提交的精确 Chord op', 'the same view + each commit\'s exact Chord ops'), ('慢消费者最多 100 帧，之后换成一帧完整视图', 'slow consumers: 100 frames, then one whole-view frame')),
         ('watchEvents(…)', ('coding-agent 风格事件（实验性）', 'coding-agent style events (experimental)'), ('落后超过 100 批 → 一个新的 snapshot 事件', 'more than 100 batches behind → a fresh snapshot event'))]
    for i, (a, b, c) in enumerate(W):
        x = 32 + i * 356
        f.node(f'w{i}', x, 412, 340, 56, 'agent', a, b, None, tsize=11, ssize=9.2, strong=(i == 1))
        f.text(x, 492, c, 9.2, 450, cls='muted', layer='label')
    f.text(32, 528, ('迟到或重连的客户端从当前视图开始，不会重放历史；部分回答与工具输出默认最多每 100 ms 提交一次。', 'Late or reconnecting clients start from the current view, nothing is replayed; partials and tool output commit at most every 100 ms.'), 9.3, 450, cls='faint', layer='label')
    f.legend(24, 580, [('layer:ext', ('文档', 'documents')), ('layer:agent', ('观察', 'watching'))])
    return f

# ============================================================== dur_storage
@reg
def dur_storage():
    wt = re.findall(r'readonly type: "([\w.]+)"', re.search(r'export type StorageWrite =(.*?)\n\n', D.src('types.ts'), re.S).group(1))
    assert wt == ['conversation', 'entry', 'task', 'submission', 'document.create', 'document.copy', 'document.change', 'document.retire'], wt
    D.has('storage/sqlite/node.ts', 'PRAGMA journal_mode = WAL', 'PRAGMA synchronous = NORMAL', 'const DEFAULT_WAL_AUTO_CHECKPOINT_PAGES = 1_000;', 'const DEFAULT_BUSY_TIMEOUT_MS = 5_000;')
    tables = re.findall(r'CREATE TABLE (\w+) \(', D.src('storage/sqlite/migrations.ts'))
    assert tables == ['durable_metadata', 'record_ids', 'conversations', 'entries', 'tasks', 'submissions', 'documents', 'document_revisions'], tables
    D.has('storage/jsonl/storage.ts', 'const MAIN_FILE = "main.jsonl";', 'readonly type: "commit";', '`${kind}-${id}.jsonl`')
    readme('One process owns a storage at a time; there is no cross-process locking.')
    f = Fig('dur_storage', 1120, 620, ('存储：一个 commit(writes) 接口，四种后端', 'Storage: one commit(writes) interface, four backends'))
    E = f.edge
    f.node('sess', 16, 64, 250, 60, 'agent', 'Session', ('把一次事务变成一组写入', 'turns a transaction into writes'), 'db', tsize=12, ssize=9.2)
    f.node('st', 330, 64, 460, 60, 'infra', 'Storage.commit(writes, ctx) → Seq', ('全部写入或全部不写；Seq 单调递增', 'all writes or none; Seq increases'), 'stack', tsize=11.5, ssize=9.2, strong=True)
    E([(266, 94), (330, 94)], 'sess', 'st', 'main', 'agent')
    f.group(820, 52, 284, 230, 'infra', ('StorageWrite 的 8 种类型', 'The 8 StorageWrite types'), None, 'layers', title_mono=False, gid='wt')
    for i, w in enumerate(wt):
        f.chip(836 + (i % 2) * 132, 96 + (i // 2) * 34, w, 'infra', size=9.6, h=22)
    f.text(836, 262, ('文档还有修订历史（rewindable）', 'documents also keep revisions'), 9.2, 450, cls='faint', layer='label')
    f.group(16, 148, 790, 134, 'infra', ('读取接口', 'Read interface'), None, 'eye', title_mono=False, gid='rd')
    RD = ['conversation', 'scanConversations', 'entry', 'scanEntries', 'findLatestHeadMarker', 'task', 'scanTasks', 'submission', 'submissionByRequest', 'scanSubmissions', 'document', 'findDocument', 'scanDocuments', 'mintId', 'close']
    blk = re.search(r'export interface Storage \{(.*?)^\}', D.src('types.ts'), re.S | re.M).group(1)
    for r in RD: assert re.search(r'^\t' + r + r'[<(]', blk, re.M), r
    x, y = 32, 190
    for r in RD:
        w = maxw(r + '()', 9.6, 500, True) + 16
        if x + w > 792: x, y = 32, y + 30
        x += f.chip(x, y, r + '()', 'infra', size=9.6, h=22) + 6
    f.text(32, 268, ('每个查询都分页（limit + cursor）；同一时刻只能有一个进程拥有一个存储，没有跨进程锁。', 'Every scan is paged (limit + cursor); one process owns a storage at a time, with no cross-process locking.'), 9.2, 450, cls='faint', layer='label')
    B = [('Memory', 'MemoryStorage', ('什么都不持久化；测试与示例', 'nothing persisted; tests and examples'), [(('从包根导入', 'exported from the package root'), 'm'), (('与其他后端跑同一套一致性测试', 'runs the same conformance suite'), 'm')], 'ext'),
         ('SQLite (Node)', 'openNodeSqliteStorage(file)', ('一个数据库文件', 'one database file'),
          [('WAL · synchronous = NORMAL', ''), ('wal_autocheckpoint 1000 · busy 5000 ms', ''), (('崩溃不丢提交；断电可能丢最新一个', 'survives crashes; power loss may drop the newest'), 'm')], 'coding'),
         ('JSONL (Node)', 'openNodeJsonlStorage(dir, ctx)', ('一个目录里的追加文件', 'append-only files in a directory'),
          [(('main.jsonl：每次提交追加一行标记', 'main.jsonl: one marker line per commit'), 'm'), ('{format:1, type:"commit", seq, writes}', ''), (('task-<id>.jsonl / doc-<id>.jsonl 旁路文件', 'task-<id>.jsonl / doc-<id>.jsonl sidecars'), 'm'), ('{ fsync: true }', '')], 'agent'),
         ('Cloudflare DO', 'openDurableObjectSqliteStorage(…)', ('一个 Durable Object 的 SQLite', 'one Durable Object\'s SQLite'), [(('提交 = 它的存储事务', 'commits = its storage transactions'), 'm')], 'modes')]
    for i, (name, fn, sub, det, lay) in enumerate(B):
        x = 16 + i * 276
        f.group(x, 300, 264, 236, lay, name, None, 'db', title_mono=False, gid=f'b{i}')
        f.text(x + 16, 344, fn, 9.4, 650, True, cls='strongt', layer='label')
        f.text(x + 16, 362, sub, 9.2, 450, cls='muted', layer='label')
        for j, (t, kind) in enumerate(det):
            f.text(x + 16, 392 + j * 22, t, 8.8, 500, kind != 'm', cls='muted', layer='label')
        E([(x + 132, 300), (x + 132, 282)], None, None, 'dep', lay)
    f.text(16 + 276 + 16, 470, ('8 张表：', '8 tables:'), 9.0, 600, cls='faint', layer='label')
    for i, t in enumerate(tables):
        f.text(16 + 276 + 16 + (i % 2) * 118, 488 + (i // 2) * 14, t, 8.6, 500, True, cls='faint', layer='label')
    f.note(1096, 600, ('可移植核心 /storage/sqlite、/storage/jsonl 不依赖 Node：可跑在 Bun 或 Durable Object 上', 'portable cores /storage/sqlite and /storage/jsonl need no Node APIs: Bun, Durable Objects'), 10.5, anchor='end')
    f.legend(24, 600, [('main', ('提交', 'commit')), ('dep', ('实现', 'implements'))])
    return f

# ============================================================== dur_ext : extensions, hooks, prompt, reload
@reg
def dur_ext():
    for fn in ['defineExtension', 'defineTool', 'section', 'hook', 'wrapTool', 'wrapSection']:
        D.has('harness/define.ts', f'export function {fn}')
    D.has('harness/registry.ts', 'export const BUILTIN_TASKS: readonly AnyTask[] = [GenerationTask, ToolTask, CompactionTask];')
    for h in ['beforeRequest(', 'afterResponse(', 'onYield(', 'afterTools(', 'beforeTool(', 'afterTool(', 'beforeCompact(']:
        D.has('harness/types.ts', h)
    readme('Sections and tool changes are stored as positional system entries in the transcript.', 'each task phase resolves hooks and the agent once, from the registry at the phase\'s start.',
           'when every result of the round asks for it, the run ends without another model request.')
    f = Fig('dur_ext', 1120, 620, ('扩展：工具 · 提示词段 · 钩子 · 包装器 · 任务', 'Extensions: tools · sections · hooks · wraps · tasks'))
    E = f.edge
    f.group(16, 52, 340, 300, 'tui', 'defineExtension({ name, … })', None, 'layers', title_mono=True, gid='ex')
    X = [('tools', ('defineTool：TypeBox 参数', 'defineTool: TypeBox params')),
         ('sections', ('section(name, fn)', 'section(name, fn)')),
         ('hooks', ('hook(Task, {…})：见右', 'hook(Task, {…}): see right')),
         ('wraps', ('wrapTool / wrapSection', 'wrapTool / wrapSection')),
         ('tasks', ('自己的持久任务', 'your own durable tasks'))]
    for i, (a, b) in enumerate(X):
        y = 100 + i * 44
        f.chip(32, y, a, 'tui', size=10, h=22)
        f.text(112, y + 15, b, 9.2, 450, cls='muted', layer='label')
    f.text(32, 330, ('同名工具：后安装的覆盖先安装的', 'Same-name tool: the later extension wins'), 9.2, 600, cls='faint', layer='label')
    # hooks matrix
    f.group(372, 52, 732, 300, 'coding', ('钩子挂在三个内置任务上', 'Hooks attach to the three built-in tasks'), 'BUILTIN_TASKS', 'branch', title_mono=False, gid='hk')
    H = [('GenerationTask', 'pi.generation', [('beforeRequest', ('替换一次请求的消息', 'replace one request\'s messages')), ('afterResponse', ('看到回答', 'observe the answer')),
                                              ('onYield', ('{ continue } 让 run 继续', '{ continue } keeps the run going')), ('afterTools', ('一轮工具都结束后', 'after a round\'s tools'))]),
         ('ToolTask', 'pi.tool', [('beforeTool', ('{ block } 或改写参数', '{ block } or rewrite args')), ('afterTool', ('替换结果', 'replace the result'))]),
         ('CompactionTask', 'pi.compaction', [('beforeCompact', ('拒绝或自给摘要', 'decline or supply a summary'))])]
    x = 388
    for i, (tk, kind, hs) in enumerate(H):
        w = 270 if i == 0 else 208
        f.node(f'h{i}', x, 96, w, 44, 'coding', tk, f'`{kind}', None, tsize=11, ssize=9.2, strong=(i == 0))
        for j, (hn, hd) in enumerate(hs):
            y = 160 + j * 44
            f.text(x + 4, y + 4, hn, 10, 650, True, cls='strongt', layer='label')
            f.text(x + 4, y + 21, hd, 9.2, 450, cls='muted', layer='label')
        x += w + 14
    f.text(388, 340, ('钩子只在选中该扩展的会话里生效：configure({ extensions: { add: [Guard] } })', 'Hooks act only in conversations that select their extension: configure({ extensions: { add: [Guard] } })'), 9.2, 450, cls='faint', layer='label')
    # prompt
    f.group(16, 368, 540, 192, 'agent', ('系统提示词', 'The system prompt'), 'harness/prompt.ts', 'file', title_mono=False, gid='pr')
    f.text(32, 420, ('按顺序渲染所选扩展的段；instructions 最后渲染。', 'Selected extensions\' sections render in order; instructions last.'), 9.4, 450, cls='muted', layer='label')
    f.text(32, 440, '<cwd>\\n/work/repo\\n</cwd>   ← section("cwd", i => i.env?.cwd)', 9.4, 600, True, cls='strongt', layer='label')
    f.text(32, 470, ('段与工具变化存成转录里按位置的 pi.system 条目，', 'Section and tool changes are stored as positional pi.system'), 9.4, 450, cls='muted', layer='label')
    f.text(32, 488, ('只重发变化的部分 → provider 提示缓存保持命中。', 'entries; only changes are resent → prompt caches stay warm.'), 9.4, 450, cls='muted', layer='label')
    f.text(32, 518, ('每次都变的段（如当前时间）会破坏缓存。', 'A section that changes every time (e.g. the time) defeats that.'), 9.4, 600, cls='err', layer='label')
    # reload
    f.group(572, 368, 532, 192, 'modes', ('重载', 'Reload'), None, 'loop', title_mono=False, gid='rl')
    f.text(588, 420, ('registry.install(ext)：同名就原地替换，一步完成。', 'registry.install(ext): same name replaces in place, in one step.'), 9.4, 450, cls='muted', layer='label')
    f.text(588, 444, ('已开始的工作保留它拿到的代码：', 'Work that started keeps the code it took:'), 9.4, 600, cls='strongt', layer='label')
    f.text(588, 464, ('· 运行中的工具调用用旧实现跑完', '· a running tool call finishes on the old code'), 9.4, 450, cls='muted', layer='label')
    f.text(588, 482, ('· 每个任务阶段开始时解析一次钩子和 agent', '· each task phase resolves hooks and agent once'), 9.4, 450, cls='muted', layer='label')
    f.text(588, 500, ('· 下一个阶段 / 请求 / 调用用新代码', '· the next phase / request / call uses new code'), 9.4, 450, cls='muted', layer='label')
    f.text(588, 530, ('重启后重新安装同样的扩展，其 pending 任务就会继续。', 'After a restart, install them again; their pending tasks resume.'), 9.4, 450, cls='faint', layer='label')
    f.legend(24, 596, [('layer:tui', ('扩展', 'extensions')), ('layer:coding', ('内置任务与钩子', 'built-in tasks & hooks')), ('layer:agent', ('提示词', 'prompt')), ('layer:modes', ('重载', 'reload'))])
    return f
