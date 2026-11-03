def audit_initial():
 return dict(mode='PROGRESS',action=None,selected_at=-12,scan_start_yaw=None,scan_angle=0.,scan_min=0.,scan_max=0.,last_yaw=None,turn_sign=0)
def audit_select(cs,step,heading,hold,prior):
 import copy,math
 state=copy.deepcopy(prior);events=[]
 if state['mode']=='OBSERVE':
  delta=math.atan2(math.sin(heading-state['last_yaw']),math.cos(heading-state['last_yaw']))
  state['scan_angle']+=delta;state['last_yaw']=heading
  state['scan_min']=min(state['scan_min'],state['scan_angle']);state['scan_max']=max(state['scan_max'],state['scan_angle'])
  if state['scan_max']-state['scan_min']>=math.pi/16 and hold>=.55:
   state['mode']='PROGRESS';state['action']=None;state['selected_at']=step-12;events.append('ACTUAL_SWEEP_AND_INFORMATION_RENEWED')
 if state['mode']=='PROGRESS'and hold<=.45:
  state.update(mode='OBSERVE',action=None,scan_start_yaw=heading,scan_angle=0.,scan_min=0.,scan_max=0.,last_yaw=heading,turn_sign=0);events.append('EARLY_INFORMATION_TRIGGER')
 valid={c['action_index']:c for c in cs if c['admissible']}
 if not valid:return None,state,dict(events=events+['NO_CERTIFIED_ACTION'],mode=state['mode'],reason='NO_CERTIFIED_ACTION')
 goal_order=sorted(valid,key=lambda i:(-valid[i]['goal_progress_m'],-valid[i]['minimum_causal_clearance_m'],i))
 info_order=sorted(valid,key=lambda i:(-valid[i]['minimum_causal_clearance_m'],-valid[i]['goal_progress_m'],i))
 previous=state['action']
 if state['mode']=='PROGRESS':
  if previous in valid and step-state['selected_at']<12:chosen=previous;reason='PROGRESS_COMMITMENT'
  else:chosen=goal_order[0];state['selected_at']=step;reason='PROGRESS_RESELECT'
 else:
  scan=[i for i in info_order if sum(valid[i]['target'][2:])<=2 and abs(valid[i]['target'][2]-valid[i]['target'][3])==12]
  same=[i for i in scan if (1 if valid[i]['target'][2]>valid[i]['target'][3]else -1)==state['turn_sign']]
  if previous in same:chosen=previous;reason='OBSERVATION_COMMITMENT'
  elif same:chosen=same[0];reason='SAME_TURN_SAFE_REPLACEMENT'
  elif scan:
   chosen=scan[0];reason='SAFE_SCAN_DIRECTION_SELECTION'
   if state['turn_sign']!=0:
    state.update(scan_start_yaw=heading,scan_angle=0.,scan_min=0.,scan_max=0.,last_yaw=heading);events.append('OLD_DIRECTION_NOT_CERTIFIABLE_RESET_SWEEP')
  else:chosen=info_order[0];reason='NO_SCAN_ACTION_SAFE_OTHER_ACTION';events.append('OBSERVATION_NOT_ACHIEVED')
  diff=valid[chosen]['target'][2]-valid[chosen]['target'][3];state['turn_sign']=int(diff>0)-int(diff<0)
 state['action']=chosen
 return chosen,state,dict(events=events,mode=state['mode'],reason=reason,actual_scan_range_rad=state['scan_max']-state['scan_min'])
