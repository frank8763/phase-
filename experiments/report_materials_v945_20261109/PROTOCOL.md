# V945 saved-state visualization only

User requests seeing why the last under2m failed, with path lines. No new scientific
run, navigation, prediction, training, or model integration is authorized here.
Restore only the already remote-verified main_we record. Sources stay immutable.

Create a whole-run4x overview and last-under2m1x detail, using saved native
qpos/qvel/ctrl/mocap/time only. MJB is loaded solely for offline rendering;
mj_step/step1/step2/rollout are blocked. mj_forward may update derived rendering
coordinates but every frame must preserve all saved state/control/time exactly.
Blue actual path; green most recently published saved plan at the frame's recorded
wall clock; purple actual recovery segment reference. Actor display is evaluation
truth only and does not become a controller input. Static rectangle catalog uses
half extents, checked against the scene convention. Never animate invented progress.

Render through run_phase.sh in Phase namespace, exclusive execution lock/singleCPU,
600s inner/605s outer cap. Temporarily release REVIEW_PENDING only for this renderer
and restore its original bytes in finally. Metadata must distinguish render model
load from zero new integrations. Preserve scientific NOT_PASSED and original audits.

Decode every video frame and inspect PNGs. Save input/media SHA and event/source
provenance. Publish visualization source/metadata and selected PNGs in Git and media
as separate assets in the same repository Release, verified by download SHA before
removing restored raw cache. This new media-only publication is not a retry of any
old scientific sync. Keep playable local media for the user's requested review.
