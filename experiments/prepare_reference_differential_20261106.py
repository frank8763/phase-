"""Second and final scientific candidate, same root cutoff; preserve V835 failure."""
import ast
from datetime import datetime
import json
from pathlib import Path
import fcntl
import hashlib

repo=Path(__file__).resolve().parents[1]
oldcommon=repo/'experiments/reference_recovery_20261106'
common=repo/'experiments/reference_differential_20261106'
root=repo/'runs/reference_differential_20261106'
names=[('v835_reference_recovery_qualification','v838_reference_differential_qualification'),('v836_reference_recovery_development','v839_reference_differential_development'),('v837_reference_recovery_confirmation','v840_reference_differential_confirmation')]
assert json.loads((repo/'runs/v835_reference_recovery_qualification/FINALIZED.json').read_text())['source_and_decompressed_sha_verified']
assert json.loads((repo/'runs/reference_recovery_entry_20261106/ROUND_WINDOW.json').read_text())['round_closed']
assert not common.exists()and not root.exists()and(repo/'REVIEW_PENDING').exists()
with(repo/'runs/v648_static_unknown/execution.lock').open('rb')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
common.mkdir();root.mkdir()
replace=[('reference_recovery_20261106','reference_differential_20261106'),*names,
 ('RPCCR_REFERENCE_RECOVERY_AUTHORIZATION_20261106.json','RPCCR_REFERENCE_DIFFERENTIAL_AUTHORIZATION_20261106.json'),
 ('RPCCR_REFERENCE_RECOVERY_20261106','RPCCR_REFERENCE_DIFFERENTIAL_20261106'),
 ('RPCCR_REFERENCE_RECOVERY_V835','RPCCR_REFERENCE_DIFFERENTIAL_V838'),('RPCCR_REFERENCE_RECOVERY_V836','RPCCR_REFERENCE_DIFFERENTIAL_V839'),('RPCCR_REFERENCE_RECOVERY_V837','RPCCR_REFERENCE_DIFFERENTIAL_V840'),
 ('v835','v838'),('V835','V838'),('V836','V839'),('V837','V840'),
 ('rpccr_reference_recovery_v835_20261106','rpccr_reference_differential_v838_20261106'),('rpccr_reference_recovery_v836_20261106','rpccr_reference_differential_v839_20261106'),('rpccr_reference_recovery_v837_20261106','rpccr_reference_differential_v840_20261106'),('rpccr_reference_recovery_ops_20261106','rpccr_reference_differential_ops_20261106')]
for source,destination in [(oldcommon,common),*[(repo/'experiments'/a,repo/'experiments'/b)for a,b in names]]:
 if destination!=common:destination.mkdir()
 for p in source.iterdir():
  if not p.is_file()or p.suffix not in['.py','.md','.json']or p.name in['INPUT_FREEZE.json','CANDIDATE_FREEZE.json']:continue
  text=p.read_text()
  for a,b in replace:text=text.replace(a,b)
  (destination/p.name).write_text(text)
auth=json.loads((repo/'RPCCR_REFERENCE_RECOVERY_AUTHORIZATION_20261106.json').read_text())
auth.update(authorized_at=datetime.now().astimezone().isoformat(),user_instruction='抓紧时间将动态跑出来',scientific_candidate_index=2,max_scientific_candidates_this_user_round=2,
 continuation_basis='Same user completion instruction. Assistant plan revision after independently archived V835 failed: no new explicit user instruction. One last evidence-based rear differential candidate, same23:00 root, no further revisions.',
 previous_candidate='V835_REFERENCE_RECOVERY_NOT_PASSED_V836_V837_UNEXECUTED',
 hypothesis='V835 constant rear speeds give only .002447rad yaw despite front steer .52 in low-speed curved tail. Test the existing nominal vehicle rear differential gain8 instead of equal rear speeds, with all full-body/control/dynamic gates unchanged.',
 rear_differential_gain=8.0,new_scientific_change='Only rear wheel reference target: wheel +/- 8*wheel*tan(steer)*track/(2*wheelbase); original canonical clipping/slew and full native model admission unchanged.',
 additional_candidates_after_this=0,private_component_native_cap=500000,old_deadlines_preserved=True)
(repo/'RPCCR_REFERENCE_DIFFERENTIAL_AUTHORIZATION_20261106.json').write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n')
(root/'LEDGER.json').write_text(json.dumps(dict(status='PREPARING_LAST_CANDIDATE',closed=False,candidates_started=0,scientific_candidate_index=2,absolute_deadline_unix=1793977200.,active_simulation=False),indent=2)+'\n')
for label in [names[1][1],names[2][1]]:(repo/'runs'/label).mkdir()
for name in [names[1][1],names[2][1]]:
 own=repo/'experiments'/name
 p=own/'reference_recovery.py';s=p.read_text()
 s=s.replace("    return target, index", "    delta=8.0*wheel*math.tan(steer)*.54/(2*wheel_base)\n    target[2:]=[wheel-delta,wheel+delta]\n    return target, index")
 p.write_text(s)
 p=own/'reference_certificate_audit.py';s=p.read_text();needle="        else:\n            target = target.copy(); target[2:] = 0."
 replacement="            differential=8.0*wheel*math.tan(steer)*.54/1.20\n            target[2:]=[wheel-differential,wheel+differential]\n"+needle
 assert needle in s;s=s.replace(needle,replacement);p.write_text(s)
 # Actual discovery follows the frozen original controller, not this candidate.
 protocol=(own/'PROTOCOL.md').read_text()
 protocol+='\n## Second/final candidate amendment, shared original23:00 cutoff\n\nV835 fixed qualification independently audited and archived NOT_PASSED,3960oldreplay/58096private/0newactual/repeat/nav. Its original failure and all freezes remain unchanged. This is a second scientific candidate under the same user completion instruction, not an interface patch or retry of V835. Only reference-following target rear wheels now use existing vehicle nominal differentialgain8, left=wheel-8*wheel*tan(steer)*.54/(2*.60),right=wheel+same. Front geometry/reference/18 schedules/original21 priority/successor/full gates unchanged. Target may exceed actuator amplitude, but original canonical clipping/slew and exact native execution remain mandatory. Originalgain8 independently reconstructed from original recorded nominal targets before any newmodel. No new fixed states, firstcommands, confirmation seeds or phases; prior10070001–24 unexecuted task bytes retained. Scientificcandidate2of2, no third scientific or interface continuation. Remaining assertions of “one candidate” above refer to this frozen version, not to replacing the prior failed candidate. After this candidate failure only zero-model closure.\n'
 (own/'PROTOCOL.md').write_text(protocol)
 p=own/'BATCH.json';cfg=json.loads(p.read_text());cfg['report']='docs/RPCCR_REFERENCE_DIFFERENTIAL_'+('V839'if name==names[1][1]else'V840')+'_REPORT.md';p.write_text(json.dumps(cfg,indent=2)+'\n')
q=repo/'experiments'/names[0][1];protocol=(q/'PROTOCOL.md').read_text();protocol+='\nSecond and final scientific candidate: change reference-tail rearwheel targets to original nominal differentialgain8, keep exactly the fixed490/495 inputs and all safety gates. PriorV835 failed archive immutable, same root23:00; no further scientific/interface repair or retry.\n';(q/'PROTOCOL.md').write_text(protocol)
# Correct the operational identity before freezing: launcher and sleep guard use campaign.py.
(common/'campaign.py').write_text((common/'run_campaign.py').read_text());(common/'run_campaign.py').unlink()
p=common/'launch.py';p.write_text(p.read_text().replace("common/'run_campaign.py'","common/'campaign.py'"))
# The original new24 task list was never physically used. Preserve its bytes.
a=repo/'experiments'/names[2][0]/'TASK_LIST.json';b=repo/'experiments'/names[2][1]/'TASK_LIST.json';assert a.read_bytes()==b.read_bytes()
plan=(repo/'experiments'/names[1][1]/'PROTOCOL.md').read_text();(repo/'docs/RPCCR_REFERENCE_DIFFERENTIAL_20261106_PLAN.md').write_text(plan)
(root/'HANDOFF.md').write_text('# LATEST OVERRIDE — second/final scientific candidate, same23:00\n\n'+plan)
for d in [common,*[repo/'experiments'/b for a,b in names]]:
 for p in d.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
print('SECOND_AND_LAST_DIFFERENTIAL_CANDIDATE_PREPARED_SAME2300')
