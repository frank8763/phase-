"""New policy against fixed V848 evidence; all physics/model imports forbidden.

This is a saved-certificate decision test, not a new search, safety evaluation,
counterfactual vehicle trajectory, or proof of future three-route arrival.
"""
import copy
import gzip
import hashlib
import importlib.abc
import json
from pathlib import Path
import signal
import sys
from types import SimpleNamespace


class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):
            raise RuntimeError('V850_SAVED_QUALIFICATION_FORBIDS_MODELS')


sys.meta_path.insert(0,NoModels())
import numpy as np
R=Path(__file__).resolve().parents[2];W=R/'experiments/v850_progress_consistent_worker'
sys.path.insert(0,str(W))
from progress_contract import context,assess,summarize
from audit_progress_record import check
from reserved_recovery import ReservedRecovery


def main():
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SAVED_QUALIFICATION_180S')));signal.alarm(180)
    out=R/'runs/v850_progress_consistent_return/saved_qualification';out.mkdir(exist_ok=False)
    cell=R/'runs/v848_goal_first_worker/v848_main_slot01/paired/geometry_memory';sources={};records=[];negative=[]
    def read(path):
        raw=path.read_bytes();sources[str(path.relative_to(R))]=hashlib.sha256(raw).hexdigest()
        return json.loads(gzip.decompress(raw)if path.suffix=='.gz'else raw)
    def reject(name,call):
        try:call()
        except (AssertionError,RuntimeError,ValueError):negative.append(name);return
        raise AssertionError('NEGATIVE_ACCEPTED:'+name)
    contracts={c['created_step']:c for c in [read(p)for p in sorted((cell/'recovery_contracts').glob('*.json.gz'))]}
    protocol=read(cell.parent/'STATIC_PROTOCOL.json');goal=np.asarray(protocol['goal_xy'])
    returns=sorted((cell/'handover_certificates').glob('*.json.gz'));assert len(returns)==14
    first=None
    for file in returns:
        new=read(file);old=contracts[new['old_created_step']];cursor=new['old_native_cursor']
        real=SimpleNamespace(qpos=np.asarray(new['real_entry_qpos']),qvel=np.asarray(new['real_entry_qvel']),time=new['real_entry_time'])
        reference={'goal_xy':goal.tolist()};ctx=context(real,new['forecast_state'],reference,old,cursor,new['handover_step'],'BACKUP_RETURN')
        decision=assess(ctx,np.asarray(new['qpos'])[-1,:2])
        # Independent scalar reconstruction from raw states, not recorded gains.
        start=float(np.linalg.norm(real.qpos[:2]-goal));old_end=float(np.linalg.norm(np.asarray(old['qpos'])[-1,:2]-goal));new_end=float(np.linalg.norm(np.asarray(new['qpos'])[-1,:2]-goal))
        assert new['metadata']['predicted_goal_progress_m']>=.02
        assert start-new_end<0 and not decision['normal_allowed']and not decision['recovery_only']
        assert abs(decision['complete_goal_gain_m']-(start-new_end))<=1e-10
        assert abs(decision['old_terminal_improvement_m']-(old_end-new_end))<=1e-10
        records.append(dict(step=new['handover_step'],nominal_gain_m=new['metadata']['predicted_goal_progress_m'],old_remaining_gain_m=start-old_end,rejected_full_gain_m=start-new_end,new_policy_accepts_saved_switch=False,old_preserved=True))
        if new['handover_step']==573:first=(real,old,new,ctx)
    assert first is not None
    real,old,new,ctx=first
    reject('bad_old_state',lambda:context(SimpleNamespace(qpos=real.qpos+.001,qvel=real.qvel,time=real.time),new['forecast_state'],{'goal_xy':goal},old,ctx['old_cursor'],573))
    reject('bad_old_time',lambda:context(SimpleNamespace(qpos=real.qpos,qvel=real.qvel,time=real.time+.01),new['forecast_state'],{'goal_xy':goal},old,ctx['old_cursor'],573))
    reject('bad_old_cursor',lambda:context(real,new['forecast_state'],{'goal_xy':goal},old,-1,573))
    reject('nan_terminal',lambda:assess(ctx,[np.nan,0.]))
    reject('nan_public_goal',lambda:context(real,new['forecast_state'],{'goal_xy':[np.nan,0.]},None,0,573))
    # Synthetic exact boundary and independent audit checks, no dynamics.
    source=SimpleNamespace(qpos=np.array([0.,0.,0.]),qvel=np.zeros(3),time=0.)
    motion={'center':[1.,1.]};reference={'goal_xy':[10.,0.]}
    fresh=context(source,motion,reference,None,0,0)
    make=lambda x:dict(prefix_initial_qpos=source.qpos.copy(),qpos=np.repeat([[x,0.,0.]],320,axis=0))
    candidate=make(.5);summarize(candidate,fresh,assess(fresh,[.5,0.]),'PROGRESS');check(candidate,source)
    at_floor=make(.02);summarize(at_floor,fresh,assess(fresh,[.02,0.]),'PROGRESS');check(at_floor,source)
    bad=make(.019999);reject('below_original_progress_floor',lambda:summarize(bad,fresh,assess(fresh,[.019999,0.]),'PROGRESS'))
    retreat=make(-.5);summarize(retreat,fresh,assess(fresh,[-.5,0.]),'RECOVERY_ENTRY');check(retreat,source)
    retreat.update(created_step=0,start_time=.08,initial_qpos=np.array([.01,0.,0.]),initial_qvel=np.zeros(3),prefix_command=np.zeros(4))
    # The actual entry function creates only controller metadata, after the
    # previously certified eight-native prefix has completed and matched.
    retained=ReservedRecovery.__new__(ReservedRecovery);retained.cache=retreat;retained.progress_pending=True;retained.executing=False;retained.activations=0;retained.cursor=0;retained.expected=None;retained.expected_ctrl=None;retained.cell=out;retained.ids=[0,1,2,3]
    after=SimpleNamespace(qpos=np.array([.01,0.,0.]),qvel=np.zeros(3),ctrl=np.zeros(4),time=.08)
    before=copy.deepcopy(after);retained.begin_pending_recovery(after,1)
    assert retained.executing and not retained.progress_pending and retained.activations==1
    assert np.array_equal(after.qpos,before.qpos)and np.array_equal(after.qvel,before.qvel)and np.array_equal(after.ctrl,before.ctrl)and after.time==before.time
    retain=dict(created_step=0,start_time=0.,initial_qpos=source.qpos.copy(),initial_qvel=source.qvel.copy(),qpos=np.repeat([[1.,0.,0.]],320,axis=0),qvel=np.zeros((320,3)))
    retained_ctx=context(source,motion,reference,retain,0,1)
    dominated=assess(retained_ctx,[.5,0.]);assert not dominated['normal_allowed']and not dominated['recovery_only']and dominated['reason']=='PROGRESS_REPLACES_BETTER_RETAINED'
    improved=make(1.02);summarize(improved,retained_ctx,assess(retained_ctx,[1.02,0.]),'PROGRESS');check(improved,source,retain,0)
    tampered=copy.deepcopy(improved);tampered['qpos'][-1,0]=.5
    reject('forged_full_progress_certificate',lambda:check(tampered,source,retain,0))
    tampered=copy.deepcopy(retreat);tampered['progress_contract']['mode']='PROGRESS'
    reject('recovery_disguised_as_progress',lambda:check(tampered,source))
    tampered=copy.deepcopy(improved);tampered['progress_contract']['context']['old_terminal_goal_m']=10.
    reject('forged_retained_endpoint',lambda:check(tampered,source,retain,0))
    inactive=context(source,{'center':None},reference,None,0,0)
    assert assess(inactive,[-1.,0.])['normal_allowed']
    reverse=context(source,motion,None,retain,0,0)
    assert assess(reverse,[-1.,0.])['normal_allowed']
    # The phase classifier keeps predetection and explicitly planned reverse.
    # This is not a no-reverse controller or an arrival theorem.
    result=dict(status='SAVED_PROGRESS_POLICY_QUALIFICATION_PASS',saved_returns=records,negative_cases=negative,original_progress_floor_m=.02,positive_and_boundary_checks_passed=True,predetection_and_planned_reverse_preserved=True,recovery_entry_metadata_only=True,physics_revalidated=False,new_models=0,new_integrations=0,new_navigation=0,training=0,new_full_candidate_search=False,limitations='Only saved selected certificates and synthetic policy cases; no new physical trajectory or navigation outcome established.')
    (out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');(out/'INPUT_SHA256.json').write_text(json.dumps(sources,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in ['saved_returns','negative_cases']},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
