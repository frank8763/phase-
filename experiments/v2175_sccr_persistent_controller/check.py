"""Explicit software boundary fixtures: NO newly applied commands or inference."""
from pathlib import Path
import json,copy,os,hashlib,math
import numpy as np
from controller import Controller,digest,assembly
R=Path(__file__).resolve().parents[2];OUT=R/'runs/v2175_sccr_persistent_controller';PRIOR=R/'runs/v2170_sccr_live_source_scope/components/SCCR/actual'
assert os.sched_getaffinity(0)=={0}and not(OUT/'RESULT.json').exists()
saved={k:json.loads((PRIOR/f'SCCR_UNION_{k:06d}.json').read_text())for k in [0,5,10]}
E='EXPLICIT_SOFTWARE_FIXTURE_NOT_ACTUAL_ISSUED_COMMANDS'

def frame(c,k,*,blocked=False):
 a=copy.deepcopy(saved[k]);p=a['sensor_packet'];previous=c.previous_action()
 p['previous_body_command']=previous['virtual_action'];p['producer_proof']['episode_id']=E;p['producer_proof']['previous_action_commit']=previous['commit']
 if blocked:p['core_lidar36_raw_m']=[3.]*36;p['core_lidar36_raw_m'][0]=.1
 # Recorded actor OUTPUTS are explicit input stubs for changed observations, not re-inferred policies.
 base=np.asarray(a['assembly']['base_action_2'],dtype=np.float32)
 obs,parts=assembly.build(np,p,lambda _:base.copy());a['assembly']=parts;a['observation186']=obs.tolist();a['sensor_packet_sha256']=digest(p)
 a['software_fixture_only']='measured_saved_body_plus_synthetic_applied_journal_and_recorded_output_stub'
 return a

def rows(q):return [dict(episode_id=E,before_native=q['origin_native']+i,request=q['request'].copy(),applied=True)for i in range(5)]
def commit(c,q,k,*,patch=None):
 p=copy.deepcopy(saved[k]['receipt']['packet']);rs=rows(q)
 if patch:patch(p,rs)
 return c.commit(p,episode_id=E,token=q['token'],applied_rows=rs)

c=Controller(E);a0=frame(c,0);q0=c.propose(a0,episode_id=E);m0=c.memory();commit(c,q0,5)
a5=frame(c,5);assert a5['sensor_packet']['previous_body_command']!=[0.,0.] and a5['observation186'][40:42]!=[0.,0.]
assert a5['sensor_packet']['producer_proof']['previous_action_commit']['end_native']==5
q5=c.propose(a5,episode_id=E);m5=c.memory();commit(c,q5,10);m10=c.memory()
assert m5['motor_arithmetic_memory'][2]>m0['motor_arithmetic_memory'][2]>0 and m10['proposals']==m10['commits']==2
expected=float(np.linalg.norm(np.asarray(a5['sensor_packet']['goal_xy'],np.float32)-np.asarray(saved[10]['receipt']['packet']['body'][:2],np.float32)))
assert c.leaf.prev_goal_dist_residual==expected
assert c.pending is None and c.expected_native==10 and c.previous_action()['commit']['end_native']==10
bc=Controller(E);bq0=bc.propose(frame(bc,0,blocked=True),episode_id=E);timer0=bc.leaf.recovery_timer;commit(bc,bq0,5);bq5=bc.propose(frame(bc,5,blocked=True),episode_id=E);timer5=bc.leaf.recovery_timer
assert bc.leaf.recovery_stage=='BACKUP' and timer5==timer0-1
neg=[]
for label in ['double_propose','foreign_episode','wrong_commit_request','wrong_commit_native','wrong_commit_time','partial_prefix','foreign_commit_episode','wrong_token','packet_hash','receipt_body','previous_virtual','prefix_provenance','wrong_observation186','policy_inflight','source_native','route_change']:
 t=Controller(E);a=frame(t,0);q=None
 try:
  if label=='foreign_episode':t.propose(a,episode_id='FOREIGN')
  elif label in ['packet_hash','receipt_body','previous_virtual','prefix_provenance','wrong_observation186','policy_inflight','source_native']:
   if label=='packet_hash':a['sensor_packet_sha256']='0'*64
   if label=='receipt_body':a['receipt']['packet']['body'][0]+=.01
   if label=='previous_virtual':a['sensor_packet']['previous_body_command']=[.1,.2];a['sensor_packet_sha256']=digest(a['sensor_packet'])
   if label=='prefix_provenance':a['sensor_packet']['producer_proof']['previous_action_commit']={'foreign':True};a['sensor_packet_sha256']=digest(a['sensor_packet'])
   if label=='wrong_observation186':a['observation186'][40]+=.01
   if label=='policy_inflight':a['model_counts']['inflight']=['forward',186,0]
   if label=='source_native':a['sensor_packet']['producer_proof']['native']=5;a['sensor_packet_sha256']=digest(a['sensor_packet'])
   t.propose(a,episode_id=E)
  else:
   q=t.propose(a,episode_id=E)
   if label=='double_propose':t.propose(a,episode_id=E)
   elif label=='route_change':
    commit(t,q,5);b=frame(t,5);b['sensor_packet']['path_world'][1][1]+=.01;b['sensor_packet_sha256']=digest(b['sensor_packet']);t.propose(b,episode_id=E)
   else:
    p=copy.deepcopy(saved[5]['receipt']['packet']);rs=rows(q);eid=E;token=q['token']
    if label=='wrong_commit_request':rs[2]['request'][0]+=.001
    if label=='wrong_commit_native':p['native_tick']=10;p['sim_time']=.1
    if label=='wrong_commit_time':p['sim_time']=.025
    if label=='partial_prefix':rs=rs[:-1]
    if label=='foreign_commit_episode':eid='FOREIGN'
    if label=='wrong_token':token='bad'
    t.commit(p,episode_id=eid,token=token,applied_rows=rs)
 except (AssertionError,ValueError,KeyError)as err:
  assert t.poisoned
  try:t.propose(a,episode_id=E)
  except ValueError as again:assert str(again)=='CLOSED_OR_POISONED_CONTROLLER'
  else:raise AssertionError('POISONED_RETRY_ACCEPTED')
  neg.append(dict(case=label,first_error=str(err),poisoned_retry_refused=True))
 else:raise AssertionError('NEGATIVE_ACCEPTED:'+label)

r=dict(passed=True,closed=True,scope='PERSISTENT_CONTROLLER_PROPOSE_COMMIT_SOFTWARE_FIXTURES_ONLY',
 normal_proposals_commits=[c.proposals,c.commits],first_memory=m0,second_memory=m5,committed_memory=m10,
 nonzero_previous_virtual_action_and_complete186_provenance_bound=True,recovery_timer=[timer0,timer5],negative_cases=neg,
 controller_native_dt_s=.01,prefix_native=5,prefix_duration_s=.05,
 actual_saved_body_measurements_reused=True,newly_projected_requests_NOT_physically_executed=True,
 modified_observation_actor_outputs_are_EXPLICIT_RECORDED_OUTPUT_STUBS=True,new_NN_render_model_physics_replay_audit_source_formal=0,
 actual_online_controller_or_navigation_qualified=False,
 source_sha256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__).parent/'controller.py',R/'experiments/v2173_sccr_inner_control_readout/readout.py',R/'experiments/v2171_sccr_control_contract_readout/study.py',R/'experiments/v2170_sccr_live_source_scope/assemble.py',R/'experiments/v2174_shared_virtual_command_domain/domain.py']},
 input_sha256={str((PRIOR/f'SCCR_UNION_{k:06d}.json').relative_to(R)):hashlib.sha256((PRIOR/f'SCCR_UNION_{k:06d}.json').read_bytes()).hexdigest()for k in saved})
raw=json.dumps(r,indent=2,allow_nan=False)+'\n';assert len(raw.encode())<96*1024;(OUT/'RESULT.json').write_text(raw)
print(json.dumps({'passed':True,'persistent_proposals_commits':[2,2],'negative_cases':len(neg),'recovery_timer':[timer0,timer5],'new_NN_physics':0}))
