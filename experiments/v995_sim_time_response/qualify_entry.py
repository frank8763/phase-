"""Reject wrong roots/tasks/reserves before model imports; zero-model dispatch proof."""
import ast,copy,hashlib,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v995_sim_time_response'
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
if __name__=='__main__':
    m=load('v995_authority_fixture',C/'authority.py');task=json.loads((C/'TASKS.json').read_text())[0]
    def run_case(change=None,now=200.,newtask=None):
        data={str(m.ROOT/'USER_AUTHORIZATION.json'):dict(maximum_root_s=5400.),
            str(m.ROOT/'ROUND_WINDOW.json'):dict(started_unix=100.,deadline_unix=5500.,source_freeze_sha256='fixture',user_authorization_sha256='fixture'),
            str(m.O/'ROUND_WINDOW.json'):dict(started_unix=100.,deadline_unix=1300.),
            str(m.C/'SOURCE_FREEZE.json'):dict(files={'not_a_physical_input':'fixture'}),
            str(m.C/'TASKS.json'):[task],str(m.O/'RESTORE_RECEIPT.json'):dict(files=[])}
        for n in ['QUALIFICATION.json','EXECUTION_QUALIFICATION.json','ENTRY_QUALIFICATION.json']:data[str(m.O/n)]=dict(passed=True)
        if change:change(data)
        m.read=lambda p:data[str(p)];m.sha=lambda p:'fixture'
        return m.authorize(task if newtask is None else newtask,now)
    cases=[]
    assert run_case()==1300.;cases.append('registered_root_and_task')
    bad=[('duration',lambda d:d[str(m.ROOT/'ROUND_WINDOW.json')].update(deadline_unix=5501.)),
         ('stage',lambda d:d[str(m.O/'ROUND_WINDOW.json')].update(deadline_unix=1301.)),
         ('freeze',lambda d:d[str(m.ROOT/'ROUND_WINDOW.json')].update(source_freeze_sha256='changed')),
         ('qualification',lambda d:d[str(m.O/'QUALIFICATION.json')].update(passed=False))]
    for name,change in bad:
        try:run_case(change)
        except AssertionError:cases.append('reject_'+name)
        else:raise AssertionError('AUTHORITY_ACCEPTED_'+name)
    for now in [50.,981.,5501.]:
        try:run_case(now=now)
        except AssertionError:cases.append('reject_clock_'+str(now))
        else:raise AssertionError('CLOCK_ACCEPTED')
    changed=copy.deepcopy(task);changed['seed']+=1
    try:run_case(newtask=changed)
    except AssertionError:cases.append('reject_changed_task')
    else:raise AssertionError('UNREGISTERED_TASK_ACCEPTED')
    # Source-bound import order and exact selected scientific class.
    tree=ast.parse((C/'worker.py').read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
    calls=[n for n in ast.walk(main)if isinstance(n,ast.Call)]
    auth_line=min(n.lineno for n in calls if isinstance(n.func,ast.Name)and n.func.id=='authorize')
    physical_line=min(n.lineno for n in ast.walk(main)if isinstance(n,ast.ImportFrom)and n.module=='physical')
    assert auth_line<physical_line;cases.append('authority_precedes_physical_import')
    from actuation_binding import SOURCE
    assert SOURCE==R/'experiments/v993_steering_transient_diagnosis/vehicle_control.py';cases.append('exact_original_science_binding')
    for p in C.glob('*.py'):ast.parse(p.read_text())
    assert not any(k.split('.')[0]in ['mujoco','torch','rclpy']for k in sys.modules)
    result=dict(passed=True,models=0,integrations=0,cases=cases,live_entry_order_checked=True,physical_bridge_not_yet_tested=True)
    (O/'ENTRY_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
