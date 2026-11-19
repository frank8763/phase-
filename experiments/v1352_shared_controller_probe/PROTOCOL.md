# V1352 fixed saved-input controller comparison

Authorized by the user's “好，开始下一步的实验”, following V1351 steps1–2.

This finite software experiment has exactly six cases, ordered saved1 RPP/MPPI,
saved4 RPP/MPPI, saved8 RPP/MPPI. Each case starts a fresh actual installed Nav2
controller server. No vehicle construction, MuJoCo, physical integration,
training, Stage access, new tasks, parameter search or automatic physical launch.
REVIEW_PENDING is preserved byte for byte. Software root600s, worker60s,
temporary storage128MiB. Serial measurements on Phase CPU3, nice19, one math
thread, GPU hidden, isolated ROS/bubblewrap namespace.

## Common information and authority

Use the frozen V1350 mode0 paths for the V1348 requests1/4/8. Reuse their existing
dense geometry audits; these are progress prefixes, not complete-goal routes.
Select the first constant incoming-edge gear segment, keeping every pose and
yaw on that segment. Both controllers get identical path bytes, measured body
pose converted to rear axle(-.30m), last actual32-ray scan at or before request,
public static grid plus the same request's causal speed-bound ball. Rasterize
every cell intersecting that ball conservatively, without actor truth.
The map is a software costmap representation, not an exact geometry certificate.

Hold pose and scan stationary and set odometry velocity to zero for this
explicit synthetic saved-state fixture; retain original measured velocities,
sensor pose/time and snapshot age in provenance. Republished timestamps describe
software playback, not renewed real observations or dynamic forecast coverage.
The frozen ball does not expand with wall playback time. Fresh server per case
prevents costmap/optimizer state carryover. Same20Hz command /10Hz costmap,
6x6m rolling5cm grid, Minkowski15cm footprint, scan and inflation configuration.
Same segment endpoint checker(.08m) is a component checker; original task goal
(4,-2), arrival radius.45 is recorded, not replaced by the prefix endpoint.

Actual installed engineering-adapted ExecutableRPP vs DeadbandMPPI with the
registered coherent yaw sampler. Preserve existing controller-specific parameters
and disclose these adaptations. This is shared-framework controller comparison,
not canonical upstream implementations or controlled superiority over V1281.

## Outcomes, timing and stops

After map/lifecycle readiness send actual FollowPath. Collect24 raw callbacks
or a terminal result, max5s, then cancel cleanly. A controller's legitimate
NoValidControl/abort, zero output or wrong-segment direction is a recorded
functional outcome, not a reason to tune parameters. Preserve raw output;
direction mismatch maps to zero at the common adapter, never sign-flipped.
Nonfinite/speed/curvature violation, stale input at callback, action/lifecycle
infrastructure error, missing/mutated evidence or source stops the batch.

Record action dispatch-to-first raw/nonzero/admitted command and callback spacing,
including server/ROS scheduling; these are not pure optimizer compute times.
Twist has no origin timestamp: generation-to-receipt age remains UNKNOWN.
Record observation callback age and measured envelope-to-adapter time separately;
do not claim the legacy.2s envelope check proves end-to-end command freshness.

Independent readback recomputes shared input hashes, command bounds, direction
filter and envelopes, delivered costmap equality per paired input, source hashes,
and total model/native counts0. A successful software interface does not mean
navigation, physical safety, goal arrival or real-time qualification. No trial
or independent navigation success is counted. Old rounds and deadlines stay closed.
