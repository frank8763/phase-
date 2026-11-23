# Original TEB current cycle V1739

One exposed WE03 operational development case. Body-centre/rear-axle/footprint geometry, original HCP binary, original raw output plus explicit upstream ROS saturation port, original fullstate stop/feedback gates. No new phase, whole navigation, statistical or realtime claim. Source/interface failures and finite planner/command/safety refusals distinguished by the exact primary and secondary records below. q1159 counters are a subset, all other native/static/FFI work and internal factory/Allocator counts remain unknown. Source qualification was separate zero-model work.

```json
{
  "closed": true,
  "scope": "EXPOSED_TEB_CURRENT_QUERY_SHORT_ACTUATOR_COMPONENT_NOT_WHOLE_BENCHMARK",
  "passed": false,
  "scientific_navigation_passed": false,
  "whole_navigation_passed": false,
  "new_independent_task_increment": 0,
  "formal_assignment_increment": 0,
  "actual_canonical_initializations": 1,
  "internal_factory_model_constructions": null,
  "actual_native": 200,
  "own_replay_native": 200,
  "component_passed": false,
  "independent_full_actual_audit_passed": false,
  "native_query": {
    "passed": false,
    "closed": true,
    "wire_sha256": "b6deee4643d9a49000d7653d8fa045c0b3dba3b3fac4432fae51090675f39cd0",
    "models": 0,
    "physical_native": 0,
    "replay_native": 0,
    "counts": {
      "explicit_DLL_loads": 1,
      "metadata_FFI_calls": 15,
      "constructor_attempts": 1,
      "constructor_returns": 1,
      "query_attempts": 1,
      "query_returns": 1,
      "destructor_calls": 1,
      "constructor_inflight_unknown": false,
      "query_inflight_unknown": false,
      "internal_optimizer_iterations": null,
      "all_native_work": null,
      "automatic_static_registrations": null
    },
    "first_error": "AssertionError(('TEB_ORIGINAL_FINITE_QUERY_REFUSED', 'NO_OPTIMIZED_SELECTED_TEB', 1, 1))",
    "proposal": {
      "returncode": 1,
      "status": 1,
      "samples": 0,
      "classes": 0,
      "vx": 0.0,
      "vy": 0.0,
      "omega": 0.0,
      "sequence": 1,
      "error": "NO_OPTIMIZED_SELECTED_TEB",
      "trajectory": []
    },
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1739_teb_current_cycle/native_query.py\", line 75, in main\n    result['proposal']=proposal;assert status==0 and answer.status==0,('TEB_ORIGINAL_FINITE_QUERY_REFUSED',proposal['error'],status,answer.status)\nAssertionError: ('TEB_ORIGINAL_FINITE_QUERY_REFUSED', 'NO_OPTIMIZED_SELECTED_TEB', 1, 1)\n",
    "native_library_counters": {
      "20": 1,
      "21": 1,
      "22": 1
    },
    "wall_s": 0.06959129800088704
  },
  "first_error": {
    "stage": "normal",
    "error": "AssertionError('TEB_NATIVE_ORIGINAL_QUERY_REFUSED')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1739_teb_current_cycle/driver.py\", line 90, in execute\n    result['component']=component.run(v,binding,task,source,out,save,quota,measured_origin)\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1739_teb_current_cycle/component.py\", line 21, in run\n    assert raw['passed'],'TEB_NATIVE_ORIGINAL_QUERY_REFUSED'\nAssertionError: TEB_NATIVE_ORIGINAL_QUERY_REFUSED\n"
  },
  "secondary_errors": [],
  "outer_first_error": null,
  "physical": {
    "actual_native": 200,
    "fully_recorded_native": 200,
    "minimum_actual_clearance_m": 0.31498918194116166,
    "minimum_self_margin_m": 0.009944851725426362,
    "bad_contacts": 0,
    "final_body": [
      -4.000063036520518,
      -1.9999544849496327,
      -7.23247111948151e-08,
      -1.0833237080721948e-05,
      -3.388483804457622e-09
    ],
    "final_translation_speed_m_s": 1.0838707181219234e-05,
    "root_guard_native_count": 200,
    "goal_distance_m": 8.000063036649994,
    "first_actor_detection": null,
    "actual_travel_after_detection_m": 0.0
  },
  "own_replay": {
    "replay_native": 200,
    "maximum_qpos_qvel_ctrl_mocap_error": 0.0,
    "contact_mismatched_ticks": 0,
    "passed": true
  },
  "component": {},
  "independent_audit": {},
  "tracked_q1159_recovery_subset": {
    "cpp_native": 0,
    "python_native": 0,
    "cpp_completed_native": 0,
    "python_completed_native": 0,
    "inflight": null,
    "cpp_calls": 0,
    "python_calls": 0,
    "cpp_constructor_returns": 0,
    "python_constructor_returns": 0,
    "internal_Allocator_constructions": null,
    "poisoned": false
  },
  "all_modelwork_total": null,
  "internal_Allocator_constructions": null,
  "journal_rows": 200,
  "journal_applied_rows": 200,
  "terminal2200_zero_requests": false,
  "source_members": 14191,
  "all_source_SHA_verified_after_child_exit": true,
  "review_original": true,
  "execution_idle": true,
  "owned_child_gone": true,
  "remote_runtime_recovery_pending": true,
  "reviewed_unix": 1795420456.154172,
  "source_result_paths_SHA256": {
    "runs/v1739_teb_current_cycle/COMPLETION.json": "083b02ac8cd60d99cf722312d36e3d706d6d82931ff25a9d2f813ea8ce75e6b6",
    "runs/v1739_teb_current_cycle/SOURCE_FREEZE.json": "c4ef49e60fc7c864d5d8ffc5f5335417f04bdd5e0de4da195de5f490ab7a88cc",
    "runs/v1739_teb_current_cycle/actual/RESULT.json": "4199a182a0a70967d8389b5ca958c03dc70676a220a40b94c105989c8d661a36",
    "runs/v1739_teb_current_cycle/actual/APPLIED_JOURNAL.json": "c81a3742edb65a7fd14632105ecc33017e0e36dea6649d141d0fd7d9180fabcf"
  }
}
```
