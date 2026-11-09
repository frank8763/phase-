"""One operational exception; original frozen scientific modules are never edited."""
import hashlib,importlib.util,json,runpy,sys,time
from pathlib import Path
OPS=Path(__file__).resolve().parent;R=OPS.parents[1];BASE=R/'experiments/v909_timed_command_contract';O=R/'runs/v909_output_continuation';OLD=R/'runs/v909_timed_command_contract';WRITABLE=R/'runs/v858_nav2_verified/v909/continuation_status'
sys.path[:0]=[str(BASE),str(R/'experiments/v862_ready_static')]
import authority
from handshake import require,verify_sources,file_sha
def read(p):return json.loads(Path(p).read_text())
def root_authorized(now,sha):
    approval=read(O/'AUTHORIZATION.json');original=read(OLD/'AUTHORIZATION.json');window=read(OLD/'ROUND_WINDOW.json')
    require(approval['models_authorized']is True and not(O/'COMPLETION.json').exists(),'CONTINUATION_CLOSED')
    require(approval['deadline_unix']==original['deadline_unix']==window['deadline_unix'] and original['started_unix']==window['started_unix'],'NO_WINDOW_RESET')
    require(now<window['deadline_unix']-30,'EXPIRED')
    require(approval['original_source_freeze_sha256']==sha==original['source_freeze_sha256'],'SCIENTIFIC_SOURCE_CHANGED')
    require(read(OLD/'COMPLETION.json')['status']=='NOT_PASSED','ORIGINAL_FAILURE_ERASED')
    require(read(R/'runs/v858_nav2_verified/v909/platform_00/QUALIFICATION.json')['passed'],'FIRST_PHYSICAL_CASE_NOT_PASSED')
    require(read(O/'ZERO_MODEL_QUALIFICATION.json')['passed'],'OUTPUT_BOUNDARY_NOT_QUALIFIED')
    require(approval['operational_source_freeze_sha256']==file_sha(OPS/'SOURCE_FREEZE.json'),'OPERATIONAL_SOURCE_CHANGED')
    verify_sources(R,OPS/'SOURCE_FREEZE.json');verify_sources(R,BASE/'SOURCE_FREEZE.json')
    return original
def authorized(task,receipt,now,sha):
    root=root_authorized(now,sha)
    require(receipt==dict(root,run_id=task['run_id'],task_sha256=authority.digest(task)),'RECEIPT_CHANGED')
    require(task in read(BASE/'TASKS.json'),'UNREGISTERED_TASK')
    require(read(O/'PLATFORM_RESULT.json')['passed'],'PLATFORM_NOT_PASSED')
    if task['role']=='dynamic_repeat':require(read(Path(task['output']).parent/'main_we/INDEPENDENT_AUDIT.json')['passed'],'MAIN_NOT_PASSED')
    return root['deadline_unix']
def install():
    authority.root_authorized=root_authorized
    authority.authorized=authorized
def main():
    install();root_authorized(time.time(),file_sha(BASE/'SOURCE_FREEZE.json'))
    mode=sys.argv[1];args=sys.argv[2:]
    if mode=='response':
        index=int(args[0]);require(1<=index<18,'FIRST_CASE_MUST_NOT_BE_REPEATED')
        module_path=BASE/'qualify_response.py';spec=importlib.util.spec_from_file_location('v909_same_frozen_response',module_path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        m.O=WRITABLE;sys.argv=[str(module_path),str(index)];return m.main()
    target={'native':BASE/'native_worker.py','ros':BASE/'ros_worker.py','launch':OPS/'launch_one.py'}[mode]
    sys.argv=[str(target),*args];runpy.run_path(str(target),run_name='__main__');return 0
if __name__=='__main__':sys.exit(main())
