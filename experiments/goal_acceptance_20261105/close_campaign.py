"""One zero-model supplemental archive; review and commit explicit transferable files."""
import fcntl,gzip,json,os,signal,subprocess,time,zipfile
from pathlib import Path
from evidence_rules import dump,read,sha
repo=Path(__file__).resolve().parents[2];root=repo/'runs/goal_acceptance_20261105';own=Path(__file__).parent
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('ZERO_MODEL_CLOSURE_900S')));signal.alarm(900)
assert read(root/'ROUND_WINDOW.json')['round_closed']
assert(repo/'REVIEW_PENDING').read_bytes()==(root/'REVIEW_PENDING.before').read_bytes()
with(repo/'runs/v648_static_unknown/execution.lock').open('rb')as probe:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
if(root/'ZERO_MODEL_CLOSURE.json').exists():print('ALREADY_CLOSED_NO_OVERWRITE');raise SystemExit(0)
results=[]
for name in ['v827_goal_route_validation','v828_goal_dynamic_confirmation']:
 cfg=read(repo/'experiments'/name/'BATCH.json');stage=repo/cfg['output']
 if(stage/'ROUND_WINDOW.json').exists():
  assert read(stage/'ROUND_WINDOW.json')['round_closed'],'PHYSICS_WINDOW_NOT_CLOSED'
  assert(stage/'FINALIZED.json').exists(),'FINALIZE_EXISTING_CLOSED_STAGE_FIRST_NO_PHYSICS_RESTART'
  final=read(stage/'FINALIZED.json');assert final['source_and_decompressed_sha_verified']
  results.append(dict(stage=name,final=final,audit=read(stage/'FINAL_INDEPENDENT_AUDIT.json')))
for row in read(root/'qualification/ORIGINAL_MAIN_SOURCE_INVENTORY.json'):assert sha(repo/row['path'])==row['sha256'],'OLD_REFERENCE_CHANGED'
summary=dict(status=read(root/'COMPLETION.json')['status'],stages=results,new_models=0,new_integrations=0,old_v826_formal_status_preserved=True,raw_deleted=False,review_guard_restored=True,execution_lock_free=True,no_more_physics=True,report='docs/RPCCR_GOAL_ACCEPTANCE_20261105_REPORT.md')
dump(root/'ZERO_MODEL_CLOSURE.json',summary)
snap=root/'closure_snapshot';snap.mkdir()
for p in [repo/'CURRENT_EXPERIMENT.json',root/'LEDGER.json',repo/'RESEARCH_STATUS.md',repo/'docs/RPCCR_GOAL_ACCEPTANCE_20261105_REPORT.md']:(snap/p.name).write_bytes(p.read_bytes())
files={repo/'RPCCR_GOAL_ACCEPTANCE_AUTHORIZATION_20261105.json',repo/'docs/RPCCR_GOAL_ACCEPTANCE_20261105_PLAN.md',repo/'docs/RPCCR_GOAL_ACCEPTANCE_20261105_REPORT.md'}
for p in root.rglob('*'):
 if p.is_file()and not p.is_symlink()and p.suffix not in['.pyc','.lock']and p.name not in['close.console','GIT_SYNC_RESULT.json','GIT_SYNC_CLAIM.json']:files.add(p)
for name in ['v827_goal_route_validation','v828_goal_dynamic_confirmation']:
 stage=repo/'runs'/name
 for suffix in ['driver.console','finalize.console','transport.console','FINALIZED.json','FINAL_INDEPENDENT_AUDIT.json']:
  if(stage/suffix).exists():files.add(stage/suffix)
archive=repo/'evidence/rpccr_goal_acceptance_20261105_supplement';assert not archive.exists();archive.mkdir();entries=[]
with zipfile.ZipFile(archive/'saved_operations.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in sorted(files):
  row=dict(path=str(p.relative_to(repo)),bytes=p.stat().st_size,sha256=sha(p));entries.append(row);z.write(p,row['path'])
with zipfile.ZipFile(archive/'saved_operations.zip')as z:
 for row in entries:
  import hashlib
  raw=z.read(row['path']);assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']and sha(repo/row['path'])==row['sha256']
dump(archive/'RAW_INVENTORY.json',entries);dump(archive/'MANIFEST.json',[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p))for p in sorted(archive.iterdir())if p.is_file()])
dump(root/'CLOSURE_ARCHIVE_VERIFIED.json',dict(archive=str(archive.relative_to(repo)),source_and_decompressed_sha_verified=True,files=len(entries),raw_deleted=False))
# An explicit list excludes local original blobs and all symlinks. No blanket add.
paths={str(p.relative_to(repo))for d in [own,repo/'experiments/v827_goal_route_validation',repo/'experiments/v828_goal_dynamic_confirmation',archive]for p in d.rglob('*')if p.is_file()and not p.is_symlink()and p.stat().st_size<=90*1024**2 and p.suffix!='.pyc'}
paths.update(str(p.relative_to(repo))for p in[repo/'CURRENT_EXPERIMENT.json',repo/'RESEARCH_STATUS.md',repo/'RPCCR_GOAL_ACCEPTANCE_AUTHORIZATION_20261105.json',repo/'docs/RPCCR_GOAL_ACCEPTANCE_20261105_PLAN.md',repo/'docs/RPCCR_GOAL_ACCEPTANCE_20261105_REPORT.md',root/'LEDGER.json',root/'ZERO_MODEL_CLOSURE.json',root/'CLOSURE_ARCHIVE_VERIFIED.json'])
for item in results:
 final=item['final'];paths.add(final['report'])
 for d in [repo/final['archive'],repo/final['transport']if final.get('transport')else None]:
  if d is not None:paths.update(str(p.relative_to(repo))for p in d.rglob('*')if p.is_file()and p.stat().st_size<=90*1024**2)
pathsfile=root/'CLOSURE_STAGE_PATHS.nul';pathsfile.write_bytes(b'\0'.join(p.encode()for p in sorted(paths))+b'\0')
subprocess.run(['git','add','--pathspec-from-file='+str(pathsfile),'--pathspec-file-nul'],cwd=repo,check=True,timeout=120)
with(root/'CLOSURE_DIFF_STAT.txt').open('x')as stream:subprocess.run(['git','diff','--cached','--stat'],cwd=repo,stdout=stream,check=True,timeout=60)
print(json.dumps(dict(status='CLOSURE_ARCHIVED_AND_STAGED_REVIEW_DIFF_THEN_COMMIT',paths=len(paths),new_models=0,new_integrations=0)))
