"""Zero-model independent closure readback for the one authorized RPP static run."""
import fcntl,hashlib,json,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];REC=R/'records/nav2_v863_execution_20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    class NoModels:
        def find_spec(self,fullname,*args):
            if fullname.split('.')[0]in {'mujoco','torch','rclpy','vehicle','factory'}:raise RuntimeError('NO_MODEL_OR_ROS_IMPORT')
    sys.meta_path.insert(0,NoModels())
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    checked={}
    for name in ['v862_ready_static','v863_rpp_preparation']:
        manifest=R/'experiments'/name/'SOURCE_FREEZE.json';files=read(manifest)['files']
        for p,h in files.items():assert sha(R/p)==h,p
        checked[name]=dict(files=len(files),manifest_sha256=sha(manifest))
    p=R/'runs/v858_nav2_verified/v863_rpp_static';result=read(p/'RESULT.json');audit=read(p/'INDEPENDENT_AUDIT.json');done=read(p/'COMPLETION.json');task=read(p/'TASK.json');auth=read(p/'AUTHORIZATION.json');setup=read(p/'physics/SETUP.json')
    assert done['closed']and done['status']=='PASSED'and done['guard_restored']and audit['passed']and not task['dynamic']
    assert done['closed_unix']<=auth['deadline_unix']==1794062038.6753576
    assert auth['one_navigation_only']and auth['no_dynamic_or_new24']and auth['source_freeze_sha256']==checked['v863_rpp_preparation']['manifest_sha256']
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    sys.path.insert(0,str(R/'experiments/v862_ready_static'));from audit_result import _audit
    original_audit_bytes=(p/'INDEPENDENT_AUDIT.json').read_bytes()
    try:independently_recomputed=_audit(task)
    finally:(p/'INDEPENDENT_AUDIT.json').write_bytes(original_audit_bytes)
    assert independently_recomputed['passed']and independently_recomputed==audit
    a=np.load(p/'physics/NATIVE_TRACE.npz');ids=setup['actuator_ids'];unused=[i for i in range(a['ctrl'].shape[1])if i not in ids]
    assert np.all(a['ctrl'][:,unused]==0)
    xy=np.vstack([np.asarray(setup['case']['start_xy']),a['qpos'][:,:2]]);delta=np.diff(xy,axis=0);yaw=np.arctan2(2*(a['qpos'][:,3]*a['qpos'][:,6]+a['qpos'][:,4]*a['qpos'][:,5]),1-2*(a['qpos'][:,5]**2+a['qpos'][:,6]**2));projection=np.sum(delta*np.c_[np.cos(yaw),np.sin(yaw)],axis=1)
    old=read(R/'runs/v858_nav2_verified/v862_ready_static/physics/SETUP.json');assert setup==old
    receipt=dict(passed=True,functional_passed=True,scope='ONE_DEVELOPMENT_STATIC_WEST_EAST_ONLY',source_readback=checked,original_v862_failed=True,same_complete_model_and_setup_as_v862=True,actual_native=len(a['time']),replay_native=result['replay_native'],mujoco_private_native=result['private_native'],new_dynamic_navigation=0,new24=0,full_navigation_repeats=0,goal_distance_m=audit['goal_distance_m'],minimum_clearance_m=audit['minimum_clearance_m'],bad_contacts=audit['bad_contacts'],all_state_control_mocap_replay_max_error=audit['maximum_state_error'],physical_sim_s=float(a['time'][-1]),ros_wall_s=result['ros_action']['wall_s'],actual_path_length_m=float(np.linalg.norm(delta,axis=1).sum()),forward_projection_m=float(np.maximum(projection,0).sum()),reverse_projection_m=float(np.maximum(-projection,0).sum()),all_unused_actuators_zero=True,independent_saved_evidence_audit=independently_recomputed,guard_original_sha_restored=True,execution_lock_idle=True,model_initializations_this_audit=0,model_integrations_this_audit=0,closed_unix=done['closed_unix'],verified_unix=time.time(),initialization_accounting='One environment initialization completed; explicit XML compile1; internal factory load/compile count not separately measured',no_dynamic_chain_claim=True)
    (REC/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    for f in ['RESULT.json','ROS_RESULT.json','INDEPENDENT_AUDIT.json','COMPLETION.json','TASK.json','AUTHORIZATION.json','CLAIM.json']:(REC/f).write_bytes((p/f).read_bytes())
    for f in ['PLUGIN_READY.json','ZERO_QUALIFICATION.json','PREPARATION_CONFIG_NOTE.json']:(REC/f).write_bytes((R/'runs/v863_rpp_preparation'/f).read_bytes())
    print(json.dumps({k:v for k,v in receipt.items()if k not in ['independent_saved_evidence_audit','source_readback']}))
if __name__=='__main__':main()
