"""Exact old reconstruction, new servo outputs and encoder gate; zero dynamics."""
import copy
import importlib.abc
import json
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoModel())
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/v949_steering_handoff'
OUT.mkdir(exist_ok=True)
from vehicle_control import Adapter, old
from alignment import ready
RAW=ROOT/'runs/v858_nav2_verified/v945/main_we'
setup=json.loads((RAW/'physics/SETUP.json').read_text())
limits=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second'])


def make(cls,last=None):
    obj=cls.__new__(cls);obj.dt=.01;obj.last=np.zeros(4)if last is None else np.array(last).copy();obj.integral=0.
    obj.wheelbase=.60;obj.track=.54;obj.radius=.12;obj.center_limit=.42722137342572125
    obj.max_curvature=np.tan(obj.center_limit)/obj.wheelbase
    obj.commands=SimpleNamespace(lower=limits[:,0],upper=limits[:,1],rate=rates*.08,
        legal=lambda x:bool(np.all(x>=limits[:,0])and np.all(x<=limits[:,1])))
    return obj


commands=json.loads((RAW/'physics/BODY_COMMANDS.json').read_text())
with np.load(RAW/'physics/NATIVE_TRACE.npz')as trace:recorded=trace['ctrl'][:,setup['actuator_ids']].copy()
previous=make(old.Adapter);maximum=0.
for i,(_,v,w,mv,mw,stale)in enumerate(commands):
    maximum=max(maximum,float(np.max(abs(previous.compute(v,w,mv,mw,stale)-recorded[i]))))
corridor=json.loads((RAW/'RECOVERY_CORRIDORS.json').read_text())[0]
tick=corridor['install_packet']['native_tick'];last=recorded[tick-1]
previous=make(old.Adapter,last);candidate=make(Adapter,last);new=[];old_zero=[]
for _ in range(100):
    old_zero.append(previous.compute(0.,0.,0.,0.).copy());new.append(candidate.compute(0.,0.,0.,0.).copy())
new=np.asarray(new);old_zero=np.asarray(old_zero)
checks=dict(exact_old_adapter_reconstruction=maximum<=1e-8,
    old_zero_retains_bad_steering=bool(np.max(abs(old_zero[-1,:2]))>.5),
    new_zero_centers_steering=bool(np.max(abs(new[-1,:2]))==0),
    new_zero_drive_target=bool(np.max(abs(new[:,2:]))==0),
    original_per_second_slew=bool(np.all(abs(np.diff(np.vstack([last,new]),axis=0))<=rates*.01+1e-12)))
# Counterfactual adapter outputs under recorded measured body rates: not a new
# vehicle trajectory. Isolate the documented straight-reference steering loop.
previous=make(old.Adapter,last);candidate=make(Adapter,last);steer_old=[];steer_new=[]
for _,_,_,mv,mw,_ in commands[tick:corridor['end_packet']['native_tick']]:
    steer_old.append(previous.compute(.1,0.,mv,mw)[:2].copy())
    steer_new.append(candidate.compute(.1,0.,mv,mw)[:2].copy())
checks['straight_reference_has_no_inner_yaw_steering_oscillation']=bool(np.max(abs(np.asarray(steer_new)[50:]))==0)
packet=dict(native_tick=10,body=[0.,0.,0.,0.,0.],body_measured_at=100.,
    steering=dict(native_tick=10,measured_at=100.,position=[0.,0.],velocity=[0.,0.]))
checks['actual_neutral_encoder_gate']=ready(packet,100.)
bad=copy.deepcopy(packet);bad['steering']['position']=[-.36,-.52]
checks['stopped_body_with_turned_wheels_rejected']=not ready(bad,100.)
bad=copy.deepcopy(packet);bad['steering']['velocity']=[.1,0.]
checks['moving_steering_rejected']=not ready(bad,100.)
errors=[]
for case in ['missing','stale','incoherent','nonfinite']:
    bad=copy.deepcopy(packet)
    if case=='missing':del bad['steering']
    if case=='stale':bad['steering']['measured_at']=99.9
    if case=='incoherent':bad['steering']['native_tick']=9
    if case=='nonfinite':bad['steering']['position']=[float('nan'),0.]
    try:ready(bad,100.)
    except ValueError as error:errors.append(dict(case=case,reason=str(error)));checks[case+'_encoder_rejected']=True
    else:checks[case+'_encoder_rejected']=False
result=dict(passed=all(checks.values()),checks=checks,errors=errors,models=0,integrations=0,
    exact_old_adapter_rows=len(commands),old_control_max_error=maximum,
    new_command_neutral_after_ticks=int(np.flatnonzero(abs(new[:,:2]).max(axis=1)==0)[0]+1),
    steering_physical_response_qualified=False,full_route_ready=False,
    scope='Exact recorded old adapter reconstruction and explicit synthetic new-controller outputs. No new vehicle response or improved physical trajectory claim.')
(OUT/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));assert result['passed']
