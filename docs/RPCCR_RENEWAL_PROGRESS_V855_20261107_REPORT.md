# 2026-11-07截至20:00日间无人值守实验实际报告

{
  "previous_closed_run": {
    "path": "runs/v854_daytime_input_continuation",
    "status": "NOT_PASSED_OR_INCOMPLETE",
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
    "source_and_decompressed_sha_verified": true
  },
  "status": "NOT_PASSED_OR_INCOMPLETE",
  "root_stop": "ALL_PREREGISTERED_BRANCHES_CLOSED",
  "source_unchanged": true,
  "variants": [
    {
      "variant": "RENEW64_328",
      "commit_native": 64,
      "component": {
        "status": "TWO_FIXED_COMPONENTS_AND_FULL_REPEATS_PASS",
        "passed": true,
        "rows": [
          {
            "checkpoint": 303,
            "passed": true,
            "maximum_native_error": 0.0,
            "full_integration_repeat_error": 0.0,
            "minimum_actual_clearance_m": 0.305892278021587,
            "minimum_actual_self_margin_m": 0.008834415617669344,
            "bad_contacts": 0,
            "proof": {
              "gear": 1,
              "normal_allowed": true,
              "short_gain": 0.052600585499487935,
              "full_gain": 0.43960278584255613,
              "commit_native": 64
            },
            "native_actual": 328,
            "native_repeat": 328,
            "private_native": 8072
          },
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
              "short_gain": 0.08493220915181127,
              "full_gain": 0.22334166000118166,
              "commit_native": 64
            },
            "native_actual": 328,
            "native_repeat": 328,
            "private_native": 7176
          }
        ],
        "counts": {
          "old_replay_native": 5616,
          "private_native": 15248,
          "actual_branch_native": 656,
          "repeat_branch_native": 656
        }
      },
      "development_passed": false,
      "records": [
        {
          "name": "v855_RENEW64_328_main_slot01",
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
          "run": "runs/v855_renewal_worker/v855_RENEW64_328_main_slot01/paired",
          "physical_passed": true,
          "functional_passed": false,
          "repeat_passed": null,
          "repeat": null,
          "result": {
            "condition": "geometry_memory",
            "seed": 10010001,
            "outcome": "NO_RESERVED_RECOVERY_COMMAND",
            "strict_safe_arrival": false,
            "goal_distance_m": 1.400662720160083,
            "public_steps": 573,
            "physics_steps": 4584,
            "contacts": {
              "physics_steps": 4584,
              "all_contact_records": 51755,
              "contact_type_counts": {
                "ground_support": 36672,
                "robot_self_contact": 15083
              },
              "negative_distance_counts_all_types": {
                "ground_support": 36672,
                "robot_self_contact": 15083
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
              "contact_log_content_sha256": "36fb2a757350057719d3b31d05897b8f72ce0887e340231be6da029381ffd617"
            },
            "backup_attempts": 22,
            "backup_steps": 248,
            "planning_attempts": 2,
            "planning_wall_s": 3.0590766620007344,
            "command_overrides": 573,
            "elapsed_s": 843.3565158320125,
            "initial_state_hash": "cca6d4968b0ac2e180f00a1b6b86eac4c5a27ee41049fc204bd208bb4bc706f0",
            "normalized_initial_state_hash": "f3e5981844b6ab84d6f01804218e8fd51d0070235a8859d8700706eb736d0be3",
            "minimum_actual_self_domain_margin_m": 0.009030496086219586,
            "self_geometry_checked_native_ticks": 4584,
            "static_obstacle_pose_unchanged": true,
            "root_mutations_outside_mjstep": 0,
            "source_revision": "V855_ADAPTIVE_NATIVE_RENEWAL_PROGRESS",
            "prediction_steps": 5837456,
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
            "native_applied_ctrl_checks": 4584,
            "reserved_recovery_activations": 22,
            "reserved_recovery_public_steps": 248,
            "certified_handover_attempts": 36,
            "certified_handover_successes": 20,
            "proposal_model_sha256": "fc9d3132c912033e2ec04cd8ae1ce236c818c484d5b96961c6f3dc1b0548b527",
            "course_distance_m": 8.0,
            "course_phase": 0.6573753567727383,
            "initial_observation_steps": 0,
            "dynamic_mode": "predictive",
            "minimum_dynamic_native_clearance_m": 0.2817606086282387,
            "actor_maximum_native_displacement_m": 0.0007999996434164296,
            "actor_motion_ticks": 4584,
            "actor_position_at_end": [
              3.0358531406146674,
              -0.9140316641458593
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
    }
  ],
  "backend": null,
  "known_counts": {
    "navigation_native": 4584,
    "navigation_private_native": 5837456,
    "navigation_replay_native": 4584,
    "component_old_replay_native": 5616,
    "component_private_native": 15248,
    "component_actual_native": 656,
    "component_repeat_native": 656,
    "backend_old_replay_native": 0,
    "backend_private_native": 0
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
    "navigation_native": 4584,
    "navigation_private_native": 5837456,
    "navigation_replay_native": 4584,
    "component_old_replay_native": 5616,
    "component_private_native": 15248,
    "component_actual_native": 656,
    "component_repeat_native": 656,
    "backend_old_replay_native": 0,
    "backend_private_native": 0
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
