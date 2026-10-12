/* Hand-authored SVG diagrams: hover focus (component + its connections) and click-to-enlarge lightbox with zoom / pan. */
(function () {
  const state = (window.__dg = { done: false, count: 0 });
  function prep(root) {
    (root || document).querySelectorAll('.dg').forEach((host) => {
      const s = host.querySelector('svg.pd'); if (!s) return;
      const vb = s.viewBox.baseVal; host.dataset.w = Math.round(vb.width); host.dataset.h = Math.round(vb.height);
    });
  }
  /* hover: highlight a component, its edges and its direct neighbours */
  let cur = null;
  function clear() { if (!cur) return; cur.classList.remove('focus'); cur.querySelectorAll('.on').forEach((e) => e.classList.remove('on')); cur = null; }
  document.addEventListener('pointerover', (e) => {
    const nd = e.target.closest && e.target.closest('svg.pd .nd[data-id]');
    if (!nd) { if (cur && !(e.target.closest && e.target.closest('svg.pd') === cur)) clear(); else if (cur) clear(); return; }
    const svg = nd.closest('svg.pd'); const id = nd.dataset.id;
    clear(); cur = svg; svg.classList.add('focus'); nd.classList.add('on');
    const near = new Set([id]);
    svg.querySelectorAll('.ed').forEach((ed) => {
      if (ed.dataset.a === id || ed.dataset.b === id) { ed.classList.add('on'); near.add(ed.dataset.a); near.add(ed.dataset.b); }
    });
    svg.querySelectorAll('.nd[data-id]').forEach((n) => { if (near.has(n.dataset.id)) n.classList.add('on'); });
    if (near.size === 1) clear();
  });
  document.addEventListener('pointerleave', clear);

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
    const svg = host.querySelector('svg.pd'); if (!svg) return;
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


  function openHost(host, title) { open(host, title); }
  prep(); state.count = document.querySelectorAll('.dg svg.pd').length;
  document.fonts && document.fonts.ready.then(() => { state.done = true; document.dispatchEvent(new CustomEvent('dg:ready')); });
  if (!document.fonts) state.done = true;
  window.PiDG = { open: openHost, prep };
})();
