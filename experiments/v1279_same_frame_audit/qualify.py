"""Supplement the original main, preserving all its failed batch bytes."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('SAVED_AUDIT_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];OUT=R/'runs'/C.name
sys.path.insert(0,str(R/'experiments/v1278_static_partial_reconnection'))
from campaign_context import *
import copy,fcntl
def main():
    f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    parent=R/'runs/v1278_static_partial_reconnection';manifest=read(parent/'LOCAL_MANIFEST.json')['files']
    assert read(parent/'FINALIZED.json')['manifest_readback']and all(sha(R/n)==v['sha256']and(R/n).stat().st_size==v['bytes']for n,v in manifest.items())
    raw=R/'runs/v858_nav2_verified/v1278/slot24_main';events=read(raw/'PARTIAL_STATIC_RENEWALS.json');task=read(R/'experiments/v1278_static_partial_reconnection/TASK_slot24_main.json')
    original=load('phase_v1279_original_transition',R/'experiments/v1278_static_partial_reconnection/transition_audit.py')
    try:original.verify(task,events)
    except AssertionError as exc:assert str(exc)=='RENEWAL_NOT_FROM_ACTUAL_COMPLETE_PACKET'
    else:raise AssertionError('ORIGINAL_REJECTION_NOT_REPRODUCED')
    fixed=load('phase_v1279_same_tick_transition',__import__('pathlib').Path(__file__).resolve().parent/'transition_audit.py')
    segments=read(raw/'DIRECT_SEGMENTS.json');e=events[0];s=next(s for s in segments if s['origin_native']==e['native']and s['label'].startswith('STATIC_'));b=read(R/s['path'])['packet'];a=e['packet']
    delta=fixed.same_frame_packet(a,b);negative=[]
    for label in ['body','native_tick','sim_time','steering','control','discovery','clock_skew','old_clock','stale_clock']:
        bb=copy.deepcopy(b)
        if label=='body':bb['body'][0]+=.001
        elif label=='native_tick':bb['native_tick']+=1
        elif label=='sim_time':bb['sim_time']+=.01
        elif label=='steering':bb['steering']['position'][0]+=.001
        elif label=='control':bb['controller_memory']['last_ctrl'][0]+=.001
        elif label=='discovery':bb['dynamic_discovered']=True
        elif label=='clock_skew':bb['sent_at']+=.001
        else:
            t=a['sent_at']+(-.001 if label=='old_clock'else .051)
            bb['sent_at']=bb['body_measured_at']=bb['steering']['measured_at']=t
        try:fixed.same_frame_packet(a,bb)
        except AssertionError:negative.append(label)
        else:raise AssertionError('PACKET_TAMPER_ACCEPTED '+label)
    supplement=fixed.verify(task,events);assert supplement['passed']
    r=read(raw/'RESULT.json');audit=read(raw/'FINAL_INDEPENDENT_AUDIT.json')
    assert r['passed']and r['error']is None and r['new_actual_native']==r['own_replay_native']==audit['native_reviewed']==56361
    assert r['replay']['passed']and r['replay']['maximum_qpos_qvel_ctrl_mocap_error']==0 and audit['passed']and audit['physical_audit_complete']
    assert all(sha(R/n)==v['sha256']for n,v in manifest.items()),'ORIGINAL_MEMBER_MUTATED'
    proof=dict(passed=True,parent_original_NOT_PASSED_preserved=True,main_functional_passed=True,main_whole_replay_passed=True,
        original_EW_full_audit_passed=True,supplemental_transition=supplement,interface_clock_delta_s=delta,
        state_and_control_fields_exact=True,negative_rejections=negative,original_archived_members_readback=len(manifest),
        original_evidence_unchanged=True,models=0,physical_native=0,analytical_python_native=len(read(R/s['path'])['planned_body_requests']),
        complete_repeat_executed=False,CLI_exit0_qualification=True)
    dump(OUT/'QUALIFICATION.json',proof);print((OUT/'QUALIFICATION.json').read_text())
if __name__=='__main__':main()
