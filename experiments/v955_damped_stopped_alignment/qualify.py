"""Exact old failure tape and real moving-map differential; zero physical models."""
import importlib.abc
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoModel())
ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent;OUT=ROOT/'runs/v955_damped_stopped_alignment'
from vehicle_control import Adapter


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


previous=load('actual_failed_v952',ROOT/'experiments/v952_stopped_steering_alignment/vehicle_control.py')
feedforward=load('v949_moving_map',ROOT/'experiments/v949_steering_handoff/vehicle_control.py')
RAW=ROOT/'runs/v858_nav2_verified/v953/response_01';setup=json.loads((RAW/'physics/SETUP.json').read_text())
limits=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second'])
with np.load(RAW/'BODY_AND_STEERING.npz')as f:enc=f['steering'].copy();old_phases=f['phases'].copy()
with np.load(RAW/'physics/NATIVE_TRACE.npz')as f:recorded=f['ctrl'][:,setup['actuator_ids']].copy()
commands=json.loads((RAW/'physics/BODY_COMMANDS.json').read_text())


def make(cls,last=None,encoders=lambda:([-.36,-.52],[0.,0.])):
    a=cls.__new__(cls);a.dt=.01;a.last=np.zeros(4)if last is None else np.asarray(last,float).copy();a.integral=0.
    a.wheelbase=.60;a.track=.54;a.radius=.12;a.center_limit=.42722137342572125;a.max_curvature=np.tan(a.center_limit)/a.wheelbase
    a.commands=SimpleNamespace(lower=limits[:,0],upper=limits[:,1],rate=rates*.08,
        legal=lambda value:bool(np.all(value>=limits[:,0])and np.all(value<=limits[:,1])))
    a.encoders=encoders;a.mode='DRIVING';a.stable_ticks=0;return a


checks={};i=[0]
def encoder():return([0.,0.],[0.,0.])if i[0]<0 else(enc[i[0],:2],enc[i[0],2:])
old=make(previous.Adapter,encoders=encoder);new=make(Adapter,encoders=encoder);rebuild=[];outputs=[];phases=[]
for tick,(_,v,w,mv,mw,stale)in enumerate(commands):
    i[0]=tick-1;rebuild.append(old.compute(v,w,mv,mw,stale).copy())
    outputs.append(new.compute(v,w,mv,mw,stale).copy());phases.append(new.mode)
outputs=np.asarray(outputs);rebuild=np.asarray(rebuild);phases=np.asarray(phases)
checks['old_actual_trace_exactly_reconstructed']=float(abs(rebuild-recorded).max())<=1e-8
checks['old_failure_one_tick_alignment_reproduced']=int(np.sum(old_phases=='ALIGNING'))==9
first=int(np.flatnonzero(phases=='ALIGNING')[0])
checks['new_alignment_stays_latched_on_actual_small_yaw']=np.all(phases[first:]=='ALIGNING')
checks['new_actual_tape_command_reaches_neutral']=abs(outputs[-1,:2]).max()==0.
checks['no_immediate_centering_at_stop_request']=np.array_equal(outputs[200,:2],outputs[199,:2])
checks['straight_moving_steering_not_excited_by_old_yaw']=abs(outputs[:200,:2]).max()==0.
maximum=0.;count=0
for v in [-.1,-.05,.005,.05,.1]:
    for k in [-.758770385,0.,.758770385]:
        for mv in [-.1,0.,.1]:
            for mw in [-.1,0.,.1]:
                lhs=make(feedforward.Adapter,[-.2,.3,-.4,.5]);rhs=make(Adapter,[-.2,.3,-.4,.5])
                lhs.integral=rhs.integral=.13
                maximum=max(maximum,float(abs(lhs.compute(v,v*k,mv,mw)-rhs.compute(v,v*k,mv,mw)).max()));count+=1
checks['moving_map_matches_v949_135_cases']=maximum==0.
a=make(Adapter,[-.36,-.52,0.,0.]);before=a.last.copy()
for _ in range(9):a.compute(0.,0.,0.,0.)
checks['body_stop_ten_tick_entry']=a.mode=='BRAKING'and np.array_equal(a.last,before)
a.compute(0.,0.,0.,0.);checks['tenth_tick_enters_alignment']=a.mode=='ALIGNING'
before=a.last.copy();u=a.compute(0.,0.,.001,.01)
checks['small_yaw_no_relock']=a.mode=='ALIGNING'and abs(u[:2]).max()<abs(before[:2]).max()
checks['rear_correction_opposes_yaw']=u[2]>0 and u[3]<0
checks['rear_correction_zero_mean']=abs(u[2]+u[3])<1e-12
checks['alignment_slew_not_instant']=np.max(abs(u[:2]-before[:2]))<=.006+1e-12
for label,v,w in [('yaw',0.,.030001),('speed',.030001,0.)]:
    q=make(Adapter);q.mode='ALIGNING'
    try:q.compute(0.,0.,v,w)
    except ValueError:checks[label+'_original_body_settle_envelope_rejected']=True
    else:checks[label+'_original_body_settle_envelope_rejected']=False
for label,callback in [('turned',lambda:([-.2,-.3],[0.,0.])),('moving',lambda:([0.,0.],[.1,0.])),('missing',None),('nonfinite',lambda:([float('nan'),0.],[0.,0.]))]:
    q=make(Adapter,encoders=callback);q.mode='ALIGNING'
    try:q.compute(.1,0.,0.,0.)
    except ValueError:checks[label+'_cannot_resume']=True
    else:checks[label+'_cannot_resume']=False
q=make(Adapter,encoders=lambda:([0.,0.],[0.,0.]));q.mode='ALIGNING'
checks['measured_neutral_can_resume']=np.array_equal(q.compute(.1,0.,0.,0.),make(feedforward.Adapter).compute(.1,0.,0.,0.))
checks['control_bounds']=bool(np.all(outputs>=limits[:,0])and np.all(outputs<=limits[:,1]))
checks['control_rates']=bool(np.all(abs(np.diff(np.vstack([np.zeros(4),outputs]),axis=0))<=rates*.01+1e-12))
result=dict(passed=bool(all(checks.values())),checks={k:bool(v)for k,v in checks.items()},fixed_moving_cases=count,
    moving_max_difference=maximum,old_trace_controller_error=float(abs(rebuild-recorded).max()),
    old_rows=len(commands),models=0,integrations=0,physical_response_qualified=False,
    scope='Controller outputs on unchanged old measured inputs plus explicit boundary fixtures. Not new vehicle dynamics or proof of physical completion.')
np.savez_compressed(OUT/'OLD_MEASUREMENT_OUTPUTS.npz',original_actual=recorded,new_controller_only=outputs,new_phases=phases)
(OUT/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));assert result['passed']
