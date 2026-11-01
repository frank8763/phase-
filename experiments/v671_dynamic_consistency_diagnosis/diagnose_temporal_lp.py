"""Fixed causal log feasibility LP, never exports an online tracker or controls."""
import os,sys,json,gzip,time
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(os.environ['PHASE_REPO'])/'runs/v671_dynamic_consistency_diagnosis/analysis_dependencies'))
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
repo=Path(os.environ['PHASE_REPO']);sys.path.insert(0,str(repo/'experiments/v670_dynamic_empty_samples'))
from motion_tracker import capsule_constraints
path=repo/'runs/v670_dynamic_empty_samples/dev38_95000011_empty/paired';read=lambda p:json.loads(p.read_text());model=read(path/'STATIC_PROTOCOL.json');config=read(path/'DYNAMIC_PROTOCOL.json');states=list(map(json.loads,(path/'geometry_memory/motion_estimate.jsonl').read_text().splitlines()))
with gzip.open(path/'geometry_memory/sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
records=[];started=time.monotonic()
for k in [48,192,300,650]:
 ss=states[max(0,k-63):k+1];pp=packets[max(0,k-63):k+1];n=len(ss);bounds=[];rowids=[];cols=[];data=[];bb=[]
 def add(items,bound):
  row=len(bb)
  for j,v in items:rowids.append(row);cols.append(j);data.append(v)
  bb.append(bound)
 for i,(s,p)in enumerate(zip(ss,pp)):
  bounds.extend(list(zip(s['position_lower'],s['position_upper']))+list(zip(s['velocity_lower'],s['velocity_upper'])))
  A,b,_=capsule_constraints(np.asarray(p['rays']).reshape(-1,7),model['known_rectangles'],model['known_circles'])
  for normal,value in zip(A,b):add([(4*i,normal[0]),(4*i+1,normal[1])],value+1e-6)
  if i:
   dt=s['time']-ss[i-1]['time'];assert .079<dt<.081
   for d in range(2):
    p0=4*(i-1)+d;p1=4*i+d;v0=p0+2;v1=p1+2
    for sign in [-1,1]:
     add([(v1,sign),(v0,-sign)],.04*dt+1e-8)
     add([(p1,sign),(p0,-sign),(v0,-sign*dt)],.5*.04*dt*dt+1e-8)
     add([(p1,sign),(p0,-sign),(v1,-sign*dt)],.5*.04*dt*dt+1e-8)
     add([(p1,sign),(p0,-sign),(v0,-sign*dt/2),(v1,-sign*dt/2)],.25*.04*dt*dt+1e-8)
 A=csr_matrix((data,(rowids,cols)),shape=(len(bb),4*n));b=np.asarray(bb);new=[];solver=[]
 for d in range(4):
  limits=[]
  for sign in [1,-1]:
   c=np.zeros(4*n);c[4*(n-1)+d]=sign;r=linprog(c,A_ub=A,b_ub=b,bounds=bounds,method='highs',options={'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8,'threads':1,'parallel':False});solver.append({'success':bool(r.success),'status':int(r.status)})
   assert r.success,('TEMPORAL_LP_NOT_FEASIBLE',k,d,sign,r.message)
   limits.append(float(r.x[4*(n-1)+d]))
  new.append([limits[0]-1e-6,limits[1]+1e-6])
 # Evaluator only; truth was never an LP argument.
 times=np.asarray([s['time']for s in ss]);truthp=np.asarray(config['anchor_xy'])+np.sin(times*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy']);truthv=np.cos(times*config['omega_rad_s']+config['phase_rad'])[:,None]*config['maximum_speed_m_s']*np.asarray(config['axis_xy']);truth=np.c_[truthp,truthv].reshape(-1);original=np.asarray(bounds);new=np.asarray(new)
 violation=float(np.max(A@truth-b));box_violation=float(np.maximum(original[:,0]-truth,truth-original[:,1]).max());terminal=float(np.maximum(new[:,0]-truth[-4:],truth[-4:]-new[:,1]).max());assert max(violation,box_violation,terminal)<=1e-7,('TRUTH_NOT_IN_NECESSARY_TEMPORAL_SET',k,violation,box_violation,terminal)
 old=original[-4:];records.append({'checkpoint':k,'frames':n,'lp_variables':4*n,'linear_inequalities':len(bb),'original_bounds':old.tolist(),'temporal_lp_bounds':new.tolist(),'position_area_old_m2':float(np.prod(old[:2,1]-old[:2,0])),'position_area_lp_m2':float(np.prod(new[:2,1]-new[:2,0])),'velocity_width_old_m_s':(old[2:,1]-old[2:,0]).tolist(),'velocity_width_lp_m_s':(new[2:,1]-new[2:,0]).tolist(),'maximum_true_history_constraint_violation':violation,'current_truth_box_excess':terminal,'solver':solver})
result={'status':'PASS_FIXED_LOG_INFORMATION_DIAGNOSIS','checkpoints':[48,192,300,650],'linear_programs':32,'records':records,'elapsed_s':time.monotonic()-started,'robot_simulation_integrations':0,'navigation_tasks':0,'online_tracker_modified':False,'scope':'causal history compatibility diagnostics only; not a third control candidate, certified estimator or dynamic navigation outcome'};(repo/'runs/v671_dynamic_consistency_diagnosis/TEMPORAL_LP_INFORMATION_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
