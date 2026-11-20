"""All-native complete-braking branches from the original response model.

Exact support extrema of the full rear-based rectangle over yaw +/-0.1 and
translation0.02 certify conservative separating distances, not centre points.
Every analytical model step remains isolated/locked CPU2 and separately counted.
"""
import copy
import hashlib
import importlib.abc
import json
import math
import os
from pathlib import Path
import signal
import sys
import time
import fcntl
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def read(p):return json.loads(Path(p).read_text())


def main():
    assert not (O/'BRAKING_WITNESS.json').exists(),'ALREADY_EVALUATED'
    frozen=read(O/'BRAKING_SOURCE_FREEZE.json')['files'];assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in frozen.items())
    from response_probe import NoPhysical
    sys.meta_path.insert(0,NoPhysical());begin=time.monotonic();steps=0
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('BRAKING_WITNESS_STOP')));signal.alarm(max(1,int(min(1500,1795165200-time.time()-120))))
    result=dict(passed=False,models=0,physical_native=0,physical_replay_native=0,analytical_native=0)
    with (R/'runs/v648_static_unknown/execution.lock').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            sys.path.insert(0,str(R/'experiments/v1114_coupled_steering_mode'))
            from logic import Predictor,initial,kernel,Adapter
            import numpy as np
            sys.path.insert(0,str(R/'experiments/v1377_timed_handoff_witness'))
            from snapshot_diagnostic import load,function,np as same_np
            source=read(O/'serialized03/RESPONSE_MODEL_PROBE.json');assert source['passed']
            raw=R/'runs/v858_nav2_verified/v1378/steering_response';setup=read(raw/'physics/SETUP.json')
            model=read(R/'runs/v858_nav2_verified/v1370/rpp_default_horizon_m1_s01_main/CAUSAL_PREDICTION_MODEL.json');assert model['periodic']['source_tick']==32200
            swept=load('v1379_original_periodic_support','experiments/v1020_terminal_two_route_development/periodic_support.py')
            clipped=function('experiments/v1366_canonical_timed_lattice/build_polygons.py','clipped')
            geometry=load('v1379_original_static','experiments/v855_renewal_worker/exact_footprint.py')
            from types import SimpleNamespace
            known=setup['known'];field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),rectangles=np.asarray(known['known_rectangles']),circles=np.asarray(known['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
            original_normals=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)]
            normals=np.c_[np.cos(np.arange(64)*math.tau/64),np.sin(np.arange(64)*math.tau/64)]
            corners=np.array([[-.14,-.375],[-.14,.375],[.74,-.375],[.74,.375]])
            radius=math.hypot(.74,.375);angular_full_cost=2*radius*math.sin(.1/2)
            polygon_cache={}
            def polygon(index):
                if index not in polygon_cache:
                    lower=model['last_observed_time']+max(0,index*.1-.22);upper=model['last_observed_time']+(index+1)*.1+.22
                    support=swept.swept_bounds(model['periodic']['vertices'],lower,upper)+.1
                    vertices=clipped(original_normals,support)
                    polygon_cache[index]=dict(vertices=vertices,lower_projected=np.min(vertices@normals.T,axis=0),interval=[lower,upper],support=support.tolist())
                return polygon_cache[index]
            def rear_states(states):
                a=np.asarray(states);return np.c_[a[:,0]-.3*np.cos(a[:,2]),a[:,1]-.3*np.sin(a[:,2]),a[:,2]]
            def bounds(states,start_offset):
                rear=rear_states(states);yaw=rear[:,2];cs=np.cos(yaw);sn=np.sin(yaw)
                maximum=np.full((len(rear),64),-math.inf)
                for x,y in corners:
                    # Rotate the corner into nominal world frame, then take its
                    # support maximum over the complete +/-0.1rad angle interval.
                    X=x*cs-y*sn;Y=x*sn+y*cs
                    A=X[:,None]*normals[:,0]+Y[:,None]*normals[:,1]
                    B=-Y[:,None]*normals[:,0]+X[:,None]*normals[:,1]
                    value=A*math.cos(.1)+abs(B)*math.sin(.1)
                    at=np.arctan2(B,A);inside=abs(at)<=.1
                    value=np.where(inside,np.hypot(A,B),value)
                    maximum=np.maximum(maximum,value)
                robot=rear[:,:2]@normals.T+maximum+.02
                indices=np.floor((3.9+(start_offset+np.arange(len(rear)))*.01)/.1+1e-10).astype(int)
                dynamic=np.empty(len(rear))
                for index in np.unique(indices):
                    mask=indices==index;dynamic[mask]=np.max(polygon(int(index))['lower_projected']-robot[mask],axis=1)
                # Static distance is1-Lipschitz under full footprint displacement.
                static=geometry.pose_values(field,rear)-.02-angular_full_cost
                # Native interpolation of nominal response uses actual predicted
                # translation/yaw increments, not the requested-speed assumption.
                if len(rear)>1:
                    travel=np.linalg.norm(np.diff(rear[:,:2],axis=0),axis=1)+radius*abs(np.diff(rear[:,2]))
                    interpolation=float(travel.max())
                else:interpolation=0.
                lower=float(np.minimum(dynamic,static).min())-interpolation
                return lower,float(dynamic.min()),float(static.min()),interpolation
            nominal=source['predicted_states'];whole=bounds(nominal,0);assert whole[0]>=.22-1e-8,('NOMINAL_FULL_TUBE_REJECTED',whole)
            p=Predictor(setup,initial(source['origin_packet']),kernel.PARAMETERS);p.adapter.__class__=Adapter;p.adapter.parked_target=None;p.adapter._steering_motion_active=False
            branches=[];minimum=math.inf;largest_speed=0.;brake_limit=200
            for index,row in enumerate(source['predicted_schedule']):
                assert time.time()<1795165200-100 and steps+brake_limit+1<246000,'ANALYTICAL_OR_ROOT_RESERVE'
                branch=copy.deepcopy(p);states=[branch.state.copy()]
                for _ in range(brake_limit):
                    state,u=branch.step(0.,0.,False);steps+=1;states.append(state.copy())
                array=np.asarray(states);lower,dynamic,static,interpolation=bounds(array,index);minimum=min(minimum,lower)
                rest=bool(abs(array[-1,[3,4,5]]).max()<=.003 and abs(array[-1,7])<=.03 and abs(branch.adapter.last[2:]).max()<=1e-10)
                body_caps=bool((abs(array[:,3:6])<=np.array([.13,.03,.16])+1e-8).all());largest_speed=max(largest_speed,float(abs(array[:,3]).max()))
                item=dict(before_native=32600+index,causal_complete_tube_lower_m=lower,dynamic_separation_lower_m=dynamic,static_lipschitz_lower_m=static,continuous_nominal_interpolation_allowance_m=interpolation,complete_stop_native=brake_limit,rest=rest,body_caps=body_caps)
                branches.append(item)
                if lower<.22-1e-8 or not rest or not body_caps:
                    result.update(first_rejected_brake=item);break
                state,u=p.step(*row['admitted'],False);steps+=1
                assert np.max(abs(state-np.asarray(nominal[index+1])))<=1e-8,'RESPONSE_NOMINAL_NOT_REPRODUCED'
            complete=len(branches)==len(source['predicted_schedule']) and all(x['causal_complete_tube_lower_m']>=.22-1e-8 and x['rest'] and x['body_caps'] for x in branches)
            result.update(passed=complete,nominal_tube_lower_m=whole[0],all_native_brake_states_covered=complete,
                branches=branches,minimum_complete_braking_tube_lower_m=minimum,maximum_braking_abs_speed_m_s=largest_speed,
                original_complete_stop_native=200,source_coefficient_native=32200,
                error_assumptions=dict(rear_translation_m=.02,yaw_rad=.1,time_s=.2),
                supporting_calibration_is_finite_saved_case_only=True,actual32210_moving_error_assumptions_not_yet_measured=True,
                physical_admission=False,actual_moving_response_qualified=False,
                geometry_method='complete rectangle support extrema over yaw interval and translation ball,64 separating axes of original16-support causal polygon; static full footprint Lipschitz, each native nominal interpolation allowance',
                conditional_not_universal_safety=True)
        except BaseException as exc:
            import traceback
            result.update(error=repr(exc),traceback=traceback.format_exc(),passed=False)
        finally:
            signal.alarm(0);result.update(analytical_native=steps,wall_s=time.monotonic()-begin,source_unchanged=all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in frozen.items()),closed=True)
            def scalar(x):
                if hasattr(x,'item'):return x.item()
                raise TypeError(type(x).__name__)
            target=O/'BRAKING_WITNESS.json';target.write_text(json.dumps(result,indent=2,default=scalar,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['branches','traceback']},default=scalar,allow_nan=False));return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
