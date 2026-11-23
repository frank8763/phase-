# Current results and interpretation — 23 November 2026

This section replaces the current-status interpretation of earlier manuscript
drafts, while preserving their dated development history. It is a working
Methods/Results section, not a submission-ready superiority claim. Numerical
outcomes refer to original machine records and their independent audits;
source qualification and artifact preservation do not contribute trials.

## Evaluation protocol

We distinguish historical whole-task comparisons, exposed development tasks,
and the preregistered new-phase mechanism experiment. Results from these groups
are not pooled. A repeat on an exposed task checks reproducibility and does not
increase the number of independent tasks. Likewise, a short control-cycle
qualification does not constitute successful navigation.

The prospective mechanism experiment fixes twelve actor phases and twenty
applicable assignments before execution. Map, vehicle model, start and goal,
sensor seed, actor count and motion class remain fixed within each task; only
the actor phase changes. Four west-to-east tasks compare the complete method
against removal of the pre-execution onward check. Four east-to-west tasks
compare the complete method against zero-wait eligibility. Four north-to-south
tasks use the complete method, without an inactive ablation. The within-task
order is counterbalanced. Failed and unexecuted assignments remain in the
twenty-assignment denominator.

The onward ablation retains feedback execution of the refuge prefix,
continuous full-state shadow checks, the complete stop, and onward planning
from the measured handoff. It removes only the onward feasibility check before
prefix execution. A refuge-prefix certificate is checked against its reference
endpoint and is never substituted for arrival at the task goal. The time
ablation retains the candidate computation and changes only nonzero-wait
selection eligibility. Candidate parameters and safety thresholds are not
retuned on a failed formal assignment.

All prospective runs retain the original V1281 simulation contract: the
original conservative predictive margins, 0.15 m actual clearance floor,
0.04 m position, 0.035 rad heading and 0.015 rad steering tracking limits,
the complete 2200-native-step stop tail, contact/self/root checks, and
full-state/control/mocap replay tolerance of 1e-8. Successful navigation also
requires the original whole-goal and independent numerical/physical audit.
This is not the later weekend contract. A positive prefix safety audit does
not change a failed navigation result.

Planning, model evaluation, allocation, physics and replay are serialized on
CPU2. Each run has a 5400 s technical limit, split into 4200 s normal work and
1200 s closure, with boot-bound wall and monotonic clocks. These are per-run
limits, not an overall study deadline. The recovery counter covers only the
q1159 subset; total normal, static and other native/FFI work remains unknown.
Consequently, an equal-total-work or real-time comparison is not established.

## Historical whole-task comparison

The following completed historical cohorts retain their original method
identities and contracts. Phase21-v11 is not relabelled as the current RPCCR.

|Cohort|Method|Executed|Successes|Collisions|Environment timeouts|Wall timeouts|
|---|---|---:|---:|---:|---:|---:|
|G4C, original contract|Phase21-v11|100|47|29|—|24|
|G4C, original contract|SCCR / Phase22-v1|100|60|30|—|10|
|G4C, original contract|DWA-C3 vehicle adaptation|100|61|39|—|0|
|Final300, original contract|Phase21-v11|300|165|57|0|78|
|Final300, original contract|SCCR / Phase22-v1|300|214|65|1|20|

A dash denotes a field not separately listed in the assembled G4C table; it is
not an imputed zero.

In G4C, SCCR completed 60 tasks and DWA-C3 completed 61. Their collision and
timeout counts differ, so these data support an observed tradeoff rather than
overall SCCR dominance. In the separate Final300 cohort, SCCR completed more
tasks than Phase21-v11 (214 versus165). The stored paired safe-success difference
was16.33 percentage points, with95% paired-bootstrap interval[12.33,20.67]
percentage points and exact McNemar p=4.618527782440651e-14. Collision counts
were65 versus57, and planner-call P95 was22.73 s versus11.08 s. The original
composite and1.5 s real-time acceptance gates were not passed. These are
reported stored statistics, not a new analysis or a current-RPCCR comparison. Neither cohort establishes comparative superiority of
the current RPCCR or a result on the new-phase experiment.

Source: `runs/v1650_comparison_completion/RESULTS_BY_BENCHMARK.csv` and its
`EVIDENCE_REGISTRY.json`; Final300 outcome categories and paired statistics
are also preserved in `evidence/phase22_formal/Final300/summary.json`. The tables
are not additional experiments.

## Current author-baseline adaptations

The current DWA cycle uses a pinned PythonRobotics reference with an explicitly
disclosed Phase Ackermann admissibility mask and vehicle configuration; it is
not the unavailable historical DWA-C3 implementation. One exposed current
cycle passed 2210 actual steps and its 2210-step own replay, including the
independent numerical/control-memory/physical audit. A separate receding
whole-task attempt was refused by the unchanged predictive stop margin after
80 control steps. Its 200-step closure and replay were retained, while
independent evidence-interface gaps prevent a complete safety-audit claim.

For TEB, we retain the original HomotopyClassPlanner implementation at author
commit `9e55af4724310c34bcfa8cbb3b2783478c1a246a`. The explicit standalone
adaptation uses a rear-axle reference, a transformed vehicle polygon, current
public static geometry and scan endpoints. It preserves raw HCP output and
declares a Python port of the upstream ROS command-saturation operation. It
does not execute the complete ROS global-plan/costmap-converter plugin, and
point-obstacle costs do not replace the common full-state safety gate.

The first fresh exposed query constructed one original HCP object, called its
top-level plan once, and destroyed it once. It returned
`NO_OPTIMIZED_SELECTED_TEB`, with zero returned classes and trajectory samples.
No TEB control was executed. The original 200-step zero-command closure and
200-step own replay completed with state/control/mocap error 0 and contact
mismatch 0. Recorded actual minimum clearance was 0.31498918194116166 m;
the goal remained 8.000063036649994 m away. The full independent actual
numerical audit was not executed after refusal. Internal optimization and
iteration counts are unknown. This is a finite negative result for this
declared adaptation and input, not global infeasibility or a general failure
of the author algorithm. The input, parameters and seed were not changed to
rescue the outcome.

The current SVG-MPPI adaptation likewise retains a predictive-margin refusal
after five actual control steps, followed by 200 closure steps and exact own
replay. These exposed component outcomes cannot be converted into a shared
whole-task success-rate table. RPP/MPPI evidence comes from separately stated
versions and cohorts; PRIEST car mapping remains unresolved. PSF and PCBF are
literature baselines without completed vehicle comparisons. Listing ten
method identities does not imply ten completed experimental comparisons.

Detailed current records: `docs/ALGORITHM_COMPARISON_COMPLETION_20261123.md`,
`docs/TEB_ACTUAL_CURRENT_CYCLE_V1739_REPORT.md`, and the original per-run results.
Bibliography keys already verified in
`baseline_support_20261118/REFERENCES.bib` include `rosmann2017teb`,
`macenski2023rpp`, `williams2018mppi`, `rastgar2024priest`,
`wabersich2021psf` and `wabersich2023pcbf`. Verified DWA/SVG-MPPI additions
are in `REFERENCES_ADDITIONS_20261123.bib` (`fox1997dwa`,
`honda2024svgmppi`); their primary-source check is recorded in
`BASELINE_BIBLIOGRAPHY_CHECK_20261123.md`.

## Mechanism results and remaining claims

The exposed V1281 fixed24 and its three repeats are development/reproducibility
evidence. They do not supply unseen new-phase or mechanism-ablation evidence.
The first locked new-phase pair has closed without arrival in either variant:
the complete method refused a current whole-goal source, and the onward
ablation refused an onward source at the measured handoff. Their independent
prefix audit gaps remain disclosed; neither is silently repaired or rerun.

The second locked pair, phase02 at4.551718764234382 rad with sensor seed10060001, has now closed under the same frozen V1649 source. Both variants executed39320actual steps and39320own replay steps, with replay error0, contact mismatch0, independent actual-prefix safety auditPASS, no secondary errors, and final goal distance2.534647053805079m. Both refused a measured-handoff onward source. All saved physical state/control/mocap/time, body requests and clearance/self-margin traces are identical; no execution divergence is observed. Initial complete states and public setup are also identical, apart from genuine wall measurement times in packets. This phase provides no observed completion benefit from the pre-execution onward check.

The full method did perform its extra nominal onward check: a8700-step nominal complete reference with2600-step prefix was accepted, but measured-handoff finite search later returned no source (3571nodes,0terminal attempts, best distance0.599417m). The actual handoff differed from the nominal point by6.57mm in position,0.000149rad in heading and0.001067rad in virtual steering, all within the original tracking limits. These data show a boundary between a nominal onward witness and successful replanning from the actual handoff. State/memory deviation, observation/source renewal and finite-search incompleteness have not been causally separated; no unique failure cause or global infeasibility is inferred. The full method adds4174900tracked CPP and12200tracked Python recovery-model native steps in this pair; total model work remains unknown.

See `docs/RPCCR_PHASE02_PAIR_20261123.md` and the saved pair analysis and PDF/PNG figure. The two plotted curves coincide exactly. Six of the twenty assignments are closed without a complete success. Four did not arrive; phase03 no_onward recorded arrival and stopping but failed the full independent source-proof audit; phase03 full was technically censored before numerical admission. Fourteen assignments have not started. The earlier phase01 audit gaps remain explicit. No new repeat or independent task is created by analysis/figure export.

The paper still requires completed applicable mechanism contrasts and faithful
common-task external comparisons before claiming which mechanism improves
completion. Generalization is limited to phases of the same known course,
model and single-actor motion class. New-map, multi-actor, statistical,
real-time and hardware claims remain unsupported by these results.


## Phase03 interim result: recorded arrival with failed complete audit

The no-onward assignment completed44875actual steps and44875own replay steps
with zero maximum replay error and no contact mismatch. The recorded final
goal distance was0.276449900m, with final translation speed2.15e-7m/s; the
minimum actual clearance was0.276984656m and no bad contact was recorded.
The original base native audit reviewed all44875rows and returned controller
and memory errors of2.220446049250313e-16. However, the complete independent
audit refused `REBUILT_SOURCE_PROOF`. The canonical outcome therefore remains
not passed; recorded arrival is not substituted for the required complete
audit. The paired full assignment was subsequently censored before numerical admission.

Saved-source inspection identifies a separate audit-scope issue: the flagged
no-onward initial reference is a local refuge prefix, while another full-audit
path rebuilds its proof against the whole task goal. Its saved endpoint is
2.546081537m from that goal. The caught assertion did not retain the complete
failed-check set, so source inspection is not presented as a numerical
re-audit or a retrospective pass. The old result and all safety gates remain
unchanged. The full assignment refused a monotonic duration of5400.000000000007s against the immutable <=5400s entry bound, before numerical imports or factory execution. Its canonical owner counts remain null and no machine RESULT is reconstructed; a separate exact-source/console record derives zero factory, physical and replay calls. Both outcomes are retained, and this pair cannot establish a mechanism advantage.

## Discussion: what the present evidence establishes

The distinction between admissible execution and continued task completion is
central to interpreting these experiments. In phase02, independent numerical
auditing of the executed prefixes and exact replay succeeded, while both
variants failed to reach the goal. These findings support the recorded
prefix checks; they do not establish a guarantee of eventual arrival. A
refusal to supply a new command must therefore remain a functional
non-success even when the resulting recorded stop is collision-free.

The additional onward check in the complete method was active, rather than
skipped by this task. Its accepted nominal continuation did not lead to a
different actual trajectory or successful replanning at the measured
handoff. A nominal continuation from a reference state is consequently
insufficient evidence, in this case, for successful continuation after
execution. The saved handoff deviation was within the unchanged tracking
limits. This observation motivates examining the relationship between
nominal continuation and measured-state renewal; it does not isolate whether
state and controller-memory differences, renewed observations, or finite
search caused the refusal. No counterfactual rollout was performed to assign
a unique cause, and the registered experiments were not tuned after failure.

The result also limits the efficiency claim. The complete method performed
additional tracked recovery-model work without an observed completion
benefit in phase02. The instrumented subset is not a complete accounting of
normal planning, static processing, other foreign-function work or internal
optimizer iterations. We therefore report the subset explicitly and make
no equal-total-work or overall computational-efficiency claim from it.

External-method component tests answer a different question from the
registered mechanism contrasts. An adapter refusal or failed current query
characterizes the stated implementation and contract. It is not evidence
that the published algorithm is globally incapable, nor a substitute for a
shared whole-task comparison. Historical SCCR/DWA results retain their
original task populations and evaluation contracts. Pooling them with the
current RPCCR phase experiments would confound the method with the test
conditions.

## Provisional conclusion and completion conditions

The current implementation has reproducible exposed-task evidence and
explicitly audited new-phase execution prefixes. The completed phase02
contrast does not show an arrival benefit from the pre-execution onward
check. The remaining registered contrasts and common-contract external
comparisons are required before a paper can claim a mechanism improves task
completion. The final contribution statement must follow those results,
including negative outcomes and technical censoring. The present manuscript
is a working draft and is not submission-ready. A concrete completion
checklist is recorded in `docs/PAPER_REMAINING_STEPS_20261123.md`.
