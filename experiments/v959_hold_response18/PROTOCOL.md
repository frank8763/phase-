# V959 original18 steering-hold response qualification

User explicitly selected “保持轮角刹停，转向交接另验（推荐）” after reviewing
the V956 failure and proposed V958 source/zero-model qualification. This new
prospective contract removes only the later-added requirement for final steering
neutrality in every stopping response. All steering encoders remain recorded.
V956/V953 failures and their deadlines/denominators remain unchanged; no old
physical trial or failed protocol is regraded. This is not V956 qualification.

One new independent90-minute maximum locked before model initialization. Same
original18 tasks/order, true t0 per case, warm200/requested20/brake200, one model
per task, 420actual+420own replay each; maximum7560actual/7560replay/private0.
Vehicle, static19, actor/sensor/noise/model unchanged. Moving V949 kinematic
Ackermann/longitudinal PI; stopping holds current steering while drive targets
zero. No stationary centering, no alignment counter-yaw actuation, no new path
or navigation. Fixed reverse response cases remain platform qualification only.

Required: .02m aligned/zero or .04m reversal position residual; .035rad heading;
native speed .13/yaw .16; within.5s body speed/yaw<=.03; native clearance>=.15;
bad obstacle/penetration/unknown/self contacts0; full self containment, original
control limits/slew, static geometry invariant/no root rewrite; complete own
qpos/qvel/ctrl/mocap replay<=1e-8. Final steering position/velocity is descriptive,
not a neutral-completion pass gate. Turned stopped wheels do NOT qualify a new
straight handoff: actual-steering-compatible forward reference/continuation
requires separate physical qualification and is not automatically started.

Zero-model actual worker/evaluator loop for all18, original real failure array
reconstruction, explicit retained old-failure verdict, prospective contract
boundaries, original real write_guard/child-parent roundtrip, full12s+2s handoff
late-negative evaluator fixtures before freeze. Fixtures are not model responses.
No physical handoff/new24/full route/training/realrobot in this authorization.

First function/safety/source/model/state/control/coverage/evidence/interface
failure stops and closes the stage. No frozen repair, extra candidate, rerun,
replacement or extension. All model initialization/integration/replay only
run_phase.sh singleCPU/model lock; child60s/outer70s/root immutable90min.
Finally restore REVIEW_PENDING original bytes and close model authority. Exact
or unknown accounting preserved. Independent zero-model audit, report, necessary
Git source/metadata and same-repo Release with all downloaded/member SHA verified
before listed raw cleanup. Temporary<=2GiB; one new source push<=30s+remoteHEAD<=5s,
no old synchronization retry. Component18 pass does not equal dynamic acceptance.
