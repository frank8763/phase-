"""Independent saved-native check of every newly admitted static transition."""
from campaign_context import *
def verify(task,events):
    out=Path(task['output']);segments=read(out/'DIRECT_SEGMENTS.json');setup=read(out/'physics/SETUP.json')
    with np.load(out/'physics/NATIVE_TRACE.npz')as z:t={k:z[k].copy()for k in z.files}
    proof=[]
    for e in events:
        seg=next(s for s in segments if s['path']==e['completed_plan']);p=read(R/e['completed_plan']);k=e['native'];packet=e['packet']
        rr=np.asarray(p['planned_body_requests']);assert seg['status']=='COMPLETE'and seg['executed_native']==len(rr)and seg['origin_native']+len(rr)==k
        assert p['source_kind']=='SAFE_PROGRESS_NOT_ARRIVAL'and p['functional_goal_source']is False and p['finite_progress_never_counts_as_arrival']is True
        assert p['checks']['full_200_stop']and all(p['checks'].values())and np.array_equal(rr[-200:],np.zeros((200,3)))
        assert packet['native_tick']==k and packet['dynamic_discovered']is False and e['counts_as_goal']is False and e['actual_sensor_discovery']is False
        qp=t['qpos'][k-1];qv=t['qvel'][k-1];yaw=math.atan2(2*(qp[3]*qp[6]+qp[4]*qp[5]),1-2*(qp[5]**2+qp[6]**2))
        assert abs(qp[:2]-packet['body'][:2]).max()<=1e-8 and abs(math.atan2(math.sin(yaw-packet['body'][2]),math.cos(yaw-packet['body'][2])))<=1e-8
        assert np.linalg.norm(qv[:2])<=.03 and abs(qv[5])<=.03 and abs(qv[setup['steering_qvel_addresses']]).max()<=.03
        assert abs(qp[setup['steering_qpos_addresses']]-packet['steering']['position']).max()<=1e-8
        controls=t['ctrl'][k-1,setup['actuator_ids']];assert abs(controls-packet['controller_memory']['last_ctrl']).max()<=1e-8 and abs(controls[-2:]).max()<=1e-8
        nextseg=next(s for s in segments if s['origin_native']==k and s['label'].startswith('STATIC_'))
        nxt=read(R/nextseg['path']);assert nxt['packet']==packet,'RENEWAL_NOT_FROM_ACTUAL_COMPLETE_PACKET'
        from fresh import finite_plan
        independent=finite_plan(setup,packet,None,nxt['planned_body_requests'],'INDEPENDENT_COMPLETE_STATIC_RENEWAL')
        assert independent['passed']and all(independent['checks'].values())
        assert np.asarray(independent['state_path']).shape==np.asarray(nxt['state_path']).shape and abs(np.asarray(independent['state_path'])-np.asarray(nxt['state_path'])).max()<=1e-8
        assert abs(np.asarray(independent['predicted_actuator_controls'])-np.asarray(nxt['predicted_actuator_controls'])).max()<=1e-8
        if 'static_reconnection'in nxt:
            rec=read(out/('STATIC_RECONNECTION_%02d.json'%int(nextseg['label'].split('_')[-1])))
            assert not rec['normal_refusal']['passed']and len(rec['fixed_records'])==10
            selected=next(a for a in rec['fixed_records']if a['passed']);assert rec['selected']==selected
            assert selected==nxt['static_reconnection']['record'],'FIXED_SELECTION_OR_BINDING_CHANGED'
        proof.append(dict(native=k,passed=True,static_stop_tail_required=200,new_goal_claimed=False,new_sensor_evidence_fabricated=False))
    return dict(passed=True,events=proof,models=0,new_mujoco_native=0)
