# V1082 one guarded saved continuation

Closed; passed=False

```json
{
  "closed": true,
  "passed": false,
  "saved_continuation_passed": false,
  "attempted": [
    "remaining3555"
  ],
  "unexecuted": [],
  "error": {
    "error": "AssertionError('FIRST_ACTUAL_RESPONSE_FAILURE')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1082_guarded_saved_continuation/driver.py\", line 23, in <module>\n    result=json.loads(result_path.read_text())if result_path.exists()else dict(passed=False,vehicle_initializations=None,new_actual_native=None,own_replay_native=None,missing_result=True);row=dict(task_id=task['task_id'],worker_returncode=code,result=result);rows.append(row);dump(O/'RESULTS.json',rows);assert code==0 and result['passed'],'FIRST_ACTUAL_RESPONSE_FAILURE'\nAssertionError: FIRST_ACTUAL_RESPONSE_FAILURE\n"
  },
  "counts": {
    "vehicle_initializations": 1,
    "new_actual_native": 14,
    "own_replay_native": 18088,
    "replay_state_initializations": 1,
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
