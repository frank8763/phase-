"""One task-parameterized producer; complete endpoint and controls are gates."""
import sys,math,time
from pathlib import Path
import numpy as np
from kernel import C,R,load,predict,checks,initial,Predictor,PARAMETERS,CAP
base=load('v1061_preserved_timing_core',C/'baseline_handoff.py')
parked=base.parked;source_check=base.source_check;contained=base.contained;refresh_module=base.refresh_module;PERIOD=base.PERIOD;REQUIRED=base.REQUIRED;virtual=base.virtual;MAX_HOLD=base.MAX_HOLD;hold_permission=base.hold_permission;publish=base.publish

def validate_actions(actions):
 assert isinstance(actions,list)and actions,'EMPTY_ACTIONS'
 total=0
 for a in actions:
  assert a['kind']in ['move','wait']and type(a['ticks'])is int and a['ticks']>0,'INVALID_ACTION_SCHEMA';total+=a['ticks'];assert math.isfinite(a['target'])and abs(a['target'])<=CAP+1e-12,'UNQUALIFIED_STEERING_TARGET'
  if a['kind']=='wait':assert a['gear']==0 and a['target']==0 and a.get('speed',0.)==0.,'INVALID_STOP'
  else:
   assert a['gear']in [-1,1],'INVALID_GEAR';v=a.get('speed',.08 if a['gear']>0 else-.03);assert v in [-.03,.03,.08]and (v>0)==(a['gear']>0),'UNQUALIFIED_SPEED'
 assert total<=40000,'SOURCE_NATIVE_LIMIT'

def profile_gates(ss,uu,rr,packet,setup,goal):
 # Geometric validity is supplied separately by full prefix/timed suffix
 # certificates. Do not manufacture a geometric pass from a placeholder.
 cc,upper=checks(ss,uu,rr,packet,setup,np.asarray(goal),float('-inf'),REQUIRED);cc.pop('full_raw_geometry');assert all(cc.values()),'COMPLETE_INPUT_ENDPOINT_OR_CONTROL_REJECTED'
 return cc,upper

def prepare(setup,packet,source,goal,actions,elapsed):
 validate_actions(actions);assert np.asarray(goal).shape==(2,)and np.isfinite(goal).all(),'INVALID_ORIGINAL_GOAL'
 generic=any('speed'in a for a in actions)
 if generic:
  from fixed_clock import prepare_generic
  return prepare_generic(setup,packet,source,goal,actions,elapsed,base)
 proposal=base.prepare(setup,packet,source,goal,actions,elapsed)
 ss=np.vstack([proposal['prefix_states'],np.asarray(proposal['cross_states'])[1:]]);uu=np.vstack([proposal['prefix_controls'],proposal['cross_controls']]);rr=np.vstack([proposal['prefix_requests'],proposal['cross_requests']]);cc,upper=profile_gates(ss,uu,rr,packet,setup,goal);proposal.update(complete_profile_checks=cc,terminal_goal_upper_m=upper,generic_complete_profile_checked=generic)
 return proposal
sys.path.insert(0,str(C))

# New bounded policy: complete-goal proposal or explicitly labelled complete
# full-cycle-safe observation corridor. Neither a prefix nor an information
# corridor can satisfy the external navigation arrival gate.
from recovery_source import prepare
