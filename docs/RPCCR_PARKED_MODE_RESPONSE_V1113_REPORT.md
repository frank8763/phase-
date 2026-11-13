# V1113 actual parked-mode response: NOT_PASSED

The static-fixture correction passed at real t0, including exact static compiled SHA and all setup fields. One canonical vehicle executed2200 initial hold steps then28 parked-steering steps. The next command was rejected by the original V1108 body-rest prerequisite: measured longitudinal speed -0.0031814105218046385m/s exceeds0.003; the nominal model predicts0. Both rear targets remained exactly0. Initial last50-step maximum translation was 1.054043769958088e-05m/s.

All2228 applied controls reproduce from saved measured inputs/mode/memory, full physical control replay error0 with identical contacts; minimum actual clearance 0.45194146664169554m and bad contacts0. Whole-prefix position/heading/steering errors remain within the original empirical response thresholds. This does not validate the full reversal or restart.

The original saved audit rejected the2229-entry journal because it includes one command rejected before integration. A separate zero-model saved-prefix review explicitly accounts for that unexecuted entry and reproduces the exact guard failure without changing controller memory. Original failed audit/result/source/window remain unchanged. Its complete2200-tail check is correctly false: the worker terminated at the allocator assertion and did not execute the intended failure stop. Final translation speed 0.003186022524351682m/s is not claimed as verified rest.

The observed gap is in the parked-mode physical-model/entry/exit contract. Steering-phase body drift is measured; its precise friction/contact cause is not established. Next design must certify steering-induced coupled motion and retained braking on refusal, without simply loosening the3mm/s prerequisite. No further model run, route,24 or training is authorized by this closed batch.

```json
{
  "closed": true,
  "original_component_passed": false,
  "original_saved_audit_failed_and_preserved": true,
  "scope": "2228 applied native steps and one unapplied rejected parked command",
  "applied_native": 2228,
  "executed_initial_hold_native": 2200,
  "executed_parked_native": 28,
  "unapplied_command_count": 1,
  "actual_original_guard_reproduced": "STEERING_ONLY_BODY_NOT_STOPPED",
  "rejected_guard_left_controller_memory_unchanged": true,
  "applied_prefix_audit": {
    "passed": false,
    "evidence_passed": false,
    "checks": {
      "recorded_native": true,
      "actual_measurements_bound": true,
      "all_mode_memory_reconstructed": true,
      "mode_rear_zero": true,
      "fixed_schedule": true,
      "raw_actual_clearance": true,
      "independent_bounding_footprint": true,
      "self_containment": true,
      "no_bad_contacts": true,
      "legal_ctrl": true,
      "legal_slew": true,
      "complete2200tail": false,
      "replay_exact": true
    },
    "complete_response_passed": false,
    "maximum_response_errors": [
      0.0005506530400490507,
      0.0003754970216307551,
      0.005415379600871909
    ],
    "maximum_controller_error": 0.0,
    "physical_native": 2228,
    "models": 0,
    "integrations": 0,
    "analytical_prediction_integrations": 0,
    "not_dynamic_acceptance": true
  },
  "actual_last_longitudinal_m_s": -0.0031814105218046385,
  "nominal_last_longitudinal_m_s": 0.0,
  "parked_body_longitudinal_limit_m_s": 0.003,
  "actual_last_yaw_rad": -1.5607367578871985,
  "nominal_last_yaw_rad": -1.5608741986074928,
  "maximum_prepark_last50_translation_m_s": 1.054043769958088e-05,
  "parked_rear_targets_all_zero": true,
  "all_native_body_caps": true,
  "full2200failure_stop_executed": false,
  "terminal_actual_rest_not_claimed": true,
  "observed_motion_without_rear_drive_target": true,
  "physical_mechanism_inference": "Steering-phase coupled body drift is observed; contact/friction/geometric mechanism not separately identified",
  "model_contract_gap": "Nominal longitudinal dynamics predict zero under rear-zero steering, but measured drift crosses the mode prerequisite",
  "exit_contract_gap": "Allocator assertion exits worker before the intended retained2200 stop tail; simulation termination is not verified actual braking",
  "next_design": "Treat steering as a coupled physical mode and certify its body-motion bounds; preserve actual pre-entry rest check and complete retained-stop handoff, rather than simply raising the3mm/s gate",
  "new_models": 0,
  "new_integrations": 0,
  "new_analytical_dynamics": 0,
  "source_unchanged": true,
  "guard_original": true,
  "no_physical_restart": true
}
```
