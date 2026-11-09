"""One closed V910–V912 delivery; no model imports, no old-batch sync retries."""
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess,sys,tarfile,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v912_startup_dependency_qualification';REC=R/'records/nav2_v911_20261109';TAG='phase-timed-command-v911-20261109';GH=R/'tools/phase_storage_20261107/vendor/gh';REPO='frank8763/phase-'
NAMES=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/NAV2_TIMED_COMMAND_V911_REPORT.md','docs/NAV2_PERIODIC_COURSE_V910_V912_ANALYSIS.md','experiments/v910_corridor_diagnosis','experiments/v911_periodic_causal_navigation','experiments/v912_startup_dependency_qualification','records/nav2_v911_20261109']
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cmd(a,t=30):
 p=subprocess.run(a,cwd=R,capture_output=True,text=True,timeout=t);assert p.returncode==0,(a[0],p.stderr[-800:]);return p.stdout
def gh(a,t=45):return cmd([str(GH),*a,'--repo',REPO],t)
def main():
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert json.loads((R/'runs/v911_periodic_causal_navigation/COMPLETION.json').read_text())['closed']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(O/'DELIVERY_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0,one_push_only=True),f)
 spec=importlib.util.spec_from_file_location('pack',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=O/'cloud';m.OUT.mkdir(exist_ok=False)
 paths=[]
 for n in NAMES:
  p=R/n;paths.extend(m.walk(p)if p.is_dir()else[p])
 for root in ['runs/v910_corridor_diagnosis','runs/v911_periodic_causal_navigation','runs/v912_startup_dependency_qualification']:
  paths.extend(p for p in m.walk(R/root)if not any(z in p.relative_to(R/root).parts for z in ['remote','dependencies','cloud','saved','audit_fixture','response_saved'])and p.name not in ['delivery.console'])
 supplement=m.archive('v910-v912-closed-operations',paths)
 index=json.loads((REC/'RECORD_INDEX.json').read_text());index['archives'].append({k:v for k,v in supplement.items()if k!='files'});index.update(release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',scope='Original frozen V911 preARM failure, V910 retrospective diagnosis and V912 zero-model dependency checks')
 dump(REC/'RECORD_INDEX.json',index)
 assert not cmd(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
 cmd(['git','add','--',*NAMES]);cmd(['git','diff','--cached','--check'])
 staged=cmd(['git','diff','--cached','--name-only']).splitlines();assert all(any(p==n or p.startswith(n+'/')for n in NAMES)for p in staged)
 assert all((R/n).stat().st_size<90*1024**2 for n in staged)
 cmd(['git','commit','-m','Record periodic-course qualification and preserve zero-step startup failure'],30);head=cmd(['git','rev-parse','HEAD']).strip()
 sync=dict(commit=head,attempted_once=True,push_budget_s=30,read_budget_s=5)
 with(O/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(sync,f)
 try:cmd(['git','push','origin','main'],30);sync['push_succeeded']=True
 except Exception as e:sync['push_error']=repr(e)
 try:sync['remote_head']=cmd(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==head
 except Exception as e:sync['verify_error']=repr(e)
 dump(REC/'GIT_SYNC_RESULT.json',sync);assert sync.get('remote_head_verified'),'PRESERVE_RAW_REMOTE_NOT_VERIFIED'
 print('SOURCE_REMOTE_VERIFIED',head,flush=True)
 gh(['release','create',TAG,'--title','V911 periodic-course preparation and pre-ARM failure','--notes','Original V911 failed before ARM: model initialized, 0 integration, 0 navigation. New periodic prior software results only; no dynamic acceptance. All prior failures retained. See tracked report and evidence inventories.','--target',head,'--draft'])
 clouds=[R/'runs/v911_periodic_causal_navigation/cloud',m.OUT];files=[]
 for cloud in clouds:files.extend(p for p in cloud.iterdir()if p.name.endswith('.part000')or p.name.endswith('.INVENTORY.json'))
 gh(['release','upload',TAG,*map(str,files)],120)
 dest=O/'remote_verified';dest.mkdir();gh(['release','download',TAG,'--dir',str(dest)],120)
 for p in files:assert sha(p)==sha(dest/p.name)
 restored=0;originals={}
 for archive in index['archives']:
  inventory=json.loads((dest/(archive['group']+'.INVENTORY.json')).read_text());catalog={x['path']:x for x in inventory['files']};part=dest/archive['parts'][0]['name'];assert sha(part)==archive['archive_sha256']
  proc=subprocess.Popen(['zstd','-dc',str(part)],stdout=subprocess.PIPE);seen=set()
  with tarfile.open(fileobj=proc.stdout,mode='r|')as tf:
   for member in tf:
    row=catalog[member.name];assert member.isfile();data=tf.extractfile(member).read();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'];seen.add(member.name);restored+=1;originals[member.name]=row['sha256']
  assert proc.wait()==0 and seen==set(catalog)
 gh(['release','edit',TAG,'--draft=false'])
 proof=dict(passed=True,commit=head,members_downloaded_decompressed_sha_verified=restored,release_url=index['release_url'],models=0,at=time.time());dump(REC/'REMOTE_VERIFIED.json',proof)
 # Delete only current closed raw model records represented exactly in verified release.
 deleted=0;raw=R/'runs/v858_nav2_verified/v911'
 for p in m.walk(raw):
  rel=str(p.relative_to(R));assert originals.get(rel)==sha(p),'RAW_NOT_VERIFIED '+rel;deleted+=p.stat().st_size
 shutil.rmtree(raw)
 # Restored prior inputs are exact copies of already verified remote members;
 # qualification fixtures and dependency installs are reproducible temporary caches.
 cache_roots=[R/'runs/v910_corridor_diagnosis'/n for n in ['remote','saved','response_saved','dependencies']]+[R/'runs/v911_periodic_causal_navigation'/n for n in ['saved','audit_fixture']]+clouds+[dest]
 for p in cache_roots:
  assert p.is_relative_to(R/'runs') and not p.is_symlink()
  if p.exists():deleted+=sum(f.stat().st_size for f in m.walk(p));shutil.rmtree(p)
 result=dict(status='CLOSED_REMOTE_VERIFIED_CACHE_CLEANED',deleted_bytes=deleted,original_failed_result_preserved=True,new24=0,actual_native=0,replay_native=0,private_native=0,models_initialization_completed=True,release_url=index['release_url'],models=0)
 dump(REC/'DELIVERY_RESULT.json',result)
 gh(['release','upload',TAG,str(REC/'REMOTE_VERIFIED.json'),str(REC/'GIT_SYNC_RESULT.json'),str(REC/'DELIVERY_RESULT.json')])
 receipts=O/'receipt_readback';receipts.mkdir()
 for n in ['REMOTE_VERIFIED.json','GIT_SYNC_RESULT.json','DELIVERY_RESULT.json']:
  gh(['release','download',TAG,'--pattern',n,'--dir',str(receipts)],20);assert sha(receipts/n)==sha(REC/n)
 shutil.rmtree(receipts)
 cmd(['git','add','--',str(REC.relative_to(R))]);cmd(['git','commit','-m','Record verified V911 delivery and bounded cache cleanup'],30)
 print(json.dumps(result),flush=True)
if __name__=='__main__':main()
