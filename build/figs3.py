"""pi-agent-core deep-dive diagrams (ac_*). Facts read from /workspace/pi-src/packages/agent at build time."""
import re
from svgkit import Fig, maxw, tw, icon, pair
from figs import reg
from figkit import SRC, uml, codebox, bar, dot, hline, vline, chiprow, lines_of

AG = 'packages/agent/'
def _src(p): return (SRC / (AG + p)).read_text()

# ============================================================== ac_arch : modules & public API
@reg
def ac_arch():
    f = Fig('ac_arch', 1120, 640, ('pi-agent-core 模块结构', 'pi-agent-core modules'))
    R = [88, 180, 272, 364, 456]; H = 64
    AX, AW, BX, BW, CX, CW, DX, DW = 24, 180, 236, 130, 400, 300, 744, 352
    # consumers
    f.node('ca', AX, R[0], AW, H, 'coding', 'pi-coding-agent', 'AgentSession · sdk.ts', None, strong=True)
    f.node('app', AX, R[1], AW, H, 'infra', ('你的应用', 'your app'), 'new Agent({ streamFn })', None, mono=False)
    f.node('host', AX, R[2], AW, H, 'infra', ('宿主运行时', 'host runtime'), 'setDefaultStreamFn(fn)', None, mono=False)
    tests = {p.name: len(re.findall(r'^\s*(?:it|test)\(', p.read_text(), re.M)) for p in (SRC / AG / 'test').glob('*.test.ts')}
    f.node('test', AX, R[4], AW, H, 'infra', 'test/', (f'{len(tests)} 个文件 · {sum(tests.values())} 个用例', f'{len(tests)} files · {sum(tests.values())} cases'), None)
    f.text(AX, 70, ('使用方', 'CONSUMERS'), 10.5, 700, cls='faint', layer='label', ls='.08em')
    # index
    f.node('idx', BX, R[0], BW, R[4] + H - R[0], 'agent', 'index.ts', 'export *', None, align='center', strong=True)
    f.text(BX, 70, ('入口', 'ENTRY'), 10.5, 700, cls='faint', layer='label', ls='.08em')
    # modules
    f.group(CX - 16, 52, CW + 32, R[4] + H - 52 + 16, 'agent', 'src/', ('6 个文件', '6 files'), 'box', gid='src')
    mods = [('agent', 'agent.ts', 'class Agent · AgentOptions', ('PendingMessageQueue ×2（私有）', 'PendingMessageQueue ×2 (private)'), 'cpu'),
            ('loop', 'agent-loop.ts', 'agentLoop() · agentLoopContinue()', 'runAgentLoop*() · runToolCall()', 'loop'),
            ('sfn', 'stream-fn.ts', ('setDefaultStreamFn()（导出）', 'setDefaultStreamFn() (exported)'), ('getDefaultStreamFn()（内部）', 'getDefaultStreamFn() (internal)'), 'plug'),
            ('proxy', 'proxy.ts', 'streamProxy(model, ctx, opts)', 'ProxyAssistantMessageEvent', 'globe'),
            ('types', 'types.ts', 'AgentEvent · AgentTool · AgentState', 'AgentLoopConfig · StreamFn · hooks', 'braces')]
    for (k, t, s1, s2, ic), y in zip(mods, R):
        n = lines_of(AG + 'src/' + t)
        f.node(k, CX, y, CW, H, 'agent', t, s1, ic, sub2=s2, strong=k in ('agent', 'loop'), tag=f'{n} L', ssize=11)
    # pi-ai
    f.group(DX - 16, 52, DW + 16 + 8, R[4] + H - 52 + 16, 'ai', '@earendil-works/pi-ai', ('唯一的运行时依赖', 'the only runtime dependency'), 'spark', gid='ai')
    DXn, DWn = DX, DW - 8
    f.node('tr', DXn, R[0], DWn, H, 'ai', 'utils/transcript.ts', 'createInitialSystemMessage · getCurrentTools', None, sub2='getToolStateChanges · toToolDeclaration', ssize=11)
    f.node('val', DXn, R[1], DWn, H, 'ai', 'utils/validation.ts', 'validateToolArguments(tool, toolCall)', None, sub2=('TypeBox 模式校验 · 失败即抛出', 'TypeBox schema check · throws on failure'), ssize=11)
    f.node('es', DXn, R[2], DWn, R[3] + H - R[2], 'ai', 'utils/event-stream.ts', ('EventStream<T, R> → agentLoop() 的返回值', 'EventStream<T, R> → what agentLoop() returns'),
           None, sub2='AssistantMessageEventStream → streamProxy()', ssize=11)
    f.node('ty', DXn, R[4], DWn, H, 'ai', 'types.ts', 'Model · Message · Tool · Usage', None, sub2='SimpleStreamOptions · TranscriptContext', ssize=11)
    E = f.edge
    for k, y in (('ca', R[0]), ('app', R[1]), ('host', R[2]), ('test', R[4])):
        E([(AX + AW, y + 32), (BX, y + 32)], k, 'idx', 'dep')
    for (k, *_), y in zip(mods, R):
        E([(BX + BW, y + 32), (CX, y + 32)], 'idx', k, 'main' if k in ('agent', 'loop') else 'dep', 'agent' if k in ('agent', 'loop') else None)
    E([(CX + 150, R[0] + H), (CX + 150, R[1])], 'agent', 'loop', 'main', 'agent', label='runAgentLoop()', lpos=(CX + 150, (R[0] + H + R[1]) / 2), lsize=10, flow=True)
    E([(CX + 150, R[1] + H), (CX + 150, R[2])], 'loop', 'sfn', 'dep', label=('未传 streamFn 时', 'when streamFn is omitted'), lpos=(CX + 150, (R[1] + H + R[2]) / 2), lsize=10, lmono=False)
    E([(CX + CW, R[0] + 32), (DXn, R[0] + 32)], 'agent', 'tr', 'dep', 'ai')
    E([(CX + CW, R[1] + 18), (DXn - 22, R[1] + 18), (DXn - 22, R[0] + 50), (DXn, R[0] + 50)], 'loop', 'tr', 'dep', 'ai', r=6)
    E([(CX + CW, R[1] + 34), (DXn, R[1] + 34)], 'loop', 'val', 'dep', 'ai')
    E([(CX + CW, R[1] + 50), (DXn - 22, R[1] + 50), (DXn - 22, R[2] + 40), (DXn, R[2] + 40)], 'loop', 'es', 'dep', 'ai', r=6)
    E([(CX + CW, R[3] + 32), (DXn, R[3] + 32)], 'proxy', 'es', 'dep', 'ai')
    E([(CX + CW, R[4] + 32), (DXn, R[4] + 32)], 'types', 'ty', 'dep', 'ai')
    # exports band
    y = 560
    f.raw(f'<rect class="band" x="16" y="{y-8}" width="1088" height="44" rx="10"/>', 'bg')
    f.text(32, y + 18, ('值导出', 'Value exports'), 11, 700, cls='strongt', layer='label')
    vals = ['Agent', 'agentLoop', 'agentLoopContinue', 'runAgentLoop', 'runAgentLoopContinue', 'runToolCall', 'streamProxy', 'setDefaultStreamFn']
    x = 132
    for v in vals: x += f.chip(x, y + 4, v, 'agent', size=10, h=20, cls='solid' if v == 'Agent' else '') + 6
    ntypes = sum(len(re.findall(r'^export (?:type|interface) ', _src('src/' + m), re.M)) for m in ('types.ts', 'agent.ts', 'agent-loop.ts', 'proxy.ts'))
    f.text(1088, y + 18, (f'+ {ntypes} 个导出类型', f'+ {ntypes} exported types'), 11, 600, cls='muted', layer='label', anchor='end')
    f.legend(24, 622, [('main', ('主路径', 'main path')), ('dep', ('import / 再导出', 'import / re-export')), ('layer:agent', 'pi-agent-core'), ('layer:ai', 'pi-ai'), ('layer:coding', 'pi-coding-agent'), ('layer:infra', ('其他', 'other'))])
    return f

# ============================================================== ac_state : run lifecycle state machine
@reg
def ac_state():
    f = Fig('ac_state', 1120, 610, ('Agent 运行状态机', 'Agent run state machine'))
    Y1, Y2, Y3, H = 96, 244, 372, 68
    f.node('abort', 580, 20, 220, 44, 'err', 'abort()', ('中止信号 → 流与工具', 'signal → stream & tools'), 'x', tsize=12, kind='tint')
    f.node('idle', 24, Y1, 196, H, 'term', ('空闲', 'Idle'), 'activeRun = undefined', 'check', kind='term', mono=False)
    f.node('run', 350, Y1, 196, H, 'agent', 'runWithLifecycle()', 'isStreaming = true', sub2='new AbortController()', strong=True, ssize=11)
    f.node('stream', 580, Y1, 220, H, 'agent', ('流式响应', 'Streaming response'), 'streamingMessage = partial', 'spark', mono=False, sub2='message_start · _update', strong=True, ssize=10.5)
    f.node('settle', 880, Y1, 216, H, 'coding', ('收尾', 'Settling'), ('await agent_end 监听器', 'await agent_end listeners'), 'clock', mono=False, sub2=('isStreaming 仍为 true', 'isStreaming still true'), ssize=10.5)
    f.node('tools', 580, Y2, 220, H, 'agent', ('执行工具', 'Executing tools'), 'pendingToolCalls ∪ {id}', 'tool', mono=False, sub2='tool_execution_start · _end', strong=True, ssize=10.5)
    f.node('finish', 880, Y2, 216, H, 'coding', 'finishRun()', 'isStreaming = false', 'flag', sub2=('清空状态 · resolve 等待者', 'clear state · resolve waiters'), ssize=10.5)
    f.node('fail', 350, Y3, 196, H, 'err', 'handleRunFailure()', ('合成 error 助手消息', 'synthesize error message'), None, kind='err', sub2='message_* · turn_end · agent_end', ssize=10.5)
    E = f.edge
    E([(220, Y1 + 34), (350, Y1 + 34)], 'idle', 'run', 'main', 'accent', label='prompt · continue', lpos=(285, Y1 + 34), lsize=10, step=1, spos=(285, Y1 + 12))
    E([(546, Y1 + 34), (580, Y1 + 34)], 'run', 'stream', 'main', 'agent', flow=True, step=2, spos=(563, Y1 + 12))
    E([(650, Y1 + H), (650, Y2)], 'stream', 'tools', 'main', 'agent', label='toolCall', lpos=(650, (Y1 + H + Y2) / 2), lsize=10, flow=True)
    E([(740, Y2), (740, Y1 + H)], 'tools', 'stream', 'dep', 'agent', label='turn_start', lpos=(740, (Y1 + H + Y2) / 2), lsize=10)
    E([(800, Y1 + 34), (880, Y1 + 34)], 'stream', 'settle', 'main', 'coding', label='agent_end', lpos=(840, Y1 + 20), lsize=9.5, step=3, spos=(840, Y1 + 46))
    E([(988, Y1 + H), (988, Y2)], 'settle', 'finish', 'main', 'coding', label=('监听器全部完成', 'listeners settled'), lpos=(988, (Y1 + H + Y2) / 2), lmono=False, lsize=10, step=4, spos=(1050, (Y1 + H + Y2) / 2))
    E([(448, Y1 + H), (448, Y3)], 'run', 'fail', 'err', label=('executor 抛出', 'executor throws'), lpos=(448, 250), lmono=False, lcls='err', lsize=10)
    E([(546, Y3 + 34), (940, Y3 + 34), (940, Y2 + H)], 'fail', 'finish', 'err', label='finally', lpos=(743, Y3 + 34), lcls='err', lsize=10, r=8)
    E([(1040, Y2 + H), (1040, 470), (109, 470), (109, Y1 + H)], 'finish', 'idle', 'main', 'accent', label=('再次空闲 · waitForIdle() 返回', 'idle again · waitForIdle() resolves'), lpos=(575, 470), lmono=False, lsize=10, r=12, step=5, spos=(1040, Y2 + H + 22))
    E([(690, 64), (690, Y1)], 'abort', 'stream', 'err')
    # guards
    gy = 500
    f.group(16, gy, 1088, 96, 'agent', ('守卫与约束（agent.ts）', 'GUARDS (agent.ts)'), None, 'shield', title_mono=False, dashed=True)
    G = [('prompt()', ('运行中调用 → 抛错，提示改用 steer() / followUp()', 'while running → throws: use steer() / followUp()')),
         ('reset()', ('运行中调用 → 抛错；空闲时保留 system 基线、清空队列', 'throws while running; idle: keeps the system baseline, clears queues')),
         ('continue()', ('末条为 assistant → 先排空 steering，再 follow-up，否则抛错', 'last = assistant → drain steering, else follow-ups, else throw')),
         ('subscribe()', ('监听器按订阅顺序 await，并拿到本次运行的 signal', 'listeners awaited in order, each gets the run signal'))]
    for i, (k, d) in enumerate(G):
        x = 36 + (i % 2) * 540; y = gy + 50 + (i // 2) * 24
        f.text(x, y, k, 10.5, 650, True, cls='cf c-agent', layer='label')
        f.text(x + 92, y, d, 10.5, 450, False, cls='muted', layer='label')
    return f

# ============================================================== ac_turn : hook call order (sequence)
@reg
def ac_turn():
    lanes = [('loop', 'runLoop()', 'agent'), ('hk', ('AgentLoopConfig 钩子', 'AgentLoopConfig hooks'), 'coding'), ('sf', 'streamFn · pi-ai', 'ai'), ('tl', 'AgentTool', 'ext')]
    LC = {k: c for k, _, c in lanes}
    X = {'loop': 104, 'hk': 344, 'sf': 574, 'tl': 744}
    EVX = 836
    P = [(('开始', 'Start'), [
            ('loop', 'loop', 'declareToolChanges(prompts)', 's', 'agent_start · turn_start · message_*(user)'),
            ('loop', 'hk', 'getSteeringMessages()', 'c', '')]),
         (('请求 1', 'Request 1'), [
            ('loop', 'hk', 'prepareRequest(req, signal)', 'c', ''),
            ('loop', 'hk', 'transformContext(messages)', 'c', ''),
            ('loop', 'hk', 'convertToLlm(messages)', 'c', ''),
            ('loop', 'hk', 'getApiKey(provider)', 'c', ''),
            ('loop', 'sf', 'streamFn(model, normalizeContext(llm), opts)', 'c', 'message_start (assistant)'),
            ('sf', 'loop', 'text_* · thinking_* · toolcall_*', 'e', 'message_update ×n'),
            ('sf', 'loop', 'done(toolUse)', 'e', 'message_end (assistant)')]),
         (('工具', 'Tools'), [
            ('loop', 'tl', 'prepareArguments() → validate', 'c', 'tool_execution_start'),
            ('loop', 'hk', 'beforeToolCall(ctx, signal)', 'c', ''),
            ('loop', 'tl', 'execute(id, args, signal, onUpdate)', 'c', ''),
            ('tl', 'loop', 'onUpdate(partial) … result', 'e', 'tool_execution_update ×n'),
            ('loop', 'hk', 'afterToolCall(ctx, signal)', 'c', 'tool_execution_end · message_*(toolResult)')]),
         (('轮次结束', 'End of turn'), [
            ('loop', 'hk', 'finishTurn(turn, signal)', 'c', 'turn_end'),
            ('loop', 'hk', 'getSteeringMessages()', 'c', ''),
            ('loop', 'hk', 'prepareNextTurn(turn)', 'c', 'turn_start')]),
         (('请求 2 → 结束', 'Request 2 → end'), [
            ('loop', 'hk', 'prepareRequest → … → getApiKey', 'c', ''),
            ('loop', 'sf', 'streamFn(…)', 'c', 'message_start … message_end'),
            ('sf', 'loop', 'done(stop)', 'e', ''),
            ('loop', 'hk', 'finishTurn → getFollowUpMessages', 'c', 'turn_end · agent_end')])]
    RH, PH, Y0 = 24, 30, 104
    n = sum(len(m) for _, m in P)
    H = Y0 + n * RH + len(P) * PH + 44
    f = Fig('ac_turn', 1120, H, ('一次运行中的钩子调用顺序', 'Hook call order in one run'))
    yb = H - 32
    for k, t, l in lanes:
        x = X[k]
        f.raw(f'<line class="life" x1="{x}" y1="80" x2="{x}" y2="{yb}"/>', 'grp')
        f.node(k, x - 80, 40, 160, 40, l, t, None, None, mono=isinstance(t, str), tsize=11.5, strong=True, align='center', tweight=650)
    f.node('ev', EVX, 40, 1096 - EVX, 40, 'agent', ('emit → AgentEvent', 'emit → AgentEvent'), None, 'stream', mono=True, tsize=11.5, kind='tint')
    y = Y0; rows = []
    for pi_, (pl, msgs) in enumerate(P, 1):
        f.raw(f'<rect class="band" x="16" y="{y-2}" width="{EVX - 28}" height="{len(msgs)*RH + PH - 4}" rx="10"/>', 'bg')
        f.text(EVX - 20, y + 15, (f'{pi_} · {pl[0]}', f'{pi_} · {pl[1]}'), 10.5, 700, cls='faint', layer='label', ls='.04em', anchor='end')
        y += PH - 4
        for m in msgs: rows.append((y, m)); y += RH
    def act(k, y0, y1):
        f.raw(f'<g class="c-{LC[k]}"><rect class="act" x="{X[k]-4}" y="{y0}" width="8" height="{y1-y0}" rx="2"/></g>', 'band')
    act('loop', rows[0][0] + 2, rows[-1][0] + 14)
    for i, (yy, (a, b, lab, kind, ev)) in enumerate(rows, 1):
        yy += 10
        if kind == 's':
            x = X[a] + 4
            f.edge([(x, yy - 7), (x + 24, yy - 7), (x + 24, yy + 3), (x, yy + 3)], a, b, 'dep', r=4)
            f.step(i, x + 38, yy - 2, LC[a], r=7.5)
            f.text(x + 50, yy + 2, lab, 10.5, 500, True, cls='strongt', layer='label')
        else:
            dirn = 1 if X[b] > X[a] else -1
            x0 = X[a] + 4 * dirn; x1 = X[b] - 4 * dirn
            f.edge([(x0, yy), (x1, yy)], a, b, 'dep' if kind == 'c' else 'event', LC[b] if kind == 'c' else None)
            lw = maxw(lab, 10.5, 500, True); tot = lw + 20
            sx = (x0 + x1) / 2 - tot / 2 + 7.5
            if kind == 'c' and a == 'loop' and b == 'hk': sx = X['loop'] + 22
            f.step(i, sx, yy - 9, LC[a], r=7.5)
            f.text(sx + 12, yy - 5.5, lab, 10.5, 500, True, 'start', 'strongt' if kind == 'c' else 'muted', layer='label')
            if sx + 12 + lw > max(x0, x1) + 2: f.warn.append(f'ac_turn: label too long "{lab}"')
        if ev:
            f.raw(f'<line class="rule-d" x1="{EVX - 8}" y1="{yy - 3}" x2="{EVX}" y2="{yy - 3}"/>', 'band')
            f.chip(EVX + 4, yy - 13, ev, 'agent', size=9.5, h=19)
    f.legend(24, H - 14, [('dep', ('调用', 'call')), ('event', ('返回 / 流事件', 'return / stream event')), ('step', ('顺序编号，颜色 = 发起方', 'order · colour = caller'))])
    f.note(1096, H - 10, ('error / aborted → finishTurn → turn_end → agent_end，直接退出', 'error / aborted → finishTurn → turn_end → agent_end, hard exit'), 10.5, anchor='end')
    return f

# ============================================================== ac_events : AgentEvent catalogue + reducer
@reg
def ac_events():
    f = Fig('ac_events', 1120, 600, ('AgentEvent 事件流', 'AgentEvent stream'))
    # A: nesting
    f.group(16, 20, 682, 318, 'agent', 'agent_start … agent_end', ('一次运行', 'one run'), 'play', gid='run')
    f.group(32, 60, 650, 168, 'agent', 'turn_start … turn_end', ('第 1 轮：一次响应 + 其工具', 'turn 1 · one response + its tools'), 'loop', gid='t1')
    def row(y, items, label):
        f.text(48, y + 14, label, 10, 650, cls='faint', layer='label')
        chiprow(f, 144, y, items, size=9.5, h=20, gap=5)
    row(100, [('message_start', 'coding'), ('message_end', 'coding')], ('user 提示', 'user prompt'))
    row(128, [('message_start', 'ai'), ('message_update ×n', 'ai'), ('message_end', 'ai')], 'assistant')
    row(156, [('tool_execution_start', 'agent'), ('tool_execution_update ×n', 'agent'), ('tool_execution_end', 'agent')], ('每个工具调用', 'per tool call'))
    row(184, [('message_start', 'ext'), ('message_end', 'ext')], 'toolResult')
    f.group(32, 240, 650, 84, 'agent', 'turn_start … turn_end', ('第 2 轮：最终回答', 'turn 2 · final answer'), 'loop', gid='t2')
    row(282, [('message_start', 'ai'), ('message_update ×n', 'ai'), ('message_end', 'ai')], 'assistant')
    f.text(670, 296, 'stopReason: "stop"', 10, 550, True, cls='muted', layer='label', anchor='end')
    # B: reducer
    f.group(722, 20, 382, 318, 'coding', 'Agent.processEvents()', ('先归约，再 await 监听器', 'reduce, then await listeners'), 'cpu', gid='red')
    RD = [('message_start · _update', 'streamingMessage = message'),
          ('message_end', 'messages.push(message)'),
          ('tool_execution_start', 'pendingToolCalls ∪ {id}'),
          ('tool_execution_end', 'pendingToolCalls ∖ {id}'),
          ('turn_end', 'errorMessage ← message.errorMessage'),
          ('agent_end', 'streamingMessage = undefined')]
    for i, (e, s) in enumerate(RD):
        y = 64 + i * 40
        f.chip(738, y, e, 'agent', size=9.5, h=20)
        f.text(752, y + 34, '→ ' + s, 10.5, 500, True, cls='strongt', layer='label')
    f.note(738, 324, ('pendingToolCalls 每次替换为新 Set（便于 UI 比较）', 'pendingToolCalls is replaced with a new Set each time'), 10)
    # C: mapping from pi-ai
    y0 = 364
    f.group(16, y0, 1088, 206, 'ai', ('pi-ai 事件 → AgentEvent（streamAssistantResponse）', 'pi-ai events → AgentEvent (streamAssistantResponse)'), None, 'stream', title_mono=False, gid='map')
    top = ['start', 'text_start', 'text_delta', 'text_end', 'thinking_start', 'thinking_delta', 'thinking_end', 'toolcall_start', 'toolcall_delta', 'toolcall_end', 'done', 'error']
    xs = chiprow(f, 40, y0 + 52, [(t, 'err' if t == 'error' else 'ai') for t in top], size=9.5, h=21, gap=5)
    by = y0 + 132
    def node_under(cid, cx, w, t, sub):
        f.node(cid, cx - w / 2, by, w, 44, 'agent', t, sub, None, tsize=11.5, ssize=10, strong=True)
    cx0 = xs[0][0] + xs[0][1] / 2
    mid0, mid1 = xs[1][0], xs[9][0] + xs[9][1]
    cxm = (mid0 + mid1) / 2
    cxe = (xs[10][0] + xs[11][0] + xs[11][1]) / 2
    node_under('ms', cx0 + 60, 160, 'message_start', ('push(partial)', 'push(partial)'))
    node_under('mu', cxm, 330, 'message_update', ('{ message: {...partial}, assistantMessageEvent }', '{ message: {...partial}, assistantMessageEvent }'))
    node_under('me', cxe - 60, 200, 'message_end', ('result() + thinkingLevel', 'result() + thinkingLevel'))
    yb = y0 + 80
    def brace(x0, x1, ytop, xt, target):
        f.raw(f'<path class="rule" d="M{x0} {ytop}v6H{x1}v-6" style="fill:none;stroke:var(--dg-edge)"/>', 'band')
        f.edge([(xt, ytop + 6), (xt, by)], None, target, 'main', 'agent', flow=True)
    brace(xs[0][0] + 2, xs[0][0] + xs[0][1] - 2, yb, cx0, 'ms') if False else None
    f.edge([(cx0, yb), (cx0, by - 14), (cx0 + 60, by - 14), (cx0 + 60, by)], None, 'ms', 'main', 'agent', r=6)
    brace(mid0 + 2, mid1 - 2, yb, cxm, 'mu')
    f.raw(f'<path class="rule" d="M{xs[10][0]+2} {yb}v6H{xs[11][0]+xs[11][1]-2}v-6" style="fill:none;stroke:var(--dg-edge)"/>', 'band')
    f.edge([(cxe, yb + 6), (cxe, by - 14), (cxe - 60, by - 14), (cxe - 60, by)], None, 'me', 'main', 'agent', r=6)
    f.note(40, y0 + 196, ('若流在 start 之前就以 error 结束，循环会补发 message_start；最终消息替换上下文中的 partial', 'if the stream ends before start, the loop emits message_start itself; the final message replaces the partial in context'), 10)
    f.legend(24, 590, [('main', ('映射', 'maps to')), ('layer:coding', ('user 消息', 'user message')), ('layer:ai', ('assistant 消息', 'assistant message')), ('layer:agent', ('工具执行', 'tool execution')), ('layer:ext', ('toolResult 消息', 'toolResult message'))])
    return f

# ============================================================== ac_queues : steering & follow-up
@reg
def ac_queues():
    f = Fig('ac_queues', 1120, 560, ('Steering 与 Follow-up 队列', 'Steering and follow-up queues'))
    f.node('steer', 24, 84, 196, 56, 'modes', 'agent.steer(msg)', ('运行中插话', 'nudge mid-run'), 'user', tsize=12)
    f.node('follow', 24, 316, 196, 56, 'modes', 'agent.followUp(msg)', ('做完之后再…', 'after you finish…'), 'user', tsize=12)
    for gid, y, name in (('sq', 52, 'steeringQueue'), ('fq', 284, 'followUpQueue')):
        f.group(236, y, 316, 128, 'coding', name, 'PendingMessageQueue', 'queue', gid=gid)
        x = 252
        for m in ('m1', 'm2', 'm3'):
            x += f.chip(x, y + 46, m, 'coding', size=10, h=22) + 6
        f.text(x + 6, y + 61, ('← enqueue()', '← enqueue()'), 10, 500, True, cls='faint', layer='label')
        f.text(252, y + 92, ('one-at-a-time（默认）→ drain() 取 [m1]', 'one-at-a-time (default) → drain() takes [m1]'), 10.5, 500, cls='muted', layer='label')
        f.text(252, y + 110, ('all → drain() 取 [m1, m2, m3]', 'all → drain() takes [m1, m2, m3]'), 10.5, 500, cls='muted', layer='label')
    f.edge([(220, 112), (236, 112)], 'steer', 'sq', 'main', 'modes')
    f.edge([(220, 344), (236, 344)], 'follow', 'fq', 'main', 'modes')
    # drain points
    D = [('d1', 604, ('① 运行开始', '① run start'), ('初次轮询', 'initial poll')),
         ('d2', 772, ('② turn_end 之后', '② after turn_end'), ('除非 finishTurn → end', 'unless finishTurn → end')),
         ('d3', 940, '③ prepareNextTurn', ('之后 · 仅当 ② 为空', 'after it · only if ② empty'))]
    for k, x, t, s in D:
        f.node(k, x, 60, 156, 56, 'coding', t, s, None, mono=False, tsize=11.5, ssize=10, strong=True)
    f.node('d4', 940, 316, 156, 56, 'coding', ('④ 本该停止时', '④ would stop'), 'getFollowUpMessages()', None, mono=False, tsize=11.5, ssize=10, strong=True)
    f.edge([(552, 88), (604, 88)], 'sq', 'd1', 'event', 'coding')
    f.edge([(552, 150), (850, 150), (850, 116)], 'sq', 'd2', 'event', 'coding', r=6, label='getSteeringMessages()', lpos=(766, 150), lsize=10)
    f.edge([(552, 166), (1018, 166), (1018, 116)], 'sq', 'd3', 'event', 'coding', r=6)
    f.edge([(552, 344), (940, 344)], 'fq', 'd4', 'event', 'coding', label=('外层循环重新开始', 'restarts the outer loop'), lpos=(746, 344), lmono=False, lsize=10)
    # timeline axis
    ay = 232
    f.raw(f'<line x1="600" y1="{ay}" x2="1096" y2="{ay}" style="stroke:var(--dg-edge);stroke-width:1.5"/>', 'band')
    f.raw(f'<path d="M1096 {ay}l-8 -4.2q2 4.2 0 8.4z" style="fill:var(--dg-edge)"/>', 'band')
    segs = [(604, 760, ('请求 + 工具', 'request + tools'), 'agent'), (772, 928, 'turn_end', 'coding'), (940, 1080, ('下一轮', 'next turn'), 'agent')]
    for x0, x1, t, l in segs:
        bar(f, x0, ay - 30, x1 - x0, l, t, h=20, size=9.5, mono=isinstance(t, str))
    for k, x, y0 in (('d1', 682, 116), ('d2', 850, 150), ('d3', 1018, 166)):
        vline(f, x, y0, ay - 30)
    vline(f, 1018, ay + 4, 316)
    f.text(600, ay + 22, ('一次运行的时间轴', 'timeline of one run'), 10, 600, cls='faint', layer='label')
    f.note(604, 278, ('continue() 从 assistant 末尾恢复且有 steering 时，① 会被跳过一次（skipInitialSteeringPoll）', 'continue() resuming from an assistant tail with steering skips ① once (skipInitialSteeringPoll)'), 10)
    # API band
    by = 432
    f.group(16, by, 1088, 112, 'coding', ('队列 API（agent.ts）', 'QUEUE API (agent.ts)'), None, 'gear', title_mono=False, dashed=True)
    api = ['steer()', 'followUp()', 'clearSteeringQueue()', 'clearFollowUpQueue()', 'clearAllQueues()', 'hasQueuedMessages()', 'peekQueuedMessages()', 'steeringMode', 'followUpMode']
    chiprow(f, 32, by + 44, api, 'coding', size=10, h=21)
    f.note(32, by + 92, ('peekQueuedMessages() 优先返回 steering，否则 follow-up；reset() 会清空两个队列', 'peekQueuedMessages() returns steering first, else follow-ups; reset() clears both'), 10.5)
    return f

# ============================================================== ac_parallel : batch timing
@reg
def ac_parallel():
    f = Fig('ac_parallel', 1120, 560, ('一批工具调用的时序', 'Timing of a tool batch'))
    X0, X1, T = 196, 1080, 820
    sx = lambda ms: X0 + (X1 - X0) * ms / T
    calls = [('A', 'read', 120), ('B', 'bash', 380), ('C', 'grep', 60)]
    PREP, AFT = 30, 14
    # axis
    def axis(y):
        f.raw(f'<line x1="{X0}" y1="{y}" x2="{X1}" y2="{y}" style="stroke:var(--dg-edge-2);stroke-width:1"/>', 'band')
        for ms in range(0, T + 1, 100):
            f.raw(f'<line x1="{sx(ms):.1f}" y1="{y}" x2="{sx(ms):.1f}" y2="{y+4}" style="stroke:var(--dg-edge-2)"/>', 'band')
            f.text(sx(ms), y + 16, f'{ms} ms', 9, 500, True, 'middle', 'faint', layer='label')
    # --- parallel
    gy = 24
    f.group(16, gy, 1088, 252, 'agent', ('parallel（默认）', 'parallel (default)'), ('准备按顺序 · 执行并发 · 结果按原顺序', 'prepare in order · execute concurrently · results in source order'), 'stack', title_mono=False)
    rows = {}
    for i, (k, t, d) in enumerate(calls):
        y = gy + 52 + i * 34; rows[k] = y
        f.text(36, y + 15, f'{k} · {t}', 11, 650, True, cls='strongt', layer='label')
    ends = []
    for i, (k, t, d) in enumerate(calls):
        y = rows[k]
        p0 = i * PREP
        bar(f, sx(p0), y, sx(p0 + PREP) - sx(p0) - 2, 'ext', 'prep', size=9)
        e0 = len(calls) * PREP
        bar(f, sx(e0), y, sx(e0 + d) - sx(e0) - 2, 'agent', f'execute · {d} ms' if d >= 100 else None, size=9)
        bar(f, sx(e0 + d), y, sx(e0 + d + AFT) - sx(e0 + d), 'ext', None)
        ends.append((e0 + d + AFT, k, y))
    for n, (ms, k, y) in enumerate(sorted(ends), 1):
        x = sx(ms) + 4
        f.raw(f'<g class="c-agent"><path class="fillc" d="M{x:.1f} {y+11}l6 -6 6 6 -6 6z"/></g>', 'label')
        f.text(x + 16, y + 15, (f'tool_execution_end #{n}', f'tool_execution_end #{n}'), 9.5, 550, True, cls='cf c-agent', layer='label')
    last = max(e for e, _, _ in ends)
    my = gy + 52 + 3 * 34 + 8
    f.text(36, my + 15, ('消息', 'messages'), 11, 650, cls='strongt', layer='label')
    for i, (k, *_ ) in enumerate(calls):
        bar(f, sx(last + 10 + i * 34), my, sx(34) - sx(0) - 4, 'ai', f'msg {k}', size=9)
    f.text(sx(last + 10 + 3 * 34) + 8, my + 15, ('Promise.all 之后按 A → B → C 发出', 'after Promise.all · in A → B → C order'), 10, 500, cls='muted', layer='label')
    axis(gy + 214)
    # --- sequential
    gy2 = 296
    f.group(16, gy2, 1088, 168, 'agent', 'sequential', ('toolExecution = "sequential"，或批内任一工具声明 executionMode: "sequential"', 'toolExecution = "sequential", or any tool in the batch declares executionMode: "sequential"'), 'queue', title_mono=False)
    t = 0
    for i, (k, tt, d) in enumerate(calls):
        y = gy2 + 50 + i * 26
        f.text(36, y + 13, f'{k} · {tt}', 11, 650, True, cls='strongt', layer='label')
        bar(f, sx(t), y, sx(t + PREP) - sx(t) - 2, 'ext', None, h=18); t += PREP
        bar(f, sx(t), y, sx(t + d) - sx(t) - 2, 'agent', f'{d} ms' if d > 80 else None, h=18, size=9); t += d
        bar(f, sx(t), y, sx(t + AFT) - sx(t) - 1, 'ext', None, h=18); t += AFT
        bar(f, sx(t), y, sx(t + 24) - sx(t) - 2, 'ai', None, h=18); t += 26
    f.text(1088, gy2 + 50 + 13, (f'≈ {t} ms：每个调用 start → … → message 后才开始下一个', f'≈ {t} ms: each call finishes start → … → message before the next'), 10, 500, cls='muted', layer='label', anchor='end')
    axis(gy2 + 132)
    # legend + rules
    f.legend(24, 486, [('layer:ext', ('准备：查找 · prepareArguments · 校验 · beforeToolCall；以及 afterToolCall', 'prepare: find · prepareArguments · validate · beforeToolCall; and afterToolCall')),
                       ('layer:agent', 'tool.execute()'), ('layer:ai', 'ToolResultMessage')])
    f.note(24, 514, ('立即结果（未找到 / 校验失败 / 被阻止）在准备阶段就发 tool_execution_end；中止后剩余调用得到 "Operation aborted"', 'immediate outcomes (not found / invalid / blocked) emit tool_execution_end during prepare; after abort the rest get "Operation aborted"'), 10.5)
    f.note(24, 536, ('terminate：只有批内每个最终结果都设 terminate: true，循环才在本批后停止', 'terminate: the loop stops after the batch only if every finalized result sets terminate: true'), 10.5)
    return f

# ============================================================== ac_proxy : StreamFn resolution + streamProxy
@reg
def ac_proxy():
    f = Fig('ac_proxy', 1120, 600, ('StreamFn 与代理流', 'StreamFn and the proxy stream'))
    f.node('opt', 24, 40, 220, 56, 'coding', 'AgentOptions.streamFn', ('构造时传入', 'passed at construction'), 'gear', tsize=12)
    f.node('sf', 330, 40, 250, 56, 'agent', 'agent.streamFunction', ('传给 runAgentLoop()', 'handed to runAgentLoop()'), 'cpu', strong=True, tsize=12)
    f.node('def', 660, 40, 210, 56, 'agent', 'getDefaultStreamFn()', ('未设置时抛错', 'throws if none set'), 'plug', tsize=12)
    f.node('set', 920, 40, 176, 56, 'infra', 'setDefaultStreamFn()', ('由宿主安装', 'installed by a host'), None, tsize=12)
    E = f.edge
    E([(244, 68), (330, 68)], 'opt', 'sf', 'main', 'agent', flow=True)
    E([(660, 68), (580, 68)], 'def', 'sf', 'dep', label='??', lpos=(620, 68), lsize=10)
    E([(920, 68), (870, 68)], 'set', 'def', 'dep')
    f.node('ct', 330, 150, 540, 74, 'agent', 'StreamFn(model, TranscriptContext, SimpleStreamOptions?)', '→ AssistantMessageEventStream | Promise<…>', None, kind='tint', tsize=12,
           sub2=('约定：不抛异常 · 失败编码为 error 事件 + stopReason "error" / "aborted"', 'contract: never throw · failures = error event + stopReason "error" / "aborted"'), ssize=10.5)
    E([(455, 96), (455, 150)], 'sf', 'ct', 'main', 'agent')
    f.node('models', 170, 286, 300, 60, 'ai', 'models.streamSimple', ('pi-ai Models · coding-agent 用 ModelRuntime', 'pi-ai Models · coding-agent uses ModelRuntime'), 'hub', strong=True, tsize=12, ssize=10.5)
    f.node('proxy', 600, 286, 270, 60, 'agent', 'streamProxy(model, ctx, opts)', 'proxy.ts · { authToken, proxyUrl }', 'globe', strong=True, tsize=12, ssize=10.5)
    E([(400, 224), (400, 286)], 'ct', 'models', 'event', emark='tri', label=('直接调用', 'direct'), lpos=(400, 255), lmono=False, lsize=10)
    E([(735, 224), (735, 286)], 'ct', 'proxy', 'event', emark='tri', label=('经服务端', 'via a server'), lpos=(735, 255), lmono=False, lsize=10)
    # proxy chain
    Y4, Y5 = 400, 510
    f.node('post', 600, Y4, 270, 60, 'agent', 'POST {proxyUrl}/api/stream', 'Authorization: Bearer <authToken>', None, tsize=11.5, ssize=10.5)
    f.node('srv', 920, Y4, 176, 60, 'infra', ('你的代理服务', 'your proxy server'), ('运行 pi-ai', 'runs pi-ai'), 'cloud', mono=False, tsize=11.5)
    f.node('sse', 920, Y5, 176, 60, 'infra', 'data: {event}', ('SSE · 无 partial', 'SSE · no partial'), 'stream', tsize=11.5)
    f.node('rb', 600, Y5, 270, 60, 'agent', 'processProxyEvent(e, partial)', ('在客户端重建 partial', 'rebuild partial client-side'), None, tsize=11.5, ssize=10.5, strong=True)
    f.node('out', 170, Y5, 300, 60, 'ai', 'AssistantMessageEventStream', ('与直连相同 · 带 durationMs（1.1.0）', 'same as direct · gets durationMs (1.1.0)'), 'stream', tsize=11.5, ssize=10.5)
    E([(735, 346), (735, Y4)], 'proxy', 'post', 'main', 'agent', flow=True, step=1, spos=(755, 373))
    E([(870, Y4 + 30), (920, Y4 + 30)], 'post', 'srv', 'main', 'agent', step=2, spos=(895, Y4 + 14))
    E([(1008, Y4 + 60), (1008, Y5)], 'srv', 'sse', 'event', label='stream', lpos=(1008, (Y4 + 60 + Y5) / 2), lsize=10)
    E([(920, Y5 + 30), (870, Y5 + 30)], 'sse', 'rb', 'main', 'agent', step=3, spos=(895, Y5 + 14))
    E([(600, Y5 + 30), (470, Y5 + 30)], 'rb', 'out', 'main', 'ai', flow=True, step=4, spos=(535, Y5 + 14))
    # body + failures
    codebox(f, 24, 380, 520 - 24 - 40, [(0, 'body: { model, context, options }', 'strongt'), (1, 'options = 11 serializable fields:', 'muted'),
            (1, 'temperature · samplingParams · maxTokens', 'muted'), (1, 'reasoning · cacheRetention · sessionId', 'muted'), (1, 'headers · metadata · transport', 'muted'), (1, 'thinkingBudgets · maxRetryDelayMs', 'muted')], size=10)
    fy = 586
    f.text(24, fy, ('失败 → error 事件：', 'failures → error event:'), 10.5, 650, cls='cf c-err', layer='label')
    f.text(162, fy, ('!response.ok → "Proxy error: …" · 无 done/error 的 EOF → "Connection closed by proxy server…" · abort → reader.cancel() → aborted',
                     '!response.ok → "Proxy error: …" · EOF without done/error → "Connection closed by proxy server…" · abort → reader.cancel() → aborted'), 10, 500, True, cls='muted', layer='label')
    return f

# ============================================================== ac_types : data types (UML)
@reg
def ac_types():
    f = Fig('ac_types', 1120, 560, ('pi-agent-core 数据类型', 'pi-agent-core data types'))
    W = 250; C = [24, 300, 576, 852]
    hS = uml(f, 'state', C[0], 24, W, 'agent', 'AgentState', '«interface»', [['+systemPrompt (readonly)', '+model · thinkingLevel', '+tools · messages (copy on set)'], ['+isStreaming · streamingMessage?', '+pendingToolCalls: Set<string>', '+errorMessage?']])
    hC = uml(f, 'ctx', C[0], 300, W, 'agent', 'AgentContext', '«interface»', [['+messages: AgentMessage[]', '+tools?: AgentTool[]']])
    hM = uml(f, 'msg', C[1], 24, W, 'agent', 'AgentMessage', '«union»', [['|Message (pi-ai)', '|CustomAgentMessages[K]']])
    uml(f, 'cust', C[1], 186, W, 'coding', 'CustomAgentMessages', '«merge»', [[('声明合并扩展', 'extend by declaration merging'), ('如 artifact · notification', 'e.g. artifact · notification')]])
    uml(f, 'aimsg', C[1], 340, W, 'ai', 'Message', '«pi-ai»', [['|SystemMessage · UserMessage', '|AssistantMessage', '|ToolResultMessage']])
    hT = uml(f, 'tool', C[2], 24, W, 'agent', 'AgentTool', '«extends Tool»', [['+name · description · parameters', '+label · outputSchema?', '+executionMode? · replay?'], ['+prepareArguments?(args)', '+execute(id, params, signal,', ' onUpdate) → Promise<Result>']])
    hR = uml(f, 'res', C[2], 250, W, 'agent', 'AgentToolResult<T>', None, [['+content: (Text | Image)[]', '+details: T', '+structuredContent? · usage?', '+isError? · terminate?']])
    uml(f, 'out', C[2], 418, W, 'agent', 'AgentToolCallOutcome', None, [['+toolCall · result · isError', '+durationMs? (1.1.0)']])
    hL = uml(f, 'cfg', C[3], 24, W, 'coding', 'AgentLoopConfig', '«interface»', [['+…SimpleStreamOptions', '+model', '+convertToLlm (required)', '+transformContext? · getApiKey?'], ['+prepareRequest? · prepareNextTurn?', '+finishTurn? → end | continue', '+beforeToolCall? · afterToolCall?', '+getSteeringMessages?', '+getFollowUpMessages?', '+toolExecution? = "parallel"']])
    uml(f, 'bres', C[3], 300, W, 'ext', 'BeforeToolCallResult', None, [['+block? · reason?', '+terminate?']])
    uml(f, 'ares', C[3], 418, W, 'ext', 'AfterToolCallResult', None, [['+content? · details? · isError?', '+usage? · terminate?', '+structuredContent?']])
    E = f.edge
    def rl(x, y, s, anchor='start'): f.text(x, y, s, 10, 500, True, anchor, 'faint', layer='label', owner='note')
    E([(C[0] + W, 60), (C[1], 60)], 'state', 'msg', 'dep', smark='diamond')
    E([(C[0] + 125, 24 + hS), (C[0] + 125, 300)], 'state', 'ctx', 'event', label=('快照', 'snapshot'), lpos=(C[0] + 125, (24 + hS + 300) / 2), lmono=False, lsize=10)
    E([(C[1] + 60, 24 + hM), (C[1] + 60, 186)], 'msg', 'cust', 'event', emark='tri')
    E([(C[1] + 20, 24 + hM), (C[1] + 20, 340)], 'msg', 'aimsg', 'event', emark='tri', r=6) if False else None
    E([(C[1], 100), (C[1] - 14, 100), (C[1] - 14, 380), (C[1], 380)], 'msg', 'aimsg', 'event', emark='tri', r=6)
    E([(C[0] + 200, 24), (C[0] + 200, 12), (C[2] + 60, 12), (C[2] + 60, 24)], 'state', 'tool', 'dep', smark='diamond', r=5, label='tools', lpos=(438, 12), lsize=9.5)
    E([(C[2] + 125, 24 + hT), (C[2] + 125, 250)], 'tool', 'res', 'dep', label=('execute 返回', 'execute returns'), lpos=(C[2] + 125, (24 + hT + 250) / 2), lmono=False, lsize=10)
    E([(C[2] + 125, 250 + hR), (C[2] + 125, 418)], 'res', 'out', 'dep', smark='odiamond')
    E([(C[3] + 125, 24 + hL), (C[3] + 125, 300)], 'cfg', 'bres', 'event', label=('钩子返回', 'hooks return'), lpos=(C[3] + 125, (24 + hL + 300) / 2), lmono=False, lsize=10)
    E([(C[3], 24 + hL - 20), (C[3] - 13, 24 + hL - 20), (C[3] - 13, 450), (C[3], 450)], 'cfg', 'ares', 'event', r=6)
    f.legend(24, 546, [('dep', ('持有 / 返回', 'owns / returns')), ('event', ('派生 / 联合成员', 'derived / union member')), ('layer:agent', 'pi-agent-core'), ('layer:coding', ('由宿主提供', 'provided by the host')), ('layer:ext', ('钩子结果', 'hook results')), ('layer:ai', 'pi-ai')])
    return f
