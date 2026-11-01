"""Independent closed account and full vehicle/support identity, zero integrations."""
import os,json,hashlib
from pathlib import Path
import numpy as np
import mujoco
repo=Path(os.environ['PHASE_REPO']);src=repo/'experiments/v691_discovery_in_motion';root=repo/'runs/v691_discovery_in_motion';window=root/'development01'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ledger=read(root/'ROUND_WINDOW.json');assert ledger['round_closed'];rows=read(window/'RESULTS.json');tasks=[]
old=mujoco.MjModel.from_binary_path(str(repo/'runs/v690_visible_eight_meter/learned8m_train_task/paired/scene_model.mjb'));actor=mujoco.mj_name2id(old,mujoco.mjtObj.mjOBJ_BODY,'phase_dynamic_actor');body_ids=[i for i in range(old.nbody)if i!=actor]
for row in rows:
 pair=repo/row['run'];r=row['result'];checks={};vehicle={}
 if r is None:
  partial=read(pair/'geometry_memory/interrupted.json');checks={'original_failure_retained':read(pair/'completion.json')['status']=='FAILED'and row['runner_exit']!=0,'not_counted_as_arrival':partial['strict_safe_arrival']is False}
  if partial['public_steps']>0:checks['full_executed_prefix_replay']=read(pair/'NATIVE_REPLAY_AUDIT.json')['status']=='MATCHED_RECORDED_PUBLIC_STATES'
 else:
  replay=read(pair/'NATIVE_REPLAY_AUDIT.json');checks={'result_matches':r==read(pair/'geometry_memory/result.json'),'physical_audit':read(pair/'INDEPENDENT_CANONICAL_AUDIT.json')['status']=='ALL_PHYSICAL_STATE_COMMAND_CHECKS_PASS','route_audit':read(pair/'ROUTE_COMMITMENT_AUDIT.json')['status']=='PASS','projection_learning':read(pair/'PROJECTION_LEARNING_AUDIT.json')['status']=='PASS','all_original_tails':read(pair/'SAVED_TAIL_GEOMETRY_AUDIT.json')['status']=='ALL_SAVED_TAIL_GEOMETRY_DIRECTION_SCHEDULE_PASS','full_replay':replay['replay_integration_steps']==r['physics_steps']and max(replay[k]for k in ['maximum_full_public_qpos_error','maximum_full_public_qvel_error','maximum_public_mocap_error'])<=1e-8,'source_snapshot':read(pair.parent/'source_snapshot/SHA256.json')==read(window/'SOURCE_FREEZE.json')}
  chain=read(pair/'DISCOVERY_CHAIN_AUDIT.json');checks['functional_chain_status_consistent']=row.get('discovery_chain_audit_passed')==(chain['status']=='PASS')
  if 'repeat'in row['name']:checks['complete_exact_repeat']=read(pair/'EXACT_REPEAT_AUDIT.json')['passed']
  m=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));vehicle['dimensions']=(m.nq,m.nv,m.nu,m.nbody,m.nmocap)==(old.nq,old.nv,old.nu,old.nbody,old.nmocap)
  for k in ['body_pos','body_quat','body_mass','body_inertia','body_ipos','body_iquat']:vehicle[k]=np.array_equal(getattr(m,k)[body_ids],getattr(old,k)[body_ids])
  for k in ['qpos0','dof_damping','dof_frictionloss','dof_armature','actuator_gainprm','actuator_biasprm','actuator_forcerange','actuator_ctrlrange','jnt_range','jnt_limited']:vehicle[k]=np.array_equal(getattr(m,k),getattr(old,k))
  own=np.flatnonzero((m.geom_bodyid>0)&(m.geom_bodyid!=actor));prior=np.flatnonzero((old.geom_bodyid>0)&(old.geom_bodyid!=actor))
  for k in ['geom_type','geom_pos','geom_quat','geom_size','geom_friction','geom_solref','geom_solimp','geom_margin','geom_gap','geom_contype','geom_conaffinity','geom_bodyid']:vehicle['robot_'+k]=np.array_equal(getattr(m,k)[own],getattr(old,k)[prior])
  floor=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,'floor');of=mujoco.mj_name2id(old,mujoco.mjtObj.mjOBJ_GEOM,'floor')
  for k in ['geom_friction','geom_solref','geom_solimp','geom_type','geom_pos','geom_size']:vehicle['floor_'+k]=np.array_equal(getattr(m,k)[floor],getattr(old,k)[of])
  for k in ['timestep','integrator','solver','iterations','tolerance','cone','jacobian','gravity']:vehicle['opt_'+k]=np.array_equal(getattr(m.opt,k),getattr(old.opt,k))
  checks['complete_vehicle_support_unchanged']=all(vehicle.values())
 tasks.append({'name':row['name'],'checks':{k:bool(v)for k,v in checks.items()},'vehicle_checks':{k:bool(v)for k,v in vehicle.items()},'account_passed':bool(all(checks.values()))})
expected_gate=bool(len(rows)==2 and all(r['result']is not None and r['result']['strict_safe_arrival']and r.get('physical_audits_passed')and r.get('discovery_chain_audit_passed')for r in rows)and read(repo/rows[-1]['run']/'EXACT_REPEAT_AUDIT.json')['passed'])
checks={'all_account_evidence':all(t['account_passed']for t in tasks),'frozen_sources':all(sha(src/n)==h for n,h in read(window/'SOURCE_FREEZE.json').items()),'frozen_documents':all(sha(src/n)==h for n,h in read(window/'DOCUMENT_FREEZE.json').items()),'frozen_model':sha(repo/'runs/v690_visible_eight_meter/training_8m/proposer.json')==read(window/'MODEL_FREEZE.json')['sha256']=='fc9d3132c912033e2ec04cd8ae1ce236c818c484d5b96961c6f3dc1b0548b527','original3600deadline':abs(ledger['absolute_deadline_unix']-ledger['started_unix']-3600)<1e-6 and ledger['elapsed_s']<=3600,'bounded_attempts':ledger['navigation_attempts']==len(rows)<=2 and ledger['preflight_attempts']==1,'preflight_passed':read(root/'preflight/paired/INITIAL_UNSEEN_AUDIT.json')['status']=='PASS','zero_gradient_updates':ledger['supervised_gradient_updates']==ledger['sac_gradient_updates']==0,'gate_matches_actual':expected_gate==ledger['moving_discovery_gate_passed'],'old_v690_evidence_preserved':read(repo/'runs/v690_visible_eight_meter/FINAL_ACCOUNT_AUDIT.json')['status']=='FAIL'and read(repo/'runs/v690_visible_eight_meter/FINAL_ACCOUNT_AUDIT_V2.json')['status']=='ALL_FINAL_ACCOUNT_CHECKS_PASS'}
out={'status':'ALL_FINAL_ACCOUNT_CHECKS_PASS'if all(checks.values())else'FAIL','checks':checks,'tasks':tasks,'moving_discovery_gate_passed':expected_gate,'verification_integrations':0,'verification_gradient_updates':0,'scope':'finite discovery range-entry task with explicit startup clearing prior, no arbitrary unseen-space guarantee'}
(root/'FINAL_ACCOUNT_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'checks':checks,'tasks':len(tasks),'moving_discovery_gate_passed':expected_gate},indent=2));assert out['status']!='FAIL'
