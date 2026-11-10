"""Zero-model finalization after a two-archive verifier temp-name collision. No push retry."""
import fcntl,importlib.util,json,shutil,tempfile,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v975_daytime_delivery';REC=R/'records/nav2_v974_20261110';D=R/'runs/v976_saved_recovery_diagnosis'
spec=importlib.util.spec_from_file_location('v976_day_delivery',R/'experiments/v975_daytime_closure/deliver.py');delivery=importlib.util.module_from_spec(spec);spec.loader.exec_module(delivery)
t=delivery.transport;sha=t.sha;dump=t.dump;gh=t.gh

def main():
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 assert json.loads((REC/'COMPLETION.json').read_text())['closed']
 with(D/'TRANSPORT_RECOVERY_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0,integrations=0,no_git_push_retry=True),f)
 sync=json.loads((REC/'GIT_SYNC_RESULT.json').read_text());assert sync['remote_head_verified']
 index=json.loads((REC/'RECORD_INDEX.json').read_text());downloaded=O/'readback';verified=[]
 assert sha(downloaded/'RECORD_INDEX.json')==sha(REC/'RECORD_INDEX.json')
 for group in index['archives']:
  with tempfile.TemporaryDirectory(prefix='independent_group_',dir=downloaded)as folder:
   view=Path(folder)
   for name in[group['group']+'.INVENTORY.json',*[x['name']for x in group['parts']]]:(view/name).symlink_to(downloaded/name)
   t.shared_verifier()(view,dict(index,archives=[group]))
   verified.append(dict(group=group['group'],archive_sha256=group['archive_sha256'],source_files=group['source_files'],all_part_and_decompressed_member_sha_verified=True))
 receipt=dict(passed=True,models=0,integrations=0,original_failure='Shared verifier reused combined.tar.zst with exclusive create for two archive groups; first group verified then second raised FileExistsError. Original code/archive/error retained.',resolution='Each unchanged downloaded archive independently verified in a fresh temporary directory. No archive or inventory overwritten.',groups=verified,git_push_attempts=1,no_push_or_model_retry=True)
 dump(REC/'TRANSPORT_RECOVERY.json',receipt)
 (D/'ORIGINAL_CLOSE.console').write_bytes((R/'runs/v974_daytime_binding_gate/close.console').read_bytes())
 # Supplement contains only saved diagnostics, their code and explicit next-gate scope.
 pack=t.packer();pack.OUT=D/'supplement';pack.OUT.mkdir(exist_ok=False)
 files=[p for p in D.iterdir()if p.is_file()]+[p for p in(R/'experiments/v976_saved_recovery_diagnosis').iterdir()if p.is_file()]+[REC/'TRANSPORT_RECOVERY.json']
 record=pack.archive('v976-saved-reference-diagnosis',files)
 supplemental_index=dict(repository=index['repository'],release_tag=index['release_tag'],models=0,integrations=0,scientific_outcome='V974_NOT_PASSED_UNCHANGED',archives=[{k:v for k,v in record.items()if k!='files'}])
 supindex=REC/'V976_SUPPLEMENT_INDEX.json';dump(supindex,supplemental_index)
 assets=[p for p in pack.OUT.iterdir()if p.is_file()]+[supindex,REC/'TRANSPORT_RECOVERY.json']
 gh(['release','upload',delivery.TAG,*map(str,assets)])
 supread=D/'supplement_readback';supread.mkdir(exist_ok=False)
 for p in assets:gh(['release','download',delivery.TAG,'--pattern',p.name,'--dir',str(supread)]);assert sha(p)==sha(supread/p.name)
 t.shared_verifier()(supread,supplemental_index)
 gh(['release','edit',delivery.TAG,'--draft=false'])
 dump(REC/'REMOTE_VERIFIED.json',dict(passed=True,source_commit=sync['commit'],all_asset_and_decompressed_member_sha_verified=True,supplement_verified=True,release_url=index['release_url'],models=0))
 for p in[REC/'GIT_SYNC_RESULT.json',REC/'REMOTE_VERIFIED.json']:t.upload_receipt(p,downloaded)
 catalog={}
 for group in index['archives']:
  inv=json.loads((downloaded/(group['group']+'.INVENTORY.json')).read_text());catalog.update({x['path']:x for x in inv['files']})
 catalog.update({x['path']:x for x in json.loads((REC/'EXCLUDED_REBUILDABLE_CACHE.json').read_text())['files']})
 for folder in delivery.FOLDERS:
  for p in t.packer().walk(folder):
   if delivery.active(p):continue
   row=catalog[str(p.relative_to(R))];assert p.stat().st_size==row['bytes']and sha(p)==row['sha256']
 removed=[];total=0
 for folder in[*delivery.FOLDERS,downloaded,O/'cloud',pack.OUT,supread]:
  if not folder.exists():continue
  assert folder.resolve().is_relative_to(R/'runs')and not folder.is_symlink();size=0
  if folder==R/'runs/v974_daytime_binding_gate':
   for p in list(folder.iterdir()):
    if delivery.active(p):continue
    if p.is_symlink():p.unlink()
    elif p.is_dir():size+=sum(q.stat().st_size for q in t.packer().walk(p));shutil.rmtree(p)
    else:size+=p.stat().st_size;p.unlink()
  else:size=sum(p.stat().st_size for p in t.packer().walk(folder));shutil.rmtree(folder)
  removed.append(dict(path=str(folder.relative_to(R)),bytes=size));total+=size
 dump(REC/'CLEANUP_RESULT.json',dict(deleted_bytes=total,removed=removed,all_remote_member_sha_verified_before_cleanup=True,models=0))
 upload=D/'receipt_readback';upload.mkdir(exist_ok=False);t.upload_receipt(REC/'CLEANUP_RESULT.json',upload)
 dump(REC/'FINALIZED.json',dict(closed=True,scientific_outcome='NOT_PASSED',remote_verified=True,necessary_raw_cleaned=True,all_source_and_member_sha_verified=True,supplement_verified=True,release_url=index['release_url'],models=0))
 t.upload_receipt(REC/'FINALIZED.json',upload);shutil.rmtree(upload)
 print(json.dumps(dict(finalized=True,scientific_outcome='NOT_PASSED',deleted_bytes=total,release_url=index['release_url'],new_models=0)),flush=True)
if __name__=='__main__':main()
