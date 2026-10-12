(function () {
  const d = document.documentElement;
  const save = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
  const zh = () => d.dataset.lang !== 'en';

  function syncButtons() {
    document.querySelectorAll('[data-set-lang]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.setLang === d.dataset.lang)));
    document.querySelectorAll('[data-i18n-title]').forEach((b) => { const [z, e] = b.dataset.i18nTitle.split('|'); b.title = zh() ? z : e; b.setAttribute('aria-label', b.title); });
    document.title = zh() ? document.body.dataset.titleZh : document.body.dataset.titleEn;
  }
  document.querySelectorAll('[data-set-lang]').forEach((b) => b.addEventListener('click', () => {
    d.dataset.lang = b.dataset.setLang; d.lang = b.dataset.setLang === 'en' ? 'en' : 'zh-CN'; save('pi-lang', d.dataset.lang); syncButtons(); fitDiagrams();
  }));
  document.getElementById('theme-btn').addEventListener('click', async () => {
    d.dataset.theme = d.dataset.theme === 'dark' ? 'light' : 'dark'; save('pi-theme', d.dataset.theme);
  });

  /* mobile TOC drawer */
  const tocBtn = document.getElementById('toc-btn');
  tocBtn.addEventListener('click', () => document.body.classList.toggle('toc-open'));
  document.addEventListener('click', (e) => {
    if (document.body.classList.contains('toc-open') && !e.target.closest('.toc') && !e.target.closest('#toc-btn')) document.body.classList.remove('toc-open');
  });
  document.querySelectorAll('.toc a').forEach((a) => a.addEventListener('click', () => document.body.classList.remove('toc-open')));

  /* scrollspy + reading progress */
  const links = [...document.querySelectorAll('.toc a[href^="#"]')];
  const targets = links.map((a) => document.getElementById(a.getAttribute('href').slice(1))).filter(Boolean);
  const bar = document.querySelector('.progress');
  let ticking = false;
  function spy() {
    ticking = false;
    const y = window.scrollY + 120;
    let cur = targets[0];
    for (const t of targets) if (t.offsetTop <= y) cur = t;
    if (window.innerHeight + window.scrollY >= document.body.scrollHeight - 4) cur = targets[targets.length - 1];
    links.forEach((a) => a.classList.toggle('active', a.getAttribute('href') === '#' + cur.id));
    const h = document.body.scrollHeight - window.innerHeight;
    bar.style.width = (h > 0 ? (window.scrollY / h) * 100 : 0) + '%';
  }
  window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(spy); } }, { passive: true });
  spy();

  /* diagram sizing: keep text legible on narrow screens, scroll instead of shrinking forever */
  function fitDiagrams() {
    document.querySelectorAll('.diagram-body').forEach((body) => {
      const m = body.querySelector('.dg'); const svg = m && m.querySelector('svg.pd'); if (!svg) return;
      const w = +m.dataset.w, cw = body.clientWidth - parseFloat(getComputedStyle(body).paddingLeft) * 2;
      const minScale = window.innerWidth < 700 ? 0.78 : 0.8;
      svg.style.maxWidth = w + 'px';
      if (w * minScale > cw) { svg.style.width = Math.round(w * minScale) + 'px'; svg.style.maxWidth = 'none'; body.classList.add('scrolls'); }
      else { svg.style.width = '100%'; body.classList.remove('scrolls'); }
    });
  }
  let rt; window.addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(fitDiagrams, 120); });

  /* click to enlarge */
  document.querySelectorAll('figure.diagram').forEach((fig) => {
    const open = () => PiDG.open(fig.querySelector('.dg'), fig.querySelector(zh() ? '.cap .zh' : '.cap .en')?.textContent || '');
    fig.querySelector('.expand').addEventListener('click', open);
    let moved = false;
    const body = fig.querySelector('.diagram-body');
    body.addEventListener('pointerdown', () => { moved = false; });
    body.addEventListener('scroll', () => { moved = true; }, { passive: true });
    body.addEventListener('click', () => { if (!moved && !window.getSelection().toString()) open(); });
  });

  syncButtons();
  PiDG.prep(); fitDiagrams();
})();
