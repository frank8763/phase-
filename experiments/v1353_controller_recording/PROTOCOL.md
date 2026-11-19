# V1353 result-recording correction

V1352 is closed with its original error and complete raw first-controller output
preserved. Actual RPP generated commands, then a nested ROS Empty result could
not be JSON encoded. Parent correctly closed but reported missing RESULT.json.
This is a recording infrastructure failure, not navigation or algorithm evidence.

User-authorized next software step continues in this separate finite batch.
Reuse the exact V1352 six tasks, inputs, controller configurations and600s/128MiB
software protocol. Full protocol: experiments/v1352_shared_controller_probe/PROTOCOL.md.
Reinitialize software servers, not vehicles; repeats of the first software call
are explicitly additional calls, not new independent saved inputs or physical
trials. No scientific/controller/map/path change. No old run/deadline reopened.

Only change: recursively encode ROS result fields, including Empty, into JSON
data; reject unknown object types. First reproduce the exact TypeError using a
real installed FollowPath.Result and verify strict JSON roundtrip. All probe,
driver and independent command audits are reused as frozen source modules.
No automatic physical continuation; review hold bytes remain unchanged.
