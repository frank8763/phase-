"""Independent persisted-evidence checks; no controller/simulator import or steps."""
import gzip,hashlib,json,math,argparse
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2]
def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(s)for s in p.read_text().splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
window=repo/'runs/v675_dynamic_joint_admission/development01'
assert (window/'COMPLETION.json').exists(),'Do not audit unfinished candidate'
outcomes=read(window/'RESULTS.json',) if (window/'RESULTS.json').exists() else []
roots=[window.parent/x['name']/'paired'for x in outcomes]
records=[]
for root in roots:
 cell=root/'geometry_memory'
 if not (cell/'result.json').exists() or not (root/'NATIVE_REPLAY_AUDIT.json').exists():
  records.append({'run':str(root.relative_to(repo)),'passed':False,'outcome':'INTERRUPTED_OR_NATIVE_REPLAY_MISSING','interrupted':read(cell/'interrupted.json')if(cell/'interrupted.json').exists()else None,'scope':'no completed full physical audit claimed'});continue
 r=read(cell/'result.json');model=read(root/'STATIC_PROTOCOL.json');motion=read(root/'DYNAMIC_PROTOCOL.json')
 replay=read(root/'NATIVE_REPLAY_AUDIT.json');execution=lines(cell/'v648_execution.jsonl');admissions=lines(cell/'model_admission.jsonl')
 with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as f:native=[json.loads(s)for s in f]
 c=motion;xy=np.asarray([s['actor_xy']for s in native]);t=np.asarray([s['time']for s in native]);a=np.asarray(c['anchor_xy']);axis=np.asarray(c['axis_xy'])
 expected=a+np.sin(t*c['omega_rad_s']+c['phase_rad'])[:,None]*c['amplitude_m']*axis
 displacement=np.linalg.norm(np.diff(xy,axis=0),axis=1)
 h=hashlib.sha256();contact_count=0;unknown_count=0;obstacle_count=0
 with gzip.open(cell/'contacts.jsonl.gz','rb')as f:
  for b in f:
   h.update(b);row=json.loads(b);kind=row['contact_type'];contact_count+=1
   unknown_count+=kind=='unknown_contact';obstacle_count+=kind in ['robot_obstacle_contact','robot_obstacle_penetration']
 source=read(root.parent/'source_snapshot/SHA256.json')
 source_match=all(sha(root.parent/'source_snapshot'/name)==digest for name,digest in source.items())
 certificate=c['swept_envelope_reference']
 checks={'all_public_and_native_records':len(execution)==r['public_steps']==len(admissions)and len(native)==r['physics_steps']==8*len(execution),
         'source_snapshot':source_match,'saved_model':sha(root/'scene_model.mjb')==model['full_model_sha256']==replay['scene_model_sha256'],
         'causal_admission':all(s['hidden_world_geometry_used']is False and s['dynamic_time_gate']is True for s in admissions),
         'actor_motion_formula':float(np.max(abs(expected-xy)))<=1e-12,
         'actor_mocap_at_all_native_ticks':all(np.max(abs(np.asarray(s['mocap_pos'])[c['mocap_id'],:2]-s['actor_xy']))<=1e-12 for s in native),
         'native_time_steps':np.max(abs(np.diff(t)-.01))<=1e-10,
         'motion_bounds':np.max(np.linalg.norm(xy-a,axis=1))<=.25+1e-10 and np.max(displacement)<=.08*.01+1e-10,
         'smaller_actor':c['radius_m']==.10,'not_at_junction':c['protected_junction_clearance_of_sweep_m']>=.05,
         'swept_known_geometry_clearance':c['known_obstacle_clearance_of_swept_envelope_m']>=.55,
         'full_sweep_bypass':certificate['eligible']and certificate['continuous_polygonal_pose_clearance_lower_bound_m']>=.15 and certificate['search']['minimum_clearance_m']>=.155,
         'online_native_clearance':min(s['actual_clearance_m']for s in native)>=.15 and abs(min(s['actual_clearance_m']for s in native)-r['minimum_dynamic_native_clearance_m'])<=1e-12,
         'full_replay':replay['status']=='MATCHED_RECORDED_PUBLIC_STATES'and replay['replay_integration_steps']==len(native)and max(replay['maximum_full_public_qpos_error'],replay['maximum_full_public_qvel_error'],replay['maximum_public_mocap_error'])<=1e-8,
         'replay_safety':replay['minimum_reconstructed_native_actual_axis_AABB_clearance_m']>=.15 and replay['reconstructed_native_states_below_015']==0 and replay['minimum_reconstructed_self_domain_margin_m']>=0,
         'zero_contact':obstacle_count==unknown_count==replay['replay_obstacle_contact_records']==replay['replay_unknown_contact_records']==0,
         'raw_contact_digest':h.hexdigest()==r['contacts']['contact_log_content_sha256']and contact_count==r['contacts']['all_contact_records'],
         'self_coverage':r['self_geometry_checked_native_ticks']==len(native)and r['minimum_actual_self_domain_margin_m']>=0,
         'native_root_only':r['root_mutations_outside_mjstep']==0,
         'strict_outcome_consistent':r['strict_safe_arrival']==bool(r['outcome']=='GOAL'and r['goal_distance_m']<=.45 and obstacle_count==unknown_count==0)}
 records.append({'run':str(root.relative_to(repo)),'passed':all(checks.values()),'checks':checks,'outcome':r['outcome'],'strict_arrival':r['strict_safe_arrival'],
     'public_steps':len(execution),'native_steps':len(native),'minimum_native_clearance_m':min(s['actual_clearance_m']for s in native),
     'actor_displacement_span_m':float(np.linalg.norm(xy.max(axis=0)-xy.min(axis=0))),
     'actor_max_native_displacement_m':float(np.max(displacement)),'raw_contact_records':contact_count})
origin=read(repo/'runs/v674_dynamic_renewable_backup/ROUND_WINDOW.json');final=read(window/'COMPLETION.json');w=read(window/'WINDOW.json')
def union_check(state,config):
 times=np.linspace(0,3.28,329);t=times[:,None,None];a=np.asarray(state['outer_state_cells']);pl,pu,vl,vu=[a[:,i][None,:,:]for i in range(4)]
 low=np.maximum(pl+t*vl-.02*t*t,pl-.12*t);high=np.minimum(pu+t*vu+.02*t*t,pu+.12*t)
 truth=np.asarray(config['anchor_xy'])+np.sin((state['time']+times)*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy'])
 velocity=np.cos(state['time']*config['omega_rad_s']+config['phase_rad'])*config['maximum_speed_m_s']*np.asarray(config['axis_xy'])
 excess=float(np.maximum(low-truth[:,None,:],truth[:,None,:]-high).max(axis=2).min(axis=1).max())
 joint=float(np.maximum.reduce([a[:,0]-truth[0],truth[0]-a[:,1],a[:,2]-velocity,velocity-a[:,3]]).max(axis=1).min())
 return excess,joint
coverage=[]
for root in roots:
 rows=lines(root/'geometry_memory/motion_estimate.jsonl');c=read(root/'DYNAMIC_PROTOCOL.json');saved=lines(root/'geometry_memory/forecast_coverage.jsonl')
 values=[union_check(r,c)for r in rows];worst=max(x[0]for x in values);joint=max(x[1]for x in values)
 coverage.append({'run':str(root.relative_to(repo)),'frames':len(rows),'forecast_times_per_frame':329,'maximum_center_union_excess_m':worst,'maximum_joint_current_state_excess':joint,'saved_rows_pass':len(saved)==len(rows)and all(x['passed']and x['checked_future_samples']==329 for x in saved),'passed':worst<=1e-7 and joint<=1e-7 and len(saved)==len(rows)and all(x['passed']and x['checked_future_samples']==329 for x in saved)})
source=read(window/'SOURCE_FREEZE.json');documents=read(window/'DOCUMENT_FREEZE.json');src=repo/'experiments/v675_dynamic_joint_admission'
pose_errors=[]
for root in roots:
 trace=read(root/'geometry_memory/trace.json');admissions=lines(root/'geometry_memory/model_admission.jsonl')
 error=np.asarray([np.asarray(r['pose'])-a['predicted_next_pose']for r,a in zip(trace,admissions)]);error[:,2]=(error[:,2]+np.pi)%(2*np.pi)-np.pi
 pose_errors.append({'run':str(root.relative_to(repo)),'maximum_first_public_xy_yaw_error':np.max(abs(error),axis=0).tolist(),'public_steps':len(trace)})
reserve_checks=[]
for root in roots:
 cell=root/'geometry_memory';executions=lines(cell/'v648_execution.jsonl');admissions=lines(cell/'model_admission.jsonl');matches=lines(cell/'reserved_state_matches.jsonl')
 contracts=[]
 for file in sorted((cell/'recovery_contracts').glob('*.json.gz')):
  with gzip.open(file,'rt')as f:c=json.load(f)
  activation=c['activation_step'];used=[r for r in admissions if r.get('status')=='RETAINED_REVERSE_BRAKE_CONTRACT' and r.get('retained_from_step')==c['created_step']]
  assert len(used)<=40
  qerror=verror=controlerror=0.
  for row in used:
   t=row['step'];cursor=row['contract_native_cursor'];qerror=max(qerror,float(np.max(abs(np.asarray(executions[t]['qpos_full'])-c['qpos'][cursor+7]))));verror=max(verror,float(np.max(abs(np.asarray(executions[t]['qvel_full'])-c['qvel'][cursor+7]))));controlerror=max(controlerror,float(np.max(abs(np.asarray(executions[t]['ctrl'][:4])-c['controls'][cursor]))))
  state=c['forecast_state'];times=np.linspace(0,3.28,165);tt=times[:,None]
  low=np.maximum(np.asarray(state['position_lower'])+tt*np.asarray(state['velocity_lower'])-.02*tt**2,np.asarray(state['position_lower'])-.12*tt)
  high=np.minimum(np.asarray(state['position_upper'])+tt*np.asarray(state['velocity_upper'])+.02*tt**2,np.asarray(state['position_upper'])+.12*tt)
  config=read(root/'DYNAMIC_PROTOCOL.json');truth=np.asarray(config['anchor_xy'])+np.sin((state['time']+times)*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy'])
  excess,joint_excess=union_check(state,config)
  commands=np.asarray(c['controls'])[::8];deltas=np.diff(commands,axis=0)
  checks={'finite_forecast_coverage':excess<=1e-7 and joint_excess<=1e-7,'recorded_gate_threshold':c['minimum_causal_predicted_clearance_m']>=.155,'predicted_self_domain':c['minimum_predicted_self_domain_margin_m']>=.002,'terminal_braked':c['terminal_speed_m_s']<=.025,'appropriate_backup_kind':(c.get('recovery_kind','REVERSE_BRAKE')=='BRAKE_ONLY'and np.max(abs(np.asarray(c['target'])[2:]))==0)or(c.get('recovery_kind','REVERSE_BRAKE')=='REVERSE_BRAKE'and c['signed_reverse_displacement_m']<=-.02),'complete_control_and_state_sequence':len(c['controls'])==len(c['qpos'])==len(c['qvel'])==320,'all_executed_states_match':max(qerror,verror)<=1e-8,'all_executed_controls_match':controlerror<=1e-10,'command_slew_limits':np.max(abs(deltas[:,:2]))<=.1+1e-10 and np.max(abs(deltas[:,2:]))<=.7+1e-10,'causal_input_flag':c['hidden_world_geometry_used']is False}
  contracts.append({'file':str(file.relative_to(repo)),'activation_step':activation,'created_step':c['created_step'],'recovery_kind':c.get('recovery_kind','REVERSE_BRAKE'),'signed_displacement_m':c['signed_reverse_displacement_m'],'terminal_speed_m_s':c['terminal_speed_m_s'],'executed_public_steps':len(used),'maximum_executed_qpos_error':qerror,'maximum_executed_qvel_error':verror,'maximum_executed_command_error':controlerror,'past_forecast_maximum_center_excess_m':excess,'checks':checks,'passed':all(checks.values())})
 reserve_checks.append({'run':str(root.relative_to(repo)),'public_state_matches':len(matches),'maximum_full_qpos_qvel_error':max((max(r['maximum_qpos_error'],r['maximum_qvel_error'])for r in matches),default=None),'contracts':contracts,'passed':len(matches)==len(executions) and all(max(r['maximum_qpos_error'],r['maximum_qvel_error'])<=1e-8 for r in matches)and all(r['passed']for r in contracts)})
handover_checks=[]
for root in roots:
 cell=root/'geometry_memory';executions=lines(cell/'v648_execution.jsonl');admissions=lines(cell/'model_admission.jsonl');values=[]
 attempts=lines(cell/'handover_attempts.jsonl')if(cell/'handover_attempts.jsonl').exists()else[]
 for file in sorted((cell/'handover_certificates').glob('*.json.gz')):
  with gzip.open(file,'rt')as stream:c=json.load(stream)
  step=c['handover_step'];prior=executions[step-1];executed=executions[step];admit=admissions[step]
  # The retained contract may have begun earlier than its most recent executed row.
  oldcert=None
  for other in (cell/'recovery_contracts').glob('*.json.gz'):
   with gzip.open(other,'rt')as stream:previous=json.load(stream)
   if previous['created_step']==c['old_created_step']:oldcert=previous;break
  assert oldcert is not None
  cursor=c['old_native_cursor'];oq=oldcert['initial_qpos']if cursor==0 else oldcert['qpos'][cursor-1];ov=oldcert['initial_qvel']if cursor==0 else oldcert['qvel'][cursor-1]
  cmds=np.asarray(c['controls'])[::8];delta=np.diff(np.vstack((c['first_command'],cmds)),axis=0)
  errs={'entry_qpos':float(np.max(abs(np.asarray(prior['qpos_full'])-c['real_entry_qpos']))),'entry_qvel':float(np.max(abs(np.asarray(prior['qvel_full'])-c['real_entry_qvel']))),'old_qpos':float(np.max(abs(np.asarray(oq)-c['real_entry_qpos']))),'old_qvel':float(np.max(abs(np.asarray(ov)-c['real_entry_qvel']))),'new_first_qpos':float(np.max(abs(np.asarray(executed['qpos_full'])-c['initial_qpos']))),'new_first_qvel':float(np.max(abs(np.asarray(executed['qvel_full'])-c['initial_qvel']))),'new_first_command':float(np.max(abs(np.asarray(executed['ctrl'][:4])-c['first_command'])))}
  excess,joint=union_check(c['forecast_state'],read(root/'DYNAMIC_PROTOCOL.json'))
  checks={'complete_full_state_handover':max(errs.values())<=1e-8,'old_cursor_and_time':cursor==8*(step-oldcert['activation_step'])and abs(c['real_entry_time']-oldcert['start_time']-.01*cursor)<=1e-8,'fresh_forecast_timestamp':abs(c['forecast_state']['time']-c['real_entry_time'])<=1e-8,'finite_forecast_coverage':max(excess,joint)<=1e-7,'original_gates':c['minimum_causal_predicted_clearance_m']>=.155 and c['minimum_predicted_self_domain_margin_m']>=.002 and c['terminal_speed_m_s']<=.025,'new_full_tail':len(c['controls'])==len(c['qpos'])==len(c['qvel'])==320,'slew_limits':np.max(abs(delta[:,:2]))<=.1+1e-10 and np.max(abs(delta[:,2:]))<=.7+1e-10,'registered_progress_and_forward_gear':c['metadata']['predicted_goal_progress_m']>=.02 and c['metadata']['active_gear']==1,'admission_matches_certificate':admit.get('certified_backup_handover')is True and admit['recovery_reserve']['handover_certificate']==file.name,'causal_flag':c['hidden_world_geometry_used']is False}
  values.append({'file':str(file.relative_to(repo)),'step':step,'old_native_cursor':cursor,'checks':checks,'full_state_control_errors':errs,'passed':all(checks.values())})
 r=read(cell/'result.json');checks={'every_attempt_recorded':len(attempts)==r['certified_handover_attempts'],'every_success_certified':sum(x['status']=='CERTIFIED_RETURN'for x in attempts)==r['certified_handover_successes']==len(values),'all_certificates_valid':all(x['passed']for x in values)}
 handover_checks.append({'run':str(root.relative_to(repo)),'attempts':len(attempts),'successes':len(values),'certificates':values,'checks':checks,'passed':all(checks.values())})
joint_admission_checks=[]
for root in roots:
 cell=root/'geometry_memory';decisions=lines(cell/'control_decisions.jsonl');admissions=lines(cell/'model_admission.jsonl');executions=lines(cell/'v648_execution.jsonl');values=[]
 for admit in admissions:
  if admit['status']!='MODEL_SAFE_COMMAND'or admit.get('certified_backup_handover'):continue
  step=admit['step'];entry=next(x for x in decisions if x['step']==step and x['stage']=='NOMINAL'and x['candidate_role']=='ORDINARY')
  ordered=sorted([x for x in entry['candidates']if x['reason']is None],key=lambda x:x['score'],reverse=True);unique=[];seen=set()
  for candidate in ordered:
   key=tuple(candidate['first_command'])
   if key not in seen:seen.add(key);unique.append(candidate)
  rank=admit.get('joint_admission_distinct_command_rank',99);tested=[x for x in decisions if x['step']==step and x['stage']=='BACKUP_APPEND'and x['candidate_role']=='ORDINARY']
  checks={'registered_top_three_rank':rank in range(3)and rank<len(unique),'all_prior_ranks_tested_and_rejected':len(tested)==rank+1 and all(x['distinct_command_rank']==i and x['detail']['status']==('APPENDABLE_BACKUP_FOUND'if i==rank else'NO_APPENDABLE_BACKUP')for i,x in enumerate(tested)),'actual_input_equals_ranked_input':rank<len(unique)and np.max(abs(np.asarray(executions[step]['ctrl'][:4])-unique[rank]['first_command']))<=1e-10,'original_score_and_geometry_gate':rank<len(unique)and abs(admit['score']-unique[rank]['score'])<=1e-10 and abs(admit['predicted_minimum_clearance_m']-unique[rank]['minimum_clearance_m'])<=1e-10,'original_maximum_score_preserved':bool(unique)and abs(admit['ordinary_maximum_score']-unique[0]['score'])<=1e-10,'has_unchanged_full_reserve':admit['recovery_reserve']['reserve_total_native_ticks']==328 and admit['recovery_reserve']['reserve_minimum_clearance_m']>=.155}
  values.append({'step':step,'rank':rank,'checks':checks,'passed':all(checks.values())})
 joint_admission_checks.append({'run':str(root.relative_to(repo)),'ordinary_admissions':len(values),'alternative_admissions':sum(x['rank']>0 for x in values),'checks_all_passed':all(x['passed']for x in values),'failed_rows':[x for x in values if not x['passed']],'passed':bool(values)and all(x['passed']for x in values)})
old=repo/'runs/v664_dynamic_causal_proposals/dev34_95000011_proposal/paired'
checks={'joint_admission_rank_and_safety':all(x['passed']for x in joint_admission_checks),'certified_handover_checks':all(x['passed']for x in handover_checks),'retained_recovery_certificates':bool(reserve_checks)and all(r['passed']for r in reserve_checks),'all_native_records':bool(records)and all(r['passed']for r in records),'finite_prediction_coverage':bool(coverage)and all(r['passed']for r in coverage),
 'frozen_source_protocol':all(sha(src/n)==h for n,h in {**source,**documents}.items()),
 'deadline_unchanged':abs(w['absolute_deadline_unix']-origin['absolute_deadline_unix'])<=1e-6 and origin['absolute_deadline_unix']==final['absolute_deadline_unix'],
 'within_deadline':w['started_unix']+final['elapsed_s']<=origin['absolute_deadline_unix'],
 'within_registered_attempt_caps':origin['candidates_started']<=2 and origin['navigation_attempts']<=4,
 'old_task_model_initial_unchanged':all(read(r/'STATIC_PROTOCOL.json')['full_model_sha256']==read(old/'STATIC_PROTOCOL.json')['full_model_sha256'] and (read(r/'geometry_memory/result.json')['normalized_initial_state_hash']if(r/'geometry_memory/result.json').exists()else read(r/'geometry_memory/state_hash_normalization.json')['normalized_hash'])==read(old/'geometry_memory/result.json')['normalized_initial_state_hash']for r in roots if read(r/'STATIC_PROTOCOL.json')['seed']==95000011),
 'first_public_predicted_pose_matches':all(max(r['maximum_first_public_xy_yaw_error'])<=1e-8 for r in pose_errors),
 'all_registered_repeats_match':all(read(r/'EXACT_REPEAT_AUDIT.json')['matched']for r in roots if 'repeat'in str(r))}
output={'status':'EVIDENCE_AND_EXECUTED_NATIVE_CHECKS_PASS'if all(checks.values())else'FAIL','checks':checks,'branches':records,'coverage':coverage,'prediction_first_public_pose_checks':pose_errors,'reserved_recovery_checks':reserve_checks,'certified_handover_checks':handover_checks,'joint_admission_checks':joint_admission_checks,
 'distinct_development_tasks':len(set(read(r/'STATIC_PROTOCOL.json')['seed']for r in roots)),'navigation_branches_including_repeats':len(roots),'independent_confirmation_tasks':0,'strict_arrivals_including_repeats':sum(r.get('strict_arrival',False)for r in records),'verification_simulation_steps':0,'dynamic_stability_acceptance_passed':False,'scope':'finite development, no population, continuous-time or real-time guarantee'}
out=window.parent/'INDEPENDENT_DYNAMIC_AUDIT.json';out.write_text(json.dumps(output,indent=2,default=lambda x:x.item())+'\n');print(json.dumps(output,indent=2,default=lambda x:x.item()))
