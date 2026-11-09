# V949 actuator handoff source/array qualification only

V945 exact13517 adapter reconstruction proved zero Twist retained nonzero steering,
and complete straight recovery exceeded its .035rad heading gate. This source
candidate addresses the mechanism: zero/stale Twist slews both steering servos
to neutral with zero wheel target; moving Twist uses Ackermann curvature
feedforward without the extra body-yaw P loop inside the already closed RPP loop.
Original longitudinal PI, actuator bounds and per-second slew remain unchanged.

The next recovery handoff must inspect measured steering joint position AND rate,
as well as stopped body velocity, before constructing/installing a new reference.
Steering commands alone are not encoder measurements. Missing/nonfinite/stale
proprioception fails closed. No steering-position/root-state writes are permitted.
Reverse escape is disabled in V948; future reverse-to-forward transition must use
this measured stop/alignment gate before a fresh forward plan towards original goal.

This stage only re-evaluates saved adapter inputs and explicit constant-straight
test data. No model, dynamics integration or physical replay is performed. Reused
V909 response measurements DO NOT qualify this changed adapter. New bounded
physical response/stop/turn/hand-off tests and complete control replay are required
before a full route. Original .15 safety and error gates are not reduced.

Keep old failures and all preparation errors, REVIEW_PENDING and closed windows.
No new model deadline/authority, navigation, training, real robot or 24 confirmation.
