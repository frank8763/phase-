"""Pure-math comparison against the original swept-support implementation."""
import copy
import hashlib
import importlib.abc
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]; HERE = Path(__file__).resolve().parent; OUT = ROOT/'runs'/HERE.name
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','coupled_model','factory','physical','rclpy'}:
            raise AssertionError('NO_MODEL_BRIDGE_MATH:'+name)
sys.meta_path.insert(0,NoModel())
from route_event import exact_module
from causal_bridge_field import all_future
from route_context import dump

def main():
    assert sorted(os.sched_getaffinity(0)) == [4]
    os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    result_path=OUT/'BRIDGE_FIELD_MATH_QUALIFICATION.json'; assert not result_path.exists()
    source=ROOT/'runs/v858_nav2_verified/v1370/rpp_default_horizon_m1_s01_main/CAUSAL_PREDICTION_MODEL.json'
    snapshot=json.loads(source.read_text()); before=copy.deepcopy(snapshot)
    reference_path=ROOT/'experiments/v1020_terminal_two_route_development/periodic_support.py'
    reference=exact_module('v1397_original_swept_math',reference_path)
    t=snapshot['periodic']['last']; tick=snapshot['periodic']['source_tick']
    value=all_future(snapshot,current_native=tick,current_sim_time=t)
    for start in (0.,t,t+123.456):
        support=reference.swept_bounds(snapshot['periodic']['vertices'],start,start+math.tau/.32)
        lower=[-float(support[8]),-float(support[12])];upper=[float(support[0]),float(support[4])]
        assert max(abs(a-b) for a,b in zip(lower+upper,value['lower_xy']+value['upper_xy']))<=1e-12
    # Independently enumerate each vertex at257 phases. This is mathematical
    # enclosure verification, not a trajectory/scan/physical experiment.
    checked=0; maximum_violation=-math.inf
    for direction in (0,4):
        for c,a,b in snapshot['periodic']['vertices'][direction]:
            for i in range(257):
                x=c+a*math.sin(math.tau*i/256)+b*math.cos(math.tau*i/256)
                axis=direction//4; maximum_violation=max(maximum_violation,value['lower_xy'][axis]-x,x-value['upper_xy'][axis]);checked+=1
    assert maximum_violation<=1e-12 and snapshot==before
    negatives=[]
    def reject(name,s):
        try:all_future(s,current_native=tick,current_sim_time=t)
        except (AssertionError,ValueError,KeyError,TypeError):negatives.append(name)
        else:raise AssertionError('BRIDGE_NEGATIVE_ACCEPTED:'+name)
    for name,mutate in [
        ('future_coefficient',lambda s:s['periodic'].__setitem__('source_tick',tick+1)),
        ('future_coefficient_time',lambda s:s['periodic'].__setitem__('last',t+.1)),
        ('actor_truth_allowed',lambda s:s.__setitem__('online_actor_truth',True)),
        ('changed_frequency',lambda s:s['periodic'].__setitem__('omega',.33)),
        ('changed_amplitude_prior',lambda s:s['class_assumptions'].__setitem__('amplitude_m',.26)),
        ('missing_direction',lambda s:s['periodic']['vertices'].pop()),
        ('nonfinite_vertex',lambda s:s['periodic']['vertices'][0][0].__setitem__(0,float('nan'))),
    ]:
        changed=copy.deepcopy(snapshot);mutate(changed);reject(name,changed)
    result=dict(passed=True,scope='current coefficient full-period enclosure pure math only',
                saved_snapshot_not_current_fresh_source=True,coefficient_source_tick=tick,
                original_swept_full_period_comparisons=3,independent_vertex_phase_checks=checked,
                maximum_sample_enclosure_violation_m=maximum_violation,input_unchanged=True,
                original_HORIZON_planner_unchanged=True,negative_cases=negatives,
                field={k:v for k,v in value.items() if k!='input_periodic'},
                physical_admission=False,models=0,analytical_native=0,physical_native=0)
    dump(result_path,result)
    files=[HERE/'causal_bridge_field.py',HERE/'qualify_bridge_field.py',source,reference_path]
    dump(OUT/'BRIDGE_FIELD_SOURCE_FREEZE.json',dict(files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},physical_admission=False))
    print(json.dumps(result))

if __name__=='__main__': main()
