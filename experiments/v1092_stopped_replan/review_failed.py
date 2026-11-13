"""Zero-model post-closure audit; preserves failed route and frozen auditor."""
import sys,json,types,copy,gzip,ast,math,importlib.util
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1092_stopped_replan'
def review_failed_proposal(setup,task,out,packet):
    import numpy as np,corridor
    from kernel import load
    from types import SimpleNamespace
    causal=load('failed_actual_public_ranges',R/'experiments/v1024_full_route_execution/causal.py')
    norm=load('failed_actual_norm_domain',R/'experiments/v1037_periodic_norm_source/periodic_norm.py')
    evidence=causal.Evidence(setup['known']);evidence.periodic=norm.PeriodicSupport()
    with gzip.open(Path(out)/'physics/SENSORS.json.gz','rt')as file:scans=json.load(file)
    for scan in scans[2:]:evidence.update(scan)
    source=evidence.source(SimpleNamespace(d=SimpleNamespace(time=packet['sim_time'])))
    x=dict(setup=setup,packet=packet,source=source,goal=task['goal_xy'])
    assert not(O/'FAILED_ACTUAL_INPUT.json').exists()
    (O/'FAILED_ACTUAL_INPUT.json').write_text(json.dumps(x,indent=2)+'\n')
    try:corridor.construct(setup,packet,source,Path(task['run_root']),task['goal_xy']);raise RuntimeError('FAILED_PROPOSAL_WAS_ACCEPTED')
    except AssertionError as error:
        old=json.loads((Path(out)/'RESULT.json').read_text())['error']
        expected=ast.literal_eval(old[len('AssertionError('):-1])
        def equal(a,b):
            if isinstance(a,dict):return a.keys()==b.keys()and all(equal(a[k],b[k])for k in a)
            if isinstance(a,(tuple,list)):return len(a)==len(b)and all(equal(x,y)for x,y in zip(a,b))
            if isinstance(a,(float,int))and not isinstance(a,bool):return abs(a-b)<=1e-8
            return a==b
        assert equal(error.args[0],expected),'FAILED_PROPOSAL_DID_NOT_REPRODUCE'
        (O/'FAILED_PROPOSAL_REBUILT.json').write_text(json.dumps(dict(reproduced=True,payload=error.args[0],models=0,integrations=0),indent=2)+'\n')
def main():
    assert json.loads((O/'COMPLETION.json').read_text())['closed']
    # Retain exact frozen operation source, adding only diagnostic access to
    # its already-transformed audit text. Frozen files are never edited.
    p=C/'audit.py';text=p.read_text();old='exec(compile(s,str(prior.ORIGINAL)'
    assert text.count(old)==1;text=text.replace(old,'m._review_source=s;'+old)
    wrapper=types.ModuleType('failed_route_review_wrapper');wrapper.__file__=str(p);exec(compile(text,str(p),'exec'),wrapper.__dict__)
    m=wrapper.patched_module();source=m._review_source
    # The unchanged core imports finite_plan locally inside audit(); the old
    # extension had incorrectly assumed it was a module attribute.
    m.finite_plan=__import__('fresh').finite_plan
    old="assert result['passed']and result['historical_replay_native']==0 and result['fresh_native_zero']"
    assert source.count(old)==1;source=source.replace(old,"assert not result['passed']and result['historical_replay_native']==0 and result['fresh_native_zero']")
    anchor=" causal=load('fresh_audit_causal_ranges'"
    assert source.count(anchor)==1
    block=""" final_packet=__import__('copy').deepcopy(entry['packet']);final_packet.update(body=[float(q[-1,0]),float(q[-1,1]),float(yaw[-1]),float(forward[-1]),float(z['qvel'][-1,5])],native_tick=n,sim_time=float(z['time'][-1]),dynamic_discovered=True,speed_episode=False)
 final_packet['steering'].update(position=q[-1,setup['steering_qpos_addresses']].tolist(),velocity=z['qvel'][-1,setup['steering_qvel_addresses']].tolist(),native_tick=n)
 final_packet['controller_memory'].update(last_ctrl=memories[n][:4].tolist(),integral=float(memories[n][4]))
 review_failed_proposal(setup,task,out,final_packet)
"""
    source=source.replace(anchor,block+anchor)
    source=source.replace("out/'FINAL_INDEPENDENT_AUDIT.json'","out/'FAILED_ROUTE_INDEPENDENT_AUDIT.json'")
    m.review_failed_proposal=review_failed_proposal;exec(compile(source,str(p),'exec'),m.__dict__)
    task=json.loads((C/'TASKS.json').read_text())[0];answer=m.audit(task)
    failed=[key for key,value in answer['checks'].items()if not value]
    result=dict(evidence_integrity_passed=failed==['goal'],functional_passed=False,failed_gates=failed,
                audit=answer,models=0,integrations=0,new_model_not_started=True)
    (O/'FAILED_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
