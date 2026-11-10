"""Exact V990 final-target reconstruction plus original history comparison."""
import importlib.util,json,sys,traceback
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
C990=R/'experiments/v990_coordinated_actuation'
source=C990/'vehicle_control.py'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
saved_independent=sys.modules.get('independent');saved_fixture=sys.modules.get('fixture')
sys.modules['independent']=load('v991_exact_independent',C990/'independent.py')
sys.modules['fixture']=load('v991_exact_control_fixture',C990/'fixture.py')
try:implementation=load('v991_exact_v990_audit',C990/'actuation_audit.py')
finally:
    for name,old in [('independent',saved_independent),('fixture',saved_fixture)]:
        if old is None:sys.modules.pop(name,None)
        else:sys.modules[name]=old
check=implementation.check
body=implementation.body

def compare_history(data,expected,commands,old_commands,origin):
    assert len(commands)>=origin and len(old_commands)>=origin
    errors={}
    for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
        a=np.asarray(data[key][:origin]);b=np.asarray(expected[key][:origin]);assert a.shape==b.shape and len(a)==origin
        errors[key]=float(abs(a-b).max())if a.size else 0.
    assert max(errors.values())<=1e-8,'INDEPENDENT_HISTORICAL_STATE_CONTROL_MISMATCH'
    assert all([a[1],a[2],a[5]]==[b[1],b[2],b[5]]for a,b in zip(commands[:origin],old_commands[:origin])),'HISTORICAL_BODY_REQUEST_CHANGED'
    return dict(passed=True,full_state_control_errors=errors,historical_native_rows=origin,integrations=0)

def audit(out,task):
    out=Path(out)
    try:
        p=out/'RESULT.json';native=json.loads(p.read_text())if p.exists()else{}
        if native.get('armed_at')is None:
            answer=dict(passed=False,status='NOT_EXECUTED',reason='NO_ARM_NEW_CONTROL_NOT_TESTED',
                exact_new_branch_native=native.get('new_branch_native'),original_native_error=native.get('error'),models=0,integrations=0)
        else:
            prior=R/'runs/v991_coordinated_components/prior_v974'
            required=json.loads((Path(__file__).parent/'RESTORE_REQUIREMENTS.json').read_text())
            import hashlib
            for name in ['physics/NATIVE_TRACE.npz','physics/BODY_COMMANDS.json']:
                path=prior/name;row=next(r for r in required['files']if r['path']==str(path.relative_to(R)))
                assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'],'HISTORICAL_INPUT_SHA_MISMATCH'
            commands=json.loads((out/'physics/BODY_COMMANDS.json').read_text());old_commands=json.loads((prior/'physics/BODY_COMMANDS.json').read_text())
            with np.load(out/'physics/NATIVE_TRACE.npz')as data,np.load(prior/'physics/NATIVE_TRACE.npz')as expected:
                history=compare_history(data,expected,commands,old_commands,task['origin_native_tick'])
            answer=check(out,task);answer['independent_full_historical_restore']=history
    except BaseException as e:answer=dict(passed=False,error=repr(e),traceback=traceback.format_exc(),models=0,integrations=0)
    (out/'ACTUATION_AUDIT.json').write_text(json.dumps(answer,indent=2)+'\n')
    return answer
