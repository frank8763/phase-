# V1203 production goal seam: software qualification only

No physical window, vehicle/MuJoCo/ROS construction, training, three-route or
24-item launch. Do not edit old sources, model, controls, geometry or gates.
Preserve original REVIEW_PENDING. CPU2 idle policy, GPU hidden, serial shared
Phase lock, total360s software wall cap, temporary storage2GiB.

One goal executor is used by the new live-chain call site and the analytical
vehicle-interface harness. The harness is explicitly not a physical vehicle.
Initial input must match current eight-state/controller memory and native time.
Generate at most one full source with the V1201 fixed direct6s/refuge25s
algorithm, generalized only to carry explicit initial load mode and native
offset. If composite, execute its entire prefix and2200 stop; then read the
current state/memory/mode and regenerate its onward source (direct at most8s).
Do not reuse a nominal suffix or reset the original causal source clock. No
second intermediate-refuge transition. No source may be replaced while moving.

Keep original pose feedback, response .04m/.035rad/.015rad, reference
.04m/.035rad, measured rest, forward capture<=600, and final2200 stop. Preserve
absolute geometry time at the seam, full original proof and raw threshold.
Check each scheduled stop from its actual carried state before executing it.
No claim of immediate braking feasibility at every travelling state.

Fixed8 cases: C1/A2/B1/P1 nominal, then V1202 C1 yaw_plus, B1 x_minus,
B1 y_plus, P1 x_plus. No replacements. Independently replay all actual requests
with C++ and compare every state/control/controller-memory sample<=1e-8.
The harness uses the same predictor as the executor shadow, so perfect nominal
model response is expected; this does not test physical model error.

Before search validate zero-step rejection of stale full state, clock,
controller memory, lateral velocity, steering state, active/coupled mode and
missing load mode, plus a valid expired deadline/zero work. Freeze all source,
fixed inputs, binary/parameters and prior successful references first. During
qualification first exception stops; preserve partial work as unknown if needed.
Production full-chain native audit and isolated physical worker qualification
remain a separate gate, even if these eight software cases pass.
