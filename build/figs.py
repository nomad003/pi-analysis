"""Every architecture diagram, laid out by hand with exact coordinates (see svgkit.py). Facts re-verified against /workspace/pi-src @ 4130bd5."""
import re
from pathlib import Path
from svgkit import Fig, maxw, tw, icon, pair
SRC = Path('/workspace/pi-src')
FIG = {}
def reg(fn): FIG[fn.__name__] = fn; return fn

# ============================================================== 1. packages
@reg
def packages():
    f = Fig('packages', 1120, 624, ('包依赖图', 'Package dependency graph'))
    # containers
    f.group(232, 84, 220, 404, 'coding', ('运行时栈', 'RUNTIME STACK'), icon_name='layers', title_mono=False)
    f.group(476, 84, 200, 236, 'tui', ('独立库', 'STANDALONE'), ('无内部依赖', 'no internal deps'), title_mono=False)
    f.group(700, 84, 400, 308, 'infra', ('持久化与远程会话', 'DURABLE & REMOTE SESSIONS'), icon_name='cloud', title_mono=False)
    N = lambda *a, **k: f.node(*a, **k)
    N('ca', 252, 120, 180, 56, 'coding', 'pi-coding-agent', ('AgentSession · 8 工具', 'AgentSession · tools'), 'terminal', strong=True)
    N('ag', 252, 216, 180, 56, 'agent', 'pi-agent-core', 'Agent · runLoop()', 'loop', strong=True)
    N('ai', 252, 312, 180, 56, 'ai', 'pi-ai', ('42 provider · 10 种 API', '42 providers · 10 APIs'), 'spark', strong=True)
    N('tel', 252, 408, 180, 56, 'infra', 'pi-telemetry', ('遥测契约', 'telemetry contracts'), 'eye')
    N('tui', 496, 124, 160, 48, 'tui', 'pi-tui', ('差分渲染', 'differential render'), 'monitor')
    N('mcp', 496, 188, 160, 48, 'infra', 'pi-mcp', ('MCP 客户端', 'MCP client'), 'plug')
    N('cm', 496, 252, 160, 48, 'infra', 'pi-codemode', ('沙箱 JS 执行', 'sandboxed JS'), 'code')
    N('srv', 720, 120, 170, 56, 'infra', 'pi-server', ('实验性服务端', 'experimental server'), 'cloud')
    N('cli', 910, 120, 170, 56, 'infra', 'pi-client', ('远程会话客户端', 'remote client'), 'globe')
    N('prot', 815, 216, 170, 56, 'infra', 'pi-protocol', ('CBOR 帧协议', 'CBOR protocol'), 'braces')
    N('dur', 720, 312, 170, 56, 'infra', 'pi-durable', ('持久化运行时', 'durable runtime'), 'db')
    N('env', 910, 312, 170, 56, 'infra', 'pi-env', ('经 SSH 远程执行', 'remote exec · SSH'), 'terminal')
    N('ev', 40, 312, 164, 56, 'infra', 'pi-evals', ('评测工具', 'eval harness'), 'check')
    N('ch', 12, 520, 1096, 48, 'infra', 'chord', ('应用组合运行时：services · 复制状态 · RPC · plugins', 'application composition runtime — services · replicated state · RPC · plugins'), 'hub', strong=True)
    E = f.edge
    E([(342, 176), (342, 216)], 'ca', 'ag', 'main', 'agent', flow=True)
    E([(342, 272), (342, 312)], 'ag', 'ai', 'main', 'ai', flow=True)
    E([(342, 368), (342, 408)], 'ai', 'tel')
    E([(432, 166), (444, 166), (444, 328), (432, 328)], 'ca', 'ai', r=6)
    E([(432, 148), (496, 148)], 'ca', 'tui')
    E([(432, 148), (464, 148), (464, 212), (496, 212)], 'ca', 'mcp')
    E([(432, 148), (464, 148), (464, 276), (496, 276)], 'ca', 'cm')
    f.raw('<circle class="fillc c-infra jn" cx="464" cy="148" r="2.6" style="fill:var(--dg-edge)"/>', 'label')
    E([(850, 176), (850, 216)], 'srv', 'prot')
    E([(950, 176), (950, 216)], 'cli', 'prot')
    E([(910, 340), (890, 340)], 'env', 'dur')
    E([(720, 352), (432, 352)], 'dur', 'ai', label=('pi-durable → pi-ai', 'pi-durable → pi-ai'), lpos=(600, 352))
    E([(252, 132), (24, 132), (24, 520)], 'ca', 'ch', r=10)
    E([(1000, 392), (1000, 520)], None, 'ch', label=('5 个包都依赖 chord', 'all 5 depend on chord'), lpos=(1000, 456), lmono=False)
    E([(122, 312), (122, 164), (252, 164)], 'ev', 'ca', 'dev', label='dev', lpos=(122, 238))
    E([(204, 340), (252, 340)], 'ev', 'ai', 'dev')
    E([(400, 120), (400, 60), (1040, 60), (1040, 84)], 'ca', None, 'dev',
      label=('devDependencies（仅测试）：pi-server · pi-client · pi-protocol', 'devDependencies (tests only): pi-server · pi-client · pi-protocol'), lpos=(720, 60), lmono=False)
    f.legend(24, 600, [('dep', ('dependency（运行时依赖）', 'dependency')), ('dev', ('devDependency（开发依赖）', 'devDependency')),
                       ('main', ('四层运行时栈', 'the 4-deep runtime stack')), ('layer:coding', 'pi-coding-agent'), ('layer:agent', 'pi-agent-core'),
                       ('layer:ai', 'pi-ai'), ('layer:tui', 'pi-tui'), ('layer:infra', ('其他包', 'other packages'))])
    return f


# ============================================================== 2. layers
@reg
def layers():
    f = Fig('layers', 1120, 760, ('分层架构', 'Layered architecture'))
    W0, W1 = 24, 852          # main column; pi-tui column 876..1096
    # actors
    acts = [('rpc', 'braces', ('宿主应用 / IDE', 'Host app / IDE'), 'JSONL'), ('print', 'terminal', ('脚本 / CI', 'Scripts / CI'), 'pipe'), ('im', 'user', ('开发者', 'Developer'), 'TTY')]
    xs = [44, 320, 596]
    for (k, ic, lab, io), x in zip(acts, xs):
        f.node('u-' + k, x + 33, 18, 190, 36, 'infra', lab, None, ic, mono=False, kind='pill', tsize=12, tag=io)
    f.group(W0, 76, W1 - W0, 100, 'modes', ('运行模式', 'RUN MODES'), ('共享同一个运行时', 'all share one runtime'), 'play', title_mono=False)
    f.node('rpc', 44, 112, 256, 50, 'modes', 'runRpcMode()', ('33 种 JSONL 命令 · 事件', '33 JSONL commands · events'), 'braces')
    f.node('print', 320, 112, 256, 50, 'modes', 'runPrintMode()', ('text · json，一次性', 'text · json, one-shot'), 'terminal')
    f.node('im', 596, 112, 236, 50, 'modes', 'InteractiveMode', ('编辑器 · 聊天视图 · /命令', 'editor · chat view · /commands'), 'user', strong=True)
    for k, x in zip(('rpc', 'print', 'im'), xs):
        f.edge([(x + 128 if k != 'im' else x + 118, 54), (x + 128 if k != 'im' else x + 118, 112)], 'u-' + k, k, 'faint')
    # pi-coding-agent
    f.group(W0, 200, W1 - W0, 262, 'coding', 'pi-coding-agent', ('会话编排', 'session orchestration'), 'terminal')
    f.node('asr', 44, 236, 788, 40, 'coding', 'AgentSessionRuntime', ('持有当前会话 · newSession() · switchSession() · fork() 时整体替换', 'owns the current session · replaced wholesale on newSession() · switchSession() · fork()'), None, tsize=12.5, strong=True)
    f.group(44, 296, 788, 150, 'coding', 'AgentSession', ('prompt() · steer() · followUp() · compact() · bindExtensions()', 'prompt() · steer() · followUp() · compact() · bindExtensions()'), gid='as')
    comps = [('sm', 'coding', 'SessionManager', ('只追加的 JSONL 树', 'append-only JSONL tree'), 'db'),
             ('er', 'ext', 'ExtensionRunner', ('41 种事件 · register*', '41 events · register*'), 'plug'),
             ('tools', 'coding', ('8 个内置工具', '8 built-in tools'), 'read · bash · edit · write …', 'tool'),
             ('cp', 'coding', 'compaction', ('摘要 + 保留尾部', 'summary + kept tail'), 'compress'),
             ('mr', 'coding', 'ModelRuntime', ('实现 pi-ai 的 Models', 'implements pi-ai Models'), 'key'),
             ('rl', 'coding', 'ResourceLoader', ('扩展 · skills · prompts', 'extensions · skills · prompts'), 'file')]
    for i, (k, l, t, sub, ic) in enumerate(comps):
        cx = 60 + (i % 3) * 256; cy = 336 + (i // 3) * 54
        f.node(k, cx, cy, 244, 44, l, t, sub, ic, mono=not isinstance(t, tuple), tsize=12.5)
    # pi-agent-core
    f.group(W0, 486, W1 - W0, 150, 'agent', 'pi-agent-core', None, 'loop')
    f.node('agent', 44, 534, 228, 58, 'agent', 'Agent', ('状态 · 两个消息队列', 'state · two message queues'), 'cpu', strong=True)
    f.node('loop', 316, 534, 252, 58, 'agent', 'runLoop()', ('内层 + 外层循环', 'inner + outer loop'), 'loop', strong=True)
    f.group(596, 506, 236, 118, 'agent', ('AgentSession 注入的钩子', 'hooks set by AgentSession'), None, None, gid='hooks', dashed=True, title_mono=False)
    hooks = [['transformContext', 'convertToLlm'], ['prepareNextTurn', 'prepareRequest'], ['beforeToolCall', 'afterToolCall'], ['finishTurn']]
    for r, row in enumerate(hooks):
        x = 608
        for h in row:
            x += f.chip(x, 540 + r * 21, h, 'agent', size=10, h=17) + 5
    # pi-ai
    f.group(W0, 660, 1096 - W0, 88, 'ai', 'pi-ai', None, 'spark')
    f.node('models', 44, 690, 200, 46, 'ai', 'Models', ('getModel · checkAuth', 'getModel · checkAuth'), 'hub', strong=True)
    f.node('prov', 272, 690, 200, 46, 'ai', 'providers/*', ('42 个内置 provider', '42 built-in providers'), 'globe')
    f.node('api', 500, 690, 200, 46, 'ai', 'api/*.lazy.ts', ('10 种对话 API · 懒加载', '10 chat APIs · lazy'), 'braces')
    f.node('es', 728, 690, 348, 46, 'ai', 'AssistantMessageEventStream', ('start · text_* · thinking_* · toolcall_* · done · error', 'start · text_* · thinking_* · toolcall_* · done · error'), 'stream', strong=True)
    # pi-tui column
    f.group(876, 76, 220, 386, 'tui', 'pi-tui', ('仅 interactive', 'interactive only'), 'monitor')
    tn = [('tui1', 'TuiMainScreen', ('主屏 · 保留 scrollback', 'main buffer · scrollback')), ('tui2', 'TuiAltScreen', ('备用屏 · 全屏', 'alt screen · fullscreen')),
          ('tui3', 'Component', 'render(width) → string[]'), ('tui4', 'ProcessTerminal', ('StdinBuffer → 按键', 'StdinBuffer → keys'))]
    for i, (k, t, sub) in enumerate(tn):
        f.node(k, 892, 112 + i * 58, 188, 46, 'tui', t, sub, None, tsize=12.5)
    cx = 892
    for i, c in enumerate(['Editor', 'Markdown', 'SelectList', 'Loader', 'Image', 'ScrollView']):
        if i == 3: cx = 892
        cx += f.chip(cx, 352 + (i // 3) * 24, c, 'tui', size=10, h=18) + 5
    f.note(892, 414, ('内置组件，还有 Input、Stack …', 'built-ins, plus Input, Stack …'), 10.5)
    # edges: request path
    for k, x in (('rpc', 172), ('print', 448)):
        f.edge([(x, 162), (x, 236)], k, 'asr', 'dep', start=True)
    f.edge([(714, 162), (714, 236)], 'im', 'asr', 'main', 'modes', start=True, label=('prompt ↓ · 事件 ↑', 'prompt ↓ · events ↑'), lpos=(714, 199), lmono=False, step=1, spos=(714, 176))
    f.edge([(832, 137), (892, 137)], 'im', 'tui1', 'main', 'tui')
    f.edge([(438, 276), (438, 296)], 'asr', 'as', 'dep')
    f.edge([(230, 446), (230, 534)], 'as', 'agent', 'main', 'agent', flow=True, label='agent.prompt()', lpos=(230, 466), step=2, spos=(230, 516))
    f.edge([(272, 563), (316, 563)], 'agent', 'loop', 'main', 'agent', flow=True)
    f.edge([(714, 446), (714, 506)], 'as', 'hooks', 'dev', label=('注入', 'installs'), lpos=(714, 476), lmono=False)
    f.edge([(392, 592), (392, 648), (214, 648), (214, 690)], 'loop', 'models', 'main', 'ai', flow=True, label='streamFn = modelRuntime.streamSimple()', lpos=(300, 648), step=3, spos=(392, 612))
    f.edge([(244, 713), (272, 713)], 'models', 'prov', 'main', 'ai')
    f.edge([(472, 713), (500, 713)], 'prov', 'api', 'main', 'ai', step=4, spos=(486, 690))
    f.edge([(700, 713), (728, 713)], 'api', 'es', 'main', 'ai')
    f.edge([(902, 690), (902, 648), (520, 648), (520, 592)], 'es', 'loop', 'event', 'ai', label=('事件流回到循环', 'events back to the loop'), lpos=(720, 648), lmono=False, step=5, spos=(902, 670))
    return f

# ============================================================== 3. loop
@reg
def loop():
    f = Fig('loop', 1120, 620, ('Agent 循环', 'Agent loop'))
    LX, RX, CW = 250, 660, 290
    T, B, E = 116, 296, 448          # rows: ring top, ring bottom, exit row
    H = 64
    f.node('start', 24, T + 4, 196, 56, 'term', 'runLoop()', ('prompt() / continue()', 'prompt() / continue()'), 'play', kind='term')
    f.group(16, 250, 212, 334, 'coding', ('消息队列', 'MESSAGE QUEUES'), None, 'queue', title_mono=False)
    f.node('sq', 32, B, 180, H, 'coding', ('Steering 队列', 'Steering queue'), 'agent.steer()', 'inbox', mono=False)
    f.node('fq', 32, E, 180, H, 'coding', ('Follow-up 队列', 'Follow-up queue'), 'agent.followUp()', 'inbox', mono=False)
    f.note(32, 548, ('用户在 Agent 运行时输入', 'typed while the agent runs'), 10.5)
    f.note(32, 564, ('模式：one-at-a-time（默认）| all', 'mode: one-at-a-time (default) | all'), 10.5)
    f.node('a', LX, T, CW, H, 'agent', ('注入待处理消息', 'Inject pending messages'), ('prepared + steering → message_start/end', 'prepared + steering → message_start/end'), 'msg', mono=False, strong=True)
    f.node('b', RX, T, CW + 20, H, 'agent', 'streamAssistantResponse()', ('transformContext → convertToLlm → streamFn', 'transformContext → convertToLlm → streamFn'), 'spark', strong=True, ssize=11)
    f.node('c', RX, B, CW + 20, H, 'agent', 'executeToolCalls()', ('sequential | parallel · length → 全部失败', 'sequential | parallel · length → all fail'), 'tool', strong=True)
    f.node('d', LX, B, CW, H, 'coding', 'finishTurn() · turn_end', ('决策 end | continue，再轮询 steering', 'decision end | continue, then poll steering'), 'flag', strong=True)
    f.node('e', LX, E, CW, H, 'coding', 'getFollowUpMessages()', ('Agent 本该停止时才检查', 'checked only when the agent would stop'), 'inbox')
    f.node('end', RX, E, CW + 20, H, 'term', 'agent_end', ('运行结束，回到 idle', 'run finished → idle'), 'check', kind='term')
    # ring
    f.edge([(220, T + 32), (LX, T + 32)], 'start', 'a', 'main', 'accent', step=0, spos=(235, T + 32))
    f.edge([(LX + CW, T + 32), (RX, T + 32)], 'a', 'b', 'main', 'agent', flow=True, step=1, spos=(LX + CW + 18, T + 32))
    f.edge([(RX + 145, T + H), (RX + 145, B)], 'b', 'c', 'main', 'agent', flow=True, label=('有工具调用', 'tool calls'), lpos=(RX + 145, (T + H + B) / 2), lmono=False, step=2, spos=(RX + 145, T + H + 16))
    f.edge([(RX, B + 40), (LX + CW, B + 40)], 'c', 'd', 'main', 'agent', flow=True, step=3, spos=(RX - 18, B + 40))
    f.edge([(RX, T + 50), (RX - 24, T + 50), (RX - 24, B + 16), (LX + CW, B + 16)], 'b', 'd', 'dep', label=('无工具调用', 'no tool calls'), lpos=(LX + CW + 46, B + 16), lmono=False, r=8, lsize=10)
    f.edge([(LX + 145, B), (LX + 145, T + H)], 'd', 'a', 'main', 'agent', flow=True, label='prepareNextTurn() · turn_start', lpos=(LX + 145, 210), step=4, spos=(LX + 145, B - 16))
    f.note(LX + 135, 244, ('仍有工具调用 / steering', 'tool calls or steering left'), 10.5, anchor='end')
    # queues
    f.edge([(212, B + 32), (LX, B + 32)], 'sq', 'd', 'event', 'coding', label=('轮询', 'poll'), lpos=(231, B + 14), lmono=False)
    f.edge([(212, E + 32), (LX, E + 32)], 'fq', 'e', 'event', 'coding')
    # exits
    f.edge([(LX + 60, B + H), (LX + 60, E)], 'd', 'e', 'dep', label=('都没有', 'neither'), lpos=(LX + 60, (B + H + E) / 2), lmono=False)
    f.edge([(LX + 230, B + H), (LX + 230, 400), (RX + 60, 400), (RX + 60, E)], 'd', 'end', 'dep', label=('决策 = end', 'decision = end'), lpos=(555, 400), lmono=False)
    f.edge([(LX + CW, E + 40), (RX, E + 40)], 'e', 'end', 'dep', label=('无 follow-up', 'none queued'), lpos=(600, E + 40), lmono=False)
    f.edge([(RX + CW + 20, T + 20), (RX + CW + 66, T + 20), (RX + CW + 66, E + 32), (RX + CW + 20, E + 32)], 'b', 'end', 'err', label=('error / aborted', 'error / aborted'), lpos=(RX + CW + 66, 238), lmono=True, lcls='err', lsize=10)
    f.edge([(LX + 145, E + H), (LX + 145, 588), (1104, 588), (1104, 76), (LX + 200, 76), (LX + 200, T)], 'e', 'a', 'main', 'coding', flow=True, r=14,
           label=('外层循环：follow-up 到达（或 finishTurn → continue）', 'outer loop: follow-ups arrived (or finishTurn → continue)'), lpos=(800, 588), lmono=False, step=5, spos=(LX + 145, E + H + 16))
    # center label
    f.raw(icon('loop', 589, 196, 22, 'ico c-agent'), 'label')
    f.text(600, 238, ('内层', 'inner'), 12, 650, anchor='middle', cls='cf c-agent', layer='label')
    f.text(600, 253, ('循环', 'loop'), 12, 650, anchor='middle', cls='cf c-agent', layer='label')
    return f

# ============================================================== 4. tool execution
@reg
def toolexec():
    f = Fig('toolexec', 1120, 610, ('工具调用执行', 'Tool call execution'))
    Y, H = 218, 72
    st = [('find', ('查找工具', 'Find tool'), 'tools.find(name)', 'filter', 'agent'),
          ('prep', ('准备参数', 'Prepare args'), 'prepareArguments()', 'gear', 'agent'),
          ('val', ('校验', 'Validate'), 'validateToolArguments()', 'shield', 'agent'),
          ('before', 'beforeToolCall()', ('ext · tool_call', 'ext · tool_call'), 'plug', 'ext'),
          ('exec', 'tool.execute()', '(…, signal, onUpdate)', 'play', 'agent'),
          ('after', 'afterToolCall()', ('ext · tool_result', 'ext · tool_result'), 'plug', 'ext'),
          ('fin', ('完成', 'Finish'), 'tool_execution_end', 'check', 'agent')]
    ws = [114, 136, 160, 146, 156, 140, 142]
    gap = (1120 - 48 - sum(ws)) / 6
    xs = []; x = 24
    for w in ws: xs.append(x); x += w + gap
    for i, ((k, t, sub, ic, l), x, w) in enumerate(zip(st, xs, ws)):
        f.node(k, x, Y, w, H, l, t, sub, None, mono=not isinstance(t, tuple), strong=True, tsize=12.5, ssize=10.5)
        f.step(i + 1, x + 2, Y + 2, l, onnode=True)
    f.chip(xs[4] + 8, Y + H - 2, 'executionMode', 'agent', size=9, h=15, cls='plain') if False else None
    for i in range(6):
        a, b = st[i][0], st[i + 1][0]
        f.edge([(xs[i] + ws[i], Y + 36), (xs[i + 1], Y + 36)], a, b, 'main', st[i + 1][4] if st[i+1][4] == 'ext' else 'agent', flow=True)
    # entry + output
    f.node('tc', 24, 108, 200, 46, 'term', 'toolCall', ('来自 assistant 消息', 'from assistant message'), 'msg', kind='term', tsize=12.5)
    f.edge([(84, 154), (84, Y)], 'tc', 'find', 'main', 'accent', label='tool_execution_start', lpos=(150, 186), lsize=10)
    f.node('trm', xs[6] - 58, 108, 200, 46, 'term', 'ToolResultMessage', ('message_start / end', 'message_start / end'), 'file', kind='term', tsize=12.5)
    f.edge([(xs[6] + 71, Y), (xs[6] + 71, 154)], 'fin', 'trm', 'main', 'accent')
    # extensions lane
    f.group(xs[3] - 10, 28, xs[5] + ws[5] - xs[3] + 20, 112, 'ext', ('扩展（经 ExtensionRunner）', 'EXTENSIONS (via ExtensionRunner)'), None, 'plug', title_mono=False, gid='extg')
    f.node('tcall', xs[3], 66, ws[3], 56, 'ext', 'tool_call', ('可阻止 · block', 'may block'), None, tsize=12, kind='tint')
    f.node('tres', xs[5], 66, ws[5], 56, 'ext', 'tool_result', ('可改写结果', 'may rewrite result'), None, tsize=12, kind='tint')
    f.node('upd', xs[4] - 4, 66, ws[4] + 8, 56, 'modes', 'tool_execution_update', ('流式输出 · 例如 bash', 'streamed output, e.g. bash'), None, tsize=10.5, ssize=10, kind='tint')
    f.edge([(xs[3] + 50, Y), (xs[3] + 50, 122)], 'before', 'tcall', 'event', 'ext', start=True)
    f.edge([(xs[5] + 50, Y), (xs[5] + 50, 122)], 'after', 'tres', 'event', 'ext', start=True)
    f.edge([(xs[4] + 78, Y), (xs[4] + 78, 122)], 'exec', 'upd', 'event', 'modes', label='onUpdate', lpos=(xs[4] + 78, 170), lsize=10)
    # error lane
    ey = 372
    f.node('err', 24, ey, xs[3] + ws[3] - 24, 48, 'err', 'createErrorToolResult(message)', ('isError: true —— 失败是结果，不是异常', 'isError: true — a failure is a result, never a throw'), 'x', kind='err', tsize=12.5)
    f.edge([(xs[0] + 58, Y + H), (xs[0] + 58, ey)], 'find', 'err', 'err', label=('未找到', 'not found'), lpos=(xs[0] + 58, 331), lmono=False, lcls='err')
    f.edge([(xs[1] + 68, Y + H), (xs[1] + 68, ey)], 'prep', 'err', 'err', label=('抛错', 'throws'), lpos=(xs[1] + 68, 331), lmono=False, lcls='err')
    f.edge([(xs[2] + 80, Y + H), (xs[2] + 80, ey)], 'val', 'err', 'err', label=('不合法', 'invalid'), lpos=(xs[2] + 80, 331), lmono=False, lcls='err')
    f.edge([(xs[3] + 67, Y + H), (xs[3] + 67, ey)], 'before', 'err', 'err', label=('block / abort', 'block / abort'), lpos=(xs[3] + 67, 331), lcls='err')
    f.edge([(xs[3] + ws[3], ey + 24), (xs[6] + 71, ey + 24), (xs[6] + 71, Y + H)], 'err', 'fin', 'err', label=('跳过 afterToolCall', 'skips afterToolCall'), lpos=(xs[5] + 30, ey + 24), lmono=False, lcls='err')
    f.node('thr', xs[4] + 14, 312, ws[4] - 28, 34, 'err', ('execute 抛错', 'execute throws'), ('→ isError 结果', '→ isError result'), None, mono=False, kind='err', tsize=11, ssize=10, align='center')
    f.edge([(xs[4] + 78, Y + H), (xs[4] + 78, 312)], 'exec', 'thr', 'err')
    f.edge([(xs[4] + ws[4] - 14, 329), (xs[5] + 64, 329), (xs[5] + 64, Y + H)], 'thr', 'after', 'err', label=('仍经过 after', 'still runs after'), lpos=(xs[5] + 64, 305), lmono=False, lcls='err') if False else \
        f.edge([(xs[4] + ws[4] - 14, 329), (xs[5] + 64, 329), (xs[5] + 64, Y + H)], 'thr', 'after', 'err')
    # batch strip
    by = 448
    f.group(24, by, 1072, 148, 'agent', ('一批工具调用', 'A BATCH OF TOOL CALLS'), ('assistant 消息含多个 toolCall 时', 'when one assistant message has several tool calls'), 'stack', title_mono=False)
    lab_x = 44
    rows = [('sequential', by + 62), ('parallel', by + 110)]
    for name, yy in rows:
        f.text(lab_x, yy + 4, name, 12, 650, True, cls='cf c-agent', layer='label')
    def bar(x, y, w, kind, txt):
        cls = {'p': 'c-ext', 'x': 'c-agent', 'r': 'c-ai'}[kind]
        f.raw(f'<g class="{cls}"><rect class="fillcb" x="{x}" y="{y-11}" width="{w}" height="22" rx="5"/></g>', 'node')
        f.text(x + w / 2, y + 4, txt, 10, 600, True, 'middle', cls='cf ' + cls, layer='label')
    X0 = 150
    x = X0
    for i in (1, 2, 3):
        bar(x, rows[0][1], 66, 'p', f'prep {i}'); x += 70
        bar(x, rows[0][1], 92, 'x', f'exec {i}'); x += 96
        bar(x, rows[0][1], 52, 'r', f'msg {i}'); x += 64
    x = X0
    for i in (1, 2, 3):
        bar(x, rows[1][1], 66, 'p', f'prep {i}'); x += 70
    ex = [(x, 150), (x, 92), (x, 120)]
    order = []
    for i, (sx, w) in enumerate(ex):
        f.raw(f'<g class="c-agent"><rect class="fillcb" x="{sx}" y="{rows[1][1]-11 + (i-1)*0}" width="{w}" height="22" rx="5" opacity="{1 - i*0.0}"/></g>', 'node') if False else None
    # parallel exec drawn as three thin concurrent tracks
    for i, w in enumerate((150, 92, 120)):
        yy = rows[1][1] - 13 + i * 9
        f.raw(f'<g class="c-agent"><rect class="fillcb" x="{x}" y="{yy}" width="{w}" height="7" rx="3.5"/></g>', 'node')
        f.raw(f'<g class="c-agent"><circle class="fillc" cx="{x + w}" cy="{yy + 3.5}" r="3"/></g>', 'node')
    f.text(x + 4, rows[1][1] + 26, ('并发执行 · 每个完成即发 tool_execution_end', 'run concurrently · tool_execution_end as each finishes'), 10, 500, cls='faint', layer='label')
    x2 = x + 160
    for i in (1, 2, 3):
        bar(x2, rows[1][1], 52, 'r', f'msg {i}'); x2 += 56
    f.text(x2 + 8, rows[1][1] + 4, ('结果按原顺序发出', 'results in source order'), 10.5, 550, cls='muted', layer='label')
    f.note(1080, by + 28, ('任一工具声明 executionMode: "sequential" → 整批串行', 'any tool with executionMode: "sequential" serializes the batch'), 10.5, anchor='end')
    lx = 806
    for kind, lab in (('p', ('准备（含 beforeToolCall）', 'prepare (incl. beforeToolCall)')), ('x', ('执行', 'execute')), ('r', 'ToolResultMessage')):
        cls = {'p': 'c-ext', 'x': 'c-agent', 'r': 'c-ai'}[kind]
    return f

def build_all():
    import figs2  # noqa: registers diagrams 5-12
    import figs3  # noqa: pi-agent-core deep dive (ac_*)
    try:
        import figs4  # noqa: pi-ai deep dive (ai_*)
    except ModuleNotFoundError:
        pass
    for m in ('figs5', 'figs6', 'figs7', 'figs8'):  # coding-agent (ca_*), tui (tui_*), mcp (mcp_*), codemode (cm_*)
        try: __import__(m)
        except ModuleNotFoundError: pass
    out = {}
    for k, fn in FIG.items():
        out[k] = fn()
    return out
