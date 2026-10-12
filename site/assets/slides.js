(function () {
  const d = document.documentElement;
  const slides = [...document.querySelectorAll('.slide')];
  const N = slides.length, stage = document.getElementById('stage');
  const save = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
  const zh = () => d.dataset.lang !== 'en';
  let cur = 0;

  function fit() {
    const pad = window.innerWidth < 700 ? 8 : 28;
    const s = Math.min((window.innerWidth - pad * 2) / 1600, (window.innerHeight - pad * 2 - (window.innerWidth < 700 ? 0 : 40)) / 900);
    stage.style.transform = `translate(-50%,-50%) scale(${s})`;
  }
  function go(i, fromHash) {
    cur = Math.max(0, Math.min(N - 1, i));
    slides.forEach((s, j) => { s.classList.toggle('on', j === cur); s.classList.toggle('before', j < cur); s.setAttribute('aria-hidden', String(j !== cur)); });
    document.getElementById('cur').textContent = cur + 1;
    document.getElementById('prog').style.width = ((cur + 1) / N) * 100 + '%';
    document.querySelectorAll('.ov-grid button').forEach((b) => b.classList.toggle('cur', +b.dataset.go === cur + 1));
    if (!fromHash) history.replaceState(null, '', '#' + (cur + 1));
  }
  const next = () => go(cur + 1), prev = () => go(cur - 1);
  function syncText() {
    document.querySelectorAll('[data-i18n-title]').forEach((b) => { const [z, e] = b.dataset.i18nTitle.split('|'); b.title = zh() ? z : e; b.setAttribute('aria-label', b.title); });
    document.title = zh() ? document.body.dataset.titleZh : document.body.dataset.titleEn;
  }
  async function toggleTheme() { d.dataset.theme = d.dataset.theme === 'dark' ? 'light' : 'dark'; save('pi-theme', d.dataset.theme); }
  function toggleLang() { d.dataset.lang = zh() ? 'en' : 'zh'; d.lang = zh() ? 'zh-CN' : 'en'; save('pi-lang', d.dataset.lang); syncText(); }
  function fullscreen() { if (document.fullscreenElement) document.exitFullscreen(); else d.requestFullscreen?.().catch(() => {}); }
  const ov = document.getElementById('overview');
  const toggleOv = (show) => { ov.hidden = show === undefined ? !ov.hidden : !show; };

  document.addEventListener('keydown', (e) => {
    if (document.querySelector('.lb:not([hidden])')) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const k = e.key;
    if (!ov.hidden && (k === 'Escape' || k === 'o' || k === 'O')) { toggleOv(false); return; }
    if (['ArrowRight', 'ArrowDown', 'PageDown', ' ', 'Enter', 'j'].includes(k)) { e.preventDefault(); next(); }
    else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace', 'h', 'k'].includes(k)) { e.preventDefault(); prev(); }
    else if (k === 'Home') go(0);
    else if (k === 'End') go(N - 1);
    else if (k === 'f' || k === 'F') fullscreen();
    else if (k === 'o' || k === 'O') toggleOv();
    else if (k === 't' || k === 'T') toggleTheme();
    else if (k === 'l' || k === 'L') toggleLang();
  });
  document.getElementById('next').onclick = next;
  document.getElementById('prev').onclick = prev;
  document.getElementById('fs').onclick = fullscreen;
  document.getElementById('th').onclick = toggleTheme;
  document.getElementById('lg').onclick = toggleLang;
  document.getElementById('ov').onclick = () => toggleOv();
  document.getElementById('ov-x').onclick = () => toggleOv(false);
  ov.addEventListener('click', (e) => { const b = e.target.closest('[data-go]'); if (b) { go(+b.dataset.go - 1); toggleOv(false); } else if (e.target === ov) toggleOv(false); });
  document.querySelectorAll('.dia').forEach((el) => el.addEventListener('click', () => {
    const h2 = el.closest('.slide').querySelector('h2 .' + (zh() ? 'zh' : 'en'));
    PiDG.open(el.querySelector('.dg'), h2 ? h2.textContent : '');
  }));
  // swipe
  let sx = null, sy = 0;
  document.addEventListener('touchstart', (e) => { if (e.touches.length === 1) { sx = e.touches[0].clientX; sy = e.touches[0].clientY; } }, { passive: true });
  document.addEventListener('touchend', (e) => {
    if (sx === null || document.querySelector('.lb:not([hidden])')) return;
    const dx = e.changedTouches[0].clientX - sx, dy = e.changedTouches[0].clientY - sy; sx = null;
    if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) (dx < 0 ? next : prev)();
  }, { passive: true });
  // idle HUD
  let idle; const wake = () => { document.body.classList.remove('idle'); clearTimeout(idle); idle = setTimeout(() => document.body.classList.add('idle'), 2600); };
  ['mousemove', 'keydown', 'touchstart'].forEach((ev) => document.addEventListener(ev, wake, { passive: true }));
  window.addEventListener('resize', fit);
  window.addEventListener('hashchange', () => go((parseInt(location.hash.slice(1), 10) || 1) - 1, true));
  fit(); syncText(); wake();
  go((parseInt(location.hash.slice(1), 10) || 1) - 1, true);
  PiDG.prep();
})();
