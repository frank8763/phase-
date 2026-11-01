"""Execution-only audit repair; retain the old baseline and original deadline."""
import signal,time,traceback
from pathlib import Path
from bounded_execution import Window,read,dump,digest
src=Path(__file__).resolve().parent;repo=src.parents[1]
origin=read(repo/'runs/v658_dynamic_unknown/development01/WINDOW.json')
window=Window(src,'v661_dynamic_corridor_consistency','development04',3600,origin['absolute_deadline_unix'])
oldsrc=repo/'experiments/v659_dynamic_scene_repair'
base=repo/'runs/v659_dynamic_scene_repair/dev31_95000011_instant/paired'
outcomes=[];repeats=[];status='RECOVER_BASELINE_AUDIT'
def stop(*_):raise RuntimeError('BOUNDARY_OR_USER_STOP')
signal.signal(signal.SIGTERM,stop)
try:
 equality={p.name:p.read_bytes()==(oldsrc/p.name).read_bytes() for p in src.glob('*.py')
           if p.name not in ['run_static.py','motion_tracker.py','replay_native_audit.py','execute_development.py']}
 assert all(equality.values()),'UNDECLARED_ALGORITHM_CHANGE'
 dump(window.path/'UNCHANGED_MODULES.json',equality)
 code=window.execute([str(repo/'run_phase.sh'),str(src.relative_to(repo)/'replay_native_audit.py'),str(base)],
                     window.path/'baseline_supplemental_replay.console',35)
 audit=read(base/'NATIVE_REPLAY_AUDIT.json',{});result=read(base/'geometry_memory/result.json')
 oldfreeze=read(repo/'runs/v659_dynamic_scene_repair/development02/SOURCE_FREEZE.json')
 checks={'replay_exit':code==0,'full_state_match':audit.get('status')=='MATCHED_RECORDED_PUBLIC_STATES'
         and max(audit.get('maximum_full_public_qpos_error',1),audit.get('maximum_full_public_qvel_error',1),
                 audit.get('maximum_public_mocap_error',1))<=1e-8,
         'native_count':audit.get('replay_integration_steps')==result['physics_steps']==8*result['public_steps'],
         'native_clearance':audit.get('minimum_reconstructed_native_actual_axis_AABB_clearance_m',-1)>=.15
              and audit.get('reconstructed_native_states_below_015')==0,
         'contact_and_unknown_zero':audit.get('replay_obstacle_contact_records')==0 and audit.get('replay_unknown_contact_records')==0
              and all(result['contacts'][k]==0 for k in ['robot_obstacle_contact_records','robot_obstacle_penetration_records','unknown_contact_records']),
         'self_domain':audit.get('minimum_reconstructed_self_domain_margin_m',-1)>=0
              and result['self_geometry_checked_native_ticks']==result['physics_steps'],
         'same_saved_model':digest(base/'scene_model.mjb')==audit.get('scene_model_sha256')==read(base/'STATIC_PROTOCOL.json')['full_model_sha256'],
         'frozen_old_source':all(digest(oldsrc/n)==h for n,h in oldfreeze.items()),
         'original_integrity':read(repo/'runs/v659_dynamic_scene_repair/FINAL_PHYSICAL_AUDITS.json')[0]['checks']['integrity'],
         'no_root_mutation':result['root_mutations_outside_mjstep']==0}
 dump(window.path/'BASELINE_SUPPLEMENTAL_AUDIT.json',{'passed':all(checks.values()),'checks':checks,'native':audit,
      'original_failed_completion_retained':True,'navigation_result_unchanged':result})
 assert all(checks.values()),'SUPPLEMENTAL_BASELINE_PHYSICAL_AUDIT_FAILED'
 row=window.run('dev32_95000011_predictive',95000011,'single_event',mode='predictive')
 if row is None:status='NAVIGATION_BUDGET_INCOMPLETE'
 else:
  result=window.result(row);safe=window.audit(row)
  pair=window.root/row['name']/'paired'
  same={'model':read(base/'STATIC_PROTOCOL.json')['full_model_sha256']==read(pair/'STATIC_PROTOCOL.json')['full_model_sha256'],
        'normalized_initial_state':bool(result and result['normalized_initial_state_hash']==read(base/'geometry_memory/result.json')['normalized_initial_state_hash'])}
  a=read(base/'DYNAMIC_PROTOCOL.json');b=read(pair/'DYNAMIC_PROTOCOL.json')
  a.pop('swept_envelope_reference');b.pop('swept_envelope_reference');same['motion']=a==b
  dump(window.path/'PAIRING_AUDIT.json',{'passed':all(same.values()),'checks':same,'baseline_pair':str(base.relative_to(repo))})
  outcomes.append({'seed':95000011,'mode':'predictive','name':row['name'],'result':result,'physical_audit_passed':safe})
  dump(window.path/'RESULTS.json',outcomes)
  if not safe or not all(same.values()):status='STOPPED_PHYSICAL_OR_PAIRING_AUDIT'
  elif not result['strict_safe_arrival']:status='PREDICTIVE_NON_SUCCESS'
  else:
   repeat=window.run('dev32_95000011_predictive_repeat',95000011,'single_event',mode='predictive')
   if repeat is None:status='REPEAT_BUDGET_INCOMPLETE'
   else:
    record=window.repeat(repeat,pair);repeats.append(record);dump(window.path/'REPEAT_AUDIT.json',repeats)
    status='PREDICTIVE_REPEAT_MATCHED'if record['matched']else'PREDICTIVE_REPEAT_FAILED'
except BaseException as error:
 status='STOPPED_EXCEPTION';dump(window.path/'ERROR.json',{'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
finally:
 dump(window.path/'COMPLETION.json',{'status':status,'elapsed_s':time.monotonic()-window.started,'limit_s':window.limit,
      'original_absolute_deadline_unix':origin['absolute_deadline_unix'],'baseline_retained':str(base.relative_to(repo)),
      'new_navigation_branches':len(outcomes),'predictive_repeat_attempted':bool(repeats),
      'dynamic_stability_acceptance_passed':False,'training_updates':0,'scope':'single evidence-supported forecast-corridor development repair; old failures retained'})
 dump(window.path/'ACTIVE.json',{'status':status,'completed':True});print('DYNAMIC_DEVELOPMENT_COMPLETE',status,flush=True)
