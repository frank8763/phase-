# Proposed V953 stop-then-align physical component qualification

New V952 source after the user's next-step instruction. Old V950/V951 failed
and closed; their window and output exception remain unchanged. No model starts
until the user approves this new independent90-minute component window.

Single frozen candidate: original moving/braking adapter unchanged, only measured
stopped-body10tick gate before zero-drive steering alignment. Original vehicle,
19static entities, actor/sensor/model/noise and all safety gates unchanged.
18original V909 response cases in the original order, all new true t0 runs,
200warm+20requested+200brake each. No substitute/retry. Only if all18 pass, one
predeclared platform handoff:200forward left-curved [.1,+.0758770385],200zero,
then1200straight [.1,0],200zero. The left curve points away from the known
lower-left static circle; this is a new fixed component input chosen before any
model result, not a changed map or route-success sample. No reverse request.

Handoff requires measured body speed/yaw<=.03 and actual steering position<=.01rad,
rate<=.03rad/s before the straight command; complete12s reference error<=.04m/
.035rad, actual forward progress>=1m. Original response limits remain .02aligned/
zero or.04direction reversal, angle.035, half-second stopped body.03, native body
speed.13/yaw.16, clearance>=.15, bad contacts0, complete self containment, actuator
limits/rates, fixed static geometry, no root rewrite, own full qpos/qvel/ctrl/mocap
replay<=1e-8. Parent independently verifies phase history and output receipts.

Maximum19model attempts/9360actual+9360own replay/private0/navigation0. Response
child60s, handoff90s, outer70/100s; all tighter than the ONE absolute90-minute
deadline locked before first model initialization. First functional/safety/source/
state/control/evidence/interface failure closes the whole batch. No frozen patch,
entry exception, replacement, extra branch or extension. All integration only
run_phase.sh singleCPU/exclusive model lock. Original REVIEW_PENDING restored.

The already demonstrated factory write protection remains enabled. Child result
files stay inside the case directory. Parent receives/cross-checks a full stdout
result and stores the operation ledger outside the child. The actual write_guard
function and whole worker-to-parent metadata exchange are qualified with model
imports blocked before freezing; no exception is reserved for an output bug.

No automatic full static/dynamic route, new24, comparison, training/SAC or real
robot follows a component pass. Actual raw temporary cap2GiB; necessary evidence
to the same-repo Release with downloaded asset/member SHA before cache cleanup.
One new-stage source push<=30s+remoteHEAD<=5s; old synchronization not retried.
