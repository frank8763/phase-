"""Saved-byte/array comparison for the new phase04 pair; no numerical replay."""
import hashlib,json,os,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v1643_formal_parent_metadata';D=R/'runs/v1748_phase04_pair_review/analysis'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def without_clocks(value):
 v=json.loads(json.dumps(value));v.pop('body_measured_at');v.pop('sent_at');v['steering'].pop('measured_at');return v
def main():
 assert os.sched_getaffinity(0)=={4},'OFFLINE_NON_MODEL_ARRAY_MATH_CPU4_ONLY'
 import numpy as np
 ids=['phase_04__no_onward','phase_04__full'];cases=[];paths=[]
 for aid in ids:
  O=ROOT/'rounds'/aid;assert read(O/'COMPLETION.json')['closed']and(O/'RUNTIME_CLOSED_REVIEW.json').exists()
  out=O/'actual';r=read(out/'RESULT.json');a=read(O/'FORMAL_ADMISSION.json');task=read(O/'FORMAL_TASK.json')
  with np.load(out/'physics/NATIVE_TRACE.npz')as z:trace={k:z[k].copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat','time']}
  with zipfile.ZipFile(out/'INITIAL_FULL_STATE.npz')as z:initial={k:hashlib.sha256(z.read(k)).hexdigest()for k in z.namelist()}
  setup=read(out/'physics/SETUP.json');packet=read(out/'CANONICAL_INITIAL_PACKET.json');journal=read(out/'APPLIED_JOURNAL.json');requests=np.asarray([x['request']for x in journal],float)
  cases.append(dict(id=aid,result=r,admission=a,task=task,trace=trace,initial=initial,setup=setup,packet=packet,requests=requests))
  paths.extend([O/'COMPLETION.json',O/'FORMAL_TASK.json',O/'FORMAL_ADMISSION.json',out/'RESULT.json',out/'INITIAL_FULL_STATE.npz',out/'CANONICAL_INITIAL_PACKET.json',out/'APPLIED_JOURNAL.json',out/'physics/SETUP.json',out/'physics/NATIVE_TRACE.npz'])
 left,right=cases;common_keys=['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic']
 same_task=all(left['task'][k]==right['task'][k]for k in common_keys)
 same_source=left['admission']['source_freeze_sha256']==right['admission']['source_freeze_sha256']and left['admission']['source_version_root']==right['admission']['source_version_root']
 initial_equal=left['initial']==right['initial'];packet_equal=without_clocks(left['packet'])==without_clocks(right['packet'])
 setup_equal=all(left['setup'][k]==right['setup'][k]for k in ['known','limits','slew_per_second','dt'])
 limit=min(len(left['trace']['time']),len(right['trace']['time']));firsts={}
 for k in left['trace']:
  a,b=left['trace'][k][:limit],right['trace'][k][:limit];assert a.shape==b.shape
  diff=np.any((a!=b).reshape((limit,-1)),axis=1);indices=np.flatnonzero(diff);firsts[k]=int(indices[0]+1)if len(indices)else None
 a,b=left['requests'][:limit],right['requests'][:limit];indices=np.flatnonzero(np.any(a!=b,axis=1));request_first=int(indices[0]+1)if len(indices)else None
 first=min([v for v in firsts.values()if v is not None],default=limit+1);prefix=min(first-1,limit)
 rows=[]
 for d in cases:
  r=d['result'];phy=r['physical'];pre=r.get('independent_prefix_audit')or{};full=r.get('independent_audit')or{}
  rows.append(dict(assignment=d['id'],success=r['passed'],actual_original_goal_reached=r.get('actual_original_goal_reached',False),actual_native=r['new_actual_native'],own_replay_native=r['own_replay_native'],goal_distance_m=phy['goal_distance_m'],minimum_actual_clearance_m=phy['minimum_actual_clearance_m'],bad_contacts=phy['bad_contacts'],replay_error=r['replay']['maximum_qpos_qvel_ctrl_mocap_error'],contact_mismatch=r['replay']['contact_mismatched_ticks'],first_error=r['first_error'],secondary_errors=r['secondary_errors'],independent_full_goal_audit_passed=bool(full.get('passed')),independent_prefix_safety_audit_passed=bool(pre.get('passed')),error_stop_origin_native=(r.get('error_stop_progress')or{}).get('origin_native'),error_stop_applied=(r.get('error_stop_progress')or{}).get('applied'),normal_nonzero_requests=int(np.any(d['requests'][:,:2]!=0,axis=1).sum())))
 evidence=dict(scope='closed saved pair metadata/array comparison only; not an independent physical audit',same_scientific_task_except_declared_variant=same_task,same_frozen_source=same_source,initial_state_member_SHA_equal=initial_equal,initial_packet_equal_except_actual_wall_measurement_times=packet_equal,public_setup_equal=setup_equal,common_exact_physical_state_control_mocap_time_prefix_native=prefix,first_nonidentical_native_by_array=firsts,first_nonidentical_body_request_native=request_first,shorter_trace_native=limit,rows=rows,pair_interpretation_eligible=all([same_task,same_source,initial_equal,packet_equal,setup_equal]),new_models=0,new_planner_calls=0,new_Allocator_calls=0,new_physical_or_replay_native=0,statistical_superiority_established=False,source_paths_SHA256={str(p.relative_to(R)):sha(p)for p in paths},late_analysis_source_not_in_prior_case_archive=True)
 D.mkdir(parents=True,exist_ok=False);(D/'PAIR_ANALYSIS.json').write_text(json.dumps(evidence,indent=2)+'\n')
 (D/'PAIR_SUMMARY.csv').write_text('assignment,success,actual_native,own_replay_native,goal_distance_m,min_actual_clearance_m,bad_contacts,prefix_safety_audit_passed,full_goal_audit_passed\n'+'\n'.join(','.join(str(x[k])for k in ['assignment','success','actual_native','own_replay_native','goal_distance_m','minimum_actual_clearance_m','bad_contacts','independent_prefix_safety_audit_passed','independent_full_goal_audit_passed'])for x in rows)+'\n')
 print(json.dumps({k:evidence[k]for k in ['pair_interpretation_eligible','common_exact_physical_state_control_mocap_time_prefix_native','first_nonidentical_body_request_native','rows']}))
if __name__=='__main__':main()
