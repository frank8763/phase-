"""Zero-model final closure: exact frozen-input readback and original saved failure gates."""
import fcntl,hashlib,json,os,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];REC=R/'records/nav2_v864_20261107';O=R/'runs/v864_rpp_static_regression'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 frozen=read(R/'experiments/v864_rpp_static_regression/SOURCE_FREEZE.json')
 for name,h in frozen['files'].items():assert sha(R/name)==h,name
 done=read(O/'COMPLETION.json');assert done['closed']and not done['passed']and done['attempted_items']==1 and done['unexecuted_items']==4
 assert done['actual_native']==3845 and done['replay_native']==3845 and done['guard_restored']
 p=R/'runs/v858_nav2_verified/v864_static/main_ns';audit=read(p/'INDEPENDENT_AUDIT.json');native=read(p/'RESULT.json');ros=read(p/'ROS_RESULT.json');assert audit['evidence_passed']and not audit['functional_passed'];assert ros['action_status']==6 and ros['action_error_code']==104
 assert native['bad_contacts']==0 and native['replay']['maximum_qpos_qvel_ctrl_mocap_error']==0 and native['replay']['contact_mismatched_ticks']==0
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 pid=read(O/'LAUNCH_PID.json')['pid']
 try:os.kill(pid,0)
 except ProcessLookupError:pass
 else:raise AssertionError('MASTER_STILL_EXISTS')
 for name in ['COMPLETION.json','ROUND_WINDOW.json','AUTHORIZATION.json','CLAIM.json','RESULTS.json','ZERO_QUALIFICATION.json','RESTORED_INPUTS.json','ERROR.json']:
  (REC/name).write_bytes((O/name).read_bytes())
 for name in ['RESULT.json','INDEPENDENT_AUDIT.json','ROS_RESULT.json','TASK.json']:(REC/('NS_'+name)).write_bytes((p/name).read_bytes())
 for name in ['SAVED_GEOMETRY.json','COLLISION_WITNESS.json','COLLISION_WITNESS.png','PLAYBACK01_ERROR.json']:(REC/name).write_bytes((R/'runs/v864_diagnosis'/name).read_bytes())
 playback=read(R/'runs/v864_diagnosis/pb02/PLAYBACK_COMPLETION.json');assert playback['model_integrations']==0 and playback['actuator_execution']==0 and not playback['actual_closed_loop_navigation']
 summary=dict(passed=True,audit_scope='Failed static regression record consistency; NOT navigation acceptance',functional_passed=False,original_frozen_input_files=len(frozen['files']),source_readback_all_passed=True,attempted_new_navigation=1,unexecuted_new_navigation=4,actual_native=3845,replay_native=3845,mujoco_private_native=0,environment_initializations_completed=1,explicit_xml_compiles=1,factory_internal_load_compile_count='NOT_SEPARATELY_INSTRUMENTED',model_initializations_this_audit=0,integrations_this_audit=0,old_v863_main_preserved_and_not_reexecuted=True,complete_navigation_repeats=0,new_dynamic_navigation=0,new24=0,training=0,real_robot=0,guard_original_restored=True,lock_idle=True,master_exited=True,stop='RPP_NO_VALID_CONTROL_COLLISION_AHEAD_NAV2_ABORT104',diagnosis_software_only_playbacks=2,diagnostic_first_playback_io_error_preserved=True,diagnostic_second_reproduced_nav2_abort104=True,no_physical_repair_or_retry=True,closed_unix=done['closed_unix'],verified_unix=time.time())
 (REC/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
