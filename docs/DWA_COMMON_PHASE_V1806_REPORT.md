# 首DWA共同任务实际结果

分类：VALID_FINITE_METHOD_REFUSAL_WITH_INDEPENDENT_PREFIX_AUDIT。原method/config未调参，非旧C3/Fox原生。

{
  "closed": true,
  "common_method": "DWA",
  "common_task": "common_01",
  "classification": "VALID_FINITE_METHOD_REFUSAL_WITH_INDEPENDENT_PREFIX_AUDIT",
  "qualified_whole_navigation_passed": false,
  "valid_finite_method_negative": true,
  "actual_native": 280,
  "own_replay_native": 280,
  "physical": {
    "actual_native": 280,
    "fully_recorded_native": 280,
    "minimum_actual_clearance_m": 0.31374149903963056,
    "minimum_self_margin_m": 0.00990178014268428,
    "bad_contacts": 0,
    "final_body": [
      -3.992844280968741,
      -1.9999579445605362,
      -0.0006568021533209401,
      -1.0433112207068691e-05,
      -1.084601484057708e-07
    ],
    "final_translation_speed_m_s": 1.0433228982871428e-05,
    "root_guard_native_count": 280,
    "goal_distance_m": 7.992844281079382,
    "first_actor_detection": null,
    "actual_travel_after_detection_m": 0.0
  },
  "replay": {
    "replay_native": 280,
    "maximum_qpos_qvel_ctrl_mocap_error": 0.0,
    "contact_mismatched_ticks": 0,
    "passed": true
  },
  "independent_audit": {
    "passed": true,
    "scope": "INDEPENDENT_ACTUAL_PREFIX_SAFETY_ONLY_CANONICAL_FAILURE_PRESERVED",
    "whole_navigation_passed": false,
    "actual_native": 280,
    "own_replay_native": 280,
    "maximum_controller_error": 1.3877787807814457e-17,
    "maximum_memory_error": 1.3877787807814457e-17,
    "maximum_actual_tracking": [
      5.564074459255222e-05,
      0.00027448013331687936,
      0.0038762660902994708
    ],
    "normal_native_with_current_admission": 80,
    "minimum_actual_clearance_m": 0.31374149903963056,
    "canonical_first_error": {
      "stage": "normal",
      "error": "AssertionError('DWA_CURRENT_CYCLE_COMPLETE_STOP_REFUSED')",
      "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1806_dwa_common_phase/driver.py\", line 88, in execute\n    result['navigation']=navigator.run(v,binding,task,source,out,save,quota,refresh)\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1806_dwa_common_phase/navigation.py\", line 71, in run\n    assert proof['passed'],'DWA_CURRENT_CYCLE_COMPLETE_STOP_REFUSED'\nAssertionError: DWA_CURRENT_CYCLE_COMPLETE_STOP_REFUSED\n"
    },
    "original_generic_audit_seam": {
      "generic_original_statements_preserved": 30,
      "original_SHA256": "be03f551bfe6fcdecfbd6adcb88ecd1254a515336adebc696833878154540946",
      "generic_AST_SHA256": "324366ca2ba25a010aeec864ab1db49517d8d95ace9e85beebac7f3240d37d6b",
      "removed_only_old_discovery_and_whole_task_scope": true
    },
    "causal_sources_rebuilt_from_whitelist": true,
    "independent_saved_prediction_geometry_profiles": 25,
    "internal_Allocator_constructions": null,
    "total_modelwork": null,
    "new_physical_native_during_audit": 0
  },
  "first_error": {
    "stage": "normal",
    "error": "AssertionError('DWA_CURRENT_CYCLE_COMPLETE_STOP_REFUSED')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1806_dwa_common_phase/driver.py\", line 88, in execute\n    result['navigation']=navigator.run(v,binding,task,source,out,save,quota,refresh)\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1806_dwa_common_phase/navigation.py\", line 71, in run\n    assert proof['passed'],'DWA_CURRENT_CYCLE_COMPLETE_STOP_REFUSED'\nAssertionError: DWA_CURRENT_CYCLE_COMPLETE_STOP_REFUSED\n"
  },
  "secondary_errors": [],
  "outer_first_error": null,
  "canonical_initializations": 1,
  "internal_factory_count": null,
  "full_modelwork_total": null,
  "source_members": 14404,
  "source_all_SHA_verified_after_exit": true,
  "no_global_algorithm_failure_or_superiority_claim": true,
  "scientific_denominator_retained": true,
  "remote_pending": true
}

原全部20消融与历史G4C/Final300另账；此case不能单独说明相对RPCCR收益或统计优势。
