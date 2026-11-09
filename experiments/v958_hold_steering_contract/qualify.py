"""Prospective contract, actual old trace refusal, geometric start seam; no physics."""
import importlib.abc
import json
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoModel());ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/v958_hold_steering_contract'
from vehicle_control import Adapter,base
from response_contract import evaluate,reference_start_compatible

setup=json.loads((ROOT/'runs/v858_nav2_verified/v956/response_03/physics/SETUP.json').read_text())
bounds=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second'])
def make(cls,last):
    a=cls.__new__(cls);a.dt=.01;a.last=np.array(last,float);a.integral=0.;a.mode='DRIVING'
    a.wheelbase=.6;a.track=.54;a.radius=.12;a.center_limit=.42722137342572125;a.max_curvature=np.tan(a.center_limit)/a.wheelbase
    a.commands=SimpleNamespace(lower=bounds[:,0],upper=bounds[:,1],rate=rates*.08,legal=lambda v:bool(np.all(v>=bounds[:,0])and np.all(v<=bounds[:,1])))
    return a


checks={};a=make(Adapter,[-.36,-.52,1.,1.]);original=a.last.copy();outputs=[]
for _ in range(200):outputs.append(a.compute(0.,0.,.01,-.02).copy())
outputs=np.array(outputs)
checks['holds_steering_entire_two_seconds']=np.all(outputs[:,:2]==original[:2])
checks['drive_targets_brake_to_zero']=np.array_equal(outputs[-1,2:],np.zeros(2))
checks['actuator_original_slew']=np.all(abs(np.diff(np.vstack([original,outputs]),axis=0))<=rates*.01+1e-12)
checks['no_hidden_differential_actuation']=np.all(outputs[:,2]==outputs[:,3])
maximum=0.;count=0
for v in[-.1,.1]:
    for k in[-.758770385,0.,.758770385]:
        for yaw in[-.1,0.,.1]:
            a=make(Adapter,[0,0,0,0]);b=make(base.Adapter,[0,0,0,0])
            maximum=max(maximum,float(abs(a.compute(v,v*k,0.,yaw)-b.compute(v,v*k,0.,yaw)).max()));count+=1
checks['moving_map_unchanged']=maximum==0.
data=np.zeros((420,5));servo=np.tile([-.36,-.52,0.,0.],(420,1));origin=np.zeros(5)
metric,_=evaluate(data,servo,origin,dict(command=[0.,0.]))
checks['turned_stop_accepted_only_prospectively']=all(metric['checks'].values())and not metric['final_measured_steering_neutral_observation']and not metric['forward_handoff_qualified']
data[285,4]=-.0301472199296381
metric,_=evaluate(data,servo,origin,dict(command=[0.,0.]))
checks['v956_original_settle_violation_still_fails']=not metric['checks']['settled_by_half_second']
k=-.758770385;t=k*.6
steer=[np.arctan(t/(1-k*.27)),np.arctan(t/(1+k*.27))]
checks['turned_wheels_cannot_start_straight']=not reference_start_compatible(steer,.1,0.)
checks['matching_curved_reference_is_only_geometric_compatible']=reference_start_compatible(steer,.1,.1*k)
checks['zero_speed_not_forward_handoff']=not reference_start_compatible(steer,0.,0.)
result=dict(passed=bool(all(checks.values())),checks={k:bool(v)for k,v in checks.items()},moving_cases=count,
    models=0,integrations=0,physical_authority=False,physical_response_qualified=False,
    scope='Prospective stopping definition and necessary geometric handoff seam only. No regrading, new physical response or executable corridor proof.')
(OUT/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));assert result['passed']
