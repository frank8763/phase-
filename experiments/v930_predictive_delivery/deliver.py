"""Closed V928/V929 evidence, one new source push, remote full SHA readback."""
import fcntl,hashlib,importlib.util,json,shutil,subprocess,sys,tarfile,time
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];O=R/'runs/v930_predictive_delivery';REC=R/'records/nav2_v929_20261109';OPS=R/'runs/v929_executable_mppi';TAG='phase-executable-mppi-v929-20261109';REPO='frank8763/phase-';GH=R/'tools/phase_storage_20261107/vendor/gh'
NAMES=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/EXECUTABLE_MPPI_V929_REPORT.md','docs/PREDICTIVE_CONTROL_V928_V929_ANALYSIS.md','experiments/v928_predictive_control_diagnosis','experiments/v929_executable_mppi','experiments/v930_predictive_delivery','records/nav2_v929_20261109']
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
 frozen=json.loads((R/'experiments/v929_executable_mppi/SOURCE_FREEZE.json').read_text())['files'];assert all(sha(R/p)==h for p,h in frozen.items())
 m=packer();m.OUT.mkdir(exist_ok=False);idx=json.loads((REC/'RECORD_INDEX.json').read_text());archives=idx['archives'];files=[]
 for base in [*[R/n for n in NAMES if(R/n).is_dir()],*[R/'runs'/n for n in ['v929_startup_fixture02','v929_startup_fixture03','v929_controller_fixture','v929_controller_fixture02','v929_controller_fixture03']]]:files.extend(m.walk(base))
 for n in ['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/EXECUTABLE_MPPI_V929_REPORT.md','docs/PREDICTIVE_CONTROL_V928_V929_ANALYSIS.md']:files.append(R/n)
 diag=R/'runs/v928_predictive_control_diagnosis'
 files.extend(p for p in m.walk(diag)if p.relative_to(diag).parts[0]not in ['saved','navigation_download','response_download'])
 for n in ['campaign.console','finalize.console','DRIVER.json','PREPARATION_ERRORS.json']:
  if(OPS/n).exists():files.append(OPS/n)
 supplement=m.archive('v928-v929-closed-operations',files);archives.append({k:v for k,v in supplement.items()if k!='files'})
 idx.update(release_tag=TAG,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',archives=archives);dump(REC/'RECORD_INDEX.json',idx)
 assert not run(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
 run(['git','add','--',*NAMES]);run(['git','diff','--cached','--check']);staged=run(['git','diff','--cached','--name-only']).splitlines();assert all((R/p).stat().st_size<90*1024**2 for p in staged)
 dump(O/'PREPARED.json',dict(staged=len(staged),models=0));print('PREPARED',len(staged),flush=True)

def publish():
 assert(O/'PREPARED.json').exists()
 with(O/'PUBLISH_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
 run(['git','diff','--cached','--check']);run(['git','commit','-m','Project MPPI samples before scoring and preserve bounded predictive-baseline evidence']);head=run(['git','rev-parse','HEAD']).strip()
 sync=dict(commit=head,push_budget_s=30,verify_budget_s=5,one_attempt=True)
 with(O/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(sync,f)
 try:run(['git','push','origin','main'],30);sync['push_succeeded']=True
 except Exception as e:sync['push_error']=repr(e)
 try:sync['remote_head']=run(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==head
 except Exception as e:sync['verify_error']=repr(e)
 dump(REC/'GIT_SYNC_RESULT.json',sync);assert sync.get('remote_head_verified'),'REMOTE_SOURCE_UNKNOWN_KEEP_RAW'
 gh(['release','create',TAG,'--title','Executable-sample MPPI V929 bounded engineering baseline','--notes','Original WE static then conditionally dynamic; exact result in report. Nominal baseline, not RP-CCR safety proof or fresh24 confirmation. Preparation errors and rejected response fit preserved. Full own-state/control/contact replay and source SHA inventories.','--target',head,'--draft'])
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
 roots=[R/'runs/v858_nav2_verified/v929',*[R/'runs'/n for n in ['v929_startup_fixture02','v929_startup_fixture03','v929_controller_fixture','v929_controller_fixture02','v929_controller_fixture03']]]
 for root in roots:
  assert root.is_relative_to(R/'runs')and not root.is_symlink()
  for p in packer().walk(root):assert originals.get(str(p.relative_to(R)))==sha(p),'UNVERIFIED_RAW '+str(p);deleted+=p.stat().st_size
  shutil.rmtree(root)
 for root in clouds+[dest,OPS/'headers',OPS/'debs']:
  assert root.is_relative_to(R/'runs')and not root.is_symlink();deleted+=sum(p.stat().st_size for p in packer().walk(root));shutil.rmtree(root)
 dump(REC/'DELIVERY_RESULT.json',dict(status='REMOTE_VERIFIED_RAW_AND_REBUILD_CACHE_CLEANED',deleted_bytes=deleted,old_downloaded_evidence_not_included_in_delete=True,models=0,release_url=idx['release_url']))
 receipts=[REC/n for n in ['REMOTE_VERIFIED.json','GIT_SYNC_RESULT.json','DELIVERY_RESULT.json']];gh(['release','upload',TAG,*map(str,receipts)]);check=O/'receipt_readback';check.mkdir()
 for p in receipts:gh(['release','download',TAG,'--pattern',p.name,'--dir',str(check)],30);assert sha(p)==sha(check/p.name)
 shutil.rmtree(check);run(['git','add','--',str(REC.relative_to(R))]);run(['git','commit','-m','Record verified V929 remote evidence and bounded cache cleanup']);print(json.dumps(proof),flush=True)
if __name__=='__main__':
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 {'prepare':prepare,'publish':publish}[sys.argv[1]]()
