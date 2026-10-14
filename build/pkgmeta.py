"""Registry of all workspace packages. Mechanical facts come from package.json at build time; status/prose is editorial."""
import json
from pathlib import Path
SRC = Path('/workspace/pi-src')

# slug -> (dir, layer, status, zh blurb, en blurb [None = package.json description], group)
# status: done = full deep dive · partial = hosts moved v1 sections, deep dive planned · planned = generated stub
PKGS = [
 ('agent-core',   'agent',        'agent',  'done',    '通用 Agent：状态、事件循环、工具执行与钩子', None, 'core'),
 ('pi-ai',        'ai',           'ai',     'done',    '统一的 LLM API：模型目录、认证、42 个 provider、事件流', None, 'core'),
 ('coding-agent', 'coding-agent', 'coding', 'done',    '编码智能体 CLI：工具、会话树、压缩、扩展与运行模式', None, 'core'),
 ('tui',          'tui',          'tui',    'done',    '差分渲染的终端 UI 库', None, 'core'),
 ('mcp',          'mcp',          'ext',    'done',    '独立的 Model Context Protocol 客户端', None, 'capabilities'),
 ('codemode',     'codemode',     'ext',    'done',    '沙箱化 JavaScript 执行：唯一能力是调用注入的工具', None, 'capabilities'),
 ('telemetry',    'telemetry',    'infra',  'planned', '与厂商无关的遥测契约与类型化 schema 工具', None, 'capabilities'),
 ('chord',        'chord',        'infra',  'planned', '应用组合运行时：服务、复制状态、RPC 与插件', None, 'runtime'),
 ('durable',      'durable',      'infra',  'planned', '持久化的会话、任务与文档运行时', None, 'runtime'),
 ('env',          'env',          'infra',  'planned', 'Pi Durable 的远程执行环境（经 SSH 部署的小型守护进程）', None, 'runtime'),
 ('protocol',     'protocol',     'modes',  'planned', '远程 pi 会话的传输无关 CBOR 协议', None, 'remote'),
 ('client',       'client',       'modes',  'planned', '基于分帧 CBOR 的远程 pi 会话客户端', None, 'remote'),
 ('server',       'server',       'modes',  'planned', '实验性的 pi 服务端', None, 'remote'),
 ('evals',        'evals',        'infra',  'planned', '私有包：评测套件（Docker 化任务）', 'Private package: evaluation suites (dockerised tasks)', 'tooling'),
]
GROUP_NAME = {'core': ('核心栈', 'Core stack'), 'capabilities': ('能力包', 'Capabilities'), 'runtime': ('持久化与运行时', 'Durable runtime'),
              'remote': ('远程会话', 'Remote sessions'), 'tooling': ('工具链', 'Tooling')}
STATUS_NAME = {'done': ('已完成', 'Done'), 'partial': ('部分完成', 'Partial'), 'planned': ('计划中', 'Planned')}

def load():
    out = []
    by_npm = {}
    for slug, d, layer, status, zh, en, group in PKGS:
        j = json.loads((SRC / 'packages' / d / 'package.json').read_text())
        deps = sorted(k for k in j.get('dependencies', {}) if k.startswith('@earendil-works/'))
        dev = sorted(k for k in j.get('devDependencies', {}) if k.startswith('@earendil-works/'))
        ex = j.get('exports'); exports = [k for k in ex] if isinstance(ex, dict) else []
        exports = [e for e in exports if e != './package.json']
        b = j.get('bin'); bins = list(b) if isinstance(b, dict) else ([j['name'].split('/')[-1]] if b else [])
        p = dict(slug=slug, dir=d, layer=layer, status=status, group=group, npm=j['name'], version=j.get('version'), private=j.get('private', False),
                 desc=(zh, en or j.get('description') or ''), deps=deps, dev=dev, exports=exports, bins=bins,
                 ext_deps=sorted(k for k in j.get('dependencies', {}) if not k.startswith('@earendil-works/')))
        out.append(p); by_npm[p['npm']] = p
    for p in out:
        p['dep_slugs'] = [by_npm[n]['slug'] for n in p['deps'] if n in by_npm]
        p['dev_slugs'] = [by_npm[n]['slug'] for n in p['dev'] if n in by_npm]
    for p in out:
        p['dependents'] = [q['slug'] for q in out if p['slug'] in q['dep_slugs']]
        p['dev_dependents'] = [q['slug'] for q in out if p['slug'] in q['dev_slugs']]
    dirs = sorted(x.name for x in (SRC / 'packages').iterdir() if (x / 'package.json').exists())
    assert sorted(p['dir'] for p in out) == dirs, ('package list drifted', dirs)
    return out

# The per-package template every deep dive follows (also rendered on the roadmap and stub pages).
TEMPLATE = [
 ('overview', ('概览', 'Overview'), ('定位、依赖、规模、一句话结论', 'role, deps, size, one-line takeaway')),
 ('api', ('公共 API', 'Public API'), ('导出路径与导出符号（逐行链接）', 'export paths and exported symbols (line-linked)')),
 ('arch', ('内部架构图', 'Internal architecture'), ('模块 / 文件之间的结构', 'structure between modules and files')),
 ('flows', ('关键流程', 'Key flows'), ('时序、状态机、数据流', 'sequences, state machines, data flow')),
 ('types', ('数据类型', 'Data types'), ('核心接口与它们的关系', 'core interfaces and how they relate')),
 ('ext', ('扩展点', 'Extension points'), ('宿主可以替换或注入的地方', 'where a host can plug in or replace behaviour')),
 ('files', ('关键文件', 'Key files'), ('链接到 v1.1.0 的具体行', 'links to exact lines at v1.1.0')),
 ('tests', ('测试', 'Tests'), ('测试文件与用例数', 'test files and case counts')),
 ('xref', ('交叉链接', 'Cross-links'), ('相关包与相关章节', 'related packages and sections')),
]
