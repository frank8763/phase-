# RP-CCR: execution-consistent recovery under partial observation

Working manuscript, 7 November 2026. Internal research draft, **not submission ready**. RP-CCR retains the project's existing meaning; no new English acronym expansion is asserted. Planned components below are distinguished from implemented historical versions. Quantitative superiority, final-model dynamic acceptance and real-robot performance remain unestablished.

## Abstract — working problem statement, results pending

Reactive navigation can fail to complete a task even when individual motion prefixes admit finite collision-avoidance backups. This work studies the coordination of obstacle information, executable recovery corridors and control handoffs for an Ackermann mobile robot under limited visibility and actuation delay. We investigate RP-CCR as a recovery method integrated with a mature navigation stack. The intended mechanism selects recovery references together with dynamically executable controls before the validity of a retained backup is exhausted, and commits a replacement only after time-aligned feasibility checks. The evaluation will separate vehicle-model qualification, ordinary navigation performance, mechanism ablations and held-out confirmation. At the present development stage, a genuine Nav2 software integration succeeds in a nonphysical interface test, while native vehicle qualification exposes an internal assembly-contact defect. This observation motivates model validation before further method comparisons. Final comparative and hardware results are pending; this abstract makes no superiority or recursive-safety claim.

## 1. Introduction

A safe finite motion and sustained task completion are different requirements. A mobile robot may safely execute a certified braking or retreat sequence yet end in a configuration from which no tested continuation satisfies its uncertainty-dependent constraints. Partial observation makes this distinction particularly relevant: stopping the robot does not stop a moving obstacle, and an uncertainty set can expand while the robot is waiting.

The research question is whether coupling recovery-corridor selection, progress and executable control handoffs reduces these deadlocks within a practical computation budget. Our scope is an Ackermann platform with limited-range measurements and explicitly declared obstacle-motion bounds. The proposed contribution must be evaluated against mature planning and control, rather than against an intentionally weak nominal tracker. We therefore use Nav2 as infrastructure and retain RP-CCR as the method under investigation.

The intended contributions are: (i) an execution-consistent formulation relating finite obstacle bounds to full-body motion and actuator constraints; (ii) a recovery-selection mechanism that explicitly examines finite continuation rather than only the ability to stop; and (iii) deadline-aware commitment and evaluation of retained and replacement controls. These are research targets, not completed claims. Integrating an existing navigation framework, repairing simulation geometry and implementing generic predictive filtering are not counted as algorithmic novelty.

## 2. Related work and differentiation

Navigation2 provides behavior-tree orchestration and a modular ROS2 navigation system, with real-world operation reported by Macenski et al. [1]. MPPI/IT-MPC provides a mature sampling-based optimization approach, including autonomous-driving experiments [2]. PRIEST combines sampling with feasibility-directed projection [3]; a vehicle-compatible implementation is required before using it as a measured baseline here. Predictive safety filtering already separates nominal control proposals from model-based constraint enforcement [4]. Consequently, merely adding a backup or uncertainty-aware check to a nominal controller is insufficient to establish our novelty.

The unresolved differentiation is the particular coupling of finite recovery progress, changing causal information and time-consistent executable handoffs. A full-text novelty review and experiments are still needed. Sources [1–4] establish relatedness and boundaries; their performance or guarantees are not transferred to our implementation.

## 3. Problem and assumptions

Let x contain robot pose, velocity and relevant actuator states, and let u be the actual actuator command. The plant evolves under a declared model class with input-amplitude and input-rate limits. The occupied robot region F(x) includes every collision-enabled body component, including wheels and the parked manipulator; a point or circular base approximation is insufficient for final safety evaluation.

At time t, causal measurements produce a set C_t of possible obstacle **centres** for an obstacle with declared radius r. Static occupied geometry is S. A speed bound v_o expands C_t to C_t ⊕ B(v_o τ). This centre-set convention avoids counting the obstacle radius twice. Measurement error, robot-state uncertainty, execution delay and model error must be included explicitly. Ideal simulator odometry is an evaluation assumption, not a real-robot localization result.

The current development course uses one small actor with a public 0.08 m/s Euclidean speed bound, 3 m sensing and a fixed dropout model. This does not imply coverage of a broader per-axis motion class, arbitrary occlusion, multiple actors or arbitrary maps. The pre-detection reactive contract is weaker than a guarantee against every possible unseen actor. An independent probability of dropout does not supply a deterministic maximum blind interval.

## 4. Finite-time geometric condition — conditional draft

For a candidate control sequence U, let R_U(τ) be a tube enclosing the robot's occupied set at physical time t+τ, including execution error and any delay before the new command can take effect. Let

D_t(τ) = C_t ⊕ B(v_o τ + r).

If C_t contains the true obstacle centre at t, the stated obstacle-motion bound holds, and R_U encloses the actual robot for every τ ∈ [0,H], then the conditions

    dist(R_U(τ), S) ≥ d_min,
    dist(R_U(τ), D_t(τ)) ≥ d_min,  for every τ ∈ [0,H]

are sufficient for that finite interval's separation. The argument follows set inclusion: actual occupied sets are subsets of the sets in the tested distances. This simple conditional observation is not itself a novel theorem. Current sampled native evaluations require an independently justified between-sample bound before they can be claimed as a continuous-time proof. An empirical error quantile cannot be silently substituted for a deterministic tube bound.

The interval begins at the current physical time, not at the completion of a solver. If a command may remain queued or retained for δ seconds, R_U must include those δ seconds and the obstacle set must advance over the same absolute time. Checking a trajectory as though it began immediately after an asynchronous solver finishes is insufficient.

The present system does not establish an invariant terminal set. A finite braking suffix therefore does not prove recursive feasibility or eventual arrival. These stronger claims are excluded unless separately justified.

## 5. RP-CCR mechanism — design to validate

The system maintains a reference corridor, a retained executable control sequence, its absolute validity interval, and causal information provenance. New candidates pair a reference with a legal control prefix and finite recovery continuation. A candidate is evaluated for full-body separation, executable actuator limits, progress and the feasibility of a predefined finite continuation. Lack of a tested continuation means lack of a witness within the specified candidate set, not proof that no physical solution exists.

The replacement is transactional: the active reference, executable command sequence and certificate interval change together after successful revalidation against the latest state and timestamp. A late, stale or rejected proposal leaves the retained sequence intact. At expiry, the system reports the finite contract's limitation; it cannot assert that emergency braking is indefinitely safe against a moving obstacle.

The research hypothesis is that preparing such replacements before the active sequence's usable margin collapses reduces safe deadlocks. An ablation must isolate the continuation check and trigger from changes to the nominal controller, actuator model, sensing and compute budget. Previous finite-tail variants have failed; the new integration cannot inherit a success claim from their components.

## 6. Implementation and runtime evaluation

Nav2 supplies the ordinary planner/controller/behavior infrastructure. The current integration uses Smac Hybrid and MPPI with an Ackermann model. Native physics and low-level actuation advance continuously at 100 Hz; a 20 Hz navigation target is evaluated by measured timestamps, not assumed from configuration. Proposed GPU acceleration is optional and must have its model error and resource budget reported.

Record sensing age, solver start/end, verification time, candidate age at commitment, actual actuator application and deadline violations. Separate online computation from offline replay, evidence compression and audit. A fair comparison gives all methods the same robot model, control authority, physical task, observation mechanism and hardware budget. Common offline physical evaluation does not require imposing our internal safety optimizer on every baseline.

## 7. Current evidence and planned evaluation

| Evidence | Status | Permitted interpretation |
|---|---|---|
| V657 historical static benchmark | 23/24 within its frozen finite benchmark | Historical version; one failure remains; not final-model dynamic evidence |
| V827 historical three-route development | Two new mains plus reused NS reference, three complete repeats | Development/repeat evidence; no new independent confirmation denominator |
| V828 dynamic confirmation | 8 attempted, 6 complete chains, 2 failures, 16 unexecuted | Failed/incomplete original campaign; no full-24 success rate |
| V855 later dynamic development | One failed WE main; 1.40 m remaining | Preserves finite feasibility/compute failure; not a completed dynamic method |
| V856 genuine Nav2 software interface | 6 m analytic task in 40.23 s; max lateral 0.0587 m | Interface/kinematic test only |
| V856 native actuator qualification | 0.20 m/s command, mean 0.0961 m/s; internal contacts | Failed native controller/model qualification; no Nav2 scene navigation |
| V857 assembly-filter model query | Physical arrays preserved; exact two-pair contact change; external collision fixtures retained | Zero-integration model-query qualification only |
| V857 original-model replay | One exact state step; serialization comparison error stopped batch | No corrected-model motion, causal speed improvement or full replay established |
| Final-model algorithm comparison and held-out confirmation | Pending | No superiority estimate |
| Real robot | Pending | No sim-to-real or deployment claim |

The planned comparisons include genuine Nav2 MPPI, a second qualified Ackermann-compatible controller and RP-CCR on the same infrastructure. Mechanism ablations isolate finite continuation, early recovery triggering and optional learning proposals. Confirmation uses a previously unused locked task set, with development, error calibration, complete repeats and held-out outcomes counted separately.

Primary outcomes are strict arrival, physical contacts/penetration, minimum clearance, deadlocks, completion time, travelled distance and deadline violations. Failure timeouts remain part of the denominator. Reporting only completion times among successes would hide failed trials; paired rescue/harm and censored outcomes must be explicit. Trial count is an experimental design choice, not a journal-specified acceptance rule.

## 8. Vehicle model validity and limits

The present simplified vehicle model places front wheel collision cylinders within the chassis collision box. Front-wheel steering introduces an intermediate body, so parent–child contact filtering differs from the rear-wheel hierarchy. V856 saved states show sustained front-wheel/chassis contacts. The V857 candidate excludes only those mechanical assembly pairs and preserves external collision geometry, but its speed effect remains untested after an interface error stopped the experiment.

A contact-filter correction is an engineering intervention, not evidence of algorithmic improvement. Real-robot geometry, wheel/ground parameters, actuator response and localization must still be checked. Any later comparison must use the same final model for every method; old outcomes cannot be combined with a changed model as homogeneous trials.

## 9. Discussion and conclusion — pending results

The current evidence supports studying finite safe recovery and sustained progress as separate questions, and it demonstrates the need to validate the vehicle model before interpreting controller failures. It does not establish that the proposed RP-CCR integration outperforms a mature navigation baseline. A defensible RAS submission requires final-model dynamic results, controlled ablations, equal-budget comparison, measured runtime behavior and application validation. The manuscript should be revised around the mechanism that survives those tests, even if that requires dropping an intended claim.

## References

[1] S. Macenski, F. Martín, R. White, J. G. Clavero. The Marathon 2: A Navigation System. IROS 2020. https://arxiv.org/abs/2003.00368

[2] G. Williams, P. Drews, B. Goldfain, J. M. Rehg, E. A. Theodorou. Information Theoretic Model Predictive Control: Theory and Applications to Autonomous Driving. https://arxiv.org/abs/1707.02342

[3] F. Rastgar, H. Masnavi, B. Sharma, A. Aabloo, J. Swevers, A. K. Singh. PRIEST: Projection Guided Sampling-Based Optimization For Autonomous Navigation. https://arxiv.org/abs/2309.08235

[4] K. P. Wabersich, M. N. Zeilinger. A predictive safety filter for learning-based control of constrained nonlinear dynamical systems. https://arxiv.org/abs/1812.05506

[5] MuJoCo 3.9.0. Collision filtering and MJCF contact exclusion reference. https://mujoco.readthedocs.io/en/3.9.0/computation/index.html#selection
