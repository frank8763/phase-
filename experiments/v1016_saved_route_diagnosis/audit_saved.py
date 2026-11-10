"""Full original audit in a copied namespace with isolated numeric metadata check."""
import copy,importlib.util,json,shutil,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1016_saved_route_diagnosis';sys.path[:0]=[str(C),str(R/'experiments/v1015_atomic_entry_continuation')]
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=load('old_scalar',R/'experiments/v961_steering_continuity/independent_shaping.py');new=load('new_scalar',C/'independent_shaping.py')
import gzip
rows=json.loads(gzip.decompress((O/'saved/COMMAND_TUBES.json.gz').read_bytes()));last=None;red=None
for i,r in enumerate(rows):
 try:old.check(r['nominal_shaping'],r['packet'],last)
 except AssertionError:red=dict(index=i,old_previous=last,recorded_prior=r['nominal_shaping']['prior']);break
 nxt=old.check(r['selected_shaping'],r['packet'],last)
 if not r.get('retained_previous'):last=nxt
assert red is not None
shape=copy.deepcopy(rows[red['index']]['nominal_shaping']);shape['prior']['delta']+=1e-9
try:new.check(shape,rows[red['index']]['packet'],red['old_previous'])
except AssertionError:pass
else:raise AssertionError('PRIOR_1E9_TAMPER_ACCEPTED')
source=R/'runs/v858_nav2_verified/v1015/main_we';view=O/'audit_view';assert not view.exists();shutil.copytree(source,view,symlinks=True)
shape_module=load('shaping_audit',C/'shaping_audit.py');sys.modules['shaping_audit']=shape_module
m=load('saved_full_science',R/'experiments/v1014_atomic_handoff_navigation/scientific_audit.py');task=json.loads((source/'TASK.json').read_text());task['output']=str(view)
result=m.audit(task)
summary=dict(models=0,integrations=0,original_total_failure_not_upgraded=True,original_shaping_red=red,prior_1e9_tamper_rejected=True,new_full_saved_audit=result)
(O/'SAVED_INDEPENDENT_DIAGNOSIS.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2)[:14000])
