# V1359 same-gear restart: component first, then pending swept dynamic

User asks to check, analyze and accelerate the experiment. V1358 stopped at its
first control anomaly; original unknown-inflight accounting, error and archives
remain unchanged. New finite repair round keeps absolute17:00+0800/1795078800
deadline,2GiB,CPU2 single native lock/ROS-planning3–5,lowpriority/maththreads1,
OSMesa/GPUhidden,Stageisolated. No new training/hardware/tasks/seed/scene/24.

Saved tick23760: rear targets exactly0, measured body velocity-.006968m/s,
requested reverse-.07877m/s, old interlock gear already-1. It passed because
there was no sign change; unchanged signed allocator correctly rejected reverse
entry from zero rear targets while not actually stopped. Real old gate and
actual unchanged signed allocator reproduce this with zero-model saved data.

Only repair: when a fresh reverse request has zero drive targets and
abs(measured longitudinal speed)>.003, enter the EXISTING200-native zero hold,
requiring body<=.003,drivezero<=1e-10,steering-jointvelocity<=.03 before passing
the current fresh request. No allocator,plant,cmdtimestamp,steering,actuator,
model,state/groundtruth or safety threshold changes. Do not remove lower guard.
Both positive/negative residual body motion is refused; stationary initial
commands and all18385saved forward-static commands remain unchanged.

To shorten turnaround, first fixed physical component original staticWE t0:
200steps reverse-.08→zero commands only until rear targets first reach0
(max100steps)→fresh reverse-.08 for300steps→200-step complete stop.
The zero-target handoff MUST occur while abs(bodyv)>.003, so this is an actual
physical reproduction rather than a stationary synthetic case. Require same
gear restart held>=200, released at full measured rest, then actual reverse
motion>=.02m/bodyv<-.02. All original native/contact/ctrl/rate/self/.15 and full
own replay gates plus independent allocator/gear reconstruction mandatory.
Component main succeeds before complete component repeat; if not, whole batch
stops. Exactly2 component trials, not goal-navigation successes or independent
scene samples. Every canonical initialization and integration separately counted.

Only after both component audits pass run the already-frozen V1358
NESTED_SWEEP/bodygoal/nondecreasing-reserve originalWE dynamic main then its
full success-only repeat. Horizon candidate is not rerun. Max2 new navigations,
max4 physical tasks total. Original sensor/map19/actor.20 amplitude.25 speed.08,
seed10060001/phase1.5107128341898335/start(-4,-2)/goal(4,-2) stay unchanged.
No new algorithm tuning,12plans/4000wait and original nav/stop/replay limits.
All-future periodic prior remains explicitly restricted; no broad robustness.

First safety/control/source/model/truth/evidence/infrastructure anomaly stops;
functional component failure stops; dynamic failure skips repeat and closes.
No frozen repair/relaunch. Before model: saved failure red/green with actual
allocator, strict bothsign/boundary checks, all old static commands, existing
exact search/predictor/installed-controller receipts by dependencySHA, proposed
outputguard/backend/fullcomponent/native/ROS entry. Offline complete reports,
counts exact/unknown,archive/memberSHA/32MiB blocks/readback/REVIEW_PENDING.
One new-round bounded push30s+read-only5s, no old sync retry; raw only removed
after remote downloaded/member/restore verification. Do not run failures to
fill time. CPU/GPU changes require measured benefit, not utilization targets.
