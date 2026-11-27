"""One raw-core ABI2 compile; never load the produced library."""
import datetime,fcntl,hashlib,json,os,resource,subprocess,time
from pathlib import Path

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
BASE=R/'experiments/v1943_rpp_synchronous_native_api';M=1024**2
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
allocated=lambda p:sum(f.stat().st_blocks*512 for f in p.rglob('*')if f.is_file())

def main():
    assert os.sched_getaffinity(0)=={4}
    assert not(S/'RPP_RAW_BUILD_ONCE.json').exists()and not(S/'RPP_RAW_BUILD_RESULT.json').exists()
    assert allocated(S)+allocated(R/'runs/v2183_lossless_capture_stream')+512*1024<=M,'RAW_BRIDGE_PREPARATION_NOT_FUNDED'
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    locks=[]
    for name in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
        h=(R/name).open();fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(h)
    assert not Path('/proc/113868').exists()
    original=BASE/'bridge.cpp';raw=original.read_text()
    changes=[('#include "../../experiments/v1338_rpp_executable_pair/executable_rpp.cpp"','#include "nav2_regulated_pure_pursuit_controller/regulated_pure_pursuit_controller.hpp"',1),
             ('phase_rpp::ExecutableRPP','nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController',2),
             ('int phase_rpp_abi_version(){return 1;}','int phase_rpp_abi_version(){return 2;}',1)]
    generated=raw
    for before,after,count in changes:
        assert generated.count(before)==count
        generated=generated.replace(before,after)
    reverted=generated
    for before,after,count in reversed(changes):
        assert reverted.count(after)==count
        reverted=reverted.replace(after,before)
    assert reverted==raw,'UNDECLARED_CPP_BEHAVIOR_CHANGE'
    # Comments disclose the NEW identity without modifying the historical file.
    prefix='// NEW shared-module raw upstream RPP ABI2. NO inner Phase projection/deadband.\n// Preserved historical comments below describe the ABI1 source ancestry.\n'
    target=C/'rpp_raw_core_bridge.cpp';assert not target.exists()
    root=R/'runs/v856_nav2_foundation/rootfs/opt/ros/jazzy';headers=R/'runs/v1340_overnight_preparation/headers'
    deps=[original,BASE/'registered_parameters.inc',BASE/'RPP_PARAMETER_SOURCE.json',
          R/'experiments/v1370_overnight_controller_matrix/rpp_default_params.json',
          root/'lib/libnav2_regulated_pure_pursuit_controller.so',C/'RPP_RAW_CORE_SCOPE.md',Path(__file__).resolve()]
    pins={str(p.relative_to(R)):sha(p)for p in deps}
    claim=dict(created_at=datetime.datetime.now().astimezone().isoformat(),pid=os.getpid(),cpu=4,max_s=120,
               compiler_AS_limit=1024*M,new_output_charge=512*1024,old_preparation_bytes=allocated(S)+allocated(R/'runs/v2183_lossless_capture_stream'),
               source_pins=pins,source_or_physical_authority=False,compile_only_no_library_load=True)
    with(S/'RPP_RAW_BUILD_ONCE.json').open('x')as f:f.write(json.dumps(claim,indent=2)+'\n')
    with target.open('x')as f:f.write(prefix+generated)
    include=[root/'include',*[p for p in(root/'include').iterdir()if p.is_dir()],headers/'opt/ros/jazzy/include',
             *[p for p in(headers/'opt/ros/jazzy/include').iterdir()if p.is_dir()],headers/'usr/include',headers/'usr/include/eigen3',BASE]
    output=S/'libphase_rpp_raw_core_abi2.so'
    tmp=S/'rpp_raw_build_tmp';tmp.mkdir()
    command=['g++','-std=c++17','-fPIC','-shared','-O2','-fmax-errors=4',str(target),
             *[v for p in include for v in ['-I',str(p)]],'-L'+str(root/'lib'),
             '-lnav2_regulated_pure_pursuit_controller','-lnav2_costmap_2d_core','-lnav2_util_core',
             '-lrclcpp_lifecycle','-lrclcpp','-ltf2_ros','-ltf2','-o',str(output)]
    def limits():resource.setrlimit(resource.RLIMIT_AS,(1024*M,1024*M));resource.setrlimit(resource.RLIMIT_FSIZE,(2*M,2*M));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    start=time.monotonic();answer=dict(passed=False,closed=False,scope='RAW_UPSTREAM_RPP_ABI2_COMPILATION_ONLY',
        declared_replacements=[dict(before=a,after=b,count=n)for a,b,n in changes],reverting_only_declared_changes_byte_exact=True,
        old_projection_deadband_and_projected_pair_recheck_removed=True,original_native_RPP_and_parameters_unchanged=True,
        source_pins=pins,command=command,DLL_loads_FFI_constructors_queries_models_physics_replay_audit_Source=0,
        shared_group_ready=False,physical_launch_authorized=False)
    try:
        p=subprocess.run(command,cwd=R,env=dict(os.environ,TMPDIR=str(tmp)),capture_output=True,timeout=120,preexec_fn=limits)
        log=p.stdout+p.stderr;assert len(log)<=64*1024,'COMPILER_LOG_EXCEEDS_DECLARED_LIMIT'
        with(S/'RPP_RAW_COMPILE.log').open('xb')as f:f.write(log)
        assert p.returncode==0,'RAW_RPP_COMPILE_FAILED:'+str(p.returncode)
        assert 0<output.stat().st_size<=320*1024
        assert all(sha(R/name)==h for name,h in pins.items()),'SOURCE_CHANGED_DURING_BUILD'
        assert allocated(S)+allocated(R/'runs/v2183_lossless_capture_stream')<=M,'PREPARATION_ALLOWANCE_EXCEEDED'
        answer.update(passed=True,binary_path=str(output.relative_to(R)),binary_bytes=output.stat().st_size,binary_sha256=sha(output),new_bridge_source_sha256=sha(target),empty_compiler_tmp=not any(tmp.iterdir()))
    except BaseException as e:answer['first_error']=repr(e)
    finally:
        answer.update(closed=True,wall_s=time.monotonic()-start,created_at=datetime.datetime.now().astimezone().isoformat())
        with(S/'RPP_RAW_BUILD_RESULT.json').open('x')as f:f.write(json.dumps(answer,indent=2)+'\n')
    print(json.dumps({k:v for k,v in answer.items()if k not in ['command','source_pins','declared_replacements']}))
    return 0 if answer['passed']else 1

if __name__=='__main__':raise SystemExit(main())
