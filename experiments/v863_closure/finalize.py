"""Publish the post-cleanup metadata receipt; does not push source or run models."""
import hashlib,json,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];REC=R/'records/nav2_v863_execution_20261107';GH=R/'tools/phase_storage_20261107/vendor/gh';TAG='phase-nav2-v862-v863-20261107'
def read(p):return json.loads(p.read_text())
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
 assert read(REC/'CLEANUP_RESULT.json')['passed']and read(REC/'PUBLIC_RESTORE_QUALIFICATION.json')['passed']
 sync=read(REC/'SOURCE_SYNC_RESULT.json');assert sync['remote_head_verified']
 final=dict(status='CLOSED_PUBLIC_EVIDENCE_SOURCE_VERIFIED_AND_LOCAL_TEMP_CLEANED',scientific_outcome='ONE_STATIC_RPP_DEVELOPMENT_ROUTE_PASSED',v862_original_functional_failure_preserved=True,actual_native=4569,replay_native=4569,complete_navigation_repeats=0,other_static_routes=0,dynamic_navigation=0,new24=0,training=0,real_robot=0,source_commit=sync['source_commit'],source_remote_head_verified=True,public_release='https://github.com/frank8763/phase-/releases/tag/'+TAG,public_member_restore_verified=True,cleanup_bytes=read(REC/'CLEANUP_RESULT.json')['total_bytes'],review_pending_original_restored=True,execution_lock_idle=True,no_automatic_additional_models=True,stopping_reason='Explicitly approved one RPP static candidate completed; larger scope not authorized by this one-task receipt',at=time.time())
 dump(REC/'FINALIZED.json',final)
 p=R/'CURRENT_EXPERIMENT.json';d=read(p);d['v863_rpp_static'].update(storage_status='PUBLIC_RELEASE_VERIFIED_RESTORED_AND_TEMP_CLEANED',release_url=final['public_release'],finalized='records/nav2_v863_execution_20261107/FINALIZED.json');dump(p,d)
 post=dict(format_version=1,kind='POST_CLOSURE_ZERO_MODEL_RECEIPT',finalized=final,small_records={},closure_sources={},current_experiment_snapshot=d,root_deadline_unix=1794062038.6753576,no_second_source_push=True)
 for f in sorted(REC.rglob('*')):
  if not f.is_file()or f.name.startswith('POST_CLOSURE_')or f.name=='CLEANUP_FILES.jsonl.gz':continue
  data=f.read_bytes();post['small_records'][str(f.relative_to(R))]=dict(sha256=hashlib.sha256(data).hexdigest(),text=data.decode())
 for f in sorted((R/'experiments/v863_closure').glob('*.py')):
  data=f.read_bytes();post['closure_sources'][str(f.relative_to(R))]=dict(sha256=hashlib.sha256(data).hexdigest(),text=data.decode())
 receipt=REC/'POST_CLOSURE_RECEIPT.json';assert not receipt.exists();dump(receipt,post)
 subprocess.run([str(GH),'release','upload',TAG,str(receipt),'--repo','frank8763/phase-'],cwd=R,check=True,timeout=60)
 data=subprocess.run([str(GH),'api',f'repos/frank8763/phase-/releases/437593650/assets?per_page=100&phase_read={time.time_ns()}'],capture_output=True,text=True,check=True,timeout=20).stdout
 asset=next(x for x in json.loads(data)if x['name']==receipt.name);h=hashlib.sha256(receipt.read_bytes()).hexdigest();assert asset['digest']=='sha256:'+h and asset['size']==receipt.stat().st_size
 downloaded=subprocess.run([str(GH),'release','download',TAG,'--repo','frank8763/phase-','--pattern',receipt.name,'--output','-'],cwd=R,capture_output=True,check=True,timeout=60).stdout
 assert hashlib.sha256(downloaded).hexdigest()==h
 verification=dict(passed=True,url=asset['browser_download_url'],sha256=h,bytes=len(downloaded),server_digest_matched=True,download_sha_verified=True,includes_post_cleanup_records_and_new_closure_scripts=True,source_pushes_this_round=1,at=time.time());dump(REC/'POST_CLOSURE_VERIFIED.json',verification);print(json.dumps(verification),flush=True)
if __name__=='__main__':main()
