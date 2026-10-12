# pi-tui deep dive. Same section schema as deep_agent.py; files: (path, regex, symbol, zh, en)
from figs6 import components, total_loc, kb_ids
U = 'packages/tui/src/'
SLIDE_KEYS = ['tui_component', 'tui_render', 'tui_screens', 'tui_input', 'tui_editor', 'tui_overlay', 'tui_terminal', 'tui_arch']
_NC = len(components()); _LOC = total_loc(); _KB = sum(len(v) for v in kb_ids().values())

INTRO = dict(
 takeaway=("`pi-tui` 是一个独立的终端 UI 库：组件只需实现 `render(width): string[]`，TUI 把组件树渲染成行，再只把变化的部分写进终端。它自带两种屏幕（保留滚动历史的 regular 与备用屏 fullscreen）、Kitty 键盘协议、覆盖层、多行编辑器和自动补全。",
           "`pi-tui` is a standalone terminal UI library: a component only implements `render(width): string[]`; the TUI renders the tree to lines and writes only what changed. It ships two screens (regular, which keeps scrollback, and fullscreen on the alternate screen), the Kitty keyboard protocol, overlays, a multi-line editor and autocomplete."),
 role=(f"没有 pi 内部依赖，`pi-coding-agent` 的 interactive 模式建立在它之上。共 {_LOC:,} 行 TypeScript、{_NC} 个内置组件；package.json 没有 exports 字段，入口是 `dist/index.js`。", f"No internal pi dependencies; `pi-coding-agent`'s interactive mode is built on it. {_LOC:,} lines of TypeScript and {_NC} built-in components; package.json has no exports map, the entry is `dist/index.js`."),
)

SECTIONS = [
dict(id="tui-arch", group="arch", layer="tui", diagram="tui_arch",
 title=("模块结构", "Module structure"),
 takeaway=("四块：终端与输入（`terminal.ts`、`stdin-buffer.ts`、`keys.ts`）、渲染核心（`tui.ts` 与两种屏幕）、编辑（`editor.ts` 与自动补全）、文本与图形（宽度计算、Markdown、LaTeX、终端图片）。`components/` 下是可直接使用的组件。",
           "Four blocks: terminal & input (`terminal.ts`, `stdin-buffer.ts`, `keys.ts`), the render core (`tui.ts` and the two screens), editing (`editor.ts` and autocomplete), and text & graphics (width maths, Markdown, LaTeX, terminal images). `components/` holds ready-to-use components."),
 points=[
  ("最大的文件是 `components/editor.ts`：多行编辑、撤销、kill ring、历史、粘贴折叠与补全菜单都在这里。", "The largest file is `components/editor.ts`: multi-line editing, undo, the kill ring, history, paste folding and the completion menu all live there."),
  ("`utils.ts` 的 `visibleWidth()` / `truncateToWidth()` 处理 ANSI 序列与全角字符，是所有组件遵守宽度约定的基础。", "`utils.ts`'s `visibleWidth()` / `truncateToWidth()` handle ANSI sequences and wide characters; every component relies on them to respect the width contract."),
  ("`native-platform.ts` 加载可选的原生模块（剪贴板、修饰键状态）；没有时功能降级而不报错。", "`native-platform.ts` loads an optional native module (clipboard, modifier state); without it features degrade instead of failing."),
 ],
 how=[
  ("创建 `ProcessTerminal`，再用它创建 `TuiMainScreen` 或 `TuiAltScreen`。", "Create a `ProcessTerminal`, then a `TuiMainScreen` or `TuiAltScreen` on top of it."),
  ("`addChild()` 组件、`setFocus()` 输入组件，`start()`。", "`addChild()` components, `setFocus()` the input component, `start()`."),
  ("状态变化后调用 `requestRender()`；输入由 TUI 交给获得焦点的组件。", "Call `requestRender()` after state changes; the TUI routes input to the focused component."),
 ],
 files=[
  (U + "index.ts", r"tui\.ts", "export …", "包入口", "package entry"),
  (U + "tui.ts", r"^export abstract class TuiBase", "TuiBase", "两种屏幕的共同基类", "base of both screens"),
  (U + "terminal.ts", r"^export class ProcessTerminal", "ProcessTerminal", "真实终端", "the real terminal"),
  (U + "utils.ts", r"^export function visibleWidth", "visibleWidth()", "可见宽度", "visible width"),
  (U + "components/editor.ts", r"^export class Editor\b", "Editor", "最大的组件", "the largest component"),
 ]),

dict(id="tui-component", group="types", layer="tui", diagram="tui_component",
 title=("组件模型", "The component model"),
 takeaway=("`Component` 只有一个必需的渲染方法：`render(width)` 返回字符串数组，每个元素是一行。没有虚拟 DOM、没有布局树——`Container` 把子组件的行依次拼起来，TUI 再对这些行做差分。",
           "`Component` has one required render method: `render(width)` returns an array of strings, one per line. No virtual DOM, no layout tree — `Container` concatenates its children's lines, and the TUI diffs those lines."),
 points=[
  ("每一行的可见宽度不能超过 `width`；超过时 TUI 抛错并写 `pi-tui-crash.log`，而不是让终端自动换行弄乱画面。", "No line may be wider than `width`; if one is, the TUI throws and writes `pi-tui-crash.log` instead of letting the terminal wrap and corrupt the screen."),
  ("获得焦点的组件（`Focusable.focused = true`）在光标处输出零宽的 `CURSOR_MARKER`；TUI 找到它、删掉它，再把硬件光标移过去——输入法候选框因此出现在正确位置。", "The focused component (`Focusable.focused = true`) emits a zero-width `CURSOR_MARKER` at the cursor; the TUI finds it, strips it and moves the hardware cursor there — so IME candidate windows appear in the right place."),
  ("每行末尾都追加 `SEGMENT_RESET`（重置样式并关闭超链接），一行的样式不会漏到下一行。", "`SEGMENT_RESET` (reset style, close hyperlinks) is appended to every line, so styles never leak into the next line."),
  ("`wantsKeyRelease` 默认 false：Kitty 协议的按键释放事件会被过滤，组件需要时再显式打开。", "`wantsKeyRelease` defaults to false: Kitty key-release events are filtered unless a component opts in."),
 ],
 how=[
  ("实现 `render(width)`：用 `visibleWidth()` / `truncateToWidth()` 保证每行不超宽。", "Implement `render(width)`: use `visibleWidth()` / `truncateToWidth()` so no line is too wide."),
  ("需要输入就实现 `handleInput(data)`，用 `matchesKey(data, \"ctrl+c\")` 等判断按键。", "For input, implement `handleInput(data)` and test keys with `matchesKey(data, \"ctrl+c\")` and friends."),
  ("缓存渲染结果时实现 `invalidate()`，主题变化时 TUI 会调用它。", "If you cache rendered output, implement `invalidate()`; the TUI calls it when the theme changes."),
 ],
 files=[
  (U + "tui.ts", r"^export interface Component\b", "Component", "组件接口", "component interface"),
  (U + "tui.ts", r"^export interface Focusable\b", "Focusable", "焦点", "focus"),
  (U + "tui.ts", r"^export const CURSOR_MARKER", "CURSOR_MARKER", "光标标记", "cursor marker"),
  (U + "tui.ts", r"^export class Container\b", "Container", "子组件拼接", "child concatenation"),
  (U + "tui.ts", r"^export interface TUI extends Component", "TUI", "TUI 接口", "TUI interface"),
 ]),

dict(id="tui-render", group="flows", layer="tui", diagram="tui_render",
 title=("差分渲染", "Differential rendering"),
 takeaway=("`requestRender()` 不立即渲染：同一 tick 内的请求被合并，两帧之间至少间隔 16ms；按键则走 `requestImmediateRender()` 立即出帧。regular 屏幕按行比较新旧两帧，只重写第一处到最后一处变化之间的行，并且整个写入包在同步输出序列里。",
           "`requestRender()` does not render right away: requests in one tick are merged and frames are at least 16 ms apart; key presses use `requestImmediateRender()` for an immediate frame. The regular screen compares old and new frames line by line, rewrites only the lines from the first to the last change, and wraps the whole write in synchronized output."),
 points=[
  ("宽度变化、高度变化（Termux 除外）、内容变短（开启 `clearOnShrink` 时）以及变化发生在视口上方时，会清屏重绘——终端滚动区里已经滚出去的行无法原地修改。", "A width change, a height change (except on Termux), shrinking content (with `clearOnShrink`) or a change above the viewport triggers a full redraw — lines already scrolled into the terminal's history cannot be edited in place."),
  ("只删了行时不重写任何内容，只清掉尾部多出来的行。", "If lines were only deleted, nothing is rewritten; the extra tail lines are just cleared."),
  ("Kitty 图片占多行：变化区间会扩大到覆盖整张图，避免半张图残留。", "Kitty images span several rows: the changed range widens to cover the whole image so no half-image remains."),
  ("`TUI.fullRedraws` 记录全量重绘次数，可用来检查组件是否引起了不必要的重绘。", "`TUI.fullRedraws` counts full redraws, handy for spotting components that cause needless redraws."),
 ],
 how=[
  ("准备一帧：`render(width)` → `compositeOverlays()` → `extractCursorPosition()` → `applyLineResets()`。", "Prepare a frame: `render(width)` → `compositeOverlays()` → `extractCursorPosition()` → `applyLineResets()`."),
  ("依次判断是否需要全量重绘（见图中 7 个判断）。", "Check, in order, whether a full redraw is needed (the seven checks in the figure)."),
  ("否则移动光标到 `firstChanged`，逐行写到 `lastChanged`，每行先 `\\x1b[2K` 清除。", "Otherwise move to `firstChanged` and write each line through `lastChanged`, clearing each with `\\x1b[2K` first."),
  ("最后把硬件光标放到 `CURSOR_MARKER` 的位置。", "Finally place the hardware cursor where `CURSOR_MARKER` was."),
 ],
 files=[
  (U + "tui.ts", r"^\trequestRender\(force", "requestRender()", "合并与节流", "coalesce and throttle"),
  (U + "tui.ts", r"MIN_RENDER_INTERVAL_MS = 16", "MIN_RENDER_INTERVAL_MS", "16ms", "16 ms"),
  (U + "tui.ts", r"private requestImmediateRender\(", "requestImmediateRender()", "输入后立即渲染", "render right after input"),
  (U + "tui-main-screen.ts", r"^export class TuiMainScreen", "TuiMainScreen", "regular 屏幕", "the regular screen"),
  (U + "tui-main-screen.ts", r"protected doRender\(\)", "doRender()", "差分逻辑", "the diff logic"),
 ]),

dict(id="tui-screens", group="flows", layer="tui", diagram="tui_screens",
 title=("两种屏幕：regular 与 fullscreen", "Two screens: regular and fullscreen"),
 takeaway=("regular（`TuiMainScreen`）把内容写进终端自己的滚动区，退出后历史仍在；fullscreen（`TuiAltScreen`）进入备用屏，自己管理滚动、鼠标、选择与搜索，每帧按屏幕行比较。pi-coding-agent 默认用 fullscreen，可在设置里改为 regular。",
           "Regular (`TuiMainScreen`) writes into the terminal's own scrollback, so history survives exit; fullscreen (`TuiAltScreen`) switches to the alternate screen and manages scrolling, mouse, selection and search itself, diffing by screen row every frame. pi-coding-agent defaults to fullscreen; settings can switch it to regular."),
 points=[
  ("备用屏一帧依次经过：布局帧 → 搜索高亮 → 回到底部提示 → 覆盖层 → 选区 → 短暂提示 → 光标与行尾重置，最后只写变化的行。", "An alternate-screen frame goes through: layout frame → search highlights → jump-to-end pill → overlays → selection → flashes → cursor and line resets, then only changed rows are written."),
  ("备用屏开启鼠标报告（`?1000/?1002/?1003/?1004/?1006`），滚轮带加速，选择后可通过 OSC 52 复制。", "The alternate screen enables mouse reporting (`?1000/?1002/?1003/?1004/?1006`), accelerated wheel scrolling, and copy via OSC 52 after a selection."),
  ("布局用 `HStack` / `VStack` / `ScrollView`，支持 basis / grow / shrink；regular 屏幕不需要这些。", "Layout uses `HStack` / `VStack` / `ScrollView` with basis / grow / shrink; the regular screen does without."),
 ],
 how=[
  ("`TuiAltScreen.start()` 写 `\\x1b[?1049h` 进入备用屏并开启鼠标。", "`TuiAltScreen.start()` writes `\\x1b[?1049h` to enter the alternate screen and enables the mouse."),
  ("`doRender()` 调 `renderLayoutFrame(root, width, height)` 得到布局与行。", "`doRender()` calls `renderLayoutFrame(root, width, height)` for the layout and lines."),
  ("与 `previousScreen` 逐行比较；尺寸变化时整屏重绘。", "Compare row by row with `previousScreen`; redraw the whole screen when the size changes."),
 ],
 files=[
  (U + "tui-alt-screen.ts", r"^export class TuiAltScreen", "TuiAltScreen", "fullscreen 屏幕", "the fullscreen screen"),
  (U + "tui-alt-screen.ts", r"protected override doRender\(\)", "doRender()", "备用屏一帧", "one alt-screen frame"),
  (U + "layout.ts", r"^export function renderLayoutFrame\(", "renderLayoutFrame()", "布局帧", "layout frame"),
  (U + "wheel-scroll.ts", r"MAX_AUTO_LINES", "MAX_AUTO_LINES", "滚轮加速上限", "wheel acceleration cap"),
  ("packages/coding-agent/src/core/settings-manager.ts", r"getTuiMode\(\): TuiMode", "getTuiMode()", "默认 fullscreen", "defaults to fullscreen"),
 ]),

dict(id="tui-input", group="flows", layer="tui", diagram="tui_input",
 title=("输入与按键", "Input and keys"),
 takeaway=("stdin 的原始字节先由 `StdinBuffer` 拼成完整的转义序列，再经过 `handleTerminalInput()` 的 8 个步骤——终端回复、输入监听器、调试键、覆盖层焦点修复、按键释放过滤——最后才交给获得焦点的组件。",
           "Raw stdin bytes are first assembled into whole escape sequences by `StdinBuffer`, then pass the eight steps of `handleTerminalInput()` — terminal replies, input listeners, the debug key, overlay focus repair, key-release filtering — before reaching the focused component."),
 points=[
  ("单独的 ESC 要等 10ms 才能确定是 Escape 键而不是序列开头；SSH 下默认 100ms，可用 `PI_TUI_ESC_TIMEOUT` 调整。", "A lone ESC needs 10 ms to be sure it is the Escape key rather than the start of a sequence; 100 ms over SSH, adjustable with `PI_TUI_ESC_TIMEOUT`."),
  ("启动时请求 Kitty 键盘协议（flags 7）；终端不回复时改用 modifyOtherKeys，这样 shift+enter 等组合键仍可区分。", "Start-up requests the Kitty keyboard protocol (flags 7); if the terminal stays silent it falls back to modifyOtherKeys so combos like shift+enter remain distinguishable."),
  (f"按键用语义 id 表示（`tui.input.submit`、`tui.editor.undo` …，共 {_KB} 个），默认键位可被用户覆盖。", f"Keys are referred to by semantic ids (`tui.input.submit`, `tui.editor.undo` …, {_KB} in total), and users can override the default bindings."),
 ],
 how=[
  ("`ProcessTerminal.start()` 打开 raw 模式与括号粘贴，并发送协议查询。", "`ProcessTerminal.start()` enables raw mode and bracketed paste and sends the protocol queries."),
  ("`StdinBuffer` 输出完整序列；括号粘贴内容作为一整段交付。", "`StdinBuffer` emits whole sequences; bracketed-paste content is delivered as one chunk."),
  ("`handleTerminalInput(data)` 走完 8 步，调用 `focused.handleInput(data)`，再立即渲染。", "`handleTerminalInput(data)` runs the eight steps, calls `focused.handleInput(data)`, then renders immediately."),
  ("组件里用 `getKeybindings().matches(data, id)` 或 `matchesKey(data, \"ctrl+c\")` 判断。", "Inside components, test with `getKeybindings().matches(data, id)` or `matchesKey(data, \"ctrl+c\")`."),
 ],
 files=[
  (U + "stdin-buffer.ts", r"DEFAULT_ESCAPE_TIMEOUT_MS = 10", "StdinBuffer", "序列重组", "sequence reassembly"),
  (U + "terminal.ts", r"^export function resolveEscapeTimeoutMs\(", "resolveEscapeTimeoutMs()", "ESC 超时", "ESC timeout"),
  (U + "tui.ts", r"private handleTerminalInput\(", "handleTerminalInput()", "8 步分发", "eight-step dispatch"),
  (U + "keys.ts", r"^export function matchesKey\(", "matchesKey()", "按键匹配", "key matching"),
  (U + "keybindings.ts", r"^export const TUI_KEYBINDINGS", "TUI_KEYBINDINGS", "默认键位", "default bindings"),
  (U + "keybindings.ts", r"^export class KeybindingsManager", "KeybindingsManager", "可覆盖的绑定", "overridable bindings"),
 ]),

dict(id="tui-editor", group="flows", layer="tui", diagram="tui_editor",
 title=("编辑器与自动补全", "The editor and autocomplete"),
 takeaway=("`Editor` 是一个完整的多行编辑器：状态是 `{ lines, cursorLine, cursorCol }`，配有快照式撤销、Emacs 风格的 kill ring、最多 100 条历史和大段粘贴折叠。`handleInput()` 按固定顺序尝试 13 类按键；自动补全由可替换的 `AutocompleteProvider` 提供。",
           "`Editor` is a full multi-line editor: its state is `{ lines, cursorLine, cursorCol }`, with snapshot undo, an Emacs-style kill ring, up to 100 history entries and folding of large pastes. `handleInput()` tries 13 kinds of keys in a fixed order; completions come from a swappable `AutocompleteProvider`."),
 points=[
  ("超过 10 行或 1000 字符的粘贴显示为 `[paste #1 +42 lines]` 这样的标记，提交时再换回原文——编辑器本身保持轻量。", "Pastes over 10 lines or 1000 characters show as markers like `[paste #1 +42 lines]` and expand back on submit — the editor itself stays light."),
  ("内置的 `CombinedAutocompleteProvider` 处理三种情况：行首 `/` 的斜杠命令（模糊匹配）、`@` 文件附件（用 fd 搜索，20ms 防抖）、Tab 路径补全。", "The built-in `CombinedAutocompleteProvider` covers three cases: `/` slash commands at line start (fuzzy matched), `@` file attachments (searched with fd, 20 ms debounce), and Tab path completion."),
  ("光标前一个字符是 `\\` 时，Enter 会删掉它并插入换行而不是提交——给不支持 shift+enter 的终端用。", "When the character before the cursor is `\\`, Enter deletes it and inserts a newline instead of submitting — a workaround for terminals without shift+enter."),
 ],
 how=[
  ("`handleInput(data)`：跳转模式 → 括号粘贴 → ctrl+c 交给上层 → 撤销 → 补全菜单 → … → 提交 → 插入字符。", "`handleInput(data)`: jump mode → bracketed paste → ctrl+c to the parent → undo → completion menu → … → submit → insert text."),
  ("输入触发字符后调用 `provider.getSuggestions(lines, line, col, { signal })`，结果显示在 `SelectList` 中。", "After a trigger character, `provider.getSuggestions(lines, line, col, { signal })` runs and results show in a `SelectList`."),
  ("确认后 `applyCompletion()` 返回新的文本与光标位置。", "On confirm, `applyCompletion()` returns the new text and cursor position."),
 ],
 files=[
  (U + "components/editor.ts", r"^export class Editor\b", "Editor", "编辑器", "the editor"),
  (U + "components/editor.ts", r"^\thandleInput\(data: string\)", "handleInput()", "按键分支顺序", "key-branch order"),
  (U + "components/editor.ts", r"pastedLines.length > 10 \|\| totalChars > 1000", "paste markers", "粘贴折叠阈值", "paste-fold threshold"),
  (U + "autocomplete.ts", r"^export interface AutocompleteProvider", "AutocompleteProvider", "补全接口", "completion interface"),
  (U + "autocomplete.ts", r"^export class CombinedAutocompleteProvider", "CombinedAutocompleteProvider", "/ · @ · 路径", "/ · @ · paths"),
  (U + "kill-ring.ts", r"^export class KillRing", "KillRing", "kill / yank", "kill / yank"),
 ]),

dict(id="tui-overlay", group="flows", layer="tui", diagram="tui_overlay",
 title=("覆盖层", "Overlays"),
 takeaway=("`showOverlay(component, options)` 把一个组件画在其他内容之上并返回 `OverlayHandle`。位置由 9 个锚点、偏移、百分比 row/col 和边距决定；每帧在 `compositeOverlays()` 中按列拼进底层行。覆盖层组成一个栈，关闭时焦点回到打开前的组件。",
           "`showOverlay(component, options)` draws a component on top of everything and returns an `OverlayHandle`. Position comes from nine anchors, offsets, percentage row/col and margins; every frame `compositeOverlays()` splices it into the base lines by column. Overlays form a stack, and closing one returns focus to whatever had it before."),
 points=[
  ("默认居中，宽度为 `min(80, 可用宽度)`；`width` / `maxHeight` / `row` / `col` 都接受数字或 `\"50%\"` 这样的百分比。", "Default: centred, width `min(80, available)`; `width` / `maxHeight` / `row` / `col` accept a number or a percentage such as `\"50%\"`."),
  ("`visible(w, h)` 每帧重新求值：终端变小时覆盖层可以自动隐藏，焦点也随之转移。", "`visible(w, h)` is re-evaluated every frame: an overlay can hide itself on small terminals, and focus moves accordingly."),
  ("`nonCapturing: true` 的覆盖层只显示、不抢焦点，适合状态提示。", "A `nonCapturing: true` overlay shows without taking focus — good for status pop-ups."),
 ],
 how=[
  ("`showOverlay()` 记下当前焦点为 `preFocus`，把覆盖层压栈并聚焦（nonCapturing 除外）。", "`showOverlay()` records the current focus as `preFocus`, pushes the overlay and focuses it (unless nonCapturing)."),
  ("每帧：筛选可见的 → 解析宽度 → `render(width)` 并截到 maxHeight → 用实际高度解析 row/col → `compositeLineAt()`。", "Each frame: filter visible → resolve width → `render(width)` cut to maxHeight → resolve row/col with the real height → `compositeLineAt()`."),
  ("`hide()` 出栈，焦点交给下一个可见覆盖层或 `preFocus`。", "`hide()` pops it; focus goes to the next visible overlay or `preFocus`."),
 ],
 files=[
  (U + "tui.ts", r"^export interface OverlayOptions", "OverlayOptions", "位置与尺寸", "position and size"),
  (U + "tui.ts", r"^export interface OverlayHandle", "OverlayHandle", "控制句柄", "control handle"),
  (U + "tui.ts", r"private resolveOverlayLayout\(", "resolveOverlayLayout()", "布局计算", "layout maths"),
  (U + "tui.ts", r"protected compositeOverlays\(", "compositeOverlays()", "按列拼接", "column splicing"),
  (U + "tui.ts", r"^export type OverlayAnchor", "OverlayAnchor", "9 个锚点", "nine anchors"),
 ]),

dict(id="tui-terminal", group="arch", layer="tui", diagram="tui_terminal",
 title=("终端能力", "Terminal capabilities"),
 takeaway=("`ProcessTerminal` 在启动时协商能力（raw 模式、括号粘贴、Kitty 键盘协议或 modifyOtherKeys），运行中用 OSC 序列设置标题、进度和程序状态、查询前景/背景色。图片协议、真彩色和超链接按环境变量识别终端后决定，并可用 `PI_*` 环境变量覆盖。",
           "`ProcessTerminal` negotiates capabilities at start-up (raw mode, bracketed paste, Kitty keyboard protocol or modifyOtherKeys) and at run time uses OSC sequences for the title, progress, program status and fg/bg colour queries. Image protocol, truecolor and hyperlinks are decided by recognising the terminal from env vars, with `PI_*` overrides."),
 points=[
  ("图片：kitty、ghostty、wezterm、warp 用 Kitty 图形协议，iTerm2 用自己的协议；tmux、screen 与其他终端不显示图片。", "Images: kitty, ghostty, wezterm and warp use the Kitty graphics protocol, iTerm2 its own; tmux, screen and other terminals show no images."),
  ("超链接（OSC 8）只在确认支持的终端里开启，否则 URL 会被吞掉；tmux 下会实际探测是否转发。", "Hyperlinks (OSC 8) are enabled only where known to work, since otherwise the URL disappears; under tmux forwarding is actually probed."),
  ("DA 查询（`\\x1b[c`）用作“查询结束”的哨兵：在它之前没收到 Kitty 回复，就说明终端不支持。", "The DA query (`\\x1b[c`) is the end-of-queries sentinel: no Kitty reply before it means no support."),
 ],
 how=[
  ("`start(onInput, onResize)`：raw 模式 → `?2004h` → Kitty 查询 → DA。", "`start(onInput, onResize)`: raw mode → `?2004h` → Kitty query → DA."),
  ("`detectCapabilities()` 根据 `TERM_PROGRAM`、`KITTY_WINDOW_ID`、`TMUX` 等变量给出 images / trueColor / hyperlinks。", "`detectCapabilities()` derives images / trueColor / hyperlinks from `TERM_PROGRAM`, `KITTY_WINDOW_ID`, `TMUX` and similar variables."),
  ("`stop()` 关闭各模式并恢复原来的 raw 状态。", "`stop()` turns the modes off and restores the previous raw state."),
 ],
 files=[
  (U + "terminal.ts", r"^export interface Terminal\b", "Terminal", "终端接口", "terminal interface"),
  (U + "terminal.ts", r"KITTY_KEYBOARD_PROTOCOL_QUERY = ", "KITTY_KEYBOARD_PROTOCOL_QUERY", "Kitty 查询", "Kitty query"),
  (U + "terminal-image.ts", r"^export function detectCapabilities\(", "detectCapabilities()", "能力识别", "capability detection"),
  (U + "terminal-colors.ts", r"^export ", "terminal colours", "颜色查询", "colour queries"),
  (U + "program-status.ts", r"^export interface ProgramStatus", "ProgramStatus", "OSC 7501", "OSC 7501"),
 ]),
]

EXT_POINTS = [
 ("Component", ("实现 render(width) 即可成为组件；可选 handleInput / handleMouse。", "Implement render(width) to be a component; handleInput / handleMouse are optional.")),
 ("AutocompleteProvider", ("替换或组合补全来源。", "Replace or combine completion sources.")),
 ("KeybindingsManager", ("覆盖默认键位，或增加自己的按键 id。", "Override default bindings or add your own key ids.")),
 ("showOverlay(component, options)", ("对话框、选择器、提示浮层。", "Dialogs, pickers, pop-ups.")),
 ("addInputListener()", ("在组件之前拦截或改写输入。", "Intercept or rewrite input before components see it.")),
 ("Terminal", ("实现接口即可在非真实终端上运行（测试、虚拟终端）。", "Implement the interface to run on something other than a real terminal (tests, virtual terminals).")),
 ("PI_IMAGE_PROTOCOL · PI_TRUE_COLOR · PI_HYPERLINKS", ("手动覆盖能力识别结果。", "Manually override capability detection.")),
]
XREF = [('coding-agent', ('interactive 模式如何用 pi-tui 搭出整个界面', 'how interactive mode builds the whole UI on pi-tui'))]
