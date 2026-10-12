# Keynote-style slide deck. Each slide: dict(kind, ...). Rendered into slides.html by render_slides().
SLIDES = [
 dict(kind='title'),
 dict(kind='stack', kicker=('一句话', 'In one sentence'),
      title=('Pi 是四层，每层只认识下一层', 'Pi is four layers, each knowing only the next'),
      sub=('运行模式 → AgentSession → Agent 循环 → pi-ai 事件流。产品逻辑全部以钩子形式注入通用循环。', 'Run mode → AgentSession → agent loop → pi-ai event stream. All product logic is injected into a generic loop as hooks.')),
 dict(kind='numbers', kicker=('规模', 'By the numbers'), title=('一个中等体量、测试充分的 monorepo', 'A mid-sized, well-tested monorepo')),
 dict(kind='wide', layer='coding', diagram='packages', kicker=('01 · 包', '01 · Packages'),
      title=('14 个包，运行时栈只有四层深', '14 packages, a runtime stack four deep'),
      note=('`pi-ai` 只依赖 `pi-telemetry`；`pi-tui`、`pi-mcp`、`pi-codemode`、`chord` 零内部依赖。', '`pi-ai` depends only on `pi-telemetry`; `pi-tui`, `pi-mcp`, `pi-codemode` and `chord` have no internal deps.')),
 dict(kind='side', layer='coding', diagram='layers', kicker=('02 · 分层', '02 · Layers'),
      title=('请求自上而下穿过四层', 'A request flows down four layers'),
      points=[('模式层只和 `AgentSessionRuntime` 对话', 'Modes only talk to `AgentSessionRuntime`'),
              ('`AgentSession` 把策略挂到 `Agent` 钩子上', '`AgentSession` hangs policy on `Agent` hooks'),
              ('`streamFn` = `modelRuntime.streamSimple()`', '`streamFn` = `modelRuntime.streamSimple()`'),
              ('只有 interactive 模式使用 `pi-tui`', 'Only interactive mode uses `pi-tui`')]),
 dict(kind='side', layer='agent', diagram='loop_compact', kicker=('03 · Agent 循环', '03 · Agent loop'),
      title=('两层循环驱动一切', 'Two nested loops drive everything'),
      points=[('内层：有工具调用或 steering 消息就继续', 'Inner: continue while tool calls or steering remain'),
              ('外层：follow-up 消息到达时重启', 'Outer: restart when follow-ups arrive'),
              ('`stopReason: length` → 所有工具调用失败', '`stopReason: length` → every tool call fails'),
              ('`finishTurn` 可返回 `end` / `continue`', '`finishTurn` may return `end` / `continue`')]),
 dict(kind='compare', layer='agent', kicker=('03 · 消息队列', '03 · Message queues'),
      title=('用户可以在 Agent 运行时插话', 'Users can talk while the agent works'),
      cols=[(('Steering', 'Steering'), ('当前轮工具执行完成后、下一次 LLM 请求前注入。适合“停，换个方向”。', 'Injected after the current turn\'s tools finish, before the next LLM request. For “stop, go another way”.'), '`agent.steer()` · `getSteeringMessages()`'),
            (('Follow-up', 'Follow-up'), ('只在 Agent 本该停止时投递，触发外层循环。适合“做完之后再……”。', 'Delivered only when the agent would stop, driving the outer loop. For “when you’re done, also…”.'), '`agent.followUp()` · `getFollowUpMessages()`'),
            (('finishTurn', 'finishTurn'), ('每轮结束的决策钩子：`end` 立即结束；`continue` 在无新消息时再跑一轮仅含上下文的请求。', 'End-of-turn decision hook: `end` stops now; `continue` runs one more context-only turn when nothing is queued.'), '`AgentLoopConfig.finishTurn`')]),
 dict(kind='wide', layer='agent', diagram='toolexec_compact', kicker=('04 · 工具执行', '04 · Tool execution'),
      title=('每个工具调用走同一条管道', 'One pipeline for every tool call'),
      note=('失败永远是结果而不是异常。并行模式：准备按顺序、执行并发、结果按原顺序发出；任何一个 `sequential` 工具会让整批串行。', 'Failures are results, never throws. Parallel mode: prepare in order, execute concurrently, emit results in source order; one `sequential` tool serializes the batch.')),
 dict(kind='side', layer='coding', diagram='sequence_compact', kicker=('05 · 时序', '05 · Sequence'),
      title=('一次提示：两次请求，一次工具调用', 'One prompt: two requests, one tool call'),
      points=[('扩展先拦截：`input` → `before_agent_start`', 'Extensions intercept first: `input` → `before_agent_start`'),
              ('每个 delta 变成 `message_update`', 'Every delta becomes `message_update`'),
              ('工具结果回到上下文，循环自动发起第二次请求', 'Tool results rejoin the context; the loop sends request 2'),
              ('每个 `message_end` 都写入 JSONL', 'Every `message_end` is written to JSONL')]),
 dict(kind='events', layer='ai', kicker=('05 · 事件', '05 · Events'),
      title=('一个协议贯穿所有 provider', 'One protocol across every provider')),
 dict(kind='wide', layer='coding', diagram='classes_compact', kicker=('06 · 核心类型', '06 · Key types'),
      title=('谁持有谁', 'Who owns what'),
      note=('`ModelRuntime` 实现 pi-ai 的 `Models` 接口；`ExtensionRunner` 由 `AgentSession` 创建。', '`ModelRuntime` implements pi-ai\'s `Models`; `ExtensionRunner` is created by `AgentSession`.')),
 dict(kind='side', layer='coding', diagram='session', kicker=('07 · 会话', '07 · Sessions'),
      title=('一个 JSONL 文件就是一棵树', 'One JSONL file is a tree'),
      points=[('每个条目带 `id` + `parentId`', 'Every entry has `id` + `parentId`'),
              ('`leafId` 指向当前位置', '`leafId` marks the current position'),
              ('分支 = 移动 leaf，从不改写历史', 'Branching = moving the leaf, never rewriting'),
              ('11 种条目类型，含 `compaction`、`context_edit`', '11 entry types incl. `compaction`, `context_edit`')]),
 dict(kind='side', layer='coding', diagram='compaction', kicker=('08 · 压缩', '08 · Compaction'),
      title=('三种触发，一条路径', 'Three triggers, one path'),
      big=[('16,384', ('默认 reserveTokens', 'default reserveTokens')), ('20,000', ('默认 keepRecentTokens', 'default keepRecentTokens')), ('1×', ('溢出后只重试一次', 'retry once after overflow'))]),
 dict(kind='side', layer='ext', diagram='extensions_compact', kicker=('09 · 扩展', '09 · Extensions'),
      title=('从发现到事件分发', 'From discovery to dispatch'),
      points=[('来源：`~/.pi/agent/extensions`、`.pi/extensions`、settings packages、`-e`', 'Sources: `~/.pi/agent/extensions`, `.pi/extensions`, settings packages, `-e`'),
              ('jiti 直接加载 TypeScript，无需构建', 'jiti loads TypeScript directly, no build step'),
              ('`bindCore()` 之后注册才连到真实会话', 'Registrations reach the real session after `bindCore()`'),
              ('UI 由运行模式通过 `bindExtensions()` 提供', 'UI is supplied by the mode via `bindExtensions()`')],
      _note=('来源：`~/.pi/agent/extensions`、`.pi/extensions`、settings packages、`-e`；用 jiti 直接加载 TypeScript。', 'Sources: `~/.pi/agent/extensions`, `.pi/extensions`, settings packages, `-e`; TypeScript loaded directly with jiti.')),
 dict(kind='api', layer='ext', kicker=('09 · ExtensionAPI', '09 · ExtensionAPI'),
      title=('扩展几乎能改变一切', 'Extensions can change almost anything')),
 dict(kind='wide', layer='modes', diagram='modes', kicker=('10 · 运行模式', '10 · Run modes'),
      title=('四种模式，一个运行时', 'Four modes, one runtime'),
      note=('RPC 模式：33 种 JSONL 命令，扩展 UI 请求以 `extension_ui_request` 代理给宿主。', 'RPC mode: 33 JSONL command types; extension UI requests are proxied as `extension_ui_request`.')),
 dict(kind='wide', layer='ai', diagram='providers_compact', kicker=('11 · Provider', '11 · Providers'),
      title=('42 个 provider，10 种对话 API', '42 providers, 10 chat APIs'),
      note=('API 模块经 `lazyApi()` 在首次调用时才 import；失败编码为 `error` 事件，从不抛出。', 'API modules are imported on first use via `lazyApi()`; failures become `error` events, never throws.')),
 dict(kind='wide', layer='tui', diagram='tui', kicker=('12 · TUI', '12 · TUI'),
      title=('只重写变化的行', 'Rewrite only what changed'),
      note=('组件只实现 `render(width) → string[]`；`requestRender()` 在 nextTick 合并，两帧间隔 ≥ 16 ms，再与 `previousLines` 做差分，在同步输出中只写变化的行。', 'Components implement only `render(width) → string[]`; `requestRender()` coalesces on nextTick, frames are ≥ 16 ms apart, then a diff against `previousLines` writes only changed lines inside synchronized output.')),
 dict(kind='bars', layer='infra', kicker=('13 · 仓库', '13 · Repository'),
      title=('代码都在哪里', 'Where the code lives')),
 dict(kind='close', kicker=('总结', 'Takeaways'), title=('值得借鉴的五个设计', 'Five design choices worth stealing')),
]

def render_slides(T, md, FACTS, STATS, SRC_LOC, TEST_LOC, SHORT, SHA, GH, COMMIT_DATE, ICON, PKG_LAYER, LAYER_NAME, fmt, FIGS, DEFS):
    N = len(SLIDES)
    def dia(key):
        key = key.replace('_compact', '')
        return f'<div class="dia"><div class="dg" data-dg="{key}">{FIGS[key].svg()}</div></div>'
    def kick(s, layer=None):
        L = layer or s.get('layer')
        chip = f'<span class="chip L-{L}">{LAYER_NAME[L]}</span>' if L and L in LAYER_NAME else ''
        return f'<div class="kicker"><span class="k">{T(s["kicker"])}</span>{chip}</div>'
    out = []
    for i, s in enumerate(SLIDES, 1):
        k = s['kind']; L = s.get('layer', 'coding')
        if k == 'title':
            inner = f'''<div class="title-wrap"><div class="eyebrow"><b>{SHORT}</b>earendil-works/pi · {COMMIT_DATE[:10]}</div>
<h1>{T(("读懂 Pi", "Inside Pi"))}</h1>
<p class="title-sub">{T(("一个可扩展编码智能体内核的架构", "The architecture of an extensible coding-agent core"))}</p>
<div class="title-layers">{''.join(f'<span class="chip L-{x}">{LAYER_NAME[x]}</span>' for x in ['modes','coding','ext','agent','ai','tui'])}</div>
<p class="hint">{T(("← → 翻页 · F 全屏 · O 目录 · T 明暗 · L 语言", "← → navigate · F fullscreen · O overview · T theme · L language"))}</p></div>
<div class="orb o1"></div><div class="orb o2"></div><div class="orb o3"></div>'''
        elif k == 'stack':
            inner = f'''{kick(s)}<div class="two"><div><h2>{T(s["title"])}</h2><p class="sub">{T(s["sub"])}</p></div>
<div class="tiers"><div class="tier L-modes"><b>Run modes</b><span>interactive · print · json · rpc</span></div><div class="arrow">↓</div>
<div class="tier L-coding"><b>pi-coding-agent</b><span>AgentSession · tools · sessions · extensions</span></div><div class="arrow">↓</div>
<div class="tier L-agent"><b>pi-agent-core</b><span>Agent · runLoop()</span></div><div class="arrow">↓</div>
<div class="tier L-ai"><b>pi-ai</b><span>{FACTS["providers"]} providers → AssistantMessageEventStream</span></div></div></div>'''
        elif k == 'numbers':
            cards = [(str(FACTS['packages']), ('workspace 包', 'packages'), 'coding'), (f'{SRC_LOC/1000:.0f}k', ('行源码', 'src LOC'), 'agent'),
                     (f'{TEST_LOC/1000:.0f}k', ('行测试', 'test LOC'), 'ai'), (str(FACTS['providers']), ('LLM provider', 'LLM providers'), 'ai'),
                     (str(FACTS['tools']), ('内置工具', 'built-in tools'), 'coding'), (str(FACTS['ext_events']), ('扩展事件', 'extension events'), 'ext'),
                     (str(FACTS['rpc']), ('RPC 命令', 'RPC commands'), 'modes'), (str(FACTS['ai_events']), ('流事件类型', 'stream event types'), 'ai')]
            inner = kick(s, 'infra') + f'<h2>{T(s["title"])}</h2><div class="nums">' + ''.join(
                f'<div class="num L-{l}"><div class="n">{n}</div><div class="l">{T(lb)}</div></div>' for n, lb, l in cards) + '</div>'
        elif k == 'wide':
            inner = f'''{kick(s)}<h2>{T(s["title"])}</h2>{dia(s["diagram"])}
<p class="note">{T(s["note"])}</p>''' + (('<div class="bigrow">' + ''.join(f'<div class="big"><div class="n">{n}</div><div class="l">{T(lb)}</div></div>' for n, lb in s['big']) + '</div>') if s.get('big') else '')
        elif k == 'side':
            extra = ''
            if 'points' in s:
                extra = '<ul class="pts">' + ''.join(f'<li>{T(p)}</li>' for p in s['points']) + '</ul>'
            if 'big' in s:
                extra = '<div class="bigs">' + ''.join(f'<div class="big"><div class="n">{n}</div><div class="l">{T(lb)}</div></div>' for n, lb in s['big']) + '</div>'
            inner = f'''<div class="sidegrid"><div class="sidetext">{kick(s)}<h2>{T(s["title"])}</h2>{extra}</div>
{dia(s["diagram"])}</div>'''
        elif k == 'compare':
            inner = kick(s) + f'<h2>{T(s["title"])}</h2><div class="cols">' + ''.join(
                f'<div class="col"><div class="ct">{T(t)}</div><p>{T(b)}</p><div class="api">{md(a)}</div></div>' for t, b, a in s['cols']) + '</div>'
        elif k == 'events':
            ai_ev = ['start', 'text_start', 'text_delta', 'text_end', 'thinking_start', 'thinking_delta', 'thinking_end', 'toolcall_start', 'toolcall_delta', 'toolcall_end', 'done', 'error']
            ag_ev = ['agent_start', 'turn_start', 'message_start', 'message_update', 'message_end', 'tool_execution_start', 'tool_execution_update', 'tool_execution_end', 'turn_end', 'agent_end']
            inner = f'''{kick(s)}<h2>{T(s["title"])}</h2><div class="evgrid">
<div class="evcol L-ai"><div class="evh">pi-ai · AssistantMessageEvent · {len(ai_ev)}</div><div class="evs">{''.join(f'<code>{e}</code>' for e in ai_ev)}</div></div>
<div class="evmid">→</div>
<div class="evcol L-agent"><div class="evh">pi-agent-core · AgentEvent</div><div class="evs">{''.join(f'<code>{e}</code>' for e in ag_ev)}</div></div></div>
<p class="note">{T(("provider 增量在 agent 层变成 `message_update`；工具与轮次事件由循环自己发出。`StreamFn` 约定：不抛异常，失败以 `error` 事件编码。", "Provider deltas become `message_update` in the agent layer; tool and turn events are emitted by the loop itself. `StreamFn` contract: never throw, encode failures as `error`."))}</p>'''
        elif k == 'api':
            reg = ['registerTool', 'registerCommand', 'registerShortcut', 'registerFlag', 'registerProvider', 'registerMcpServer', 'registerMessageRenderer', 'registerEntryRenderer', 'registerToolRenderer', 'registerVirtualModel']
            act = ['sendMessage', 'sendUserMessage', 'appendEntry', 'exec', 'setActiveTools', 'setSessionName', 'setLabel', 'on(event)']
            mut = [('input', ('改写或吞掉输入', 'rewrite or swallow input')), ('context', ('改写发给模型的消息', 'rewrite messages sent to the model')),
                   ('before_provider_request', ('改写请求负载', 'rewrite the request payload')), ('tool_call', ('阻止工具调用', 'block a tool call')),
                   ('tool_result', ('改写工具结果', 'rewrite a tool result')), ('session_before_compact', ('取消或替换压缩', 'cancel or replace compaction'))]
            inner = f'''{kick(s)}<h2>{T(s["title"])}</h2><div class="apigrid">
<div class="apibox"><div class="evh">{T(("注册能力", "Register"))}</div><div class="evs">{''.join(f'<code>{x}</code>' for x in reg)}</div>
<div class="evh" style="margin-top:22px">{T(("会话动作", "Act on the session"))}</div><div class="evs">{''.join(f'<code>{x}</code>' for x in act)}</div></div>
<div class="apibox"><div class="evh">{T((f"{FACTS['ext_events']} 种事件中可改写数据的", f"Of {FACTS['ext_events']} events, the ones that change data"))}</div>
<div class="mut">{''.join(f'<div><code>{e}</code><span>{T(d)}</span></div>' for e, d in mut)}</div></div></div>'''
        elif k == 'bars':
            rows = sorted(STATS, key=lambda x: -x['src_loc'])
            mx = max(r['src_loc'] + r['test_loc'] for r in rows)
            bars = ''.join(f'<div class="bar L-{PKG_LAYER.get(r["pkg"], "infra")}"><span class="nm">{r["pkg"]}</span><span class="tr"><span class="s" style="width:{r["src_loc"]/mx*100:.2f}%"></span><span class="t" style="width:{r["test_loc"]/mx*100:.2f}%"></span></span><span class="v">{fmt(r["src_loc"])}</span></div>' for r in rows)
            ca = next(r for r in STATS if r['pkg'] == 'coding-agent')
            inner = f'''{kick(s)}<div class="sidegrid bars-grid"><div class="sidetext"><h2>{T(s["title"])}</h2>
<div class="bigs"><div class="big"><div class="n">{ca["src_loc"]/SRC_LOC*100:.0f}%</div><div class="l">{T(("的源码在 coding-agent", "of source is coding-agent"))}</div></div>
<div class="big"><div class="n">{TEST_LOC/SRC_LOC:.2f}×</div><div class="l">{T(("测试 / 源码 行数比", "test-to-source line ratio"))}</div></div></div>
<p class="note">{T(("实色 = 源码，浅色 = 测试。仅 .ts，不含 .d.ts。", "Solid = source, light = tests. .ts only, no .d.ts."))}</p></div>
<div class="bars">{bars}</div></div>'''
        elif k == 'close':
            items = [
              (('通用循环 + 钩子', 'Generic loop + hooks'), ('`pi-agent-core` 不知道“编码”；压缩、权限、工具清单全部通过 `AgentLoopConfig` 注入。', '`pi-agent-core` knows nothing about coding; compaction, permissions and tool loadout arrive through `AgentLoopConfig`.'), 'agent'),
              (('失败即数据', 'Failures are data'), ('流错误是 `error` 事件，工具错误是 `isError` 结果——循环从不需要 try/catch 逃逸。', 'Stream errors are `error` events and tool errors are `isError` results — the loop never unwinds.'), 'ai'),
              (('追加式会话树', 'Append-only session tree'), ('分支、压缩、上下文编辑都是新条目，历史永不改写。', 'Branches, compactions and context edits are all new entries; history is never rewritten.'), 'coding'),
              (('Provider ≠ API', 'Provider ≠ API'), ('42 个 provider 复用 10 种对话 API（`KnownApi`），并且按需懒加载。', '42 providers reuse 10 chat APIs (`KnownApi`), loaded lazily.'), 'ai'),
              (('一切皆可扩展', 'Everything is extensible'), (f"{FACTS['ext_events']} 种事件 + `register*` API，用 jiti 直接加载 TypeScript。", f"{FACTS['ext_events']} events plus the `register*` API, TypeScript loaded directly with jiti."), 'ext'),
            ]
            inner = kick(s, 'coding') + f'<h2>{T(s["title"])}</h2><div class="closing">' + ''.join(
                f'<div class="ci L-{l}"><div class="cn">{j}</div><div><div class="ct">{T(t)}</div><p>{T(b)}</p></div></div>' for j, (t, b, l) in enumerate(items, 1)) + \
                f'</div><div class="links"><a href="index.html">{T(("← 返回完整图解", "← Back to the full walkthrough"))}</a><a href="{GH}/tree/{SHA}" target="_blank" rel="noopener">github.com/earendil-works/pi · {SHORT}</a></div>'
        out.append(f'<section class="slide k-{k} L-{L}" data-i="{i}" aria-roledescription="slide" aria-label="{i} / {N}">{inner}<div class="foot"><span>Pi · {SHORT}</span><span>{i:02d}</span></div></section>')
    titles = []
    for i, s in enumerate(SLIDES, 1):
        t = s.get('title') or ('读懂 Pi', 'Inside Pi')
        titles.append(f'<button type="button" data-go="{i}" class="L-{s.get("layer", "coding")}"><span class="no">{i:02d}</span>{T(t)}</button>')
    return f'''<body class="deck" data-title-zh="读懂 Pi · 演示" data-title-en="Inside Pi · Slides">
<div class="viewport" id="viewport"><div class="stage" id="stage">{"".join(out)}</div></div>
<div class="hud" id="hud">
<div class="hud-l"><a class="hb" href="index.html" data-i18n-title="返回图解|Back to site">←</a>
<button class="hb" type="button" id="prev" data-i18n-title="上一页|Previous">‹</button><button class="hb" type="button" id="next" data-i18n-title="下一页|Next">›</button>
<button class="hb" type="button" id="ov" data-i18n-title="目录 (O)|Overview (O)">▦</button>
<button class="hb" type="button" id="fs" data-i18n-title="全屏 (F)|Fullscreen (F)">⛶</button>
<button class="hb" type="button" id="th" data-i18n-title="明暗 (T)|Theme (T)">◐</button>
<button class="hb" type="button" id="lg" data-i18n-title="语言 (L)|Language (L)"><span class="zh">EN</span><span class="en">中</span></button></div>
<div class="count"><b id="cur">1</b> / {N}</div></div>
<div class="bar-progress"><i id="prog"></i></div>
<div class="overview" id="overview" hidden><div class="ov-in"><div class="ov-h">{T(("全部幻灯片", "All slides"))}<button class="hb" type="button" id="ov-x">✕</button></div><div class="ov-grid">{"".join(titles)}</div></div></div>
<script src="assets/dg.js"></script><script src="assets/slides.js"></script>
</body></html>'''
