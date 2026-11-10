"""Run the production campaign with nonphysical subprocess peers and isolated files."""
import importlib.util,json,sys,tempfile,types
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1015_atomic_entry_continuation'
sys.path.insert(0,str(C));import authority as a

def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x)+'\n')
def scenario(label,failed_slot=None,safety=False):
    s=importlib.util.spec_from_file_location('queue_'+label,C/'campaign.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    original=(a.R,a.C,a.O,a.ROOT);prior_modules={k:sys.modules.get(k)for k in ['preflight_audit','repeat_contract']};old_process=m.subprocess
    with tempfile.TemporaryDirectory(prefix='queue-',dir=O)as td:
        f=Path(td);m.R=a.R=f;m.C=a.C=f/'C';m.O=a.O=f/'O';m.ROOT=a.ROOT=f/'ROOT';m.O.mkdir();m.ROOT.mkdir();m.C.mkdir()
        tasks=a.read(C/'TASKS.json')
        for t in tasks:
            t['output']=str(f/'outputs'/t['task_id']);t['baseline_output']=str(f/'outputs'/('main_'+t['route']))
            t['preflight_output']=str(f/'preflights'/t['task_id'])
        dump(m.C/'TASKS.json',tasks);dump(m.C/'SOURCE_FREEZE.json',dict(files={}));freeze=a.sha(m.C/'SOURCE_FREEZE.json')
        for name in ['ZERO_MODEL_QUALIFICATION.json','SAVED_AUDIT_QUALIFICATION.json','BACKEND_ENTRY_QUALIFICATION.json','AUTHORITY_QUALIFICATION.json']:dump(m.O/name,dict(passed=True))
        dump(f/'records/nav2_v1003_20261110/FINAL_INDEPENDENT_AUDIT.json',dict(component_passed=True));dump(f/'records/nav2_v1010_20261110/FINAL_INDEPENDENT_AUDIT.json',dict(passed=True));dump(f/'records/nav2_v1013_20261110/HANDOFF_QUALIFICATION.json',dict(passed=True))
        dump(f/'runs/atomic_handoff_night_20261110/COMPLETION.json',dict(closed=True));dump(m.ROOT/'APPROVAL.json',dict(models_authorized=True,new_night_authorized=True,independent_route_branches=True,source_freeze_sha256=freeze))
        dump(m.ROOT/'ROUND_WINDOW.json',dict(started_unix=1794310000.,deadline_unix=a.HARD_END));dump(f/'CURRENT_EXPERIMENT.json',dict(status='REVIEW_PENDING'))
        (f/'REVIEW_PENDING').write_bytes(b'original-guard\n');(m.ROOT/'REVIEW_PENDING.before').write_bytes(b'original-guard\n')
        screens=[];executed=[];preflight_tasks=[];closed=[]
        def screen(selected):screens.append([t['slot']for t in selected]);return dict(passed=True)
        sys.modules['preflight_audit']=types.SimpleNamespace(audit=screen);sys.modules['repeat_contract']=types.SimpleNamespace(repeat_check=lambda *args:dict(passed=True))
        class Child:
            pid=999999
            def __init__(self,args,**kw):
                self.task=json.loads(Path(args[-2]).read_text());self.preflight=any('t0_worker.py'in str(x)for x in args)
            def poll(self):return 0
            def wait(self,**kw):
                t=self.task
                if self.preflight:preflight_tasks.append(t['slot']);return 0
                slot=t['slot'];executed.append(slot);ok=slot!=failed_slot
                dump(Path(t['output'])/'RESULT.json',dict(actual_native=100,replay_native=100,private_native=0,goal_distance_m=.1 if ok else 1.,error=None))
                dump(Path(t['output'])/'INDEPENDENT_AUDIT.json',dict(passed=ok,evidence_passed=not(safety and not ok),minimum_clearance_m=.3))
                return 0 if ok else 1
        m.subprocess=types.SimpleNamespace(Popen=Child,run=lambda *args,**kw:closed.append('zero-model-close'),STDOUT=old_process.STDOUT,TimeoutExpired=old_process.TimeoutExpired)
        try:
            result=m.main();done=json.loads((m.ROOT/'COMPLETION.json').read_text())
            assert(f/'REVIEW_PENDING').read_bytes()==b'original-guard\n'and not a.read(m.ROOT/'APPROVAL.json')['models_authorized']
            assert closed==['zero-model-close']
            if safety:assert executed==[0]and len(done['unexecuted_tasks'])==32 and result==1
            elif failed_slot==0:assert executed==[0,2,3,4,5]and done['status']=='THREE_ROUTE_DEVELOPMENT_NOT_PASSED'and 'repeat_we'in done['unexecuted_tasks']and not preflight_tasks
            else:assert executed==list(range(33))and len(preflight_tasks)==24 and done['new24_executed']==24 and result==0
            return dict(case=label,passed=True,executed_slots=executed,preflights=len(preflight_tasks),guard_restored=True)
        finally:
            a.R,a.C,a.O,a.ROOT=original;m.subprocess=old_process
            for key,value in prior_modules.items():
                if value is None:sys.modules.pop(key,None)
                else:sys.modules[key]=value

def main():
    rows=[scenario('pure_WE_function_failure_other_routes_continue',0),scenario('first_safety_failure_stops_all',0,True),scenario('six_routes_enable_fixed24_and_three_repeats',10)]
    result=dict(passed=True,models=0,integrations=0,actual_campaign_exercised=True,rows=rows)
    (O/'QUEUE_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows),models=0)))
if __name__=='__main__':main()
