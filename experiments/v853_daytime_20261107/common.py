"""Fixed root deadline, original tasks and explicit applicability registration."""
import hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;W=R/'experiments/v853_maneuver_worker';ROOT=R/'runs/v853_daytime_20261107';RAW=R/'runs/v853_maneuver_worker';DEADLINE=1794052800.


def read(p):return json.loads(Path(p).read_text())


def dump(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);temporary=p.with_suffix(p.suffix+'.tmp');temporary.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False,default=lambda x:x.tolist()if hasattr(x,'tolist')else str(x))+'\n');temporary.replace(p)


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


sys.path.insert(0,str(R/'experiments/staged_audit_completion_20261106'))
from evidence_rules import AUDITS as ORIGINAL_AUDITS,FUNCTIONAL_CHECKS,repeat_check
sys.path.remove(str(R/'experiments/staged_audit_completion_20261106'))
AUDITS=[(s,f,600 if s=='audit_run.py'else 1200)for s,f,_ in ORIGINAL_AUDITS]
AUDITS.extend([('audit_candidate_policy.py','CANDIDATE_POLICY_AUDIT.json',1200),('audit_maneuver.py','MANEUVER_AUDIT.json',300)])
VARIANTS=[('A32',32),('B64',64),('C328',328)]


def tasks():return read(C/'TASK_LIST.json')


def unchanged():
    v=read(C/'CANDIDATE_FREEZE.json');assert sha(C/'CANDIDATE_FREEZE.json')==read(ROOT/'PREPARED.json')['freeze_sha256']
    for p,h in v['files'].items():assert sha(R/p)==h,('FROZEN_INPUT_CHANGED',p)


def complete_gate(rows):
    return len(rows)==6 and all(r.get('physical_passed')and r.get('functional_passed')and(r['role']!='REPEAT'or r.get('repeat_passed'))for r in rows)


def model_fits(deadline,now,cap):return now+cap+2<deadline
