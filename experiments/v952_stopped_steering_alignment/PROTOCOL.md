# V952 stop, then steering alignment: source qualification

New user instruction after closed V950/V951: continue the next repair. Old
failures, metadata exception and21:50:02.974deadline remain closed and unchanged.
This preparation creates no model/window authority.

One behavioural change from the original V856/V884 platform adapter: retain its
EXACT moving PI/yaw/Ackermann mapping and its held-steering zero-drive braking.
Only after measured body |v|<=.005m/s AND |yaw-rate|<=.005rad/s for10consecutive
native ticks, allow zero-drive servo neutralization. If either body measurement
exceeds those bounds, stop neutralizing immediately, retain current steering and
resume the held-steering brake phase. Original actuator limits/rates unchanged.

Once neutralization has started, any new moving command requires actual steering
encoder positions<=.01rad and rates<=.03rad/s. Missing/nonfinite encoders reject
that command; command targets are not measured encoders. No implicit conversion
of an unqualified moving command into a supposedly qualified stop. Interrupted
braking before steering neutralization may resume the unchanged old moving map.
The outer supervisor still needs its fresh body/encoder/causal permission gates.

Regression: original V951 case3 saved actual inputs must reproduce V949's first
steering change at221; the new adapter must retain old steering while that saved
body is moving. Exact moving-map differential on a fixed control grid,10-tick
hysteresis, body-motion reset, encoder negatives, actuator bounds/slew and premature
forward command tests. No synthetic sensor successor is physical evidence.

Any physical validation must be separately authorized, frozen and bounded. Reuse
the original18response tasks and one complete handoff task, with all original
.02/.04position/.035heading/.03half-second settle/.15native gates and own full
state/control replay. No reused response from another adapter is a new pass.
No full route, dynamic24, training or real robot automatically follows.
