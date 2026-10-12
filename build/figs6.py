"""pi-tui deep-dive diagrams (tui_*). Facts read from /workspace/pi-src/packages/tui at build time."""
import re
from svgkit import Fig, maxw, pair
from figs import reg
from figkit import SRC, uml, codebox, bar, dot, hline, vline, chiprow, lines_of

T = 'packages/tui/src/'
def _src(p): return (SRC / (T + p)).read_text()
def loc(p): return lines_of(T + p)
def L(n): return (f'{n:,} 行', f'{n:,} lines')
def has(p, *needles):
    s = _src(p)
    for n in needles: assert n in s, (p, n)
def components():
    return sorted(x.stem for x in (SRC / (T + 'components')).glob('*.ts') if not x.name.endswith(('.test.ts', '.d.ts')))
def total_loc():
    return sum(lines_of(str(x.relative_to(SRC))) for x in (SRC / T).rglob('*.ts') if not x.name.endswith(('.test.ts', '.d.ts')))
def kb_ids():
    ids = sorted(set(re.findall(r'"(tui\.[a-zA-Z]+\.[a-zA-Z.]+)"', _src('keybindings.ts'))))
    out = {}
    for i in ids: out.setdefault(i.split('.')[1], []).append(i)
    return out
def iface(name, p='tui.ts'):
    m = re.search(r'^export interface ' + name + r'\b[^{]*\{(.*?)^\}', _src(p), re.M | re.S)
    out = []
    for n in re.findall(r'^\t(?:readonly )?([a-zA-Z]+)\??[(:<]', m.group(1), re.M):
        if n not in out: out.append(n)
    return out

# ============================================================== tui_arch
@reg
def tui_arch():
    tot = total_loc()
    f = Fig('tui_arch', 1120, 600, (f'pi-tui 模块结构（{tot:,} 行 TypeScript）', f'pi-tui modules ({tot:,} lines of TypeScript)'))
    COLS = [(('终端与输入', 'Terminal & input'), 'infra', 'keyboard', [
                ('terminal.ts', ('ProcessTerminal · 协议协商', 'ProcessTerminal · negotiation')),
                ('stdin-buffer.ts', ('字节流 → 完整序列', 'bytes → whole sequences')),
                ('keys.ts', ('parseKey · matchesKey', 'parseKey · matchesKey')),
                ('keybindings.ts', ('可配置的按键 id', 'configurable key ids')),
                ('native-platform.ts', ('剪贴板 · 修饰键（可选）', 'clipboard · modifiers (opt.)')),
                ('program-status.ts', ('OSC 7501 程序状态', 'OSC 7501 program status'))]),
            (('渲染核心', 'Render core'), 'tui', 'monitor', [
                ('tui.ts', ('Component · TuiBase · 覆盖层', 'Component · TuiBase · overlays')),
                ('tui-main-screen.ts', ('regular：行级差分', 'regular: line diff')),
                ('tui-alt-screen.ts', ('fullscreen：备用屏', 'fullscreen: alt screen')),
                ('layout.ts', ('布局帧 · 滚动条', 'layout frame · scrollbars')),
                ('alt-screen-search.ts', ('全屏内搜索', 'in-screen search')),
                ('wheel-scroll.ts', ('滚轮加速', 'wheel acceleration'))]),
            (('编辑', 'Editing'), 'coding', 'code', [
                ('components/editor.ts', ('多行编辑器', 'multi-line editor')),
                ('autocomplete.ts', ('/ 命令 · @ 文件 · 路径', '/ commands · @ files · paths')),
                ('undo-stack.ts', ('快照式撤销', 'snapshot undo')),
                ('kill-ring.ts', ('Emacs 式 kill/yank', 'Emacs kill / yank')),
                ('fuzzy.ts', ('模糊匹配打分', 'fuzzy scoring')),
                ('word-navigation.ts', ('按词移动', 'word motion'))]),
            (('文本与图形', 'Text & graphics'), 'ai', 'eye', [
                ('utils.ts', ('visibleWidth · 截断 · 换行', 'visibleWidth · truncate · wrap')),
                ('components/markdown.ts', ('Markdown → ANSI', 'Markdown → ANSI')),
                ('latex.ts', ('LaTeX → Unicode', 'LaTeX → Unicode')),
                ('terminal-image.ts', ('Kitty / iTerm2 图片', 'Kitty / iTerm2 images')),
                ('colors.ts', ('颜色转换', 'colour conversion')),
                ('terminal-colors.ts', ('前景/背景色探测', 'fg / bg detection'))])]
    W, X0 = 264, 16
    for ci, (title, lay, ic, rows) in enumerate(COLS):
        x = X0 + ci * (W + 10)
        f.group(x, 52, W, 384, lay, title, None, ic, title_mono=False, gid=f'g{ci}')
        for ri, (p, role) in enumerate(rows):
            n = loc(p)
            f.node(f'n{ci}{ri}', x + 12, 98 + ri * 54, W - 24, 46, lay, p.replace('components/', ''), role, None, tsize=11.5, ssize=10, tag=f'{n:,}')
    comps = components()
    f.group(16, 452, 1088, 104, 'tui', ('components/：开箱即用的组件', 'components/: ready-made components'), (f'{len(comps)} 个文件', f'{len(comps)} files'), 'layers', title_mono=False, gid='cmp')
    x, y = 32, 498
    for c in comps:
        s = f'{c} {loc("components/" + c + ".ts"):,}'
        w = maxw(s, 9.5, 550, True) + 14
        if x + w > 1092: x, y = 32, y + 26
        f.chip(x, y, s, 'tui', size=9.5, h=20)
        x += w + 6
    f.legend(24, 582, [('layer:infra', ('终端', 'terminal')), ('layer:tui', ('渲染', 'render')), ('layer:coding', ('编辑', 'editing')), ('layer:ai', ('文本 · 图形', 'text · graphics'))])
    f.note(1096, 582, ('标签 = 行数', 'tag = lines of code'), 10.5, anchor='end')
    return f

# ============================================================== tui_component
@reg
def tui_component():
    f = Fig('tui_component', 1120, 596, ('组件模型：render(width) 返回字符串行', 'The component model: render(width) returns lines'))
    has('tui.ts', 'render(width: number): string[];', 'wantsKeyRelease?: boolean;', 'export const CURSOR_MARKER = "\\x1b_pi:c\\x07";', 'const SEGMENT_RESET = "\\x1b[0m\\x1b]8;;\\x07";')
    h1 = uml(f, 'cmp', 16, 52, 330, 'tui', 'Component', '«interface»', [
        ['+render(width): string[]', '+handleInput?(data): void', '+handleMouse?(event)', '+wantsKeyRelease?: boolean', '+invalidate(): void']])
    h2 = uml(f, 'foc', 16, 52 + h1 + 24, 330, 'tui', 'Focusable', '«interface»', [['+focused: boolean']])
    y3 = 52 + h1 + 24 + h2 + 24
    h3 = uml(f, 'con', 16, y3, 330, 'tui', 'Container', '«class»', [['+children: Component[]', '+addChild() · removeChild() · clear()', '+render(w) = children 各行依次拼接' if False else '+render(w): concat(child.render(w))']])
    y4 = y3 + h3 + 24
    tm = iface('TUI')
    h4 = uml(f, 'tui', 16, y4, 330, 'tui', 'TUI extends Component', '«interface»', [['+mode: "regular" | "fullscreen"', '+setFocus(c) · showOverlay(c, opts)', '+requestRender(force?) · renderNow()', f'+… {len(tm)} members in total']])
    # example tree
    f.group(372, 52, 340, 336, 'coding', ('例：交互模式的组件树', 'e.g. the interactive-mode tree'), None, 'tree', title_mono=False, gid='tree')
    f.node('root', 392, 98, 300, 42, 'tui', 'TuiAltScreen', ('根 = Container', 'root = Container'), None, tsize=11.5, ssize=10, strong=True)
    kids = [('header', 'Text', ('标题与提示', 'title & hints')), ('chat', 'ScrollView', ('消息列表（Markdown…）', 'messages (Markdown…)')),
            ('wid', 'Container', ('扩展 widgets', 'extension widgets')), ('ed', 'Editor', ('focused = true', 'focused = true')), ('foot', 'Text', ('页脚：模型 · token', 'footer: model · tokens'))]
    for i, (k, t, s) in enumerate(kids):
        yy = 158 + i * 44
        f.node(k, 432, yy, 260, 36, 'coding' if k == 'ed' else 'tui', t, s, None, tsize=11, ssize=9.5, strong=(k == 'ed'))
        f.edge([(410, 140), (410, yy + 18), (432, yy + 18)], 'root', k, 'dep', r=6)
    f.text(392, 382, ('render(width) 自上而下，各子组件的行拼在一起', 'render(width) top-down; child lines are concatenated'), 9.8, 450, cls='faint', layer='label')
    # contract
    f.group(736, 52, 368, 336, 'err', ('每一帧的约定', 'The contract for every frame'), None, 'shield', title_mono=False, gid='rules')
    R = [(('每行可见宽度 ≤ width', 'Every line\'s visible width ≤ width'), ('否则抛错，并写 pi-tui-crash.log', 'otherwise it throws and writes pi-tui-crash.log')),
         (('focused 组件在光标处输出 CURSOR_MARKER', 'The focused component emits CURSOR_MARKER'), ('`"\\x1b_pi:c\\x07"：零宽 APC 序列', '`"\\x1b_pi:c\\x07": a zero-width APC sequence')),
         (('TUI 找到标记并删掉，再移动硬件光标', 'TUI finds and strips it, then moves the hardware cursor'), ('输入法候选框因此跟着光标走', 'so IME candidate windows follow the cursor')),
         (('每行末尾追加 SEGMENT_RESET', 'Each line gets SEGMENT_RESET appended'), ('`\\x1b[0m\\x1b]8;;\\x07：样式和超链接不会串行', '`\\x1b[0m\\x1b]8;;\\x07: no style or link bleeds to the next line')),
         (('invalidate()：主题变化时清缓存', 'invalidate(): drop caches on theme change'), ('下一次 render 从头计算', 'the next render starts from scratch'))]
    for i, (a, b) in enumerate(R):
        yy = 104 + i * 56
        f.step(i + 1, 760, yy - 4, 'err', r=8)
        f.text(776, yy, a, 10.8, 620, cls='strongt', layer='label')
        mono = isinstance(b, tuple) and b[0].startswith('`')
        bb = (b[0].lstrip('`'), b[1].lstrip('`')) if mono else b
        f.text(776, yy + 18, bb, 9.8, 450, False, cls='muted', layer='label')
    # catalogue
    comps = components()
    CAT = [(('布局', 'layout'), ['box', 'stack', 'h-stack', 'v-stack', 'spacer', 'scroll-view', 'mouse-region'], 'tui'),
           (('内容', 'content'), ['text', 'truncated-text', 'markdown', 'image'], 'ai'),
           (('输入', 'input'), ['input', 'editor', 'select-list', 'settings-list'], 'coding'),
           (('反馈', 'feedback'), ['loader', 'cancellable-loader', 'alt-screen-flash'], 'agent')]
    assert sorted(sum((c[1] for c in CAT), [])) == comps, set(comps) ^ set(sum((c[1] for c in CAT), []))
    f.group(372, 408, 732, 148, 'tui', ('内置组件', 'Built-in components'), (f'{len(comps)} 个，按用途', f'{len(comps)}, by purpose'), 'layers', title_mono=False, gid='cat')
    for i, (g, items, lay) in enumerate(CAT):
        yy = 452 + i * 25
        f.text(392, yy + 14, g, 10, 700, cls='faint', layer='label')
        x = 470
        for it in items:
            x += f.chip(x, yy, it, lay, size=9.5, h=20) + 6
    f.legend(24, 578, [('layer:tui', ('接口 / 组件', 'interfaces / components')), ('layer:coding', ('获得焦点', 'focused')), ('layer:err', ('约定', 'contract'))])
    return f

# ============================================================== tui_render : scheduling + main-screen diff
@reg
def tui_render():
    has('tui.ts', 'MIN_RENDER_INTERVAL_MS = 16', 'process.nextTick(() => this.scheduleRender())', 'this.requestImmediateRender();')
    has('tui-main-screen.ts', 'isTermuxSession', '\\x1b[?2026h', 'firstChanged < prevViewportTop', 'expandChangedRangeForKittyImages')
    f = Fig('tui_render', 1120, 760, ('差分渲染：一次 requestRender() 之后发生了什么', 'Differential rendering: what follows requestRender()'))
    E = f.edge
    # scheduling
    f.group(16, 52, 1088, 150, 'tui', ('调度', 'Scheduling'), ('合并请求 · 每帧至少间隔 16ms', 'coalesced · at least 16 ms between frames'), 'clock', title_mono=False, gid='sch')
    f.node('rr', 32, 98, 200, 44, 'tui', 'requestRender()', ('已请求就直接返回', 'no-op if already pending'), None, tsize=11.5, ssize=9.5)
    f.node('nt', 262, 98, 170, 44, 'tui', 'nextTick', ('同一 tick 内合并', 'coalesce this tick'), None, tsize=11.5, ssize=9.5)
    f.node('sr', 462, 98, 250, 44, 'tui', 'scheduleRender()', ('setTimeout(16ms − 距上一帧)', 'setTimeout(16 ms − since last)'), None, tsize=11.5, ssize=9.5)
    f.node('dr', 900, 98, 188, 86, 'tui', 'doRender()', ('子类实现：', 'per subclass:'), 'play', strong=True, sub2='main / alt screen', ssize=10)
    f.node('hi', 32, 150, 200, 40, 'coding', 'handleInput(data)', None, None, tsize=11)
    f.node('im', 262, 150, 450, 40, 'coding', 'requestImmediateRender()', ('nextTick 直接渲染，取消等待中的定时器', 'render on nextTick, cancel any pending timer'), None, tsize=11, ssize=9.5)
    E([(232, 120), (262, 120)], 'rr', 'nt', 'main', 'tui')
    E([(432, 120), (462, 120)], 'nt', 'sr', 'main', 'tui')
    E([(712, 120), (900, 120)], 'sr', 'dr', 'main', 'tui', label=('定时器到期', 'timer fires'), lpos=(806, 110))
    E([(232, 170), (262, 170)], 'hi', 'im', 'main', 'coding')
    E([(712, 170), (900, 170)], 'im', 'dr', 'main', 'coding', label=('按键延迟敏感', 'keys are latency-sensitive'), lpos=(806, 160))
    # prep
    f.group(16, 222, 1088, 104, 'ai', ('准备一帧（两种屏幕共用）', 'Preparing a frame (both screens)'), None, 'layers', title_mono=False, gid='prep')
    P = [('render(width)', ('组件树 → 行', 'tree → lines')), ('compositeOverlays', ('覆盖层拼进行内', 'splice overlays in')),
         ('extractCursorPosition', ('找到并删掉标记', 'find & strip marker')), ('applyLineResets', ('行尾 SEGMENT_RESET', 'SEGMENT_RESET per line')),
         (('宽度检查', 'width check'), ('超宽 → 抛错', 'too wide → throw'))]
    x = 32
    for i, (t, s) in enumerate(P):
        w = 196
        f.node(f'p{i}', x, 266, w, 44, 'ai', t, s, None, tsize=11, ssize=9.5, mono=not isinstance(t, tuple))
        if i: E([(x - 18, 288), (x, 288)], f'p{i-1}', f'p{i}', 'main', 'ai')
        x += w + 18
    # decision chain
    f.group(16, 346, 1088, 318, 'infra', 'TuiMainScreen.doRender()', ('regular 模式：在终端滚动区里原地更新', 'regular mode: update in place in the scrollback'), 'diff', gid='dec')
    D = [(('首帧？', 'first frame?'), '`previousLines = []', ('全量输出', 'full render'), '`fullRender(false)'),
         (('宽度变了？', 'width changed?'), '`previousWidth', ('清屏重绘', 'clear + redraw'), '`fullRender(true)'),
         (('高度变了？', 'height changed?'), ('Termux 除外', 'not on Termux'), ('清屏重绘', 'clear + redraw'), '`fullRender(true)'),
         (('内容变短？', 'shrank?'), '`clearOnShrink', ('清屏重绘', 'clear + redraw'), '`fullRender(true)'),
         (('没有变化？', 'nothing changed?'), ('逐行比较', 'compare lines'), ('只移光标', 'move cursor only'), None),
         (('只删了行？', 'only deletions?'), '`first ≥ new.length', ('清掉尾部行', 'clear tail lines'), None),
         (('在视口上方？', 'above viewport?'), '`first < viewportTop', ('清屏重绘', 'clear + redraw'), '`fullRender(true)')]
    W, G = 246, 24
    pos = []
    for i, (q, qs, o, os_) in enumerate(D):
        col, row = i % 4, i // 4
        x = 32 + col * (W + G); y = 392 + row * 144
        pos.append((x, y))
        f.node(f'd{i}', x, y, W, 48, 'infra', q, qs, None, mono=False, kind='dec', tsize=11.5, ssize=9.5)
        f.node(f'o{i}', x + 30, y + 70, W - 30, 40, 'err' if os_ else 'tui', o, os_, None, mono=False, tsize=10.5, ssize=9)
        E([(x + 16, y + 48), (x + 16, y + 90), (x + 30, y + 90)], f'd{i}', f'o{i}', 'err' if os_ else 'dep', r=6)
        if i and col: E([(x - G, y + 24), (x, y + 24)], f'd{i-1}', f'd{i}', 'main', 'infra')
    x0, y0 = pos[3]
    E([(x0 + W, 416), (1096, 416), (1096, 516), (32 + W / 2, 516), (32 + W / 2, 536)], 'd3', 'd4', 'main', 'infra')
    x = 32 + 3 * (W + G)
    f.node('part', x, 536, W, 110, 'coding', ('否则：局部重写', 'else: partial write'), ('firstChanged … lastChanged', 'firstChanged … lastChanged'), 'diff', mono=False, strong=True, sub2='`\\x1b[?2026h … ?2026l', ssize=9.5)
    E([(x - G, 560), (x, 560)], 'd6', 'part', 'main', 'coding')
    f.text(32, 690, ('比较前把变化区间扩大到覆盖整张 Kitty 图片；所有输出都包在同步输出 ?2026h … ?2026l 里，避免闪烁。', 'The changed range is widened to cover whole Kitty images; every write is wrapped in synchronized output ?2026h … ?2026l to avoid flicker.'), 10, 450, cls='muted', layer='label')
    f.text(32, 712, ('fullRender(true) = 清屏 + 清滚动区（\\x1b[2J\\x1b[H\\x1b[3J）后输出全部行；TUI.fullRedraws 计数。', 'fullRender(true) = clear screen and scrollback (\\x1b[2J\\x1b[H\\x1b[3J), then write every line; counted in TUI.fullRedraws.'), 10, 450, cls='muted', layer='label')
    f.legend(24, 742, [('main', ('否 → 下一个判断', 'no → next check')), ('err', ('是 → 全量重绘', 'yes → full redraw')), ('dep', ('是 → 轻量处理', 'yes → light path'))])
    return f

# ============================================================== tui_screens : main vs alt screen
@reg
def tui_screens():
    has('tui-alt-screen.ts', 'const ENTER_ALT_SCREEN = "\\x1b[?1049h";', 'compositeScrollToEndIndicator', 'compositeFlashes', 'applySearchHighlights', 'applySelection', 'OSC 52')
    has('../../coding-agent/src/core/settings-manager.ts', 'return this.settings.tuiMode === "regular" ? "regular" : "fullscreen";')
    f = Fig('tui_screens', 1120, 640, ('两种屏幕：regular（主屏）与 fullscreen（备用屏）', 'Two screens: regular (main) and fullscreen (alternate)'))
    E = f.edge
    f.group(16, 52, 400, 538, 'infra', 'TuiMainScreen', ('mode = "regular"', 'mode = "regular"'), 'terminal', gid='main')
    MP = [(('内容写进终端自己的滚动区', 'Content goes into the terminal\'s own scrollback'), ('往上翻就是历史，退出后仍在', 'scroll up for history; it stays after exit')),
          (('按行差分（见上一张图）', 'Line diff (see the previous figure)'), ('只重写 firstChanged…lastChanged', 'rewrites only firstChanged…lastChanged')),
          (('不抓鼠标', 'No mouse capture'), ('终端原生选择与复制照常', 'native selection and copy still work')),
          (('视口之上的变化只能清屏重绘', 'Changes above the viewport force a full redraw'), ('rows/cols 变化同理', 'so do rows / cols changes')),
          (('Kitty 图片按行预留', 'Kitty images reserve rows'), ('变化区间会扩到整张图', 'diff ranges widen to whole images'))]
    for i, (a, b) in enumerate(MP):
        yy = 112 + i * 62
        f.step(i + 1, 40, yy - 4, 'infra', r=8)
        f.text(56, yy, a, 10.8, 620, cls='strongt', layer='label')
        f.text(56, yy + 18, b, 9.8, 450, cls='muted', layer='label')
    codebox(f, 32, 430, 368, [(0, '# pi-coding-agent: settings.json', 'faint'), (0, '"tuiMode": "regular" | "fullscreen"', 'strongt'), (0, ('# 默认 fullscreen（getTuiMode）', '# default: fullscreen (getTuiMode)'), 'faint')], ('选择', 'CHOOSING'), 10, 18)
    # alt
    f.group(436, 52, 668, 538, 'tui', 'TuiAltScreen', ('mode = "fullscreen" · 进入 \\x1b[?1049h', 'mode = "fullscreen" · enters \\x1b[?1049h'), 'monitor', gid='alt')
    ST = [('renderLayoutFrame(root)', ('布局帧：盒子 · 滚动视图', 'layout frame: boxes · scroll views')),
          ('applySearchHighlights', ('搜索命中高亮', 'search hits')),
          ('compositeScrollToEndIndicator', ('"回到底部"提示', '"jump to end" pill')),
          ('compositeOverlays', ('覆盖层', 'overlays')),
          ('applySelection', ('鼠标选区', 'mouse selection')),
          ('compositeFlashes', ('短暂提示', 'transient flashes')),
          ('extractCursorPosition · applyLineResets', ('光标 · 行尾重置 · 裁到 width', 'cursor · resets · clip to width')),
          (('与 previousScreen 逐行比较', 'diff rows against previousScreen'), ('尺寸变化 → 整屏重绘', 'size change → full redraw'))]
    for i, (t, s) in enumerate(ST):
        yy = 100 + i * 52
        f.node(f's{i}', 456, yy, 340, 42, 'tui' if i < 7 else 'coding', t, s, None, tsize=10.5, ssize=9.5, mono=not isinstance(t, tuple), strong=(i == 7))
        if i: E([(626, yy - 10), (626, yy)], f's{i-1}', f's{i}', 'main', 'tui')
    f.node('w', 456, 532, 340, 42, 'coding', '\\x1b[row;1H\\x1b[2K …', ('只写变化的行 · 包在 ?2026 中', 'changed rows only · inside ?2026'), None, tsize=10.5, ssize=9.5)
    E([(626, 506), (626, 532)], 's7', 'w', 'main', 'coding')
    FE = [(('鼠标', 'mouse'), '?1000 ?1002 ?1003 ?1004 ?1006'), (('滚轮', 'wheel'), ('加速，最多 6 行/次', 'accelerated, ≤ 6 lines')),
          (('选择复制', 'select & copy'), 'OSC 52'), (('搜索', 'search'), 'alt-screen-search.ts'), (('布局', 'layout'), 'HStack · VStack · ScrollView'), (('退出', 'exit'), '\\x1b[?1049l')]
    for i, (k, v) in enumerate(FE):
        yy = 112 + i * 60
        f.text(820, yy, k, 10, 700, cls='faint', layer='label', ls='.03em')
        f.text(820, yy + 18, v, 10, 500, isinstance(v, str), cls='strongt', layer='label')
    f.legend(24, 620, [('layer:infra', 'regular'), ('layer:tui', 'fullscreen'), ('layer:coding', ('输出', 'output'))])
    return f

def default_keys(i):
    m = re.search(r'"' + re.escape(i) + r'":\s*\{\s*defaultKeys:\s*(\[[^\]]*\]|"[^"]*")', _src('keybindings.ts'))
    return re.findall(r'"([^"]+)"', m.group(1))

# ============================================================== tui_input
@reg
def tui_input():
    has('terminal.ts', 'const DESIRED_KITTY_KEYBOARD_PROTOCOL_FLAGS = 7;', 'process.stdout.write("\\x1b[?2004h");', 'process.stdout.write("\\x1b[>4;2m");', 'const DEFAULT_SSH_ESCAPE_TIMEOUT_MS = 100;', 'PI_TUI_ESC_TIMEOUT')
    has('stdin-buffer.ts', 'const DEFAULT_SEQUENCE_TIMEOUT_MS = 50;', 'const DEFAULT_ESCAPE_TIMEOUT_MS = 10;')
    f = Fig('tui_input', 1120, 640, ('输入：从 stdin 字节到 focused.handleInput()', 'Input: from stdin bytes to focused.handleInput()'))
    E = f.edge
    f.node('in', 16, 56, 300, 40, 'infra', 'process.stdin', ('原始字节', 'raw bytes'), 'keyboard', kind='term', ssize=10)
    f.node('pt', 16, 126, 300, 64, 'infra', 'ProcessTerminal', ('setRawMode · ?2004h 括号粘贴', 'setRawMode · ?2004h bracketed paste'), 'terminal', sub2=('Kitty 键盘协议 flags = 7', 'Kitty keyboard protocol, flags = 7'), ssize=10)
    f.node('sb', 16, 220, 300, 64, 'infra', 'StdinBuffer', ('拆成完整转义序列 · 粘贴整段保留', 'split into whole sequences · paste kept whole'), 'queue', sub2=('ESC 10ms（SSH 100ms）· 序列 50ms', 'ESC 10 ms (SSH 100 ms) · sequence 50 ms'), ssize=10)
    E([(166, 96), (166, 126)], 'in', 'pt', 'main', 'infra')
    E([(166, 190), (166, 220)], 'pt', 'sb', 'main', 'infra')
    codebox(f, 16, 306, 300, [(0, '\\x1b[A            up', 'muted'), (0, '\\x1b[13;2u        shift+enter', 'muted'), (0, '\\x1b[99;5:3u      ctrl+c release', 'muted'),
                              (0, '\\x1b[200~ … \\x1b[201~  paste', 'muted'), (0, '\\x1b]11;rgb:…      bg colour reply', 'muted')], ('序列举例', 'SAMPLE SEQUENCES'), 9.5, 18)
    f.text(16, 470, ('Kitty 查询 \\x1b[>7u\\x1b[?u 无回应时，', 'If the Kitty query \\x1b[>7u\\x1b[?u gets no reply'), 10, 450, cls='muted', layer='label')
    f.text(16, 488, ('在 DA 回复后改用 modifyOtherKeys \\x1b[>4;2m', 'before DA, fall back to modifyOtherKeys \\x1b[>4;2m'), 10, 450, cls='muted', layer='label')
    # chain
    f.group(340, 52, 400, 548, 'tui', 'TuiBase.handleTerminalInput(data)', ('依次尝试，可被消费', 'in order; may be consumed'), 'filter', gid='chain')
    C = [(('终端颜色回复', 'terminal colour reply'), 'OSC 10 / 11 / 4'), (('配色方案通知', 'colour-scheme report'), ('深/浅色切换', 'dark / light switch')),
         ('addInputListener()', ('consume 或改写 data', 'consume or rewrite data')), (('单元格尺寸回复', 'cell-size reply'), ('图片用', 'for images')),
         ('shift+ctrl+d', ('调试回调 onDebug', 'onDebug hook')), (('覆盖层焦点修复', 'overlay focus repair'), ('visible() 变化后', 'after visible() changes')),
         (('过滤按键释放', 'drop key releases'), ('除非 wantsKeyRelease', 'unless wantsKeyRelease')), ('focused.handleInput(data)', ('然后立即渲染', 'then render immediately'))]
    for i, (t, s) in enumerate(C):
        yy = 98 + i * 62
        last = i == len(C) - 1
        f.node(f'c{i}', 360, yy, 360, 48, 'coding' if last else 'tui', t, s, None, mono=not isinstance(t, tuple), tsize=11, ssize=9.5, strong=last)
        f.step(i + 1, 362, yy + 2, 'coding' if last else 'tui', r=8, onnode=True)
        if i: E([(540, yy - 14), (540, yy)], f'c{i-1}', f'c{i}', 'main', 'tui')
    E([(316, 252), (328, 252), (328, 122), (360, 122)], 'sb', 'c0', 'main', 'infra', r=6)
    # keys
    f.group(764, 52, 340, 236, 'coding', 'keys.ts', ('把序列认成按键名', 'turn sequences into key names'), 'keyboard', gid='keys')
    K = [('matchesKey(data, "ctrl+c")', ('Kitty CSI-u · 旧式 · modifyOtherKeys', 'Kitty CSI-u · legacy · modifyOtherKeys')),
         ('parseKey(data)', ('→ "shift+enter" 等', '→ "shift+enter" etc.')),
         ('isKeyRelease(data)', ('Kitty 事件类型 3', 'Kitty event type 3')),
         ('decodeKittyPrintable(data)', ('CSI-u → 可打印字符', 'CSI-u → printable text'))]
    for i, (a, b) in enumerate(K):
        yy = 112 + i * 44
        f.text(784, yy, a, 10.5, 600, True, cls='strongt', layer='label')
        f.text(784, yy + 17, b, 9.6, 450, cls='muted', layer='label')
    ids = kb_ids()
    tot = sum(len(v) for v in ids.values())
    f.group(764, 308, 340, 292, 'coding', 'KeybindingsManager', (f'{tot} 个 tui.* 按键 id', f'{tot} tui.* key ids'), 'key', gid='kb')
    y = 352
    for ns in ('input', 'select', 'editor', 'altScreen'):
        f.text(784, y + 14, f'tui.{ns}.*', 10, 650, True, cls='faint', layer='label')
        f.text(1088, y + 14, str(len(ids.get(ns, []))), 10, 650, True, cls='faint', layer='label', anchor='end')
        y += 24
    for k in ('tui.input.submit', 'tui.input.newLine', 'tui.input.copy', 'tui.editor.undo', 'tui.editor.yank'):
        dk = ' / '.join(default_keys(k))
        f.text(784, y + 14, k.split('.', 1)[1], 9.8, 500, True, cls='strongt', layer='label')
        f.text(1088, y + 14, dk, 9.8, 500, True, cls='muted', layer='label', anchor='end')
        y += 21
    f.text(784, y + 22, ('用户覆盖：~/.pi/agent/keybindings.json', 'Overrides: ~/.pi/agent/keybindings.json'), 9.6, 450, cls='faint', layer='label')
    f.legend(24, 622, [('layer:infra', ('终端层', 'terminal layer')), ('layer:tui', ('TUI 分发', 'TUI dispatch')), ('layer:coding', ('组件 · 按键', 'component · keys'))])
    return f

# ============================================================== tui_editor
@reg
def tui_editor():
    has('components/editor.ts', 'pastedLines.length > 10 || totalChars > 1000', 'this.history.length > 100', 'const ATTACHMENT_AUTOCOMPLETE_DEBOUNCE_MS = 20;', 'this.jumpMode !== null')
    has('autocomplete.ts', 'export class CombinedAutocompleteProvider implements AutocompleteProvider', 'spawn(fdPath, args')
    f = Fig('tui_editor', 1120, 650, ('Editor 与自动补全', 'The Editor and autocomplete'))
    E = f.edge
    h = uml(f, 'ed', 16, 52, 340, 'coding', 'Editor', '«class» implements Component, Focusable', [
        ['-state: { lines[], cursorLine, cursorCol }', '-undoStack: UndoStack<EditorState>', '-killRing: KillRing', '-history: string[]  (≤ 100)', '-pastes: Map<id, text>'],
        ['+onSubmit?(text) · onChange?(text)', '+getText() · setText() · insertTextAtCursor()', '+setAutocompleteProvider(p)', '+addToHistory(text)']], lh=17)
    y = 52 + h + 20
    f.group(16, y, 340, 600 - y, 'coding', ('细节', 'Details'), None, 'spark', title_mono=False, gid='det')
    D = [(('大段粘贴折叠成标记', 'Large pastes collapse to a marker'), '[paste #1 +42 lines]'), (('阈值', 'threshold'), ('> 10 行或 > 1000 字符', '> 10 lines or > 1000 chars')),
         (('提交时', 'on submit'), ('标记换回原文', 'markers expand back')), (('行尾 \\ + Enter', 'trailing \\ + Enter'), ('插入换行而不是提交', 'inserts a newline instead')),
         (('撤销', 'undo'), ('UndoStack 保存状态快照', 'UndoStack keeps state snapshots')), (('历史', 'history'), ('最多 100 条', 'up to 100 entries')),
         (('kill ring', 'kill ring'), ('按行/按词删除的文本，连续删除合并', 'line / word kills; consecutive ones merge'))]
    for i, (a, b) in enumerate(D):
        yy = y + 62 + i * 30
        f.text(36, yy, a, 9.8, 600, cls='strongt', layer='label')
        f.text(340, yy, b, 9.8, 450, isinstance(b, str), cls='muted', layer='label', anchor='end')
    # handleInput order
    O = [(('跳转模式', 'jump mode'), 'jumpForward'), (('括号粘贴', 'bracketed paste'), '\\x1b[200~'), (('交给上层', 'to parent'), 'ctrl+c'), (('撤销', 'undo'), 'ctrl+-'),
         (('补全菜单', 'completion menu'), 'up · down · tab · enter'), (('Tab 触发', 'Tab trigger'), 'force: true'), (('删除', 'delete'), ('字符 · 单词 · 到行首尾', 'char · word · line')),
         (('kill ring', 'kill ring'), 'ctrl+y · alt+y'), (('历史', 'history'), 'up · down'), (('光标移动', 'cursor'), ('行首尾 · 按词', 'line · word')),
         (('换行', 'new line'), 'shift+enter'), (('提交', 'submit'), 'enter → onSubmit'), (('其余：插入字符', 'else: insert text'), 'decodeKittyPrintable')]
    f.group(376, 52, 728, 248, 'tui', 'Editor.handleInput(data)', ('自上而下尝试，命中即返回', 'tried top to bottom; first match returns'), 'filter', gid='hi')
    W, H = 168, 44
    for i, (t, s) in enumerate(O):
        col, row = i % 4, i // 4
        x = 392 + col * (W + 12); yy = 98 + row * 50
        if i == 12: x, W2 = 392 + 1 * (W + 12) - (W + 12), W
        f.node(f'h{i}', x if i < 12 else 392, yy if i < 12 else 98 + 3 * 50, W if i < 12 else 3 * W + 2 * 12 + 0, 42, 'coding' if i == 11 else 'tui', t, s, None, mono=False, tsize=10.5, ssize=9, strong=(i == 11))
        f.step(i + 1, (x if i < 12 else 392) + 2, (yy if i < 12 else 248) + 2, 'coding' if i == 11 else 'tui', r=8, onnode=True)
    # autocomplete
    f.group(376, 320, 728, 280, 'ai', ('自动补全', 'Autocomplete'), 'CombinedAutocompleteProvider', 'spark', title_mono=False, gid='ac')
    TR = [('/', ('行首的斜杠命令', 'slash command at line start'), ('fuzzyFilter(commands)', 'fuzzyFilter(commands)')),
          ('@', ('文件附件', 'file attachment'), ('fd 搜索 · 防抖 20ms', 'fd search · 20 ms debounce')),
          ('Tab', ('路径补全', 'path completion'), ('force: true · 读目录', 'force: true · readdir'))]
    for i, (k, a, b) in enumerate(TR):
        yy = 368 + i * 56
        f.node(f't{i}', 396, yy, 56, 44, 'ai', k, None, None, align='center', tsize=14, strong=True)
        f.node(f'a{i}', 476, yy, 250, 44, 'ai', a, b, None, mono=False, tsize=11, ssize=9.5)
        E([(452, yy + 22), (476, yy + 22)], f't{i}', f'a{i}', 'main', 'ai')
    f.node('sl', 768, 368, 316, 64, 'tui', 'SelectList', ('弹出在编辑器上方 · ↑↓ 选择', 'pops above the editor · ↑↓ to pick'), 'filter', ssize=10)
    f.node('ap', 768, 480, 316, 64, 'ai', 'applyCompletion(…)', ('→ { lines, cursorLine, cursorCol }', '→ { lines, cursorLine, cursorCol }'), 'check', ssize=10)
    for i in range(3):
        yy = 368 + i * 56 + 22
        E([(726, yy), (746, yy), (746, 400), (768, 400)] if i else [(726, yy), (746, yy), (746, 400), (768, 400)], f'a{i}', 'sl', 'dep', r=6) if i == 0 else None
    E([(746, 502), (746, 400)], None, None, 'dep', arrow=False)
    for i in (1, 2):
        yy = 368 + i * 56 + 22
        E([(726, yy), (746, yy)], f'a{i}', None, 'dep', arrow=False)
    E([(926, 432), (926, 480)], 'sl', 'ap', 'main', 'ai', label=('确认', 'confirm'), lpos=(960, 456))
    f.text(396, 580, ('提供者接口：triggerCharacters? · getSuggestions(lines, line, col, { signal, force }) · applyCompletion(…)', 'Provider interface: triggerCharacters? · getSuggestions(lines, line, col, { signal, force }) · applyCompletion(…)'), 9.6, 450, cls='faint', layer='label')
    f.legend(24, 630, [('layer:coding', ('编辑器状态 / 提交', 'editor state / submit')), ('layer:tui', ('按键分支', 'key branches')), ('layer:ai', ('补全', 'completion'))])
    return f

# ============================================================== tui_overlay
@reg
def tui_overlay():
    has('tui.ts', 'Math.min(80, availWidth)', 'preFocus: this.focusedComponent', 'nonCapturing?: boolean;', 'compositeLineAt(')
    anchors = re.findall(r'\| "([a-z-]+)"', re.search(r'export type OverlayAnchor =(.*?);', _src('tui.ts'), re.S).group(1))
    hm = iface('OverlayHandle')
    f = Fig('tui_overlay', 1120, 620, ('覆盖层：showOverlay(component, options)', 'Overlays: showOverlay(component, options)'))
    E = f.edge
    h = uml(f, 'oo', 16, 52, 330, 'ext', 'OverlayOptions', '«interface»', [
        ['+width?: number | "50%"', '+minWidth?: number', '+maxHeight?: number | "%"'],
        [f'+anchor?: {len(anchors)} values', '+offsetX? · offsetY?', '+row? · col?: number | "%"', '+margin?: number | { top … }'],
        ['+visible?(w, h): boolean', '+nonCapturing?: boolean']])
    h2 = uml(f, 'oh', 16, 52 + h + 20, 330, 'ext', 'OverlayHandle', '«returned»', [[f'+{m}()' for m in hm[:4]], [f'+{m}()' for m in hm[4:]]])
    # anchor grid
    f.group(370, 52, 360, 330, 'tui', ('9 个锚点', '9 anchors'), ('终端可用区域（去掉 margin）', 'terminal area minus margin'), 'layers', title_mono=False, gid='grid')
    gx, gy, gw, gh = 400, 104, 300, 222
    f.raw(f'<rect class="codebg" x="{gx}" y="{gy}" width="{gw}" height="{gh}" rx="8"/>', 'grp')
    f.raw(f'<rect class="rule-d" fill="none" x="{gx + 14}" y="{gy + 14}" width="{gw - 28}" height="{gh - 28}" rx="4"/>', 'grp')
    pos = {'top-left': (0, 0), 'top-center': (1, 0), 'top-right': (2, 0), 'left-center': (0, 1), 'center': (1, 1), 'right-center': (2, 1), 'bottom-left': (0, 2), 'bottom-center': (1, 2), 'bottom-right': (2, 2)}
    assert sorted(pos) == sorted(anchors)
    for a, (cx, cy) in pos.items():
        x = gx + 14 + cx * (gw - 28) / 2; y = gy + 14 + cy * (gh - 28) / 2
        dot(f, x, y, 'ext' if a == 'center' else 'tui', 4.5 if a == 'center' else 3.4)
        anc = 'start' if cx == 0 else ('end' if cx == 2 else 'middle')
        dx = 8 if cx == 0 else (-8 if cx == 2 else 0)
        dy = 16 if cy == 0 else (-8 if cy == 2 else 18)
        f.text(x + dx, y + dy, a, 9.5, 600 if a == 'center' else 500, True, anchor=anc, cls='strongt' if a == 'center' else 'muted', layer='label')
    f.text(550, 362, ('默认：center · 宽 min(80, 可用宽度)', 'default: center · width min(80, available)'), 10, 450, anchor='middle', cls='faint', layer='label')
    # pipeline
    f.group(754, 52, 350, 330, 'ai', ('每一帧', 'Every frame'), 'compositeOverlays()', 'stack', title_mono=False, gid='pipe')
    P = [(('筛选可见的', 'filter visible'), ('visible(w, h) · 未隐藏', 'visible(w, h) · not hidden')), (('解析宽度', 'resolve width'), ('% / minWidth / margin', '% / minWidth / margin')),
         ('component.render(width)', ('截到 maxHeight', 'cut to maxHeight')), (('解析 row / col', 'resolve row / col'), ('用实际高度算锚点', 'anchor with real height')),
         ('compositeLineAt(…)', ('按列拼进底层行', 'splice into base lines'))]
    for i, (t, s_) in enumerate(P):
        yy = 98 + i * 56
        f.node(f'p{i}', 774, yy, 310, 44, 'ai', t, s_, None, mono=not isinstance(t, tuple), tsize=11, ssize=9.5)
        f.step(i + 1, 776, yy + 2, 'ai', r=8, onnode=True)
        if i: E([(929, yy - 12), (929, yy)], f'p{i-1}', f'p{i}', 'main', 'ai')
    # focus
    f.group(370, 402, 734, 196, 'coding', ('焦点', 'Focus'), ('覆盖层是一个栈', 'overlays form a stack'), 'eye', title_mono=False, gid='focus')
    FN = [('show', 'showOverlay()', ('记住 preFocus，然后抢焦点', 'remember preFocus, take focus')),
          ('nc', 'nonCapturing: true', ('显示但不抢焦点', 'shown, focus untouched')),
          ('hide', 'hide()', ('焦点交给下一个可见覆盖层或 preFocus', 'focus to next visible overlay or preFocus'))]
    for i, (k, t, s_) in enumerate(FN):
        x = 390 + i * 236
        f.node(k, x, 448, 222, 56, 'coding', t, s_, None, tsize=11, ssize=9.5)
    f.text(390, 534, ('每次输入前都会复查：focused 覆盖层若已不可见（resize 或 visible() 变 false），焦点改到最上层可见覆盖层或 preFocus。', 'Before every input: if the focused overlay is no longer visible (resize, or visible() turned false), focus moves to the top visible overlay or preFocus.'), 9.8, 450, cls='muted', layer='label')
    f.text(390, 556, ('覆盖层按 focusOrder 排序叠放；focus() 把一个覆盖层提到最上层。', 'Overlays stack by focusOrder; focus() brings one to the top.'), 9.8, 450, cls='muted', layer='label')
    f.legend(24, 602, [('layer:ext', ('API', 'API')), ('layer:tui', ('定位', 'placement')), ('layer:ai', ('合成', 'compositing')), ('layer:coding', ('焦点', 'focus'))])
    return f

# ============================================================== tui_terminal
@reg
def tui_terminal():
    has('terminal.ts', 'const TERMINAL_PROGRESS_ACTIVE_SEQUENCE = "\\x1b]9;4;3\\x07";', 'process.stdout.write(`\\x1b]0;${title}\\x07`);', 'const DEVICE_ATTRIBUTES_QUERY = "\\x1b[c";', 'OSC 7501')
    has('terminal-image.ts', 'process.env.KITTY_WINDOW_ID', 'termProgram === "ghostty"', 'process.env.WEZTERM_PANE', 'termProgram === "warpterminal"', 'process.env.ITERM_SESSION_ID', 'process.env.TMUX', 'term.startsWith("screen")', 'process.env.WT_SESSION', 'termProgram === "alacritty" || termProgram === "vscode" || termProgram === "zed"', 'terminalEmulator === "jetbrains-jediterm"')
    tm = iface('Terminal', 'terminal.ts')
    f = Fig('tui_terminal', 1120, 656, ('终端能力：协商、输出序列与图片支持', 'Terminal capabilities: negotiation, output sequences, images'))
    E = f.edge
    f.group(16, 52, 520, 300, 'infra', 'ProcessTerminal.start()', (f'Terminal 接口 {len(tm)} 个成员', f'Terminal interface: {len(tm)} members'), 'terminal', gid='start')
    S = [('setRawMode(true)', ('逐字节读取，不回显', 'byte-wise input, no echo')),
         ('\\x1b[?2004h', ('开启括号粘贴', 'bracketed paste on')),
         ('\\x1b[>7u \\x1b[?u', ('请求 Kitty 键盘协议并查询', 'push Kitty flags 7 and query')),
         ('\\x1b[c', ('DA：用作"查询结束"哨兵', 'DA as the end-of-queries sentinel')),
         ('\\x1b[>4;2m', ('无 Kitty 回复时的 modifyOtherKeys', 'modifyOtherKeys when Kitty is silent'))]
    for i, (a, b) in enumerate(S):
        yy = 100 + i * 48
        f.node(f's{i}', 36, yy, 480, 40, 'infra', a, b, None, tsize=11, ssize=9.5)
        f.step(i + 1, 38, yy + 2, 'infra', r=8, onnode=True)
    f.text(36, 342, ('Windows：额外打开 VT 输入；stop() 恢复原 raw 状态并关掉以上模式。', 'Windows: also enables VT input; stop() restores raw state and undoes the modes.'), 9.8, 450, cls='faint', layer='label')
    # outputs
    f.group(556, 52, 548, 300, 'tui', ('输出与查询', 'Output & queries'), None, 'monitor', title_mono=False, gid='out')
    O = [('OSC 0', '\\x1b]0;title\\x07', ('窗口标题', 'window title')), ('OSC 9;4', '\\x1b]9;4;3 / 0', ('任务栏进度（不确定 / 清除）', 'taskbar progress (busy / clear)')),
         ('OSC 7501', 'idle · working · blocked …', ('程序状态（终端声明支持时）', 'program status (if supported)')),
         ('OSC 10/11', ('前景 / 背景色查询', 'fg / bg colour query'), ('自动判断深浅主题', 'picks dark or light')),
         ('OSC 8', ('超链接', 'hyperlinks'), ('只在确认支持时启用', 'only where known to work')),
         ('?2026', ('同步输出', 'synchronized output'), ('每帧包起来，防闪烁', 'wraps every frame'))]
    for i, (k, v, d) in enumerate(O):
        yy = 112 + i * 38
        f.chip(576, yy - 14, k, 'tui', size=9.5, h=20, cls='solid')
        f.text(666, yy, v, 10, 500, isinstance(v, str), cls='strongt', layer='label')
        f.text(1088, yy, d, 9.6, 450, cls='muted', layer='label', anchor='end')
    # image table
    f.group(16, 372, 1088, 248, 'ai', 'detectCapabilities()', ('按环境变量识别；PI_IMAGE_PROTOCOL · PI_TRUE_COLOR · PI_HYPERLINKS 可覆盖', 'from env vars; PI_IMAGE_PROTOCOL · PI_TRUE_COLOR · PI_HYPERLINKS override'), 'eye', gid='img')
    rows = [('kitty · ghostty · wezterm · warp', 'kitty', True, True), ('iTerm2', 'iterm2', True, True),
            ('Windows Terminal · alacritty · vscode · zed', None, True, True), ('JetBrains · Windows console', None, True, False),
            ('tmux', None, 'COLORTERM', ('探测', 'probed')), (('screen · 未知终端', 'screen · unknown'), None, 'COLORTERM', False)]
    hx = [36, 520, 720, 900]
    for x, t in zip(hx, [('终端', 'TERMINAL'), ('图片协议', 'IMAGES'), ('真彩色', 'TRUECOLOR'), ('超链接', 'HYPERLINKS')]):
        f.text(x, 432, t, 9.5, 700, cls='faint', layer='label', ls='.06em')
    hline(f, 36, 1084, 440)
    for i, (t, im, tc, hl) in enumerate(rows):
        yy = 464 + i * 26
        f.text(36, yy, t, 10, 550, isinstance(t, str), cls='strongt', layer='label')
        if im: f.chip(520, yy - 14, im, 'ai', size=9.5, h=19, cls='solid')
        else: f.text(520, yy, '—', 10, 500, cls='faint', layer='label')
        for x, v in ((720, tc), (900, hl)):
            f.text(x, yy, ('✓' if v is True else '—') if isinstance(v, bool) else v, 10, 550 if v is True else 450, cls='strongt' if v is True else 'muted', layer='label')
    f.legend(24, 640, [('layer:infra', ('启动协商', 'start-up negotiation')), ('layer:tui', ('输出序列', 'output sequences')), ('layer:ai', ('能力识别', 'capability detection'))])
    return f
