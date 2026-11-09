# Final-method evidence gates and paper deliverables

Status2026-11-09: execution plan, not completed experiments. User delegates progress; current physical round retains its original absolute10:38:29.771335 ceiling. No extra navigation is authorized by this document alone. Old failures remain part of history.

## Gate1: stable closed-loop method
Freeze final vehicle/sensor/nominal controller/recovery algorithm. Complete all three original development routes and full same-configuration repeats. Native safety>=.15,full-body/contact/legal amplitude/rate/no root rewrite/causal sensing/own-control replay remain independently evaluated. Failures produce a ranked diagnosis and exact saved reproduction; no task/seed replacement. Navigation repeats in an asynchronous ROS stack need not have identical trajectories; each own replay must be exact and both runs must meet functional/safety gates.

Stop interpreting a geometric witness as an executable controller certificate. Report assumed travel speed, measured tracking error, solver age and braking response separately. Terminal holding must be finite and actually observed. Performance of an architecture that uses soft reference costs and hard local prediction does not establish a formal invariant.

## Gate2: independent dynamic confirmation
Before any new confirmatory navigation, publish task manifest/hash, all denominators,success definitions,stopping rules and timing budget. The historical10060001–24 pool was partially executed duringV828 and repeatedly inspected; it is development history, not a fresh held-out pool. Keep those failed outcomes. A final-version independent pool must be newly preregistered and include balanced routes/directions/phases, not selected for likely success. Three routes on one map do not establish multi-map generalization.24 is a limited engineering threshold, not a journal rule or proof of high reliability. Do not reuse confirmation outcomes for tuning and still call them held out.

## Gate3: qualified paired comparisons
Use the same robot,nominal limits,known map,original sensor noise/dropout stream,actor specification,start/goal,physical termination and hardware. First qualify each baseline separately without ranking performance. Required: standardNav2RPP baseline,vehicle-compatible Nav2MPPI,our complete mechanism. PRIEST is optional only after faithful vehicle-compatible implementation and qualification; otherwise omit rather than include a broken comparator. Give comparable online resources and report actualCPU/GPU and end-to-end latency,not onlysolver kernel timing. Do not force every comparator to use our internal safety optimizer; evaluate them with common independent physical criteria.

Use paired task outcomes: rescued,harmed,bothpass,bothfail; report failures/timeouts,not only mean time among successes. Keep development,parameter calibration,repeats and heldout trials separate. Randomness/repeatability in middleware is a limitation to quantify. Report uncertainty intervals and use enough independent task geometries to support the actual claim; no percentage superiority without measured paired evidence.

## Gate4: mechanism ablations
Preregister one mechanism removed at a time: early finite-recovery trigger;retained admitted/executed reference consistency;temporary terminal region with actual braking/new observation;causal prediction versus observation-only. Run all with matched nominal navigation/map/limits and budgets. Negative effects as well as gains must remain. Component unit checks are not ablation experiments. If the gain is only model repair or replacing an immature controller with RPP, revise the contribution accordingly.

## Gate5: runtime, robustness and hardware
Measure sensor age,planner latency,verification cost,command application,control-period misses,max/p50/p95/p99 and memory/disk. The current100Hzplant/20Hzcontrol configuration is a target,not proof of hardreal-time. Holdout layouts and controlled observation/actuation/delay disturbances must stay inside clearly declared assumptions; do not assert arbitraryocclusion,multiactor or broader.12-axis bounds from the single.08Euclidean actor course.

Only after simulation gates: integrate actualvehicle localization,laser,drive,steering and emergency stop. Validate shape/model response and low-speed stop/turn/retreat error on the PC/GPU hardware. Real localization is not simulator ground truth. Expand physical tasks progressively with an operator and documented safe test area;无人值守 refers tosimulation only.

## Gate6: manuscript delivery
Rewrite final method equations/algorithm to match the implemented winner,including all assumptions and exclusions. Deliver complete results tables,paired outcome plots,runtime distributions,representative successful/failed traces,ablations,limitations,relatedwork and reproducibility records. Git stores small source/metadata/reports;fullraw evidence in verifiedRelease archives,with restoration recipe. Final draft must clearly label historicaldata and unexecutedexperiments;submission-ready status requires completed results,not merely prose. RAS acceptance cannot be promised.
