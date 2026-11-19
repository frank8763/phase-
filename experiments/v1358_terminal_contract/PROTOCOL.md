# V1358 terminal body goal and recoverable dynamic occupancy

User “下一步开始” authorizes this bounded revision after V1357 closed.
Absolute native/model deadline remains2026-11-19 17:00+0800/1795078800;
no old experiment/result is reopened. This is exposed WE engineering development.
No new seed/map/actor/goal, independent confirmation, automatic24, training,
hardware, Stage access or GPU migration.

## Reproduced failures and changes

1. Fixed saved mode0 plan10 labelled GLOBAL_GOAL_PATH but terminal body center
was.770157m from goal. New compiled search evaluates actual body center against
the original goal for ALL modes and labels complete only within.32m nominal
acceptance region. Original physical arrival remains.45m. Keep22000 expansions,
1.5s kernel bound, original7steers/gears/primitives/costs and dense geometry.
Physical candidates use mode1; no reliance on false legacy mode0 goal labels.
2. Fixed actual near-wall request19650 was refused even though its current
.244918m clearance never decreased over.5s and increased slightly. Replace
the extra +.002m progress requirement with nondecreasing full-footprint geometry
at the SAME.22m recovery floor. Keep.245m early intervention for all consuming
commands. This is explicitly an empirical geometric monitor, not a universal
physical stopping/tracking proof. Original native.15/contact/self/ctrl/rate and
completeownreplay1e-8 gates remain; never lower them to accept nominal plans.
3. Two preregistered candidates: `horizon_terminal` keeps the existing PERIODIC
1.5s forecast; `sweep_terminal` uses an all-future enclosing disk under the
already-declared.25m fixed-anchor amplitude/.32 frequency class. A real point
return implies center uncertainty.24 plus maximum center displacement.50;
existing coefficient polytopes also give continuous full-period swept x/y
supports. Each disk includes actor radius.10. Install a new all-future disk
only if contained in the old disk. Thus an installed field cannot expand into
the path merely because1.5s elapses. The tradeoff is conservatism: old saved
late poses already inside this field are correctly refused, not falsely
rescued. New candidate activates before first dynamic plan from a safe pose.

Both forecasts use only measured32rays/body/time and declared motion prior;
unknown anchor/axis/phase/actor truth never enters controller/planner. No
arbitrary-motion robustness or unseen/generalization/superiority claim.

## Readiness and tasks

Zero-model: exact old red signals, new terminal label/body tests, signed geometry
of newly compiled binary against original NumPy, forward/reverse/mirror/turn
positive cases, unsafe/malformed negatives, saved tail/main1 paths and actual
worker CLI. Inspect all returned paths with original dense.22 geometry and
constant-gear installed RPP calls. Separately evaluate saved horizon disks and
full-period invariant disks against evaluator-only actor truth, sample every
time/disk and analytically verify nested-disk containment. Late inside-sweep
saved failures remain explicit negative fixtures. No false whole-goal claim
for a progress prefix or a refused historical state.

Unchanged V1357 native/strict200ms/zero expiry/ROS cooperative evidence, controller
parameters/publicmap/staticreference/gear/segment sources and tasks are checked
by exact SHA; static main/repeat reused as0new samples because changed search,
tracking monitor and occupancy only execute on the dynamic branch. Complete new
native/ROS entry/output/backend/source checks remain mandatory before models.

Order horizon_terminal originalWE dynamic main→success full repeat, then
sweep_terminal main→success full repeat; maximum4 new navigations. Safe complete
functional failure skips repeat and continues the other frozen candidate;
first safety/control/source/model/groundtruth/evidence/infrastructure anomaly
stops batch. No runtime source repair or extra work-budget search. Each original
WE start(-4,-2)/goal(4,-2)/seed10060001/phase1.5107128341898335. Native physics,
actual sensor and noise/dropout, original19static and.20actor/.25amplitude/.08
speed unchanged. Same12replans/4000wait/59800native,1200ssoft/1500hard/1600outer,
full200stop and ownreplay. No child beyond root; remaining reserve enforced.

2GiB total this round, live614MiB archive reserve, CPU2 one execution lock,
ROS/planner3–5, nice19/maththreads1/OSMesa/GPUhidden. Offline full denominator,
exact/unknown integration and repeat accounting, independent source/member SHA
and32MiB lossless blocks/readback, REVIEW_PENDING restored. Remote downloaded
SHA/restore before deleting raw. One new-round30s push+5s readonly check, no
retry of old syncs. Completed tasks end early; no repetition to fill time.
