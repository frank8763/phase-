# V947 normal forward direction contract: preparation only

User: reversing is for difficult trapped/dead-end recovery, not routine navigation
through this visible passage. This is a new source/array-only preparation stage;
no physical models, new navigation, deadline or integration authority is created.
V945 and all old frozen failures remain unchanged.

Normal planner proposal: same Smac Hybrid, footprint/map/radius/cost/budget, change
motion_model_for_search REEDS_SHEPP to DUBIN; same FeasibleRPP with
allow_reversing=false. Independently reject a normal reference containing reverse
gear segments and reject a negative nominal request with explicit replan status,
never clamp a reverse velocity to zero and pretend it is a forward solution.
Normal RP-CCR alternatives retain only the original zero and six forward commands;
all unchanged .155 command/brake/full-cycle, native.15 and source/control gates remain.

Reverse escape must be a separate stopped-state recovery transaction, requiring
causal evidence of being trapped, failure of appropriate forward planning and a
qualified exit path with original safety/actuator gates. A single forward command
rejection, temporary moving actor or search timeout is not a dead-end witness.
No reverse-escape authorizer is implemented or enabled in this preparation.

Qualification uses original V945 fixed saved command snapshots and references,
not simulated future motion: preserve every admissible nominal forward command,
never emit reverse in normal mode, preserve zero-request no-motion behavior,
reject the actual reversing reference, and test malformed/reference reverse cases.
Keep original nominal/reference failures visible. This does not certify a new
Dubin path, ROS production integration, steering stability, freshness scheduling
or final arrival. All of those remain mandatory before any new physical window.
The proposed configuration and selector are not deployed to frozen V945.

Official planner model names/semantics:
https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/planners_plugins/smac/smac_hybrid/configuring_smac_hybrid/
