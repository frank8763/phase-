"""Finite read-only verification and new zero-model metadata closure only."""
import fcntl,hashlib,importlib.abc,json,signal,sys,time
from pathlib import Path

class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('OFFLINE_ONLY_USER_AUTHORIZATION')
sys.meta_path.insert(0,NoModels())
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OUT=R/'runs/v852_maneuver_contract'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('OFFLINE_CLOSURE_180S')));signal.alarm(180)
    target=OUT/'OFFLINE_REVIEW.json';assert not target.exists()
    guard=R/'REVIEW_PENDING';guard_hash=sha(guard);assert guard_hash=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    old=json.loads((R/'experiments/v851_profile_output_continuation/CANDIDATE_FREEZE.json').read_text());assert len(old['files'])==4104
    for path,value in old['files'].items():assert sha(R/path)==value,('OLD_FROZEN_INPUT_CHANGED',path)
    inputs={}
    for manifest in [R/'runs/v851_outcome_analysis/INPUT_SHA256.json',R/'runs/v851_outcome_analysis/extra/INPUT_SHA256.json',OUT/'qualification_final02/INPUT_SHA256.json']:
        values=json.loads(manifest.read_text())
        for path,value in values.items():
            assert sha(R/path)==value,('INPUT_CHANGED',path)
            if path in inputs:assert inputs[path]==value
            inputs[path]=value
    qualifications=[]
    for relative in ['qualification_final02/QUALIFICATION.json','coordinator_final01/COORDINATOR_QUALIFICATION.json','boundaries_final01/QUALIFICATION.json']:
        p=OUT/relative;v=json.loads(p.read_text());assert v['passed']and v['new_models']==v['new_integrations']==0
        for name,value in v.get('source_sha256',{}).items():assert sha(C/name)==value
        qualifications.append(dict(path=str(p.relative_to(R)),sha256=sha(p),status=v['status']))
    with(R/'runs/v648_static_unknown/execution.lock').open('rb')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert sha(guard)==guard_hash
    assert not any(n=='mujoco'or n.startswith('mujoco.')for n in sys.modules)
    sources={str(p.relative_to(R)):sha(p)for p in C.iterdir()if p.is_file()}
    value=dict(status='OFFLINE_CORE_QUALIFIED_PHYSICAL_INTEGRATION_PENDING',closed=True,authorization='User: 先完成修订和资格，不启动模型; subsequent 继续 preserves that restriction.',checked_unix=time.time(),qualifications=qualifications,old_frozen_inputs_verified=4104,old_frozen_manifest_sha256=sha(R/'experiments/v851_profile_output_continuation/CANDIDATE_FREEZE.json'),saved_input_files_verified=len(inputs),review_pending_original_bytes_preserved=True,review_pending_sha256=guard_hash,execution_lock_idle=True,new_models=0,new_integrations=0,new_navigation=0,new_confirmation=0,training_updates=0,physical_worker_integrated=False,native_batch_physics_qualified=False,real_time_qualified=False,no_model_window_created=True,no_background_start=True,no_automatic_restart=True,no_network_sync=True,source_sha256=sources)
    (OUT/'VERIFIED_INPUT_SHA256.json').write_text(json.dumps(inputs,indent=2)+'\n');target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in value.items()if k not in ['source_sha256','qualifications']},ensure_ascii=False))


if __name__=='__main__':main()
