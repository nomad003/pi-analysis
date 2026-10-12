"""Shared helpers for the per-package deep-dive diagrams (built on svgkit)."""
import re
from pathlib import Path
from svgkit import Fig, maxw, tw, icon, pair, esc

SRC = Path('/workspace/pi-src')

def lines_of(path):
    return sum(1 for _ in open(SRC / path, errors='ignore'))

def uml(f, cid, x, y, w, layer, name, stereo=None, sections=(), lh=17):
    """UML-style class card (same look as the v1 `classes` diagram). Returns height."""
    rows = sum(len(s) for s in sections)
    h = 34 + rows * lh + len(sections) * 9 + 2
    g = [f'<g class="nd c-{layer} k-uml" data-id="{cid}">', f'<rect class="card" x="{x}" y="{y}" width="{w}" height="{h}" rx="10" filter="url(#pd-sh)"/>',
         f'<path class="uml-h" d="M{x} {y+10}a10 10 0 0 1 10-10h{w-20}a10 10 0 0 1 10 10v22h-{w}z"/>']
    if stereo:
        g.append(f.text(x + 12, y + 21, stereo, 9.5, 500, True, cls='faint', layer=None, owner=cid))
        g.append(f.text(x + 12 + maxw(stereo, 9.5, 500, True) + 6, y + 21, name, 12.5, 680, True, cls='cf', layer=None, owner=cid))
        if maxw(stereo, 9.5, 500, True) + 6 + maxw(name, 12.5, 680, True) > w - 20: f.warn.append(f'{f.key}: uml header too long {name}')
    else:
        g.append(f.text(x + 12, y + 21, name, 12.5, 680, True, cls='cf', layer=None, owner=cid))
    yy = y + 32
    for si, sec in enumerate(sections):
        if si: g.append(f'<line class="rule" x1="{x+1}" y1="{yy+2}" x2="{x+w-1}" y2="{yy+2}"/>')
        yy += 6
        for line in sec:
            yy += lh
            vis = line[0] if isinstance(line, str) and line[:1] in '+-#|' else ''
            txt = line[1:] if vis else line
            cls = 'muted' if vis == '-' else 'strongt'
            mark = {'+': '+', '-': '−', '#': '#', '|': '|', '': ''}[vis]
            g.append(f.text(x + 12, yy - 4, mark, 10, 600, True, cls='faint', layer=None, owner=cid))
            g.append(f.text(x + 24, yy - 4, txt, 10, 450, not isinstance(txt, tuple), cls=cls, layer=None, owner=cid))
            if maxw(txt, 10, 450, not isinstance(txt, tuple)) > w - 34: f.warn.append(f'{f.key}: uml line too long {pair(txt)[1]}')
        yy += 3
    g.append('</g>')
    f.L['node'].append(''.join(g)); f.nodes[cid] = (x, y, w, h); f.solid.append((cid, (x, y, w, h)))
    return h

def codebox(f, x, y, w, lines, title=None, size=10.5, lh=16, layer='grp', tlayer='label'):
    """Mono code panel. lines: list of (indent, text, cls) or strings."""
    h = 14 + (22 if title else 0) + len(lines) * lh
    f.raw(f'<rect class="codebg" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>', layer)
    yy = y + 8
    if title:
        f.text(x + 12, yy + 13, title, 10, 650, False, cls='faint', layer=tlayer, ls='.04em'); yy += 22
    for ln in lines:
        ind, txt, cls = (ln if isinstance(ln, tuple) and len(ln) == 3 else (0, ln, 'muted'))
        yy += lh
        f.text(x + 12 + ind * 14, yy - 4, txt, size, 450 if cls != 'strongt' else 600, True, cls=cls, layer=tlayer)
        if maxw(txt, size, 450, True) + 24 + ind * 14 > w: f.warn.append(f'{f.key}: code line too long {pair(txt)[1]}')
    return h

def bar(f, x, y, w, layer, txt=None, h=22, size=10, mono=True, dashed=False, cls='fillcb'):
    st = ' style="stroke-dasharray:3 3"' if dashed else ''
    f.raw(f'<g class="c-{layer}"><rect class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="5"{st}/></g>', 'node')
    if txt:
        f.text(x + w / 2, y + h / 2 + size * 0.36, txt, size, 600, mono, 'middle', cls='cf c-' + layer, layer='label')
        if maxw(txt, size, 600, mono) > w - 4: f.warn.append(f'{f.key}: bar text too long {pair(txt)[1]}')

def dot(f, cx, cy, layer, r=3.2):
    f.raw(f'<g class="c-{layer}"><circle class="fillc" cx="{cx:.1f}" cy="{cy:.1f}" r="{r}"/></g>', 'label')

def hline(f, x1, x2, y, cls='rule-d', layer='band'):
    f.raw(f'<line class="{cls}" x1="{x1}" y1="{y}" x2="{x2}" y2="{y}"/>', layer)

def vline(f, x, y1, y2, cls='rule-d', layer='band'):
    f.raw(f'<line class="{cls}" x1="{x}" y1="{y1}" x2="{x}" y2="{y2}"/>', layer)

def chiprow(f, x, y, items, layer='agent', size=10, h=20, gap=6, cls=''):
    """items: str | (text, layer) ; returns list of (x, w)."""
    out = []
    for it in items:
        t, l = (it if isinstance(it, tuple) and len(it) == 2 and isinstance(it[1], str) and it[1] in
                ('agent', 'ai', 'coding', 'ext', 'modes', 'tui', 'infra', 'err', 'accent') else (it, layer))
        w = f.chip(x, y, t, l, size=size, h=h, cls=cls)
        out.append((x, w)); x += w + gap
    return out
