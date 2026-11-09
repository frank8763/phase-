"""Closed V934 evidence, one new source push, remote full SHA readback."""
import fcntl,hashlib,importlib.util,json,shutil,subprocess,sys,tarfile,time
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];O=R/'runs/v935_rpccr_delivery';REC=R/'records/nav2_v934_20261109';OPS=R/'runs/v934_rpccr_certified_recovery';TAG='phase-rpccr-recovery-v934-20261109';REPO='frank8763/phase-';GH=R/'tools/phase_storage_20261107/vendor/gh'
NAMES=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_MAINLINE_CONTRACT_20261109.md','docs/RPCCR_CERTIFIED_RECOVERY_V934_REPORT.md','docs/RPCCR_RETURN_V933_V934_ANALYSIS.md','experiments/v933_rpccr_certified_recovery','experiments/v934_rpccr_certified_recovery','experiments/v935_rpccr_delivery','records/nav2_v934_20261109']
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def run(args,timeout=30):
 p=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=timeout);assert p.returncode==0,p.stderr[-1200:];return p.stdout

def gh(args,timeout=90):return run([str(GH),*args,'--repo',REPO],timeout)
def packer():
 spec=importlib.util.spec_from_file_location('p',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=O/'cloud'
 def opened(*a,**kw):
  if str(kw.get('mode','')).startswith('w'):kw['dereference']=True
  return tarfile.open(*a,**kw)
 m.tarfile=SimpleNamespace(open=opened);return m

def prepare():
 O.mkdir(exist_ok=True)
 with(O/'PREPARE_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
 assert json.loads((OPS/'COMPLETION.json').read_text())['closed']and json.loads((OPS/'FINALIZED.json').read_text())['all_sources_and_decompressed_sha_verified']
 frozen=json.loads((R/'experiments/v934_rpccr_certified_recovery/SOURCE_FREEZE.json').read_text())['files'];assert all(sha(R/p)==h for p,h in frozen.items())
 m=packer();m.OUT.mkdir(exist_ok=False);idx=json.loads((REC/'RECORD_INDEX.json').read_text());archives=idx['archives'];files=[]
 for base in [*[R/n for n in NAMES if(R/n).is_dir()],*[R/'runs'/n for n in ['v934_startup_fixture02']]]:files.extend(m.walk(base))
 for n in ['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_MAINLINE_CONTRACT_20261109.md','docs/RPCCR_CERTIFIED_RECOVERY_V934_REPORT.md','docs/RPCCR_RETURN_V933_V934_ANALYSIS.md']:files.append(R/n)
 diag=R/'runs/v933_rpccr_certified_recovery'
 files.extend(p for p in m.walk(diag)if p.relative_to(diag).parts[0]!='download')
 for n in ['campaign.console','finalize.console','DRIVER.json','PREPARATION_ERRORS.json']:
  if(OPS/n).exists():files.append(OPS/n)
 supplement=m.archive('v933-v934-closed-operations',files);archives.append({k:v for k,v in supplement.items()if k!='files'})
 idx.update(release_tag=TAG,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',archives=archives);dump(REC/'RECORD_INDEX.json',idx)
 assert not run(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
 run(['git','add','--',*NAMES]);run(['git','diff','--cached','--check']);staged=run(['git','diff','--cached','--name-only']).splitlines();assert all((R/p).stat().st_size<90*1024**2 for p in staged)
 dump(O/'PREPARED.json',dict(staged=len(staged),models=0));print('PREPARED',len(staged),flush=True)

def publish():
 assert(O/'PREPARED.json').exists()
 with(O/'PUBLISH_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
 run(['git','diff','--cached','--check']);run(['git','commit','-m','Add certified RP-CCR recovery without replacing the passed RPP nominal controller']);head=run(['git','rev-parse','HEAD']).strip()
 sync=dict(commit=head,push_budget_s=30,verify_budget_s=5,one_attempt=True)
 with(O/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(sync,f)
 try:run(['git','push','origin','main'],30);sync['push_succeeded']=True
 except Exception as e:sync['push_error']=repr(e)
 try:sync['remote_head']=run(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==head
 except Exception as e:sync['verify_error']=repr(e)
 dump(REC/'GIT_SYNC_RESULT.json',sync);assert sync.get('remote_head_verified'),'REMOTE_SOURCE_UNKNOWN_KEEP_RAW'
 gh(['release','create',TAG,'--title','RP-CCR certified recovery with frozen RPP V934 bounded engineering baseline','--notes','Original WE dynamic RP-CCR development and success-only repeat. FeasibleRPP nominal control, causal risk, unchanged command certificate plus fixed13 recovery proposal arbitration. Exact full result and failures in report; not fresh24 acceptance or a formal reachability proof. Full original records and source SHA inventories.','--target',head,'--draft'])
 idx=json.loads((REC/'RECORD_INDEX.json').read_text());clouds=[OPS/'cloud',O/'cloud'];assets=[p for c in clouds for p in c.iterdir()if '.part'in p.name or p.name.endswith('.INVENTORY.json')]
 assert len({p.name for p in assets})==len(assets)
 gh(['release','upload',TAG,*map(str,assets)],180);dest=O/'download';dest.mkdir();gh(['release','download',TAG,'--dir',str(dest)],180)
 for p in assets:assert sha(p)==sha(dest/p.name)
 originals={};members=0
 for a in idx['archives']:
  inventory=json.loads((dest/(a['group']+'.INVENTORY.json')).read_text());catalog={x['path']:x for x in inventory['files']};combined=dest/'reassembled.tar.zst';h=hashlib.sha256()
  with combined.open('xb')as f:
   for row in a['parts']:
    p=dest/row['name'];assert sha(p)==row['sha256']and p.stat().st_size==row['bytes']
    with p.open('rb')as stream:
     for b in iter(lambda:stream.read(1048576),b''):h.update(b);f.write(b)
  assert h.hexdigest()==a['archive_sha256'];proc=subprocess.Popen(['zstd','-dc',str(combined)],stdout=subprocess.PIPE);seen=set()
  with tarfile.open(fileobj=proc.stdout,mode='r|')as tf:
   for member in tf:
    row=catalog[member.name];assert member.name not in seen and member.isfile();h=hashlib.sha256();n=0;stream=tf.extractfile(member)
    for b in iter(lambda:stream.read(1048576),b''):h.update(b);n+=len(b)
    assert n==row['bytes']and h.hexdigest()==row['sha256'];seen.add(member.name);originals[member.name]=row['sha256'];members+=1
  assert proc.wait()==0 and seen==set(catalog);combined.unlink()
 gh(['release','edit',TAG,'--draft=false']);proof=dict(passed=True,source_commit=head,downloaded_decompressed_members=members,release_url=idx['release_url'],models=0,at=time.time());dump(REC/'REMOTE_VERIFIED.json',proof)
 # Raw current evidence and software fixtures only after every byte read back.
 deleted=0
 roots=[R/'runs/v858_nav2_verified/v934',*[R/'runs'/n for n in ['v934_startup_fixture02']]]
 for root in roots:
  assert root.is_relative_to(R/'runs')and not root.is_symlink()
  for p in packer().walk(root):assert originals.get(str(p.relative_to(R)))==sha(p),'UNVERIFIED_RAW '+str(p);deleted+=p.stat().st_size
  shutil.rmtree(root)
 for root in clouds+[dest]:
  assert root.is_relative_to(R/'runs')and not root.is_symlink();deleted+=sum(p.stat().st_size for p in packer().walk(root));shutil.rmtree(root)
 # Selected old fixtures are now contained and read back in the new supplement.
 diag=R/'runs/v933_rpccr_certified_recovery';saved=diag/'saved'
 for p in packer().walk(saved):assert originals.get(str(p.relative_to(R)))==sha(p);deleted+=p.stat().st_size
 shutil.rmtree(saved)
 alias=OPS/'saved';reference_prefix='runs/v933_rpccr_certified_recovery/saved/'
 for p in packer().walk(alias):assert originals.get(reference_prefix+p.name)==sha(p);deleted+=p.stat().st_size
 shutil.rmtree(alias)
 old_index=json.loads((R/'records/nav2_v924_20261109/RECORD_INDEX.json').read_text());old_archive=next(a for a in old_index['archives']if a['group']=='phase-v924-20261109');download=diag/'download';h=hashlib.sha256()
 assert{p.name for p in download.iterdir()}=={r['name']for r in old_archive['parts']}|{old_archive['group']+'.INVENTORY.json'}
 for part in old_archive['parts']:
  p=download/part['name'];assert sha(p)==part['sha256'];h.update(p.read_bytes())
 assert h.hexdigest()==old_archive['archive_sha256'];deleted+=sum(p.stat().st_size for p in packer().walk(download));shutil.rmtree(download)
 dump(REC/'DELIVERY_RESULT.json',dict(status='REMOTE_VERIFIED_RAW_AND_REBUILD_CACHE_CLEANED',deleted_bytes=deleted,frozen_prior_t0_retained=True,models=0,release_url=idx['release_url']))
 receipts=[REC/n for n in ['REMOTE_VERIFIED.json','GIT_SYNC_RESULT.json','DELIVERY_RESULT.json']];gh(['release','upload',TAG,*map(str,receipts)]);check=O/'receipt_readback';check.mkdir()
 for p in receipts:gh(['release','download',TAG,'--pattern',p.name,'--dir',str(check)],30);assert sha(p)==sha(check/p.name)
 shutil.rmtree(check);run(['git','add','--',str(REC.relative_to(R))]);run(['git','commit','-m','Record verified V934 remote evidence and bounded cache cleanup']);print(json.dumps(proof),flush=True)
if __name__=='__main__':
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 {'prepare':prepare,'publish':publish}[sys.argv[1]]()
