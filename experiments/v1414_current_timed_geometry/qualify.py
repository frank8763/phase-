"""Original timed-support equivalence, zero model/physical integrations."""
import copy
import hashlib
import importlib.abc
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','vehicle','torch','coupled_model','prediction','factory','physical','rclpy'}:raise AssertionError('TIMED_GEOMETRY_MATH_NO_MODEL:'+name)


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));sys.meta_path.insert(0,NoModel())
    assert not O.exists();O.mkdir();read=lambda p:json.loads(p.read_text())
    saved=R/'runs/v1413_current_reserve_qualification';data=read(saved/'FIXED_INPUTS.json');snapshot=read(saved/'CAUSAL_SNAPSHOT.json');setup=read(saved/'SETUP.json');origin=data['origin'];tick=origin['native_tick']
    old=exact('v1414_original_timed_support',R/'experiments/v1383_exact_timed_handoff/geometry_contract.py');new=exact('v1414_current_origin_timed_support',C/'geometry.py')
    import numpy as np
    reference=old.Geometry(setup['known'],snapshot);current=new.Geometry(setup['known'],snapshot,origin_native=tick,origin_sim_time=origin['sim_time'])
    b=origin['body'];s=np.array([b[0],b[1],b[2],b[3],origin['body_lateral'],b[4],0.,0.]);path=np.repeat(s[None,:],201,axis=0)
    maximum=0.;cases=0
    for offset in [0,1,5,10,37,100,200,700]:
        t=tick+offset
        for variant in [0,1,2]:
            a=path.copy()
            if variant==1:a[:,0]+=np.linspace(0.,.04,201)
            if variant==2:a[:,1]+=np.linspace(0.,-.03,201);a[:,2]+=np.linspace(0.,.02,201)
            old_polygon=reference.polygon(t);new_polygon=current.polygon(t)
            assert old_polygon.shape==new_polygon.shape
            maximum=max(maximum,float(np.max(abs(old_polygon-new_polygon))),abs(reference.actual(a[0,:5],t)-current.actual(a[0,:5],t)),abs(reference.tube(a,t)-current.tube(a,t)))
            cases+=1
    assert maximum<=1e-12
    translated=copy.deepcopy(snapshot);shift=100003;translated['periodic']['source_tick']+=shift
    equivalent=new.Geometry(setup['known'],translated,origin_native=tick+shift,origin_sim_time=origin['sim_time'])
    assert abs(current.tube(path,tick)-equivalent.tube(path,tick+shift))<=1e-12
    negatives=[]
    def reject(name,fn):
        try:fn()
        except(AssertionError,ValueError,KeyError):negatives.append(name)
        else:raise AssertionError('TIMED_GEOMETRY_NEGATIVE_ACCEPTED:'+name)
    changed=copy.deepcopy(snapshot);changed['periodic']['source_tick']=tick+1;reject('future_coefficients',lambda:new.Geometry(setup['known'],changed,origin_native=tick,origin_sim_time=origin['sim_time']))
    changed=copy.deepcopy(snapshot);changed['online_actor_truth']=True;reject('online_truth',lambda:new.Geometry(setup['known'],changed,origin_native=tick,origin_sim_time=origin['sim_time']))
    changed=copy.deepcopy(snapshot);changed['class_assumptions']['amplitude_m']=.3;reject('changed_motion_class',lambda:new.Geometry(setup['known'],changed,origin_native=tick,origin_sim_time=origin['sim_time']))
    changed=copy.deepcopy(snapshot);changed['last_observed_time']=origin['sim_time']+.01;reject('future_observation_time',lambda:new.Geometry(setup['known'],changed,origin_native=tick,origin_sim_time=origin['sim_time']))
    reject('unaligned_native_clock',lambda:new.Geometry(setup['known'],snapshot,origin_native=tick,origin_sim_time=origin['sim_time']+.0001))
    reject('noninteger_origin',lambda:new.Geometry(setup['known'],snapshot,origin_native=float(tick),origin_sim_time=origin['sim_time']))
    reject('time_before_bound_origin',lambda:current.polygon(tick-1))
    value=dict(passed=True,closed=True,models=0,analytical_native=0,physical_native=0,replay_native=0,mathematical_paths_not_model_predictions=True,comparison_cases=cases,maximum_original_geometry_error=maximum,native_label_translation_invariant=True,negative_checks=negatives,measured_origin_repeated201_pose_time_geometry_lower_m=current.tube(path,tick),full_model_or_physical_admission=False,closed_unix=time.time())
    (O/'QUALIFICATION.json').write_text(json.dumps(value,indent=2)+'\n')
    files=[*C.iterdir(),saved/'FIXED_INPUTS.json',saved/'SETUP.json',saved/'CAUSAL_SNAPSHOT.json',R/'experiments/v1383_exact_timed_handoff/geometry_contract.py',R/'experiments/v1020_terminal_two_route_development/periodic_support.py',R/'experiments/v855_renewal_worker/exact_footprint.py',R/'experiments/v1366_canonical_timed_lattice/build_polygons.py',R/'experiments/v934_rpccr_certified_recovery/polygon_geometry.py',R/'experiments/v1397_event_handoff_integration/causal_bridge_field.py',R/'experiments/v1397_event_handoff_integration/route_event.py']
    hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files if p.is_file()}
    (O/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files=hashes,qualification='runs/v1414_current_timed_geometry/QUALIFICATION.json',models=0,physical_admission=False),indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
