# SCCR original control contract: bounded saved-input analysis

V2171 separates three questions: whether complete sensor/policy inputs work (V2170 passed as a log-only component), whether the historical environment is compatible with the common physical plant (it is not), and whether an explicitly adapted controller can navigate that plant (not tested). No new policy inference, renderer, physical model, solver, physics, replay or physical audit was executed. The original120 denominator remains72closed/7whole/48unexecuted; SCCR12slots remain unexecuted.

## Source-exact risk and shield arithmetic

Original V2 sensor point, future-path, distance, corridor-risk, LiDAR-sector and shield functions were extracted by AST without importing historical environments. They received the three saved V2170 measured public packets and already-recorded107/186actor outputs. Source SHA and exact method line ranges are in `runs/v2171_sccr_control_contract_readout/RESULT.json`. Default parameters are conditional source defaults, not a recovered historical run configuration. Original Phase22 dispatch uses V3 and bypasses V2 action injection; no V2 mode transition is claimed here.

| Saved native tick | Corridor risk | Conflicts | Minimum path clearance (m) | Shield |
|---|---:|---:|---:|---|
|0|0|0|0.678614616394043|none|
|5|0|0|0.6771368980407715|none|
|10|0|0|0.6560468673706055|none|

Five fixed shield cases passed: front index0 stop, rear index16 excluded from the front sector, left/right escape direction and all-clear identity. Four malformed/nonfinite/out-of-range/unregistered-truth packet cases were rejected before original functions could sanitize them. A distinct ten-case synthetic risk supplement verified front/left/right positive conflicts, rear/all-clear negatives, independent straight-path distances and invariance under a fixed rigid translation/rotation. These are arithmetic/interface tests, not physical safety acceptance or navigation.

## Residual actions are not vehicle commands

Original Phase14 scales the residual by0.15; source-default Phase9 then adds0.06 times that scaled residual to the Phase6 action, boosts positive speed by1.15 and clips before another inner controller. Under only these explicitly stated defaults, saved three-frame normalized inner inputs are approximately `(0.889866,1)`, `(0.888384,1)`, `(0.886564,1)`. These are neither body v/omega nor issued motor commands. Actual upstream action noise/domain randomization, V3 detour/path changes, inner Pure Pursuit/recovery, rate/steer limits and final wheel/Ackermann conversion were not executed.

A fixed conditional counterexample uses recorded-output-like base `(0.9,0.94)` and a shield-limited residual `(-0.35,-0.15)`: the same source prefixes still return normalized inner speed1. This does not prove the full SCCR controller unsafe; it proves that a shield on the residual cannot substitute for final-command/physical feasibility validation.

## Historical environment changes the plant state

Frozen `mkmini_phase14_phase9_yawsync_fast_nav_env.py` invokes `_phase14_apply_bicycle_yaw_sync` after its parent step. That function directly writes free-joint qpos position/quaternion and qvel linear/angular velocities. The inherited H3 branch also contains post-step yaw/velocity synchronization. Original environment execution would violate the common plant's no state injection contract.

An exact extracted Phase14 function was executed on explicitly synthetic arrays, without MuJoCo or a plant. At steer0.2rad/wheel6rad/s and source-default gains/dt0.02s it moved the synthetic position0.00432m and wrote yaw rate0.16158885687691324rad/s despite zero physical integration steps. This is an executable contract witness, not a simulated vehicle result. Historical SCCR results retain their separate contract and are not retrospectively relabelled.

Native full-environment SCCR is therefore inapplicable to the current common plant as-is. A prospective **controller-only SCCR adaptation on the common plant** must declare the omitted environment state corrections, freeze all remaining control/noise/configuration choices, preserve the original learned policies, and separately qualify complete inner control and actual nonzero command units with unchanged physical safety gates. It must be reported under that adapted identity, never silently as native full SCCR.

## Evidence and disposition

The main saved-frame study and separate positive-risk supplement passed on CPU0/nice19/thread1/GPUhidden. Source/inputs were read only; old V2170 was not rerun, re-audited or altered. New preparation/report files are local after Git468f39f and are not claimed to be in its closed Release. Existing capacity must still be qualified before any future physical initializer. No navigation or whole-goal success is established by this analysis.
