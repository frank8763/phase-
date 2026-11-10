# V999 zero-model bounded search diagnosis

User explicitly requested the next step after V995–V998. This is only a new
zero-model stage, not reopening the closed90minute/20:00 windows. No model
initialization, physical integration, dynamics rollout, navigation or physics
replay; no training/hardware/Stage. Original REVIEW_PENDING and execution lock
remain. Source-only stage<=900seconds, <=60seconds/search.

First reproduce the original V997 second-state failure with the exact frozen
function (1697 expansions/2009 generated under recorded setup). Then compare
exactly4preregistered state-key variants ×2original saved states, fixed5000work,
same5targets/.1m primitives, physical constraints, geometry, clearance reserves,
original goal and fitted coefficients. Only visited-state key resolution varies:
oldxy.05/yaw72; yaw144; xy.025; xy.025/yaw144. No target/phase/seed/threshold fit.
Keep original merge pruning but count distinct continuous poses collapsed to one
key. Distinguish heap exhaustion from work/wall cap. Static full-goal route is not
dynamic qualification. For each found route, independently reconstruct its
existing1.2m recovery-prefix rule and full actor-cycle geometry with original
progress.4 and safety.155 checks. Never turn negative results into impossibility.

Ranked alternatives: (1) quantized state merges prune useful feasible successors;
(2) demanding full-goal static reachability before accepting a local safe-progress
prefix rejects useful recovery segments; (3) the original recovery trigger occurs
after a useful causal window; (4) teacher-forced response fit is not an adequate
causal planning model. Test one variable at a time. Earlier-window review may read
saved actual states and sensor history, never actor truth to select an online
trigger. A nonstopped earlier pose cannot be claimed as an executed stopped
recovery start without an actual full braking trajectory.

Any source-only repair found must retain independent geometry and causal source
checks and does not become an authorized physical controller. No new physical
window in this stage. Preserve every baseline/counterfactual and qualification
failure. Selected evidence goes to same-repo GitHub with all-member SHA readback
before scoped cleanup, cache<=2GiB, one new stage30second push/5second HEAD check;
old sync not retried.
