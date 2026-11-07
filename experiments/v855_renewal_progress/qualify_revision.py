"""Real saved startup red/green and independent renewal-cost crosscheck; no models."""
import copy,gzip,hashlib,importlib.abc,json,signal,sys
from pathlib import Path
from types import SimpleNamespace,MethodType
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('REVISION_QUALIFICATION_NO_MODELS')
sys.meta_path.insert(0,NoModels())
from common import *
sys.path.insert(0,str(W))
import numpy as np
from maneuver_core import ReferenceOwner,evaluate,evaluate_fixed
from maneuver_policy import decorate,commit_ticks
from current_guide import attach
from independent_norm import static_field
from independent_soft_reference import soft_values


def main():
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('REVISION_ZERO_MODEL_180S')));signal.alarm(180);out=ROOT/'revision_qualification02';out.mkdir(exist_ok=False);source=R/'runs/v853_maneuver_worker/v853_A32_main_slot01/paired';protocol=read(source/'STATIC_PROTOCOL.json');cell=source/'geometry_memory';cases=[];red=0;rescued=0
    for step in [303,344,508,631,1041,1246,1451,1574,1738,1779]:
        c=json.load(gzip.open(cell/'progress_certificates'/f'certificate_{step:04d}.json.gz','rt'));m=c['maneuver_contract'];owner=ReferenceOwner();owner.install(m['reference_path'],protocol['goal_xy'],0);owner.index=m['reference_index'];segment=owner.segment();q=np.asarray(m['real_entry_qpos']);v=np.asarray(m['real_entry_qvel']);t=c['created_time']
        old=evaluate_fixed(segment,c,q,v,t,commit_native=32);new=evaluate(segment,c,q,v,t);red+=not old['normal_allowed'];rescued+=not old['normal_allowed']and new['normal_allowed'];cases.append(dict(step=step,old32_allowed=old['normal_allowed'],new_adaptive_allowed=new['normal_allowed'],new_commit_native=new['committed_native_ticks'],reason=new['reason'],full_gain=new['route_merit_gain328_m']))
        if new['normal_allowed']:assert new['committed_native_ticks']in[64,328]and new['route_merit_gain328_m']>=.02-1e-10
    assert red==10 and rescued==10,'ACTUAL_STARTUP_REJECTION_NOT_REPAIRED'
    assert sum(x['new_commit_native']==328 and x['new_adaptive_allowed']for x in cases)==3,'ADAPTIVE_FULL328_NOT_EXERCISED'
    inputs=[cell/'progress_certificates'/f'certificate_{x["step"]:04d}.json.gz'for x in cases]+[source/'STATIC_PROTOCOL.json'];dump(ROOT/'REVISION_INPUT_SHA.json',{str(p.relative_to(R)):sha(p)for p in inputs})
    # Merely entering a new complete tail with negative full progress must not
    # become nominal progress because a longer execution commitment was used.
    negative=copy.deepcopy(c);negative['qpos']=np.repeat(q[None],320,axis=0).tolist();negative['qvel']=np.zeros_like(negative['qvel']).tolist();bad=evaluate(segment,negative,q,v,t);assert not bad['normal_allowed']
    pair=R/'runs/v853_maneuver_worker/v853_B64_main_slot01/paired';protocol=read(pair/'STATIC_PROTOCOL.json');states={x['step']:x for x in map(json.loads,(pair/'geometry_memory/motion_estimate.jsonl').read_text().splitlines())};rng=np.random.default_rng(855);points=np.c_[rng.uniform(-4,4,320),rng.uniform(-4,4,320),rng.uniform(-np.pi,np.pi,320)];errors=[]
    for step in [303,533,936,1105]:
        f=static_field(protocol);attach(f,states[step]);online=f.soft_forecast_cost(points);offline=soft_values(static_field(protocol),states[step],points,renewal=True);error=float(np.max(abs(online-offline)));assert error<=1e-10;errors.append(dict(step=step,poses=len(points),error=error))
    # Actual old reviewer condition is retained in the new canonical audit;
    # new reserve selection enumerates all entries rather than waiving it.
    text=(W/'reserved_recovery.py').read_text();assert "if maneuver is not None or(not following and brake_only):break"not in text;assert "registered_five_low_speed"in(W/'audit_run.py').read_text()
    result=dict(passed=True,old_real_startup_cases_red=red,real_saved_full_progress_rescued=rescued,cases=cases,renewal_soft_geometry_independent_errors=errors,negative_full_progress_not_reclassified=True,original_five_library_audit_preserved=True,models=0,integrations=0,physical_native456_not_yet_qualified=True,proof_scope='Saved-array policy red/green and1280 independent geometric queries only; no new model search or arrival evidence.')
    dump(out/'RESULT.json',result);dump(ROOT/'REVISION_QUALIFICATION.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':main()
