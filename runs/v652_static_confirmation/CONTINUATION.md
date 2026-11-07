# Ongoing Phase static work — continue, do not claim acceptance yet

Canonical repo only. Latest user requests analyze causes and continue until static stable; dynamics require user review after success. No Stage, SAC training, agents, unbounded runs. Read repo AGENTS/RESEARCH_STATUS and V652 protocol.

V650 original confirmation stopped 13 attempts: 11 strict arrivals, 2 HORIZON (93000045 single, 93000074 two). All 82168 replay ticks/public full states matched, min native AABB clearance0.179278m. This failure remains. Evidence static_acceptance_v650_20261031 verified785 manifest files.

V651 rev28 projection rescued two-obstacle case1104steps but cusp bypass audit failed. Final rev29 uses projected path progress/heading, ideal joint-limit-consistent planner center steer0.427221rad (robot wheels limits±0.52; not measured dynamics guarantee), and prevents nearest-index cusp bypass. Same models/normalized initial states: 93000074 two1046steps/minnative0.18106207;93000045 single1027/min0.18544366;91000002 single789/min0.19141759. All final three full auditsPASS. Old91000002 was773steps, so no general efficiency claim. Four development runs total including28 duplicate, not independent confirmation. V651 closure14007.554s of ORIGINAL14400s, before19:45:11; full evidence static_progress_repair_v651_20261031 verified159 manifest files/4branches. No raw deletion because remote unverified.

V652 currently RUNNING under latest user continuation as a separate preregistered single bounded confirmation; never reset oldV650 ledger. Window started2026-10-31T19:40:51.861+08:00; deadline23:40:51.861 (14400s, also no later23:45). timeout wrapperPID55340, masterPID55341. Detached orchestrator experiments/v652_static_confirmation/execute_confirmation.py; console runs/v652_confirmation.console. Do NOT modify any V652 .py or PROTOCOL while running: hashes are asserted before every task.

Fresh seeds94000001–94000360 odd single/even two. Ordered t0 screen; stop at first prefix with12eligible each, lockfirst12perclass before ANYnav; amendment preregistered when fresh preflight/nav both0, equivalent selection to full360. Reference now uses0.427221 steer (different target subset fromV650; no direct population-rate comparison). Truth paths evaluator-only. All online source byte-identical to rev29 except output root.

Gate:24selected>=23strict, each>=11/12; full per-run native replay/control/contact/geometry/source audit,3 repeats of above same-rev29 baseline tasks. Second non-success stops, physical/source/model failure stops. Original failures and unexecuted remain distinct. No automatic new window or dynamics.

Status: python experiments/v649_static_stability/summarize_static_progress.py. V652 files runs/v652_static_confirmation/confirmation_window01/{WINDOW,ACTIVE,LEDGER,SELECTION_FREEZE,CONFIRMATION_RESULTS,REPEAT_AUDIT,COMPLETION}. Replays audited automatically immediately after every navigation/repeat, sequential through run_phase.sh, not new trials. If early stop/complete inspect ERROR/COMPLETION/console.

After completion: run python experiments/v649_static_stability/audit_v652_final.py (independent read-only source/contact/state/selection/repeat gate; pending partial result currently false). Inspect/recompute all checks, do not trust exit code alone. Curate all completed attempts and preflight ledger with existing curate.py + verify_curated.py; scientific plots matplotlib, view_image. New final docs report and outputs symlink, update canonical metadata with pass/fail and user review gate. Commit; bounded push attempt.

GitHub CLI pushes still timeout. Last known remote227c267..., local many commits incl V650/V651 evidence. SYNC_STATUS pendingnetwork. Never delete raw outputs until remote verified. Readiness ./run_phase.sh lastREADY,1235frozenfiles,envinstances0/sim0/train0,Stagehidden; Phase20SHA4072c19e02ba5c7c6b218a268c4ff1d987d2352eada01a3de918854d7173fc9f.

Utilities outside frozen candidate can be edited in V649. Reports docs/STATIC_ACCEPTANCE_REPORT.md (V650 fail), STATIC_REPAIR_REPORT.md (3dev repairs) and docs/figures/static_repair_comparison.png. Newpool report not yet written. Keep Chinese commentary meaningful at least every60s; toolread progress and clock.sleep40–50s while sequential jobs run. Do not end with a fake/partial success; persist through this bounded confirmation then report truth and stop before dynamics.

Local committed HEAD at handoff: f4b56ddfa9769924ded5ee21d37785094b20350a
