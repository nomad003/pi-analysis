# 图解 Pi Agent · Pi Agent, Illustrated

A static, bilingual (zh/EN) site and slide decks that walk through the architecture of
[earendil-works/pi](https://github.com/earendil-works/pi). It is an **analysis of Pi v1.1.0**: every
fact and link is computed from the source at the release tag `v1.1.0`.

- Output: `/workspace/pi-site/` (open `index.html`; it works offline over `file://`). The zip is `/workspace/pi-site.zip`.
- Plan, information architecture and package status: [PLAN.md](PLAN.md). The rendered version is `roadmap/index.html`.
- Build: `python3 build.py`. Verify: `python3 shoot2.py <shots-dir>`.

| file | role |
|---|---|
| `build.py` | multi-page generator: facts and assertions, chrome (top bar, package switcher, breadcrumbs), all pages and decks, font subsetting |
| `content.py` | the 12 first-edition sections (now spread over the hub and package pages) |
| `deep_agent.py`, `deep_ai.py` | agent-core and pi-ai deep-dive content |
| `pkgmeta.py` | package registry: status, grouping, template; the facts come from package.json |
| `svgkit.py`, `figkit.py` | diagram toolkit, plus a strict lint for overlaps, crossings and overflow |
| `figs.py`, `figs2.py` | first-edition diagrams |
| `figs3.py`, `figs4.py` | agent-core and pi-ai diagrams |
| `slides.py` | deck renderer, used for the main deck and the per-package decks |
| `shoot2.py` | link check plus a headless Chromium matrix (light/dark × 1440/1920/390 × zh/EN) |
| `preview.py` | renders single diagrams |
