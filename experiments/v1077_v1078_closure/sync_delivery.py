"""One bounded source push, release upload and full streamed evidence readback."""
import sys,json,subprocess,time,urllib.request,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1077_v1078_closure';D=R/'records/nav2_v1077_v1078_20261112';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();assert not(D/'GIT_SYNC_CLAIM.json').exists();head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();(D/'GIT_SYNC_CLAIM.json').write_text(json.dumps(dict(head=head,at=time.time(),one_push=True,no_old_sync_retry=True))+'\n');sync=dict(head=head,push_succeeded=False,remote_head_verified=False)
try:
 p=subprocess.run(['git','push','origin','HEAD:main'],cwd=R,text=True,capture_output=True,timeout=30);sync.update(push_succeeded=p.returncode==0,diagnostic=(p.stdout+p.stderr)[-1000:]);q=subprocess.run(['git','ls-remote','origin','refs/heads/main'],cwd=R,text=True,capture_output=True,timeout=5);remote=q.stdout.split()[0]if q.returncode==0 and q.stdout.split()else None;sync.update(remote_head=remote,remote_head_verified=remote==head)
except subprocess.TimeoutExpired as e:sync['error']='bounded sync timeout: '+str(e.cmd)
(D/'GIT_SYNC_RESULT.json').write_text(json.dumps(sync,indent=2)+'\n');print(json.dumps(sync),flush=True)
if not(sync['push_succeeded']and sync['remote_head_verified']):sys.exit(1)
assert not(D/'DELIVERY_CLAIM.json').exists();(D/'DELIVERY_CLAIM.json').write_text(json.dumps(dict(head=head,at=time.time(),one_release=True))+'\n')
try:
 from kernel import load
 delivery=load('v1077_actual_delivery',C/'delivery.py');index=json.loads((D/'RECORD_INDEX.json').read_text());inventory=json.loads((O/'INVENTORY.json').read_text())['files'];summary='Five .125 response components passed. Saved NS continuation failed steering-return tracking gate; original failure retained. Dual-front prediction repair has saved-data qualification only; no new main or24 confirmation. Complete original evidence, precise counts and transport truncation diagnostic retained.';result,post,upload=delivery.deliver(index['archives'][0],inventory,O/'cloud',D,index['release_tag'],head,summary)
 asset=index['selected_model_asset'];url='https://github.com/frank8763/phase-/releases/download/'+index['release_tag']+'/'+asset['name'];temp=O/'model_readback.zst'
 with urllib.request.urlopen(url,timeout=60)as src,temp.open('xb')as out:
  import shutil
  shutil.copyfileobj(src,out,1048576)
 assert temp.stat().st_size==asset['compressed_bytes']and hashlib.sha256(temp.read_bytes()).hexdigest()==asset['compressed_sha256'];p=subprocess.Popen(['zstd','-q','-dc',str(temp)],stdout=subprocess.PIPE);h=hashlib.sha256();size=0
 for b in iter(lambda:p.stdout.read(1048576),b''):h.update(b);size+=len(b)
 assert p.wait()==0 and size==asset['model_bytes']and h.hexdigest()==asset['model_sha256'];temp.unlink();result.update(selected_model_asset_compressed_and_decompressed_sha_verified=True,original_failure_preserved=True);(D/'REMOTE_VERIFIED.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
except BaseException as e:
 (D/'DELIVERY_ERROR.json').write_text(json.dumps(dict(error=repr(e),raw_retained=True,no_automatic_retry=True,models=0),indent=2)+'\n');print(json.dumps(dict(delivery_failed=True,error=repr(e),raw_retained=True)),flush=True);sys.exit(1)
