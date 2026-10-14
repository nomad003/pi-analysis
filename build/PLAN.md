# 图解 Pi Agent · Pi Agent, Illustrated — site plan

Analysis of **Pi v1.1.0**: the source under analysis is the release tag
[`v1.1.0`](https://github.com/earendil-works/pi/releases/tag/v1.1.0) (`abe508e`, 2026-10-07).
Every number, diagram and GitHub line link is computed from `/workspace/pi-src` checked out at that tag.
`build.py` refuses to build if HEAD isn't the tag, if any package.json version isn't `1.1.0`,
or if any of the 12 core counts drifts.

*Version semantics:* `v1.1.0` is the **Pi source version**, not a version of this site. The earlier
site edition analysed the development commit `4130bd5` (dated 2026-10-10). Re-verified at the tag:
all 12 core counts are unchanged (42 providers, 10 chat APIs, 41 extension events, 33 RPC commands,
8 tools, 12 stream events, 11 session entry types, 4 modes, 14 packages). `pi-agent-core` source is
identical. `pi-ai` differs in `types.ts` (compat settings are plain TS interfaces at the tag; `compat-schema.ts` /
`model-schema.ts` don't exist yet) and the Mistral transport. One first-edition file link was retargeted:
`settings-defaults.ts` doesn't exist at the tag, so `DEFAULT_COMPACTION_SETTINGS` in `compaction.ts` is used instead.

## Information architecture

```
/index.html                     overview hub: hero, 14 package cards, 4 big-picture sections, repo stats
/packages/<slug>/index.html     one page per package (14), same template
/packages/agent-core/slides.html  per-package deck
/packages/pi-ai/slides.html       per-package deck
/roadmap/index.html             this plan + the Pi 1.1.0 changelog + the changes in this site edition
/slides.html                    main 20-slide deck
/assets/                        css, js, subset fonts, stats.json, pages.json
```

Shared chrome on every page:
- the top bar (brand `图解 Pi Agent` + `v1.1.0` badge, a **package switcher** dropdown with status dots that is also visible on mobile, Overview, Roadmap, Slides, language, theme, GitHub at the tag)
- breadcrumbs on sub-pages
- a per-page TOC with scrollspy (a drawer on mobile)
- a footer naming the tag

Old first-edition anchors (`index.html#loop`, …) redirect to their new homes.

## Packages and status

Statuses:
- **done**: full deep dive.
- **partial**: hosts the moved first-edition sections plus generated reference; the deep dive is planned.
- **planned**: a generated placeholder with package.json facts, export paths, largest files, tests, the 1.1.0 changelog link and the template checklist. Every link stays valid.

| page | npm | dir | status | internal deps | role |
|---|---|---|---|---|---|
| [agent-core](../pi-site/packages/agent-core/index.html) | `@earendil-works/pi-agent-core` | `packages/agent` | **done** | pi-ai | General-purpose agent with transport abstraction, state management, and attachment support |
| [pi-ai](../pi-site/packages/pi-ai/index.html) | `@earendil-works/pi-ai` | `packages/ai` | **done** | telemetry | Unified LLM API with automatic model discovery and provider configuration |
| [coding-agent](../pi-site/packages/coding-agent/index.html) | `@earendil-works/pi-coding-agent` | `packages/coding-agent` | **done** | chord, agent-core, pi-ai, codemode, mcp, tui | Coding agent CLI with read, bash, edit, write tools and session management |
| [tui](../pi-site/packages/tui/index.html) | `@earendil-works/pi-tui` | `packages/tui` | **done** | — | Terminal User Interface library with differential rendering for efficient text-based applications |
| [mcp](../pi-site/packages/mcp/index.html) | `@earendil-works/pi-mcp` | `packages/mcp` | **done** | — | Standalone Model Context Protocol client for pi and other applications |
| [codemode](../pi-site/packages/codemode/index.html) | `@earendil-works/pi-codemode` | `packages/codemode` | **done** | — | Sandboxed JavaScript execution where the only capability is calling injected tools |
| [telemetry](../pi-site/packages/telemetry/index.html) | `@earendil-works/pi-telemetry` | `packages/telemetry` | **planned** | — | Vendor-neutral telemetry contracts and typed schema utilities for pi |
| [chord](../pi-site/packages/chord/index.html) | `@earendil-works/chord` | `packages/chord` | **planned** | — | Application composition runtime for services, replicated state, RPC, and plugins |
| [durable](../pi-site/packages/durable/index.html) | `@earendil-works/pi-durable` | `packages/durable` | **planned** | chord, pi-ai | Durable conversation, task, and document runtime for Pi |
| [env](../pi-site/packages/env/index.html) | `@earendil-works/pi-env` | `packages/env` | **planned** | chord, durable | Remote execution environments for Pi Durable: a small daemon deployed over SSH and its ExecutionEnv client |
| [protocol](../pi-site/packages/protocol/index.html) | `@earendil-works/pi-protocol` | `packages/protocol` | **planned** | chord | Transport-neutral CBOR protocol for remote pi sessions |
| [client](../pi-site/packages/client/index.html) | `@earendil-works/pi-client` | `packages/client` | **planned** | chord, protocol | Transport-neutral client for remote pi sessions over framed CBOR bytes |
| [server](../pi-site/packages/server/index.html) | `@earendil-works/pi-server` | `packages/server` | **planned** | chord, protocol | experimental server package for pi |
| [evals](../pi-site/packages/evals/index.html) | `@earendil-works/pi-evals` | `packages/evals` | **planned** | — | Private package: evaluation suites (dockerised tasks) |

## Per-package template

1. **Overview** — role, deps, size, one-line takeaway
2. **Public API** — export paths and exported symbols (line-linked)
3. **Internal architecture** — structure between modules and files
4. **Key flows** — sequences, state machines, data flow
5. **Data types** — core interfaces and how they relate
6. **Extension points** — where a host can plug in or replace behaviour
7. **Key files** — links to exact lines at v1.1.0
8. **Tests** — test files and case counts
9. **Cross-links** — related packages and sections

## First edition → this edition

| first-edition section | now on |
|---|---|
| packages, layers, sequence, classes | overview hub |
| loop, toolexec | packages/agent-core |
| providers | packages/pi-ai |
| session, compaction, extensions, modes | packages/coding-agent |
| tui | packages/tui |

Every first-edition diagram is kept. There are 12 first-edition diagrams and 49 new ones (16 for agent-core/pi-ai, 17 for coding-agent/tui, 16 for mcp/codemode), 61 in total.

## New diagrams

- **agent-core** (`figs3.py`):
  - `ac_arch`: modules and the pi-ai surface
  - `ac_state`: run state machine and guards
  - `ac_turn`: hook call order sequence
  - `ac_events`: event nesting, the reducer and the pi-ai mapping
  - `ac_queues`: steering and follow-up
  - `ac_parallel`: tool batch timelines
  - `ac_proxy`: StreamFn resolution and streamProxy
  - `ac_types`: UML of the types
- **pi-ai** (`figs4.py`):
  - `ai_entry`: entry points and lazy loading
  - `ai_registry`: Models, Provider and refresh
  - `ai_pipeline`: streamSimple end to end
  - `ai_events`: event grammar and EventStream
  - `ai_convert`: transformMessages
  - `ai_anthropic`: SSE to events
  - `ai_budget`: thinking, maxTokens and cost
  - `ai_oneshot`: images and classifiers
- **coding-agent** (`figs5.py`):
  - `ca_arch`: entry points, core/ modules with line counts, dependencies
  - `ca_startup`: the 14 steps of main() and mode dispatch
  - `ca_session`: what AgentSession installs into each Agent hook; the post-run loop
  - `ca_runtime`: AgentSessionRuntime session replacement and cancel branch
  - `ca_tools`: the 8 built-in tools, truncation limits, Operations
  - `ca_jsonl`: session file location, sample lines, entry types, write/read paths
  - `ca_extapi`: ExtensionAPI method groups, the 41 events (18 interceptable), ctx surfaces
  - `ca_rpc`: stdin/stdout message kinds and the 33 RPC commands
  - `ca_config`: settings merge + trust, ResourceLoader.reload(), system prompt sections
- **tui** (`figs6.py`):
  - `tui_arch`: four module groups and components/
  - `tui_component`: Component/Focusable/Container/TUI, example tree, per-frame contract
  - `tui_render`: render scheduling, frame prep, TuiMainScreen's seven checks
  - `tui_screens`: regular vs fullscreen, the alt-screen frame pipeline
  - `tui_input`: stdin → StdinBuffer → handleTerminalInput (8 steps) → keys/keybindings
  - `tui_editor`: Editor state, handleInput order, autocomplete
  - `tui_overlay`: OverlayOptions, 9 anchors, compositing, focus stack
  - `tui_terminal`: start-up negotiation, OSC outputs, capability table
- **mcp** (`figs7.py`):
  - `mcp_arch`: three module groups, the three import paths, coding-agent's extensions/mcp
  - `mcp_lifecycle`: connection state machine, initialize handshake, Client/ServerCapabilities
  - `mcp_requests`: pending-request bookkeeping, 30 s timeout and cancel, server→client requests, paging
  - `mcp_stdio`: spawn, newline framing and limits, the staged close (0 / 500 / 2,500 ms)
  - `mcp_http`: headers, the three POST responses, error mapping, SSE reconnect back-off
  - `mcp_oauth`: triggers, the six-step flow, recovery, loopback callback server, provider state
  - `mcp_content`: toLlmContent mapping, error classes, JSON-RPC codes
  - `mcp_pi`: config sources, runtime, tool naming (64-char limit), the four exposures
- **codemode** (`figs8.py`):
  - `cm_arch`: host / in-sandbox / model-facing modules, four import paths
  - `cm_sandbox`: host thread, per-run worker, QuickJS VM, the shared interrupt flag
  - `cm_exec`: one execute() and its five endings
  - `cm_bridge`: one tool call's round trip (VM → worker → host → back)
  - `cm_prelude`: the script API, hard limits, lockdown, reserved names
  - `cm_types`: public types and the `// @options:` source format
  - `cm_decl`: JSON Schema → TypeScript declarations, with a worked example
  - `cm_pi`: the codemode tool in coding-agent: nested calls, globals, store entries, modes

Decks: diagrams with height/width ≥ 0.6 (tui_render, ca_session, ca_jsonl, …) use the `side` layout (two points beside the diagram) instead of `wide`, so they render at roughly 0.9× instead of 0.7×.

## Next batches

Done: agent-core, pi-ai (batches 1–2), coding-agent, tui (batches 3–4), mcp, codemode (batch 5).

6. chord, durable, env  ← next
7. protocol, client, server, telemetry, evals

To promote a package, add `deep_<pkg>.py` (same schema as `deep_agent.py`) and `figsN.py`, then set the status in `pkgmeta.py`.

## Build and verify

```
python3 build.py                          # → /workspace/pi-site (asserts tag, versions, facts, diagram lint)
python3 shoot2.py /workspace/pi-shots/rN  # link check + Chromium matrix + screenshots
python3 preview.py /tmp/dg ac_arch,ai_entry   # iterate on single diagrams
```

The upstream `main` branch was not pulled. It has moved past the tag, and it also removes the `client`, `protocol` and `server` packages.
