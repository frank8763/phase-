"""Remove explicit remote-verified closed experiment caches, never other workspaces."""
import fcntl,json,os,shutil,stat,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v857_assembly_contact';REC=R/'records/v857_20261107'
def main():
 proof=json.loads((REC/'REMOTE_VERIFIED.json').read_text());assert proof['public']and proof['all_server_and_download_sha_verified']and len(proof['assets'])+len(proof['supplement_assets'])==4;assert json.loads((ROOT/'RESTORE_QUALIFICATION.json').read_text())['passed'];assert json.loads((ROOT/'interface01/ROUND_WINDOW.json').read_text())['round_closed'];assert(R/'REVIEW_PENDING').read_bytes()==(ROOT/'interface01/REVIEW_PENDING.before').read_bytes()
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);ops=REC/'operations';ops.mkdir(exist_ok=True)
 for base,names in [(ROOT,['SOURCE_SYNC_RESULT.json','source_push.console','archive.console','publish.console','supplement.console','ORIGINAL_RESTORE.console','INTERFACE_RESTORE.console','RESTORE_QUALIFICATION.json'])]:
  for name in names:
   p=base/name
   if p.exists():shutil.copyfile(p,ops/name)
 targets=[ROOT/'PATCHED_MODEL.mjb',ROOT/'old_replay',ROOT/'cloud',ROOT/'interface01/PATCHED_MODEL.mjb',ROOT/'interface01/old_replay',ROOT/'interface01/same_control_actual']
 old=R/'runs/v856_nav2_foundation'
 for name in ['vehicle_qualification01','entry01/vehicle_qualification01','smoke01','smoke02','smoke03','smoke04','smoke05','apt']:targets.append(old/name)
 # V856 restored inputs are covered by its already public, server/download-verified Release.
 oldproof=json.loads((R/'records/nav2_v856_20261107/FULL_REMOTE_VERIFIED.json').read_text());assert oldproof['all_streamed_download_sha_verified']and oldproof['status']=='PUBLIC_RELEASE_AND_SOURCE_REMOTE_VERIFIED'
 inventory=[];allocated=0
 for target in targets:
  assert target.is_relative_to(R/'runs')and not target.is_symlink();paths=[]
  if target.is_file():paths=[target]
  elif target.is_dir():
   for current,dirs,files in os.walk(target,followlinks=False):
    dirs[:]=[x for x in dirs if not(Path(current)/x).is_symlink()];paths.extend(Path(current)/x for x in files)
  size=0
  for p in paths:
   st=p.lstat()
   if stat.S_ISREG(st.st_mode):size+=st.st_blocks*512
  allocated+=size;inventory.append(dict(path=str(target.relative_to(R)),allocated_bytes=size,existed=target.exists()))
 receipt=dict(status='PREPARED',paths=inventory,allocated_bytes_to_remove=allocated,new_models=0,new_integrations=0,stage_accessed=False)
 (REC/'CLEANUP_RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n')
 for target in targets:
  if target.is_dir():shutil.rmtree(target)
  elif target.exists():target.unlink()
 receipt.update(status='COMPLETE',completed_unix=time.time(),all_paths_absent=all(not p.exists()for p in targets));(REC/'CLEANUP_RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items()if k!='paths'}))
if __name__=='__main__':main()
