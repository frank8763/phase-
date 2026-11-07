"""Supplementary original-kernel pointwise rejection witnesses; frozen full audit remains incomplete."""
import argparse,json,sys,hashlib,signal,time
import mujoco,mujoco.rollout
def forbidden(*a,**kw):raise AssertionError("NO_MODEL_SUPPLEMENT")
for n in ["MjModel","MjSpec","MjData","mj_step","mj_step1","mj_step2","mj_forward"]:setattr(mujoco,n,forbidden)
mujoco.rollout.rollout=forbidden
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError("SUPPLEMENT_300S")));signal.alarm(300)
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo/'experiments/v800_spatial_nominal_global'))
from motion_tracker import install_time_gate
ap=argparse.ArgumentParser();ap.add_argument('pair',type=Path);a=ap.parse_args();cell=a.pair/'geometry_memory'
read=lambda p:json.loads(p.read_text());lines=lambda p:list(map(json.loads,p.read_text().splitlines()))
p=read(a.pair/'STATIC_PROTOCOL.json');b=np.asarray(p['footprint_bounds']);base=dict(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,rectangles=np.asarray(p['known_rectangles']),circles=np.asarray(p['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
states={x['step']:x for x in lines(cell/'motion_estimate.jsonl')};fields={};checked=0;error=0.;seen=set();geometry_wall=0.;tails=0
for row in lines(cell/'control_decisions.jsonl'):
 if row.get('stage')!='BACKUP_APPEND':continue
 for tail in row['detail'].get('candidates',[]):
  tails+=1;geometry_wall+=tail.get('geometry_wall_s',0.)
  if not tail.get('full_minimum_not_evaluated',False):
   assert tail['minimum_clearance_m']is not None and tail['minimum_clearance_native_tick']is not None
   continue
  assert tail['reason']=='TIME_CLEARANCE' and tail['minimum_clearance_m']is None and tail['minimum_clearance_native_tick']is None
  file=cell/tail['early_rejection_witness_file'];assert file not in seen;seen.add(file);z=np.load(file);step=int(z['step']);assert step==row['step']
  state={k:v for k,v in states[step].items()if k!='step'};assert str(z['state_sha256'])==hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()
  if step not in fields:
   f=SimpleNamespace(**base);install_time_gate(f,state,'predictive',p['known_circles'],p['known_rectangles']);fields[step]=f
  poses=z['poses'];assert poses.shape==(328,3);tick=int(z['witness_native_tick']);value=float(z['witness_value']);v=fields[step].trajectory_values(poses[[tick-1]],tick*.01);e=abs(float(v[0])-value);error=max(error,e)
  assert e<=1e-10 and value<.155-1e-8 and v.min()<.155
  assert tick==tail['early_rejection_witness_native_tick'] and value==tail['early_rejection_witness_value_m']
  assert np.array_equal(z['target'],tail['target_command'])
  checked+=1
assert len(seen)==len(list((cell/'rejection_witnesses').glob('*.npz')))if(cell/'rejection_witnesses').exists()else not seen
old=repo/'runs/v800_spatial_nominal_global/main_slot01/paired';oldrows=lines(old/'geometry_memory/v648_execution.jsonl');newrows=lines(cell/'v648_execution.jsonl');count=min(len(newrows),200);errors={k:float(np.max(abs(np.asarray([x[k]for x in oldrows[:count]])-np.asarray([x[k]for x in newrows[:count]]))))for k in ['qpos_full','qvel_full','ctrl','mocap_pos']}if count else{}
if p.get('field_case')=='WEST_EAST' or read(a.pair/'geometry_memory/result.json').get('seed')==10010001:
 assert count==200 and all(v<=1e-8 for v in errors.values()),'ORIGINAL_200_PREFIX_CHANGED'
else:errors={};count=0
result=dict(status='POINTWISE_WITNESS_SUPPLEMENT_PASS',original_frozen_full_vector_audit_still_uncompleted=True,full_vectors_recomputed=False,proof='One original causal value below threshold implies original complete minimum below threshold; no acceptance inferred from subset.',early_rejection_witnesses_pointwise_verified=checked,all_tail_geometry_evaluations=tails,maximum_witness_pointwise_error=error,original_first200_prefix_steps=count,original_prefix_errors=errors,online_tail_geometry_wall_s=geometry_wall,early_witness_is_not_full_minimum=True,new_integrations=0,new_models=0)
out=repo/'runs/v802_pointwise_witness_supplement';assert not out.exists();out.mkdir();(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
