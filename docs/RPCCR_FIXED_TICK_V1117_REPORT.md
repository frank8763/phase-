# V1117 fixed-tick source

NOT_PASSED. Original all-native raw/path/goal/full-stop gates passed; gear2 endpoint0.021291843m exceeds0.02, mode2 envelope lower0.242713985m remains below0.243534210. No physical/model launch; agreed12-hour root not started.123.56s bounded software wall.

Read-only diagnosis: 11/12,12/12,12/12 first three gear steering knots at physical steering cap. Fixing timings leaves little effective steering authority; this local bounded result is not a global impossibility proof. Integer segment timing must be considered explicitly rather than continuing to adjust steering weights.

```json
{
  "passed": false,
  "optimizer_constraint_review": {
    "minimum_certified_raw_lower_m": 0.24769549396490664,
    "maximum_certified_cross_upper_m": 0.03862436977872352,
    "endpoint_errors_m": [
      0.019110776907148425,
      0.021291843412685002,
      0.01333774113873306,
      0.016404334758885728
    ],
    "coupled_mode_envelope_lower_m": [
      0.48618722907099243,
      0.24271398470759278,
      0.38010068943583575
    ],
    "maximum_restoration_violation_m": 0.0022918434126850025,
    "restoration_targets_met": false,
    "sampled_geometry_poses": 18466,
    "explicit_inequality_count": 2055
  },
  "cpp_python_maximum_error": 1.1062475215249894e-15,
  "complete_review": {
    "passed": false,
    "checks": {
      "finite": true,
      "full_states": true,
      "full_raw_geometry": true,
      "full_200_stop": true,
      "goal_upper": true,
      "speed_yaw": true,
      "legal_ctrl": true,
      "legal_slew": true,
      "path_cross_track": true,
      "gear_endpoints_within_02": false,
      "parked_alignment_settled": true,
      "coupled_mode_envelopes": false,
      "complete2200stop": true,
      "terminal_full_cycle_hold": true
    },
    "minimum_full_cycle_raw_m": 0.2476954939649062,
    "goal_upper_m": 0.1028356389170509,
    "maximum_predicted_cross_track_m": 0.03862436977872374,
    "sections": [
      {
        "gear": -1,
        "start_native": 0,
        "moving_end_native": 1550,
        "end_native": 3750,
        "stopped_endpoint_error_m": 0.019110776907148425,
        "maximum_cross_track_m": 0.019110776907148425
      },
      {
        "gear": 1,
        "start_native": 3750,
        "moving_end_native": 4996,
        "end_native": 7196,
        "stopped_endpoint_error_m": 0.021291843412685002,
        "maximum_cross_track_m": 0.021291843412685002
      },
      {
        "gear": -1,
        "start_native": 7196,
        "moving_end_native": 8392,
        "end_native": 10592,
        "stopped_endpoint_error_m": 0.01333774113873306,
        "maximum_cross_track_m": 0.029231527961839827
      },
      {
        "gear": 1,
        "start_native": 10592,
        "moving_end_native": 16259,
        "end_native": 18459,
        "stopped_endpoint_error_m": 0.016404334758885683,
        "maximum_cross_track_m": 0.03862436977872374
      }
    ],
    "coupled_envelopes": [
      {
        "start_native": 3750,
        "whole_mode_raw_lower_m": 0.48618722907099243,
        "translation_m": 0.008363021926945604,
        "angle_rad": 0.08671673378228784,
        "speed_m_s": 0.006971608913433221,
        "passed": true
      },
      {
        "start_native": 7196,
        "whole_mode_raw_lower_m": 0.24271398470759278,
        "translation_m": 0.008366942565326356,
        "angle_rad": 0.08672836708670983,
        "speed_m_s": 0.006970964537865523,
        "passed": false
      },
      {
        "start_native": 10592,
        "whole_mode_raw_lower_m": 0.38010068943583575,
        "translation_m": 0.008366942565326656,
        "angle_rad": 0.08672836708735909,
        "speed_m_s": 0.006970964537923469,
        "passed": true
      }
    ],
    "analytical_native": 18459
  },
  "handoff_selection": {
    "mode": "RETAINED_COMPLETE_STOP",
    "retained_stop_preserved": true,
    "actual_execution": false
  },
  "cpp_accounting": {
    "completed_calls": 650,
    "completed_native": 11998350,
    "partial_call_work_unknown": false
  },
  "python_accounting": {
    "python_full_source": 18459,
    "python_rolling_stops": 0
  },
  "entry_analytical_work": {
    "cpp_native": 36918,
    "python_native": 0
  },
  "frozen_source_unchanged": true,
  "guard_original": true,
  "closed": true,
  "wall_s": 123.56091428099899,
  "models": 0,
  "physical_integrations": 0,
  "official_planning_calls": 0,
  "new_measurements": 0,
  "automatic_physical_launch": false,
  "whole_route_acceptance": false
}
```
