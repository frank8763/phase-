"""Read-only scientific closure verification after the overnight cutoff, zero models."""
import datetime,fcntl,gzip,hashlib,json,zipfile
from pathlib import Path
from zoneinfo import ZoneInfo
repo=Path(__file__).resolve().parents[2];out=repo/'runs/night_review_20261106';target=out/'CHECK_CLOSED.json';assert not target.exists()
def read(p):return json.loads(p.read_text())
def sha(p):
 d=hashlib.sha256()
 with Path(p).open('rb')as stream:
  for chunk in iter(lambda:stream.read(4*1024**2),b''):d.update(chunk)
 return d.hexdigest()
archive=repo/'evidence/rpccr_timed_escape_v833_20261105';inventory=json.loads(gzip.decompress((archive/'RAW_INVENTORY.json.gz').read_bytes()));verified={}
for item in inventory:
 if item['blob']not in verified:
  blob=archive/item['blob'];digest=hashlib.sha256();count=0
  with(gzip.open(blob,'rb')if item['encoding']=='gzip'else blob.open('rb'))as stream:
   for chunk in iter(lambda:stream.read(4*1024**2),b''):count+=len(chunk);digest.update(chunk)
  verified[item['blob']]=(count,digest.hexdigest())
 assert verified[item['blob']]==(item['bytes'],item['sha256']),item['path']+'_DECOMPRESSED_MISMATCH'
 assert sha(repo/item['path'])==item['sha256'],item['path']+'_SOURCE_CHANGED'
manifest=read(archive/'MANIFEST.json');assert all(sha(archive/x['path'])==x['sha256']for x in manifest)
transport=read(repo/'evidence/rpccr_timed_escape_v833_20261105_transport/TRANSPORT_MANIFEST.json')
for entry in transport['entries']:
 joined=hashlib.sha256();count=0
 for part in entry['chunks']:
  path=repo/part['path'];assert path.stat().st_size==part['bytes']and sha(path)==part['sha256']
  with path.open('rb')as stream:
   for chunk in iter(lambda:stream.read(4*1024**2),b''):joined.update(chunk);count+=len(chunk)
 assert count==entry['bytes']and joined.hexdigest()==entry['sha256']and sha(repo/entry['original_blob'])==entry['sha256']
ops=repo/'evidence/rpccr_timed_escape_ops_20261105';op=read(ops/'MANIFEST.json')
with zipfile.ZipFile(ops/'OPERATIONS_SNAPSHOT.zip')as zipped:
 for item in op['inventory']:
  data=zipped.read(item['path']);assert len(data)==item['bytes']and hashlib.sha256(data).hexdigest()==item['sha256']
freeze=read(repo/'experiments/v834_timed_escape_development/CANDIDATE_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
root=repo/'runs/timed_escape_night_20261105';w=read(root/'ROUND_WINDOW.json');assert w['round_closed']and read(root/'LEDGER.json')['closed']and not(repo/'runs/v834_timed_escape_development/ROUND_WINDOW.json').exists()
assert(repo/'REVIEW_PENDING').read_bytes()==(root/'REVIEW_PENDING.before').read_bytes()
with(repo/'runs/v648_static_unknown/execution.lock').open('rb')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
known_pids=[read(root/'ROUND_WINDOW.json')['pid'],read(root/'INHIBITOR.json')['pid'],read(root/'LAUNCH.json')['outer_pid']]
for pid in known_pids:
 p=Path('/proc')/str(pid)
 if p.exists():assert(p/'stat').read_text().rsplit(') ',1)[1].split()[0]=='Z','KNOWN_OLD_PHASE_PROCESS_STILL_LIVE'
summary=dict(status='CLOSED_SCIENTIFIC_EVIDENCE_SOURCE_AND_DECOMPRESSED_SHA_VERIFIED',checked_at=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),old_v833_result='NOT_PASSED',component_counts=read(root/'COMPLETION.json')['component_counts'],closed_at=datetime.datetime.fromtimestamp(w['started_unix']+w['elapsed_s'],ZoneInfo('Asia/Shanghai')).isoformat(),navigation_v834_started=False,planned_mains_unexecuted=5,planned_repeats_unexecuted=5,new24_confirmation=0,comparison_started=False,source_files=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),unique_verified_blobs=len(verified),verified_large_blob_reassemblies=len(transport['entries']),operation_snapshot_sources=op['sources'],frozen_sources_checked=len(freeze['files']),known_phase_processes_ended=True,execution_lock_idle=True,review_pending_original_bytes_restored=True,new_models=0,new_integrations=0,raw_deleted=False)
target.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary),flush=True)
