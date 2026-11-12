# Fresh canonical NS measured-pose navigation validation

```json
{
  "closed": true,
  "passed": false,
  "version": "v1085",
  "scope": "Fresh canonical t0 NS navigation main plus conditional same-version full repeat, observed development route",
  "attempted": [
    "main_fresh_ns"
  ],
  "unexecuted": [
    "repeat_fresh_ns"
  ],
  "error": {
    "error": "AssertionError('FIRST_FUNCTIONAL_OR_SAFETY_FAILURE')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/rpccr_execution_core/fresh_campaign.py\", line 43, in main\n    out=Path(task['output']);rp=out/'RESULT.json';rp=rp if rp.exists()else out/'physics/paired/ENTRY_FAILURE_RESULT.json';result=json.loads(rp.read_text())if rp.exists()else dict(passed=False,missing_result=True);row=dict(task=task,result=result,returncode=code);rows.append(row);dump(O/'RESULTS.json',rows);assert code==0 and result['passed'],'FIRST_FUNCTIONAL_OR_SAFETY_FAILURE'\nAssertionError: FIRST_FUNCTIONAL_OR_SAFETY_FAILURE\n"
  },
  "complete_repeat": null,
  "counts": {
    "vehicle_initializations": 1,
    "historical_replay_native": 0,
    "new_actual_native": 0,
    "own_replay_native": 0,
    "replay_state_initializations": 0,
    "private_mujoco_native": 0,
    "training_updates": 0,
    "analytical_prediction_native": 0
  },
  "guard_original": true,
  "source_unchanged": true,
  "whole_route_passed": false,
  "new24_executed": false
}
```

This is one observed NS developmental route from canonical t0, not three-route or24 confirmation. Empirical speed envelope is conditional, not global recursive safety.


## Actual zero-step entry failure
Fresh vehicle initialization1, model SHA unchanged, navigation/private/replay integration0. New exact-float t0 pose assertion rejected actual yaw-1.5707963267948963 vs metadata-1.5707963267948966, error2.220446049250313e-16. Full canonical initial-state vector exactly equals the verified V1084 canonical t0, error0. Initial clearance.461486891m/bad contacts0. Original FAILED completion/archive retained; repeat unexecuted. This is an avoidable implementation entry error, not an observed navigation/control failure.

Unique entry relay prepared under experiments/v1085_pose_entry_relay: only one assert uses the original<=1e-8 state-consistency tolerance; all other worker bytes identical. Saved true-t0 positive, three over-tolerance negatives and real isolated NoModel/two-task entry checks passed. Models remain disabled pending explicit approval; original root wall/monotonic deadline unchanged.
