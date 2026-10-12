/* Runs in <head> before paint: theme + language from ?query, localStorage, then system. */
(function () {
  var q = new URLSearchParams(location.search), d = document.documentElement, ls = {};
  try { ls = window.localStorage || {}; } catch (e) {}
  var t = q.get('theme') || ls['pi-theme'] || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  var l = q.get('lang') || ls['pi-lang'] || 'zh';
  if (d.dataset.defaultTheme && !q.get('theme') && !ls['pi-theme']) t = d.dataset.defaultTheme;
  d.dataset.theme = t === 'dark' ? 'dark' : 'light';
  d.dataset.lang = l === 'en' ? 'en' : 'zh';
  d.lang = d.dataset.lang === 'en' ? 'en' : 'zh-CN';
})();
