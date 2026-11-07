"""Remove only explicit closed Phase temporary paths after public remote verification."""
import fcntl,hashlib,json,os,shutil,stat,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v856_nav2_foundation';REC=R/'records/nav2_v856_20261107'
def main():
 proof=json.loads((REC/'FULL_REMOTE_VERIFIED.json').read_text());assert proof['passed']and proof['status']=='PUBLIC_RELEASE_AND_SOURCE_REMOTE_VERIFIED'and proof['assets']==9
 assert json.loads((ROOT/'RESTORE_QUALIFICATION.json').read_text())['passed']
 for p in [ROOT/'ROUND_WINDOW.json',ROOT/'entry01/ROUND_WINDOW.json']:assert json.loads(p.read_text())['round_closed']
 assert(R/'REVIEW_PENDING').read_bytes()==(ROOT/'entry01/REVIEW_PENDING.before').read_bytes()
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 # Preserve late operation receipts/logs that were produced after the closed evidence snapshot.
 ops=REC/'operations';ops.mkdir(exist_ok=True)
 for source in [ROOT/'RESTORE_QUALIFICATION.json',ROOT/'cloud/SOURCE_SYNC_RESULT.json',ROOT/'cloud/PUBLIC_REMOTE_VERIFIED.json',ROOT/'cloud/UPLOAD_PREPARATION_NOTE.json',ROOT/'cloud/upload.console',ROOT/'cloud/upload_after_draft_visible.console',ROOT/'cloud/license_upload.console',ROOT/'cloud/source_push.console']:
  if source.exists():shutil.copyfile(source,ops/source.name)
 targets=[ROOT/x for x in ['rootfs','apt','runtime_licenses','restore_qualification','cloud','vehicle_qualification01','entry01/vehicle_qualification01','smoke01','smoke02','smoke03','smoke04','smoke05','RUNTIME_SELECTED.json']]
 inventory=[];allocated=0;logical=0
 for target in targets:
  assert target.is_relative_to(ROOT)and target!=ROOT and not target.is_symlink()
  paths=[target]if target.is_file()else[]
  if target.is_dir():
   for current,dirs,files in os.walk(target,followlinks=False):
    dirs[:]=[x for x in dirs if not(Path(current)/x).is_symlink()]
    paths.extend(Path(current)/x for x in files)
  for p in paths:
   st=p.lstat()
   if stat.S_ISREG(st.st_mode):logical+=st.st_size;allocated+=st.st_blocks*512
  inventory.append(dict(path=str(target.relative_to(R)),existed=target.exists(),reason='remote-verified essential evidence/runtime or rebuildable SDK/APT cache; closed original data retained in Release'))
 receipt=dict(status='CLEANUP_RUNNING',targets=inventory,estimated_logical_bytes=logical,estimated_allocated_bytes=allocated,remote_verified_assets=9,source_commit=proof['source_commit'],release_url=proof['release_url'],stage_accessed=False,model_integrations=0)
 (REC/'CLEANUP_RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n')
 for target in targets:
  if target.is_dir():shutil.rmtree(target)
  elif target.exists():target.unlink()
 receipt.update(status='COMPLETE',completed_unix=time.time(),all_target_paths_absent=all(not p.exists()for p in targets),local_phase_du_bytes=int(subprocess.run(['du','-s','-B1',str(R)],check=True,capture_output=True,text=True).stdout.split()[0]),free_disk_bytes=shutil.disk_usage(R).free)
 (REC/'CLEANUP_RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items()if k!='targets'}),flush=True)
if __name__=='__main__':main()
