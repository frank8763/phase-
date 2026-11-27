"""New control-journal audit with explicit synthetic file/NN/physical boundaries."""
from context import R,C,read,load,digest
from pathlib import Path
from types import SimpleNamespace
import os,copy,json,traceback
import numpy as np
S=R/'runs'/C.name;assert os.sched_getaffinity(0)=={0}and not(S/'CONTROL_AUDIT_PREFLIGHT.json').exists()
OLD=R/'runs/v2170_sccr_live_source_scope/components/SCCR/actual';task=read(S/'components/SCCR/PILOT_TASK.json');out=S/'software_control_audit_not_actual';out.mkdir(exist_ok=False)
audit=load('CP_new_control_audit_fixture',C/'union_audit.py');assembly=load('CP_audit_fixture_assembly',C/'assemble.py');cp=load('CP_audit_fixture_controller',C/'cp_controller.py')
original_load=audit.load;original_read=audit.read
memory={'SETUP.json':read(OLD/'physics/SETUP.json'),'SCCR_UNION_PUBLIC_ROUTE.json':read(OLD/'SCCR_UNION_PUBLIC_ROUTE.json')};rows=[];controller=cp.Controller(task['run_id']);full={};depth_calls=[]
# Only three saved mocap frames are read, for new software arithmetic fixtures.
with np.load(OLD/'FULL_STATE_NPLUS1.npz')as z:
 for key in ['mocap_pos','mocap_quat']:
  shape=(11,)+z[key].shape[1:];full[key]=np.zeros(shape,dtype=z[key].dtype)
  for k in [0,5,10]:full[key][k]=z[key][k]
for k in [0,5,10]:
 a=read(OLD/f'SCCR_UNION_{k:06d}.json');p=a['sensor_packet'];previous=controller.previous_action();p['previous_body_command']=previous['virtual_action'];p['producer_proof'].update(episode_id=task['run_id'],previous_action_commit=previous['commit'],previous_action_from_committed_same_episode_prefix=True)
 p['producer_proof'].pop('previous_action_zero_from_entire_zero_request_journal',None)
 base=np.asarray(a['assembly']['base_action_2'],np.float32);obs,parts=assembly.build(np,p,lambda _:base.copy());a.update(sensor_packet_sha256=digest(p),assembly=parts,observation186=obs.tolist(),actual_commands_not_implied_by_capture=True,actor_outputs_used_for_controller_proposal=(k in [0,5]));a.pop('actor_outputs_not_executed',None)
 memory[f'SCCR_UNION_{k:06d}.json']=copy.deepcopy(a);memory[f'SCCR_UNION_PRIVATE_{k:06d}.json']=read(OLD/f'SCCR_UNION_PRIVATE_{k:06d}.json');memory[f'SCCR_DEPTH_{k:06d}.json']=read(OLD/f'SCCR_DEPTH_{k:06d}.json');memory[f'cycle_{k//5:06d}_origin.json']=dict(receipt=a['receipt'])
 if k<10:
  q=controller.propose(a,episode_id=task['run_id']);memory[f'SCCR_CP_{k//5:06d}_PROPOSAL.json']=q
  applied=[dict(episode_id=task['run_id'],before_native=k+i,request=q['request'],applied=True)for i in range(5)]
  after=read(OLD/f'cycle_{k//5+1:06d}_origin.json')['receipt']['packet'];committed=controller.commit(after,episode_id=task['run_id'],token=q['token'],applied_rows=applied);memory[f'SCCR_CP_COMMIT_{k+5:06d}.json']=committed
  rows.extend(dict(before_native=k+i,phase='FILTER_RECEDING_CURRENT',request=q['request'].copy(),applied=True)for i in range(5))
rows.extend(dict(before_native=k,phase='FILTER_SEGMENT_COMPLETE_STOP',request=[0.,0.,False],applied=True)for k in range(10,2210));memory['APPLIED_JOURNAL.json']=rows
controller.close()
for name in memory:
 if name.startswith(('SCCR_UNION_','SCCR_CP_')):(out/name).write_text('{"EXPLICIT_SOFTWARE_MARKER_ONLY":true}\n')
class Arrays:
 def __enter__(self):return full
 def __exit__(self,*a):return False
class NP:
 def __getattr__(self,k):return getattr(np,k)
 def load(self,p):assert Path(p)==out/'FULL_STATE_NPLUS1.npz';return Arrays()
def fixture_load(n,p):
 if Path(p).name=='depth.py':return SimpleNamespace(audit_saved=lambda *a:depth_calls.append('explicit_fake_depth_saved_boundary'))
 return original_load(n,p)
audit.load=fixture_load;audit.read=lambda p:copy.deepcopy(memory[Path(p).name])
try:
 verified=audit.audit_saved(NP(),out,task,{})
 assert len(verified)==3 and len(depth_calls)==3 and all(row['previous_action_from_actual_committed_prefix']for row in verified)
 # These are SYNTHETIC applied rows, not new physical prefix evidence.
 baseline=copy.deepcopy(memory);negative=[]
 for label in ['actual_request_tamper','saved_token_tamper','prefix_phase_tamper']:
  memory=copy.deepcopy(baseline)
  if label=='actual_request_tamper':memory['APPLIED_JOURNAL.json'][2]['request'][0]+=.001
  if label=='saved_token_tamper':memory['SCCR_CP_000000_PROPOSAL.json']['token']='bad'
  if label=='prefix_phase_tamper':memory['APPLIED_JOURNAL.json'][2]['phase']='error_stop'
  try:audit.audit_saved(NP(),out,task,{})
  except (AssertionError,ValueError,KeyError)as e:negative.append(dict(case=label,error=str(e)))
  else:raise AssertionError('CONTROL_AUDIT_NEGATIVE_ACCEPTED')
 result=dict(passed=True,closed=True,scope='NEW_INDEPENDENT_CONTROL_JOURNAL_AUDIT_WITH_EXPLICIT_SYNTHETIC_BOUNDARIES',
  saved_measured_fixture_frames=len(verified),negative_cases=negative,depth_render_audit_boundary_was_STUB_NOT_OLD_REAUDIT=True,
  synthetic_applied_journal_not_actual_commands=True,recorded_actor_outputs_used_as_explicit_stubs_not_new_inference=True,
  new_models_NN_render_physics_replay_physical_audit_source_claims=0)
 (S/'CONTROL_AUDIT_PREFLIGHT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='negative_cases'}))
except BaseException as e:
 (S/'CONTROL_AUDIT_PREFLIGHT_FAILED.json').write_text(json.dumps(dict(error=repr(e),traceback=traceback.format_exc(),new_models_physics=0),indent=2)+'\n');raise
