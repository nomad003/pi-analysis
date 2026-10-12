"""Diagrams 5-12."""
import re
from pathlib import Path
from svgkit import Fig, maxw, tw, icon, pair, esc
from figs import reg, SRC

# ============================================================== 5. sequence (swimlanes)
@reg
def sequence():
    lanes = [('im', 'InteractiveMode', 'modes'), ('as', 'AgentSession', 'coding'), ('ex', 'ExtensionRunner', 'ext'),
             ('sm', 'SessionManager', 'coding'), ('t', ('工具 · bash', 'Tool · bash'), 'coding'), ('ag', 'Agent · runLoop', 'agent'),
             ('ai', 'streamFn · pi-ai', 'ai')]
    LC = dict((k, c) for k, t, c in lanes)
    X = {k: 92 + i * 156 for i, (k, *_) in enumerate(lanes)}
    P = [(('预处理', 'Preprocess'), [
            ('im', 'as', 'prompt(text)', 'c'), ('as', 'ex', ('input · 可改写或接管', 'input · may rewrite / handle'), 'c'),
            ('as', 'as', ('展开 skill 与模板', 'expand skills · templates'), 's'), ('as', 'ex', 'before_agent_start', 'c'),
            ('as', 'ag', 'agent.prompt() → runAgentLoop()', 'c'), ('ag', 'as', 'message_end(user)', 'e'), ('as', 'sm', 'appendMessage()', 'c')]),
         (('请求 1', 'Request 1'), [
            ('ag', 'ex', ('context · 每次请求前', 'context · before every request'), 'c'), ('ag', 'ai', 'streamFn(model, ctx)', 'c'),
            ('ai', 'ag', 'text_delta …', 'e'), ('ag', 'as', 'message_update', 'e'), ('as', 'im', ('重绘（批处理）', 're-render (batched)'), 'e'),
            ('ai', 'ag', 'done(toolUse)', 'e'), ('ag', 'as', 'message_end(assistant)', 'e'), ('as', 'sm', 'appendMessage()', 'c')]),
         (('工具调用', 'Tool call'), [
            ('ag', 'ex', ('tool_call · 可阻止', 'tool_call · may block'), 'c'), ('ag', 't', 'execute(…)', 'c'),
            ('t', 'ag', ('onUpdate … 结果', 'onUpdate … result'), 'e'), ('ag', 'ex', ('tool_result · 可改写', 'tool_result · may rewrite'), 'c'),
            ('ag', 'as', 'message_end(toolResult)', 'e'), ('as', 'sm', 'appendMessage()', 'c')]),
         (('请求 2', 'Request 2'), [
            ('ag', 'ai', ('streamFn（含结果）', 'streamFn(+ result)'), 'c'), ('ai', 'ag', 'done(stop)', 'e'),
            ('ag', 'as', 'message_end · turn_end · agent_end', 'e'), ('as', 'sm', 'appendMessage()', 'c'), ('as', 'im', ('idle · 等待输入', 'idle · ready for input'), 'e')])]
    RH, PH, Y0 = 24, 30, 104
    n = sum(len(m) for _, m in P)
    H = Y0 + n * RH + len(P) * PH + 50
    f = Fig('sequence', 1120, H, ('一次提示的完整时序', 'One prompt, end to end'))
    for lab, a, b, l in ((('运行模式', 'run mode'), 'im', 'im', 'modes'), ('pi-coding-agent', 'as', 't', 'coding'), ('pi-agent-core', 'ag', 'ag', 'agent'), ('pi-ai', 'ai', 'ai', 'ai')):
        x0, x1 = X[a] - 74, X[b] + 74
        f.raw(f'<g class="c-{l}"><rect class="fillc" x="{x0}" y="14" width="{x1-x0}" height="3" rx="1.5" opacity=".75"/></g>', 'grp')
        f.text((x0 + x1) / 2, 32, lab, 10.5, 650, isinstance(lab, str), 'middle', 'cf c-' + l, layer='grp', ls='.02em')
    yb = H - 34
    for k, t, l in lanes:
        x = X[k]
        f.raw(f'<line class="life" x1="{x}" y1="80" x2="{x}" y2="{yb}"/>', 'grp')
        f.node(k, x - 74, 42, 148, 38, l, t, None, None, mono=False, tsize=11.5, strong=True, align='center', tweight=650)
    y = Y0; rows = []
    for pi_, (pl, msgs) in enumerate(P, 1):
        f.raw(f'<rect class="band" x="16" y="{y-2}" width="1088" height="{len(msgs)*RH + PH - 4}" rx="10"/>', 'bg')
        f.text(1092, y + 15, (f'{pi_} · {pl[0]}', f'{pi_} · {pl[1]}'), 10.5, 700, cls='faint', layer='label', ls='.04em', anchor='end')
        y += PH - 4
        for m in msgs:
            rows.append((y, m)); y += RH
    def act(k, y0, y1):
        f.raw(f'<g class="c-{LC[k]}"><rect class="act" x="{X[k]-4}" y="{y0}" width="8" height="{y1-y0}" rx="2"/></g>', 'band')
    act('as', rows[0][0] + 2, rows[-1][0] + 14)
    for k in ('ag', 't'):
        rr = [r for r in rows if k in (r[1][0], r[1][1])]
        act(k, rr[0][0] + 4, rr[-1][0] + 14)
    for i, (yy, (a, b, lab, kind)) in enumerate(rows, 1):
        yy += 10
        mono = isinstance(lab, str) or lab[1].split(' ')[0] in ('input', 'context', 'tool_call', 'tool_result', 'streamFn', 'onUpdate')
        if kind == 's':
            x = X[a] + 4
            f.edge([(x, yy - 7), (x + 24, yy - 7), (x + 24, yy + 3), (x, yy + 3)], a, b, 'dep', r=4)
            tx = x + 50
            f.text(tx, yy + 2, lab, 10.5, 500, False, cls='muted', layer='label')
            f.step(i, x + 38, yy - 2, LC[a], r=7.5)
            continue
        dirn = 1 if X[b] > X[a] else -1
        x0 = X[a] + 4 * dirn; x1 = X[b] - 4 * dirn
        f.edge([(x0, yy), (x1, yy)], a, b, 'dep' if kind == 'c' else 'event', LC[a] if kind == 'c' else None)
        lw = maxw(lab, 10.5, 500, mono)
        tot = lw + 20
        mx = (x0 + x1) / 2
        sx = mx - tot / 2 + 7.5
        f.step(i, sx, yy - 9, LC[a], r=7.5)
        f.text(sx + 12, yy - 5.5, lab, 10.5, 500, mono, 'start', 'strongt' if kind == 'c' else 'muted', layer='label')
    f.legend(24, H - 14, [('dep', ('调用', 'call')), ('event', ('事件 / 返回', 'event / return')), ('step', ('顺序编号，颜色 = 发起方', 'order · colour = caller'))])
    f.note(1096, H - 10, ('每个 message_end 都追加到会话 JSONL', 'every message_end is appended to the session JSONL'), 10.5, anchor='end')
    return f

# ============================================================== 6. classes (UML)
@reg
def classes():
    f = Fig('classes', 1120, 560, ('核心类型', 'Key types'))
    CW = 238
    cols = [24, 310, 596, 882]
    def card(cid, x, y, layer, name, stereo=None, sections=()):
        rows = sum(len(s) for s in sections)
        h = 34 + rows * 17 + len(sections) * 9 + 2
        g = [f'<g class="nd c-{layer} k-uml" data-id="{cid}">', f'<rect class="card" x="{x}" y="{y}" width="{CW}" height="{h}" rx="10" filter="url(#pd-sh)"/>',
             f'<path class="uml-h" d="M{x} {y+10}a10 10 0 0 1 10-10h{CW-20}a10 10 0 0 1 10 10v22h-{CW}z"/>']
        if stereo:
            g.append(f.text(x + 12, y + 21, stereo, 9.5, 500, True, cls='faint', layer=None, owner=cid))
            g.append(f.text(x + 12 + maxw(stereo, 9.5, 500, True) + 6, y + 21, name, 12.5, 680, True, cls='cf', layer=None, owner=cid))
        else:
            g.append(f.text(x + 12, y + 21, name, 12.5, 680, True, cls='cf', layer=None, owner=cid))
        yy = y + 32
        for si, sec in enumerate(sections):
            if si: g.append(f'<line class="rule" x1="{x+1}" y1="{yy+2}" x2="{x+CW-1}" y2="{yy+2}"/>')
            yy += 6
            for line in sec:
                yy += 17
                vis = line[0] if line[0] in '+-#' else ''
                txt = line[1:] if vis else line
                cls = 'muted' if vis == '-' else 'strongt'
                g.append(f.text(x + 12, yy - 4, ('+' if vis != '-' else '−'), 10, 600, True, cls='faint', layer=None, owner=cid))
                g.append(f.text(x + 24, yy - 4, txt, 10, 450, True, cls=cls, layer=None, owner=cid))
                if maxw(txt, 10, 450, True) > CW - 34: f.warn.append(f'classes: line too long {txt}')
            yy += 3
        g.append('</g>')
        f.L['node'].append(''.join(g)); f.nodes[cid] = (x, y, CW, h); f.solid.append((cid, (x, y, CW, h)))
        return h
    hA = card('asr', cols[0], 40, 'coding', 'AgentSessionRuntime', None, [['+session: AgentSession', '+services'], ['+newSession()', '+switchSession()', '+fork()', '+importFromJsonl()', '+dispose()']])
    card('sm', cols[0], 306, 'coding', 'SessionManager', None, [['-byId · leafId'], ['+appendMessage()', '+appendCompaction()', '+getBranch() · getTree()', '+branch() · branchWithSummary()', '+buildSessionContext()', '+createBranchedSession()']])
    hS = card('as', cols[1], 40, 'coding', 'AgentSession', None, [['+agent: Agent', '+sessionManager', '+settingsManager', '-_extensionRunner · _modelRuntime'], ['+prompt(text, options)', '+steer() · followUp()', '+setModel() · cycleModel()', '+compact() · navigateTree()', '+bindExtensions() · reload()', '+executeBash() · subscribe()']])
    card('er', cols[1], 370, 'ext', 'ExtensionRunner', None, [['+bindCore(actions)', '+setUIContext(ui, mode)', '+emit(event)', '+emitToolCall() · emitToolResult()']])
    hG = card('agent', cols[2], 40, 'agent', 'Agent', None, [['+state: AgentState', '+streamFunction: StreamFn', '+toolExecution'], ['+convertToLlm · transformContext', '+beforeToolCall · afterToolCall', '+prepareRequest · prepareNextTurn', '+finishTurn'], ['+prompt() · continue()', '+steer() · followUp()', '+abort() · waitForIdle()']])
    card('tool', cols[2], 400, 'agent', 'AgentTool', '«interface»', [['+name · label · parameters', '+executionMode?'], ['+prepareArguments?(args)', '+execute(toolCallId, params, …)']])
    card('mr', cols[3], 40, 'coding', 'ModelRuntime', None, [['+streamSimple(model, ctx)', '+getAuth() · checkAuth()', '+registerProvider(id, config)', '+resolveModel()']])
    card('models', cols[3], 214, 'ai', 'Models', '«interface» pi-ai', [['+getProviders() · getModel()', '+getAvailable() · refresh()', '+streamSimple()']])
    card('prov', cols[3], 372, 'ai', 'Provider', '«interface»', [['+id · name · auth', '+getModels()', '+stream() · streamSimple()']])
    E = f.edge
    def rl(x, y, s, anchor='start'):
        f.text(x, y, s, 10, 500, True, anchor, 'faint', layer='label', owner='note')
    E([(cols[0] + CW, 64), (cols[1], 64)], 'asr', 'as', 'dep', smark='diamond', arrow=True); rl(cols[0] + CW + 6, 58, 'session')
    E([(cols[1] + CW, 64), (cols[2], 64)], 'as', 'agent', 'dep', smark='diamond'); rl(cols[1] + CW + 6, 58, 'agent')
    E([(cols[1], 230), (cols[0] + 120, 230), (cols[0] + 120, 306)], 'as', 'sm', 'dep', smark='diamond', r=8); rl(cols[0] + 128, 290, 'sessionManager')
    E([(cols[1] + 120, 40 + hS), (cols[1] + 120, 370)], 'as', 'er', 'dep', smark='diamond'); rl(cols[1] + 128, 356, ('创建并 bindCore()', 'creates · bindCore()'))
    E([(cols[1] + 200, 40), (cols[1] + 200, 22), (cols[3] + 120, 22), (cols[3] + 120, 40)], 'as', 'mr', 'dep', smark='odiamond', r=8); rl(cols[2] + 120, 16, '_modelRuntime', 'middle')
    E([(cols[2] + CW, 104), (cols[3], 104)], 'agent', 'mr', 'event')
    E([(cols[2] + 120, 40 + hG), (cols[2] + 120, 400)], 'agent', 'tool', 'dep', smark='odiamond'); rl(cols[2] + 128, 388, 'state.tools  *')
    mrh = f.nodes['mr'][3]
    E([(cols[3] + 120, 40 + mrh), (cols[3] + 120, 214)], 'mr', 'models', 'event', emark='tri'); rl(cols[3] + 128, 200, 'implements')
    mh = f.nodes['models'][3]
    E([(cols[3] + 120, 214 + mh), (cols[3] + 120, 372)], 'models', 'prov', 'dep', smark='odiamond'); rl(cols[3] + 128, 362, 'getProviders()  *')
    # legend (UML)
    y = 540; x = 24
    out = ['<g class="lg">']
    for kind, lab in (('diamond', ('组合（持有）', 'composition (owns)')), ('odiamond', ('聚合 / 引用', 'aggregation / reference')), ('tri', ('实现接口', 'implements')), ('arrow', ('调用 / 依赖', 'calls / uses'))):
        dash = ' k-event' if kind == 'tri' else ''
        if kind == 'arrow':
            out.append(f'<g class="ed k-event"><path class="ln" d="M{x} {y}h22"/><path class="ah" d="M{x+28} {y}l-8 -4.2q2 4.2 0 8.4z"/></g>')
        else:
            mk = {'diamond': f'M{x} {y}l7 -4.5 7 4.5 -7 4.5z', 'odiamond': f'M{x} {y}l7 -4.5 7 4.5 -7 4.5z', 'tri': f'M{x+28} {y}l-11 -6v12z'}[kind]
            ln = f'M{x+14} {y}h16' if kind != 'tri' else f'M{x} {y}h17'
            out.append(f'<g class="ed{dash}"><path class="ln" d="{ln}"/><path class="mk {kind}" d="{mk}"/></g>')
        x += 38
        out.append(f.text(x, y + 4, lab, 11, 500, cls='lg-t', layer=None, owner='legend'))
        x += maxw(lab, 11, 500) + 24
    out.append('</g>'); f.L['top'].append(''.join(out))
    f.note(1096, 544, ('字段与方法均为节选', 'members are a selection'), 10.5, anchor='end')
    return f

# ============================================================== 7. session tree
@reg
def session():
    f = Fig('session', 1120, 560, ('会话持久化与分支', 'Session persistence & branching'))
    E = [
        (2, 'a1f0', 'null', 'message', ('user · 修复失败的测试', 'user · fix the failing test'), 'main'),
        (3, 'b2c4', 'a1f0', 'message', ('assistant · toolCall(bash)', 'assistant · toolCall(bash)'), 'main'),
        (4, 'c3d9', 'b2c4', 'message', ('toolResult · exit 0', 'toolResult · exit 0'), 'main'),
        (5, 'd4e1', 'c3d9', 'message', ('assistant · “已修复”', 'assistant · “fixed”'), 'main'),
        (6, 'e5a2', 'd4e1', 'model_change', ('provider · modelId', 'provider · modelId'), 'old'),
        (7, 'f6b3', 'e5a2', 'message', ('user · 顺便加测试', 'user · also add tests'), 'old'),
        (8, 'g7c8', 'f6b3', 'message', ('assistant · …', 'assistant · …'), 'old'),
        (9, 'h8d5', 'd4e1', 'branch_summary', ('fromId: g7c8 · summary', 'fromId: g7c8 · summary'), 'new'),
        (10, 'i9e6', 'h8d5', 'message', ('user · 换个思路', 'user · try another approach'), 'new'),
    ]
    TL = {'message': 'agent', 'model_change': 'modes', 'branch_summary': 'coding', 'session': 'infra'}
    px, py, pw = 24, 24, 520
    f.raw(f'<rect class="codebg" x="{px}" y="{py}" width="{pw}" height="{40 + 34 * 10 + 8}" rx="12"/>', 'grp')
    f.raw(icon('file', px + 14, py + 11, 16, 'ico c-coding'), 'grp')
    f.text(px + 38, py + 24, '~/.pi/agent/sessions/<cwd>/<id>.jsonl', 11.5, 600, True, cls='strongt', layer='grp')
    f.text(px + pw - 14, py + 24, ('只追加', 'append-only'), 10.5, 550, cls='faint', layer='grp', anchor='end')
    f.raw(f'<line class="rule" x1="{px}" y1="{py+38}" x2="{px+pw}" y2="{py+38}"/>', 'grp')
    y = py + 48
    f.text(px + 22, y + 18, '1', 10, 500, True, 'end', 'faint', layer='label')
    f.chip(px + 34, y + 4, 'session', 'infra', size=9.5, h=19, weight=600)
    f.text(px + 160, y + 18, ('文件头 · version 3 · id · cwd · parentSession?', 'header · version 3 · id · cwd · parentSession?'), 10.5, 450, False, cls='muted', layer='label')
    for i, (ln, iid, par, t, lab, br) in enumerate(E):
        y = py + 48 + (i + 1) * 34
        if br == 'new': f.raw(f'<rect class="hl-row" x="{px+1}" y="{y}" width="{pw-2}" height="30"/>', 'grp')
        f.text(px + 22, y + 18, str(ln), 10, 500, True, 'end', 'faint', layer='label')
        f.chip(px + 34, y + 4, t, TL[t], size=9.5, h=19, weight=600)
        f.text(px + 160, y + 18, iid, 10.5, 650, True, cls='strongt' if br != 'old' else 'muted', layer='label')
        f.text(px + 206, y + 18, f'← {par}', 10.5, 500, True, cls='faint', layer='label')
        f.text(px + 278, y + 18, lab, 10.5, 450, False, cls='muted', layer='label')
    f.note(px, py + 48 + 10 * 34 + 26, ('每行一个 JSON 对象；id 为 8 位 hex，← 是 parentId', 'one JSON object per line · 8-hex ids · ← is parentId'), 10.5)
    NW, NH = 190, 40
    cx, ox, nx = 790, 654, 962
    pos = {'a1f0': (cx, 40), 'b2c4': (cx, 100), 'c3d9': (cx, 160), 'd4e1': (cx, 220),
           'e5a2': (ox, 300), 'f6b3': (ox, 360), 'g7c8': (ox, 420), 'h8d5': (nx, 300), 'i9e6': (nx, 360)}
    info = {e[1]: e for e in E}
    for iid, (x, y) in pos.items():
        ln, _, par, t, lab, br = info[iid]
        f.node(iid, x - NW / 2, y, NW, NH, TL[t] if br != 'old' else 'infra', f'{iid} · {t}', lab, None, tsize=11, ssize=10,
               kind='ghost' if br == 'old' else 'card', strong=(br != 'old'))
    for iid, (x, y) in pos.items():
        par = info[iid][2]
        if par == 'null': continue
        px2, py2 = pos[par]
        old = info[iid][5] == 'old'
        if px2 == x:
            f.edge([(x, py2 + NH), (x, y)], par, iid, 'faint' if old else 'main', None if old else 'accent', arrow=False)
        else:
            f.edge([(px2, py2 + NH), (px2, 280), (x, 280), (x, y)], par, iid, 'faint' if old else 'main', None if old else 'accent', arrow=False, r=10)
    f.raw(f'<circle cx="{cx}" cy="280" r="3.2" style="fill:var(--accent-c)"/>', 'label')
    f.text(cx - NW / 2 - 10, 236, ('分支点', 'branch point'), 10.5, 650, cls='muted', layer='label', anchor='end')
    f.text(cx - NW / 2 - 10, 251, ('leaf 移回 d4e1 后追加', 'leaf → d4e1, then append'), 10.5, 450, cls='faint', layer='label', anchor='end')
    tagw = f.chip(nx - NW / 2, 418, 'leafId', 'accent', size=10.5, h=22, cls='solid')
    f.edge([(nx - NW / 2 + tagw / 2, 418), (nx - NW / 2 + tagw / 2, 400)], None, 'i9e6', 'main', 'accent')
    f.edge([(nx - NW / 2, 320), (812, 320), (812, 440), (ox + NW / 2, 440)], 'h8d5', 'g7c8', 'ref', 'coding', label='fromId', lpos=(812, 384), r=8)
    f.note(ox, 482, ('被放弃的路径仍留在文件里', 'abandoned path stays in the file'), 10.5, anchor='middle')
    f.edge([(nx + NW / 2, 380), (1092, 380), (1092, 60), (cx + NW / 2, 60)], 'i9e6', 'a1f0', 'event', 'accent', label='buildSessionContext()', lpos=(990, 60), r=10)
    f.note(1080, 230, ('leaf → root', 'leaf → root'), 10.5, anchor='end', cls='muted')
    types = ['message', 'thinking_level_change', 'model_change', 'usage', 'compaction', 'branch_summary', 'custom', 'custom_message', 'label', 'session_info', 'context_edit']
    y = 506
    f.text(24, y + 14, ('11 种条目', '11 entry types'), 11, 700, cls='strongt', layer='label')
    x = 112
    for t in types:
        x += f.chip(x, y, t, TL.get(t, 'infra'), size=9.5, h=20, cls='' if t in TL else 'plain') + 6
    f.legend(24, 546, [('main', ('当前分支（进入上下文）', 'active branch (in context)')), ('ref', ('引用字段', 'reference field')), ('event', ('上下文重建方向', 'context rebuild direction'))])
    return f

# ============================================================== 8. compaction
@reg
def compaction():
    f = Fig('compaction', 1120, 590, ('上下文压缩', 'Compaction'))
    T = [('man', 'modes', ('手动', 'manual'), '/compact · compact()', 'user'),
         ('thr', 'coding', ('阈值', 'threshold'), ('超过 window − reserve', 'tokens > window − reserve'), 'clock'),
         ('ovf', 'err', ('溢出', 'overflow'), ('上下文溢出 / 截断', 'context overflow / truncation'), 'x')]
    TW = 230
    for i, (k, l, t, sub, ic) in enumerate(T):
        f.node(k, 24, 40 + i * 70, TW, 56, l, t, sub, ic, mono=False, kind='err' if k == 'ovf' else 'card')
    PX, PW = 300, 236
    f.node('prep', PX, 106, PW, 64, 'coding', 'prepareCompaction()', 'getBranch() → findCutPoint()', 'scissors', strong=True, sub2='compaction_start(reason)', ssize=10.5)
    for i, k in enumerate(('man', 'thr', 'ovf')):
        yy = 68 + i * 70
        f.edge([(24 + TW, yy), (276, yy), (276, 138), (PX, 138)] if yy != 138 else [(24 + TW, yy), (PX, yy)], k, 'prep', 'main', 'coding', r=8)
    f.step(1, PX + 7, 106, 'coding', onnode=True)
    HX, HW = 580, 214
    f.node('hook', HX, 106, HW, 64, 'ext', 'session_before_compact', ('扩展钩子', 'extension hook'), None, strong=True, tsize=11.5)
    f.step(2, HX + 7, 106, 'ext', onnode=True)
    f.edge([(PX + PW, 138), (HX, 138)], 'prep', 'hook', 'main', 'coding', flow=True)
    OX, OW = 862, 210
    f.node('cancel', OX, 24, OW, 48, 'infra', ('已取消', 'cancelled'), ('不追加任何条目', 'nothing appended'), 'x', mono=False, kind='ghost')
    f.node('extc', OX, 110, OW, 56, 'ext', ('扩展自带结果', "extension's result"), 'fromExtension: true', 'plug', mono=False)
    f.node('gen', OX, 200, OW, 56, 'coding', 'compact()', ('generateSummary() · LLM', 'generateSummary() · LLM'), 'spark', strong=True)
    f.step(3, OX + 7, 200, 'coding', onnode=True)
    f.edge([(HX + HW, 124), (828, 124), (828, 48), (OX, 48)], 'hook', 'cancel', 'dep', label='cancel', lpos=(828, 86), lsize=10, r=8)
    f.edge([(HX + HW, 138), (OX, 138)], 'hook', 'extc', 'dep', 'ext')
    f.text(HX + HW + 8, 150, 'compaction', 10, 550, True, cls='muted', layer='label')
    f.edge([(HX + HW, 158), (808, 158), (808, 228), (OX, 228)], 'hook', 'gen', 'main', 'coding', label=('无', 'none'), lpos=(808, 200), lsize=10, lmono=False, flow=True, r=8)
    AX, AW = 596, 476
    f.node('app', AX, 300, AW, 56, 'coding', 'appendCompaction(summary, firstKeptEntryId, tokensBefore, …)', ('随后 session_compact · compaction_end', 'then session_compact · compaction_end'), 'db', strong=True, tsize=11.5)
    f.step(4, AX + 7, 300, 'coding', onnode=True)
    f.edge([(OX + OW, 138), (1096, 138), (1096, 328), (AX + AW, 328)], 'extc', 'app', 'dep', 'ext', r=10)
    f.edge([(OX + 113, 256), (OX + 113, 300)], 'gen', 'app', 'main', 'coding', flow=True)
    f.node('retry', PX, 300, PW, 56, 'agent', 'agent.continue()', ('overflow 且 willRetry：仅一次', 'overflow + willRetry: once'), 'loop')
    f.step(5, PX + 7, 300, 'agent', onnode=True)
    f.edge([(AX, 328), (PX + PW, 328)], 'app', 'retry', 'dep', 'agent')
    f.text((AX + PX + PW) / 2, 320, 'willRetry', 9.5, 550, True, 'middle', 'muted', layer='label')
    f.node('done', 24, 300, TW, 56, 'term', ('完成', 'done'), ('否则：等待下一次提示', 'otherwise: wait for next prompt'), 'check', mono=False, kind='term')
    f.edge([(PX, 328), (24 + TW, 328)], 'retry', 'done', 'faint')
    y0 = 392
    f.group(16, y0, 1088, 182, 'coding', ('上下文窗口里发生了什么', 'WHAT HAPPENS TO THE CONTEXT WINDOW'), None, 'layers', title_mono=False)
    X0, X1 = 150, 1080
    def seg(x, y, w, cls, txt, dashed=False):
        f.raw(f'<g class="{cls}"><rect class="fillcb" x="{x}" y="{y}" width="{w}" height="26" rx="6"' + (' style="stroke-dasharray:3 3"' if dashed else '') + '/></g>', 'node')
        f.text(x + w / 2, y + 17, txt, 10.5, 600, False, 'middle', 'cf ' + cls, layer='label')
    by = y0 + 56
    f.text(140, by + 17, ('压缩前', 'before'), 11, 650, cls='strongt', layer='label', anchor='end')
    seg(X0, by, 520, 'c-infra', ('较早的条目 → 交给 LLM 总结', 'older entries → summarized by the LLM'))
    seg(X0 + 524, by, 260, 'c-agent', ('保留尾部 ≈ keepRecentTokens 20,000', 'kept tail ≈ keepRecentTokens 20,000'))
    seg(X0 + 788, by, X1 - X0 - 788, 'c-err', 'reserveTokens 16,384', dashed=True)
    f.raw(f'<line x1="{X0+522}" y1="{by-8}" x2="{X0+522}" y2="{by+34}" style="stroke:var(--text);stroke-width:1.5;stroke-dasharray:3 2"/>', 'label')
    f.raw(icon('scissors', X0 + 514, by - 28, 16, 'ico c-coding'), 'label')
    f.text(X0 + 536, by - 15, ('切点：user 或 assistant 消息，绝不切在 toolResult（firstKeptEntryId）', 'cut point: a user or assistant message, never a toolResult (firstKeptEntryId)'), 10.5, 550, cls='muted', layer='label')
    ay = by + 54
    f.text(140, ay + 17, ('压缩后', 'after'), 11, 650, cls='strongt', layer='label', anchor='end')
    seg(X0, ay, 150, 'c-coding', ('compaction 摘要', 'compaction summary'))
    seg(X0 + 154, ay, 260, 'c-agent', ('同一段保留尾部', 'the same kept tail'))
    f.raw(f'<rect x="{X0+418}" y="{ay}" width="{X1-X0-418}" height="26" rx="6" style="fill:none;stroke:var(--dg-line);stroke-dasharray:3 4"/>', 'node')
    f.text(X0 + 418 + (X1 - X0 - 418) / 2, ay + 17, ('腾出的空间', 'freed space'), 10.5, 500, False, 'middle', 'faint', layer='label')
    f.note(X0, ay + 46, ('阈值：contextTokens > contextWindow − reserveTokens · 保留尾部按 estimateTokens()（chars/4）累加', 'threshold: contextTokens > contextWindow − reserveTokens · kept tail sized with estimateTokens() (chars / 4)'), 10.5)
    return f

# ============================================================== 9. extensions lifecycle
@reg
def extensions():
    f = Fig('extensions', 1120, 560, ('扩展生命周期', 'Extension lifecycle'))
    lanes = [('L1', ('main.ts · ResourceLoader', 'main.ts · ResourceLoader'), 'coding', 'terminal', 64, 106),
             ('L2', ('扩展模块', 'extension module'), 'ext', 'code', 182, 124),
             ('L3', ('AgentSession · ExtensionRunner', 'AgentSession · ExtensionRunner'), 'ext', 'plug', 318, 92),
             ('L4', ('运行模式', 'run mode'), 'modes', 'play', 422, 80)]
    for k, lab, l, ic, y, h in lanes:
        f.raw(f'<g class="c-{l}"><rect class="band-s" x="16" y="{y}" width="1088" height="{h}" rx="10"/></g>', 'bg')
        f.raw(icon(ic, 28, y + 10, 14, f'ico c-{l}'), 'grp')
        f.text(48, y + 21, lab, 10.5, 650, False, cls=f'cf c-{l}', layer='grp')
    C = [176, 352, 528, 704, 880]; CW = 164
    ph = [('发现', 'Discover'), ('加载', 'Load'), ('绑定核心', 'Bind core'), ('绑定 UI', 'Bind UI'), ('运行期', 'Runtime')]
    for i, (x, p) in enumerate(zip(C, ph)):
        f.step(i + 1, x + 9, 34, 'accent', r=9)
        f.text(x + 24, 38, p, 12, 700, cls='strongt', layer='label')
        if i: f.raw(f'<line class="rule-d" x1="{x-6}" y1="22" x2="{x-6}" y2="510"/>', 'bg')
    N = f.node
    N('reload', C[0], 96, CW, 48, 'coding', 'reload()', 'packageManager.resolve()', None, tsize=12, ssize=10.5)
    N('load', C[1], 96, CW, 48, 'coding', 'loadExtensionsCached()', ('按路径加载', 'by resolved path'), None, tsize=10.5)
    N('sess', C[2], 96, CW, 48, 'coding', 'AgentSession', ('由运行时创建', 'created by runtime'), None, tsize=12)
    for j, s in enumerate(['~/.pi/agent/extensions', '.pi/extensions', ('settings 里的包', 'settings packages'), '-e <path>']):
        f.chip(C[0], 210 + j * 23, s, 'ext', size=9.5, h=19, mono=isinstance(s, str))
    N('fac', C[1], 206, CW, 62, 'ext', 'factory(pi)', 'jiti.import(path)', None, tsize=12, strong=True, sub2=('registerTool · on(event)…', 'registerTool · on(event)…'), ssize=10)
    f.note(C[1] + 52, 284, ('动作先是占位桩', 'actions start as stubs'), 10)
    f.note(C[1] + 52, 297, ('registerProvider 排队', 'registerProvider queued'), 10)
    N('runner', C[2], 334, CW, 56, 'ext', 'ExtensionRunner', ('bindCore()：接上真实动作', 'bindCore(): real actions'), None, tsize=12, strong=True, ssize=10.5)
    N('bindx', C[3], 438, CW, 48, 'modes', 'bindExtensions()', '{ uiContext, mode }', None, tsize=11.5, ssize=10.5)
    N('ui', C[3], 334, CW, 56, 'ext', 'setUIContext()', ('UI 由模式提供', 'UI from the mode'), None, tsize=12)
    N('start', C[3], 222, CW, 46, 'ext', 'session_start', 'resources_discover', None, tsize=11, kind='tint', ssize=10.5)
    N('emit', C[4], 334, 216, 56, 'ext', 'emit(event)', ('分发 41 种事件', 'dispatches 41 event types'), None, tsize=12, strong=True)
    ev = [('input', 0, 0), ('context', 0, 1), ('tool_call', 0, 2), ('tool_result', 0, 3), ('turn_end', 0, 4),
          ('message_end', 1, 0), ('agent_end', 1, 1), ('model_select', 1, 2), ('session_compact', 1, 3), ('session_shutdown', 1, 4)]
    for e, c, r in ev:
        f.chip(C[4] + (0 if c == 0 else 92), 194 + r * 22, e, 'ext', size=9.5, h=19, cls='solid' if e in ('input', 'context', 'tool_call', 'tool_result') else '')
    E = f.edge
    E([(C[0] + CW, 120), (C[1], 120)], 'reload', 'load', 'main', 'coding', flow=True)
    E([(C[1] + CW, 120), (C[2], 120)], 'load', 'sess', 'main', 'coding', flow=True)
    E([(C[0] + 60, 210), (C[0] + 60, 144)], None, 'reload', 'dep', label=('来源', 'sources'), lpos=(C[0] + 60, 176), lmono=False)
    E([(C[1] + 110, 144), (C[1] + 110, 206)], 'load', 'fac', 'main', 'ext', label='import', lpos=(C[1] + 110, 176))
    E([(C[2] + 82, 144), (C[2] + 82, 334)], 'sess', 'runner', 'main', 'ext', flow=True, label='new', lpos=(C[2] + 82, 250))
    E([(C[1] + 40, 268), (C[1] + 40, 362), (C[2], 362)], 'fac', 'runner', 'event', label=('注册表', 'registrations'), lpos=(C[1] + 40, 336), lmono=False, lsize=10, r=8)
    E([(C[3] + 82, 438), (C[3] + 82, 390)], 'bindx', 'ui', 'main', 'modes')
    E([(C[2] + CW, 362), (C[3], 362)], 'runner', 'ui', 'dep')
    E([(C[3] + 82, 334), (C[3] + 82, 268)], 'ui', 'start', 'event', 'ext')
    E([(C[3] + CW, 362), (C[4], 362)], 'ui', 'emit', 'main', 'ext', flow=True)
    E([(C[4] + 108, 334), (C[4] + 108, 306)], 'emit', None, 'event', 'ext')
    f.legend(24, 540, [('main', ('主流程', 'main flow')), ('event', ('事件 / 回传', 'event / hand-back')), ('dep', ('调用', 'call'))])
    f.note(1096, 544, ('事件为 41 种中的节选 · 实心 = 处理器可改写数据', 'events: a selection of 41 · solid = handler may change data'), 10.5, anchor='end')
    return f

# ============================================================== 10. run modes
@reg
def modes():
    f = Fig('modes', 1120, 504, ('运行模式', 'Run modes'))
    f.node('argv', 24, 208, 170, 56, 'term', 'pi <args>', ('命令行入口', 'CLI entry'), 'terminal', kind='term')
    def tall(nid, x0, y0, w0, h0, layer, title, ic, ts=13):
        g = [f'<g class="nd c-{layer} strong" data-id="{nid}"><rect class="card" x="{x0}" y="{y0}" width="{w0}" height="{h0}" rx="12" filter="url(#pd-sh)"/>',
             f'<rect class="tile" x="{x0+12}" y="{y0+12}" width="26" height="26" rx="7"/>', icon(ic, x0 + 17, y0 + 17, 16)]
        g.append(f.text(x0 + 46, y0 + 30, title, ts, 650, True, cls='n-t', layer=None, owner=nid))
        return g
    x0, y0, w0, h0 = 232, 128, 236, 216
    g = tall('res', x0, y0, w0, h0, 'modes', 'resolveAppMode()', 'filter')
    rules = [('--mode rpc', 'rpc'), ('--mode json', 'json'), ('-p · stdin/stdout ≠ TTY', 'print'), (('否则', 'otherwise'), 'interactive')]
    for i, (c, r) in enumerate(rules):
        yy = y0 + 66 + i * 38
        g.append(f'<g class="stp c-modes"><circle cx="{x0+22}" cy="{yy-4}" r="8"/><text x="{x0+22}" y="{yy-0.4}" text-anchor="middle" font-size="9.5" font-weight="700">{i+1}</text></g>')
        g.append(f.text(x0 + 38, yy, c, 11, 550, isinstance(c, str), cls='n-t', layer=None, owner='res'))
        g.append(f.text(x0 + 38, yy + 15, '→ ' + r, 10.5, 500, True, cls='n-s', layer=None, owner='res'))
    g.append('</g>'); f.L['node'].append(''.join(g)); f.nodes['res'] = (x0, y0, w0, h0); f.solid.append(('res', (x0, y0, w0, h0)))
    f.edge([(194, 236), (232, 236)], 'argv', 'res', 'main', 'modes')
    M = [('rpc', 'runRpcMode()', ('33 种 JSONL 命令 · 响应与事件', '33 JSONL commands · events out'), 'braces', 'stdio'),
         ('json', 'runPrintMode() · json', ('每个事件一行 JSON', 'every event as a JSON line'), 'stream', 'stdout'),
         ('print', 'runPrintMode() · text', ('一次性运行，只输出最终文本', 'one-shot, prints the final text'), 'file', 'stdout'),
         ('im', 'InteractiveMode', ('编辑器 · 聊天视图 · /命令', 'editor · chat viewport · /commands'), 'user', 'TTY')]
    MY = [40, 144, 248, 352]
    for (k, t, sub, ic, io), y in zip(M, MY):
        f.node(k, 540, y, 290, 64, 'modes', t, sub, ic, strong=(k == 'im'), tag=io)
    for (k, *_), y in zip(M, MY):
        yy = y + 32
        f.edge([(468, 236), (500, 236), (500, yy), (540, yy)], 'res', k, 'dep', 'modes', r=8)
    f.raw('<circle cx="500" cy="236" r="2.6" style="fill:var(--modes)"/>', 'label')
    rx, ry, rw, rh = 880, 40, 216, 376
    g = tall('rt', rx, ry, rw, rh, 'coding', 'AgentSessionRuntime', 'layers', ts=12)
    g.append(f.text(rx + 46, ry + 46, ('→ AgentSession', '→ AgentSession'), 10.5, 450, True, cls='n-s', layer=None, owner='rt'))
    g.append(f'<line class="rule" x1="{rx+12}" y1="{ry+60}" x2="{rx+rw-12}" y2="{ry+60}"/>')
    lines = [(84, ('四种模式驱动同一个运行时', 'all four modes drive one runtime'), 'm'),
             (100, ('并各自调用', 'and each calls'), 'm'), (118, 'bindExtensions({ mode })', 'c'),
             (184, ('非交互模式会先接管', 'non-interactive modes'), 'm'), (200, ('stdout，日志转到 stderr', 'take over stdout first'), 'm'),
             (216, ('', 'so logs go to stderr'), 'm'),
             (288, ('RPC 把扩展 UI 请求', 'RPC forwards extension'), 'm'), (304, ('转成', 'UI requests as'), 'm'), (322, 'extension_ui_request', 'c')]
    for yy, t, kind in lines:
        if kind == 'c':
            g.append(f'<rect class="tag" x="{rx+12}" y="{ry+yy-12}" width="{maxw(t,10,600,True)+12:.0f}" height="18" rx="5"/>')
            g.append(f.text(rx + 18, ry + yy + 1, t, 10, 600, True, cls='tag-t', layer=None, owner='rt'))
        elif pair(t)[0] or pair(t)[1]:
            g.append(f.text(rx + 14, ry + yy, t, 10.5, 450, False, cls='n-s', layer=None, owner='rt'))
    g.append('</g>'); f.L['node'].append(''.join(g)); f.nodes['rt'] = (rx, ry, rw, rh); f.solid.append(('rt', (rx, ry, rw, rh)))
    for (k, *_), y in zip(M, MY):
        f.edge([(830, y + 32), (880, y + 32)], k, 'rt', 'main', 'coding', flow=True)
    f.node('tui', 540, 440, 290, 48, 'tui', 'pi-tui', 'TuiMainScreen | TuiAltScreen', 'monitor')
    f.edge([(600, 416), (600, 440)], 'im', 'tui', 'main', 'tui')
    f.text(612, 432, 'createInteractiveTui()', 9.5, 550, True, cls='muted', layer='label')
    f.legend(24, 476, [('main', ('调用 / 驱动', 'calls / drives')), ('layer:modes', ('运行模式', 'run mode')), ('layer:coding', 'pi-coding-agent'), ('layer:tui', 'pi-tui')])
    return f

# ============================================================== 11. providers (hub)
def provider_api_map():
    chat = {'openai-completions', 'mistral-conversations', 'openai-responses', 'azure-openai-responses', 'openai-codex-responses', 'anthropic-messages',
            'bedrock-converse-stream', 'google-generative-ai', 'google-vertex', 'pi-messages'}
    allts = (SRC / 'packages/ai/src/providers/all.ts').read_text()
    files = re.findall(r'^import \{ \w+Provider \} from "\./([a-z0-9-]+)\.ts"', allts, re.M)
    m = {}
    for p in files:
        src = (SRC / f'packages/ai/src/providers/{p}.ts').read_text()
        apis = sorted(set(re.findall(r'from "\.\./api/([a-z-]+)\.lazy\.ts"', src)) & chat)
        m[p] = apis
    return m, chat

API_ORDER = ['openai-completions', 'anthropic-messages', 'openai-responses', 'google-generative-ai', 'azure-openai-responses', 'openai-codex-responses',
             'mistral-conversations', 'google-vertex', 'bedrock-converse-stream', 'pi-messages']
API_COL = ['#10b981', '#d97757', '#0ea5e9', '#4f7cf7', '#6366f1', '#14b8a6', '#f59e0b', '#a855f7', '#ef8a1a', '#ec4899']

@reg
def providers():
    pm, chat = provider_api_map()
    assert len(pm) == 42, len(pm)
    assert set(a for v in pm.values() for a in v) == set(API_ORDER), set(a for v in pm.values() for a in v) ^ set(API_ORDER)
    cnt = {a: sum(a in v for v in pm.values()) for a in API_ORDER}
    f = Fig('providers', 1120, 692, ('Provider 抽象', 'Provider abstraction'))
    css = ''.join(f'.pd .api{i}{{--c:{c}}}' for i, c in enumerate(API_COL))
    f.raw(f'<style>{css}.pd .apidot{{fill:var(--c)}}</style>', 'bg')
    # top: loop -> ModelRuntime
    f.node('loop', 24, 24, 214, 52, 'agent', 'runLoop()', ('streamFn(model, context)', 'streamFn(model, context)'), 'loop', strong=True)
    f.node('mr', 300, 24, 260, 52, 'coding', 'ModelRuntime', ('实现 Models · registerProvider()', 'implements Models · registerProvider()'), 'key', strong=True) if False else f.node('mr', 300, 24, 296, 52, 'coding', 'ModelRuntime', ('实现 Models · registerProvider()', 'implements Models · registerProvider()'), 'key', strong=True)
    f.edge([(238, 50), (300, 50)], 'loop', 'mr', 'main', 'coding', flow=True, step=1, spos=(269, 50))
    # providers panel
    gx, gy, gw, gh = 24, 112, 476, 420
    f.group(gx, gy, gw, gh, 'ai', 'providers/*.ts', (f'{len(pm)} 个内置 · createProvider()', f'{len(pm)} built-in · createProvider()'), 'globe', gid='pv')
    def key(p):
        a = pm[p]
        return (len(a) > 1, API_ORDER.index(a[0]) if a else 99, p)
    order = sorted(pm, key=key)
    x, y = gx + 16, gy + 48
    for p in order:
        apis = pm[p]
        w = maxw(p, 10, 550, True) + 16 + 8 * len(apis)
        if x + w > gx + gw - 14: x = gx + 16; y += 26
        g = [f'<g class="chipg plain"><rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="20" rx="6"/>']
        g.append(f.text(x + 7, y + 13.8, p, 10, 550, True, cls='chip-t', layer=None, owner='chip'))
        dx = x + w - 8 * len(apis) - 2
        for a in apis:
            g.append(f'<circle class="apidot api{API_ORDER.index(a)}" cx="{dx+3:.1f}" cy="{y+10}" r="3"/>'); dx += 8
        if not apis:
            pass
        g.append('</g>'); f.L['node'].append(''.join(g))
        x += w + 6
    cy_ = y + 34
    f.raw(f'<rect class="codebg" x="{gx+16}" y="{cy_}" width="{gw-32}" height="64" rx="8"/>', 'node')
    f.text(gx + 28, cy_ + 20, 'interface Provider {', 10.5, 600, True, cls='strongt', layer='label')
    f.text(gx + 40, cy_ + 37, 'id · name · baseUrl? · headers? · auth', 10.5, 450, True, cls='muted', layer='label')
    f.text(gx + 40, cy_ + 53, 'getModels() · stream() · streamSimple() }', 10.5, 450, True, cls='muted', layer='label')
    f.legend(24, 674, [('main', ('调用', 'call')), ('event', ('事件流回到 runLoop', 'event stream back to runLoop')), ('step', ('顺序', 'order'))])
    f.raw(f'<g class="api0"><circle class="apidot" cx="520" cy="674" r="4"/></g><g class="api1"><circle class="apidot" cx="530" cy="674" r="4"/></g>', 'label')
    f.text(542, 678, ('= provider 使用的对话 API（typesafe 只有分类器 API）', '= chat APIs a provider uses (typesafe has only a classifier API)'), 11, 500, cls='lg-t', layer='label')
    # hub
    hx, hy, hw, hh = 548, 238, 180, 168
    f.node('hub', hx, hy, hw, hh, 'ai', 'Models', None, None, strong=True, align='center') if False else None
    g = [f'<g class="nd c-ai strong" data-id="hub"><rect class="card" x="{hx}" y="{hy}" width="{hw}" height="{hh}" rx="16" filter="url(#pd-sh)"/>',
         f'<circle cx="{hx+hw/2}" cy="{hy+40}" r="22" style="fill:color-mix(in srgb,var(--ai) 15%,transparent);stroke:color-mix(in srgb,var(--ai) 50%,transparent)"/>',
         icon('hub', hx + hw / 2 - 12, hy + 28, 24)]
    g.append(f.text(hx + hw / 2, hy + 86, 'Models', 14, 700, True, 'middle', 'n-t', layer=None, owner='hub'))
    g.append(f.text(hx + hw / 2, hy + 104, ('provider / model 注册表', 'provider · model registry'), 10.5, 450, False, 'middle', 'n-s', layer=None, owner='hub'))
    for i, l in enumerate(['getModel(provider, id)', 'checkAuth · getAuth', 'provider.streamSimple()']):
        g.append(f.text(hx + hw / 2, hy + 126 + i * 14, l, 9.5, 500, True, 'middle', 'n-s', layer=None, owner='hub'))
    g.append('</g>'); f.L['node'].append(''.join(g)); f.nodes['hub'] = (hx, hy, hw, hh); f.solid.append(('hub', (hx, hy, hw, hh)))
    f.edge([(500, 322), (548, 322)], 'pv', 'hub', 'main', 'ai', start=True)
    f.step(2, 524, 304, 'ai')
    f.edge([(596, 50), (638, 50), (638, 238)], 'mr', 'hub', 'main', 'ai', flow=True, label='streamSimple()', lpos=(638, 160), r=10)
    # API panel
    ax, ay, aw = 790, 112, 306
    f.group(ax, ay, aw, 420, 'ai', 'api/*.lazy.ts', ('10 种对话 API（KnownApi）', '10 chat APIs (KnownApi)'), 'braces', gid='apis')
    f.step(3, 762, 304, 'ai')
    for i, a in enumerate(API_ORDER):
        yy = ay + 46 + i * 36
        k = 'api-' + a
        f.node(k, ax + 30, yy, aw - 46, 30, 'ai', a, None, None, tsize=11, tweight=600, tag=f'×{cnt[a]}')
        f.raw(f'<circle class="apidot api{i}" cx="{ax+30+aw-46-0:.1f}" cy="{yy+15}" r="0"/>', 'label')
        f.raw(f'<g class="api{i}"><circle class="apidot" cx="{ax+16}" cy="{yy+15}" r="5"/></g>', 'label')
    bus = 752
    for i, a in enumerate(API_ORDER):
        yy = ay + 46 + i * 36 + 15
        f.edge([(728, 322), (bus, 322), (bus, yy), (ax + 30, yy)] if abs(yy - 322) > 1 else [(728, 322), (ax + 30, yy)], 'hub', 'api-' + a, 'dep', 'ai', r=6)
    f.raw(f'<circle cx="{bus}" cy="322" r="2.8" style="fill:var(--ai)"/>', 'label')
    f.note(ax + 16, ay + 408, ('lazyApi()：首次流式调用时才 import 模块', 'lazyApi(): module imported on its first stream call'), 10)
    # event stream band
    ey = 570
    f.group(24, ey, 1072, 92, 'ai', 'AssistantMessageEventStream', ('每个 API 都归一成这 12 种事件 · 失败也是事件，从不抛出', 'every API normalizes to these 12 events · failures are events, never throws'), 'stream', gid='es')
    evs = ['start', 'text_start', 'text_delta', 'text_end', 'thinking_start', 'thinking_delta', 'thinking_end', 'toolcall_start', 'toolcall_delta', 'toolcall_end', 'done', 'error']
    x = 44
    for e in evs:
        x += f.chip(x, ey + 50, e, 'err' if e == 'error' else 'ai', size=10, h=22, cls='solid' if e in ('done', 'error') else '') + 6
    f.edge([(943, 532), (943, 570)], 'apis', 'es', 'main', 'ai', flow=True)
    f.step(4, 943, 551, 'ai')
    f.edge([(24, 616), (12, 616), (12, 50), (24, 50)], 'es', 'loop', 'event', 'agent', r=8)
    f.note(1096, 551, 'stream() · streamSimple()', 10.5, anchor='end', mono=True) if False else None
    f.text(959, 555, 'stream() · streamSimple()', 10, 550, True, cls='muted', layer='label')
    f.note(250, 98, ('事件流回到 runLoop（左侧虚线）', 'events flow back to runLoop (dashed, left)'), 10) if False else None
    return f

# ============================================================== 12. TUI
@reg
def tui():
    f = Fig('tui', 1120, 450, ('TUI 渲染', 'TUI rendering'))
    R1, R2, H = 72, 300, 60
    C = [20, 242, 464, 686, 908]; W = 196
    N = f.node
    N('stdin', C[0], R1, W, H, 'term', 'stdin', ('批量到达的字节', 'bytes arrive in batches'), 'keyboard', kind='term')
    N('pt', C[1], R1, W, H, 'tui', 'ProcessTerminal', ('StdinBuffer 切分按键', 'StdinBuffer splits keys'), 'terminal', tsize=12)
    N('comp', C[2], R1, W, H, 'tui', ('焦点组件', 'focused Component'), 'handleInput(data)', 'eye', mono=False)
    N('rq', C[3], R1, W, H, 'tui', 'requestRender()', ('nextTick 合并', 'coalesced on nextTick'), 'inbox', strong=True, tsize=12)
    N('sch', C[4], R1, W, H, 'tui', 'scheduleRender()', ('帧间隔 ≥ 16 ms', '≥ 16 ms between frames'), 'clock', strong=True, tsize=12)
    N('ev', C[2], 186, W, 52, 'modes', ('agent 事件', 'agent events'), ('InteractiveMode 更新', 'InteractiveMode updates'), 'bolt', mono=False)
    N('dr', C[4], R2, W, H, 'tui', 'doRender()', 'render(width) → string[]', 'layers', strong=True, tsize=12, ssize=10.5)
    N('ov', C[3], R2, W, H, 'tui', ('合成 overlay', 'composite overlays'), ('弹窗、选择器叠在上面', 'dialogs · selectors on top'), 'stack', mono=False)
    N('diff', C[2], R2, W, H, 'tui', ('对比 previousLines', 'diff previousLines'), ('找出变化的行', 'find changed lines'), 'diff', mono=False, strong=True)
    N('wr', C[1], R2, W, H, 'tui', ('只写变化的行', 'write changed lines'), 'CSI ?2026h … ?2026l', 'terminal', mono=False, strong=True)
    E = f.edge
    m1, m2 = R1 + H / 2, R2 + H / 2
    for i, (a, b) in enumerate((('stdin', 'pt'), ('pt', 'comp'), ('comp', 'rq'), ('rq', 'sch'))):
        xa = C[i] + W
        E([(xa, m1), (C[i + 1], m1)], a, b, 'main', 'tui', flow=i == 3, step=i + 1, spos=(xa + 13, m1))
    E([(C[4] + 130, R1 + H), (C[4] + 130, R2)], 'sch', 'dr', 'main', 'tui', flow=True, step=5, spos=(C[4] + 130, 200))
    for i, (a, b) in enumerate((('dr', 'ov'), ('ov', 'diff'), ('diff', 'wr'))):
        xb = C[3 - i] + W
        E([(C[4 - i], m2), (xb, m2)], a, b, 'main', 'tui', flow=True, step=6 + i, spos=(xb + 13, m2))
    E([(C[2] + W, 212), (C[3] + 50, 212), (C[3] + 50, R1 + H)], 'ev', 'rq', 'event', 'modes', r=8)
    E([(C[3] + 150, R1 + H), (C[3] + 150, 248), (C[4] + 50, 248), (C[4] + 50, R2)], 'rq', 'dr', 'dev', label='force = true', lpos=((C[3] + 150 + C[4] + 50) / 2, 248), lsize=10, r=8)
    tx, ty, tw_, th = C[0], 196, W, 196
    g = [f'<g class="nd c-term k-mock" data-id="term"><rect class="card" x="{tx}" y="{ty}" width="{tw_}" height="{th}" rx="12" filter="url(#pd-sh)" style="fill:#0d1117;stroke:#30363d"/>']
    for i, c in enumerate(('#ff5f57', '#febc2e', '#28c840')):
        g.append(f'<circle cx="{tx+16+i*14}" cy="{ty+15}" r="4.5" style="fill:{c}"/>')
    lines = [('> fix the failing test', 0), ('● read math.test.ts', 0), ('● bash npm test', 0), ('  ✓ 41 passed', 1), ('  ✓ 1 fixed', 1), ('Done. The test now…', 1), ('─' * 22, 0), ('▌', 0)]
    for i, (l, ch) in enumerate(lines):
        yy = ty + 40 + i * 18
        if ch: g.append(f'<rect x="{tx+6}" y="{yy-12}" width="{tw_-12}" height="17" rx="3" style="fill:rgba(236,72,153,.24)"/>')
        g.append(f'<text x="{tx+14}" y="{yy}" font-size="10.5" class="mono" style="fill:{"#f9a8d4" if ch else "#c9d1d9"}">{esc(l)}</text>')
    g.append('</g>'); f.L['node'].append(''.join(g)); f.nodes['term'] = (tx, ty, tw_, th); f.solid.append(('term', (tx, ty, tw_, th)))
    E([(C[1], m2), (tx + tw_, m2)], 'wr', 'term', 'main', 'tui', flow=True, step=9, spos=(tx + tw_ + 13, m2))
    f.note(tx, ty + th + 18, ('高亮 = 本帧重写的行', 'highlighted = rewritten this frame'), 10.5)
    f.text(C[2], 38, ('组件契约', 'COMPONENT CONTRACT'), 10.5, 700, cls='cf c-tui', layer='label', ls='.04em')
    x = C[2] + maxw(('组件契约', 'COMPONENT CONTRACT'), 10.5, 700) + 16
    for s in ('render(width): string[]', 'handleInput?(data)', 'invalidate()'):
        x += f.chip(x, 24, s, 'tui', size=10, h=22) + 6
    f.legend(C[1], 432, [('main', ('一帧的路径', 'one frame')), ('event', ('异步事件', 'async event')), ('dev', ('force：重置并立即全量重绘', 'force: reset + immediate full redraw'))])
    return f
