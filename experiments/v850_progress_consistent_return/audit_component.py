"""Read-only independent full component, control, coverage and physical evidence audit."""
import gzip,importlib.abc,json,sys
from pathlib import Path
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('COMPONENT_AUDIT_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
from common import R,W,ROOT,read,dump,unchanged
sys.path.insert(0,str(W))
import numpy as np
from types import SimpleNamespace
from progress_record_independent import check as check_progress
from reference_certificate_audit import independent_values
from motion_evaluator import check_forecast
from union_belief import future_cells


def main():
    unchanged();folder=ROOT/'component01';result=read(folder/'RESULT.json');assert result['status']=='FIXED_NATIVE_PROGRESS_COMPONENT_PASS'and result['passed']
    source=R/'runs/v848_goal_first_worker/v848_main_slot01/paired';cell=source/'geometry_memory';protocol=read(source/'STATIC_PROTOCOL.json');config=read(source/'DYNAMIC_PROTOCOL.json');limits=np.asarray(read(cell/'ACTUATOR_COMMAND_CONTRACT.json')['limits']);ids=read(cell/'ACTUATOR_COMMAND_CONTRACT.json')['ids'];rate=np.asarray([.1,.1,.7,.7])
    def load(p):
        with gzip.open(p,'rt')as stream:return json.load(stream)
    old=load(cell/'recovery_contracts/contract_0569.json.gz');oldnew=load(cell/'handover_certificates/handover_0573.json.gz');selected=read(folder/'SELECTED.json');expected=np.load(folder/'EXPECTED_BRANCH.npz');n=len(expected['controls'])
    assert len(expected['qpos'])==len(expected['qvel'])==n and n in [288,328]
    if selected['mode']=='RETAIN_OLD_BETTER_CERTIFICATE':
        assert n==288 and selected['selected']['old_cursor']==32
        assert np.array_equal(expected['controls'],np.asarray(old['controls'])[32:])and np.array_equal(expected['qpos'],np.asarray(old['qpos'])[32:])and np.array_equal(expected['qvel'],np.asarray(old['qvel'])[32:])
        c=old
    else:
        assert selected['mode']=='BETTER_FULL_PROGRESS_CERTIFICATE'and n==328
        c=load(folder/'handover_certificates/handover_0573.json.gz')
        check_progress(c,SimpleNamespace(qpos=expected['initial_qpos'],qvel=expected['initial_qvel'],time=float(expected['initial_time'])),old,32)
        assert np.array_equal(expected['controls'][8:],c['controls'])and np.array_equal(expected['qpos'][8:],c['qpos'])and np.array_equal(expected['qvel'][8:],c['qvel'])
    complete=np.vstack((c['prefix_poses'],np.c_[np.asarray(c['qpos'])[:,:2],np.arctan2(2*(np.asarray(c['qpos'])[:,3]*np.asarray(c['qpos'])[:,6]+np.asarray(c['qpos'])[:,4]*np.asarray(c['qpos'])[:,5]),1-2*(np.asarray(c['qpos'])[:,5]**2+np.asarray(c['qpos'])[:,6]**2))]))
    values=independent_values(complete,c['forecast_state'],protocol);assert len(values)==328 and values.min()>=.155 and abs(float(values.min())-c['minimum_causal_predicted_clearance_m'])<=1e-8
    commands=np.asarray(expected['controls']);assert (commands>=limits[:,0]-1e-12).all()and(commands<=limits[:,1]+1e-12).all()
    assert (abs(np.diff(np.vstack((expected['initial_ctrl'][ids],commands[::8])),axis=0))<=rate+1e-12).all()
    actual=load(folder/'ACTUAL_OBSERVATIONS.json.gz');repeat=load(folder/'REPEAT_OBSERVATIONS.json.gz');assert actual==repeat and len(actual)==n//8
    for item in actual:
        state=item['state'];coverage=check_forecast(config,state);assert coverage['passed']and coverage==item['execution329']
        times=np.arange(657)*.01;lo,hi=future_cells(state['outer_state_cells'],times);truth=np.asarray(config['anchor_xy'])+np.sin((state['time']+times)*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy'])
        excess=float(np.maximum(lo-truth[:,None,:],truth[:,None,:]-hi).max(axis=2).min(axis=1).max());assert excess<=1e-7 and abs(excess-item['planning657_excess_m'])<=1e-10
    aa=np.load(folder/'ACTUAL.npz');bb=np.load(folder/'REPEAT.npz');assert aa['integration'].shape==bb['integration'].shape and len(aa['integration'])==n
    repeat_error=float(np.max(abs(aa['integration']-bb['integration'])));assert repeat_error<=1e-8
    count={'OLD_REPLAY':0,'ACTUAL':0,'REPEAT':0};error=0.;minimum=1e30;bad=0
    with gzip.open(folder/'ACTUAL_NATIVE.jsonl.gz','rt')as stream,gzip.open(cell/'dynamic_native.jsonl.gz','rt')as original:
        for row in map(json.loads,stream):
            label=row['context'];i=count[label];count[label]+=1;minimum=min(minimum,row['clearance_m']);assert row['clearance_m']>=.15 and row['self_margin_m']>=0
            bad+=sum(c['contact_type']in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in row['contacts'])
            if label=='OLD_REPLAY':
                oldrow=json.loads(next(original));pairs=[('qpos','qpos_full'),('qvel','qvel_full'),('ctrl','actual_ctrl'),('mocap','mocap_pos')]
                error=max(error,max(float(np.max(abs(np.asarray(row[a])-oldrow[b])))for a,b in pairs))
            else:
                error=max(error,float(np.max(abs(np.asarray(row['qpos'])-expected['qpos'][i]))),float(np.max(abs(np.asarray(row['qvel'])-expected['qvel'][i]))),float(np.max(abs(np.asarray(row['ctrl'])[ids]-commands[i]))))
    assert error<=1e-8 and bad==0 and count==dict(OLD_REPLAY=4584,ACTUAL=n,REPEAT=n)
    assert result['counts']['old_replay_native']==4584 and result['counts']['actual_branch_native']==result['counts']['repeat_branch_native']==n
    assert result['maximum_native_state_error']<=1e-8 and result['maximum_full_integration_repeat_error']==repeat_error
    # Original calibrated selected return is still a negative-progress failure.
    goal=np.asarray(protocol['goal_xy']);assert np.linalg.norm(expected['initial_qpos'][:2]-goal)-np.linalg.norm(np.asarray(oldnew['qpos'])[-1,:2]-goal)<0
    assert np.linalg.norm(expected['initial_qpos'][:2]-goal)-np.linalg.norm(aa['qpos_end'][:2]-goal)>=.02 and np.linalg.norm(aa['qvel_end'][:2])<=.025
    result=dict(status='FIXED_PROGRESS_COMPONENT_INDEPENDENT_PASS',passed=True,mode=selected['mode'],counts=result['counts'],checks=dict(original4584replay=True,complete_selected_tail=True,controls_legal_slew=True,causal_full328geometry=True,execution329_planning657coverage=True,actual_safety=True,full_integration_repeat=True,complete_goal_progress=True,source_exact=True),minimum_actual_clearance_m=minimum,maximum_recorded_error=error,full_repeat_error=repeat_error,new_models=0,new_integrations=0,new_navigation=0,full_dynamic_or_realtime_passed=False)
    dump(folder/'INDEPENDENT_AUDIT.json',result);print(json.dumps(result))


if __name__=='__main__':main()
