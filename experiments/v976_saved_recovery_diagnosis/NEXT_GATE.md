# Next gate after V974: saved-state reference executability, no new physical authority

V974 actual travel5.587976778m, physical detection at native5711/57.11s, actual postdetection travel1.170814788m; goal still2.990346700m.8038actual+8038exact own-control replay, native minimum.273036567m/contact0. This is NOT full dynamic acceptance.

The first installed recovery reference begins with curvature0 while the actual held front steering implies curvature−.49423395. Heading first exceeds.035at native6193, only.68s after installation. Maximum.089602524at native7058/9.33s; body heading−.00256 while nearest reference heading−.09216. End-heading error.07605. Position remains within.03071m; a successful FollowPath action and1.002m actual segment travel do not establish the original heading envelope. RPP uses.6mlookahead and.20mgoal tolerance; short abrupt-curvature references and early goal completion must be addressed together with the initial steering mismatch. No unique mechanical cause is claimed.

At the second state, static search finds a complete path, but its connected full-cycle-qualified prefix is only.6m, improving goal distance.531952308<original.6. The code rejects this prefix. A separate zero-model diagnostic applied the **same original dynamic/periodic geometry** inside every search edge for the two fixed saved states. Both discrete forward-only searches exhaust their open sets (262and43expanded, under.2s); neither produced a full-cycle-qualified path. This finite lattice result is not a continuous-space impossibility proof. Lowering the progress threshold alone is not established as a solution.

Next bounded qualification should:

1. Include measured steering/virtual-angle state in reference generation, matching the first curvature and respecting the original actuator/virtual steering-rate limits. No immediate straight reference from held curved wheels.
2. Generate references compatible with the actual RPP lookahead/terminal behavior, and independently check geometric position **and** heading through the entire stop. A goal-status success cannot substitute for the tracking envelope.
3. Independently qualify the same saved causal states with original.155/.15/body/command limits. If the conservative full-cycle lattice still cannot connect to the goal, separate this limitation from tracking; study time-indexed causal reachable corridors and a genuinely executable terminal backup before proposing physical changes. Do not silently turn a finite/phase-specific permission into an indefinite waiting guarantee.
4. Complete positive and negative saved-input/interface qualification first. Any later physical test needs a separately frozen finite scope; no new physical work, thresholds, seeds, pools or night run are authorized by this document.

All diagnosis in V976 is0models/0integrations/0private dynamics predictions. Static analytic searches are counted separately. V974 and all old failed outcomes remain unchanged.
