# Proposed separation of18 response qualification and steering-continuous handoff

SOURCE PREPARATION ONLY. No physical authority/window/model. V956 remains failed,
including its original .03 body-settle violation; this proposal cannot rescue it.

Original V90918 tests qualify bounded0.2s motion followed by2s braking. V950 later
added a final .01rad/.03rad/s wheel-neutral requirement to each response for a
future straight handoff. V953/V956 show that attempting stationary recentering
itself excites body yaw. V956 counter-yaw correction did not keep the original
.03 settling gate. Simply increasing its threshold is not acceptable.

Propose separate gates: original18 fixed commands/order/timing/vehicle unchanged,
kinematic moving mapping and hold current steering during braking. Position
.02/.04, heading.035, half-second settling.03, native speed.13/yaw.16, actual
clearance.15, contacts0/full self, control bounds/rates/root/static invariance and
complete own-control replay remain. Wheel encoders remain recorded but need not
be zero at the end of every stopping response. This removes only the later-added
neutral-completion condition, openly and prospectively; it is not identical to
V953/V956 qualification and cannot be reported as passing those old protocols.

Any future return to forward motion must use a newly certified reference whose
initial curvature matches actual steering and respects steering slew. A turned
stationary vehicle is not allowed to be presented as ready for a straight-line
handoff. Pure reference-start check is only a necessary geometric interface, not
a physical execution certificate. The forward corridor/continuation needs its
own qualification; no navigation or handoff is authorized by18response passage.

User explicitly selected this stopping definition on2026-11-09. V959 is the new
physical stage: independent90-minute maximum, first-failure stop,18 only. V958
preparation itself contains no model launcher/authority. V956 is not reopened
and its remaining time is not reused. No automatic forward handoff follows.
