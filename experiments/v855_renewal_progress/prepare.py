"""Exercise actual scheduler boundaries and freeze every source before models."""
import ast,fcntl,hashlib,os,sys,time
from common import *

class Boundary(BaseException):pass


def main():
    assert Path(sys.argv[0]).is_absolute();assert read(ROOT/'QUALIFICATION.json')['passed']and read(ROOT/'OUTPUT_QUALIFICATION.json')['passed']and read(ROOT/'REVISION_QUALIFICATION.json')['passed']and read(ROOT/'RENEWAL_AUDITOR_QUALIFICATION.json')['passed']
    assert time.time()+1800<DEADLINE and read(ROOT/'AUTHORIZATION.json')['absolute_model_deadline_unix']==DEADLINE
    for folder in [C,W]:
        for p in folder.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    import engine
    calls=[];phase=ROOT/'scheduler_qualification';old_unchanged=engine.unchanged;old_popen=engine.subprocess.Popen
    engine.unchanged=lambda:None
    def block(command,**kwargs):calls.append(list(map(str,command)));raise Boundary()
    engine.subprocess.Popen=block
    try:
        stage=engine.Stage('scheduler_qualification',64)
        try:stage.t0(tasks()[0])
        except Boundary:pass
        else:raise AssertionError('ACTUAL_FIRST_T0_PROCESS_BOUNDARY_NOT_REACHED')
        assert len(calls)==1 and calls[0][0]==str(R/'run_phase.sh')and calls[0][1]==str(W.relative_to(R)/'run_static.py')and'--feasibility-only'in calls[0]
    finally:engine.unchanged=old_unchanged;engine.subprocess.Popen=old_popen
    # Real master callsite stopped immediately before the physical component;
    # patching Popen occurs in this process only, no worker/model is imported.
    tree=ast.parse((C/'start.py').read_text());assert any(isinstance(n,ast.Constant)and n.value=='component.py'for n in ast.walk(tree))
    assert model_fits(DEADLINE,DEADLINE-100,90)and not model_fits(DEADLINE,DEADLINE-90,90)
    assert(R/'REVIEW_PENDING').exists()
    with(R/'runs/v648_static_unknown/execution.lock').open('rb')as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    unchanged_old=read(R/'experiments/v851_profile_output_continuation/CANDIDATE_FREEZE.json')['files'];assert all(sha(R/p)==h for p,h in unchanged_old.items())
    changes={p.name:dict(sha256=sha(p),old_sha256=sha(R/'experiments/v851_profile_output_worker'/p.name)if(R/'experiments/v851_profile_output_worker'/p.name).exists()else None)for p in W.iterdir()if p.is_file()and(not(R/'experiments/v851_profile_output_worker'/p.name).exists()or sha(p)!=sha(R/'experiments/v851_profile_output_worker'/p.name))};dump(C/'WORKER_CHANGES.json',changes)
    check=dict(passed=True,actual_scheduler_first_t0_boundary=True,commands=calls,deadline_boundary_positive_negative=True,source_syntax=True,old4104_input_sha_exact=True,review_pending_original=True,execution_lock_idle=True,models=0,integrations=0,unattended_variants=VARIANTS,never_automatically_new24=True);dump(ROOT/'OPERATIONS_CHECK.json',check)
    files=unchanged_old.copy()
    revision_inputs=read(ROOT/'REVISION_INPUT_SHA.json');assert all(sha(R/p)==h for p,h in revision_inputs.items());files.update(revision_inputs)
    for folder in [C,W]:
        for p in folder.iterdir():
            if p.is_file()and p.suffix in['.py','.md','.json']and p.name!='CANDIDATE_FREEZE.json':files[str(p.relative_to(R))]=sha(p)
    for p in [ROOT/'AUTHORIZATION.json',ROOT/'QUALIFICATION.json',ROOT/'OUTPUT_QUALIFICATION.json',ROOT/'OPERATIONS_CHECK.json',ROOT/'REVISION_QUALIFICATION.json',ROOT/'SAVED_CAUSE_REPRODUCTION.json',ROOT/'RENEWAL_AUDITOR_QUALIFICATION.json',ROOT/'REVISION_INPUT_SHA.json']:files[str(p.relative_to(R))]=sha(p)
    # Exact old inputs for fixed component and backend replay are frozen too.
    for pairname in ['runs/v851_profile_output_worker/v851_main_slot01/paired']:
        pair=R/pairname
        for p in [pair/'scene_model.mjb',pair/'STATIC_PROTOCOL.json',pair/'DYNAMIC_PROTOCOL.json',pair/'INITIALIZATION_PROVENANCE.json',pair/'geometry_memory/dynamic_native.jsonl.gz',pair/'geometry_memory/sensor_packets.jsonl.gz',pair/'geometry_memory/trace.json',*list((pair/'geometry_memory').glob('planning_*.json')),pair/'geometry_memory/progress_certificates/certificate_0399.json.gz',pair/'geometry_memory/progress_certificates/certificate_0303.json.gz']:files[str(p.relative_to(R))]=sha(p)
    dump(C/'CANDIDATE_FREEZE.json',dict(files=files,frozen_unix=time.time(),absolute_model_deadline_unix=DEADLINE,variants=VARIANTS,tasks=tasks(),scientific_change='Adaptive64-or328 complete-progress execution, actual456-native renewal witness, maximal full progress within original library, causal norm renewal soft cost6; original safety retained',navigation_public_cap=2400,new24=0,training=0))
    dump(ROOT/'PREPARED.json',dict(passed=True,freeze_sha256=sha(C/'CANDIDATE_FREEZE.json'),files=len(files),models=0,integrations=0,root_deadline=DEADLINE));unchanged();print(read(ROOT/'PREPARED.json'),flush=True)


if __name__=='__main__':main()
