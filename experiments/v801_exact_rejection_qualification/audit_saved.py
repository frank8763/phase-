"""Independent original full-vector recomputation; no accelerated evaluator imported."""
import json,sys,time,signal,hashlib,gzip
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco,mujoco.rollout
def forbidden(*a,**kw):raise AssertionError('ZERO_MODEL_AUDIT')
for n in ['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,n,forbidden)
mujoco.rollout.rollout=forbidden
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(repo/'experiments/v800_spatial_nominal_global'))
from motion_tracker import install_time_gate
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v801_exact_rejection_qualification';assert not(root/'FINALIZED.json').exists()
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('AUDIT_900S')));signal.alarm(900)
r=read(root/'RESULT.json');assert read(root/'ROUND_WINDOW.json')['round_closed'];freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/p)==h for p,h in freeze['files'].items())
p=read(repo/'runs/v800_spatial_nominal_global/main_slot01/paired/STATIC_PROTOCOL.json');b=np.asarray(p['footprint_bounds']);base=dict(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,rectangles=np.asarray(p['known_rectangles']),circles=np.asarray(p['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
states={x['step']:x for x in map(json.loads,(repo/'runs/v793_complete_joint_navigation/main_slot01/paired/geometry_memory/motion_estimate.jsonl').open())}
raw=repo/'runs/v799_spatial_nominal_qualification';old=read(raw/'RESULT.json');details=read(root/'DETAILS.json');lookup={(x['step'],x['rank'],x['tail']):x for x in details};checked=0;error=0.
for record in old['records']:
 f=SimpleNamespace(**base);install_time_gate(f,states[record['step']],'predictive',p['known_circles'],p['known_rectangles']);q=np.load(raw/(record['label']+'_PREFIX.npz'))['qpos'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));prefix=np.c_[q[:,:2],yaw]
 for i,t in enumerate(record['detail']['candidates']):
  z=np.load(raw/(record['label']+'_TAIL_%02d.npz'%i));v=f.trajectory_values(np.vstack([prefix,z['poses']]),.01);row=lookup[(record['step'],record['rank'],i)]
  assert abs(float(v.min())-t['minimum_clearance_m'])<=1e-8 and abs(float(v.min())-row['full_minimum_m'])<=1e-12
  assert bool(v.min()<.155)==row['original_rejected']==(t['reason']=='TIME_CLEARANCE')
  if row['early_rejected']:
   e=abs(float(v[row['witness_native_tick']-1])-row['witness_value_m']);error=max(error,e);assert e<=1e-10 and row['witness_value_m']<.155-1e-8
  checked+=1
assert checked==len(details)==r['V799_complete_schedules'] and len(old['records'])==75 and r['V800_accepted_schedules']==200
audit=dict(status='PASS',original_complete_vectors_recomputed=checked,maximum_witness_error=error,all_rejection_classes_exact=True,selected_tails_exact=r['selected_original_tails_exact'],accepted_vectors_exact=r['accepted_full_vectors_exact'],qualified_for_global=r['qualified_for_global'],new_models=0,new_integrations=0)
(root/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
dest=repo/'evidence/rpccr_exact_rejection_v801_20261104';assert not dest.exists();dest.mkdir();(dest/'blobs').mkdir();inventory=[]
for directory in [own,root]:
 for file in sorted(directory.rglob('*')):
  if not file.is_file()or '__pycache__'in file.parts or file.suffix=='.pyc':continue
  data=file.read_bytes();h=hashlib.sha256(data).hexdigest();blob=dest/'blobs'/(h+'.gz');blob.write_bytes(gzip.compress(data,mtime=0));inventory.append(dict(path=str(file.relative_to(repo)),sha256=h,bytes=len(data),blob=str(blob.relative_to(dest))))
for row in inventory:
 data=gzip.decompress((dest/row['blob']).read_bytes());assert len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256']==sha(repo/row['path'])
(dest/'INVENTORY.json').write_text(json.dumps(inventory,indent=2)+'\n')
(root/'FINALIZED.json').write_text(json.dumps(dict(status='SAVED_REJECTION_EQUIVALENCE_VERIFIED',qualification_passed=r['qualified_for_global'],independent_audit=audit,archive=str(dest.relative_to(repo)),source_decompressed_SHA_readback=True,new_integrations=0),indent=2)+'\n')
signal.alarm(0);print(json.dumps(audit))
