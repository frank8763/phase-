# Exact labels and steering-rate qualification repair, still zero models

OriginalV1364 sources/binaries/refusals remain immutable. This stage found a
specific old quantized dominance counterexample: actual same-bin poses at
arrival65,gear-1,speedcruise share position bin but differ4.30degrees; one next
cruise has full footprint.255625m (refused27cm), the other.292713m (admitted).
12different one-edge outcomes among32reviewed coarse collision states. Both
incoming candidates were checked by the diagnostic kernel before it recorded
them; the subsequent one-edge outcomes were independently rebuilt with NumPy. Finer2cm/1degree and1e-9diagnostic key cases still failed whole-route
search under unchanged22000/1.5s. No evidence this bug alone explains all failure.

Actual repair uses bit-identical x/y/yaw,gear,velocity,steering labels for
arrival-time rejection. Quantized buckets must never be treated as dominance.
Signedzero may coincide. No new completeness guarantee: floating pose searches
can grow and still fail the original bounded budget. No budget increase.

The same nominal acceleration is not a qualified actual response: saved
control is a0.1m/s command STEP, while the old primitive assumes1s RAMP.
These DIFFERENT inputs do not directly identify response-to-ramp error.
The saved step nevertheless does not establish the hypothesized ramp/timing
envelope. At1s actual displacement.081648m vs nominal.05m;95%sustained speed
at3.86s,not1s. Report finite observation only, not a global speed bound.

Unchanged adapter has virtualcentersteeringrate.6rad/s. Going nominalk-.5 to+.5
requires centerangle change.582914rad/atleast.971523s,not instantaneous. Zero
Twist parking holds do not establish a requested new wheel angle; explicit
parked_target is a separate qualified interface. A proposed turn-in trajectory
must integrate rate-limited steering continuously and include its occupied
footprint during that transition. Still needs real actuator/tracking capture.

Implement a separate fixed steering-rate nominal primitive and independently
check exact straight/turn-in/brake/gearwait examples and invalidcontrol/clock
negatives. Do not use the real saved response as an online historical command
tape, transplant root state outside integration, alter plant/network/safety or
claim that mathematical integration equals actual MuJoCo/hardware dynamics.
Original17:00 physical deadline remains expired, all new work0models.
