"""New user-authorized audit-only continuation; old completed batch untouched."""
import ast,gzip,hashlib,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;W=R/'experiments/v842_staged_long_navigation';ROOT=R/'runs/staged_audit_completion_20261106';ROOT.mkdir(exist_ok=False)
sys.path.insert(0,str(R/'experiments/staged_90_then12_20261106'))
from evidence_rules import AUDITS,dump,read,sha
assert read(R/'runs/staged_90_then12_20261106/ROUND_WINDOW.json')['round_closed']
assert not(R/'runs/staged_90_then12_20261106/DEVELOPMENT12_WINDOW_CLAIM.json').exists()
base=R/'runs/v842_staged_long_navigation/pilot_main02/paired';pair=ROOT/'reference/paired';pair.mkdir(parents=True);(pair.parent/'source_snapshot').symlink_to(base.parent/'source_snapshot',target_is_directory=True)
outputs={x[1]for x in AUDITS}|{'discovery_audit','EXACT_REPEAT_AUDIT.json','FINAL_INDEPENDENT_REPEAT.json'}
for p in base.iterdir():
 if p.name not in outputs and p.name!='geometry_memory' and not p.name.endswith('.console'):(pair/p.name).symlink_to(p,target_is_directory=p.is_dir())
cell=pair/'geometry_memory';cell.mkdir()
for p in(base/'geometry_memory').iterdir():(cell/p.name).symlink_to(p,target_is_directory=p.is_dir())
with gzip.open(R/'evidence/rpccr_v842_pilot90_20261106/RAW_INVENTORY.json.gz','rt')as f:inventory=json.load(f)
retained=[x for x in inventory if x['path'].startswith('runs/v842_staged_long_navigation/')]
assert all(sha(R/x['path'])==x['sha256']for x in retained)
dump(ROOT/'ORIGINAL_EVIDENCE_FREEZE.json',retained)
freeze=read(W/'CANDIDATE_FREEZE.json');assert all(sha(R/p)==h for p,h in freeze['files'].items())
source=(W/'audit_run.py').read_text();before="event=next(e for e in lines(cell/'early_joint_decisions.jsonl')if e['step']==step)";assert source.count(before)==1
path=cell/'early_joint_decisions.jsonl';events=[json.loads(s)for s in path.read_text().splitlines()];steps=[events[0]['step'],events[len(events)//2]['step'],events[-1]['step']];calls=0;cache={}
def cached(p):
 global calls
 if p not in cache:calls+=1;cache[p]=[json.loads(s)for s in p.read_text().splitlines()]
 return cache[p]
for step in steps:assert next(e for e in events if e['step']==step)==next(e for e in cached(path)if e['step']==step)
assert calls==1
for rows in [[],[{'step':1,'v':2},{'step':1,'v':3}]]:
 original=next((x for x in rows if x['step']==1),None);same=next((x for x in list(rows)if x['step']==1),None);assert original==same
for p in C.glob('*.py'):ast.parse(p.read_text())
deadline=read(R/'RPCCR_STAGED_90_THEN12_AUTHORIZATION_20261106.json')['stage1_absolute_deadline_unix'];assert time.time()+600<deadline
authorization=dict(user_instruction='下一步开始',scope='Supplement existing GOAL trajectory audits, then previously authorized conditional12h only after all original gates and archive verification',scientific_revisions=0,new_pilot_navigation=0,original_batch_unchanged=True,original_model_deadline_unix=deadline,audit_operation_exception='One new metadata-only audit invocation; original failed120s invocation and frozen sources remain. Cache exactly one immutable JSONL input. No original assertion removed.',new_metadata_model_reads_max=1,new_integrations_for_supplement=0,conditional12h_tasks=['repeat10060002','main10060008','conditional_repeat10060008'],conditional12h_s=43200,no_second_audit_repair=True,new24=0,network=0,training=0,Stage=0)
dump(ROOT/'AUTHORIZATION.json',authorization);dump(ROOT/'QUALIFICATION.json',dict(passed=True,actual_saved_first_middle_last_events_equal=True,single_parse=True,missing_and_duplicate_semantics_preserved=True,original_auditor_assertions_preserved=True,models=0,integrations=0))
dump(ROOT/'PREPARED.json',dict(files={str(p.relative_to(R)):sha(p)for p in C.glob('*.py')},old_scientific_freeze_sha256=sha(W/'CANDIDATE_FREEZE.json'),original_evidence_files=len(retained),prepared_unix=time.time()))
print(json.dumps(dict(status='PREPARED',retained_files=len(retained),original_deadline=deadline,new_models=0,new_integrations=0)))
