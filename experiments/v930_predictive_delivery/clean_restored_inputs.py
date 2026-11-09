"""Remove only this stage's SHA-verified restored historical input/cache copies."""
import fcntl,hashlib,json,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v928_predictive_control_diagnosis';REC=R/'records/nav2_v929_20261109';DEL=R/'runs/v930_predictive_delivery';GH=R/'tools/phase_storage_20261107/vendor/gh';TAG='phase-executable-mppi-v929-20261109'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert json.loads((REC/'REMOTE_VERIFIED.json').read_text())['passed']
frozen=json.loads((R/'experiments/v929_executable_mppi/SOURCE_FREEZE.json').read_text())['files'];proof=json.loads((O/'RESTORE_VERIFIED.json').read_text());records=[]
for row in proof['members']:
 p=O/'saved'/row['path'];assert not p.is_symlink()and p.is_file()and sha(p)==row['sha256']and p.stat().st_size==row['bytes']and str(p.relative_to(R))not in frozen
 records.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p),remote_release=row['release'],original_member=row['path']))
assert len(list((O/'saved').rglob('*')))>0
assert len([p for p in(O/'saved').rglob('*')if p.is_file()])==len(records)
for index,group,label in [('records/nav2_v863_execution_20261107/RECORD_INDEX.json','v862-v863-evidence','navigation'),('records/nav2_v909_20261109/RECORD_INDEX.json','phase-v909-continuation-20261109','response')]:
 idx=json.loads((R/index).read_text());a=next(x for x in idx['archives']if x['group']==group);D=O/(label+'_download');h=hashlib.sha256()
 for row in a['parts']:
  p=D/row['name'];assert sha(p)==row['sha256'];h.update(p.read_bytes())
 assert h.hexdigest()==a['archive_sha256']
 expected={r['name']for r in a['parts']}|{group+'.INVENTORY.json'};assert {p.name for p in D.iterdir()}==expected
 for p in D.iterdir():assert p.is_file()and not p.is_symlink();records.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p),remote_release=idx['release_tag'],role='verified original download or inventory'))
plan=dict(models=0,at=time.time(),files=records,bytes=sum(x['bytes']for x in records),scope='All 48 selected historical members restored from original remote archives and hash verified; discard this duplicate analysis cache only')
(REC/'RESTORED_CACHE_CLEANUP.json').write_text(json.dumps(plan,indent=2)+'\n')
# Source/selected-member verification was completed before deletion and retained
# in the already remotely decompressed V929 supplement archive.
for name in ['saved','navigation_download','response_download']:
 p=O/name;assert p.is_relative_to(R/'runs')and not p.is_symlink();shutil.rmtree(p)
receipt=REC/'RESTORED_CACHE_CLEANUP.json'
subprocess.run([str(GH),'release','upload',TAG,str(receipt),'--repo','frank8763/phase-'],check=True,timeout=45)
dest=DEL/'cleanup_readback';dest.mkdir(exist_ok=False);subprocess.run([str(GH),'release','download',TAG,'--pattern',receipt.name,'--dir',str(dest),'--repo','frank8763/phase-'],check=True,timeout=30);assert sha(dest/receipt.name)==sha(receipt);shutil.rmtree(dest)
print('VERIFIED_DUPLICATE_CACHE_REMOVED',plan['bytes'])
