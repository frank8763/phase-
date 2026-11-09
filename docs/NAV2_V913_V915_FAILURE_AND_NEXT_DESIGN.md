# V913–V915: recorded failure and next design, 2026-11-09

Both physical candidates are CLOSED / NOT_PASSED. V915 is saved-data analysis only, zero model initializations and integrations. Original failures, sources, root deadline 12:58:26.663983+0800, and original safety thresholds remain unchanged. No third physical candidate, repeat, fresh24, training, hardware or Stage work was performed.

| Batch | Actual native | Own-control replay | Private | Outcome |
|---|---:|---:|---:|---|
| V913 original WE main | 5224 | 5224 | 0 | finite command permission expired during planner recovery |
| V914 original WE main | 8895 | 8895 | 0 | new movement and stop tubes rejected at tick8694 |
| Conditional repeats | 0 | 0 | 0 | both unexecuted |
| V915 saved analyses | 0 | 0 | 0 | diagnosis, not navigation |

Both actual prefixes have minimum clearance0.26907345126624027m, zero bad contacts and full qpos/qvel/ctrl/mocap replay error0. Overall evidence and functional gates are NOT passed; component geometry/replay success must not overwrite the original audit result.

## V913 fault sequence

Full real Nav2 startup was exercised before the physical run, with synthetic message peer and no vehicle model. Seven lifecycle nodes, two full map reads and ARM passed; probe ended before goal submission. Initial probe AF_UNIX path-too-long failure is preserved as zero-model preparation failure.

During physical navigation, Nav2 planning recovery cancelled FollowPath and ceased velocity publication. Last admitted zero command used bodytick4998. Real scans continued through5221. Old permission expired before5225; native prefix ended5224. Later ROS stale-observation error was a consequence of the native stop, not evidence that the causal predictor blocked ROS. V913 reached remaining goal distance3.798916m. Forty-five recorded waiting states independently admitted a fresh zero command; V914 introduced a 20Hz fresh-observation zero-command renewal only when nominal publication had been silent at least0.15s.

## V914 actual result

The timer performed107 independently audited zero renewals. First actual actor detection was tick4556. Vehicle subsequently travelled2.946536m;30 post-detection global routes succeeded. These updates were periodic, not claimed discovery-triggered. Remaining goal distance2.004024m, final speed0.000001124m/s. Max100Hz loop lag0.003051s; single run pacing is not a general real-time guarantee. Actual navigation plus braking lasted88.95 simulated seconds, rather than hours of private rollout. ROS startup/navigation wall time95.742s. No private rollout occurred.

At tick8679 nominal movement future dynamic lower bound0.156860m passed. At8684 nominal0.154019 failed and zero0.159273 passed. At8690 zero0.155406 passed. At8694 new movement0.147019 and zero0.152238 both failed. Static zero lower bound0.447131m remained ample; current dynamic bound0.296279m was also above threshold. In all last10 states the critical dynamic time was the2.2s horizon endpoint. Original thresholds .155predicted/.15actual were unchanged. Failure was predictive future separation, not a collision or stale-message/permission-expiry failure.

Holding the first stop body pose while using the final causal source still gives0.153199m, below threshold: actual braking displacement alone is not the explanation. The finite horizon advances into the actor future motion. The recorded final braking prefix lasts2.05s after the last accepted zero certificate; maximum actual translation residual0.006122m and angle residual0.006256rad remain within original0.04m/0.035rad limits and its finite time. This shows why a valid retained tail must not be discarded merely because a newly centred full-duration certificate fails; it does not prove perpetual waiting or arrival.

## Zero-model all-phase diagnosis

V915 screens all827 saved tracked states using only their recorded causal coefficient sets. Independently written c±hypot(a,b) extrema exactly agree with the online interval-extrema implementation over a full2π/.32 period. Last saved stationary pose with all-phase geometric separation is tick8589 at(1.963671,-1.470124), dynamic lower0.157529m and static0.528691m. The final pose has all-phase lower0.097318m. This is conditional stationary geometry under the declared periodic class and empirical pose residual, not a reachable/stopping invariant-set proof. It does not establish that waiting there eventually permits arrival. No unexecuted vehicle trajectory was simulated.

## Next implementation specification (not yet physical-qualified)

1. Treat an admitted motion-plus-brake certificate as an immutable resource: anchor, source, elapsed native time and remaining tail. Replace it only after a new command certificate passes. If renewal fails, execute the remaining already-certified tail and monitor its original residual/time limits. Never reset its clock or reuse an old moving command as a new permission.
2. Distinguish bounded braking from renewable waiting. A stationary waiting region must have independently checked all-phase separation for the declared periodic actor class, static margin, and qualified braking reachability. Reject movement before it leaves that backup set unless another reachable safe backup is certified. Checking only the current pose does not establish this.
3. Have the nominal planner/controller use the same backup-feasibility constraint. A geometric path and a safe next0.2s action do not imply a recoverable next state. Waiting/replanning should occur before the unsafe future approach; preserve original physics, sensing and safety margins.
4. Before any next physical candidate, qualify certificate expiry, failed renewal, stale/future source, bounded tail completion, repeated missing observations and mismatched ctrl/body negatives. Validate stopping reachability on existing evidence first. The candidate must not claim recursive safety until residual and terminal invariance assumptions are established.

The known .32rad/s sinusoidal frequency is an added public prior; results cover only that declared class, not arbitrary .08m/s motions or the older wider .12per-axis class. This filter plus retained-tail engineering is not by itself an established RAS contribution. Fresh held-out confirmation, fair RPP/MPPI comparisons, ablations, uncertainty/runtime/generalization evidence and later hardware validation remain required. The current dynamic acceptance is still incomplete.
