"""Run actual profile install/finally under the real frozen write audit hook."""
import argparse,ast,atexit,importlib.util,json,os,subprocess,sys,types
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;ROOT=R/'runs/v855_renewal_progress'


def child(case):
    import numpy as np
    version='v850_progress_consistent_worker'if case=='old_red'else'v855_renewal_worker';w=R/'experiments'/version
    outer=ROOT/'output_cases'/case;pair=outer/'paired';pair.mkdir(parents=True,exist_ok=False)
    class FakePredictor:
        def predict(self):return 'predict'
        def select(self):return 'select'
    class FakeReserve:
        def admit_nominal(self):raise ValueError('ORIGINAL_OPERATION_ERROR')
    for name,values in [('geometry_predictor',dict(RobotPredictor=FakePredictor)),('reserved_recovery',dict(ReservedRecovery=FakeReserve)),('reference_recovery',dict(predict_follow=lambda:None))]:
        module=types.ModuleType(name);module.__dict__.update(values);sys.modules[name]=module
    spec=importlib.util.spec_from_file_location('profile_under_test',w/'operation_profile.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    finish=module.install(outer)
    tree=ast.parse((R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='write_guard')
    guard=dict(Path=Path,os=os,OUT=pair);exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual_frozen_write_guard','exec'),guard);sys.addaudithook(guard['write_guard'])
    if case!='new_t0':
        assert FakePredictor().predict()=='predict'
        try:FakeReserve().admit_nominal()
        except ValueError:pass
    node=next(n for n in ast.parse((w/'run_static.py').read_text()).body if isinstance(n,ast.Try)and n.finalbody)
    original_error={'type':'ValueError','message':'ORIGINAL_OPERATION_ERROR'}if case=='new_error'else None
    # The same actual finalbody is used for normal t0, normal navigation and
    # error completion. Only environment/model work is absent from this test.
    def dump(path,value):Path(path).write_text(json.dumps(value)+'\n')
    namespace=dict(signal=SimpleNamespace(alarm=lambda _:None),context={'out':pair},outer=outer,profile_finish=finish,dump=dump,status='FAILED'if case=='new_error'else'PREFLIGHT_COMPLETE',a=SimpleNamespace(seed=10010001),results=[],error=original_error,time=__import__('time'),started=__import__('time').monotonic())
    caught=None
    try:exec(compile(ast.Module(body=node.finalbody,type_ignores=[]),'actual_run_static_finalbody','exec'),namespace)
    except PermissionError as error:caught=str(error)
    atexit.unregister(finish)
    if case=='old_red':assert caught is not None and not(pair/'completion.json').exists()
    else:
        assert caught is None;finish()  # atexit-equivalent second flush.
        completion=json.loads((pair/'completion.json').read_text());profile=json.loads((pair/'OPERATION_PROFILE.json').read_text())
        assert completion['error']==original_error and not(outer/'OPERATION_PROFILE.json').exists()
        if case=='new_t0':assert profile['operations']=={}
        else:assert profile['operations']['native_predict']['calls']==profile['operations']['complete_admission']['calls']==1
        try:guard['write_guard']('open',(str(outer/'forbidden.json'),'w',os.O_WRONLY|os.O_CREAT))
        except PermissionError:pass
        else:raise AssertionError('GUARD_WEAKENED')
    print(json.dumps(dict(case=case,passed=True,old_exact_bug_reproduced=case=='old_red',completion_preserves_original_error=case=='new_error',new_models=0,new_integrations=0)),flush=True)


def main():
    rows=[]
    for case in ['old_red','new_t0','new_navigation','new_error']:
        result=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--case',case],cwd=R,capture_output=True,text=True,timeout=30)
        (ROOT/(case+'.console')).write_text(result.stdout+result.stderr);assert result.returncode==0,(case,result.stderr)
        rows.append(json.loads(result.stdout.splitlines()[-1]))
    (ROOT/'OUTPUT_QUALIFICATION.json').write_text(json.dumps(dict(passed=True,cases=rows,actual_guard_and_actual_profile_and_actual_finalbody=True,models=0,integrations=0),indent=2)+'\n');print(json.dumps(rows))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--case');args=parser.parse_args()
    if args.case:child(args.case)
    else:main()
