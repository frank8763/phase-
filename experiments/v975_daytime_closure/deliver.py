"""New day source sync and two separately counted evidence groups; no old sync retry."""
import fcntl,importlib.util,json,os,shutil,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];OUT=R/'runs/v975_daytime_delivery';REC=R/'records/nav2_v974_20261110';TAG='phase-rpccr-day-binding-v974-20261110'
SOURCES=['v972_daytime_binding_probe','v974_daytime_binding_gate','v975_daytime_closure']
NEW=[R/'runs/v974_daytime_binding_gate',R/'runs/v972_daytime_binding_probe',R/'runs/v974_planner_flow_fixture01',R/'runs/v974_planner_flow_fixture02',R/'runs/v858_nav2_verified/v974']
HISTORY=[R/'runs/v971_night_entry_continuation',R/'runs/v858_nav2_verified/v968']
FOLDERS=NEW+HISTORY
STAGE=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_DAYTIME_BINDING_V974_REPORT.md',str(REC.relative_to(R)),*['experiments/'+s for s in SOURCES]]
spec=importlib.util.spec_from_file_location('v975_closed_transport',R/'experiments/v954_stop_align_closure/deliver.py');transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport);transport.OUT=OUT;transport.REC=REC;transport.TAG=TAG
run=transport.run;dump=transport.dump;sha=transport.sha;gh=transport.gh

def active(p):return p.parent==R/'runs/v974_daytime_binding_gate'and p.name in{'close.console','campaign.console'}
def prepare():
 assert json.loads((REC/'LOCAL_CLOSURE.json').read_text())['closed']and not run(['git','diff','--cached','--name-only']).strip()
 with(OUT/'PREPARE_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
 module=transport.packer();module.OUT.mkdir(exist_ok=False);excluded=[];links=[]
 for folder in FOLDERS:
  for current,dirs,files in os.walk(folder,followlinks=False):
   for name in dirs+files:
    p=Path(current)/name
    if p.is_symlink():links.append(dict(path=str(p.relative_to(R)),target=os.readlink(p),target_accessed=False))
 dump(REC/'GENERATED_LINKS.json',dict(links=links))
 def selected(folders):
  result=[]
  for folder in folders:
   for p in module.walk(folder):
    if '__pycache__'in p.parts or 'mesa_shader_cache'in p.parts or active(p):excluded.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p),reason='REBUILDABLE_CACHE_OR_ACTIVE_CLOSURE_OUTPUT'))
    else:result.append(p)
  return result
 old=module.archive('historical-v971-zero-motion-failure',selected(HISTORY)+list(module.walk(R/'records/nav2_v971_20261109')))
 source=[p for s in SOURCES for p in(R/'experiments'/s).iterdir()if p.is_file()]
 dump(REC/'SOURCE_SNAPSHOT.json',dict(files={str(p.relative_to(R)):sha(p)for p in source},models=0))
 fresh=module.archive('v974-single-day-dynamic-gate',selected(NEW)+selected([R/'experiments'/s for s in SOURCES])+list(module.walk(REC))+[R/p for p in STAGE[:3]])
 dump(REC/'EXCLUDED_REBUILDABLE_CACHE.json',dict(files=excluded))
 final=json.loads((REC/'FINAL_INDEPENDENT_AUDIT.json').read_text());index=dict(repository='frank8763/phase-',release_tag=TAG,release_url=f'https://github.com/frank8763/phase-/releases/tag/{TAG}',
  scientific_outcome=final['new_day']['status'],new_day=final['new_day'],carried_night=final['carried_night'],archives=[{k:v for k,v in x.items()if k!='files'}for x in[old,fresh]],training=0,hardware=0)
 dump(REC/'RECORD_INDEX.json',index);run(['git','add','--',*STAGE]);run(['git','diff','--cached','--check'])
 assert all((R/p).lstat().st_size<90*1024**2 for p in run(['git','diff','--cached','--name-only']).splitlines())
 dump(OUT/'PREPARED.json',dict(source_and_member_sha_verified=True,models=0));print(json.dumps(dict(prepared=True,archives=index['archives'])),flush=True)
def publish():
 assert(OUT/'PREPARED.json').exists()
 with(OUT/'PUBLICATION_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
 run(['git','diff','--cached','--check']);run(['git','commit','-m','Fix intended planner and native binding; report one daytime dynamic gate'])
 head=run(['git','rev-parse','HEAD']).strip();sync=dict(commit=head,one_attempt=True,push_limit_s=30,remote_read_limit_s=5)
 with(REC/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(sync,f)
 try:run(['git','push','origin','main'],30);sync['push_succeeded']=True
 except Exception as e:sync['push_error']=repr(e)
 try:sync['remote_head']=run(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==head
 except Exception as e:sync['verify_error']=repr(e)
 dump(REC/'GIT_SYNC_RESULT.json',sync);assert sync.get('remote_head_verified'),'REMOTE_SOURCE_UNKNOWN_KEEP_RAW_NO_RETRY'
 index=json.loads((REC/'RECORD_INDEX.json').read_text());assets=[p for p in(OUT/'cloud').iterdir()if p.is_file()]+[REC/'RECORD_INDEX.json']
 gh(['release','create',TAG,'--target',head,'--title','One daytime dynamic route; explicit native and planner bindings',
  '--notes','New V974 single dynamic route only; outcome in report/index. Historical V971 zero-motion engineering failure18201actual+18201replay separately preserved. No denominator mixing, old failure regrading, new24/training/hardware. Source and all decompressed member SHA verified.','--draft'])
 gh(['release','upload',TAG,*map(str,assets)]);downloaded=OUT/'readback';downloaded.mkdir(exist_ok=False);gh(['release','download',TAG,'--dir',str(downloaded)])
 for p in assets:assert sha(p)==sha(downloaded/p.name)
 transport.shared_verifier()(downloaded,index);gh(['release','edit',TAG,'--draft=false'])
 dump(REC/'REMOTE_VERIFIED.json',dict(passed=True,source_commit=head,all_asset_and_decompressed_member_sha_verified=True,release_url=index['release_url'],models=0))
 for p in[REC/'GIT_SYNC_RESULT.json',REC/'REMOTE_VERIFIED.json']:transport.upload_receipt(p,downloaded)
 catalog={}
 for group in index['archives']:
  manifest=json.loads((downloaded/(group['group']+'.INVENTORY.json')).read_text());catalog.update({x['path']:x for x in manifest['files']})
 catalog.update({x['path']:x for x in json.loads((REC/'EXCLUDED_REBUILDABLE_CACHE.json').read_text())['files']})
 for folder in FOLDERS:
  for p in transport.packer().walk(folder):
   if active(p):continue
   x=catalog[str(p.relative_to(R))];assert sha(p)==x['sha256']and p.stat().st_size==x['bytes']
 removed=[];deleted=0
 for folder in[*FOLDERS,downloaded,OUT/'cloud']:
  if not folder.exists():continue
  assert folder.resolve().is_relative_to(R/'runs')and not folder.is_symlink();size=0
  if folder==R/'runs/v974_daytime_binding_gate':
   for p in list(folder.iterdir()):
    if active(p):continue
    if p.is_symlink():p.unlink()
    elif p.is_dir():size+=sum(q.stat().st_size for q in transport.packer().walk(p));shutil.rmtree(p)
    else:size+=p.stat().st_size;p.unlink()
  else:size=sum(p.stat().st_size for p in transport.packer().walk(folder));shutil.rmtree(folder)
  removed.append(dict(path=str(folder.relative_to(R)),bytes=size));deleted+=size
 dump(REC/'CLEANUP_RESULT.json',dict(deleted_bytes=deleted,removed=removed,all_remote_member_sha_verified_before_cleanup=True,models=0));receipt=OUT/'receipt_readback';receipt.mkdir(exist_ok=False)
 transport.upload_receipt(REC/'CLEANUP_RESULT.json',receipt)
 dump(REC/'FINALIZED.json',dict(closed=True,scientific_outcome=index['scientific_outcome'],remote_verified=True,necessary_raw_cleaned=True,all_source_and_member_sha_verified=True,release_url=index['release_url'],models=0));transport.upload_receipt(REC/'FINALIZED.json',receipt);shutil.rmtree(receipt)
 run(['git','add','--',str(REC.relative_to(R))]);run(['git','commit','-m','Record day gate evidence verification and bounded cache cleanup'])
 print(json.dumps(dict(remote_verified=True,release_url=index['release_url'],deleted_bytes=deleted)),flush=True)
if __name__=='__main__':
 OUT.mkdir(exist_ok=True);lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 {'prepare':prepare,'publish':publish}[sys.argv[1]]()
