"""All finite static/software/byte/authority checks before the one Source claim."""
import ast,datetime,fcntl,hashlib,importlib.util,io,json,os,subprocess,tarfile,gzip,time
from context import R,C,S,PARENT,read,sha,files
from fixture import fixed,RECEIPT,SETUP,EVIDENCE,RESULT,CLOSURE
from budget import check
REQUIRED={'context.py','entry.py','backend.py','budget.py','numeric.py','fixture.py','store.py','owner.py','run_phase.py','profiles.py','check_software.py','recovery.py','readiness.py','qualify.py'}

def candidate():
    assert REQUIRED<=set(p.name for p in C.iterdir())
    parent=files(PARENT/'SOURCE_FREEZE.json');assert len(parent)==29678
    paths=[p for p in C.iterdir()if p.suffix in {'.py','.md'}]
    paths += [R/n for n in [RECEIPT,SETUP,EVIDENCE,RESULT,CLOSURE,'experiments/v2182_fairness_mechanism_diagnosis/closed_math_reservation.py','experiments/v2182_fairness_mechanism_diagnosis/CLOSED_MATH_RESERVATION_SCOPE.md','runs/v2152_weekend_research_program/CLOSED_V2184_PREPARATION_BAND.json']]
    paths += [S/n for n in ['STORAGE_PRECHARGE.json','PRE_SOURCE_SCOPE_AMENDMENT.json','REQUIRED_ARRAY_FORMAT_PREFLIGHT.json']]
    new={}
    for p in paths:
        assert p.is_file()and not p.is_symlink();n=str(p.relative_to(R));h=sha(p)
        if n in parent:assert parent[n]==h
        else:new[n]=h
    return parent,new

def metadata(new,ready):
    freeze=dict(schema=1,inherit_freeze_path=str((PARENT/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(PARENT/'SOURCE_FREEZE.json'),files=new,scope='FIXED_RAW_OUTPUT_ORIGINAL_RESPONSE_MATH',original_plant_allowed=False)
    qual=dict(passed=True,source_members=29678+len(new),source_freeze_sha256='0'*64,source_ready_sha256='0'*64,git_source_files=sorted(n for n in new if n.startswith('experiments/')),original_model_imports_constructors_steps_Source_qualification=0)
    sync=dict(head='0'*40,passed=True,push_attempted=True,push_returned=True,ref_verified=True,actual_remote_Git_members_SHA256={n:new[n]for n in qual['git_source_files']})
    return dict(SOURCE_FREEZE=freeze,SOURCE_QUALIFICATION=qual,SOURCE_SYNC=sync,SOURCE_READY=ready,SOURCE_ONCE=dict(source_only=True,created_at='2026-11-28T07:00:00+08:00'))

def forecast(new,ready):
    future=metadata(new,ready);git=set(future['SOURCE_QUALIFICATION']['git_source_files'])
    rows={n:(R/n).read_bytes()for n in new if n not in git}
    rows.update({str((S/(n+'.json')).relative_to(R)):json.dumps(v,sort_keys=True,separators=(',',':')).encode()+b'\n'for n,v in future.items()})
    for n in ['STORAGE_PRECHARGE.json','PRE_SOURCE_SCOPE_AMENDMENT.json','REQUIRED_ARRAY_FORMAT_PREFLIGHT.json','ARRAY_FORMAT_PREFLIGHT.json']:rows[str((S/n).relative_to(R))]=(S/n).read_bytes()
    stream=io.BytesIO()
    with gzip.GzipFile(fileobj=stream,mode='wb',compresslevel=9,mtime=0)as z,tarfile.open(fileobj=z,mode='w|')as t:
        for n,data in sorted(rows.items()):
            m=tarfile.TarInfo(n);m.size=len(data);m.mode=0o600;m.mtime=0;t.addfile(m,io.BytesIO(data))
    return len(stream.getvalue()),len(rows)

def main():
    assert os.sched_getaffinity(0)=={5}and not any((S/n).exists()for n in ['SOURCE_READY.json','SOURCE_ONCE.json','NUMERICAL_ADMISSION.json'])
    check('preparation');start=time.monotonic();locks=[]
    for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
        f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    parent,new=candidate();source=dict(parent,**new)
    for n,h in source.items():assert sha(R/n)==h,'CURRENT_SOURCE_CHANGED:'+n
    original=read(PARENT/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert original['passed']and original['all_frozen_members_remote_chain_covered']
    assert sha(PARENT/'SOURCE_FREEZE.json')==original['source_freeze_sha256']and sha(PARENT/'SOURCE_FULL_REMOTE_VERIFIED.json')==original['remote_proof_sha256']
    fixed(source)
    software=subprocess.run(['taskset','-c','0','nice','-n','19','/usr/bin/python3','-B',str(C/'check_software.py')],cwd=R,capture_output=True,timeout=120)
    assert software.returncode==0 and len(software.stdout)+len(software.stderr)<=16*1024,repr((software.stdout[-1500:],software.stderr[-1500:]))
    soft=json.loads(software.stdout);assert soft['passed']and soft['original_q_model_imports_constructors_steps']==0
    # Existing full-source response and module aliases are inspected, not loaded.
    from backend import Q,RESPONSE,ALIASES
    witnesses=[Q,RESPONSE,*ALIASES.values(),'experiments/v1159_bounded_steering_load/model.py','experiments/v1151_retained_recovery_qualification/qualify.py','experiments/v1035_signed_timed_input_source/whole_input.py']
    for n in witnesses:assert source[n]==sha(R/n);ast.parse((R/n).read_text())
    assert not any(n in __import__('sys').modules for n in ['numpy','kernel','runtime','model','numeric'])
    sp=importlib.util.spec_from_file_location('v2185_original_readonly_Phase_CLI',R/'tools/isolate.py');phase=importlib.util.module_from_spec(sp);sp.loader.exec_module(phase)
    cmd=phase.command(C/'entry.py',writable=False);cli=subprocess.run(cmd,cwd=R,capture_output=True,timeout=20)
    assert cli.returncode==77 and json.loads(cli.stdout)['refused_before_numerical_import']and not cli.stderr
    from recovery import GH,verify,inventory,packed
    # Actual in-memory archive member/tamper checks, no archive mutation.
    test_rows=inventory([C/'fixture.py',C/'profiles.py']);raw=packed(test_rows);idx=dict(archive_bytes=len(raw),archive_sha256=hashlib.sha256(raw).hexdigest(),files=test_rows);verify(raw,idx)
    bad=bytearray(raw);bad[len(bad)//2]^=1
    try:verify(bytes(bad),idx)
    except AssertionError:pass
    else:raise AssertionError('CORRUPTED_ARCHIVE_ACCEPTED')
    ready=dict(passed=True,scope='SOURCE_READINESS_ONLY_NO_PREDICTOR_OR_PHYSICAL_AUTHORITY',created_at=datetime.datetime.now().astimezone().isoformat(),candidate_files=new,inherited_members_fresh_SHA=29678,parent_recovery_sha256=sha(PARENT/'CURRENT_SOURCE_REMOTE_RECOVERY.json'),software=soft,real_Phase_CLI_refusal=77,real_Phase_CLI_stdout_SHA256=hashlib.sha256(cli.stdout).hexdigest(),exact_uncompressed_array_format_proof_SHA256=sha(S/'REQUIRED_ARRAY_FORMAT_PREFLIGHT.json'),static_original_binding_witness_SHA256={n:source[n]for n in witnesses},actual_analytic_module_import_alias_runtime_not_yet_executed=True,installed_IO_GH_SHA256=sha(GH),installed_IO_tool_not_claimed_archived=True,Source_or_Predictor_model_physics=0,metadata_peak_file_allocation_guard_bytes=112*1024,directory_margin_bytes=16*1024)
    size,count=forecast(new,ready);assert size+16*1024<4*1024**2
    ready.update(source_archive_forecast_bytes=size,forecast_members=count,source_archive_reserved_margin=16*1024,wall_s=time.monotonic()-start)
    raw=json.dumps(ready,sort_keys=True,separators=(',',':')).encode()+b'\n';assert len(raw)<=16*1024
    with(S/'SOURCE_READY.json').open('xb')as f:f.write(raw)
    check('source');print(json.dumps(dict(passed=True,new_members=len(new),source_forecast=size,model_imports_and_queries=0,software_negative_cases=len(soft['negatives']))))
if __name__=='__main__':main()
