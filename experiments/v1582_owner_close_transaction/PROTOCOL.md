# V1582 owner-close transaction — engineering preparation only

V1580 focused SOURCE result is closed and11960 members remotely recoverable
through V1581. Its complete_actual_source_target remains false. Do not rerun or
edit any closed target/source. All V1577/78/79 failures remain preserved.

The frozen actual supervisor still has unprotected finally operations: metadata
reads/writes, log close, review restore and parent update can mask its first
error or skip later cleanup. The new close.py is a concrete callback transaction
for a future explicit native/ROS owner. It attempts every owned child close,
drain and log close separately; it verifies all child exits and the idle native
lock before restoring REVIEW_PENDING or clearing active authority. A failed
save is retained separately from the original error. It never creates runtime
success, computes a model, alters policy or adds actions.

Draft only: AST inspection, no import/target/qualification/source freeze/window/
admission/once/launch. Next review/bind the actual supervisor to this explicit
closure and qualify necessary failure/save/unknown paths once under run_phase
CPU2 zero-model profile. Do not rerun old OS/ROS/RPC/Gear/model suites. Source
qualification must include whole new production wiring and precise writer
coverage, not infer them from a narrow output/CLI PASS.

Current actual1010MiB peak is above10GiB. Old offline archive/transport files
identified by a readonly inventory are not eligible for deletion solely from
FINALIZED/local SHA: require their exact remote block/member/whole/recovery-index
proof and a new SHA/mtime/inode plan, reject source manifests/current inputs and
all success/failure anchors. No cleanup or old upload/reseal is authorized by
this draft. New-scope peak must be remeasured after any eligible cleanup.

Science12 remains final,19starts/7partial/127830actual/105105ownreplay/whole0.
No numerical or vehicle permission, parameter/domain/gate/time change or13th
scientific revision. Continue current input full-witness/independent audit,
current2200 timing and fullstate source/Allocator/replaypair only after their
actual source/authority/resource prerequisites are met.
