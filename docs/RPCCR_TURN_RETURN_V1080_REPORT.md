# V1080 two sequential rounds

Closed; passed=False

```json
{
  "closed": true,
  "passed": false,
  "both_rounds_passed": false,
  "attempted": [
    "turn_left",
    "turn_right",
    "remaining3555"
  ],
  "unexecuted": [],
  "error": {
    "error": "AssertionError('FIRST_ACTUAL_RESPONSE_FAILURE')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1080_turn_return_remaining/driver.py\", line 26, in <module>\n    result=json.loads(result_path.read_text())if result_path.exists()else dict(passed=False,vehicle_initializations=None,new_actual_native=None,own_replay_native=None,missing_result=True);row=dict(task_id=task['task_id'],worker_returncode=code,result=result);rows.append(row);dump(O/'RESULTS.json',rows);assert code==0 and result['passed'],'FIRST_ACTUAL_RESPONSE_FAILURE'\nAssertionError: FIRST_ACTUAL_RESPONSE_FAILURE\n"
  },
  "counts": {
    "vehicle_initializations": 3,
    "new_actual_native": 5226,
    "own_replay_native": 23300,
    "replay_state_initializations": 3,
    "private_mujoco_native": 0,
    "historical_replay_native": 18074,
    "training_updates": 0
  },
  "guard_original": true,
  "source_unchanged": true,
  "whole_route_passed": false,
  "new24_executed": false,
  "saved_NS_remaining_completed": false
}
```

Components and saved-prefix continuation only; no fresh whole-route or24 acceptance. Raw evidence retained pending remote verified archival.

## Saved failure inspection (zero models/integrations)

Round1 left/right both actual and20 saved-audit checks passed: each2605 actual+2605 full replay, moving-return .151455/.151407m at .119470/.119465m/s, front abs<.00060rad; tracking maxima .010330/.010274rad.

Round2 exact18074 historical replay passed, then16 new native steps; first cap breach at total18090: measured longitudinal .13029661576227547>.13m/s, predicted .11983278021131388. Actual final goal distance1.615759883m;3539 original requests unexecuted. No complete actual terminal2200 tail and no goal pass. Whole18090 own replay error0, minimum actual clearance .2792173687m and bad contacts0. An over-speed gate violation remains a failed safety outcome despite no collision. All observed ctrl reconstructed from original signed Adapter with max error 2.220446049250313e-16. Control-vs-prediction wheel command differences are feedback responses, not evidence of a second controller.

Evidence supports a speed-response prediction gap at this saved turn-release transient. Exact physical cause and a successful correction remain unverified. Next preparation should cover this transient with measured speed feedback and prediction uncertainty, preserve .13cap, and recheck full dynamic timing/stop certificate before any separately authorized physical batch. No automatic restart or threshold relaxation.

Counts: new actual5226 (5210 component+16 continuation), historical18074, own replay23300, canonical initializations3; factory internal constructions unknown; private MuJoCo0/training0. REVIEW_PENDING SHA restored and execution lock idle. Necessary raw evidence retained pending remote archival/readback.
