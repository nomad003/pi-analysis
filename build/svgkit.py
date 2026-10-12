"""Tiny exact-coordinate SVG diagram kit: measured text, rounded containers, cards with icons,
orthogonal connectors with drawn arrowheads, labelled edges, numbered steps, legends, and a geometric linter."""
import html, math
from functools import lru_cache
from PIL import ImageFont

INTER = '/usr/share/fonts/truetype/sand-box/google/Inter/Inter-VariableFont_opsz,wght.ttf'
MONO = '/usr/share/fonts/truetype/sand-box/google/JetBrains Mono/JetBrainsMono-VariableFont_wght.ttf'

@lru_cache(None)
def _font(path, size, weight):
    f = ImageFont.truetype(path, size=int(size * 4))
    try:
        axes = f.get_variation_axes()
        vals = []
        for a in axes:
            n = (a.get('name') or b'').decode() if isinstance(a.get('name'), bytes) else str(a.get('name'))
            if 'eight' in n or 'wght' in n: vals.append(weight)
            elif 'ptical' in n or 'opsz' in n: vals.append(max(a['minimum'], min(a['maximum'], size)))
            else: vals.append(a.get('default', a['minimum']))
        f.set_variation_by_axes(vals)
    except Exception:
        pass
    return f

def tw(s, size=13, weight=400, mono=False):
    """Text width in px (CJK = 1em, Latin measured with Inter / JetBrains Mono)."""
    f = _font(MONO if mono else INTER, size, weight)
    w = 0.0; run = ''
    for ch in s:
        if ord(ch) >= 0x2E80 or ch in '，。：；！？（）、《》“”‘’…—「」':
            if run: w += f.getlength(run) / 4; run = ''
            w += size * (1.0 if ch != '…' else 1.0)
        else: run += ch
    if run: w += f.getlength(run) / 4
    return w

def esc(s): return html.escape(str(s), quote=True)

def pair(s):
    return s if isinstance(s, tuple) else (s, s)

def maxw(s, size=13, weight=400, mono=False):
    zh, en = pair(s)
    return max(tw(zh, size, weight, mono), tw(en, size, weight, mono))

# ------------------------------------------------------------------ icons (24-unit grid, stroke)
ICONS = {
 'user': '<circle cx="12" cy="8" r="4"/><path d="M4.5 20.5c.6-3.9 3.7-6.5 7.5-6.5s6.9 2.6 7.5 6.5"/>',
 'terminal': '<rect x="2.5" y="4" width="19" height="16" rx="3"/><path d="M7 9.5l3 2.5-3 2.5M12.5 15h4.5"/>',
 'code': '<path d="M8.5 7L3.5 12l5 5M15.5 7l5 5-5 5M13.5 5l-3 14"/>',
 'box': '<path d="M12 2.8l8.2 4.4v9.6L12 21.2l-8.2-4.4V7.2z"/><path d="M3.8 7.2L12 11.6l8.2-4.4M12 11.6v9.6"/>',
 'layers': '<path d="M12 3.5l8.5 4.5-8.5 4.5L3.5 8z"/><path d="M3.5 12.5l8.5 4.5 8.5-4.5"/><path d="M3.5 16.5l8.5 4.5 8.5-4.5"/>',
 'loop': '<path d="M19.5 10A7.8 7.8 0 0 0 5.6 7.3L4 9"/><path d="M4 4.5V9h4.5"/><path d="M4.5 14a7.8 7.8 0 0 0 13.9 2.7L20 15"/><path d="M20 19.5V15h-4.5"/>',
 'spark': '<path d="M12 3l2.1 5.6L19.7 11l-5.6 2.1L12 18.7l-2.1-5.6L4.3 11l5.6-2.4z"/><path d="M19 17v4M17 19h4"/>',
 'plug': '<path d="M9 2.5v4.5M15 2.5v4.5"/><path d="M6.5 7h11v3.5a5.5 5.5 0 0 1-11 0z"/><path d="M12 16v5.5"/>',
 'tool': '<path d="M14.7 6.3a4.2 4.2 0 0 0 5.2 5.2l-1.6-1.6-1.4-3.6-3.6-1.4z"/><path d="M14.7 6.3L4.8 16.2a2.1 2.1 0 0 0 3 3l9.9-9.9"/>',
 'db': '<ellipse cx="12" cy="5.5" rx="7.5" ry="3"/><path d="M4.5 5.5v13c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3v-13"/><path d="M4.5 12c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3"/>',
 'file': '<path d="M14 2.8H7a2.2 2.2 0 0 0-2.2 2.2v14a2.2 2.2 0 0 0 2.2 2.2h10a2.2 2.2 0 0 0 2.2-2.2V8z"/><path d="M14 2.8V8h5.2M8.5 13h7M8.5 17h5"/>',
 'branch': '<circle cx="6" cy="5.5" r="2.3"/><circle cx="6" cy="18.5" r="2.3"/><circle cx="18" cy="7.5" r="2.3"/><path d="M6 7.8v8.4M18 9.8c0 4.2-6.5 3.6-11 6.6"/>',
 'bolt': '<path d="M13.5 2.5L4.5 14h7l-1 7.5 9-11.5h-7z"/>',
 'shield': '<path d="M12 2.8l7.5 2.9v5.6c0 4.6-3.2 8.2-7.5 9.9-4.3-1.7-7.5-5.3-7.5-9.9V5.7z"/><path d="M8.8 12l2.3 2.3 4.2-4.6"/>',
 'gear': '<circle cx="12" cy="12" r="3.2"/><path d="M12 2.8v2.6M12 18.6v2.6M2.8 12h2.6M18.6 12h2.6M5.5 5.5l1.9 1.9M16.6 16.6l1.9 1.9M5.5 18.5l1.9-1.9M16.6 7.4l1.9-1.9"/>',
 'clock': '<circle cx="12" cy="12" r="8.8"/><path d="M12 7v5.2l3.3 2"/>',
 'stream': '<path d="M3 7.5c2.2 0 2.2-2.5 4.5-2.5S9.8 7.5 12 7.5s2.2-2.5 4.5-2.5S18.8 7.5 21 7.5"/><path d="M3 13c2.2 0 2.2-2.5 4.5-2.5S9.8 13 12 13s2.2-2.5 4.5-2.5S18.8 13 21 13"/><path d="M3 18.5c2.2 0 2.2-2.5 4.5-2.5s2.3 2.5 4.5 2.5 2.2-2.5 4.5-2.5 2.3 2.5 4.5 2.5"/>',
 'queue': '<rect x="3.5" y="4" width="17" height="4.5" rx="1.5"/><rect x="3.5" y="10" width="17" height="4.5" rx="1.5"/><rect x="3.5" y="16" width="11" height="4.5" rx="1.5"/>',
 'msg': '<path d="M4 4.5h16a1.5 1.5 0 0 1 1.5 1.5v9.5a1.5 1.5 0 0 1-1.5 1.5H10l-5.5 4v-4H4a1.5 1.5 0 0 1-1.5-1.5V6A1.5 1.5 0 0 1 4 4.5z"/>',
 'monitor': '<rect x="2.8" y="3.8" width="18.4" height="12.4" rx="2.2"/><path d="M8.5 20.5h7M12 16.2v4.3"/>',
 'key': '<circle cx="7.5" cy="15.5" r="4"/><path d="M10.5 12.5l9-9M16.5 6.5l2.5 2.5"/>',
 'cpu': '<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9.5" y="9.5" width="5" height="5" rx=".8"/><path d="M9.5 2.8V6M14.5 2.8V6M9.5 18v3.2M14.5 18v3.2M2.8 9.5H6M2.8 14.5H6M18 9.5h3.2M18 14.5h3.2"/>',
 'scissors': '<circle cx="6" cy="6.5" r="2.7"/><circle cx="6" cy="17.5" r="2.7"/><path d="M8.2 8.2L20 18M8.2 15.8L20 6"/>',
 'compress': '<path d="M4 14.5h5.5V20M20 9.5h-5.5V4M14.5 9.5L21 3M3 21l6.5-6.5"/>',
 'braces': '<path d="M8.5 3.5c-2 0-3 1-3 3v2.3c0 1.4-.8 2.4-2 3.2 1.2.8 2 1.8 2 3.2v2.3c0 2 1 3 3 3M15.5 3.5c2 0 3 1 3 3v2.3c0 1.4.8 2.4 2 3.2-1.2.8-2 1.8-2 3.2v2.3c0 2-1 3-3 3"/>',
 'keyboard': '<rect x="2.5" y="6" width="19" height="12" rx="2.5"/><path d="M6.5 10h.01M10 10h.01M13.5 10h.01M17.5 10h.01M7 14h10"/>',
 'cloud': '<path d="M7.2 18.5a4.6 4.6 0 0 1-.6-9.2A6 6 0 0 1 18 9.2a4.7 4.7 0 0 1-.3 9.3z"/>',
 'globe': '<circle cx="12" cy="12" r="8.8"/><path d="M3.2 12h17.6M12 3.2c2.4 2.4 3.5 5.3 3.5 8.8s-1.1 6.4-3.5 8.8c-2.4-2.4-3.5-5.3-3.5-8.8s1.1-6.4 3.5-8.8z"/>',
 'filter': '<path d="M3.5 5h17l-6.5 7.5v5.5l-4 2.5v-8z"/>',
 'diff': '<path d="M12 3.5v8M8 7.5h8M8 17.5h8"/>',
 'check': '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
 'x': '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
 'play': '<path d="M7.5 4.8v14.4a.8.8 0 0 0 1.2.7l11.4-7.2a.8.8 0 0 0 0-1.4L8.7 4.1a.8.8 0 0 0-1.2.7z"/>',
 'flag': '<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>',
 'inbox': '<path d="M3 13.5h5l1.5 3h5l1.5-3h5"/><path d="M5.5 5h13l2.5 8.5v5a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 18.5v-5z"/>',
 'eye': '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="2.8"/>',
 'stack': '<rect x="4" y="3.5" width="16" height="5" rx="1.5"/><rect x="4" y="10" width="16" height="5" rx="1.5"/><rect x="4" y="16.5" width="16" height="4" rx="1.5"/>',
 'hub': '<circle cx="12" cy="12" r="3"/><circle cx="4.5" cy="5" r="1.8"/><circle cx="19.5" cy="5" r="1.8"/><circle cx="4.5" cy="19" r="1.8"/><circle cx="19.5" cy="19" r="1.8"/><path d="M6 6.4l3.8 3.6M18 6.4l-3.8 3.6M6 17.6l3.8-3.6M18 17.6l-3.8-3.6"/>',
 'tree': '<rect x="9" y="2.8" width="6" height="5" rx="1.2"/><rect x="2.8" y="16.2" width="6" height="5" rx="1.2"/><rect x="15.2" y="16.2" width="6" height="5" rx="1.2"/><path d="M12 7.8v4.2M5.8 16.2V12h12.4v4.2"/>',
}

def icon(name, x, y, size=16, cls='ico'):
    s = size / 24
    return f'<g class="{cls}" transform="translate({x:.1f},{y:.1f}) scale({s:.4f})">{ICONS[name]}</g>'

# ------------------------------------------------------------------ figure
class Fig:
    def __init__(self, key, w, h, title, grid=True):
        self.key, self.w, self.h, self.title = key, w, h, title
        self.L = {k: [] for k in ('bg', 'grp', 'band', 'edge', 'node', 'label', 'top')}
        self.nodes = {}       # id -> rect
        self.solid = []       # (id, rect) obstacles for edges
        self.segs = []        # (edge_idx, (x1,y1,x2,y2), a, b)
        self.lboxes = []      # (name, rect)
        self.texts = []       # (owner, rect)
        self.warn = []
        self.ne = 0
        self.grid = grid

    # ---- text
    def text(self, x, y, s, size=13, weight=400, mono=False, anchor='start', cls='', layer='top', fill=None, owner=None, ls=None):
        zh, en = pair(s)
        st = f' style="fill:{fill}"' if fill else ''
        common = f'x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}"' + (f' text-anchor="{anchor}"' if anchor != 'start' else '') + (f' letter-spacing="{ls}"' if ls else '')
        mc = ' mono' if mono else ''
        if zh == en:
            out = f'<text class="{cls}{mc}" {common}{st}>{esc(en)}</text>'
        else:
            out = f'<text class="zh {cls}{mc}" {common}{st}>{esc(zh)}</text><text class="en {cls}{mc}" {common}{st}>{esc(en)}</text>'
        w = maxw(s, size, weight, mono)
        x0 = x - (w if anchor == 'end' else w / 2 if anchor == 'middle' else 0)
        self.texts.append((owner, (x0, y - size * 0.78, w, size * 1.0)))
        if layer: self.L[layer].append(out)
        return out

    # ---- containers
    def group(self, x, y, w, h, layer, title, sub=None, icon_name=None, gid=None, dashed=False, r=16, title_mono=True):
        cls = f'grp c-{layer}' + (' dash' if dashed else '')
        g = [f'<g class="{cls}"' + (f' data-id="{gid}"' if gid else '') + '>',
             f'<rect class="grp-bg" x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/>']
        tx = x + 16
        if icon_name:
            g.append(f'<rect class="tile" x="{x+14}" y="{y+12}" width="22" height="22" rx="6"/>')
            g.append(icon(icon_name, x + 17, y + 15, 16))
            tx = x + 44
        g.append(self.text(tx, y + 27.5, title, 12.5, 650, title_mono, cls='grp-t', layer=None))
        if sub:
            sx = tx + maxw(title, 12.5, 650, title_mono) + 10
            g.append(self.text(sx, y + 27.5, sub, 11.5, 450, False, cls='grp-s', layer=None))
        g.append('</g>')
        self.L['grp'].append(''.join(g))
        if gid: self.nodes[gid] = (x, y, w, h)
        return (x, y, w, h)

    def band(self, x, y, w, h, cls='band'):
        self.L['band'].append(f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/>')

    # ---- nodes
    def node(self, nid, x, y, w, h, layer='coding', title='', sub=None, icon_name=None, mono=True, kind='card',
             tsize=13, ssize=11.5, align='left', strong=False, sub2=None, tag=None, solid=True, tweight=620):
        cls = f'nd c-{layer} k-{kind}' + (' strong' if strong else '')
        g = [f'<g class="{cls}" data-id="{nid}">']
        rx = h / 2 if kind in ('pill', 'term') else 10
        if kind == 'dec':
            rx = 10
        g.append(f'<rect class="card" x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" filter="url(#pd-sh)"/>')
        lines = [l for l in (title, sub, sub2) if l]
        sizes = [tsize, ssize, ssize][:len(lines)]
        lh = [s * 1.32 for s in sizes]
        block = sum(lh) - (lh[-1] - sizes[-1] * 1.0) if lines else 0
        cy = y + h / 2 - block / 2 + sizes[0] * 0.80 if lines else 0
        pad = 12
        if icon_name and align == 'left':
            ts = 26 if h >= 44 else 22
            g.append(f'<rect class="tile" x="{x+pad-2}" y="{y+h/2-ts/2:.1f}" width="{ts}" height="{ts}" rx="7"/>')
            isz = 16 if ts == 26 else 14
            g.append(icon(icon_name, x + pad - 2 + (ts - isz) / 2, y + h / 2 - isz / 2, isz))
            tx = x + pad - 2 + ts + 9
        elif kind == 'dec' and align == 'left':
            g.append(f'<path class="decg" d="M{x+pad+5} {y+h/2-6}l6 6-6 6-6-6z"/>')
            tx = x + pad + 17
        else:
            tx = x + pad
        if tag:
            tgw = maxw(tag, 9.5, 650, True) + 10
            g.append(f'<rect class="tag" x="{x+w-tgw-8:.1f}" y="{y+8}" width="{tgw:.1f}" height="15" rx="4"/>')
            g.append(self.text(x + w - tgw / 2 - 8, y + 18.8, tag, 9.5, 650, True, 'middle', 'tag-t', layer=None, owner=nid))
        anchor = 'middle' if align == 'center' else 'start'
        ax = x + w / 2 if align == 'center' else tx
        yy = cy
        for i, (l, s) in enumerate(zip(lines, sizes)):
            m = mono if i == 0 else (isinstance(l, tuple) is False and l.startswith('`'))
            txt = l.strip('`') if isinstance(l, str) else l
            if i == 0:
                g.append(self.text(ax, yy, txt, s, tweight, mono, anchor, 'n-t', layer=None, owner=nid))
            else:
                g.append(self.text(ax, yy, txt, s, 450, bool(m), anchor, 'n-s', layer=None, owner=nid))
            avail = (x + w - pad - (tgw + 12 if tag and i == 0 else 0)) - (tx if align == 'left' else x + pad)
            ww = maxw(txt, s, tweight if i == 0 else 450, mono if i == 0 else bool(m))
            if ww > avail + 0.5:
                self.warn.append(f'{self.key}: text overflows node {nid}: "{pair(txt)[1]}" {ww:.0f}>{avail:.0f}')
            yy += lh[i]
        g.append('</g>')
        self.L['node'].append(''.join(g))
        self.nodes[nid] = (x, y, w, h)
        if solid: self.solid.append((nid, (x, y, w, h)))
        return (x, y, w, h)

    def P(self, nid, side, t=0.5, off=0):
        x, y, w, h = self.nodes[nid]
        if side == 'top': return (x + w * t + off, y)
        if side == 'bottom': return (x + w * t + off, y + h)
        if side == 'left': return (x, y + h * t + off)
        if side == 'right': return (x + w, y + h * t + off)
        if side == 'c': return (x + w / 2, y + h / 2)

    # ---- edges
    @staticmethod
    def rpath(pts, r=9):
        d = f'M{pts[0][0]:.1f} {pts[0][1]:.1f}'
        for i in range(1, len(pts) - 1):
            (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
            d1 = math.hypot(x1 - x0, y1 - y0); d2 = math.hypot(x2 - x1, y2 - y1)
            rr = min(r, d1 / 2, d2 / 2)
            if d1 == 0 or d2 == 0: continue
            ax, ay = x1 - (x1 - x0) / d1 * rr, y1 - (y1 - y0) / d1 * rr
            bx, by = x1 + (x2 - x1) / d2 * rr, y1 + (y2 - y1) / d2 * rr
            d += f'L{ax:.1f} {ay:.1f}Q{x1:.1f} {y1:.1f} {bx:.1f} {by:.1f}'
        d += f'L{pts[-1][0]:.1f} {pts[-1][1]:.1f}'
        return d

    def edge(self, pts, a=None, b=None, kind='dep', layer=None, label=None, lpos=None, arrow=True, start=False,
             flow=False, lmono=True, lsize=11, step=None, spos=None, r=9, cls='', lcls='', smark=None, emark=None):
        pts = [tuple(map(float, p)) for p in pts]
        # drop duplicate points
        q = [pts[0]]
        for p in pts[1:]:
            if p != q[-1]: q.append(p)
        pts = q
        for i in range(len(pts) - 1):
            (x1, y1), (x2, y2) = pts[i], pts[i + 1]
            if abs(x1 - x2) > .01 and abs(y1 - y2) > .01:
                self.warn.append(f'{self.key}: non-orthogonal segment in edge {a}->{b}: {pts[i]} {pts[i+1]}')
        self.ne += 1
        idx = self.ne
        for i in range(len(pts) - 1):
            self.segs.append((idx, pts[i] + pts[i + 1], a, b))
        draw = list(pts)
        heads = []
        def head(p, q):  # arrow at p, coming from q
            dx, dy = p[0] - q[0], p[1] - q[1]; L = math.hypot(dx, dy) or 1
            ux, uy = dx / L, dy / L; px, py = -uy, ux
            tip = p; bx, by = p[0] - ux * 8, p[1] - uy * 8
            heads.append(f'M{tip[0]:.1f} {tip[1]:.1f}L{bx+px*4.2:.1f} {by+py*4.2:.1f}Q{p[0]-ux*6:.1f} {p[1]-uy*6:.1f} {bx-px*4.2:.1f} {by-py*4.2:.1f}Z')
            return (p[0] - ux * 6, p[1] - uy * 6)
        marks = []
        def uml(p, q, kind):
            dx, dy = p[0] - q[0], p[1] - q[1]; L = math.hypot(dx, dy) or 1
            ux, uy = dx / L, dy / L; px, py = -uy, ux
            if kind in ('diamond', 'odiamond'):
                a = (p[0] - ux * 7, p[1] - uy * 7); bb = (p[0] - ux * 14, p[1] - uy * 14)
                marks.append((kind, f'M{p[0]:.1f} {p[1]:.1f}L{a[0]+px*4.5:.1f} {a[1]+py*4.5:.1f}L{bb[0]:.1f} {bb[1]:.1f}L{a[0]-px*4.5:.1f} {a[1]-py*4.5:.1f}Z'))
                return bb
            if kind == 'tri':
                b2 = (p[0] - ux * 11, p[1] - uy * 11)
                marks.append((kind, f'M{p[0]:.1f} {p[1]:.1f}L{b2[0]+px*6:.1f} {b2[1]+py*6:.1f}L{b2[0]-px*6:.1f} {b2[1]-py*6:.1f}Z'))
                return b2
        if emark: draw[-1] = uml(pts[-1], pts[-2], emark)
        elif arrow: draw[-1] = head(pts[-1], pts[-2])
        if smark: draw[0] = uml(pts[0], pts[1], smark)
        elif start: draw[0] = head(pts[0], pts[1])
        d = self.rpath(draw, r)
        lc = f' c-{layer}' if layer else ''
        attrs = f' data-a="{a or ""}" data-b="{b or ""}"'
        g = [f'<g class="ed k-{kind}{lc}{" flow" if flow else ""} {cls}"{attrs}>', f'<path class="ln" d="{d}"/>']
        if flow: g.append(f'<path class="fx" d="{d}"/>')
        for hd in heads: g.append(f'<path class="ah" d="{hd}"/>')
        for k2, md in marks: g.append(f'<path class="mk {k2}" d="{md}"/>')
        g.append('</g>')
        self.L['edge'].append(''.join(g))
        if label:
            if lpos is None:
                best = max(range(len(pts) - 1), key=lambda i: math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]))
                lpos = ((pts[best][0] + pts[best + 1][0]) / 2, (pts[best][1] + pts[best + 1][1]) / 2)
            self.elabel(lpos[0], lpos[1], label, mono=lmono, size=lsize, layer=layer, cls=lcls, owner=idx)
        if step is not None:
            sp = spos or pts[0]
            self.step(step, sp[0], sp[1], layer or 'accent')
        return idx

    def elabel(self, cx, cy, s, mono=True, size=11, layer=None, cls='', owner=None):
        w = maxw(s, size, 500, mono) + 14; h = size + 9
        x, y = cx - w / 2, cy - h / 2
        lc = f' c-{layer}' if layer else ''
        g = [f'<g class="el{lc} {cls}">', f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h/2:.1f}"/>',
             self.text(cx, cy + size * 0.36, s, size, 500, mono, 'middle', 'el-t', layer=None, owner=('lbl', owner)), '</g>']
        self.L['label'].append(''.join(g))
        self.lboxes.append((owner, (x, y, w, h)))

    def note(self, x, y, s, size=11, mono=False, anchor='start', cls='faint', weight=450):
        self.text(x, y, s, size, weight, mono, anchor, cls, layer='label', owner='note')

    def step(self, n, cx, cy, layer='accent', r=9.5, onnode=False):
        lc = f' c-{layer}'
        self.L['top'].append(f'<g class="stp{lc}"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}"/>'
                             f'<text x="{cx:.1f}" y="{cy+3.6:.1f}" text-anchor="middle" font-size="10.5" font-weight="700">{n}</text></g>')
        if not onnode: self.lboxes.append((('step', n), (cx - r, cy - r, 2 * r, 2 * r)))

    def chip(self, x, y, s, layer='infra', mono=True, size=10.5, h=20, owner=None, cls='', weight=550, dot=False):
        w = maxw(s, size, weight, mono) + (22 if dot else 14)
        g = [f'<g class="chipg c-{layer} {cls}">', f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="{min(6, h/2)}"/>']
        tx = x + 7
        if dot:
            g.append(f'<circle class="dot" cx="{x+9:.1f}" cy="{y+h/2:.1f}" r="3"/>'); tx = x + 16
        g.append(self.text(tx, y + h / 2 + size * 0.36, s, size, weight, mono, cls='chip-t', layer=None, owner=owner or 'chip'))
        g.append('</g>')
        self.L['node'].append(''.join(g))
        return w

    def raw(self, s, layer='node'): self.L[layer].append(s)

    def legend(self, x, y, items, gap=22):
        """items: (kind, label) kind in dep|event|err|main|dev|step|layer:<l>|ref"""
        cx = x
        out = ['<g class="lg">']
        for kind, lab in items:
            if kind.startswith('layer:'):
                l = kind.split(':')[1]
                out.append(f'<rect class="lg-sw c-{l}" x="{cx:.1f}" y="{y-6}" width="14" height="12" rx="3.5"/>'); cx += 20
            elif kind == 'step':
                out.append(f'<g class="stp c-accent"><circle cx="{cx+8:.1f}" cy="{y}" r="7.5"/><text x="{cx+8:.1f}" y="{y+3.3:.1f}" text-anchor="middle" font-size="9" font-weight="700">1</text></g>'); cx += 22
            else:
                out.append(f'<g class="ed k-{kind}{" c-accent" if kind == "main" else ""}"><path class="ln" d="M{cx:.1f} {y}h22"/><path class="ah" d="M{cx+28:.1f} {y}l-8 -4.2q2 4.2 0 8.4z"/></g>'); cx += 36
            out.append(self.text(cx, y + 4, lab, 11, 500, False, cls='lg-t', layer=None, owner='legend'))
            cx += maxw(lab, 11, 500) + gap
        out.append('</g>')
        self.L['top'].append(''.join(out))
        self.lboxes.append(('legend', (x, y - 8, cx - x, 16)))
        return cx

    # ---- lint
    def lint(self):
        W = self.warn
        def inter(r1, r2, m=0):
            return r1[0] < r2[0] + r2[2] - m and r2[0] < r1[0] + r1[2] - m and r1[1] < r2[1] + r2[3] - m and r2[1] < r1[1] + r1[3] - m
        # segments through nodes
        for idx, (x1, y1, x2, y2), a, b in self.segs:
            sr = (min(x1, x2) - .5, min(y1, y2) - .5, abs(x2 - x1) + 1, abs(y2 - y1) + 1)
            for nid, r in self.solid:
                if nid in (a, b): continue
                if inter(sr, r, 1.5): W.append(f'{self.key}: edge {a}->{b} passes through node {nid}')
        # crossings
        S = self.segs
        for i in range(len(S)):
            for j in range(i + 1, len(S)):
                e1, s1, a1, b1 = S[i]; e2, s2, a2, b2 = S[j]
                if e1 == e2: continue
                h1 = abs(s1[1] - s1[3]) < .01; h2 = abs(s2[1] - s2[3]) < .01
                if h1 == h2:
                    # collinear overlap
                    if h1 and abs(s1[1] - s2[1]) < 2:
                        lo, hi = max(min(s1[0], s1[2]), min(s2[0], s2[2])), min(max(s1[0], s1[2]), max(s2[0], s2[2]))
                        if hi - lo > 2 and not ({a1, b1} & {a2, b2}): W.append(f'{self.key}: overlapping edges {a1}->{b1} / {a2}->{b2}')
                    if not h1 and abs(s1[0] - s2[0]) < 2:
                        lo, hi = max(min(s1[1], s1[3]), min(s2[1], s2[3])), min(max(s1[1], s1[3]), max(s2[1], s2[3]))
                        if hi - lo > 2 and not ({a1, b1} & {a2, b2}): W.append(f'{self.key}: overlapping edges {a1}->{b1} / {a2}->{b2}')
                    continue
                hs, vs = (s1, s2) if h1 else (s2, s1)
                y = hs[1]; x = vs[0]
                if min(hs[0], hs[2]) + 1 < x < max(hs[0], hs[2]) - 1 and min(vs[1], vs[3]) + 1 < y < max(vs[1], vs[3]) - 1:
                    W.append(f'{self.key}: crossing {a1}->{b1} x {a2}->{b2} at ({x:.0f},{y:.0f})')
        # labels vs nodes / labels / segments
        L = self.lboxes
        for i, (o1, r1) in enumerate(L):
            for nid, r in self.solid:
                if inter(r1, r, 1): W.append(f'{self.key}: label {o1} overlaps node {nid}')
            for o2, r2 in L[i + 1:]:
                if inter(r1, r2, 0.5): W.append(f'{self.key}: label {o1} overlaps label {o2}')
            for idx, (x1, y1, x2, y2), a, b in self.segs:
                if idx == o1 or (isinstance(o1, tuple) and o1[0] == 'step'): continue
                sr = (min(x1, x2) - .5, min(y1, y2) - .5, abs(x2 - x1) + 1, abs(y2 - y1) + 1)
                if inter(r1, sr, 0.5): W.append(f'{self.key}: label {o1} crosses edge {a}->{b}')
        # free text (notes) vs nodes
        for o, r in self.texts:
            if o == 'note':
                for nid, nr in self.solid:
                    if inter(r, nr, 1): W.append(f'{self.key}: note text overlaps node {nid}')
            if r[0] < -1 or r[1] < -1 or r[0] + r[2] > self.w + 1 or r[1] + r[3] > self.h + 1:
                W.append(f'{self.key}: text out of canvas {r}')
        for nid, (x, y, w, h) in self.nodes.items():
            if x < 0 or y < 0 or x + w > self.w or y + h > self.h: W.append(f'{self.key}: node {nid} out of canvas')
        return W

    def svg(self):
        bg = ''
        if self.grid:
            bg = f'<rect class="pd-grid" x="0" y="0" width="{self.w}" height="{self.h}" fill="url(#pd-dots)"/>'
        body = ''.join(''.join(self.L[k]) for k in ('bg', 'grp', 'band', 'edge', 'node', 'label', 'top'))
        t_zh, t_en = pair(self.title)
        return (f'<svg class="pd" id="pd-{self.key}" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" '
                f'role="img" aria-label="{esc(t_en)}" xmlns="http://www.w3.org/2000/svg">'
                f'<title>{esc(t_en)}</title>{bg}{body}</svg>')

DEFS = '''<svg class="pd-defs" width="0" height="0" aria-hidden="true" focusable="false" style="position:absolute;width:0;height:0;overflow:hidden"><defs>
<pattern id="pd-dots" width="16" height="16" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" style="fill:var(--dg-grid)"/></pattern>
<linearGradient id="pd-card" x1="0" y1="0" x2="0" y2="1"><stop offset="0" style="stop-color:var(--dg-card-top)"/><stop offset="1" style="stop-color:var(--dg-card)"/></linearGradient>
<filter id="pd-sh" x="-8%" y="-12%" width="116%" height="150%" color-interpolation-filters="sRGB">
<feGaussianBlur in="SourceAlpha" stdDeviation="0.6" result="b1"/><feOffset in="b1" dy="0.6" result="o1"/>
<feFlood style="flood-color:var(--dg-shadow)" result="c1"/><feComposite in="c1" in2="o1" operator="in" result="s1"/>
<feGaussianBlur in="SourceAlpha" stdDeviation="5" result="b2"/><feOffset in="b2" dy="4" result="o2"/>
<feFlood style="flood-color:var(--dg-shadow2)" result="c2"/><feComposite in="c2" in2="o2" operator="in" result="s2"/>
<feMerge><feMergeNode in="s2"/><feMergeNode in="s1"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs></svg>'''
