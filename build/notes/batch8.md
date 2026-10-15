# batch 8 progress (telemetry / evals)
- figs15.py tel_* | figs16.py ev_* ; deep_telemetry.py / deep_evals.py
- integrate like batch 7 (see notes for batch 7)
- status: started 20:00
[~] figs15: tel_arch tel_model tel_lifecycle tel_contract lint 0
[x] figs15.py 8 tel_* lint 0 (tel_arch tel_model tel_lifecycle tel_contract tel_memory tel_schema tel_typed tel_pi) — visual check pending for last 4
[x] deep_telemetry.py written, file regex ok
[x] telemetry integrated (captions, api_section_telemetry, deck, build_deep), pkgmeta telemetry done; build 30 pages 117 figs
[~] figs16: ev_arch ev_suites ev_pipeline ev_plan lint
[x] figs16: ev_docker lint 0, ev_suites/ev_plan tightened
[x] figs16: ev_docker ev_sandbox ev_harness lint 0, viewed
[x] figs16: ev_report done (report_example reimpl), 8/8 ev_* lint 0
[x] deep_evals.py written (8 sections)
[~] build.py: evals integrated (caption, api_section_evals, deck, build_deep); pkgmeta evals done
[x] build clean: 31 pages, 125 figs (evals integrated)
[x] tests lead fixed (static counts), vitest.*config excluded from tests_of
[x] hub lead, roadmap (plan complete), site changelog batch 8
[x] PLAN.md + README.md updated
[~] shoot2 r11-new started
[x] r11-new: RUNS 48, 0 failures, 0 broken; [~] full r11 started
[~] fixed export-path count for private evals (0); full r11 restarted
[~] ev-suites/ev-report layer → infra; full r11 restarted (3rd)
