# Proposed V950 measured steering response and forward handoff qualification

Prepared for the user's request to solve ordinary reversing and failure to resume
forward. This is a NEW proposed bounded qualification; V945 is closed and not
reopened. No models are authorized until the user confirms the new window.

If authorized: lock one independent90-minute wall-clock deadline before first
model initialization. First functional/safety/source/evidence failure closes the
whole qualification. No repair, repeated case, new candidate or deadline reset.
One CPU, one instance, execution lock, all actual models/steps/replays through
run_phase.sh. Restore the original REVIEW_PENDING bytes in finally. No navigation
or 24 confirmation even if this qualification passes. Models/actual/replay/private
counts are separate; interrupted unobserved counts remain unknown.

Same original vehicle,19static bodies, sensor/noise and single declared actor;
only V949 adapter changes. First the original fixed18 V909 response cases in
original order:200native warm,20requested,200brake=420each. Original full native
clearance>=.15, contact0, control/rate, static geometry and no root write, full
qpos/qvel/ctrl/mocap own-control replay<=1e-8, body speed/yaw and settle gates.
Position residual remains .02m aligned/zero or .04m actual direction reversal;
angle<=.035rad. All cases additionally require measured steering position<=.01rad
and velocity<=.03rad/s at the final stop. No reused old response counts as a new pass.

Only if all18 pass: one predeclared complete handoff case, same true t0.200ticks
forward right-curved [.1,-.0758770385], then200zero to stop/neutral; require actual
body and measured steering neutral, then200forward straight [.1,0], then200zero.
No initial pose/root restoration in the case. Straight segment follows the actual
stopped pose; throughout200forwardticks compare the unassisted nominal straight
reference: position<=.04m/heading<=.035rad. Require actual forward goal-axis
progress>=.15m and no reversing request. All800ticks native safety and full own
control replay required. This is a component qualification, never route arrival.

Per response child<=60s; handoff<=90s; absolute root deadline always tighter.
Actual maximum8360native plus8360own replay; private0, navigation0, training/SAC/
realrobot/Stage0. Exact models attempted and finished/unknown counts recorded.
Keep necessary raw in same-repo Release, downloaded/member SHA before local
cleanup;2GiBtemporary cap. No automatic full route or additional candidate.
