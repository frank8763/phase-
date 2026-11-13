# V1114 coupled steering component: PASSED

Both registered static NS directions physically completed:2200 initial hold,600 first full steering,2200 hold,600 full opposite steering,300 forward restart,2200 actual final stop. Total16200 actual plus16200 exact own replay; two canonical vehicle initializations, two replay-data initializations, private physical prediction/training0. Same complete initial physical state and compiled model in both tasks. This is directional component qualification, not a route/24 outcome.

One frozen longitudinal steering-coupling coefficient, stricter real entry rest, a declared bounded-motion envelope and.2rad/s parked slew replace the old always-stationary parked-mode contract. Original physical clearance/body/self/contact/control/root/state-replay hard gates remain. Maximum measured coupled-speed error 0.0008070685162121158m/s<.002; maximum position error 0.005490737417735254m<.01; minimum actual clearance 0.2853596982864619m>.15. Both independently audited all17 evidence gates and response gates.

Both restarts actually moved forward about0.21m and completed the entire final2200 stop. Refusal-to-stop dispatch, applied-only journaling and the actual-old-refusal stop certificate passed software qualification. No physical refusal was triggered in this successful batch: physical fault-injection coverage is not claimed. Worker wall times include initialization/actual/replay and are not online-control frequency measurements.

The old V1111 complete-source software PASS used different steering-mode dynamics and duration. It cannot be reused as a new-model complete-source certificate. The next zero-model prerequisite is revised-model complete recovery-source admission, followed by same-version three-route main+complete repeats. The user selected only this90-minute component window; no route/24 physical launch follows automatically.

```json
{
  "passed": true,
  "scope": "two fixed static canonical directional steering/restart/stop components",
  "tasks": [
    {
      "task_id": "negative_to_positive",
      "passed": true,
      "actual_native": 8100,
      "own_replay_native": 8100,
      "whole_trajectory_state_ctrl_mocap_error": 0.0,
      "contact_mismatched_ticks": 0,
      "minimum_actual_clearance_m": 0.41350255829526417,
      "bad_contacts": 0,
      "maximum_pose_heading_steering_error": [
        0.005490737417735254,
        0.0030643044748328574,
        0.004860518848718576
      ],
      "maximum_coupled_speed_error_m_s": 0.0008065636295126726,
      "actual_restart_net_displacement_m": 0.21290096414007698,
      "final_translation_speed_m_s": 8.064870823626919e-06,
      "terminal_last50_translation_speed_max": 8.064870823626917e-06,
      "complete2200_actual_final_stop": true,
      "model_sha": "d8e1b9064085acd9da166561eac2b1c3b09285b99a9a35e5ecb6eb4a2a954711",
      "worker_wall_s": 13.333604646002641,
      "physical_refusal_triggered": false
    },
    {
      "task_id": "positive_to_negative",
      "passed": true,
      "actual_native": 8100,
      "own_replay_native": 8100,
      "whole_trajectory_state_ctrl_mocap_error": 0.0,
      "contact_mismatched_ticks": 0,
      "minimum_actual_clearance_m": 0.2853596982864619,
      "bad_contacts": 0,
      "maximum_pose_heading_steering_error": [
        0.005316043185769091,
        0.0028160992250760852,
        0.0048823603431055185
      ],
      "maximum_coupled_speed_error_m_s": 0.0008070685162121158,
      "actual_restart_net_displacement_m": 0.2128401714981508,
      "final_translation_speed_m_s": 8.048087555502946e-06,
      "terminal_last50_translation_speed_max": 8.048087555502946e-06,
      "complete2200_actual_final_stop": true,
      "model_sha": "d8e1b9064085acd9da166561eac2b1c3b09285b99a9a35e5ecb6eb4a2a954711",
      "worker_wall_s": 13.263072378991637,
      "physical_refusal_triggered": false
    }
  ],
  "counts": {
    "vehicle_initializations": 2,
    "new_actual_native": 16200,
    "own_replay_native": 16200,
    "replay_state_initializations": 2,
    "private_mujoco_native": 0,
    "training_updates": 0,
    "analytical_prediction_native": 0
  },
  "preparation_analytical_native": 16200,
  "entry_qualification_analytical_native": 4400,
  "fit_new_physical_integrations": 0,
  "same_full_canonical_initial_state": true,
  "minimum_actual_clearance_m": 0.2853596982864619,
  "maximum_position_error_m": 0.005490737417735254,
  "maximum_coupled_speed_error_m_s": 0.0008070685162121158,
  "source_unchanged": true,
  "original_review_guard_restored": true,
  "execution_lock_idle": true,
  "refusal_to_stop_software_regression_passed": true,
  "physical_refusal_fault_injection_executed": false,
  "ordinary_full_stops_physically_verified": true,
  "three_route_development_passed": false,
  "new24_executed": false,
  "new24_denominator": null,
  "new_software_model_predictions_in_this_review": 0,
  "new_physical_integrations_in_this_review": 0,
  "next_required": "Recompute and audit complete recovery sources with the revised coupled model/mode before same-version three-route regression; later physical window remains to be decided"
}
```
