"""Zero-model archival preparation for closed response and saved continuation."""
import sys,json,hashlib,fcntl,shutil,time,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1077_v1078_closure';D=R/'records/nav2_v1077_v1078_20261112'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,allow_nan=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 a=json.loads((R/'runs/v1077_speed125_response/COMPLETION.json').read_text());b=json.loads((R/'runs/v1078_saved_ns_retimed/COMPLETION.json').read_text());assert a['closed']and b['closed'];assert json.loads((R/'runs/v1077_speed125_response/ACTIVE.json').read_text())['closed']and json.loads((R/'runs/v1078_saved_ns_retimed/ACTIVE.json').read_text())['closed'];lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';O.mkdir(exist_ok=True);D.mkdir(exist_ok=True);arc=load('v1077_closed_archive',R/'experiments/v1065_preflight_metadata_continuation/archive.py');files=[];models=[]
 for version in ['v1077','v1078']:
  root=R/'runs/v858_nav2_verified'/version
  for p in arc.walk(root):
   if any(x in p.relative_to(root).parts for x in ['cache','frozen_original']):continue
   if p.name=='scene_model.mjb':models.append(dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size,prior_release='phase-causal-recovery-v1067-20261112',prior_member='runs/v858_nav2_verified/v1067/A_main_north_south/physics/scene_model.mjb'));continue
   files.append(p)
 for version in ['v1077_speed125_response','v1078_saved_ns_retimed','v1079_dual_steering_qualification']:
  root=R/'runs'/version
  for p in root.iterdir():
   if not p.is_file()or p.suffix not in ['.json','.console','.npz','.bin']or p.name=='ARCHIVE_INVENTORY.json':continue
   files.append(p)
  for name in ['COMPLETION.json','QUALIFICATION.json','ROUND_WINDOW.json','ENTRY_QUALIFICATION.json','RESPONSE_MODEL_QUALIFICATION.json','FINAL_INDEPENDENT_AUDIT.json','FAILED_COMPONENT_INDEPENDENT_AUDIT.json','COMPLETE_GOAL_QUALIFICATION.json','NEXT_TRANSITION_PREFLIGHT.json','RESTORED_NS.json','TRANSPORT_TRUNCATION.json']:
   p=root/name
   if p.is_file():q=D/version/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
 for row in models:assert row['sha256']=='412f0616d1160dad61bb395919d9442372108ad094e07a5122274df5b29201f8'
 dump(D/'MODEL_RESTORE.json',dict(models=models,prior_record='records/nav2_v1067_20261112/REMOTE_VERIFIED.json',identical_models_not_duplicated=True));record,inventory=arc.package(R,files,O/'cloud','v1077-v1078-speed125-evidence');dump(D/'RECORD_INDEX.json',dict(repository='frank8763/phase-',release_tag='phase-speed125-v1077-v1078-20261112',archives=[record]));summary=dict(response_5_passed=a['passed'],saved_continuation_passed=b['passed'],saved_component_not_new_main=True,new_fresh_whole_route_passed=False,new24_executed=False,response_counts=a['counts'],continuation_counts={k:b.get(k)for k in ['vehicle_initializations','historical_replay_native','recovery_native','own_replay_native','private_mujoco_native','replay_state_initializations','training_updates']},goal_distance=b.get('actual_goal_distance',b.get('physical',{}).get('goal_distance_m')),continuation_net_m=b.get('actual_continuation_net_m'),local_tracking=b.get('maximum_local_tracking'),physical=b.get('physical'),replay=b.get('replay'),error=b.get('error'),guard_original=True,execution_lock_idle=True,same_root=b['same_absolute_and_monotonic_root'],high_speed_model_fit_tasks=['response_01','response_03'],high_speed_held_out_tasks=['response_02','response_04','response_05'],calibrated_speed_system_id_coefficients=2,dual_steering_zero_model_qualified=json.loads((R/'runs/v1079_dual_steering_qualification/QUALIFICATION.json').read_text())['passed'],dual_steering_actual_not_run=True,sac_updates=0,hardware_steps=0);dump(D/'FINAL_SUMMARY.json',summary);dump(D/'FINALIZED.json',dict(response_independent_audits_passed=a['passed'],saved_component_independent_audit_passed=b.get('independent_audit_passed',False),archive_all_source_and_decompressed_members_sha_verified=True,archive_part_reassembly_sha_verified=True,source_members=len(inventory),models=0,remote_delivery_pending=True));dump(O/'INVENTORY.json',dict(files=inventory));print(json.dumps(dict(prepared=True,source_members=len(inventory),archive_bytes=record['archive_bytes'],saved_continuation_passed=b['passed'])),flush=True)
if __name__=='__main__':main()
