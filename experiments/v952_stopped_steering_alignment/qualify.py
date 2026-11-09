"""Actual failed inputs plus differential/phase boundaries; no model or dynamics."""
import ast
import copy
import importlib.abc
import importlib.util
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
CODE=Path(__file__).resolve().parent;ROOT=CODE.parents[1];OUT=ROOT/'runs/v952_stopped_steering_alignment'
RAW=ROOT/'runs/v858_nav2_verified/v950/response_03'
from vehicle_control import Adapter,old,STABLE_TICKS
spec=importlib.util.spec_from_file_location('v949_failed_adapter',ROOT/'experiments/v949_steering_handoff/vehicle_control.py')
failed=importlib.util.module_from_spec(spec);spec.loader.exec_module(failed)
setup=json.loads((RAW/'physics/SETUP.json').read_text())
limits=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second'])


def make(cls,last=None,encoders=lambda:([0.,0.],[0.,0.])):
    obj=cls.__new__(cls);obj.dt=.01;obj.last=np.zeros(4)if last is None else np.asarray(last,float).copy();obj.integral=0.
    obj.wheelbase=.60;obj.track=.54;obj.radius=.12;obj.center_limit=.42722137342572125
    obj.max_curvature=np.tan(obj.center_limit)/obj.wheelbase
    obj.commands=SimpleNamespace(lower=limits[:,0],upper=limits[:,1],rate=rates*.08,
        legal=lambda v:bool(np.all(v>=limits[:,0])and np.all(v<=limits[:,1])))
    obj.encoders=encoders;obj.mode='DRIVING';obj.stable_ticks=0
    return obj


commands=json.loads((RAW/'physics/BODY_COMMANDS.json').read_text())
with np.load(RAW/'physics/NATIVE_TRACE.npz')as trace:actual=trace['ctrl'][:,setup['actuator_ids']].copy()
a=make(failed.Adapter);bad=np.asarray([a.compute(v,w,mv,mw,stale).copy()for _,v,w,mv,mw,stale in commands])
checks=dict(failed_adapter_exact_reconstruction=float(abs(actual-bad).max())<=1e-8)
a=make(Adapter);outputs=[];phases=[]
for _,v,w,mv,mw,stale in commands:
    outputs.append(a.compute(v,w,mv,mw,stale).copy());phases.append(a.mode)
outputs=np.asarray(outputs)
checks['actual_moving_prefix_exact']=float(abs(outputs[:220]-actual[:220]).max())<=1e-8
checks['old_bug_centers_on_first_brake']=bool(np.max(abs(actual[220,:2]-actual[219,:2]))>.01)
checks['new_first_brake_holds_steering']=np.array_equal(outputs[220,:2],outputs[219,:2])
checks['all_actual_moving_body_brakes_hold_steering']=all(np.array_equal(outputs[i,:2],outputs[i-1,:2])for i in range(220,len(commands))if abs(commands[i][3])>.005 or abs(commands[i][4])>.005)

# Differential on the real original moving function, varying measurements and
# controller state; no generated trajectory or new empirical response claim.
maximum=0.;cases=0
for v in [-.1,-.05,.005,.05,.1]:
    for k in [-.758770385,0.,.758770385]:
        for mv in [-.1,0.,.1]:
            for mw in [-.1,0.,.1]:
                lhs=make(old.Adapter,[-.2,.3,-.4,.5]);rhs=make(Adapter,[-.2,.3,-.4,.5])
                lhs.integral=rhs.integral=.13
                maximum=max(maximum,float(abs(lhs.compute(v,v*k,mv,mw)-rhs.compute(v,v*k,mv,mw)).max()));cases+=1
checks['fixed_grid_original_moving_map_exact']=maximum==0.
a=make(Adapter,[-.36,-.52,0.,0.]);before=a.last.copy()
for _ in range(STABLE_TICKS-1):a.compute(0.,0.,0.,0.)
checks['nine_stopped_ticks_do_not_align']=np.array_equal(a.last,before)and a.mode=='BRAKING'
a.compute(0.,0.,0.,0.)
checks['tenth_stopped_tick_starts_bounded_alignment']=a.mode=='ALIGNING'and np.max(abs(a.last[:2]))<.52 and np.all(abs(a.last-before)<=rates*.01+1e-12)
before=a.last.copy();a.compute(0.,0.,.006,0.)
checks['body_motion_immediately_relocks_steering']=a.mode=='BRAKING'and a.stable_ticks==0 and np.array_equal(a.last[:2],before[:2])
for _ in range(STABLE_TICKS-1):a.compute(0.,0.,0.,0.)
checks['new_ten_tick_body_stop_required']=a.mode=='BRAKING'
a.compute(0.,0.,0.,0.)
checks['stable_stop_reenables_alignment']=a.mode=='ALIGNING'
encoder_cases=[]
for name,encoder in [('turned',lambda:([-.2,-.3],[0.,0.])),('moving',lambda:([0.,0.],[.1,0.])),('missing',None),('nonfinite',lambda:([float('nan'),0.],[0.,0.]))]:
    q=make(Adapter,encoders=encoder);q.mode='ALIGNING';previous=q.last.copy();reason=None
    try:q.compute(.1,0.,0.,0.)
    except ValueError as error:reason=str(error)
    encoder_cases.append(dict(case=name,rejected=reason is not None,reason=reason))
    checks[name+'_encoder_cannot_resume']=reason is not None and np.array_equal(q.last,previous)
q=make(Adapter);q.mode='ALIGNING'
checks['measured_neutral_allows_original_forward']=np.array_equal(q.compute(.1,0.,0.,0.),make(old.Adapter).compute(.1,0.,0.,0.))
checks['original_full_slew']=bool(np.all(abs(np.diff(np.vstack([np.zeros(4),outputs]),axis=0))<=rates*.01+1e-12))
checks['original_limits']=bool(np.all(outputs>=limits[:,0])and np.all(outputs<=limits[:,1]))
for p in CODE.glob('*.py'):ast.parse(p.read_text(),str(p))
checks['source_ast']=True
checks={k:bool(v)for k,v in checks.items()}
result=dict(passed=all(checks.values()),checks=checks,fixed_moving_cases=cases,
    moving_differential_max_error=maximum,original_failed_input_rows=len(commands),encoder_cases=encoder_cases,
    models=0,integrations=0,physical_response_qualified=False,
    scope='New controller outputs on fixed old measurements and explicit boundary fixtures, not a counterfactual vehicle trajectory or physical success.')
np.savez_compressed(OUT/'CONTROLLER_OUTPUTS_ON_OLD_MEASUREMENTS.npz',original_actual=actual,new_controller_only=outputs)
(OUT/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));assert result['passed']
