"""Offline oracle decomposition only. Actual future values never enter planners."""
import json,math,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from analyze import read,compare,PARAMETERS,O
result={}
for task in ['straight','left']:
 setup,packet,plan,q,yaw,v,lat,u=read(task);_,ss=compare(task,PARAMETERS);initial_yaw=packet['body'][2];pv=np.r_[packet['body'][3],ss[:,3]];pl=np.r_[0.,ss[:,4]];ph=np.r_[initial_yaw,ss[:,2]];av=np.r_[packet['body'][3],v];al=np.r_[0.,lat];ah=np.unwrap(np.r_[initial_yaw,yaw]);rows={}
 for name,speed,lateral,heading in [('baseline',pv,pl,ph),('actual_speed_only',av,pl,ph),('actual_lateral_only',pv,al,ph),('actual_heading_only',pv,pl,ah),('all_actual_velocity_signals',av,al,ah)]:
  mid=(heading[:-1]+heading[1:])/2;vm=(speed[:-1]+speed[1:])/2;lm=(lateral[:-1]+lateral[1:])/2;step=.01*np.c_[vm*np.cos(mid)-lm*np.sin(mid),vm*np.sin(mid)+lm*np.cos(mid)];xy=np.asarray(packet['body'][:2])+np.cumsum(step,axis=0);err=np.linalg.norm(xy-q[:,:2],axis=1);rows[name]=dict(maximum_position_m=float(err.max()),final_vector=(q[-1,:2]-xy[-1]).tolist())
 result[task]=rows
out=dict(models=0,integrations=0,offline_oracle_not_future_predictor=True,results=result);(O/'ORACLE_DECOMPOSITION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
