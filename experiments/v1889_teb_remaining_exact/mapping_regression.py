"""Saved mapper software regression, no old trajectory audit or numerical work."""
import copy
from context import R,C,O,read,sha,load

def run():
 binding=read(O/'SAVED_REJECTION_BINDING.json')
 for n,h in binding['files'].items():assert sha(R/n)==h
 old=R/'runs/v1866_remaining_common_matrix/rounds/common_05__TEB'
 value=read(O/'MAPPING_SOFTWARE_INPUT.json');assert value['software_only']and value['not_new_plant_input']
 answer=value['answer'];row=value['row'];config=value['config'];first=value['first']
 assert answer==read(old/'actual/cycle_0000_teb_answer.json')and row==read(old/'actual/cycle_0000_query.json')and config==read(old/'TEB_CONFIG.json')and first==read(old/'actual/RESULT.json')['first_error']
 frames=load('v1884_exact_mapping_software',R/'experiments/v1888_teb_unapplied_refusal_exact/frames.py')
 helper=load('v1884_refusal_software',R/'experiments/v1888_teb_unapplied_refusal_exact/rejected_mapping.py')
 try:frames.command(answer['proposal'],config)
 except AssertionError as e:assert str(e)=='TEB_RAW_CURVATURE_OUTSIDE_COMMON_CAP';red=repr(e)
 else:raise AssertionError('ORIGINAL_MAPPING_BUG_NOT_RED')
 green=helper.verify(frames,answer,config,row,first,True);assert green['refused_unapplied']and not green['command_returned']
 bad=[]
 for kind in ['applied','different_answer','different_first','no_first','not_last','accepted_command','wrong_stage']:
  a=copy.deepcopy(answer);r=copy.deepcopy(row);f=copy.deepcopy(first);last=True
  if kind=='applied':r['executed_native']=1
  if kind=='different_answer':a['sequence']=-1
  if kind=='different_first':f['error']="AssertionError('OTHER')"
  if kind=='no_first':f=None
  if kind=='not_last':last=False
  if kind=='accepted_command':r['command']=[0.,0.]
  if kind=='wrong_stage':f['stage']='SAVE_RESULT'
  try:helper.verify(frames,a,config,r,f,last)
  except AssertionError:bad.append(kind)
  else:raise AssertionError('FALSE_REFUSAL_ACCEPTED:'+kind)
 # Explicit software successful response exercises exact original success path.
 a=copy.deepcopy(answer);a['proposal'].update(status=0,vx=.1,vy=0.,omega=0.)
 a['proposal']['trajectory']=[[0.,0.,0.,0.,.1,0.,0.],[.1,0.,0.,1.,.1,0.,0.]]
 mapped=frames.command(a['proposal'],config);trajectory=frames.trajectory(a['proposal'],config)
 r=dict(row,native_answer=a,command=mapped['body_request'][:2],original_ROS_saturation_explicit_port=mapped,reference_trajectory_body_centre=trajectory)
 assert not helper.verify(frames,a,config,r,None,True)['refused_unapplied']
 r['command']=[.2,0.]
 try:helper.verify(frames,a,config,r,None,True)
 except AssertionError:bad.append('successful_mapping_mismatch')
 else:raise AssertionError('SUCCESS_MAPPING_CHANGED')
 return dict(passed=True,original_red=red,unapplied_refusal_audited_without_command=True,success_original_mapping_preserved=True,negative_cases=bad,models=0,optimizer_calls=0,FFI_calls=0,physical_native=0,not_old_trajectory_audit=True,old_result_unchanged=True)
