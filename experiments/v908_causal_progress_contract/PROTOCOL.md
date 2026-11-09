# V908 causal snapshot and common progress-contract preparation

2026-11-09, zero vehicle models/integrations/navigation/training. V907 and all earlier outcomes remain closed. V907 was explicitly the last physical candidate within the existing10:38:29.771335 deadline; this preparation never starts or extends a physical window.

## Observed failures
V907 records three retreat/brake/resume cycles and then fails MAXIMUM_THREE_ADMITTED_REFUGES_EXHAUSTED,12080 actual+12080 own replay,remaining2.634226m. One resume event combines body native8985 with sensor/native8986, violating the declared temporal provenance gate; no full independent evidence PASS is claimed. Separate physical/contact/control/replay and motion-support audits pass.

All35 actual tracked ORIGINAL paths select endpoints rejected by the supervisor's current6s holding predicate. This is a retrospective comparison at the current observation, not a proof the path could never become feasible later. Of the same35 saved sources,10 have an alternative terminal witness among the original49 offsets within.24m and25 do not. Terminal existence alone is not executable-route feasibility.

## Delivered preparation
- CoherentMotionPublisher subclasses the actual production observation publisher. One RLock transaction contains the actual parent tracker update and decision-packet copy. Decision readers receive deep-copied pose/source from that transaction; source may never be newer than body; current age<=.2s remains required. Seven real-data/concurrency/negative checks pass. This seam is not yet integrated into a whole navigation driver.
- progress_gate rejects terminal choices that do not meet BOTH the original static clearance and unchanged6s holding condition, with .24+.20=.44<original.45 goal budget. Four real-record/negative checks pass. It reports no executable-route certificate.
- Genuine installed Smac probes on three actual V907 saved poses with matching6s hard global support and matching terminal witnesses all return208 under the original.5s search limit. Search downsampling5cm is diagnostic only, not adopted. Software failures are preserved; no physical candidate is qualified by these probes.

## Next method decision
Do not launch another clone with the same incompatible objectives. First separate stationary holding from moving-trajectory admission in the mathematical contract: robot occupied tube and obstacle uncertainty must be evaluated at common absolute times along the chosen control sequence, including sensing/solver/actuator delay and measured tracking/braking errors. A fixed6s standstill test at every moving pose is sufficient but can be unnecessarily restrictive; replacing it is an explicit scientific change requiring new qualification, not permission to lower the .15 actual safety threshold.

Nominal planning and recovery must optimize sustained continuation toward the original goal, not merely another retreat. Use retained real controls or a qualified vehicle-compatible predictive controller, and check the continuation before committing the reference. Do not assume GPU availability fixes semantics. First establish qualified RPP/MPPI baseline behavior on a declared open crossing development task, then the original constrained course; scene changes are new tasks, never old acceptance success. Freeze and measure each mechanism before comparisons, new confirmation or hardware.

Not ready for physical launch: missing complete unified trajectory/controller qualification and a passing production planner continuation witness. Broad user delegation supports preparing the next bounded design without a permission loop; it does not erase completed failures or extend the closed round.
