"""Deterministic causal mode/commitment selection; never reads world truth."""
import copy,math

def initial_state():
 return dict(mode='PROGRESS',action=None,selected_at=-12,scan_start_yaw=None,scan_angle=0.,scan_min=0.,scan_max=0.,last_yaw=None,turn_sign=0)

def select(candidates,local,yaw,unknown_hold,state):
 s=copy.deepcopy(state);events=[]
 if s['mode']=='OBSERVE':
  s['scan_angle']+=math.atan2(math.sin(yaw-s['last_yaw']),math.cos(yaw-s['last_yaw']));s['last_yaw']=yaw;s['scan_min']=min(s['scan_min'],s['scan_angle']);s['scan_max']=max(s['scan_max'],s['scan_angle'])
  if s['scan_max']-s['scan_min']>=math.pi/16 and unknown_hold>=.55:
   s['mode']='PROGRESS';s['action']=None;s['selected_at']=local-12;events.append('ACTUAL_SWEEP_AND_INFORMATION_RENEWED')
 if s['mode']=='PROGRESS'and unknown_hold<=.45:
  s.update(mode='OBSERVE',action=None,scan_start_yaw=yaw,scan_angle=0.,scan_min=0.,scan_max=0.,last_yaw=yaw,turn_sign=0);events.append('EARLY_INFORMATION_TRIGGER')
 eligible=[c for c in candidates if c['admissible']]
 score=lambda c:(-c['goal_progress_m'],-c['minimum_causal_clearance_m'],c['action_index'])
 information=lambda c:(-c['minimum_causal_clearance_m'],-c['goal_progress_m'],c['action_index'])
 if not eligible:return None,s,dict(events=events+['NO_CERTIFIED_ACTION'],mode=s['mode'],reason='NO_CERTIFIED_ACTION')
 previous=next((c for c in eligible if c['action_index']==s['action']),None)
 if s['mode']=='PROGRESS':
  if previous is not None and local-s['selected_at']<12:chosen=previous;reason='PROGRESS_COMMITMENT'
  else:chosen=min(eligible,key=score);s['selected_at']=local;reason='PROGRESS_RESELECT'
 else:
  scan=[c for c in eligible if sum(c['target'][2:])/2<=1 and abs(c['target'][2]-c['target'][3])==12]
  same=[c for c in scan if (1 if c['target'][2]>c['target'][3]else -1)==s['turn_sign']]
  if previous is not None and previous in same:chosen=previous;reason='OBSERVATION_COMMITMENT'
  elif same:chosen=min(same,key=information);reason='SAME_TURN_SAFE_REPLACEMENT'
  elif scan:
   chosen=min(scan,key=information);reason='SAFE_SCAN_DIRECTION_SELECTION'
   if s['turn_sign']!=0:
    s.update(scan_start_yaw=yaw,scan_angle=0.,scan_min=0.,scan_max=0.,last_yaw=yaw);events.append('OLD_DIRECTION_NOT_CERTIFIABLE_RESET_SWEEP')
  else:chosen=min(eligible,key=information);reason='NO_SCAN_ACTION_SAFE_OTHER_ACTION';events.append('OBSERVATION_NOT_ACHIEVED')
  delta=chosen['target'][2]-chosen['target'][3];s['turn_sign']=1 if delta>0 else -1 if delta<0 else 0
 s['action']=chosen['action_index']
 return chosen['action_index'],s,dict(events=events,mode=s['mode'],reason=reason,actual_scan_range_rad=s['scan_max']-s['scan_min'])
