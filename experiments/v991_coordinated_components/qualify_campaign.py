"""Exercise actual campaign order/finally with explicit file-only children.

The fixture root is below this batch's runs tree. No native/ROS worker or model
is launched, and fixture authorization is never written at the real root.
"""
import copy,importlib.util,json,signal,time
from pathlib import Path
from types import SimpleNamespace as S

C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v991_coordinated_components'


def exercise(label):
    spec=importlib.util.spec_from_file_location('v991_campaign_fixture_'+label,C/'campaign.py')
    engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
    root=O/'campaign_fixture_attempt3'/label;root.mkdir(parents=True,exist_ok=False)
    batch=root/'batch';batch.mkdir();engine.R=root;engine.O=batch
    engine.C=root/'experiments/candidate';engine.C.mkdir(parents=True)
    guard=(R/'REVIEW_PENDING').read_bytes();(root/'REVIEW_PENDING').write_bytes(guard)
    (root/'CURRENT_EXPERIMENT.json').write_text(json.dumps(dict(status='REVIEW_PENDING')))
    tasks=copy.deepcopy(json.loads((C/'TASKS.json').read_text()))
    for i,t in enumerate(tasks):t['output']=str(root/f'worker_{i}')
    auth=dict(deadline_unix=time.time()+(100 if label=='insufficient_time'else 5000),models_authorized=True,
              fixture_only=True)
    (batch/'AUTHORIZATION.json').write_text(json.dumps(auth))
    actual_read=engine.read
    engine.read=lambda p:tasks if Path(p)==engine.C/'TASKS.json'else actual_read(p)
    engine.root_authorized=lambda:auth
    launched=[];finalized=[]
    class Child:
        pid=0
        def __init__(self,args,**kwargs):
            self.task=json.loads(Path(args[-2]).read_text());launched.append(self.task['slot'])
        def wait(self,**kwargs):
            task=self.task;p=Path(task['output']);p.mkdir()
            passed=label!='first_failure'
            (p/'RESULT.json').write_text(json.dumps(dict(status='FIXTURE_ONLY',armed_at=None,new_branch_native=0,
                historical_prefix_replay_native=0,replay_native=0)))
            (p/'INDEPENDENT_AUDIT.json').write_text(json.dumps(dict(passed=passed,fixture_only=True)))
            (p/'COMPLETION.json').write_text(json.dumps(dict(error=None if passed else'EXPECTED_FIXTURE_FIRST_FAILURE')))
            return 0 if passed else 1
        def poll(self):return 0
    def finalizer(args,**kwargs):
        assert Path(args[-1])==engine.C/'finalize.py';finalized.append(True)
        return S(returncode=0)
    engine.subprocess=S(Popen=Child,run=finalizer,TimeoutExpired=TimeoutError,DEVNULL=-3,STDOUT=-2)
    old=signal.getsignal(signal.SIGTERM)
    try:rc=engine.main()
    finally:signal.signal(signal.SIGTERM,old)
    done=json.loads((batch/'COMPLETION.json').read_text())
    state=json.loads((root/'CURRENT_EXPERIMENT.json').read_text())
    if label=='all_pass':assert launched==[0,1]and rc==0 and done['status']=='TWO_FIXED_COMPONENTS_PASSED'
    elif label=='first_failure':assert launched==[0]and rc==1 and done['unexecuted_tasks']==['component_1']
    else:assert not launched and rc==1 and len(done['unexecuted_tasks'])==2
    assert len(finalized)==1 and done['closed']and not done['automatic_followup']and done['new24']==0
    assert not json.loads((batch/'AUTHORIZATION.json').read_text())['models_authorized']
    assert (root/'REVIEW_PENDING').read_bytes()==guard and state['status']=='REVIEW_PENDING'
    assert state['active_run']is None and not state['next_physical_authorized']
    return dict(case=label,passed=True,fixture_task_slots=launched,finalized_once=True,real_authority_modified=False,
                models=0,integrations=0)


def main():
    cases=[exercise(x)for x in ['all_pass','first_failure','insufficient_time']]
    result=dict(passed=True,cases=cases,models=0,integrations=0,file_only_campaign_fixture=True,
                actual_campaign_function_exercised=True,physical_order_or_tracking_not_executed=True)
    (O/'CAMPAIGN_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
