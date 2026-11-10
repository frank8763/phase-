"""RP-CCR safe-command recovery ranking; geometry only, no dynamics guarantee.

Normal-mode forward alternatives only. Every proposed output has the exact original
V924 command/stop/full-cycle certificate. Lookahead changes preference only.
"""
import math
from dataclasses import dataclass
import numpy as np
K=.758770385
PRIMITIVES=tuple([(0.,0.)]+[(v,v*k)for v in[.05,.1]for k in[-K,0.,K]])

@dataclass(frozen=True)
class Decision:
 mode:str
 selected:tuple|None
 proof:dict|None
 nominal_proof:dict
 alternatives:tuple
 shaping:dict|None=None

def poses(body,v,w,times):
 t=np.asarray(times,float);x,y,a=body[:3];z=a+w*t
 if abs(w)<1e-12:return np.c_[x+v*t*math.cos(a),y+v*t*math.sin(a),z]
 return np.c_[x+v/w*(np.sin(z)-math.sin(a)),y-v/w*(np.cos(z)-math.cos(a)),z]

def select(packet,source,wanted,known,now,goal,admit,static_values,previous=None,shape=None):
 assert len(wanted)==2 and len(goal)==2 and np.isfinite([*wanted,*goal,now]).all(),'INVALID_SELECTOR_INPUT'
 if wanted[0]<0:
  blocked=dict(passed=False,reason='NORMAL_REVERSE_REQUIRES_FORWARD_REPLAN',v=wanted[0],w=wanted[1])
  return Decision('FORWARD_REFERENCE_REPLAN_REQUIRED',None,None,blocked,())
 nominal=admit(packet,source,*wanted,known,now)
 if nominal['passed']:
  return Decision('NOMINAL_UNCHANGED',tuple(wanted),nominal,nominal,())
 if tuple(wanted)==(0.,0.):
  # A Nav2/collision-monitor STOP is never converted into recovery motion.
  return Decision('STOP_REQUEST_NO_OVERRIDE',None,None,nominal,())
 library=PRIMITIVES
 rows=[];start=np.asarray(packet['body'][:3],float);distance=float(np.linalg.norm(start[:2]-goal));start_clear=float(static_values(known,[start])[0])
 # Beyond the admitted .2s prefix these are nominal ranking coordinates only.
 # They are not certified successor states and cannot authorize longer motion.
 for index,requested in enumerate(library):
  shaping=None if shape is None else shape(*requested)
  control=requested if shaping is None else tuple(shaping['selected'])
  proof=admit(packet,source,*control,known,now)
  row=dict(index=index,requested=list(requested),control=list(control),passed=proof['passed'],proof=proof,shaping=shaping)
  if proof['passed']:
   short=poses(packet['body'],*control,[.2])[0];future=poses(packet['body'],*control,np.linspace(0,1.,11))
   progress=distance-float(np.linalg.norm(short[:2]-goal));future_clear=static_values(known,future)
   recovery=float(future_clear[-1])-start_clear;minimum=float(np.min(future_clear))
   continuity=0. if previous is None else -abs(control[0]-previous[0])-.5*abs(control[1]-previous[1])
   row.update(short_goal_progress_m=progress,nominal_one_second_clearance_gain_m=recovery,nominal_one_second_minimum_static_m=minimum,continuity=continuity)
  rows.append(row)
 moving=[r for r in rows if r['passed']and r['control']!=[0.,0.]]
 progress=[r for r in moving if r['short_goal_progress_m']>1e-4]
 if progress:
  chosen=max(progress,key=lambda r:(r['short_goal_progress_m'],r['proof']['static_lower_m'],r['continuity'],-r['index']));mode='CERTIFIED_PROGRESS_ALTERNATIVE'
 else:
  recovery=[r for r in moving if r['nominal_one_second_clearance_gain_m']>1e-4 and r['nominal_one_second_minimum_static_m']>=start_clear-1e-7]
  if recovery:
   chosen=max(recovery,key=lambda r:(r['nominal_one_second_clearance_gain_m'],r['short_goal_progress_m'],r['continuity'],-r['index']));mode='CERTIFIED_CLEARANCE_RECOVERY'
  else:
   stops=[r for r in rows if r['passed']and r['control']==[0.,0.]]
   if not stops:return Decision('NO_NEW_CERTIFIED_CONTROL',None,None,nominal,tuple(rows))
   chosen=stops[0];mode='CERTIFIED_STOP_ONLY'
 assert chosen['passed']and chosen['proof']['passed'],'UNSAFE_SELECTION'
 return Decision(mode,tuple(chosen['control']),chosen['proof'],nominal,tuple(rows),chosen['shaping'])
