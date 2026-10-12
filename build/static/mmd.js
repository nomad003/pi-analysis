/* Shared Mermaid theme + renderer + lightbox for index.html and slides.html. */
(function () {
  const FONT = '"Inter", "Pi CJK", "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", system-ui, sans-serif';
  // [fill, stroke, text] per layer. One palette, used by every diagram, chip and chart.
  const PALETTE = {
    light: {
      modes: ['#fff6e5', '#f59e0b', '#7a3e06'], coding: ['#f2edff', '#8b5cf6', '#3b1a7a'],
      ext: ['#e5f8f5', '#14b8a6', '#0f4c45'], agent: ['#e8f0ff', '#3b82f6', '#1e3a8a'],
      ai: ['#e6f7ef', '#10b981', '#064e3b'], tui: ['#fdebf4', '#ec4899', '#831843'],
      infra: ['#f3f5f8', '#a3adbb', '#334155'], err: ['#fdeded', '#ef4444', '#7f1d1d'],
      term: ['#0f172a', '#0f172a', '#f8fafc'], dec: ['#ffffff', '#94a3b8', '#0f172a'],
    },
    dark: {
      modes: ['#2a1f0e', '#f5a524', '#fde7b5'], coding: ['#211a3b', '#a78bfa', '#ebe4ff'],
      ext: ['#0e2926', '#2dd4bf', '#c9f5ee'], agent: ['#12203b', '#60a5fa', '#dbe7ff'],
      ai: ['#0e291f', '#34d399', '#c9f3e1'], tui: ['#2d1323', '#f472b6', '#fbd5e8'],
      infra: ['#181c25', '#566173', '#cbd5e1'], err: ['#2d1315', '#f87171', '#fecaca'],
      term: ['#e7e9ee', '#e7e9ee', '#0b0d12'], dec: ['#11141b', '#64748b', '#e5e7eb'],
    },
  };
  const VARS = {
    light: {
      background: '#ffffff', primaryColor: '#f3f5f8', primaryBorderColor: '#a3adbb', primaryTextColor: '#0f172a',
      secondaryColor: '#f8fafc', tertiaryColor: '#ffffff', mainBkg: '#f3f5f8', nodeBorder: '#a3adbb',
      lineColor: '#9aa4b2', textColor: '#334155', titleColor: '#64748b',
      clusterBkg: '#fafbfc', clusterBorder: '#e3e7ed', edgeLabelBackground: '#ffffff',
      actorBkg: '#ffffff', actorBorder: '#cbd3de', actorTextColor: '#0f172a', actorLineColor: '#d5dbe3',
      signalColor: '#7b8594', signalTextColor: '#1f2937', labelBoxBkgColor: '#f8fafc', labelBoxBorderColor: '#cbd3de',
      labelTextColor: '#0f172a', loopTextColor: '#475569', noteBkgColor: '#fff8e6', noteBorderColor: '#f3c969',
      noteTextColor: '#6b3a06', activationBkgColor: '#eef2ff', activationBorderColor: '#a5b4fc',
      sequenceNumberColor: '#ffffff', classText: '#0f172a',
    },
    dark: {
      background: '#0d0f14', primaryColor: '#181c25', primaryBorderColor: '#566173', primaryTextColor: '#e5e7eb',
      secondaryColor: '#141820', tertiaryColor: '#0d0f14', mainBkg: '#181c25', nodeBorder: '#566173',
      lineColor: '#6b7585', textColor: '#cbd5e1', titleColor: '#94a3b8',
      clusterBkg: '#11141b', clusterBorder: '#262b36', edgeLabelBackground: '#0d0f14',
      actorBkg: '#141820', actorBorder: '#3a4250', actorTextColor: '#e5e7eb', actorLineColor: '#353c49',
      signalColor: '#8a94a5', signalTextColor: '#d6dbe3', labelBoxBkgColor: '#141820', labelBoxBorderColor: '#3a4250',
      labelTextColor: '#e5e7eb', loopTextColor: '#a3adbb', noteBkgColor: '#2a2210', noteBorderColor: '#8a6d1f',
      noteTextColor: '#fde7b5', activationBkgColor: '#1e2440', activationBorderColor: '#6366f1',
      sequenceNumberColor: '#0b0d12', classText: '#e5e7eb',
    },
  };

  const theme = () => (document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light');
  const hexA = (hex, a) => {
    const n = parseInt(hex.slice(1), 16);
    return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`;
  };

  function themed(src, t) {
    const pal = PALETTE[t];
    const head = (src.match(/^\s*(flowchart|graph|sequenceDiagram|classDiagram)/m) || [])[1];
    if (head === 'flowchart' || head === 'graph') {
      const defs = Object.entries(pal).map(([k, [f, s, c]]) =>
        `  classDef ${k} fill:${f},stroke:${s},color:${c},stroke-width:${k === 'term' || k === 'dec' ? 1.5 : 1.4}px`);
      return src + '\n' + defs.join('\n');
    }
    if (head === 'sequenceDiagram') {
      return src.replace(/^(\s*)box (\w+) (.*)$/gm, (m, sp, k, label) =>
        pal[k] ? `${sp}box ${hexA(pal[k][1], t === 'dark' ? 0.07 : 0.055)} ${label}` : m);
    }
    return src;
  }

  // Class diagrams: Mermaid's classDiagram ignores classDef fills, so colour nodes by their cssClass here.
  function classCss(id, t) {
    return Object.entries(PALETTE[t]).map(([k, [f, s, c]]) =>
      `#${id} g.node.${k} path:first-child,#${id} g.node.${k} rect{fill:${f}!important;stroke:${s}!important}` +
      `#${id} g.node.${k} path{stroke:${s}!important}` +
      `#${id} g.node.${k} .nodeLabel,#${id} g.node.${k} span,#${id} g.node.${k} p{color:${c}!important;fill:${c}!important}`).join('');
  }

  function init() {
    const t = theme();
    mermaid.initialize({
      startOnLoad: false, theme: 'base', securityLevel: 'strict', fontFamily: FONT,
      themeVariables: Object.assign({ fontFamily: FONT, fontSize: window.PI_MMD_FONT_SIZE || '14px' }, VARS[t]),
      flowchart: { curve: 'basis', htmlLabels: true, padding: 14, nodeSpacing: 34, rankSpacing: 46, diagramPadding: 12, useMaxWidth: true },
      sequence: { useMaxWidth: true, mirrorActors: false, width: 128, height: 46, actorMargin: 22, boxMargin: 8, boxTextMargin: 6, messageMargin: 30, noteMargin: 10, actorFontWeight: 600, messageFontSize: 13.5, noteFontSize: 13 },
      class: { useMaxWidth: true, padding: 10 },
    });
  }

  let seq = 0;
  const state = (window.__mmd = window.__mmd || { done: false, errors: [], rendered: 0 });

  async function renderInto(el) {
    const key = el.dataset.mmd;
    const src = (window.PI_DIAGRAMS || {})[key];
    if (!src) { state.errors.push(key + ': missing source'); return; }
    const id = 'mmd-' + key.replace(/\W/g, '') + '-' + (++seq);
    try {
      const { svg } = await mermaid.render(id, themed(src, theme()));
      el.innerHTML = svg;
      const s = el.querySelector('svg');
      if (/^\s*classDiagram/m.test(src)) {
        const st = document.createElementNS('http://www.w3.org/2000/svg', 'style');
        st.textContent = classCss(s.id, theme());
        s.appendChild(st);
      }
      const vb = s.viewBox.baseVal;
      el.dataset.w = Math.round(vb.width); el.dataset.h = Math.round(vb.height);
      el.classList.add('is-rendered');
      state.rendered++;
    } catch (e) {
      state.errors.push(key + ': ' + (e && e.message ? e.message : e));
      el.innerHTML = '<div class="mmd-error">Diagram failed to render: ' + key + '</div>';
      document.getElementById('d' + id)?.remove();
    }
  }

  async function renderAll(root) {
    state.done = false; state.errors = []; state.rendered = 0;
    try { await document.fonts.ready; } catch (e) {}
    init();
    for (const el of (root || document).querySelectorAll('[data-mmd]')) await renderInto(el);
    state.done = true;
    document.dispatchEvent(new CustomEvent('mmd:rendered'));
  }

  /* ---------- Lightbox: wheel / pinch zoom, drag pan, keyboard ---------- */
  let lb, canvas, pct, view = { x: 0, y: 0, k: 1 }, natural = { w: 1, h: 1 };
  function ensureLightbox() {
    if (lb) return;
    lb = document.createElement('div');
    lb.className = 'lb'; lb.hidden = true;
    lb.setAttribute('role', 'dialog'); lb.setAttribute('aria-modal', 'true');
    lb.innerHTML = '<div class="lb-bar"><div class="lb-title"></div><div class="lb-tools">' +
      '<button type="button" data-z="out" aria-label="Zoom out">−</button><span class="lb-pct">100%</span>' +
      '<button type="button" data-z="in" aria-label="Zoom in">+</button><button type="button" data-z="fit">Fit</button>' +
      '<button type="button" data-z="close" aria-label="Close">✕</button></div></div>' +
      '<div class="lb-stage"><div class="lb-canvas"></div></div><div class="lb-hint"></div>';
    document.body.appendChild(lb);
    canvas = lb.querySelector('.lb-canvas'); pct = lb.querySelector('.lb-pct');
    const stage = lb.querySelector('.lb-stage');
    lb.querySelector('.lb-tools').addEventListener('click', (e) => {
      const z = e.target.closest('button')?.dataset.z; if (!z) return;
      if (z === 'close') close(); else if (z === 'fit') fit(); else zoomAt(z === 'in' ? 1.25 : 0.8);
    });
    stage.addEventListener('wheel', (e) => {
      e.preventDefault();
      const r = stage.getBoundingClientRect();
      zoomAt(Math.exp(-e.deltaY * (e.ctrlKey ? 0.01 : 0.0018)), e.clientX - r.left, e.clientY - r.top);
    }, { passive: false });
    const pts = new Map(); let last = null, pinch = null;
    stage.addEventListener('pointerdown', (e) => { stage.setPointerCapture(e.pointerId); pts.set(e.pointerId, e); last = e; stage.classList.add('drag'); });
    stage.addEventListener('pointermove', (e) => {
      if (!pts.has(e.pointerId)) return;
      pts.set(e.pointerId, e);
      if (pts.size === 2) {
        const [a, b] = [...pts.values()];
        const d = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
        const r = stage.getBoundingClientRect();
        const cx = (a.clientX + b.clientX) / 2 - r.left, cy = (a.clientY + b.clientY) / 2 - r.top;
        if (pinch) zoomAt(d / pinch, cx, cy);
        pinch = d; return;
      }
      if (last) { view.x += e.clientX - last.clientX; view.y += e.clientY - last.clientY; apply(); }
      last = e;
    });
    const up = (e) => { pts.delete(e.pointerId); pinch = null; last = pts.size ? [...pts.values()][0] : null; if (!pts.size) stage.classList.remove('drag'); };
    stage.addEventListener('pointerup', up); stage.addEventListener('pointercancel', up);
    stage.addEventListener('dblclick', (e) => { const r = stage.getBoundingClientRect(); zoomAt(1.6, e.clientX - r.left, e.clientY - r.top); });
    document.addEventListener('keydown', (e) => {
      if (lb.hidden) return;
      if (e.key === 'Escape') { close(); e.stopPropagation(); }
      else if (e.key === '+' || e.key === '=') zoomAt(1.25);
      else if (e.key === '-') zoomAt(0.8);
      else if (e.key === '0') fit();
    }, true);
  }
  function apply() {
    canvas.style.transform = `translate(${view.x}px,${view.y}px) scale(${view.k})`;
    pct.textContent = Math.round(view.k * 100) + '%';
  }
  function zoomAt(f, cx, cy) {
    const st = lb.querySelector('.lb-stage').getBoundingClientRect();
    if (cx === undefined) { cx = st.width / 2; cy = st.height / 2; }
    const k = Math.min(8, Math.max(0.1, view.k * f)); f = k / view.k;
    view.x = cx - (cx - view.x) * f; view.y = cy - (cy - view.y) * f; view.k = k; apply();
  }
  function fit() {
    const st = lb.querySelector('.lb-stage').getBoundingClientRect();
    const k = Math.min((st.width - 48) / natural.w, (st.height - 48) / natural.h, 2.2);
    view = { k, x: (st.width - natural.w * k) / 2, y: (st.height - natural.h * k) / 2 }; apply();
  }
  let lastFocus = null;
  function open(host, title) {
    const svg = host.querySelector('svg'); if (!svg) return;
    ensureLightbox(); lastFocus = document.activeElement;
    const c = svg.cloneNode(true);
    natural = { w: +host.dataset.w || svg.viewBox.baseVal.width, h: +host.dataset.h || svg.viewBox.baseVal.height };
    c.removeAttribute('style'); c.setAttribute('width', natural.w); c.setAttribute('height', natural.h);
    canvas.innerHTML = ''; canvas.appendChild(c);
    canvas.style.width = natural.w + 'px'; canvas.style.height = natural.h + 'px';
    lb.querySelector('.lb-title').textContent = title || '';
    const zh = document.documentElement.dataset.lang !== 'en';
    lb.querySelector('.lb-hint').textContent = zh ? '滚轮 / 双指缩放 · 拖拽平移 · 双击放大 · 0 适配 · Esc 关闭' : 'Scroll / pinch to zoom · drag to pan · double-click to zoom · 0 to fit · Esc to close';
    lb.hidden = false; document.documentElement.classList.add('lb-open');
    requestAnimationFrame(fit);
    lb.querySelector('[data-z="close"]').focus();
  }
  function close() { lb.hidden = true; document.documentElement.classList.remove('lb-open'); canvas.innerHTML = ''; lastFocus?.focus?.(); }

  window.PiMermaid = { renderAll, open, PALETTE, theme };
})();
