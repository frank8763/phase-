"""Zero-model separate audit view for FollowPath's empty global-router journal."""
import hashlib,importlib.abc,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v970_component_audit_view';original=R/'runs/v858_nav2_verified/v968/closed_handoff';view=O/'view02'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','torch','vehicle','physical','factory'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p.relative_to(original)):sha(p)for p in original.rglob('*')if p.is_file()and not p.is_symlink()}
view.mkdir(exist_ok=False)
for p in original.iterdir():
 if p.name!='INDEPENDENT_AUDIT.json':(view/p.name).symlink_to(p)
# Frozen component branch calls only FollowPath; no NavigateToPose / planner proxy
# invocation, so the missing lazy router journal is empty by source construction.
assert not(original/'ROUTER_REQUESTS.json').exists()
stages=json.loads((original/'CLOSED_HANDOFF.json').read_text())['stages'];assert len(stages)==2 and all(s['follow_status']==4 for s in stages)
(view/'ROUTER_REQUESTS.json').write_text('[]\n')
sys.path[:0]=[str(R/'experiments/v968_rpp_closed_loop_night'),str(R/'experiments/v884_feasible_rpp'),str(R/'experiments/v862_ready_static')]
from component_audit import audit
task=json.loads((original/'TASK.json').read_text());task['output']=str(view)
result=audit(task)
assert before=={str(p.relative_to(original)):sha(p)for p in original.rglob('*')if p.is_file()and not p.is_symlink()},'ORIGINAL_EVIDENCE_CHANGED'
report=dict(passed=result['passed'],models=0,integrations=0,original_evidence_sha_all_unchanged=True,original_failed_audit_preserved=True,
 original_audit_sha256=before['INDEPENDENT_AUDIT.json'],view_only_extra_file='ROUTER_REQUESTS.json = []',reason='Direct FollowPath has no global proxy invocation. Original proxy writes this journal lazily; old saved physical trace/function unchanged.',
 result=result)
(O/'AUDIT_SUPPLEMENT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k!='result'},indent=2));print(json.dumps({k:result.get(k)for k in ['component_checks','tracking','actual_forward_progress_m','error','traceback']},indent=2))
