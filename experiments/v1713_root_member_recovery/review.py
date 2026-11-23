"""Close one data-only native batch without running its contents."""
import argparse,fcntl,hashlib,json,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v1712_root_member_materials';DROOT=R/'runs/v1713_root_member_recovery'
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--batch',required=True);opt=parser.parse_args();plan=read(ROOT/'BATCHES_LOCKED.json');assert opt.batch in [x['id']for x in plan['batches']]
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));O=ROOT/'rounds'/opt.batch;assert not(O/'RUNTIME_CLOSED_REVIEW.json').exists()
 result=read(O/'RESULT.json');claim=read(O/'ONCE_CLAIM.json');assert result['closed']and not Path('/proc',str(claim['owner_pid'])).exists()and all(sha(R/n)==h for n,h in claim['source_files_SHA256'].items())
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(ROOT/'OWNER.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 inputs=result.get('completed_package_records',[])
 for row in inputs:assert sha(R/row['deb_path'])==row['SHA256']and(R/row['deb_path']).stat().st_size==int(row['Size'])
 complete=False
 if(O/'UNPACK_MANIFEST.json').exists():
  manifest=read(O/'UNPACK_MANIFEST.json')
  for row in manifest['entries'].values():
   p=O/'sysroot'/row['path']
   if row['type']in ['regular','hardlink']:assert not p.is_symlink()and sha(p)==row['sha256']and p.stat().st_size==row['bytes']and(p.lstat().st_mode&0o777)==row['mode']
   elif row['type']=='symlink':assert p.is_symlink()and os.readlink(p)==row['target']
   else:assert p.is_dir()and not p.is_symlink()and(p.lstat().st_mode&0o777)==row['mode']
  complete=True
 frozen=read(R/'runs/v1694_shared_observation_closure/SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
 task=int(subprocess.check_output(['du','-sx','-B1',str(O)]).split()[0]);used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert task<224*1024**2 and used+576*1024**2<15*1024**3
 proof=dict(closed=True,passed=result['passed'],scope='ONE_NATIVE_SELECTED_BUILD_MATERIAL_DATA_BATCH',batch_id=opt.batch,package_downloads=result['package_downloads'],package_reuses=result.get('package_reuses',0),completed_extractions=result['completed_extractions'],selected_member_full_verification=complete,selected_entries=result.get('selected_entries'),excluded_entries=result.get('excluded_entries'),selected_materials_not_full_package_install=True,task_allocated_bytes=task,allruns_bytes=used,models=0,package_programs_or_libraries_executed=0,compiler_calls=0,optimizer_calls=0,physical_native=0,replay_native=0,method_outcome=None,ABI_or_build_qualified=False,first_error=result['first_error'],source_SHA_exact=True,owner_gone=True,review_original=True,execution_idle=True,all14079_shared_source_SHA_verified=True,runtime_recovery_pending=True,source_paths_SHA256={str(p.relative_to(R)):sha(p)for p in [O/'RESULT.json',O/'ONCE_CLAIM.json',ROOT/'BATCHES_LOCKED.json']})
 (O/'RUNTIME_CLOSED_REVIEW.json').write_text(json.dumps(proof,indent=2,allow_nan=False)+'\n')
 D=DROOT/opt.batch;D.mkdir(exist_ok=True);(D/'BATCH_REPORT.json').write_text(json.dumps(proof,indent=2)+'\n')
 reports=[]
 for row in plan['batches']:
  p=ROOT/'rounds'/row['id']/'RUNTIME_CLOSED_REVIEW.json'
  if p.exists():
   x=read(p);reports.append(f"|{row['id']}|{x['passed']}|{x['package_downloads']}|{x['selected_entries']}|{x['task_allocated_bytes']}|")
 (R/'docs/NATIVE_BUILD_MATERIALS_V1712_REPORT.md').write_text('# Exact native shared-build materials V1712\n\nFrozen136-package build-material selection from publisher-signed ROS/Focal metadata, explicit systemtoolchain reuse and original CMake requirements. No complete APT installation, minimal-runtime or ABI/build/method PASS is implied. Selected headers/sharedobjects/CMake/Python/tool files retain original bytes/modes/link literals; static.a/docs/locale/debug omissions are recorded and complete raw.debs retained. Original author source unchanged. Image/GL/Pythonextension-only dependencies are deferred to actual link evidence.\n\n|Batch|DataPASS|Downloaded packages|Selected entries|Task allocatedB|\n|---|---|---:|---:|---:|\n'+'\n'.join(reports)+'\n\nEvery batch has its own once/window/closure and distinct first Release. Original.debs+selected/excluded manifest are archived; selected sysroot stays local and reconstructible, not duplicated in archive. Actualremote block/member/whole/indexSHA and exacttransportcleanup/canonicalbarrier admit the next fixed batch. Common source is pushed once, reused refonly; no resealing. Aggregate report may be later than earlier sealedbatch archives; perbatch original machine results/reviews stay immutable.0downloaded program/library/compiler/model/optimizer/physics/replay execution here.\n')
 p=R/'CURRENT_EXPERIMENT.json';cur=read(p);cur.update(status='NATIVE_MATERIAL_BATCH_CLOSED_RECOVERY_PENDING_NO_MODELS',active_preparation=None);cur['latest_native_material_batch']=dict(batch=opt.batch,passed=result['passed'],source_version='V1712',package_downloads=result['package_downloads'],task_allocated_bytes=task,ABI_or_build_qualified=False,recovery_pending=True,models=0);p.write_text(json.dumps(cur,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
 print(json.dumps({k:proof[k]for k in ['batch_id','passed','package_downloads','selected_entries','task_allocated_bytes','models']}))
if __name__=='__main__':main()
