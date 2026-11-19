# Preserve cruise-state continuity instead of forcing a stop at every node

The rest-only canonical graph is a restrictive finite graph; exhaustion is
not an impossibility proof. Its static witness includes unnecessary per-edge
brakes/holds. One structured preparation refinement adds canonical boundary
speed0/.1 to the existing exactly connected poses and zero curvature states.
No increased operating speed,curvature,sensor/prior/safety or online budget.

Each spatial edge has exactly4prebuilt temporal variants: rest→rest,rest→cruise,
cruise→rest,cruise→cruise. Nominal accel0→.1 over1s,brake.1→0 over2s and2s
stoppedhold remain;explicit.4initialrest. Waiting/gearchange allowed ONLY at
rest. Cruise end state passes directly to a same-gear start with identical
position,heading,speed. Cruise arrivals cannot dominate later arrivals through
implicit waiting; retain each distinct arrival time. Actual tracking unqualified.

To preserve an exact.2s arrival grid without snapping pose or stopping a moving
car, length-matching cruise velocity is .1-A*sin(pi*t/T)^2. Select smallest
.2multipleT>=remaininglength/.1;A=2*(.1-remaininglength/T). Endpoint velocities
remain exactly.1,integrated length exactly matches the polynomial edge arc.
Acceleration/deceleration and maximumsteeringslew checks independently gate
all variants. No extra waiting silently inserted while speednonzero.

Keep all old libraries/results and sharedcontroller two-call freeze. Separate
cruise graph source/binary/input/result,original80s/22000/1.5s/27cm plus local
interpolation allowance,40s totalwaiting,original source15105. No model launch.
Positive must pass full independent path/timing/velocity/footprint/cusp/stop
audit. Continue to report canonical resting/nominal model restrictions.
