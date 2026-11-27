"""CPU4 geometric tracking candidate and sensor-contract preparation."""
import math,os,resource,time,traceback
from common import R,C,S,read,put,authority,sha,load
def main():
 a,files,out=authority(4,'priest');resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(110,115))
 start=time.monotonic();result=dict(closed=False,models=0,optimizer_calls=0,physics=0,replay=0,formal_tasks=0,full_vehicle_qualified=False)
 try:
  from tracking import command
  P=R/'runs/v2101_parallel_priest_vehicle/vehicle/actual';current=read(P/'PRIEST_CURRENT_INPUT.json');proposal=read(P/'PRIEST_NATIVE_RESULT.json')['answer']['candidate'];reply=proposal['reply']
  assert current['input_sha256']==proposal['input_sha256']and reply['origin_native']==current['fixed_origin_native']
  try:preview=command(reply['coefficients_x'],reply['coefficients_y'],body=current['origin']['body'],gear=reply['gear'],receipt_native=current['fixed_origin_native'],proposal_native=reply['origin_native']);status='COMMAND_INTERFACE_ACCEPTED_ONLY'
  except AssertionError as x:preview=dict(error=repr(x),physical_admission=False);status='NEW_TRACKER_INTERFACE_REFUSED'
  put(out/'SAVED_POLYNOMIAL_PREVIEW.json',dict(status=status,preview=preview,old_original_preview=read(P/'PRIEST_RAW_CURRENT_PROPOSAL.json'),old_original_full_stop_refusal_preserved=True,new_wrapper_identity='PRIEST_POLYNOMIAL_GEOMETRIC_PP_0P6_SPEED_0P08',source_input_sha256=current['input_sha256'],saved_input_not_current_vehicle=True,no_normal_control_applied=True))
  feature=load('original_SCCR_feature_contract',R/'experiments/v1937_sccr_frozen_policy_bridge/feature_contract.py');missing=[]
  for name,startdim,enddim in feature.LAYOUT:
   if 'camera'in name or'depth'in name:missing.append(dict(block=name,range=[startdim,enddim],dimensions=enddim-startdim,required_causal_producer=True,available_in_original32ray_contract=False))
  assert sum(x['dimensions']for x in missing)==50
  put(out/'SCCR_INPUT_PRODUCER_REQUIREMENTS.json',dict(original_full_SCCR_qualified=False,required_features=186,missing_dimensions=50,missing_blocks=missing,direct_depth_risk_fusion_also_required=True,original_weights_sha256='4072c19e02ba5c7c6b218a268c4ff1d987d2352eada01a3de918854d7173fc9f',inference=0,training=0,formal_slots_unexecuted=12,actions_before_admission=['Exact original causal camera/depth producers and normalization plus matching disclosure, or separately registered observation adaptation with distinct identity','No missing-feature padding, hidden truth or changed frozen policy under original fullSCCR name']))
  result.update(finite_preparation_complete=True,PRIEST_preview_status=status,polynomial_tracking_changed_from_original=True,original_timing_discarded=True,full_stop_component_still_required=True,SCCR_original_applicability_blocked=True,all_frozen_source_SHA_after=all(sha(R/n)==h for n,h in files.items()))
 except BaseException as x:result.update(error=repr(x),traceback=traceback.format_exc())
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(out/'RESULT.json',result)
 print(__import__('json').dumps(result));return 0 if result.get('finite_preparation_complete')and result.get('all_frozen_source_SHA_after')else 1
if __name__=='__main__':raise SystemExit(main())
