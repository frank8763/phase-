"""Single closed V913/V914 evidence delivery. Zero models; one source push."""
import fcntl,hashlib,importlib.util,json,shutil,subprocess,sys,tarfile,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v915_saved_stop_analysis';REC=R/'records/nav2_v915_20261109';TAG='phase-certified-wait-v913-v914-20261109';REPO='frank8763/phase-';GH=R/'tools/phase_storage_20261107/vendor/gh'
BATCHES=['v913_periodic_startup_complete','v914_certified_wait_renewal']
NAMES=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/NAV2_TIMED_COMMAND_V913_REPORT.md','docs/NAV2_TIMED_COMMAND_V914_REPORT.md','docs/NAV2_V913_V915_FAILURE_AND_NEXT_DESIGN.md',*[f'experiments/{v}'for v in BATCHES],'experiments/v915_saved_stop_analysis','records/nav2_v913_20261109','records/nav2_v914_20261109','records/nav2_v915_20261109']
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def cmd(a,t=30):
 p=subprocess.run(a,cwd=R,capture_output=True,text=True,timeout=t);assert p.returncode==0,(a[0],p.stderr[-1000:]);return p.stdout
def gh(a,t=45):return cmd([str(GH),*a,'--repo',REPO],t)
def packer():
 spec=importlib.util.spec_from_file_location('pack',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=O/'cloud';return m
def prepare():
 with(O/'DELIVERY_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
 REC.mkdir(exist_ok=False);m=packer();m.OUT.mkdir(exist_ok=False);archives=[]
 for v in BATCHES:
  o=R/'runs'/v;assert json.loads((o/'COMPLETION.json').read_text())['closed'];assert json.loads((o/'FINALIZED.json').read_text())['all_sources_and_decompressed_sha_verified']
  freeze=json.loads((R/'experiments'/v/'SOURCE_FREEZE.json').read_text())['files'];assert all(sha(R/p)==h for p,h in freeze.items()),'FROZEN_SOURCE_CHANGED'
  rec=R/'records'/f'nav2_{v[:4]}_20261109';idx=json.loads((rec/'RECORD_INDEX.json').read_text());archives+=idx['archives'];idx.update(release_tag=TAG,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}');dump(rec/'RECORD_INDEX.json',idx)
 for name in ['DIAGNOSIS.json','CYCLE_WAIT_DIAGNOSIS.json']:shutil.copy2(O/name,REC/name)
 shutil.copy2(R/'experiments/v915_saved_stop_analysis/restore.py',REC/'restore.py')
 paths=[]
 for n in NAMES:
  p=R/n;paths.extend(m.walk(p)if p.is_dir()else[p])
 for base in [*[f'runs/{v}'for v in BATCHES],'runs/v913_startup_fixture02','runs/v914_startup_fixture02','runs/v915_saved_stop_analysis']:
  for p in m.walk(R/base):
   if 'cloud'not in p.relative_to(R/base).parts and p.name!='delivery.console':paths.append(p)
 supplement=m.archive('v913-v915-closed-operations',paths);archives.append({k:v for k,v in supplement.items()if k!='files'})
 index=dict(repository=REPO,release_tag=TAG,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',archives=archives,scientific_status='NOT_PASSED',models_in_delivery=0)
 dump(REC/'RECORD_INDEX.json',index)
 assert not cmd(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
 cmd(['git','add','--',*NAMES]);cmd(['git','diff','--cached','--check'])
 staged=cmd(['git','diff','--cached','--name-only']).splitlines();assert all(any(p==n or p.startswith(n+'/')for n in NAMES)for p in staged)
 assert all((R/n).stat().st_size<90*1024**2 for n in staged)
 dump(O/'PREPARED.json',dict(at=time.time(),staged=len(staged),names=NAMES));print('PREPARED',len(staged),flush=True)
def publish():
 assert (O/'PREPARED.json').exists();m=packer()
 with(O/'PUBLISH_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),one_push=True),f)
 cmd(['git','diff','--cached','--check']);cmd(['git','commit','-m','Preserve V913 V914 dynamic failures and diagnose retained stop feasibility'],30);head=cmd(['git','rev-parse','HEAD']).strip()
 sync=dict(commit=head,attempted_once=True,push_budget_s=30,read_budget_s=5)
 with(O/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(sync,f)
 try:cmd(['git','push','origin','main'],30);sync['push_succeeded']=True
 except Exception as e:sync['push_error']=repr(e)
 try:sync['remote_head']=cmd(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==head
 except Exception as e:sync['verify_error']=repr(e)
 dump(REC/'GIT_SYNC_RESULT.json',sync);assert sync.get('remote_head_verified'),'PRESERVE_RAW_REMOTE_NOT_VERIFIED';print('SOURCE_REMOTE_VERIFIED',head,flush=True)
 gh(['release','create',TAG,'--title','V913/V914 failed dynamic runs and retained-stop diagnosis','--notes','NOT PASSED. V913 5224 and V914 8895 actual native steps, each replayed exactly; private0, repeats and new24 unexecuted. Declared known-frequency actor class only. V915 saved-array diagnosis0 models. Full original failure evidence with SHA inventories.','--target',head,'--draft'])
 clouds=[R/'runs'/v/'cloud'for v in BATCHES]+[m.OUT];files=[p for c in clouds for p in c.iterdir()if '.part'in p.name or p.name.endswith('.INVENTORY.json')]
 assert len({p.name for p in files})==len(files)
 gh(['release','upload',TAG,*map(str,files)],120);dest=O/'remote_verified';dest.mkdir();gh(['release','download',TAG,'--dir',str(dest)],120)
 for p in files:assert sha(p)==sha(dest/p.name)
 index=json.loads((REC/'RECORD_INDEX.json').read_text());originals={};count=0
 for a in index['archives']:
  inventory=json.loads((dest/(a['group']+'.INVENTORY.json')).read_text());catalog={r['path']:r for r in inventory['files']};parts=[dest/r['name']for r in a['parts']];assert len(parts)==1,'MULTIPART_NEEDS_STREAMING_REASSEMBLY';assert sha(parts[0])==a['archive_sha256']
  proc=subprocess.Popen(['zstd','-dc',str(parts[0])],stdout=subprocess.PIPE);seen=set()
  with tarfile.open(fileobj=proc.stdout,mode='r|')as tf:
   for member in tf:
    row=catalog[member.name];assert member.name not in seen and member.isfile();stream=tf.extractfile(member);h=hashlib.sha256();size=0
    for b in iter(lambda:stream.read(1048576),b''):h.update(b);size+=len(b)
    assert size==row['bytes']and h.hexdigest()==row['sha256'];seen.add(member.name);originals[member.name]=row['sha256'];count+=1
  assert proc.wait()==0 and seen==set(catalog)
 gh(['release','edit',TAG,'--draft=false']);proof=dict(passed=True,commit=head,members_downloaded_decompressed_sha_verified=count,release_url=index['release_url'],models=0,at=time.time());dump(REC/'REMOTE_VERIFIED.json',proof)
 deleted=0;protected=set()
 for v in BATCHES:protected.update(json.loads((R/'experiments'/v/'SOURCE_FREEZE.json').read_text())['files'])
 for root in [R/'runs/v858_nav2_verified/v913',R/'runs/v858_nav2_verified/v914',R/'runs/v913_startup_fixture02',R/'runs/v914_startup_fixture02']:
  for p in m.walk(root):
   rel=str(p.relative_to(R));assert rel not in protected and originals.get(rel)==sha(p),'NOT_VERIFIED_OR_FROZEN '+rel;deleted+=p.stat().st_size
  shutil.rmtree(root)
 for root in clouds+[dest]:
  assert root.is_relative_to(R/'runs')and not root.is_symlink();deleted+=sum(p.stat().st_size for p in m.walk(root));shutil.rmtree(root)
 result=dict(status='CLOSED_REMOTE_VERIFIED_SELECTED_CACHE_CLEANED',deleted_bytes=deleted,release_url=index['release_url'],actual_native=14119,replay_native=14119,private_native=0,unexecuted_repeats=2,new24=0,scientific_status='NOT_PASSED',models_in_delivery=0)
 dump(REC/'DELIVERY_RESULT.json',result)
 receipts=['REMOTE_VERIFIED.json','GIT_SYNC_RESULT.json','DELIVERY_RESULT.json'];gh(['release','upload',TAG,*[str(REC/n)for n in receipts]])
 dest=O/'receipt_readback';dest.mkdir()
 for n in receipts:gh(['release','download',TAG,'--pattern',n,'--dir',str(dest)],20);assert sha(dest/n)==sha(REC/n)
 shutil.rmtree(dest);cmd(['git','add','--',str(REC.relative_to(R))]);cmd(['git','commit','-m','Record verified V913 V914 evidence delivery and selected cache cleanup'],30);print(json.dumps(result),flush=True)
if __name__=='__main__':
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 {'prepare':prepare,'publish':publish}[sys.argv[1]]()
