from campaign_context import *
import fcntl
def audit(task,result_override=None,output_path=None):
    out=Path(task['output']);r=result_override if result_override is not None else read(out/'RESULT.json');assert r['passed']and r['models']==1 and r['new_actual_native']==0 and r['error']is None
    scene=load('v1235_saved_t0_contract',R/'experiments/v1089_route_scene_contract/contract.py');proof=scene.verify_saved(out/'physics',task)
    setup=read(out/'physics/SETUP.json');p=r['canonical_initial_packet'];assert p['native_tick']==0 and p['sim_time']==0. and not p['dynamic_discovered']and previous.stopped(p)
    assert abs(np.array(p['body'][:2])-task['start_xy']).max()<=1e-8
    with np.load(out/'physics/INITIAL_STATE.npz')as z:assert np.isfinite(z['state']).all()and z['state'][0]==0.
    if result_override is None:
        safety=r['initial_safety'];assert safety['minimum_actual_clearance_m']>=.15-1e-8 and safety['minimum_self_margin_m']>=-1e-10 and safety['bad_contacts']==0
        assert all(c[2]not in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact']for c in read(out/'INITIAL_CONTACTS.json'))
        scan=read(out/'INITIAL_SENSOR.json');assert scan['native_tick']==0 and scan['time']==0. and len(scan['ranges'])==32
    proof.update(passed=True,models=0,new_mujoco_native=0,scope='saved actual t0 scene hash/compiled array contract and canonical clock')
    dump(output_path or out/'FINAL_INDEPENDENT_AUDIT.json',proof);return proof
if __name__=='__main__':
    f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);print(json.dumps(audit(read(Path(sys.argv[1])))))
