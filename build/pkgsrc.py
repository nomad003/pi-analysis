"""Small source-reading helpers shared by figs9–11 (chord, durable, env)."""
import re, json
from figkit import SRC, lines_of

class Pkg:
    def __init__(self, base):
        self.base = base                      # e.g. 'packages/chord/src/'
        self.root = base.rsplit('src/', 1)[0]  # e.g. 'packages/chord/'
    def src(self, p): return (SRC / (self.base + p)).read_text()
    def loc(self, p): return lines_of(self.base + p)
    def has(self, p, *needles):
        s = self.src(p)
        for n in needles: assert n in s, (self.base + p, n)
    def total(self, sub='', ext=('.ts',)):
        d = SRC / (self.base + sub)
        return sum(lines_of(str(x.relative_to(SRC))) for x in d.rglob('*') if x.suffix in ext and not x.name.endswith(('.test.ts', '.d.ts')))
    def count(self, sub='', ext=('.ts',)):
        d = SRC / (self.base + sub)
        return sum(1 for x in d.rglob('*') if x.suffix in ext and not x.name.endswith(('.test.ts', '.d.ts')))
    def const(self, p, name):
        return re.search(r'\b' + name + r'(?::\s*[\w<>\[\]]+)?\s*=\s*([^;\n]+);', self.src(p)).group(1).strip()
    def num(self, p, name):
        v = self.const(p, name).replace('_', '')
        r = 1
        for x in v.split('*'): r *= int(x.strip())
        return r
    def pkg(self): return json.loads((SRC / (self.root + 'package.json')).read_text())
    def exports(self):
        j = self.pkg()
        return {k: (v['source'] if isinstance(v, dict) else v) for k, v in j['exports'].items() if k != './package.json'}
    def union(self, p, typename):
        blk = re.search(r'export type ' + typename + r'\s*=(.*?);', self.src(p), re.S).group(1)
        return re.findall(r'"([\w.-]+)"', blk)

def users_of(npm):
    """Workspace packages importing `npm` (or a subpath) in their src, with file counts."""
    out = []
    for pj in sorted((SRC / 'packages').glob('*/package.json')):
        d = pj.parent
        files = [x for x in (d / 'src').rglob('*.ts')] if (d / 'src').exists() else []
        n = sum(1 for x in files if re.search(r'from "' + re.escape(npm) + r'(/[^"]*)?"', x.read_text(errors='ignore')))
        if n and json.loads(pj.read_text())['name'] != npm: out.append((d.name, n))
    return sorted(out, key=lambda t: -t[1])

def MiB(n):
    if n % (1024 * 1024) == 0: return f'{n // (1024 * 1024)} MiB'
    return f'{n // 1024} KiB'
