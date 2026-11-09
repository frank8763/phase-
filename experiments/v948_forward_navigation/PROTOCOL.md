# V948 complete forward-navigation software preparation

User: ordinary passage navigation must advance without reversing; recovery must
return to forward navigation towards the ORIGINAL goal. V945 and V947 remain
immutable. No new physical deadline, model initialization, simulation, replay,
training or real-robot authority is created here. REVIEW_PENDING remains present.

This candidate integrates V947 DUBIN/forward-only FeasibleRPP, rejects reverse
references before publication, and uses the same seven forward/stop RP-CCR
commands and unchanged original command/brake/terminal admission. A negative
normal request creates an explicit cancel/replan event, never an implicit reverse
or a claim that clipping it to zero solves navigation. A normal zero request
cannot be converted into motion. Recovery completion only starts a NEW normal
goal with the original target; it never satisfies overall goal success.

Reverse escape is disabled. There is no qualified dead-end detector/escape path
in this candidate. Future reverse recovery needs its own entry/exit qualification;
an isolated rejection, actor observation loss or planner timeout is insufficient.

Native observation reading, serialized command admission and heavy telemetry use
separate ROS callback groups. Original 200ms coherent-observation/50ms new command
and native permissions remain unchanged. A stale coherent snapshot exception now
carries the exact producer-side packet, decision time and measured ages. No stale
input is refreshed, relabeled or silently accepted.

Qualification: fixed V945 first-under-2m and last command states, original causal
prior rebuilt from saved scans only, actual installed Smac/RPP software with zero
vehicle models. No new state motion generated; any RPP output is a software
proposal, not physical execution. Preserve both feasible and infeasible results.
Read back actual planner/controller parameters and full static master map.
Separate actual ROS callback-group blocking regression and complete supervisor
callback tests (synthetic completion is never reported as arrival).

Steering remains a separate unresolved physical-readiness gate. V945 body stop
did not neutralize steering and its complete segment exceeded the .035rad bound.
Neither a new path nor callback tests validate changed actuator response. Do not
launch a full physical route until steering handoff and full response gates have
been qualified under a NEW bounded protocol. All old failures remain failed.

Storage: temporary raw budget2GiB, only necessary summaries/code in Git; selected
raw in same-repo Release with downloaded SHA and member readback before cleanup.
No old synchronization retry. No automatic 24, additional route, comparison or
algorithm pool.
