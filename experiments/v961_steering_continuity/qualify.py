"""Real saved stop symptom, production shaping/dispatch and full worker fixture."""
import ast
import copy
import importlib.abc
import importlib.util
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v963_continuous_dynamic'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','torch','vehicle','factory','physical','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path[:0]=[str(C),str(R/'experiments/v963_continuous_dynamic'),str(R/'experiments/v862_ready_static'),str(R/'experiments/v884_feasible_rpp')]
from steering_continuity import SteeringContinuity,measured,K,stopped_ready
from independent_shaping import check
saved=R/'runs/v858_nav2_verified/v959/response_06'
with np.load(saved/'BODY_AND_STEERING.npz')as f:body=f['body'][-1].tolist();enc=f['steering'][-1]
packet=dict(native_tick=420,body=body,body_measured_at=1.,steering=dict(native_tick=420,measured_at=1.,position=enc[:2].tolist(),velocity=enc[2:].tolist()))
checks={};rejected={}
def red(name,call):
    try:call()
    except Exception as e:rejected[name]=repr(e);return True
    return False
s=SteeringContinuity();first=s.preview(packet,.1,0.,1.)
checks['old_instant_straight_handoff_red']=abs(enc[:2]).max()>.35 and abs(first['selected'][1])>.07
checks['actual_stopped_wheels_not_forced_neutral']=stopped_ready(packet,1.)
last=check(first,packet,None);s.commit(first)
trajectory=[first]
for i in range(1,41):
    p=copy.deepcopy(packet);p['native_tick']+=5*i;p['steering']['native_tick']=p['native_tick'];p['body_measured_at']=p['steering']['measured_at']=1+i*.05
    shape=s.preview(p,.1,0.,1+i*.05);last=check(shape,p,last);s.commit(shape);trajectory.append(shape)
checks['full_rate_limited_transition_independent']=abs(trajectory[-1]['selected'][1])<1e-12 and all(abs(b['delta']-a['delta'])<=.030000001 for a,b in zip(trajectory,trajectory[1:]))
checks['stop_never_adds_motion']=s.preview(p,0.,0.,3.)['selected']==[0.,0.]
bad=copy.deepcopy(packet);bad['steering']['native_tick']+=1
checks['future_encoder_red']=red('future_encoder',lambda:measured(bad,1.))
bad=copy.deepcopy(packet);bad['steering']['position'][0]=float('nan')
checks['nonfinite_encoder_red']=red('nan_encoder',lambda:measured(bad,1.))
checks['stale_encoder_red']=red('stale_encoder',lambda:measured(packet,1.051))
checks['reverse_request_red']=red('reverse',lambda:s.preview(p,-.1,0.,3.))
checks['nonmonotonic_time_red']=red('backward_time',lambda:s.preview(packet,.1,0.,1.))
bad=copy.deepcopy(packet);bad['body'][3]=.04
checks['unsettled_restart_waits_without_motion']=SteeringContinuity().preview(bad,.1,0.,1.)['selected']==[0.,0.]

# Actual nested dispatch method, isolated only at packet and certificate boundary.
source=R/'experiments/v963_continuous_dynamic/ros_bridge.py';tree=ast.parse(source.read_text())
run=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='run')
bridge=next(n for n in run.body if isinstance(n,ast.ClassDef)and n.name=='Bridge')
method=next(n for n in bridge.body if isinstance(n,ast.FunctionDef)and n.name=='dispatch_command')
ns=dict(time=SimpleNamespace(monotonic=lambda:1.),task=dict(goal_xy=[4.,-2.]),require=lambda ok,msg:None if ok else(_ for _ in()).throw(AssertionError(msg)),json=json)
exec(compile(ast.Module(body=[method],type_ignores=[]),str(source),'exec'),ns)
import command_tube
original_admit=command_tube.admit;admissions=[]
def admit(p,source,v,w,known,now):
    admissions.append([v,w]);return dict(passed=True,v=v,w=w,body_native_tick=p['native_tick'],issued_at=now)
command_tube.admit=admit
node=SimpleNamespace(latest=dict(phase='RUNNING'),forward=SimpleNamespace(request=lambda v,w:True),
    motion=SimpleNamespace(decision_snapshot=lambda:(copy.deepcopy(packet),dict(support_bounds=None))),
    planner_proxy=SimpleNamespace(known=[]),steering_continuity=SteeringContinuity(),retained_proof=None,last_nominal_at=1.,
    tube_decisions=[],command_sequence=0,commands=[],sent=[],admission_deferrals=[],guard_failure=None)
node.send=node.sent.append
try:
    ns['dispatch_command'](node,SimpleNamespace(linear=SimpleNamespace(x=.1),angular=SimpleNamespace(z=0.)))
    checks['actual_dispatch_shapes_before_admission']=admissions==[first['selected']]
    checks['actual_dispatch_exact_certified_command']=len(node.sent)==1 and [node.sent[0]['v'],node.sent[0]['w']]==admissions[0]
    checks['actual_dispatch_commits_only_selected_certificate']=node.steering_continuity.last==dict(at=1.,delta=first['delta'])and node.guard_failure is None
finally:command_tube.admit=original_admit

# Full1820-tick production schedule, explicit kinematic fixture (zero model).
spec=importlib.util.spec_from_file_location('v962_worker_fixture',R/'experiments/v962_continuous_handoff/worker.py')
worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
class Fixture:
    def __init__(self):self.count=0;self.state=np.zeros(5);self.commands=[]
    def body(self):return self.state.copy()
    def steering_sample(self):
        k=K if self.count<=420 else 0.;return np.array([math.atan(.6*k/(1-.27*k)),math.atan(.6*k/(1+.27*k)),0.,0.])
    def step(self,v,w):self.state[:3]=worker.nominal_step(self.state[:3],v,w);self.state[3:]=v,w;self.commands.append([self.count,v,w]);self.count+=1
model=Fixture();task=json.loads((R/'experiments/v959_hold_response18/TASKS.json').read_text())[6]
bodyrows,servo,reference,shapes,origin=worker.execute(model,task,dict(deadline_unix=1e99),{},clock=lambda:0.,monotonic=lambda:1.+model.count*.01,sleep=lambda _:None)
checks['full_worker_1820_and_full1400_evaluation']=model.count==1820 and len(reference)==1400 and len(shapes)==280 and len(bodyrows)==len(servo)==1820
checks['exact_original420_command_prefix']=all([c[1],c[2]]==(task['warm']if c[0]<200 else task['command']if c[0]<220 else[0.,0.])for c in model.commands[:420])
checks['twelve_second_forward_complete']=all(c[1]==.1 for c in model.commands[420:1620])
checks['entire_final_two_second_brake']=all(c[1:]==[0.,0.]for c in model.commands[1620:])
checks['full_worker_reference_corresponds']=np.max(abs(np.asarray(bodyrows)[420:,:3]-reference))<1e-8
checks['late_position_fault_detected']=np.max(np.linalg.norm((np.asarray(bodyrows)[420:,:3]+np.array([.05,0.,0.]))[:,:2]-np.asarray(reference)[:,:2],axis=1))>.04
from authority import component_authorized,ready_for_navigation
checks['closed_before_root_authority']=red('no_root',component_authorized)
checks['route_closed_before_handoff']=red('no_handoff',ready_for_navigation)
prior=json.loads((R/'records/nav2_v955_v960_20261109/v960_hold_response_closure_FINAL_INDEPENDENT_AUDIT.json').read_text())
checks['independent_original18_passed']=prior['passed']
for folder in [C,R/'experiments/v962_continuous_handoff',R/'experiments/v963_continuous_dynamic',R/'experiments/v964_continuous_closure']:
    for p in folder.glob('*.py'):ast.parse(p.read_text(),str(p))
checks['all_source_ast']=True
result=dict(passed=bool(all(checks.values())),checks={k:bool(v)for k,v in checks.items()},negative_reasons=rejected,
    models=0,integrations=0,nonphysical_fixture_ticks=1820,scope='Saved steering handoff symptom and actual production dispatch/worker software seams; not new physical qualification.')
(O/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));assert result['passed']
