"""Operations and independent gates for one declared goal/first-certificate candidate."""
import hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;W=R/'experiments/v851_profile_output_worker';ROOT=R/'runs/v851_profile_output_continuation';PHASE=ROOT/'development01';RAW=R/'runs/v851_profile_output_worker'
def read(path):return json.loads(Path(path).read_text())
def dump(path,obj):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(path)
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as stream:
  for block in iter(lambda:stream.read(4*1024**2),b''):h.update(block)
 return h.hexdigest()
sys.path.insert(0,str(R/'experiments/staged_audit_completion_20261106'))
from evidence_rules import AUDITS as ORIGINAL_AUDITS,FUNCTIONAL_CHECKS,repeat_check
sys.path.remove(str(R/'experiments/staged_audit_completion_20261106'))
AUDITS=[(script,filename,600 if script=='audit_run.py'else 1200)for script,filename,_ in ORIGINAL_AUDITS]
AUDITS.append(('audit_candidate_policy.py','CANDIDATE_POLICY_AUDIT.json',1200))
AUDITS.append(('audit_progress.py','PROGRESS_CONTRACT_AUDIT.json',300))
def tasks():return read(C/'TASK_LIST.json')
def names():return[f'v851_{role}_slot{t["slot"]:02d}'for t in tasks()for role in ['main','repeat']]
def complete_gate(records):
 expected=[(t,role)for t in tasks()for role in ['MAIN','REPEAT']]
 return bool(len(records)==6 and [(x['task'],x['role'])for x in records]==expected and all(x.get('physical_passed')and x.get('functional_passed')and(x['role']!='REPEAT'or x.get('repeat_passed'))for x in records))
def model_fits(deadline,now,cap):return now+cap+3<deadline
def unchanged():
 frozen=read(C/'CANDIDATE_FREEZE.json');assert sha(C/'CANDIDATE_FREEZE.json')==read(ROOT/'PREPARED.json')['freeze_sha256']
 assert all(sha(R/p)==h for p,h in frozen['files'].items()),'FROZEN_SOURCE_OR_REGISTERED_INPUT_CHANGED'
