"""Fixed bounded geometry checks, zero simulation and zero gradient updates."""
import os,json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from unseen_prior import state_at,clearance
from motion_tracker import Tracker
rng=np.random.default_rng(691);n=3000;now=2.5;state=state_at(now)
field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2))
poses=np.c_[rng.uniform([-6.,-4.],[-2.,0.],size=(n,2)),rng.uniform(-np.pi,np.pi,n)];times=rng.uniform(0,3.28,n)
lower=clearance(field,poses,state,times);radius=np.maximum(0,3-np.sqrt(2)*.12*(now+times));angle=rng.uniform(-np.pi,np.pi,n)
actor=np.array([-4.,-2.])+(radius+rng.uniform(0,3,n))[:,None]*np.c_[np.cos(angle),np.sin(angle)]
offset=actor-poses[:,:2];c,s=np.cos(poses[:,2]),np.sin(poses[:,2]);local=np.c_[c*offset[:,0]+s*offset[:,1],-s*offset[:,0]+c*offset[:,1]];residual=abs(local)-field.half;actual=np.where(residual.max(axis=1)<=0,residual.max(axis=1),np.linalg.norm(np.maximum(residual,0),axis=1))-.1
maximum=float(np.max(lower-actual))
origin=np.array([-4.,-2.]);initial=origin+(3+rng.uniform(0,2,n))[:,None]*np.c_[np.cos(angle),np.sin(angle)];t=rng.uniform(0,16,n);moved=initial+rng.uniform(-.12,.12,(n,2))*t[:,None];excess=float(np.max(np.maximum(0,3-np.sqrt(2)*.12*t)-np.linalg.norm(moved-origin,axis=1)))
_,empty=Tracker().update_rays([],[],[],0.)
checks={'all3000_lower_bounds':maximum<=1e-10,'all3000_initial_prior_reachability':excess<=1e-10,'no_return_is_unseen_not_absent':empty==state_at(0.),'prior_not_sensor_inferred':'not inferred'in empty['prior_source']}
out={'status':'PASS'if all(checks.values())else'FAIL','checks':checks,'cases':n,'maximum_lower_bound_excess_m':maximum,'maximum_reachable_prior_excess_m':excess,'simulation_integrations':0,'gradient_updates':0,'scope':'controlled-course startup exclusion mathematics only'}
root=Path(os.environ['PHASE_RUNS'])/'v694_discovery_execution_recovery';root.mkdir(exist_ok=True);(root/'PRE_NAV_VALIDATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));assert out['status']=='PASS'
