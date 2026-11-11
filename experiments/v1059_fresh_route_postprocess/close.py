"""Single bounded source sync and verified small postmortem Release; no models."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1060_bounded_publication_capture';D=R/'records/nav2_v1060_20261111';TAG='phase-fresh-start-diagnosis-v1060-20261111';sys.path.insert(0,str(R/'experiments/v1058_fresh_repeat_entry'))
from kernel import load
arc=load('v1060_small_archive',R/'experiments/v1058_fresh_repeat_entry/archive.py')
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def cmd(args,timeout=30):
 p=subprocess.run([str(a)for a in args],cwd=R,capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-1000:])
 return p.stdout

def main():
 with(O/'POST_CLOSE_CLAIM.json').open('x')as f:json.dump(dict(models=0,at=time.time()),f)
 freeze=json.loads((R/'experiments/v1060_bounded_publication_capture/SOURCE_FREEZE.json').read_text());assert all(arc.sha(R/p)==h for p,h in freeze['files'].items());assert arc.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 files={R/'CURRENT_EXPERIMENT.json',R/'RESEARCH_STATUS.md',R/'docs/RPCCR_FRESH_START_V1056_V1060_REPORT.md'}
 for root in [C,R/'experiments/v1060_bounded_publication_capture',O,D]:files.update(p for p in arc.walk(root)if p.name not in ['close.console','POST_CLOSE_CLAIM.json']and p.suffix!='.pyc')
 # Newly generated supplemental checks are kept; original main/repeat native
 # traces already have separately verified Release records and are not copied.
 raw=R/'runs/v858_nav2_verified/v1056/main_west_east'
 for name in ['SUPPLEMENTAL_INDEPENDENT_AUDIT.json','SUPPLEMENTAL_DISCOVERY_CHAIN_AUDIT.json']:
  p=raw/name
  if p.exists():files.add(p)
 for p in [R/'runs/v1058_fresh_repeat_entry/EXECUTED_REPEAT_PREFIX_AUDIT.json',R/'runs/v1056_fresh_route_regression/SUPPLEMENTAL_RESTORED.json',R/'runs/v1056_fresh_route_regression/REPEAT_PREFIX_RESTORED.json']:files.add(p)
 record,inventory=arc.package(R,files,O/'cloud','v1060-true-start-diagnosis-evidence');dump(D/'RECORD_INDEX.json',dict(repository='frank8763/phase-',release_tag=TAG,archives=[record],original_native_dependencies=['phase-fresh-route-v1056-20261111','phase-fresh-repeat-v1058-20261111']));dump(D/'FINALIZED.json',dict(passed=True,models=0,source_and_decompressed_sha_verified=True,physical_repeat_passed=False,three_route_passed=False,physical_ready=False));paths=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_FRESH_START_V1056_V1060_REPORT.md','experiments/v1059_fresh_route_postprocess','experiments/v1060_bounded_publication_capture',str(D.relative_to(R))];cmd(['git','add','--',*paths]);cmd(['git','diff','--cached','--check','--',*paths]);cmd(['git','commit','--only','-m','Archive true-start postmortem and bounded software-only publication fix','--',*paths]);head=cmd(['git','rev-parse','HEAD']).strip()
 with(O/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(dict(commit=head,one_push=True,one_head_read=True),f)
 sync=dict(commit=head,push_succeeded=False,remote_head_verified=False)
 try:cmd(['git','push','origin','HEAD:main'],30);sync['push_succeeded']=True
 except BaseException as e:sync['push_error']=repr(e)
 try:sync['remote_head']=cmd(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==head
 except BaseException as e:sync['head_verification_error']=repr(e)
 dump(D/'GIT_SYNC_RESULT.json',sync)
 try:
  assert sync['push_succeeded']or sync['remote_head_verified'],'SOURCE_REMOTE_UNCONFIRMED'
  delivery=load('v1060_single_release_delivery',C/'delivery.py');verified,post,upload=delivery.deliver(record,inventory,O/'cloud',D,TAG,head,'Original true-start WEST_EAST main reached goal; complete repeat stopped at packet-age gate and remains failed. Executed38929 prefix exactly matches main. V1060 is zero-model capture qualification, no new physical entry. Source '+head);dump(D/'REMOTE_VERIFIED.json',verified)
  # Remove ONLY verified temporary restorations and newly archived checks.
  manifests=[R/'runs/v1056_fresh_route_regression/SUPPLEMENTAL_RESTORED.json',R/'runs/v1056_fresh_route_regression/REPEAT_PREFIX_RESTORED.json'];catalog={}
  for path in manifests:
   for row in json.loads(path.read_text())['selected']:catalog[row['path']]=row
  for row in inventory:
   if row['path'].startswith('runs/v858_nav2_verified/v1056/'):catalog[row['path']]=row
  deleted=[]
  for name,row in catalog.items():
   p=R/name
   if not p.exists():continue
   assert p.is_file()and not p.is_symlink()and p.resolve().is_relative_to(R/'runs/v858_nav2_verified/v1056');assert p.stat().st_size==row['bytes']and arc.sha(p)==row['sha256'];deleted.append(dict(path=name,bytes=row['bytes']));p.unlink()
  dump(D/'CLEANUP.json',dict(passed=True,temporary_restored_bytes_deleted=sum(x['bytes']for x in deleted),manifest=deleted,old_unverified_raw_untouched=True,source_release_records_remain=True));post(upload+'?name=REMOTE_VERIFIED.json',(D/'REMOTE_VERIFIED.json').read_bytes(),'application/octet-stream');post(upload+'?name=CLEANUP.json',(D/'CLEANUP.json').read_bytes(),'application/octet-stream')
  import shutil
  shutil.rmtree(O/'cloud')
 except BaseException as e:dump(D/'REMOTE_PENDING.json',dict(error=repr(e),no_retry=True,raw_retained=True,models=0))
 cmd(['git','add','--',str(D.relative_to(R))]);cmd(['git','commit','--only','-m','Keep postmortem remote receipts without another push','--',str(D.relative_to(R))]);dump(O/'CLOSED.json',dict(models=0,models_authorized=False,remote_verified=(D/'REMOTE_VERIFIED.json').exists(),no_retry=True));print(json.dumps(dict(models=0,remote_verified=(D/'REMOTE_VERIFIED.json').exists())))
if __name__=='__main__':main()
