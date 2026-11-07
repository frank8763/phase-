# 2026-11-07截至20:00日间无人值守实验实际报告

{
  "previous_closed_run": {
    "path": "runs/v853_daytime_20261107",
    "status": "NOT_PASSED_OR_INCOMPLETE",
    "counts": {
      "navigation_native": 0,
      "navigation_private_native": 0,
      "navigation_replay_native": 0,
      "component_old_replay_native": 3192,
      "component_private_native": 0,
      "component_actual_native": 0,
      "component_repeat_native": 0,
      "backend_old_replay_native": 0,
      "backend_private_native": 0
    },
    "source_and_decompressed_sha_verified": true
  },
  "status": "NOT_PASSED_OR_INCOMPLETE",
  "root_stop": "FATAL_ANOMALY_ALL_MODEL_BRANCHES_STOPPED",
  "source_unchanged": true,
  "variants": [
    {
      "variant": "A32",
      "commit_native": 32,
      "component": {
        "status": "TWO_FIXED_COMPONENTS_AND_FULL_REPEATS_PASS",
        "passed": true,
        "rows": [
          {
            "checkpoint": 399,
            "passed": true,
            "maximum_native_error": 0.0,
            "full_integration_repeat_error": 0.0,
            "minimum_actual_clearance_m": 0.2094313016933026,
            "minimum_actual_self_margin_m": 0.008874760518743807,
            "bad_contacts": 0,
            "proof": {
              "gear": -1,
              "normal_allowed": true,
              "short_gain": 0.045433224647577264,
              "full_gain": 0.08033002492102065,
              "commit_native": 32
            },
            "native_actual": 328,
            "native_repeat": 328,
            "private_native": 336
          },
          {
            "checkpoint": 1148,
            "passed": true,
            "maximum_native_error": 0.0,
            "full_integration_repeat_error": 0.0,
            "minimum_actual_clearance_m": 0.2094313016933026,
            "minimum_actual_self_margin_m": 0.00886761830627647,
            "bad_contacts": 0,
            "proof": {
              "gear": 1,
              "normal_allowed": true,
              "short_gain": 0.025618693324467867,
              "full_gain": 0.24355965320779568,
              "commit_native": 32
            },
            "native_actual": 328,
            "native_repeat": 328,
            "private_native": 336
          }
        ],
        "counts": {
          "old_replay_native": 12376,
          "private_native": 672,
          "actual_branch_native": 656,
          "repeat_branch_native": 656
        }
      },
      "development_passed": false,
      "records": [
        {
          "name": "v853_A32_main_slot01",
          "task": {
            "slot": 1,
            "seed": 10010001,
            "phase": 0.6573753567727383,
            "case_id": "WEST_EAST",
            "initial_axis_motion_direction": "POSITIVE_AXIS",
            "course_distance_m": 8.0,
            "role": "DEVELOPMENT_KNOWN_TASK",
            "phase_rule": "SHA256 RPCCR_FIELD_20261102_PHASE|seed; alternating cos-sign within each route"
          },
          "role": "MAIN",
          "run": "runs/v853_maneuver_worker/v853_A32_main_slot01/paired",
          "physical_passed": true,
          "functional_passed": false,
          "repeat_passed": null,
          "repeat": null,
          "result": {
            "condition": "geometry_memory",
            "seed": 10010001,
            "outcome": "NATIVE_TERMINATION",
            "strict_safe_arrival": false,
            "goal_distance_m": 3.053718287694074,
            "public_steps": 1800,
            "physics_steps": 14400,
            "contacts": {
              "physics_steps": 14400,
              "all_contact_records": 179277,
              "contact_type_counts": {
                "ground_support": 115200,
                "robot_self_contact": 64077
              },
              "negative_distance_counts_all_types": {
                "ground_support": 115200,
                "robot_self_contact": 64077
              },
              "robot_obstacle_contact_records": 0,
              "robot_obstacle_penetration_records": 0,
              "robot_obstacle_contact_steps": 0,
              "robot_obstacle_penetration_steps": 0,
              "maximum_obstacle_penetration_depth_m": 0.0,
              "minimum_obstacle_distance_m": null,
              "first_anomaly": null,
              "unknown_contact_records": 0,
              "robot_obstacle_geom_pairs": [],
              "contact_log_content_sha256": "7b2f51028db2cc44f4dd22666ce4c3a2a91d4d0939ed61399ef0539528366a29"
            },
            "backup_attempts": 37,
            "backup_steps": 1460,
            "planning_attempts": 9,
            "planning_wall_s": 188.53048058101558,
            "command_overrides": 1800,
            "elapsed_s": 1572.6826237330097,
            "initial_state_hash": "64c6f4dc659ad66af9f6a0f3c0fc3e247183f99e9d05c704ce5575df2c17eb63",
            "normalized_initial_state_hash": "fcd26304e4b0dc879085c5da4b23fd54dfb7718d1b242b5eda537c1ead2b437c",
            "minimum_actual_self_domain_margin_m": 0.009116227658063247,
            "self_geometry_checked_native_ticks": 14400,
            "static_obstacle_pose_unchanged": true,
            "root_mutations_outside_mjstep": 0,
            "source_revision": "V853_COMMON_SEGMENT_COMMITMENT",
            "prediction_steps": 2313832,
            "retained_reentry_attempts": 0,
            "retained_reentry_successes": 0,
            "retained_reentry_private_native": 0,
            "conditional_nonpenetrating_map_motion_class": true,
            "declared_euclidean_speed_cap_m_s": 0.08,
            "first_discovery_step": 262,
            "discovery_brake_finished_step": 302,
            "discovery_terminal_speed_m_s": 3.533936996404537e-06,
            "initial_unknown_mode": "UNSEEN_PRIOR",
            "early_scan_started_step": null,
            "early_scan_finished_step": null,
            "differential_candidate_bank_enabled": true,
            "native_applied_ctrl_checks": 14400,
            "reserved_recovery_activations": 37,
            "reserved_recovery_public_steps": 1460,
            "certified_handover_attempts": 0,
            "certified_handover_successes": 0,
            "proposal_model_sha256": "fc9d3132c912033e2ec04cd8ae1ce236c818c484d5b96961c6f3dc1b0548b527",
            "course_distance_m": 8.0,
            "course_phase": 0.6573753567727383,
            "initial_observation_steps": 0,
            "dynamic_mode": "predictive",
            "minimum_dynamic_native_clearance_m": 0.179961667620896,
            "actor_maximum_native_displacement_m": 0.0007999996512152172,
            "actor_motion_ticks": 14400,
            "actor_position_at_end": [
              3.0362748219948865,
              -0.9130205603514175
            ]
          },
          "audits": {
            "audit_run.py": true,
            "audit_forward_controller.py": true,
            "audit_route_commitment.py": true,
            "audit_projection_learning.py": true,
            "audit_all_tail_geometry.py": true,
            "audit_shadow_mode.py": true,
            "audit_reentry.py": true,
            "audit_complete_joint.py": true,
            "audit_nominal_layers.py": true,
            "audit_reactive.py": true,
            "audit_proposal_separation.py": true,
            "audit_tracked_norm.py": true,
            "audit_goal_renewal.py": true,
            "audit_ranked_return.py": true,
            "audit_forward_escape.py": true,
            "audit_reference_recovery.py": true,
            "audit_early_joint.py": true,
            "audit_candidate_policy.py": true,
            "audit_maneuver.py": true
          },
          "functional_failed_checks": [
            "strict_arrival"
          ]
        }
      ],
      "main_attempts": 1,
      "main_successes": 0,
      "unexecuted_navigation": 5
    },
    {
      "variant": "B64",
      "commit_native": 64,
      "component": {
        "status": "TWO_FIXED_COMPONENTS_AND_FULL_REPEATS_PASS",
        "passed": true,
        "rows": [
          {
            "checkpoint": 399,
            "passed": true,
            "maximum_native_error": 0.0,
            "full_integration_repeat_error": 0.0,
            "minimum_actual_clearance_m": 0.2094313016933026,
            "minimum_actual_self_margin_m": 0.008874760518743807,
            "bad_contacts": 0,
            "proof": {
              "gear": -1,
              "normal_allowed": true,
              "short_gain": 0.07466468209637317,
              "full_gain": 0.08033002492102065,
              "commit_native": 64
            },
            "native_actual": 328,
            "native_repeat": 328,
            "private_native": 336
          },
          {
            "checkpoint": 1148,
            "passed": true,
            "maximum_native_error": 0.0,
            "full_integration_repeat_error": 0.0,
            "minimum_actual_clearance_m": 0.2094313016933026,
            "minimum_actual_self_margin_m": 0.00886761830627647,
            "bad_contacts": 0,
            "proof": {
              "gear": 1,
              "normal_allowed": true,
              "short_gain": 0.05965740041850004,
              "full_gain": 0.24355965320779568,
              "commit_native": 64
            },
            "native_actual": 328,
            "native_repeat": 328,
            "private_native": 336
          }
        ],
        "counts": {
          "old_replay_native": 12376,
          "private_native": 672,
          "actual_branch_native": 656,
          "repeat_branch_native": 656
        }
      },
      "development_passed": false,
      "records": [
        {
          "name": "v853_B64_main_slot01",
          "task": {
            "slot": 1,
            "seed": 10010001,
            "phase": 0.6573753567727383,
            "case_id": "WEST_EAST",
            "initial_axis_motion_direction": "POSITIVE_AXIS",
            "course_distance_m": 8.0,
            "role": "DEVELOPMENT_KNOWN_TASK",
            "phase_rule": "SHA256 RPCCR_FIELD_20261102_PHASE|seed; alternating cos-sign within each route"
          },
          "role": "MAIN",
          "run": "runs/v853_maneuver_worker/v853_B64_main_slot01/paired",
          "physical_passed": false,
          "functional_passed": false,
          "repeat_passed": null,
          "repeat": null,
          "result": {
            "condition": "geometry_memory",
            "seed": 10010001,
            "outcome": "NO_RESERVED_RECOVERY_COMMAND",
            "strict_safe_arrival": false,
            "goal_distance_m": 1.7032226673472426,
            "public_steps": 1105,
            "physics_steps": 8840,
            "contacts": {
              "physics_steps": 8840,
              "all_contact_records": 102721,
              "contact_type_counts": {
                "ground_support": 70720,
                "robot_self_contact": 32001
              },
              "negative_distance_counts_all_types": {
                "ground_support": 70720,
                "robot_self_contact": 32001
              },
              "robot_obstacle_contact_records": 0,
              "robot_obstacle_penetration_records": 0,
              "robot_obstacle_contact_steps": 0,
              "robot_obstacle_penetration_steps": 0,
              "maximum_obstacle_penetration_depth_m": 0.0,
              "minimum_obstacle_distance_m": null,
              "first_anomaly": null,
              "unknown_contact_records": 0,
              "robot_obstacle_geom_pairs": [],
              "contact_log_content_sha256": "310ed2ce7190ea9bd6d87053724a5a578f043257a1d900d4c5b75085ea3eee40"
            },
            "backup_attempts": 57,
            "backup_steps": 745,
            "planning_attempts": 8,
            "planning_wall_s": 26.41315072897123,
            "command_overrides": 1105,
            "elapsed_s": 1555.3942925459996,
            "initial_state_hash": "cd32aae8a66ba3de1e832dcee4388c59f4337ae370181b07806cbc1fe78d817a",
            "normalized_initial_state_hash": "fcd26304e4b0dc879085c5da4b23fd54dfb7718d1b242b5eda537c1ead2b437c",
            "minimum_actual_self_domain_margin_m": 0.009196564944815522,
            "self_geometry_checked_native_ticks": 8840,
            "static_obstacle_pose_unchanged": true,
            "root_mutations_outside_mjstep": 0,
            "source_revision": "V853_COMMON_SEGMENT_COMMITMENT",
            "prediction_steps": 10503184,
            "retained_reentry_attempts": 0,
            "retained_reentry_successes": 0,
            "retained_reentry_private_native": 0,
            "conditional_nonpenetrating_map_motion_class": true,
            "declared_euclidean_speed_cap_m_s": 0.08,
            "first_discovery_step": 262,
            "discovery_brake_finished_step": 302,
            "discovery_terminal_speed_m_s": 3.533936996404537e-06,
            "initial_unknown_mode": "UNSEEN_PRIOR",
            "early_scan_started_step": null,
            "early_scan_finished_step": null,
            "differential_candidate_bank_enabled": true,
            "native_applied_ctrl_checks": 8840,
            "reserved_recovery_activations": 57,
            "reserved_recovery_public_steps": 745,
            "certified_handover_attempts": 123,
            "certified_handover_successes": 47,
            "proposal_model_sha256": "fc9d3132c912033e2ec04cd8ae1ce236c818c484d5b96961c6f3dc1b0548b527",
            "course_distance_m": 8.0,
            "course_phase": 0.6573753567727383,
            "initial_observation_steps": 0,
            "dynamic_mode": "predictive",
            "minimum_dynamic_native_clearance_m": 0.18620353208955032,
            "actor_maximum_native_displacement_m": 0.0007999996476611368,
            "actor_motion_ticks": 8840,
            "actor_position_at_end": [
              2.9401644233643647,
              -1.1434732037431088
            ]
          },
          "audits": {
            "audit_run.py": false,
            "audit_forward_controller.py": false,
            "audit_route_commitment.py": false,
            "audit_projection_learning.py": false,
            "audit_all_tail_geometry.py": false,
            "audit_shadow_mode.py": false,
            "audit_reentry.py": false,
            "audit_complete_joint.py": false,
            "audit_nominal_layers.py": false,
            "audit_reactive.py": false,
            "audit_proposal_separation.py": false,
            "audit_tracked_norm.py": false,
            "audit_goal_renewal.py": false,
            "audit_ranked_return.py": false,
            "audit_forward_escape.py": false,
            "audit_reference_recovery.py": false,
            "audit_early_joint.py": false,
            "audit_candidate_policy.py": false,
            "audit_maneuver.py": false
          },
          "functional_failed_checks": []
        }
      ],
      "main_attempts": 1,
      "main_successes": 0,
      "unexecuted_navigation": 5
    },
    {
      "variant": "C328",
      "commit_native": 328,
      "component": null,
      "development_passed": false,
      "records": [],
      "main_attempts": 0,
      "main_successes": 0,
      "unexecuted_navigation": 6
    }
  ],
  "backend": {
    "status": "CPU_BATCH_EQUIVALENCE_PASS",
    "passed": true,
    "errors": {
      "qpos": 0.0,
      "qvel": 0.0,
      "poses": 0.0,
      "self_bounds": 0.0,
      "minimum_self_margin": 0.0,
      "terminal_speed": 0.0
    },
    "serial_wall_s": 0.5409864490211476,
    "batch_wall_s": 0.3641554949863348,
    "measured_ratio": 1.4855918871729463,
    "old_replay_native": 3192,
    "private_native": 4320,
    "actual_branches": 0,
    "new_navigation": 0,
    "training_updates": 0,
    "automatically_adopted_in_navigation": false,
    "scope": "Only fixed original CPU predictor nine controls, full array equivalence. Single CPU sequential batch; not real-time or GPU validation."
  },
  "known_counts": {
    "navigation_native": 23240,
    "navigation_private_native": 12817016,
    "navigation_replay_native": 23240,
    "component_old_replay_native": 24752,
    "component_private_native": 1344,
    "component_actual_native": 1312,
    "component_repeat_native": 1312,
    "backend_old_replay_native": 3192,
    "backend_private_native": 4320
  },
  "accounts_exact": {
    "navigation_native": true,
    "navigation_private_native": true,
    "navigation_replay_native": true,
    "component_old_replay_native": true,
    "component_private_native": true,
    "component_actual_native": true,
    "component_repeat_native": true,
    "backend_old_replay_native": true,
    "backend_private_native": true
  },
  "counts": {
    "navigation_native": 23240,
    "navigation_private_native": 12817016,
    "navigation_replay_native": 23240,
    "component_old_replay_native": 24752,
    "component_private_native": 1344,
    "component_actual_native": 1312,
    "component_repeat_native": 1312,
    "backend_old_replay_native": 3192,
    "backend_private_native": 4320
  },
  "new24": 0,
  "training_updates": 0,
  "real_robot": 0,
  "no_statistical_confirmation": true,
  "no_realtime_claim": true,
  "model_initializations": null,
  "review_pending_restored": true,
  "execution_lock_idle": true,
  "models_finalizer": 0,
  "integrations_finalizer": 0
}

完整主/重复/失败/未执行均分版保留；原1200步失败不重开，新2400步为新开发预算。没有新24、训练、实体机或实时资格声明。20:00后只零模型收尾。
