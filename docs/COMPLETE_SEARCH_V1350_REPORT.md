# V1350 full-search acceleration and route-readiness qualification

User requested the next step after V1349. This round completed saved-data search acceleration and route-readiness tests, with **zero models, zero physical/replay integration, zero training and no new physical window**. Old V1348 failure and all deadlines remain closed. Stage access0; PhaseCPU3–5 only, low priority. Physical readiness FAILED; acceleration qualification PASSED.

## Measured computation result

The full Hybrid A* expansion, primitive generation, heap/key bookkeeping and the already qualified exact footprint arithmetic now run in C++. Original mode retains7steers/bothgears/.24m primitives/.04m edge samples/.008m final dense recheck/22000expansions/costs/.50nominal curvature/.27requested margin and original start adjustment. No footprint or gate reduction. Fixed original requests1/4/8:

|Saved request|Original NumPy planner seconds|Full C++ seconds|Observed speedup|Original path equality|
|---|---:|---:|---:|---|
|1|12.523|0.498|25.13x|All elements bit-identical|
|4|12.556|0.499|25.14x|All elements bit-identical|
|8|12.489|0.498|25.07x|All elements bit-identical|

These are separate software measurements on fixed inputs, not an end-to-end real-time or physical-arrival claim. Isolated final timing avoids competing qualification scripts on the same PhaseCPU3. The separate simultaneous-final-check timing logs retain their larger wall values and are not used for the25x claim. Actual current compiled binary geometry also agrees with original NumPy at3000deterministic signed/diagonal/workspace queries, maximum error0 and unchanged threshold decisions. All returned saved paths independently pass original NumPy dense checks.

## Why the vehicle was not restarted

The fixed saved inputs still produce0/3 complete goal paths. Obstacle-aware2D ordering, vehicle-center goal checking, official Reeds–Shepp analytic goal connections and a bounded5×4400synthetic continuation diagnostic did not establish a complete route. Empty-field forward/reverse/mirror/turn positives4/4 verify the connector seam works, not that it solves this course. Original behavior and synthetic positives are never combined into a physical success count.

The pinned OMPL BSD source and adaptation are retained with exact commit/SHA in `OMPL_SOURCE_PROVENANCE.json`. Source: [official Reeds–Shepp implementation](https://ompl.kavrakilab.org/ReedsSheppStateSpace_8cpp_source.html). It supplies analytic car-curve candidates; every proposal still needs independent exact obstacle checking. A shortest analytic curve blocked by obstacles is not proof that all curves are impossible. The initial root-connector return bug and failed center-only connection/guide attempts remain documented in qualification files; it was fixed before source freeze and no physical run occurred.

## Goal definition and information limits

The exact original goal center(4,-2)at yaw0 has nominal static clearance0.175m, lower than the unchanged0.22m live route gate. The original task accepts distance<=0.45m. Safe terminal selection must therefore use that SAME acceptance region, keeping the target fixed and leaving a0.13m tracking/stop reserve with a0.32m inner region. For example(4,-1.7)at yaw0 is0.30m from original goal and has0.475m static clearance. This semantic correction did not itself solve route generation.

A finite goal-region screen,25920sampled poses per saved request, found no eligible0.22m terminal sample in request4's currently expanded causal occupancy; the largest sampled clearance was0.207349m. Other requests have eligible terminal poses, so their connection failure also involves bounded car-route search. This finite sampling is neither a complete feasibility proof nor permission to delete occupancy. The old longest19.55s novel-return gap remains a perception/uncertainty limitation.

Faster equivalent results were conditionally rechecked against OLD saved stationary-trajectory observations at estimated completion:2/3 admitted (previous4.9s version1/3). This is an informative counterfactual, not a fresh closed-loop test. Saved request1 still fails0.22m live admission (~0.217652m) despite0.51s planning. No threshold relaxation.

## Decision and next prerequisite

Keep the25x computation implementation as reusable qualified engineering work. Do not start another vehicle run merely because computation is faster. Complete-route/recertifiable-continuation and latest-observation admission remain unqualified. The next scientific choice must explicitly address bounded car-route connectivity and what causal information is actually available during no-return intervals. If those inputs cannot certify movement, retain a bounded algorithm refusal in the baseline denominator; do not tune every baseline until it succeeds. Shared-framework RPP results do not invalidate RP-CCR V1281 exposed24/24, and do not establish independent-method superiority.

Before any future physical candidate: fix its information contract/finite task/budget, independently qualify route/capture/current-field behavior, freeze source and keep all original15cm actual/22cm live/control/self/contact/fullstate replay gates. No new model is authorized by these qualification result files. REVIEW_PENDING remains, Phase lock idle, no background vehicle task. Existing required raw remains until remote downloadSHA+restoration; this round's small source/summary/binary can be stored directly in Git.
