"""Exercise real isolated full-route import/configuration, no model allowed."""
import sys,json,ast,importlib.abc
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(Path(__file__).resolve().parent));import fresh_worker as w
assert len(sys.argv)==2 and Path(sys.argv[1]).is_absolute();task,O,cfg,out=w.entry(sys.argv[1]);assert task['historical_prefix_native']==0 and cfg['worker']=='fresh_worker.py'and cfg['audit']=='fresh_audit.py';assert task['kind']in ['main','repeat'];f=w.factory(O);owner=w.pipeline.configure(O);assert callable(f.create_vehicle)and callable(f.replay)and callable(owner.navigate)
assert Path(owner.__file__).resolve()==w.R/'experiments/v1067_causal_replan_brake_reserve/owner.py'
assert Path(__import__('planner').__file__).resolve()==w.R/'experiments/v1067_causal_replan_brake_reserve/planner.py'
import fresh_audit
for name in ['live_reference.py','fresh_pipeline.py','fresh_worker.py','fresh_audit.py','fresh_campaign.py','fresh_entry_check.py']:ast.parse((w.CORE/name).read_text())
# Fail if the production entry ever starts consuming old trajectory controls.
for name in ['live_reference.py','fresh_pipeline.py','fresh_worker.py']:
 t=(w.CORE/name).read_text()
 assert 'restore(v,'not in t and 'REMAINDER_INPUT'not in t and 'SOURCE_PRODUCER_FAILED'not in t
assert not out.exists();assert Path(__import__('planner').library()._name).is_file();w.install_history_guard(out)
try:(w.R/'runs/v858_nav2_verified/v1078/saved_NS_complete_goal/physics/NATIVE_TRACE.npz').open('rb');rejected=False
except AssertionError:rejected=True
assert rejected
try:(out/'NATIVE_TRACE.npz').open('rb');own_allowed=True
except FileNotFoundError:own_allowed=True
assert own_allowed
print(json.dumps(dict(passed=True,history_read_guard_negative_passed=True,isolated_cwd=str(Path.cwd()),fresh_t0=True,no_historical_restore_call=True,complete_production_imports=True,models=0,integrations=0)))
