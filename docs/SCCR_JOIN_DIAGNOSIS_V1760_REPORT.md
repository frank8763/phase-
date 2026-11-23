# SCCR geometric-core join diagnosis V1760

Original source checks `local_curve` metrics and then returns the concatenated `active_path`. The saved118-point candidate has an inferred 80-point local curve, starting at vertex2 and ending at81; float32-exact original prefix/suffix determine these boundaries.

The first recorded Phase request rejection is precisely the entry join: independent turn 46.905784 degrees, raw center steering -1.410288122rad, original cap 0.427221373rad. The adjacent segments are 0.100000m/0.053314m; coordinate half-ULP bound 7.45e-09m. This is not explained by degenerate segments or floating-point jitter.

Independent local-curve p95 curvature 1.016235/m (original local bound1.8), max heading increment 0.028041rad (original bound.24). Phase center-steering-equivalent curvature cap 0.758770/m. Interior vertices exceeding that Phase cap: 36. These two restrictions differ, so successful original geometric search alone does not qualify the Phase vehicle mapping.

This is an interpretable interface boundary on one already exposed synthetic candidate, not a new independent trial, physical safety/arrival result, full historical SCCR failure, or global infeasibility proof. Original V1754 PASS and V1757 sampled refusal remain immutable. No original planner, model, Allocator, physics, replay or SAC was executed here. The raw polyline-to-command gate also does not establish how a faithful controller would track the continuous curve.

Next justified step: preregister a separately named Phase-compatible geometric-core adapter with explicit join and vehicle-envelope contract, keeping original SCCR comparison identity separate; validate its actual full-state retained-stop response before whole-task comparison. Do not silently smooth the old path, lower gates, retune old candidate, or replace the original SCCR action-fusion hierarchy. The next actual task and any tonight unattended batch await user review and explicit authorization.
