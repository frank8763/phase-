# V1356 afternoon: bounded observation uncertainty and original WE recovery

User authorized “检查，然后准备到下午五点的实验；多思考分析，合理安排”.
New separate round: absolute model/native deadline2026-11-19 17:00:00+0800,
locked wall+monotonic before first model, never extends V1354 or older windows.
2GiB temporary total, CPU2 single native instance, CPU3–5 ROS/planning,
nice19, math threads1, OSMesa, GPU hidden. No Stage access/training/hardware.

V1354 finished four navigations: RPP static main/repeat pass, RPP dynamic and
MPPI static safe complete nonarrival; all full own replays and applicable safety
gates pass. These failures remain valid, not retried or reclassified. No more
MPPI tuning in this batch. V1355 reproduced lost-observation start refusal using
only last point/time, request time and actual body:20.35s gap →2.088m ball →
.0812m predicted clearance despite safe physical trajectory. Speed-only
uncertainty growth was correctly conservative for its weaker assumptions.

## Three fixed scientific candidates, frozen before any new vehicle

All use engineering RPP, the same original WE seed10060001 and phase
1.5107128341898335, unchanged plant/map19statics/actor/sensor/goal and safety
contracts, same causal observations and original command timestamp/expiry,
exact footprint/live.22/native.15/gear/cusp/tracking reserve and full own
qpos/qvel/ctrl/mocap/contact replay<=1e-8. No actor truth/anchor/axis/phase online.

1. `excursion_mode0`: public bounded.25m displacement around an unknown fixed
anchor implies <=.50m displacement between any center observations. Keep
original.24m observation-center uncertainty +.10 actor radius, replace only
speed displacement by min(.08*(age+1.5),.50). Original compiled mode0 search.
2. `periodic_mode0`: additionally condition existing public.32rad/s sinusoidal
class using the existing V1037 coefficient outer polytopes. Only qualifying
novel real-return point +.24m directional supports clip the unknown coefficients.
Exact continuous1.5s swept support → conservative enclosing disk. Choose the
smaller of two independently valid disks. Same mode0 search. This is a stronger
declared prior than V1354 and candidate1, not a free improvement for arbitrary
unknown-motion actors. Prior inconsistency stops, no reset/fallback repair.
3. `periodic_mode1`: identical candidate2 predictor, use already-qualified
obstacle-guided body-goal search mode1, retaining original.45m arrival and.32m
inner nominal target set. No goal moved, no guard lowered, no added work budget.

These are development/ablation candidates; task already exposed, no unseen
generalization or algorithm-superiority claim. Mode2 was examined only in
zero-model saved-state diagnosis; not registered for physical execution.

## Qualification and bounded relay

Before model: original saved request1, failed4 and11 sensor-only reconstruction;
each returned candidate path independently dense checked at original guard;
positive forward/reverse empty-field planner capability; frozen actual CLI
worker and installed RPP single-gear actions using the new paths; changed
causality, no-truth/malformed inputs, predictor bound containment and stale/future
command tests. Separately, evaluator-only checks all saved horizon samples
against actor truth; evaluator state never an input to the predictor. Verify
new prior matches declared class and analytic triangle/support bounds. Original
complete native/ROS/output guard/backend entry qualification is mandatory.

RPP static main/repeat from V1354 are reused only after exact physical
controller/map/reference/entry/control closure and static code-path equivalence
is recorded. These are0 new static samples; no MPPI static qualification reused.
No generic “software passed therefore skip static” inference. Change only
dynamic predictor, dynamic worker mode and its audit; both are unreachable on
static branch. Actual initial canonical vehicle is constructed anew per task.

Order: each candidate original WE dynamic main → if all functional/safety/
evidence gates pass, its full same-task repeat, then next fixed candidate.
Maximum6 new navigations, no replacements, no auto slots9/17/24. A complete
safe functional failure skips its repeat and continues the next preregistered
candidate. Any safety/control/source/model/truth/evidence/infrastructure anomaly
stops the entire batch. No source edits or auto repair after final freeze.
Per navigation same1200s soft/1500s hard/1600s supervisor,59800 native,
12 replans/4000 wait native, full200 stop tail and complete own replay. Reserve
root time for stop/evidence/replay; no child past root. No repeat-for-filling-time.

Offline closure records all6planned/unexecuted/repeats/actual/private/replay
counts, source and every member SHA,32MiB lossless archive blocks and readback,
REVIEW_PENDING restored/lock idle. Count native/raw only this round; reserve
archiving space by stopping live growth at614MiB within2GiB. Keep raw until
GitHub upload/download/member/restore verification; no deletion while running.
One bounded30s push+5s read-only verification for this new round, no retry of
V1354's failed sync. Network failure cannot restart or extend experiments.
