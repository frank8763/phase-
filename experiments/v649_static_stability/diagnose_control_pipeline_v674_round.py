"""Raw admitted vs applied vs MuJoCo-clipped commands; no integration."""
import os,sys,json,gzip,hashlib
from pathlib import Path
import numpy as np
import mujoco
repo=Path(os.environ['PHASE_REPO']);read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]
records=[]
for folder,name in [('v674_dynamic_renewable_backup','dev41_95000011_renewable'),('v675_dynamic_joint_admission','dev42_95000011_jointadmission')]:
 root=repo/'runs'/folder/name/'paired';cell=root/'geometry_memory';m=mujoco.MjModel.from_binary_path(str(root/'scene_model.mjb'));limits=np.asarray(m.actuator_ctrlrange[:4]);execution=lines(cell/'v648_execution.jsonl');ad=lines(cell/'model_admission.jsonl');decisions=lines(cell/'control_decisions.jsonl');mismatches=[];normalized=0.;tested=0
 nom={x['step']:x for x in decisions if x['candidate_role']=='ORDINARY'and x['stage']=='NOMINAL'}
 contracts={}
 for f in(cell/'recovery_contracts').glob('*.gz'):
  with gzip.open(f,'rt')as stream:c=json.load(stream)
  contracts[c['created_step']]=c
 for admit in ad:
  step=admit['step'];actual=np.asarray(execution[step]['ctrl'][:4]);kind=admit['status']
  if kind=='RETAINED_REVERSE_BRAKE_CONTRACT':c=contracts[admit['retained_from_step']];raw=np.asarray(c['controls'][admit['contract_native_cursor']])
  elif admit.get('certified_backup_handover'):
   with gzip.open(cell/'handover_certificates'/admit['recovery_reserve']['handover_certificate'],'rt')as stream:c=json.load(stream)
   raw=np.asarray(c['first_command'])
  elif kind=='MODEL_SAFE_COMMAND':
   ranked=sorted([x for x in nom[step]['candidates']if x['reason']is None],key=lambda x:x['score'],reverse=True);unique=[];seen=set()
   for x in ranked:
    key=tuple(x['first_command'])
    if key not in seen:seen.add(key);unique.append(x)
   raw=np.asarray(unique[admit.get('joint_admission_distinct_command_rank',0)]['first_command'])
  else:raise RuntimeError('UNCLASSIFIED_ADMISSION_'+kind)
  clipped=np.clip(raw,limits[:,0],limits[:,1]);error=float(np.max(abs(actual-raw)));effective=float(np.max(abs(actual-clipped)));normalized=max(normalized,effective);tested+=1
  if error>1e-10:mismatches.append({'step':step,'mode':kind,'raw_admitted_command':raw.tolist(),'actual_applied_command':actual.tolist(),'maximum_raw_difference':error,'after_declared_actuator_clipping_difference':effective})
 commands=np.asarray([x['ctrl'][:4]for x in execution]);delta=np.diff(np.vstack((np.zeros(4),commands)),axis=0);clamp_disabled=bool(m.opt.disableflags&int(mujoco.mjtDisableBit.mjDSBL_CLAMPCTRL))
 records.append({'run':str(root.relative_to(repo)),'checked_public_commands':tested,'raw_mismatches':mismatches,'raw_mismatch_public_steps':len(mismatches),'maximum_after_clipping_command_error':normalized,'actual_steering_max_slew':float(np.max(abs(delta[:,:2]))),'actual_rear_wheel_max_slew':float(np.max(abs(delta[:,2:]))),'ctrl_limits':limits.tolist(),'all_four_actuators_ctrllimited':bool(np.all(m.actuator_ctrllimited[:4])),'model_internal_clamp_disabled':clamp_disabled,'model_sha256':hashlib.sha256((root/'scene_model.mjb').read_bytes()).hexdigest(),'scope':'clipping explains observed state equality only; does not change or pass original raw-control audit'})
result={'status':'RAW_COMMAND_CONTRACT_FAILURE_CONFIRMED','records':records,'simulation_integrations':0,'new_navigation_tasks':0,'original_independent_audit_modified':False,'original_completions_modified':False,'cause':'Recorded nominal/retained commands and last_command use pre-actuator-clipping values; direct_control writes clipped values. MuJoCo internal actuator clamp can yield identical physical states despite different raw ctrl arrays.','detection':'Post-navigation independent audit; online qpos/qvel match checks did not compare applied ctrl, so original navigation continued past first mismatch. No claim of immediate detection at that earlier step.','required_next_change_not_implemented':'Use one actuator-legal command mapping before score/prediction/reserve/control logs and compare applied ctrl online; preserve original failed records, do not retroactively normalize to call acceptance PASS.'}
out=repo/'runs/v674_dynamic_renewable_backup/CONTROL_PIPELINE_DIAGNOSIS.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
