"""One zero-model proof restoration before the first actual fixed24 launch."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name;N=R/'runs/v1281_partial_reconnection_fixed24'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
    assert not(O/'STARTED.json').exists()and not(N/'ROUND_WINDOW.json').exists()and not(N/'LAUNCH_RECEIPT.json').exists(),'ONE_ENTRY_NO_MODEL_RESTART'
    assert time.time()+10800<1794963600. and read(R/'runs/v1280_slot24_repeat_clock/FINALIZED.json')['slot24_main_repeat_development_passed']
    assert read(N/'QUALIFICATION.json')['passed']and read(N/'ISOLATED_QUALIFICATION.json')['passed']and read(N/'FROZEN_READY.json')['passed']
    assert read(R/'CURRENT_EXPERIMENT.json')['active_run']is None
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    dump(O/'STARTED.json',dict(models=0,physical_native=0,restoration_only=True,previous_start_failed_before_root_lock=True))
    source=R/'runs/v1275_time_window_fixed24/NS_SOURCE_QUALIFICATION.json';target=N/source.name
    assert not target.exists(),'DO_NOT_OVERWRITE_PROOF'
    original=read(source);assert original['passed']and original['old_success_branch_source_exact']and original['physical_native']==0
    original_code=R/'experiments/v1275_time_window_fixed24';newcode=R/'experiments/v1281_partial_reconnection_fixed24'
    for name in ['ns_live.py','ns_audit.py','ns_admission_audit.py']:
        assert(newcode/name).read_bytes()==(original_code/name).read_bytes(),'NS_SOURCE_CHANGED'
    target.write_bytes(source.read_bytes());assert sha(source)==sha(target)
    # The scientific and operation freeze is left byte-for-byte untouched.
    frozen=read(newcode/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
    for name in ['QUALIFICATION.json','ISOLATED_QUALIFICATION.json','NS_SOURCE_QUALIFICATION.json','EW_SOURCE_QUALIFICATION.json']:
        assert read(N/name)['passed'],'MISSING_REAL_LAUNCH_PROOF '+name
    supplement={str(p.relative_to(R)):sha(p)for p in [Path(__file__),source,target,newcode/'SOURCE_FREEZE.json',N/'FROZEN_READY.json',N/'QUALIFICATION.json',N/'ISOLATED_QUALIFICATION.json']}
    dump(O/'PRE_MODEL_SUPPLEMENTAL_FREEZE.json',dict(passed=True,files=supplement,models=0,physical_native=0,science_and_tasks_unchanged=True,old_relay_error_preserved=True))
    with(O/'start.console').open('x')as log:
        p=subprocess.run([sys.executable,'-B',str(newcode/'start.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=60)
    dump(O/'COMPLETION.json',dict(closed=True,passed=p.returncode==0,start_returncode=p.returncode,entry_models=0,entry_physical_native=0,
        confirmation_started=(N/'LAUNCH_RECEIPT.json').exists(),receipt=read(N/'LAUNCH_RECEIPT.json')if(N/'LAUNCH_RECEIPT.json').exists()else None,no_retry=True))
    assert p.returncode==0,'ENTRY_REJECTED_NO_RETRY'
    print((O/'COMPLETION.json').read_text())
if __name__=='__main__':main()
