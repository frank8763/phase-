"""One bounded exact-control replay to expose actual causal sensor packets."""
import signal,time,traceback,hashlib
from pathlib import Path
from bounded_execution import Window,read,dump,digest
src=Path(__file__).resolve().parent;repo=src.parents[1]
window=Window(src,'v662_dynamic_sensor_diagnosis','diagnosis01',3600,time.time()+3600)
source=repo/'runs/v659_dynamic_scene_repair/dev31_95000011_instant/paired/geometry_memory/v648_execution.jsonl'
name='sensor_replay_95000011';pair=window.root/name/'paired';status='RUNNING_DIAGNOSTIC_CONTROL_REPLAY'
dump(window.path/'CONTROL_SOURCE_FREEZE.json',{'path':str(source.relative_to(repo)),'sha256':digest(source),'public_steps':264,'new_navigation_tasks':0})
dump(window.root/'ROUND_LEDGER.json',{'status':'ACTIVE_DIAGNOSIS','original_deadline_unix':window.unix+window.limit,'maximum_s':3600,'development_revisions':0,'new_navigation_branches':0,'independent_confirmation_tasks':0,'previous_round_unchanged':True})
def stop(*_):raise RuntimeError('BOUNDARY_OR_USER_STOP')
signal.signal(signal.SIGTERM,stop)
try:
 window.frozen();dump(window.path/'ACTIVE.json',{'name':name,'diagnostic_control_replay':True})
 command=[str(repo/'run_phase.sh'),str(src.relative_to(repo)/'run_static.py'),'--name',name,'--seed','95000011','--scene','single_event','--conditions','geometry_memory','--wall-seconds','120','--max-steps','264','--controls-from',str(source.relative_to(repo))]
 code=window.execute(command,window.path/'diagnostic.console',125)
 complete=read(pair/'completion.json',{});result=(complete.get('results')or[None])[0]
 assert code==0 and result and result['outcome']=='DIAGNOSTIC_CONTROL_REPLAY_COMPLETE','DIAGNOSTIC_REPLAY_INCOMPLETE'
 replay_code=window.execute([str(repo/'run_phase.sh'),str(src.relative_to(repo)/'replay_native_audit.py'),str(pair)],window.path/'native_replay.console',35)
 integrity=window.execute(['python',str(repo/'experiments/v648_static_unknown/audit_results.py'),str(pair)],window.path/'integrity.console',15)
 native=read(pair/'NATIVE_REPLAY_AUDIT.json',{})
 checks={'diagnostic_return':code==0,'original_control_unchanged':digest(source)==read(window.path/'CONTROL_SOURCE_FREEZE.json')['sha256'],
         'integrity':integrity==0,'full_native_replay':replay_code==0 and native.get('status')=='MATCHED_RECORDED_PUBLIC_STATES'
            and max(native.get(k,1)for k in ['maximum_full_public_qpos_error','maximum_full_public_qvel_error','maximum_public_mocap_error'])<=1e-8,
         'native_count':native.get('replay_integration_steps')==result['physics_steps']==2112,
         'native_clearance':native.get('minimum_reconstructed_native_actual_axis_AABB_clearance_m',-1)>=.15,
         'self_coverage':native.get('minimum_reconstructed_self_domain_margin_m',-1)>=0 and result['self_geometry_checked_native_ticks']==2112,
         'no_obstacle_or_unknown_contact':native.get('replay_obstacle_contact_records')==native.get('replay_unknown_contact_records')==0,
         'same_physical_model':read(pair/'STATIC_PROTOCOL.json')['full_model_sha256']==read(source.parents[1]/'STATIC_PROTOCOL.json')['full_model_sha256'],
         'same_normalized_initial':result['normalized_initial_state_hash']==read(source.parent/'result.json')['normalized_initial_state_hash'],
         'root_only_native':result['root_mutations_outside_mjstep']==0,'frozen_sources':read(pair.parent/'source_snapshot/SHA256.json')==window.sources}
 window.frozen();dump(window.path/'DIAGNOSTIC_AUDIT.json',{'passed':all(checks.values()),'checks':checks,'native':native,'scope':'exact old-control replay, not a new online navigation success'})
 status='DIAGNOSTIC_CONTROL_REPLAY_PASS'if all(checks.values())else'DIAGNOSTIC_AUDIT_FAILED'
except BaseException as error:
 status='STOPPED_EXCEPTION';dump(window.path/'ERROR.json',{'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
finally:
 dump(window.path/'COMPLETION.json',{'status':status,'elapsed_s':time.monotonic()-window.started,'original_deadline_unix':window.unix+window.limit,'new_navigation_tasks':0,'training_updates':0,'round_budget_continues_for_separate_preregistered_repair':status=='DIAGNOSTIC_CONTROL_REPLAY_PASS'})
 dump(window.path/'ACTIVE.json',{'status':status,'completed':True});print(status,flush=True)
