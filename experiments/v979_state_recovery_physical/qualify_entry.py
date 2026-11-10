"""Exercise actual prefix/ARM/history code using explicit no-model state peers."""
import ast,copy,importlib.abc,importlib.util,json,sys,time
from pathlib import Path
from types import SimpleNamespace as S
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v979_state_recovery_physical'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','factory','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
import physical
from native_contract import Startup
from motion_publisher import seed_history
from periodic_support import PeriodicSupport
from handshake import NODES
checks={};tasks=json.loads((C/'TASKS.json').read_text())
commands=json.loads((O/'prior_v974/physics/BODY_COMMANDS.json').read_text())
with np.load(O/'prior_v974/physics/NATIVE_TRACE.npz')as z:trace={k:z[k]for k in z.files}
class Vehicle:
    def __init__(self):self.count=0;self.scans=[];self.d=S(time=0.)
    def scan(self):self.scans.append(self.count)
    def step(self,v,w,stale):
        row=commands[self.count];assert[v,w,stale]==[row[1],row[2],row[5]]
        for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:setattr(self.d,k,trace[k][self.count].copy())
        self.count+=1;self.d.time=float(trace['time'][self.count-1])
for i,task in enumerate(tasks[:2]):
    fake=Vehicle();proof=physical.restore_prefix(fake,task,trace,commands,time.time()+120)
    checks[f'actual_prefix_loop_{i}']=proof['passed']and fake.count==task['origin_native_tick']and fake.scans==[0,*range(1,task['origin_native_tick']+1,5)]
    seed=json.loads((R/task['seed_history']).read_text());instance=S(tracker=S(),periodic=PeriodicSupport())
    proof=seed_history(instance,seed);checks[f'causal_filter_history_{i}']=proof['passed'] and instance.tracker.when==seed['source']['source_scan_sim_time']
    now=time.monotonic();arm=dict(kind='arm',run_id=task['run_id'],native_tick=task['origin_native_tick'],sim_time=task['origin_sim_time'],states={n:3 for n in NODES},checked_at={n:now for n in NODES},issued_at=now)
    startup=Startup(task['run_id']);startup._journals();startup.receive(arm,now,task['origin_native_tick'],task['origin_sim_time'])
    checks[f'exact_component_arm_{i}']=startup.phase=='RUNNING'and startup.events[-1]['event']=='COMPONENT_ORIGIN_ARM_VALIDATED'
    try:Startup(task['run_id']).receive(arm,now,task['origin_native_tick']+1,task['origin_sim_time']+.01)
    except AssertionError as e:checks[f'advanced_component_origin_rejected_{i}']=str(e)=='COMPONENT_ADVANCED_BEFORE_ARM'
    else:checks[f'advanced_component_origin_rejected_{i}']=False
bad=dict(trace);bad['ctrl']=trace['ctrl'].copy();bad['ctrl'][0,0]+=.001
try:physical.restore_prefix(Vehicle(),dict(tasks[0],origin_native_tick=1),bad,commands,time.time()+60)
except AssertionError as e:checks['altered_historical_control_rejected']=str(e)=='HISTORICAL_PREFIX_STATE_OR_CONTROL_MISMATCH'
else:checks['altered_historical_control_rejected']=False
seed=json.loads((R/tasks[0]['seed_history']).read_text());bad=copy.deepcopy(seed);bad['states'][-1]['native_tick']+=1
try:seed_history(S(tracker=S(),periodic=PeriodicSupport()),bad)
except AssertionError:checks['future_seed_rejected']=True
else:checks['future_seed_rejected']=False
for path in C.iterdir():
    if path.suffix=='.py':ast.parse(path.read_text(),filename=str(path))
    if path.is_symlink():assert path.resolve().is_relative_to(R/'experiments')and path.exists()
checks['all_operational_sources_and_aliases']=True
frozen=json.loads((R/'experiments/v977_state_consistent_recovery/SOURCE_FREEZE.json').read_text())['files']
import hashlib
checks['all_1477_frozen_sources_unchanged']=all(hashlib.sha256((R/name).read_bytes()).hexdigest()==digest for name,digest in frozen.items())
report=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,explicit_state_copy_fixtures=True,physical_prefix_not_yet_executed=True)
(O/'ZERO_MODEL_ENTRY_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['passed']
