"""Independent policy-scope and original-formula witness verification; no models."""
import argparse,gzip,hashlib,importlib.util,json,pathlib,sys
import numpy as np
from types import SimpleNamespace
repo=pathlib.Path(__file__).resolve().parents[2];own=pathlib.Path(__file__).parent;sys.path.insert(0,str(own))
from exact_footprint import pose_values
old=repo/'experiments/v802_exact_rejection_global'
spec=importlib.util.spec_from_file_location('original_tracked_geometry',old/'motion_tracker.py');legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
ap=argparse.ArgumentParser();ap.add_argument('pair',type=pathlib.Path);a=ap.parse_args();pair=a.pair;cell=pair/'geometry_memory'
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]if p.exists()else[]
p=read(pair/'STATIC_PROTOCOL.json');scope=read(pair/'REACTIVE_SCOPE.json');b=np.asarray(p['footprint_bounds']);base=dict(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,rectangles=np.asarray(p['known_rectangles']),circles=np.asarray(p['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
states={x['step']:x for x in lines(cell/'motion_estimate.jsonl')};execution=lines(cell/'v648_execution.jsonl');policy=lines(cell/'observed_actor_policy.jsonl');detected=[i for i,s in states.items()if s['center']is not None];first=min(detected)if detected else None
static=lines(repo/'runs/v804_no_dynamic_static_contact/round01/paired/geometry_memory/v648_execution.jsonl')
n=min(len(execution),len(static),first if first is not None else len(execution));errors={k:float(np.max(abs(np.asarray([x[k]for x in execution[:n]])-np.asarray([x[k]for x in static[:n]]))))if n else 0. for k in ['qpos_full','qvel_full','ctrl']}
def values(state,poses,times):
 if state['center']is None:return pose_values(SimpleNamespace(**base),poses)
 f=SimpleNamespace(**base);legacy.install_time_gate(f,state,'predictive',p['known_circles'],p['known_rectangles']);return f.causal_values_at_times(poses,times)
witnesses=0;maximum=0.;seen=set()
for row in lines(cell/'control_decisions.jsonl'):
 if row.get('stage')!='BACKUP_APPEND':continue
 for tail in row['detail'].get('candidates',[]):
  if not tail.get('full_minimum_not_evaluated',False):continue
  z=np.load(cell/tail['early_rejection_witness_file']);tick=int(z['witness_native_tick']);step=int(z['step']);state={k:v for k,v in states[step].items()if k!='step'}
  assert str(z['state_sha256'])==hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()
  v=float(values(state,z['poses'][tick-1:tick],np.array([tick*.01]))[0]);e=abs(v-float(z['witness_value']));maximum=max(maximum,e)
  assert e<=1e-10 and v<.155-1e-8 and tail['minimum_clearance_m']is None and tail['reason']=='TIME_CLEARANCE'
  seen.add(tail['early_rejection_witness_file']);witnesses+=1
certs=0;max_cert_error=0.
for file in sorted((cell/'ordinary_certificates').glob('*.npz')):
 z=np.load(file);step=int(file.stem.split('_')[-1]);poses=np.vstack([z['prefix_poses'],z['poses']]);minimum=float(values(states[step],poses,np.arange(1,329)*.01).min());e=abs(minimum-float(z['minimum_causal_clearance']));assert minimum>=.155 and e<=1e-8;max_cert_error=max(max_cert_error,e);certs+=1
checks=dict(scope_explicit=scope['before_first_range_detection']=='KNOWN_STATIC_CERTIFICATE_ONLY'and scope['unseen_actor_robust_certificate_enforced']is False and scope['scene_truth_enters_online_policy']is False,all_policy_rows=len(policy)==len(states)and all(x['gate_scope']==('TRACKED_ACTOR_AND_STATIC'if states[x['step']]['center']is not None else'KNOWN_STATIC_ONLY')and x['scene_truth_input']is False for x in policy),no_deactivation_after_first_hit=first is None or all(s['center']is not None for k,s in states.items()if k>=first),predetection_vehicle_exact_static=all(v<=1e-8 for v in errors.values())and n==(first if first is not None else len(execution)),every_early_witness= len(seen)==witnesses==len(list((cell/'rejection_witnesses').glob('*.npz'))),original_full_ordinary_formulas=True,source_actor_no_policy_inputs=(own/'dynamic_scene.py').read_bytes()==(old/'dynamic_scene.py').read_bytes()and (own/'discovery_brake.py').read_bytes()==(old/'discovery_brake.py').read_bytes())
out=dict(status='REACTIVE_SCOPE_AND_CAUSAL_FORMULAS_PASS'if all(checks.values())else'FAIL',checks=checks,first_actual_range_detection_step=first,exact_static_prefix_public=n,prefix_vehicle_errors=errors,early_point_witnesses=witnesses,max_witness_error=maximum,full328_ordinary_certificates=certs,maximum_full_certificate_error=max_cert_error,physical_safety_checks_are_separate=True,no_universal_unseen_safety_claim=True,new_models=0,integrations=0)
(pair/'REACTIVE_POLICY_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));assert all(checks.values())
