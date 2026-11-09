"""Fixed archived MPPI/RPP direction evidence and measured response models."""
import gzip,hashlib,importlib.abc,json,math,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v928_predictive_control_diagnosis';S=O/'saved';begun=time.monotonic()
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','torch','factory','physical','vehicle','rclpy'}:raise AssertionError(name)
sys.meta_path.insert(0,Block());proof=json.load(open(O/'RESTORE_VERIFIED.json'))
for row in proof['members']:assert hashlib.sha256((S/row['path']).read_bytes()).hexdigest()==row['sha256']
nav=[]
for version in ['v862_ready_static','v863_rpp_static']:
 p=S/'runs/v858_nav2_verified'/version;commands=np.asarray(json.load(open(p/'COMMANDS.json'))['cmd_vel_nav']);plans=json.load(open(p/'PLANS.json'));directions=[]
 for r in plans:
  points=np.asarray(r['path']);dis=np.diff(points[:,:2],axis=0);proj=np.sum(dis*np.c_[np.cos(points[:-1,2]),np.sin(points[:-1,2])],axis=1);nonzero=proj[abs(proj)>1e-4];directions.append((r['at'],None if not len(nonzero)else int(np.sign(nonzero[0]))))
 wrong=0;forward=0;j=0;negative=int(np.sum(commands[:,1]<-.001));switch=int(np.sum(commands[1:,1]*commands[:-1,1]<-1e-6))
 for at,v,w in commands:
  while j+1<len(directions)and directions[j+1][0]<=at:j+=1
  if directions[j][1]==1:forward+=1;wrong+=int(v<-.001)
 nav.append(dict(version=version,plan_count=len(plans),negative_raw_commands=negative,total_raw_commands=len(commands),negative_while_first_reference_forward=wrong,forward_reference_command_samples=forward,raw_direction_sign_switches=switch))
responses=[]
for i in range(18):
 p=S/f'runs/v858_nav2_verified/v909/platform_{i:02d}';q=json.load(open(p/'QUALIFICATION.json'));z=np.load(p/'BODY_SAMPLES.npz');b=z['body'];u=np.vstack([np.tile(q['case']['warm'],(200,1)),np.tile(q['case']['command'],(20,1)),np.zeros((200,2))]);responses.append(dict(index=i,b=b,u=u,origin=z['origin'],case=q['case']))
# ARX2 fit is a diagnostic approximation, never applied to native actuators.
# Split complete cases by fixed parity before fitting, no test-case refit.
coeff=[];one_step=[]
for axis,column in [(0,3),(1,4)]:
 X=[];Y=[]
 for r in responses[::2]:
  b=r['b'];u=r['u'];y=b[:,column]
  for t in range(2,419):X.append([y[t],y[t-1],u[t+1,axis],u[t,axis]]);Y.append(y[t+1])
 a=np.linalg.lstsq(X,Y,rcond=None)[0];coeff.append(a.tolist());errors=[]
 for r in responses[1::2]:
  y=r['b'][:,column];u=r['u'];x=np.c_[y[2:-1],y[1:-2],u[3:,axis],u[2:-1,axis]];errors.extend((x@a-y[3:]).tolist())
 roots=np.roots([1.,-a[0],-a[1]])
 one_step.append(dict(axis=axis,rmse=float(np.sqrt(np.mean(np.square(errors)))),max_error=max(abs(np.array(errors))),stable=bool(max(abs(roots))<1.),poles=[[float(p.real),float(p.imag)]for p in roots]))
# Recursive 2.2s prediction from actual tick200, compare fixed full-case holdout.
metrics=[]
for r in responses:
 b=r['b'];u=r['u'];pred=np.zeros((420,2));pred[:200]=b[:200,3:5]
 for t in range(199,419):
  for axis,column in [(0,3),(1,4)]:
   a=np.array(coeff[axis]);pred[t+1,axis]=a@[pred[t,axis],pred[t-1,axis],u[t+1,axis],u[t,axis]]
 origin=b[199,:3];nominal=origin.copy();arx=origin.copy();n=[];a=[]
 for t in range(200,420):
  v,w=u[t];nominal[:2]+=.01*v*np.array([math.cos(nominal[2]),math.sin(nominal[2])]);nominal[2]+=.01*w;n.append(nominal.copy())
  v,w=pred[t];arx[:2]+=.01*v*np.array([math.cos(arx[2]),math.sin(arx[2])]);arx[2]+=.01*w;a.append(arx.copy())
 def residual(p):
  p=np.asarray(p);actual=b[200:,:3];return dict(position_max_m=float(np.linalg.norm(p[:,:2]-actual[:,:2],axis=1).max()),yaw_max_rad=float(abs(np.arctan2(np.sin(p[:,2]-actual[:,2]),np.cos(p[:,2]-actual[:,2]))).max()))
 metrics.append(dict(index=r['index'],role='fit'if r['index']%2==0 else'held_out_case',warm=r['case']['warm'],command=r['case']['command'],nominal=residual(n),arx2=residual(a)))
checks=dict(old_direction_failure_detected=nav[0]['negative_while_first_reference_forward']>1000,old_success_direction_differs=nav[1]['negative_raw_commands']<nav[0]['negative_raw_commands'],all36_response_inputs_sha_verified=len(responses)==18,stable_models=all(x['stable']for x in one_step))
report=dict(models=0,integrations=0,checks=checks,direction=nav,arx2_coefficients=coeff,held_out_one_step=one_step,response_cases=metrics,elapsed_s=time.monotonic()-begun,scope='Saved-case diagnosis and parity-separated empirical fitting only, no navigation success/new model or safety-bound claim')
(O/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
