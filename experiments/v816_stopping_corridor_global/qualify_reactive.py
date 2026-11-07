"""Saved-array-only qualification: deliberate predetection change and tracked equivalence."""
import hashlib,importlib.util,json,pathlib,sys
import numpy as np
own=pathlib.Path(__file__).parent;repo=own.parents[1];sys.path.insert(0,str(own))
from motion_tracker import install_time_gate
from exact_footprint import pose_values
from types import SimpleNamespace
old=repo/'experiments/v802_exact_rejection_global'
spec=importlib.util.spec_from_file_location('old_v802_motion_gate',old/'motion_tracker.py');legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
read=lambda p:json.loads(p.read_text())
pair=repo/'runs/v804_no_dynamic_static_contact/round01/paired'
p=read(pair/'STATIC_PROTOCOL.json');b=np.asarray(p['footprint_bounds'])
base=dict(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,rectangles=np.asarray(p['known_rectangles']),circles=np.asarray(p['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
raw=repo/'runs/v802_exact_rejection_global/main_slot01/paired/geometry_memory/motion_estimate.jsonl'
unseen=read(raw) if False else json.loads(raw.read_text().splitlines()[-1])
tracked_file=repo/'runs/v697_rpccr_dynamic_initialization/v698_slot01/paired/geometry_memory/motion_estimate.jsonl'
tracked=next(json.loads(s)for s in tracked_file.open()if json.loads(s)['center']is not None)
poses=np.array([[-4.,-2.,0.],[-.6,-1.0,.12],[1.,-.8,0.],[3.5,-2.,-.3]])
poses=np.repeat(poses,83,axis=0)[:329]
errors=[]
for state in [unseen,tracked]:
 a=SimpleNamespace(**base);install_time_gate(a,state,'predictive',p['known_circles'],p['known_rectangles'])
 if state['center']is None:
  expected=pose_values(SimpleNamespace(**base),poses)
 else:
  f=SimpleNamespace(**base);legacy.install_time_gate(f,state,'predictive',p['known_circles'],p['known_rectangles']);expected=f.trajectory_values(poses,.01)
 errors.append(float(np.max(abs(a.trajectory_values(poses,.01)-expected))))
 poisoned=dict(state,anchor_xy=[999,999],phase_rad=999,actor_future_truth=[999,999])
 f=SimpleNamespace(**base);install_time_gate(f,poisoned,'predictive',p['known_circles'],p['known_rectangles']);assert np.array_equal(f.trajectory_values(poses,.01),expected)
assert max(errors)<=1e-12
unchanged=['dynamic_scene.py','scene_sensors.py','discovery_brake.py','future_guide.py','serial_predictor.py','reserved_recovery.py','joint_admission.py','recovery_supervisor.py']
assert all((own/n).read_bytes()==(old/n).read_bytes()for n in unchanged)
assert (own/'motion_tracker.py').read_text().split('def install_time_gate')[0]==(old/'motion_tracker.py').read_text().split('def install_time_gate')[0]
assert (own/'motion_tracker.py').read_text().split('def forecast_corridor_world')[1]==(old/'motion_tracker.py').read_text().split('def forecast_corridor_world')[1]
result=dict(status='REACTIVE_ZERO_MODEL_QUALIFICATION_PASS',static_only_before_hit_error=errors[0],tracked_original_gate_error=errors[1],poisoned_truth_keys_do_not_affect_gate=True,scene_sensor_brake_controller_bytes_unchanged=unchanged,positive_hit_tracker_unchanged=True,unseen_universal_guarantee_deliberately_removed=True,new_models=0,integrations=0)
out=repo/'runs/v816_stopping_corridor_global/pre_navigation';out.mkdir(parents=True,exist_ok=True);(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
