# MK-MINI Phase Final Holdout 300

## Frozen protocol

- Policy: `training/phase20_unknown_obstacle_adaptation/checkpoints/stage_b_randomized/phase20_stage_b_325000_steps.zip`
- Baseline: Phase21 v11
- Proposed method: Phase22 v1 continuous corridor
- Seeds: 22800–23099
- Paired episodes: 300
- Training: false
- Post-holdout tuning: forbidden
- Strict collision: robot sample points + map penetration (0.02 m) + physical obstacle contact

## Main result

| Method | Safe success | Collision | Env timeout | Wall timeout | Planner P95 |
|---|---:|---:|---:|---:|---:|
| Phase21 v11 | 165/300 (55.00%) | 57/300 (19.00%) | 0 | 78 | 11.08190059498883 s |
| Phase22 v1 | 214/300 (71.33%) | 65/300 (21.67%) | 1 | 20 | 22.725684179519888 s |

## Paired statistics

- Scenario mismatch: 0
- Phase22-only success: 50
- Phase21-only success: 1
- McNemar exact p (safe success): 4.618527782440651e-14
- Safe-success difference (Phase22 - Phase21): 0.16333333333333333
- Paired bootstrap 95% CI: [0.12333333333333334, 0.20666666666666667]
- Collision difference (Phase22 - Phase21): 0.026666666666666672
- McNemar exact p (collision): 0.2429849540349096

## Confirmatory decision

- Accuracy/safety confirmatory gate: False
- Phase22 v1 real-time 1.5 s P95 gate: False
- Interpretation: FINAL_HOLDOUT_DID_NOT_CONFIRM_PRE_REGISTERED_GAIN
- Post-holdout tuning allowed: false
