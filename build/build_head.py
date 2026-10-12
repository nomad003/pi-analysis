#!/usr/bin/env python3
"""Build /workspace/pi-site from source-grounded content. Every file link is resolved against /workspace/pi-src."""
import html, json, os, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path('/workspace/pi-src')
OUT = Path(os.environ.get('PI_OUT', '/workspace/pi-site'))
sys.path.insert(0, str(HERE))
from content import SECTIONS, GROUPS  # noqa
from figs import build_all  # noqa
from svgkit import DEFS  # noqa
FIGS = build_all()
for _k, _f in FIGS.items():
    assert not _f.lint(), (_k, _f.lint())
from slides import SLIDES  # noqa

# The analysed source is the Pi release tag v1.1.0. Every GitHub link points at the tag.
VERSION = '1.1.0'
REF = 'v' + VERSION
SHA = subprocess.check_output(['git', '-C', str(SRC), 'rev-parse', 'HEAD'], text=True).strip()
TAG_SHA = subprocess.check_output(['git', '-C', str(SRC), 'rev-parse', REF + '^{commit}'], text=True).strip()
assert SHA == TAG_SHA, f'/workspace/pi-src must be checked out at {REF} ({TAG_SHA[:9]}), found {SHA[:9]}'
SHORT = SHA[:7]
GH = 'https://github.com/earendil-works/pi'
COMMIT_DATE = subprocess.check_output(['git', '-C', str(SRC), 'log', '-1', '--format=%cI'], text=True).strip()
SITE = ('图解 Pi Agent', 'Pi Agent, Illustrated')
SUBTITLE = (f'Pi v{VERSION} 源码分析', f'Analysis of Pi v{VERSION}')

# ---------------------------------------------------------------- facts (computed, then asserted)
def read(p): return (SRC / p).read_text(errors='ignore')

def line_of(path, pattern):
    if pattern is None: return None
    for i, l in enumerate(read(path).splitlines(), 1):
        if re.search(pattern, l): return i
    raise SystemExit(f'pattern not found: {path} :: {pattern}')

def gh(path, line=None):
    kind = 'tree' if (SRC / path).is_dir() else 'blob'
    if not (SRC / path).exists(): raise SystemExit('missing path ' + path)
    return f'{GH}/{kind}/{REF}/{path}' + (f'#L{line}' if line else '')

pkgs = sorted(p.name for p in (SRC / 'packages').iterdir() if (p / 'package.json').exists())
providers = len(re.findall(r'^import \{ \w+Provider \} from "\./', read('packages/ai/src/providers/all.ts'), re.M))
api = read('packages/coding-agent/src/core/extensions/types.ts')
api_block = api[api.index('export interface ExtensionAPI'):]
api_block = api_block[:api_block.index('\n}\n')]
ext_events = sorted(set(re.findall(r'\bon\(\s*event: "([a-z_]+)"', api_block)))
rpc = read('packages/coding-agent/src/modes/rpc/rpc-types.ts')
rpc_block = re.search(r'export type RpcCommand\s*=(.*?);\n\n', rpc, re.S).group(1)
rpc_cmds = sorted(set(re.findall(r'type: "([a-z_]+)"', rpc_block)))
tools = re.findall(r'"(\w+)"', re.search(r'export type ToolName = (.*);', read('packages/coding-agent/src/core/tools/index.ts')).group(1))
ai_events = re.findall(r'type: "([a-z_]+)"', re.search(r'export type AssistantMessageEvent\b(.*?)\n\n', read('packages/ai/src/types.ts'), re.S).group(1))
entry_types = sorted(set(re.findall(r'^\ttype: "([a-z_]+)";', read('packages/coding-agent/src/core/session-manager.ts'), re.M)) - {'session'})
known_api = re.findall(r'\| "([a-z-]+)"', re.search(r'export type KnownApi =(.*?);', read('packages/ai/src/types.ts'), re.S).group(1))
FACTS = dict(apis=len(known_api), packages=len(pkgs), providers=providers, ext_events=len(ext_events), rpc=len(rpc_cmds), tools=len(tools),
             ai_events=len(ai_events), entries=len(entry_types), modes=4)
EXPECT = dict(apis=10, packages=14, providers=42, ext_events=41, rpc=33, tools=8, ai_events=12, entries=11, modes=4)
assert FACTS == EXPECT, (FACTS, EXPECT)

# repo stats (same method as the original analysis)
def count_stats():
    out = []
    for p in pkgs:
        sf = sl = tf = tl = al = 0
        root = SRC / 'packages' / p
        for dp, dns, fns in os.walk(root):
            dns[:] = [x for x in dns if x not in ('node_modules', 'dist')]
            for f in fns:
                if not f.endswith('.ts') or f.endswith('.d.ts'): continue
                fp = Path(dp) / f; rel = fp.relative_to(root).as_posix(); al += 1
                n = sum(1 for _ in open(fp, errors='ignore'))
                if re.match(r'test[^/]*/', rel) or '.test.' in f: tf += 1; tl += n
                elif rel.startswith('src/'): sf += 1; sl += n
        out.append(dict(pkg=p, src_files=sf, src_loc=sl, test_files=tf, test_loc=tl, all_ts_files=al))
    return out
STATS = count_stats()
SRC_LOC = sum(s['src_loc'] for s in STATS); TEST_LOC = sum(s['test_loc'] for s in STATS)
PKG_LAYER = {'coding-agent': 'coding', 'agent': 'agent', 'ai': 'ai', 'tui': 'tui'}

