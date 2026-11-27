"""Complete finite source/capacity/read-only CLI checks before SOURCE_ONCE."""
import ast,datetime,fcntl,gzip,hashlib,importlib.util,io,json,os,subprocess,sys,tarfile,time
from pathlib import Path
from context import R,C,S,sha,read,put,source_files,REVIEW_SHA
from budget import check
from fixture import build,strict_domain,TWIST
PARENT=R/'runs/v2180_fresh_projection_component'
EXTRA=[
 'experiments/v2182_fairness_mechanism_diagnosis/dwa_shared_path.py',
 'experiments/v2182_fairness_mechanism_diagnosis/rpp_raw_core_bridge.cpp',
 'experiments/v2182_fairness_mechanism_diagnosis/build_raw_rpp.py',
 'experiments/v2182_fairness_mechanism_diagnosis/nominal_frontend.py',
 'experiments/v2182_fairness_mechanism_diagnosis/check_nominal_frontend.py',
 'runs/v2182_fairness_mechanism_diagnosis/libphase_rpp_raw_core_abi2.so',
 'runs/v2182_fairness_mechanism_diagnosis/RPP_RAW_BUILD_RESULT.json',
 'runs/v2182_fairness_mechanism_diagnosis/NOMINAL_FRONTEND_GEOMETRY.json',
 'runs/v1978_rpp_first_common_round/actual/cycle_0000_origin.json']
REQUIRED={'budget.py','context.py','entry.py','fixture.py','numeric.py','owner.py','readiness.py','qualify.py','recovery.py','rpp_worker.py','run_phase.py','check_software.py','PROTOCOL.md'}
def candidate():
    assert REQUIRED<=set(p.name for p in C.iterdir())
    inherited=source_files(PARENT/'SOURCE_FREEZE.json');assert len(inherited)==29655
    paths=[p for p in C.iterdir()if p.suffix in {'.py','.md'}]+[R/n for n in EXTRA]
    delta={str(p.relative_to(R)):sha(p)for p in paths}
    assert not(set(delta)&set(inherited)),'NEW_SOURCE_CANNOT_OVERRIDE_INHERITED_PATH'
    return inherited,delta

def inherited_chain():
    p=PARENT/'CURRENT_SOURCE_REMOTE_RECOVERY.json';x=read(p);assert x['passed']and x['all_frozen_members_remote_chain_covered']
    for key in ['index','full_remote_proof','source_sync_result']:assert sha(R/x[key+'_path'])==x[key+'_sha256']
    return dict(inherited=[dict(freeze_path=str((PARENT/'SOURCE_FREEZE.json').relative_to(R)),freeze_sha256=sha(PARENT/'SOURCE_FREEZE.json'),recovery_path=str(p.relative_to(R)),recovery_sha256=sha(p),source_members=29655)],new_source_not_in_old_commit=True)

def future_metadata(delta,ready):
    freeze=dict(schema=1,inherit_freeze_path=str((PARENT/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(PARENT/'SOURCE_FREEZE.json'),files=delta,scope='FIXED_SAVED_COMMON_INPUT_RAW_CONTROLLER_MATH',original_plant_allowed=False)
    qual=dict(passed=True,source_members=29655+len(delta),source_ready_sha256='0'*64,source_freeze_sha256='0'*64,git_source_files=sorted(n for n in delta if n.startswith('experiments/')),explicit_algorithm_DLL_loads_FFI_constructors_queries_models_physics=0,scope='SOURCE_ONLY_NOT_NUMERICAL_PERMISSION')
    sync=dict(head='0'*40,source_freeze_sha256='0'*64,remote_verified=True,push_attempted=True,push_returned=True,push_returncode=0,ref_returncode=0,ref_stdout_sha256='0'*64,all_Git_members_actual_remote_SHA=True,actual_remote_Git_members_SHA256={n:delta[n]for n in qual['git_source_files']})
    return {'SOURCE_ONCE.json':dict(source_only=True,started_at='2026-11-28T05:30:00+08:00'),'SOURCE_OUTER_CLOSED.json':dict(closed=True,passed=True,source_only=True,numerical_admission=False,original_REVIEW_exact=True,algorithm_queries_DLL_FFI_models_physics=0),'SOURCE_FREEZE.json':freeze,'SOURCE_QUALIFICATION.json':qual,'SOURCE_INHERITED_CHAINS.json':inherited_chain(),'SOURCE_SYNC_RESULT.json':sync,'SOURCE_READY_PREFLIGHT.json':ready}

def packed_forecast(delta,ready):
    future=future_metadata(delta,ready);files={str(S.relative_to(R)/n):json.dumps(v,sort_keys=True,separators=(',',':')).encode()+b'\n'for n,v in future.items()}
    git_members=set(future['SOURCE_QUALIFICATION.json']['git_source_files'])
    files.update({n:(R/n).read_bytes()for n in delta if n not in git_members})
    for n in ['STORAGE_PRECHARGE.json','INNER_STAGE_ALLOCATION_AMENDMENT.json','READINESS_ARCHIVE_CAPACITY_FAILURE.json','SOURCE_READY_PREFLIGHT_01_SUPERSEDED_BY_REVIEW.json']:files[str((S/n).relative_to(R))]=(S/n).read_bytes()
    stream=io.BytesIO()
    with gzip.GzipFile(fileobj=stream,mode='wb',compresslevel=9,mtime=0)as z,tarfile.open(fileobj=z,mode='w|')as tar:
        for n,data in sorted(files.items()):
            m=tarfile.TarInfo(n);m.size=len(data);m.mode=0o600;m.mtime=0;tar.addfile(m,io.BytesIO(data))
    return len(stream.getvalue()),len(files)

def main():
    assert os.sched_getaffinity(0)=={5};check('preparation')
    assert not any((S/n).exists()for n in ['SOURCE_ONCE.json','SOURCE_READY_PREFLIGHT.json','NUMERICAL_ADMISSION.json','RUNTIME_ONCE.json'])
    locks=[]
    for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
        f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
    assert sha(R/'REVIEW_PENDING')==REVIEW_SHA and not Path('/proc/113868').exists()
    started=time.monotonic();inherited,delta=candidate()
    for n,h in {**inherited,**delta}.items():assert sha(R/n)==h,'SOURCE_CHANGED:'+n
    for p in C.glob('*.py'):ast.parse(p.read_text())
    proof_script=C/'check_software.py';p=subprocess.run(['taskset','-c','0','nice','-n','19','/usr/bin/python3','-B',str(proof_script)],cwd=R,capture_output=True,timeout=120,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'))
    assert len(p.stdout)+len(p.stderr)<=16*1024 and p.returncode==0,repr((p.returncode,p.stdout[-2000:],p.stderr[-2000:]))
    software=json.loads(p.stdout);assert software['passed']and software['algorithm_queries_DLL_FFI_models_physics']==0
    # Real refusal in BOTH runtime namespaces, without fabricated admission.
    spec=importlib.util.spec_from_file_location('v2184_ready_Phase_namespace',R/'tools/isolate.py');phase=importlib.util.module_from_spec(spec);spec.loader.exec_module(phase)
    spec=importlib.util.spec_from_file_location('v2184_ready_ROS_namespace',R/'experiments/v856_nav2_foundation/ros_environment.py');ros=importlib.util.module_from_spec(spec);spec.loader.exec_module(ros)
    commands=[phase.command(C/'entry.py',writable=False),ros.command(['/usr/bin/python3.12','-I','-B','-S',str(C/'entry.py')])]
    cli=[]
    for cmd in commands:
        if '--bind'in cmd:
            j=cmd.index('--bind');assert cmd[j+1:j+3]==[str(R/'runs'),str(R/'runs')];cmd[j]='--ro-bind'
        q=subprocess.run(cmd,cwd=R,env=dict(ros.environment(),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),capture_output=True,timeout=20)
        assert len(q.stdout)+len(q.stderr)<=16*1024 and q.returncode==77
        v=json.loads(q.stdout);assert v['refused_before_numerical_import']and v['algorithm_loads_constructors_queries_models_physics']==0
        cli.append(dict(returncode=77,stdout_sha256=hashlib.sha256(q.stdout).hexdigest(),stderr_sha256=hashlib.sha256(q.stderr).hexdigest(),command_sha256=hashlib.sha256(json.dumps(cmd).encode()).hexdigest()))
    from recovery import GH
    tool_pin=dict(path=str(GH.relative_to(R)),sha256=sha(GH),bytes=GH.stat().st_size,role='INSTALLED_IO_TOOL_NOT_SCIENTIFIC_NUMERIC_SOURCE',binary_in_source_archive=False,environment_dependency_not_claimed_remote_recoverable=True)
    ready=dict(passed=True,scope='FINITE_PRE_SOURCE_SOFTWARE_AND_CAPACITY',candidate_files=delta,inherited_source_members_fresh_SHA=29655,inherited_chains=inherited_chain(),software=software,read_only_namespace_refusals=cli,IO_tool=tool_pin,algorithm_queries_DLL_FFI_models_physics=0,numerical_authorized=False,created_at=datetime.datetime.now().astimezone().isoformat())
    size,members=packed_forecast(delta,ready);ready.update(source_archive_forecast_bytes=size,forecast_members=members,archive_reserved_margin_bytes=8192)
    size2,_=packed_forecast(delta,ready);assert size2+8192<=96*1024,'SOURCE_EXACT_FORECAST_PLUS8K_MARGIN_EXCEEDS96K'
    # Forecast is necessary, not a substitute for exact post-freeze archive check.
    ready.update(source_archive_final_forecast_bytes=size2,wall_s=time.monotonic()-started)
    assert all(sha(R/n)==h for n,h in delta.items());put(S/'SOURCE_READY_PREFLIGHT.json',ready);check('source')
    print(json.dumps(dict(passed=True,delta_members=len(delta),source_archive_forecast_bytes=size2,source_or_numeric_claims=0,software=software['counts'])));return 0
if __name__=='__main__':raise SystemExit(main())
