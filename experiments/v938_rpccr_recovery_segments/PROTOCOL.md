# V938: reference-loss recovery segments, zero-model qualification

User 2026-11-09 authorizes changing RP-CCR to actively construct an executable recovery corridor. Success cannot be guaranteed. V934 physical failure and V936/V937 unqualified complete-corridor searches remain unchanged. This stage creates no vehicle models, initializations, integrations, control replay, training, hardware execution or new physical window. No Stage access, agents or external messages.

## Scientific change

Normal-reference loss is an explicit recovery entry, independent of a rejected nonzero Twist. A complete static route to the original goal is searched with the frozen V936 analytic Ackermann search. RP-CCR extracts the connected initial segment whose entire oriented body, including the original worst-case .04 position/.035 yaw/age/delivery reserve and edge interpolation allowance, separates from the current causal **whole-cycle** actor enclosure. This is an actively constructed reference, not an override of collision-monitor zeros. Every eventual actual command still requires the original V934 finite-command/stop/all-cycle endpoint admission.

Fixed policy before qualification: maximum segment 1.2 m, minimum goal-distance improvement .6 m, original .155 predicted/.15 actual clearance, original curvature .758770385, original goal .45, original RPP controller configuration. A corridor is only an independently qualified reference proposal; kinematics do not establish actual tracking. If a complete goal route is not dynamically certified, return `RECOVERY_SEGMENT`, never goal success. If the connected prefix is too short, stop with `NO_CERTIFIED_PROGRESS_SEGMENT`. No speculative crossing, reduced margins, timed jitter assumption or oracle actor state.

The segment terminal retains whole-cycle stopping qualification. This preserves the prior conditional safe-waiting geometry, unlike V937's unqualified finite-time alternative. It does **not** guarantee information gain, future progress, recursive safety, or eventual goal reachability. New observations may shrink the causal set; until independently demonstrated, improved future visibility is a hypothesis. No synthetic future scan is represented as an actual observation.

## Handoff transaction

`NORMAL -> CANCEL_PENDING -> STOPPED_REVALIDATION -> FOLLOW_RECOVERY -> STOPPED_REPLAN`. Acknowledged cancellation of normal navigation and fresh stopped body/source are mandatory before installation. The installed path starts at the actual pose, is independently revalidated against the current causal enclosure, and is sent once to `FollowPath`, retaining the original goal separately. Periodic normal replans cannot overwrite the committed recovery segment. Action completion alone is insufficient: stopped state, endpoint proximity and measured progress are required. Then original-goal planning is requested from a fresh observation. A retry after a failed original-goal plan requires a newer causal periodic update; no identical zero-progress loop.

Any stale/future/nonfinite source, pose drift, partial certificate, cancel rejection, action rejection, safety fault or progress timeout fails closed. A clock is not a certificate. Unchanged command/native safety checks remain mandatory in a future production binding.

## Fixed saved inputs and release limits

Test the original first trigger (V934 tick4947) and the already selected V936 ticks6999/10999/16999; no state, seed or phase replacement. Freeze this source and exact inputs before the four geometric tests. Independently audit dense analytic arcs using separate polygon geometry, all-cycle enclosure reconstruction and stopping endpoints. Exercise the transaction with actual saved entry and adverse callback/source fixtures. A separate real installed RPP software action test is required before calling ROS binding ready. This stage has no physical authorization; software positives are not navigation success or new24 acceptance.

Necessary source/report/summaries go to Git, selected reproducibility inputs to the same-repository Release with download/member-SHA verification before cache cleanup. Cache <=2 GiB; no raw >90 MiB Git blobs. Preserve errors and unqualified results. REVIEW_PENDING remains byte-identical; frozen current/runtime/networks untouched.
