"""First actual transport after failed 5s ref, using previously verified immutable commit; no second ref/push."""
import hashlib,importlib.util,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1743_phase03_pair/phase_03__full';HEAD='fc909e0265df480392dc9f2e021f74973c382a7d'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 os.sched_setaffinity(0,{5});assert read(O/'SYNC_RESULT.json')['error']=='BOUNDED_REF_TIMEOUT'and not read(O/'SYNC_RESULT.json')['remote_verified']
 assert not(O/'remote_delivery').exists()and not(O/'IMMUTABLE_SOURCE_RECOVERY_CLAIM.json').exists()
 prior=R/'runs/v1743_phase03_pair/phase_03__no_onward';sync=read(prior/'SYNC_RESULT.json');remote=read(prior/'FULL_REMOTE_VERIFIED.json');assert sync['remote_verified']and sync['head']==HEAD and remote['passed']and remote['source_commit']==HEAD and remote['every_member_SHA_and_link_text']
 source=R/'runs/v1649_error_stop_sensor_capture';recovery=read(source/'CURRENT_SOURCE_REMOTE_RECOVERY.json');proofpath=R/recovery['full_remote_proof_path'];assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and sha(proofpath)==recovery['full_remote_proof_sha256']and read(proofpath)['source_commit']==HEAD
 raw=subprocess.check_output(['git','cat-file','commit',HEAD],cwd=R,timeout=5);assert hashlib.sha1(b'commit '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==HEAD
 paths=[O/'SYNC_RESULT.json',prior/'SYNC_RESULT.json',prior/'FULL_REMOTE_VERIFIED.json',source/'CURRENT_SOURCE_REMOTE_RECOVERY.json',proofpath,C/'deliver_verified_commit.py']
 proof=dict(passed=True,head=HEAD,remote_verified=True,verification_kind='PREVIOUS_ACTUAL_REMOTE_IMMUTABLE_SOURCE_COMMIT_PLUS_LOCAL_GIT_OBJECT_SHA1',original_5s_ref_failed_and_unchanged=True,new_network_ref_calls=0,push_executed=False,archive_resealed=False,old_delivery_restarted=False,first_transport_not_yet_claimed=True,source_paths_SHA256={str(p.relative_to(R)):sha(p)for p in paths},late_outside_sealed_archive=True,models=0,unix=time.time())
 (O/'IMMUTABLE_SOURCE_RECOVERY_CLAIM.json').write_text(json.dumps(dict(unix=time.time(),no_second_ref_or_push=True,models=0),indent=2)+'\n');(O/'IMMUTABLE_SOURCE_RECOVERY.json').write_text(json.dumps(proof,indent=2)+'\n')
 spec=importlib.util.spec_from_file_location('v1743_first_transport_original',C/'deliver.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 original_read=m.h.read
 def read_with_separate_proof(path):
  return proof if Path(path)==O/'SYNC_RESULT.json'else original_read(path)
 m.h.read=read_with_separate_proof;m.deliver()
 # Explicit late assets are not claimed as old archive members.
 release=m.h.read(m.h.O/'RELEASE.json');known=m.h.assets(release);late=[C/'deliver_verified_commit.py',O/'IMMUTABLE_SOURCE_RECOVERY.json'];rows=[]
 for path in late:
  m.guard();m.h.ensure_uploaded(path,known);known=m.h.assets(release)
  target=m.h.O/('late-readback-'+path.name);m.h.download(target,known[path.name]);assert sha(target)==sha(path);target.unlink();rows.append(dict(path=str(path.relative_to(R)),sha256=sha(path),bytes=path.stat().st_size))
 result=dict(passed=True,late_assets_actualremote_SHA_verified=True,files=rows,old_archive_unchanged=True,original_failed_sync_unchanged=True,source_commit=HEAD,models=0)
 (O/'LATE_HELPER_REMOTE_VERIFIED.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
