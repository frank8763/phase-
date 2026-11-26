from interface import R,WIRE,FRONT,BRIDGE,CurrentControl,sha,digest
from pathlib import Path
import copy,importlib.util,json,math,os,time
def read(p):
 p=Path(p);x=json.loads(p.read_text())
 if p.name=='SOURCE_FREEZE.json'and'inherit_freeze_path'in x:
  q=R/x['inherit_freeze_path'];assert sha(q)==x['inherit_freeze_sha256'];f=read(q)['files'];assert all(n not in f or f[n]==h for n,h in x['files'].items());x=dict(x,files=dict(f,**x['files']))
 return x
def main():
 os.sched_setaffinity(0,{7});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));C=Path(__file__).resolve().parent;O=R/'runs'/C.name;assert not(O/'ONCE.json').exists();(O/'ONCE.json').write_text(json.dumps(dict(CPU=7,models=0,algorithm_DLLs=0,unix=time.time())));import numpy as np
 S=R/'runs/v2052_svg_registered_causal_solver';assert read(S/'POST_COMPONENT_STORAGE_BARRIER.json')['solver_component_passed'];source=read(S/'SOURCE_FREEZE.json')['files'];saved=read(S/'INPUT.json');packet=saved['origin']['origin_packet'];original_request=saved['causal_request'];receipt=dict(schema='DWA_CURRENT_ACQUISITION_V1',packet_acquisitions=1,packet=packet,packet_sha256=digest(packet),before_monotonic=packet['body_measured_at']-1e-6,after_monotonic=packet['sent_at']+1e-6,scan=original_request['scan']);path=saved['path'];controls=read(S/'native_output/RESULT.json')['raw_steering'];rate=read(S/'native_output/RESULT.json')['author_collision_rate']
 def begin(r=None,gear=1):
  c=CurrentControl(source,run_id='SVG_SOFTWARE_ONLY');f=c.frame(np,copy.deepcopy(receipt if r is None else r),goal_xy=original_request['goal_xy'],rear_path=path,gear=gear);raw=dict(run_id='SVG_SOFTWARE_ONLY',origin_native_tick=packet['native_tick'],input_sha256=digest(f['request']),map_sha256=f['maps_sha256'],steering=list(controls),collision_rate=rate);return c,f,raw
 c,frame,raw=begin();answer=c.proposal(raw,now=100.);assert answer['body_request']==[.08,.08*math.tan(controls[0])/.6,False]and not answer['actual_execution_permitted'];negative=[]
 for name,change in [('foreign_tick',lambda v:v.update(origin_native_tick=1)),('foreign_run',lambda v:v.update(run_id='FOREIGN')),('wrong_map',lambda v:v.update(map_sha256='0'*64)),('wrong_request',lambda v:v.update(input_sha256='0'*64)),('actor_truth_reply',lambda v:v.update(actor_truth={})),('nonfinite_steer',lambda v:v['steering'].__setitem__(0,float('nan'))),('wrong_shape',lambda v:v.update(steering=[0.])),('Phase_cap_steer',lambda v:v['steering'].__setitem__(0,.44)),('bad_collision_rate',lambda v:v.update(collision_rate=-1.))]:
  b,f,v=begin();change(v)
  try:b.proposal(v,now=100.)
  except(AssertionError,ValueError):negative.append(name)
  else:raise AssertionError('SVG_BAD_REPLY_ACCEPTED:'+name)
 try:begin(gear=-1)
 except AssertionError as e:assert'SVG_AUTHOR_FORWARD_REFERENCE_ONLY'in str(e);negative.append('reverse_not_invented')
 else:raise AssertionError('SVG_REVERSE_SILENTLY_ASSIGNED')
 bad=copy.deepcopy(receipt);bad['scan']['actor_truth']={}
 try:begin(bad)
 except AssertionError:negative.append('actor_truth_scan')
 else:raise AssertionError('SVG_TRUTH_SCAN_ACCEPTED')
 try:c.proposal(raw,now=100.)
 except AssertionError:negative.append('duplicate_reply')
 else:raise AssertionError('SVG_DUPLICATE_REPLY')
 c.close()
 try:c.frame(np,receipt,goal_xy=original_request['goal_xy'],rear_path=path,gear=1)
 except AssertionError:negative.append('closed_handle')
 else:raise AssertionError('SVG_CLOSED_REUSED')
 result=dict(passed=True,CPU=7,positive_saved_author_output_firstcontrol_mapped_exact=True,negative_cases=negative,current_source_and_map_and_origin_bound=True,reverse_forwardonly_applicability_refusal=True,original5plus2200_and_capture_replay_audit_still_required=True,full_vehicle_qualified=False,formal_common_tasks=0,models=0,algorithm_DLLs=0,optimizer_queries=0,physics=0,replay=0,raw_steer_first=controls[0],proposed_request=answer['body_request'],actual_execution_permitted=False,source_SHA256={str(p.relative_to(R)):sha(p)for p in[WIRE,FRONT,BRIDGE,C/'interface.py',C/'qualify_software.py']});(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
