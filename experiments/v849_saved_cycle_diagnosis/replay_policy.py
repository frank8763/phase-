"""Minimal replay of the actual recovery-supervisor policy with already-certified saved outcomes.

The predictor and certificate provider return saved V848 records. No model is
constructed, advanced or claimed to have been newly validated by this replay.
"""
import argparse
import copy
import gzip
import importlib.abc
import json
import os
from pathlib import Path
import signal
import sys
from types import SimpleNamespace


class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):
            raise RuntimeError('SAVED_POLICY_REPLAY_FORBIDS_MODELS')


sys.meta_path.insert(0,NoModels())
import numpy as np
R=Path(__file__).resolve().parents[2]
W=R/'experiments/v848_goal_first_worker'
CELL=R/'runs/v848_goal_first_worker/v848_main_slot01/paired/geometry_memory'
sys.path.insert(0,str(W))
from recovery_supervisor import RecoverySupervisor


def main():
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SAVED_POLICY_180S_CAP')));signal.alarm(180)
    p=argparse.ArgumentParser();p.add_argument('--assert-progress-consistency',action='store_true');a=p.parse_args()
    read=lambda p:json.loads(p.read_text())
    with gzip.open(CELL/'recovery_contracts/contract_0569.json.gz','rt')as stream:old=json.load(stream)
    with gzip.open(CELL/'handover_certificates/handover_0573.json.gz','rt')as stream:new=json.load(stream)
    protocol=read(CELL.parent/'STATIC_PROTOCOL.json');goal=np.asarray(protocol['goal_xy'])
    execution={r['step']:r for r in map(json.loads,(CELL/'v648_execution.jsonl').open())}
    ad=next(r for r in map(json.loads,(CELL/'model_admission.jsonl').open())if r['step']==573)
    route=next(r for r in map(json.loads,(CELL/'route_revalidation.jsonl').open())if r['step']==569)
    nominal=detail=None
    for row in map(json.loads,(CELL/'control_decisions.jsonl').open()):
        if row['step']!=573 or row.get('candidate_role')!='BACKUP_RETURN':continue
        if row['stage']=='NOMINAL':nominal=row
        if row['stage']=='BACKUP_APPEND':detail=row['detail']
    assert nominal is not None and detail is not None
    safe=sorted([c for c in nominal['candidates']if c['reason']is None],key=lambda c:c['score'],reverse=True)
    ranked=[]
    for c in safe:
        z=np.load(CELL/'nominal_forecasts'/c['nominal_saved_forecast'])
        ranked.append((c['score'],np.asarray(c['first_command']),z['poses'],c['minimum_clearance_m'],c['self_domain_margin_m']))
    assert np.array_equal(ranked[0][1],new['first_command'])and new['metadata']['return_nominal_rank']==0
    q=np.asarray(new['real_entry_qpos']);v=np.asarray(new['real_entry_qvel']);ctrl=np.asarray(execution[572]['ctrl'])
    real=SimpleNamespace(qpos=q,qvel=v,ctrl=ctrl,time=new['real_entry_time'])
    yaw=np.arctan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));current=np.r_[q[:2],yaw]
    env=SimpleNamespace(data=real,goal_xy=goal,inner=SimpleNamespace(wheel_base=.60,max_steer=.52))
    class SavedPredictor:
        prediction_steps=0
        ranked_safe_candidates=ranked
        last_diagnostics=nominal['candidates']
        def select(self,*args,**kwargs):return ranked[0][1].copy(),copy.deepcopy(nominal['summary'])
    class SavedCertificateProvider:
        cache=old;cursor=new['old_native_cursor']
        last_handover_attempt=detail
        def check_current_contract(self,state):
            error=max(float(np.max(abs(state.qpos-np.asarray(old['qpos'])[self.cursor-1]))),float(np.max(abs(state.qvel-np.asarray(old['qvel'])[self.cursor-1]))))
            assert error<=1e-8
            return 0.,0.
        def set_reference(self,*args):pass
        def try_handover(self,state,command,field,motion,step,metadata,commit):
            assert step==573 and commit and np.array_equal(command,new['first_command'])
            assert abs(metadata['predicted_goal_progress_m']-new['metadata']['predicted_goal_progress_m'])<=1e-10
            return copy.deepcopy(ad['recovery_reserve'])
    out=R/'runs/v849_saved_cycle_diagnosis/replay_policy';out.mkdir(parents=True,exist_ok=True)
    supervisor=RecoverySupervisor(out);supervisor.remember(np.asarray(route['reference_path']),route['index'],569)
    os.environ['PHASE_RECOVERY_ABLATION']='FULL'
    returned=supervisor.try_return(env,SimpleNamespace(),SimpleNamespace(),SavedCertificateProvider(),SavedPredictor(),current,ctrl[[0,1,2,3]],573)
    before=float(np.linalg.norm(q[:2]-goal));old_gain=before-float(np.linalg.norm(np.asarray(old['qpos'])[-1,:2]-goal));new_gain=before-float(np.linalg.norm(np.asarray(new['qpos'])[-1,:2]-goal))
    result=dict(actual_supervisor_returned=returned is not None,nominal_predicted_goal_gain_m=new['metadata']['predicted_goal_progress_m'],old_remaining_certificate_goal_gain_m=old_gain,new_complete_certificate_goal_gain_m=new_gain,
        state_join_exact=True,old_and_new_certificates_previously_physically_audited=True,
        desired_progress_consistency=new_gain>=.02 and new_gain>=old_gain-1e-8,
        new_physics_models=0,new_integrations=0,saved_provider_stubs_do_not_revalidate_physics=True)
    assert result['actual_supervisor_returned']and old_gain>0 and new_gain<0
    (out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    if a.assert_progress_consistency:assert not result['actual_supervisor_returned']or result['desired_progress_consistency'],'ACTUAL_RETURN_POLICY_ACCEPTS_GOAL_REGRESSING_CERTIFICATE'


if __name__=='__main__':main()
