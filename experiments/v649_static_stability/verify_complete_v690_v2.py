"""V2 audit: registered warm-start conversion; original failed V1 immutable."""
import os,sys,json,hashlib,copy
from pathlib import Path
import numpy as np
import mujoco
repo=Path(os.environ['PHASE_REPO']);src=repo/'experiments/v690_visible_eight_meter';root=repo/'runs/v690_visible_eight_meter';window=root/'curriculum01'
sys.path.insert(0,str(src))
from learned_proposer import Proposer
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]
ledger=read(root/'ROUND_WINDOW.json');assert ledger['round_closed']
rows=read(window/'RESULTS.json');tasks=[]
old=mujoco.MjModel.from_binary_path(str(repo/'runs/v689_dynamic_route_commitment/learned6m_train_task/paired/scene_model.mjb'))
actor=mujoco.mj_name2id(old,mujoco.mjtObj.mjOBJ_BODY,'phase_dynamic_actor');body_ids=[i for i in range(old.nbody)if i!=actor]
for row in rows:
 pair=repo/row['run'];r=row['result'];checks={'saved_result_matches':r==read(pair/'geometry_memory/result.json'),'successful_process':row['runner_exit']==0,'initial_observation_audit':read(pair/'INITIAL_VISIBILITY_AUDIT.json')['status']=='PASS'}
 replay=read(pair/'NATIVE_REPLAY_AUDIT.json');a=read(pair/'INDEPENDENT_CANONICAL_AUDIT.json');learn=read(pair/'PROJECTION_LEARNING_AUDIT.json')
 checks.update(physical_command_audit=a['status']=='ALL_PHYSICAL_STATE_COMMAND_CHECKS_PASS',causal_projection_learning=learn['status']=='PASS',route_audit=read(pair/'ROUTE_COMMITMENT_AUDIT.json')['status']=='PASS',tail_audit=read(pair/'SAVED_TAIL_GEOMETRY_AUDIT.json')['status']=='ALL_SAVED_TAIL_GEOMETRY_DIRECTION_SCHEDULE_PASS',full_replay=replay['replay_integration_steps']==r['physics_steps']and max(replay[k]for k in ['maximum_full_public_qpos_error','maximum_full_public_qvel_error','maximum_public_mocap_error'])<=1e-8,source_snapshot=read(pair.parent/'source_snapshot/SHA256.json')==read(window/'SOURCE_FREEZE.json'))
 m=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));vehicle={'dimensions':(m.nq,m.nv,m.nu,m.nbody,m.nmocap)==(old.nq,old.nv,old.nu,old.nbody,old.nmocap)}
 for k in ['body_pos','body_quat','body_mass','body_inertia','body_ipos','body_iquat']:vehicle[k]=np.array_equal(getattr(m,k)[body_ids],getattr(old,k)[body_ids])
 for k in ['qpos0','dof_damping','dof_frictionloss','dof_armature','actuator_gainprm','actuator_biasprm','actuator_forcerange','actuator_ctrlrange','jnt_range','jnt_limited']:vehicle[k]=np.array_equal(getattr(m,k),getattr(old,k))
 own=np.flatnonzero((m.geom_bodyid>0)&(m.geom_bodyid!=actor));prior=np.flatnonzero((old.geom_bodyid>0)&(old.geom_bodyid!=actor));vehicle['robot_attachment']=np.array_equal(m.geom_bodyid[own],old.geom_bodyid[prior])
 for k in ['geom_type','geom_pos','geom_quat','geom_size','geom_friction','geom_solref','geom_solimp','geom_margin','geom_gap','geom_contype','geom_conaffinity']:vehicle['robot_'+k]=np.array_equal(getattr(m,k)[own],getattr(old,k)[prior])
 floor=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,'floor');priorfloor=mujoco.mj_name2id(old,mujoco.mjtObj.mjOBJ_GEOM,'floor')
 for k in ['geom_friction','geom_solref','geom_solimp','geom_type','geom_pos','geom_size']:vehicle['floor_'+k]=np.array_equal(getattr(m,k)[floor],getattr(old,k)[priorfloor])
 for k in ['timestep','integrator','solver','iterations','tolerance','cone','jacobian','gravity']:vehicle['opt_'+k]=np.array_equal(getattr(m.opt,k),getattr(old.opt,k))
 checks['unchanged_full_vehicle_support']=all(vehicle.values())
 if row['model'] is not None:checks['actual_learned_participation']=learn['learned_actual_ordinary_steps']>0
 if 'repeat'in row['name']:checks['full_exact_repeat']=read(pair/'EXACT_REPEAT_AUDIT.json')['passed']
 tasks.append({'name':row['name'],'checks':checks,'vehicle_checks':{k:bool(v)for k,v in vehicle.items()},'passed':all(checks.values())})
preflight=[]
for name in ['preflight8m_phase0','preflight8m_phase_pi2']:
 p=root/name/'paired';v=read(p/'INITIAL_VISIBILITY_AUDIT.json');f=read(p/'TASK_FEASIBILITY.json');c=read(p/'DYNAMIC_PROTOCOL.json')
 preflight.append({'name':name,'passed':v['status']=='PASS'and f['eligible']and c['swept_envelope_reference']['eligible']and c['protected_junction_clearance_of_sweep_m']>=.05})
training=list(root.glob('training_*/TRAINING.json'));updates=sum(read(p)['gradient_updates']for p in training);training_checks={}
if training:
 t=read(training[0]);teacher=repo/'runs/v690_visible_eight_meter/teacher8m/paired';sample=teacher/'geometry_memory/proposal_learning_samples.jsonl';ss=lines(sample);nom={d['step']:d for d in lines(teacher/'geometry_memory/control_decisions.jsonl')if d['stage']=='NOMINAL'};ad=lines(teacher/'geometry_memory/model_admission.jsonl');contract=read(teacher/'geometry_memory/ACTUATOR_COMMAND_CONTRACT.json');limits=np.asarray(contract['limits']);m=Proposer(training[0].parent/'proposer.json');initial=Proposer(repo/'runs/v688_dynamic_distance_curriculum/training_6m/proposer.json')
 provenance=[]
 for s in ss:
  chosen=[c for c in nom[s['step']]['candidates']if c['reason']is None and c['features']==s['features']and c['proposal_role']==s['selected_role']and abs(c['score']-ad[s['step']]['score'])<=1e-10 and np.array_equal(np.clip(c['target_command'],limits[:,0],limits[:,1]),s['target'])]
  provenance.append(bool(chosen))
 x=np.asarray([s['features']for s in ss]);y=np.asarray([s['target']for s in ss])/[.52,.52,20,20]
 rounded_initial=copy.deepcopy(initial)
 for layer in rounded_initial.parameters['layers']:
  for key in ['weight','bias']:layer[key]=np.asarray(layer[key],dtype=np.float32).astype(np.float64).tolist()
 precision=read(root/'INITIALIZATION_PRECISION_DIAGNOSIS.json')
 mse=lambda model:float(np.mean((np.asarray([model.predict(z)for z in x])/[.52,.52,20,20]-y)**2))
 frozen=read(window/'EVALUATION_MODEL_FREEZE.json')
 training_checks={'actual_registered_loader_precision':precision['status']=='FROZEN_WARM_START_FLOAT32_CONVERSION_EXPLAINS_DIFFERENCE'and precision['source_sha256']==sha(src/'train_proposer.py'),'original_v1_fail_preserved':read(root/'FINAL_ACCOUNT_AUDIT.json')['status']=='FAIL','exact512_updates':updates==512==t['gradient_updates'],'actual_teacher_label_provenance':all(provenance),'teacher_full_pass':read(teacher/'geometry_memory/result.json')['strict_safe_arrival']and read(teacher/'INDEPENDENT_CANONICAL_AUDIT.json')['status']=='ALL_PHYSICAL_STATE_COMMAND_CHECKS_PASS','sample_hash':sha(sample)==t['source_sample_sha256']==m.parameters['teacher_sample_sha256'],'sample_count':len(ss)==t['samples'],'frozen_model_hash':m.sha256==t['model_sha256']==frozen['sha256'],'initial_normalization_preserved':np.array_equal(initial.mean,m.mean)and np.array_equal(initial.std,m.std),'independent_initial_mse':abs(mse(rounded_initial)-t['initial_mse'])<=1e-12,'independent_final_mse':abs(mse(m)-t['final_mse'])<=1e-12,'loss_decreased':t['final_mse']<t['initial_mse'],'no_physics_or_sac_in_fitting':t['integrations']==t['sac_updates']==0}
expected_gate=len(rows)==4 and all(x['passed']for x in tasks)and all(r['result']['strict_safe_arrival']for r in rows)and all(training_checks.values())and bool(training_checks)
checks={'all_task_evidence':all(x['passed']for x in tasks),'both_registered_preflights':all(x['passed']for x in preflight),'frozen_sources':all(sha(src/n)==v for n,v in read(window/'SOURCE_FREEZE.json').items()),'frozen_documents':all(sha(src/n)==v for n,v in read(window/'DOCUMENT_FREEZE.json').items()),'attempts_within_caps':ledger['navigation_attempts']==len(rows)<=4 and ledger['preflight_attempts']==2,'original5400deadline':abs(ledger['absolute_deadline_unix']-ledger['started_unix']-5400)<1e-6 and ledger['elapsed_s']<=5400,'update_accounting':updates==ledger['supervised_gradient_updates']<=512,'training_provenance':all(training_checks.values()),'actual_gate_matches_record':bool(expected_gate)==ledger['eight_meter_gate_passed'],'old6mcheckpoint_unchanged':sha(repo/'runs/v688_dynamic_distance_curriculum/training_6m/proposer.json')=='c77b5f833fe77d3cadbab9fb41835426a058249728eee94a0cf8e92aa88796c0','old8mfailure_retained':read(repo/'runs/v689_dynamic_route_commitment/teacher8m/paired/completion.json')['status']=='FAILED','sac_updates_zero':ledger['sac_gradient_updates']==0}
out={'status':'ALL_FINAL_ACCOUNT_CHECKS_PASS'if all(checks.values())else'FAIL','checks':checks,'tasks':tasks,'preflights':preflight,'training_checks':training_checks,'eight_meter_gate_passed':bool(expected_gate),'audit_version':2,'original_failed_audit':'FINAL_ACCOUNT_AUDIT.json','original_failed_audit_sha256':sha(root/'FINAL_ACCOUNT_AUDIT.json'),'precision_diagnosis':'INITIALIZATION_PRECISION_DIAGNOSIS.json','initialization_precision':'registered loader torch.tensor(list) uses float32 before copying into float64 network; reconstructed exactly, no source/model/control/safety modification','verification_integrations':0,'verification_gradient_updates':0,'scope':'finite initially-visible development course, not invisible8m exploration/originalfield/statistical dynamic acceptance'}
(root/'FINAL_ACCOUNT_AUDIT_V2.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'checks':checks,'training_checks':training_checks,'tasks':len(tasks)},indent=2));assert out['status']!='FAIL'
