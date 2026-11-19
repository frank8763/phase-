# V1348 check and V1349 next qualification · 2026-11-19

V1348: static main and repeat passed; dynamic remains FUNCTIONAL_FAILURE_SAFE_COMPLETE, not an operation crash. Complete actual/own-replay accounting45800/45800; dynamic27410/27410, error0, physical minimum0.250033m/contact0/complete stop. Goal remaining4.016194m; dynamic repeat unexecuted. Early recovery intervention preserved recorded known-map clearance>=0.243338m and allowed44 outward commands; it did not establish full-goal progress.

The remaining blocker has two parts: slow snapshot searches and loss of useful obstacle observations while stationary/maneuvering.10requests generated only2installed routes; longest causal novel-return gap19.55s. Current search still returns heuristic progress prefixes, not complete goal routes. More waiting or a larger physical window alone does not fix this.

## Completed zero-model qualification

Pure compiled full-footprint distances versus original NumPy equations:134820saved/random geometry queries across2fields; maximum error0,539280threshold comparisons and75constructed boundaries passed. Includes signed overlap, diagonal separation, rotated footprints, workspace, known circles and sensor points. No smaller footprint, missing samples or reduced threshold; compiler uses no fast-math and no floating-point contraction.

|Fixed saved request|Original planner seconds|Compiled distances seconds|Speedup|Path error|
|---|---:|---:|---:|---:|
|1|12.523|4.908|2.55x|0.0|
|4|12.556|4.881|2.57x|0.0|
|8|12.489|4.850|2.57x|0.0|

All3 paths were bit-identical; original NumPy densely revalidated every new path. All remain SAFE_PROGRESS_PREFIX, full-goal proposals0/3. This is software computation evidence only, not real-time or closed-loop arrival evidence.

Conditional recheck against OLD saved causal observations at estimated faster completion (one simsecond per wallsecond) accepted only1/3. This counterfactual uses the old stationary saved trajectory, not a fresh physical rollout; no success claim is inferred. The2.55–2.57x speedup is insufficient by itself. Native search control-flow remains in Python and is the next timing target.

## Bounded next step

1. Keep the valid RPP dynamic failure in its denominator. Do not keep tuning until every baseline succeeds. RP-CCR V1281 exposed24/24 remains unchanged; formal comparisons and mechanism ablations remain the paper priority.
2. Qualify the entire bounded search kernel/heuristic with the same geometry and work ceiling, first seeking substantially shorter planning latency on the same fixed causal requests. Require independent original-geometry readback, explicit search-order/path differences if any, and latest-observation re-admission. Do not just add search seconds.
3. In the SAME saved-input qualification, require complete-goal or explicitly recertifiable continuation behavior. Measure response to the actual no-return intervals; never drop actor occupancy on loss. If the loose causal information cannot certify motion, report a bounded algorithm refusal, not sensor perfection or safety success.
4. Only after these qualifications: freeze one finite candidate and task/budget before any new physical validation. No new physical round was started on this check request. Keep15cm actual/22cm live gates and all native control/state/contact replay unchanged.

Stage access0, model constructions0, native integrations0, training0. Source/binary hashes and fixed inputs are in `runs/v1349_planner_latency_qualification/`. Raw V1348 archive still awaits remote downloadSHA+restore; no cleanup performed.
