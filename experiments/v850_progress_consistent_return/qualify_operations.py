"""Actual component and engine entry rehearsal, stopped at the first model/Popen."""
import ast,fcntl,os,runpy,subprocess,sys,time,types
from pathlib import Path
import common
from common import R,C,W,ROOT,read,dump,tasks

class ModelBoundary(BaseException):pass
class ProcessBoundary(BaseException):pass


def main():
    out=ROOT/'operations_qualification';out.mkdir(exist_ok=False)
    assert(R/'REVIEW_PENDING').exists()
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);lock.close()
    for p in [*C.glob('*.py'),*W.glob('*.py')]:ast.parse(p.read_text(),filename=str(p))
    assert read(ROOT/'LEGACY_AUDITOR_QUALIFICATION.json')['passed']and read(ROOT/'progress_auditor_qualification/RESULT.json')['passed']
    sys.path.insert(0,str(W))
    # Replace only the model constructor with a boundary trap. No actual
    # MuJoCo package is imported; all pre-model sensor/calibration code is real.
    fake=types.ModuleType('mujoco')
    def denied(*args,**kwargs):raise ModelBoundary('FIRST_REAL_MJB_READ_BOUNDARY_REACHED')
    fake.MjModel=types.SimpleNamespace(from_binary_path=denied)
    sys.modules['mujoco']=fake
    original_root,original_unchanged=common.ROOT,common.unchanged
    common.ROOT=out/'component_entry';common.ROOT.mkdir();common.unchanged=lambda:None
    os.environ['PHASE_MODEL_ABSOLUTE_DEADLINE']=str(time.time()+180)
    try:
        try:runpy.run_path(str(C/'component.py'),run_name='__main__')
        except ModelBoundary:pass
        else:raise AssertionError('COMPONENT_DID_NOT_REACH_EXPECTED_FIRST_MODEL')
    finally:
        common.ROOT,common.unchanged=original_root,original_unchanged
        sys.modules.pop('mujoco',None)
    component=read(out/'component_entry/component01/COMPLETION.json')
    assert component['counts']['old_replay_native']==component['counts']['actual_branch_native']==component['counts']['repeat_branch_native']==0
    assert read(out/'component_entry/component01/SENSOR_CALIBRATION.json')['raw_packets']==574
    import engine
    calls=[];old_popen=engine.subprocess.Popen;old_same=engine.unchanged
    engine.unchanged=lambda:None
    def process(command,**kwargs):
        calls.append(dict(command=list(map(str,command)),cwd=str(kwargs['cwd']),env={k:kwargs['env'][k]for k in ['PHASE_FIELD_CASE','PHASE_COURSE_PHASE','PHASE_MODEL_ABSOLUTE_DEADLINE']}));raise ProcessBoundary()
    engine.subprocess.Popen=process
    phase=out/'engine_entry';phase.mkdir();stage=engine.Stage(time.time()+5400,phase=phase,raw=out/'raw_unused')
    try:
        try:stage.t0(tasks()[0])
        except ProcessBoundary:pass
        else:raise AssertionError('ACTUAL_ENGINE_DID_NOT_REACH_FIRST_T0_PROCESS')
    finally:engine.subprocess.Popen=old_popen;engine.unchanged=old_same
    assert len(calls)==1 and calls[0]['command'][0]==str(R/'run_phase.sh')and calls[0]['command'][1]=='experiments/v850_progress_consistent_worker/run_static.py'
    assert calls[0]['env']['PHASE_FIELD_CASE']=='WEST_EAST'and'--feasibility-only'in calls[0]['command']
    cases=[]
    for label,entry,deadline,expected in [('correct',str(Path(__file__).resolve()),time.time()+60,True),('wrong',str(C/'start.py'),time.time()+60,False),('expired',str(Path(__file__).resolve()),time.time()-1,False)]:
        completed=subprocess.run([sys.executable,'-B',str(C/'os_watch.py'),'--probe-only','--pid',str(os.getpid()),'--entrypoint',entry,'--deadline',str(deadline)],capture_output=True,text=True,timeout=5)
        (out/(label+'.console')).write_text(completed.stdout+completed.stderr);assert(completed.returncode==0)==expected;cases.append(dict(case=label,passed=True))
    expected=[dict(task=t,role=role,physical_passed=True,functional_passed=True,repeat_passed=role=='REPEAT')for t in tasks()for role in ['MAIN','REPEAT']]
    assert common.complete_gate(expected)
    assert not common.complete_gate(expected[:-1])and not common.complete_gate(list(reversed(expected)))
    assert not common.model_fits(100,98,2)and common.model_fits(1000,0,600)
    dump(ROOT/'OPERATIONS_CHECK.json',dict(passed=True,component_first_model_boundary=True,real574_sensor_calibration=True,actual_engine_first_t0_process_boundary=True,commands=calls,os_identity_cases=cases,complete_stage_gate_negatives=True,new_models=0,new_integrations=0,new_navigation=0))
    print('OPERATIONS_QUALIFIED_ZERO_MODELS',flush=True)


if __name__=='__main__':main()
