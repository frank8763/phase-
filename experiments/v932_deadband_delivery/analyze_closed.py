"""Independent closed saved evidence diagnosis; no ROS, vehicle or model imports."""
import copy,gzip,hashlib,importlib.util,json,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];C=R/'experiments/v931_deadband_consistent_mppi';P=R/'runs/v858_nav2_verified/v931/static_main_we';O=R/'runs/v932_deadband_delivery';O.mkdir(exist_ok=True);REC=R/'records/nav2_v931_20261109'
N=json.loads((P/'RESULT.json').read_text());task=json.loads((P/'TASK.json').read_text());J=json.loads(gzip.decompress((P/'INGRESS.json.gz').read_bytes()));B=json.loads((P/'physics/BODY_COMMANDS.json').read_text());D=json.loads((P/'MPPI_DIAGNOSTICS.json').read_text());A=json.loads((P/'INDEPENDENT_AUDIT.json').read_text());F=json.loads((P/'FINAL_COMMAND_ATTEMPTS.json').read_text());cmd=json.loads((P/'COMMANDS.json').read_text());profile=json.loads((P/'RUNTIME_TIMING.json').read_text());timing=np.load(P/'RUNTIME_TIMING.npz')['rows'];stage=profile['stages']['receive'];by_tick={int(row[0]):row for row in timing[timing[:,1]==stage]};cut=N['armed_at']+task['wall_limit_s']
spec=importlib.util.spec_from_file_location('production_contract',C/'twist_contract.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def independent(journal,body_commands):
 receipts=journal['receipts'];phase='WAITING';last=-1;command=None;j=0;local_tick=None;novel=[]
 assert len(journal['execution'])==len(body_commands)==N['actual_native']
 for e,b in zip(journal['execution'],body_commands):
  while j<len(receipts)and receipts[j]['received_at']<=e['at']:
   row=receipts[j];j+=1;p=row['packet'];assert p['run_id']==task['run_id']and row['decision']!='ABORT'
   if p['kind']=='arm'and phase=='WAITING':phase='RUNNING'
   elif p['kind']=='stop':phase='STOPPING'
   elif p['kind']=='command':
    m.require_representable(p['v'],p['w']);assert 0<=row['received_at']-p['issued_at']<=.2
    if phase=='STOPPING':assert row['decision']=='POST_STOP_COMMAND_IGNORED'
    else:assert phase=='RUNNING'and p['sequence']>last;last=p['sequence'];command=p
  # frozen native loop samples `now` within this recorded receive-stage interval,
  # then sets STOPPING locally on its own 180s wall deadline before step.
  interval=by_tick[e['native_tick']-1];lo,hi=interval[2],interval[2]+interval[3]
  assert not(lo<cut<=hi),'AMBIGUOUS_LOCAL_DEADLINE_INTERVAL'
  oldphase=phase
  if lo>=cut:
   if local_tick is None:local_tick=e['native_tick']
   phase='STOPPING'
  stale=phase!='RUNNING'or command is None or e['at']-command['issued_at']>.2
  expected=[0.,0.,True]if stale else[float(command['v']),float(command['w']),False]
  assert e['controls']==expected and b[1:3]==expected[:2]and b[5]==expected[2]
  assert e['sequence']==(None if command is None else command['sequence'])
  if oldphase=='RUNNING'and lo>=cut:novel.append(e['native_tick'])
 return dict(passed=True,all_native_rows=len(body_commands),first_local_deadline_tick=local_tick,source_deadline_from_arm_s=task['wall_limit_s'],local_receive_interval_unambiguous=True,local_stop_before_external_stop_ticks=novel,original_frozen_ingress_verdict_overwritten=False)
supplement=independent(J,B)
negative=copy.deepcopy(B);negative[18001][1]=.1
try:independent(J,negative);raise RuntimeError('NEGATIVE_NOT_CAUGHT')
except AssertionError:negative_pass=True
for row in F:m.require_representable(row['v'],row['w'])
final_log_ok=len(F)==len(cmd['cmd_vel'])and all(x['decision']=='ACCEPTED'and [x['v'],x['w']]==y[1:]for x,y in zip(F,cmd['cmd_vel']))
deadband_ok=all(abs(x['v'])>=.005 or x['v']==0 and x['w']==0 for x in D)
trace=np.load(P/'physics/NATIVE_TRACE.npz');xy=np.vstack([[-4.,-2.],trace['qpos'][:,:2]]);body=np.asarray(B);steps=np.linalg.norm(np.diff(xy,axis=0),axis=1);gear=np.array([x['gear']for x in D]);periods=np.array([x['received_at']for x in D]);flips=periods[1:][gear[1:]!=gear[:-1]]
plans=json.loads((P/'PLANS.json').read_text());routes=[];reverse_prefixes=[]
for p in plans:
 q=np.asarray(p['path']);length=np.linalg.norm(np.diff(q[:,:2],axis=0),axis=1);forward=np.sum(np.diff(q[:,:2],axis=0)*np.column_stack([np.cos(q[:-1,2]),np.sin(q[:-1,2])]),axis=1);valid=np.where((length>.002)&(abs(forward)>.001))[0];first=None if not len(valid)else int(np.sign(forward[valid[0]]));
 if first==-1:
  signed=np.sign(forward[valid]);valid_length=length[valid];end=next((i for i,g in enumerate(signed)if g>0),len(signed));reverse_prefixes.append(float(valid_length[:end].sum()))
 routes.append(dict(at=p['at'],first_raw_gear=first,reverse_length_m=float(np.sum(length[forward<0])),length_m=float(length.sum())))
result=dict(status='NOT_PASSED',models_in_analysis=0,integrations_in_analysis=0,actual_native=N['actual_native'],own_replay_native=N['replay_native'],private_native=N['private_native'],minimum_clearance_m=N['minimum_actual_clearance_m'],bad_contacts=N['bad_contacts'],goal_distance_m=N['goal_distance_m'],actual_travel_m=float(steps.sum()),best_goal_m=float(np.min(np.linalg.norm(xy-task['goal_xy'],axis=1))),controller_records=len(D),controller_gear_flips=int(len(flips)),controller_reverse_records=int(sum(gear<0)),gear_flips_within_150ms_of_new_plan=int(sum(np.min(abs(np.array([x['at']for x in routes])-t))<=.15 for t in flips)),raw_reverse_prefix_length_m=dict(minimum=min(reverse_prefixes),median=float(np.median(reverse_prefixes)),maximum=max(reverse_prefixes)),plan_count=len(routes),raw_path_first_reverse_count=sum(x['first_raw_gear']==-1 for x in routes),desired_v_mean_m_s=float(body[:,1].mean()),measured_v_mean_m_s=float(body[:,3].mean()),desired_v_integral_m=float(body[:,1].sum()*.01),measured_v_integral_m=float(body[:,3].sum()*.01),actual_reverse_travel_m=float(steps[body[:,3]<-.005].sum()),desired_reverse_native_ticks=int(sum(body[:,1]<-.005)),actual_reverse_native_ticks=int(sum(body[:,3]<-.005)),zero_desired_ticks=int(sum(abs(body[:,1])<.005)),desired_w_rmse_actual=float(np.sqrt(np.mean((body[:,2]-body[:,4])**2))),mppi_compute_s=dict(p50=float(np.quantile([x['compute_s']for x in D],.5)),p99=float(np.quantile([x['compute_s']for x in D],.99)),maximum=max(x['compute_s']for x in D)),maximum_native_wall_lag_s=N['maximum_wall_lag_s'],deadband_output_contract_passed=deadband_ok,all_final_twists_logged_before_validation=final_log_ok,original_independent_audit_passed=A['passed'],original_evidence_passed=A['evidence_passed'],all_original_physical_checks_passed=all(A['checks'].values()),original_ingress_failure_preserved=True,deadline_only_stop_native_ticks=list(range(supplement['first_local_deadline_tick'],min(r['native_tick']for r in J['receipts']if r['packet']['kind']=='stop')+1)),supplemental_local_deadline_ingress_reconstruction=supplement,supplemental_control_tamper_negative_passed=negative_pass,arrival_passed=False,unexecuted_navigation=3,new24='UNEXECUTED',scope='Deadband defect fixed; static functional deadline failure remains. Supplement explains 3 local STOPPING rows, never retroactively changes original failed batch or proves arrival.')
assert result['deadband_output_contract_passed']and final_log_ok
(O/'SAVED_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n');(REC/'SAVED_DIAGNOSIS.json').write_bytes((O/'SAVED_DIAGNOSIS.json').read_bytes());print(json.dumps(result))
