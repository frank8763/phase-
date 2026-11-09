"""Independent old fixed18 response traces; no new physical integrations."""
import hashlib,importlib.abc,json,math,subprocess,sys,tarfile
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v916_cycle_backup';D=O/'response_restore';S=O/'response_saved'
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical','rclpy'}:raise AssertionError(name)
sys.meta_path.insert(0,Block())
idx=json.loads((R/'records/nav2_v909_20261109/RECORD_INDEX.json').read_text());selected=next(a for a in idx['archives']if a['group']=='phase-v909-continuation-20261109');inventory=json.loads((D/(selected['group']+'.INVENTORY.json')).read_text());catalog={r['path']:r for r in inventory['files']};h=hashlib.sha256()
for p in selected['parts']:
 b=(D/p['name']).read_bytes();assert len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256'];h.update(b)
assert h.hexdigest()==selected['archive_sha256'];cat=subprocess.Popen(['cat',*[str(D/p['name'])for p in selected['parts']]],stdout=subprocess.PIPE);zstd=subprocess.Popen(['zstd','-dc'],stdin=cat.stdout,stdout=subprocess.PIPE);cat.stdout.close();seen=set();restored=[]
with tarfile.open(fileobj=zstd.stdout,mode='r|')as tf:
 for m in tf:
  row=catalog[m.name];assert m.isfile()and m.name not in seen;data=tf.extractfile(m).read();assert len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256'];seen.add(m.name)
  if '/platform_'in m.name and m.name.endswith(('/NATIVE_TRACE.npz','/BODY_SAMPLES.npz','/QUALIFICATION.json')):
   p=S/m.name;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(data);restored.append(dict(path=m.name,sha256=row['sha256']))
assert zstd.wait()==0 and cat.wait()==0 and seen==set(catalog)
rows=[]
for i in range(18):
 p=S/f'runs/v858_nav2_verified/v909/platform_{i:02d}';qual=json.loads((p/'QUALIFICATION.json').read_text());case=qual['case'];trace=np.load(p/'physics/NATIVE_TRACE.npz');q=trace['qpos'];vel=trace['qvel'];a=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));body=np.c_[q[:,:2],a,vel[:,0]*np.cos(a)+vel[:,1]*np.sin(a),vel[:,5]]
 saved=np.load(p/'BODY_SAMPLES.npz');assert np.max(abs(body-saved['body']))<=1e-8
 origin=body[199];v,w=case['command'];t=np.minimum(np.arange(1,221)*.01,.2);theta=origin[2]+w*t
 if abs(w)<1e-12:x=origin[0]+v*t*np.cos(origin[2]);y=origin[1]+v*t*np.sin(origin[2])
 else:x=origin[0]+v/w*(np.sin(theta)-math.sin(origin[2]));y=origin[1]-v/w*(np.cos(theta)-math.cos(origin[2]))
 pred=np.c_[x,y,theta];actual=body[200:];position=float(np.linalg.norm(actual[:,:2]-pred[:,:2],axis=1).max());angle=float(abs(np.arctan2(np.sin(actual[:,2]-theta),np.cos(actual[:,2]-theta))).max())
 reversing=v*origin[3]<0;limit=.04 if reversing else .02
 rows.append(dict(index=i,command=case['command'],measured_origin=origin.tolist(),is_direction_reversal=bool(reversing),position_error_m=position,angle_error_rad=angle,position_bound_m=limit,passed=bool(position<=limit and angle<=.035),trace_sha256=hashlib.sha256((p/'physics/NATIVE_TRACE.npz').read_bytes()).hexdigest()))
report=dict(passed=all(r['passed']for r in rows),models=0,integrations=0,reused_original_cases=18,original_members_decompressed_sha_verified=len(seen),restored_members=restored,rows=rows,scope='Retrospective empirical conditional platform bounds only: .02 aligned/zero vs .04 direction-reversal, original .035 yaw. Runtime monitor mandatory; no universal reachability bound or new independent sample.')
(O/'CONDITIONAL_RESPONSE_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['restored_members','rows']},indent=2));print([(r['index'],r['position_error_m'],r['position_bound_m'])for r in rows]);assert report['passed']
