"""Offline curation: preserve complete trial accounting and selected raw evidence."""
import argparse,gzip,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('runs');p.add_argument('destination');p.add_argument('--selected',nargs='+',required=True);a=p.parse_args();root=Path(a.runs);dest=Path(a.destination);dest.mkdir(parents=True,exist_ok=False)
trials=[];blobs=dest/'source_blobs';blobs.mkdir()
def sha(b):return hashlib.sha256(b).hexdigest()
for run in sorted(x for x in root.iterdir()if x.is_dir()):
 completion=next(iter(run.rglob('completion.json')),None);protocol=next(iter(run.rglob('STATIC_PROTOCOL.json')),None)
 record={'run':run.name,'completion':None if completion is None else json.loads(completion.read_text()),'protocol':None if protocol is None else json.loads(protocol.read_text()),'source_hashes':{}}
 for source in sorted((run/'source_snapshot').glob('*.py')):
  b=source.read_bytes();h=sha(b);record['source_hashes'][source.name]=h
  target=blobs/(h+'.py')
  if not target.exists():target.write_bytes(b)
 for name in ['hard_floor_rejection.json','response.json','scene_geometry.json','sensor_geometry_sync.json','v648_nonphysical_mutation.json']:
  for f in sorted(run.rglob(name)):
   record.setdefault('diagnostics',{})[str(f.relative_to(run))]=json.loads(f.read_text())
 if completion is None:
  record['accounting']='No completion.json: infrastructure/probe only; do not count as completed navigation'
  for f in run.rglob('*.json'):
   if f.name in ['response.json','scene_geometry.json']:record.setdefault('probe',{})[f.name]=json.loads(f.read_text())
 # Interrupted branches retain a concise physical-accounting record even if
 # the regular result writer was not reached.
 for execution in sorted(run.rglob('v648_execution.jsonl')):
  if(execution.parent/'result.json').exists():continue
  lines=execution.read_text().splitlines()
  last=None if not lines else json.loads(lines[-1])
  record.setdefault('partial_branches',[]).append({'branch':str(execution.parent.relative_to(run)),'completed_public_steps':len(lines),'last_audited_execution':last,'status':'INTERRUPTED_OR_INFRASTRUCTURE_FAILED_NOT_COMPLETED_NAVIGATION'})
 # Keep the original console, compressed. It is not navigation success evidence by itself.
 console=next(iter(root.glob(run.name+'.console*')),None)
 if console is not None:
  target=dest/'consoles'/(run.name+'.txt.gz');target.parent.mkdir(exist_ok=True)
  with gzip.open(target,'wb') as stream:stream.write(console.read_bytes())
 trials.append(record)
(dest/'trial_ledger.json').write_text(json.dumps(trials,ensure_ascii=False,indent=2,allow_nan=False))
for name in a.selected:
 paired=root/name/'paired';assert paired.is_dir(),name
 target=dest/'selected'/name;target.mkdir(parents=True)
 for f in sorted(paired.rglob('*')):
  if not f.is_file() or any(part in {'cache','assets','frozen_original'}for part in f.relative_to(paired).parts):continue
  rel=f.relative_to(paired);to=target/rel;to.parent.mkdir(parents=True,exist_ok=True)
  if f.suffix in {'.json','.jsonl'}:
   with gzip.open(str(to)+'.gz','wb')as stream:stream.write(f.read_bytes())
  else:shutil.copy2(f,to)
 xml=paired/'assets'/'isolated_indoor.xml'
 if xml.exists():shutil.copy2(xml,target/'initial_scene.xml')
# Narrow map snapshots preserve the old endpoint-accumulation diagnosis without duplicating full runs.
for run,file in [('static_pilot_07_seed2','planning_0590.json'),('static_pilot_08_seed2','planning_0178.json')]:
 src=root/run/'paired'/'memory'/file
 if not src.exists():
  candidates=sorted((root/run/'paired'/'memory').glob('planning_*.json'));src=candidates[-1]if candidates else None
 if src:
  to=dest/'map_counterexamples'/(run+'.json.gz');to.parent.mkdir(exist_ok=True)
  with gzip.open(to,'wb')as stream:stream.write(src.read_bytes())
for name in ['perception_property_check.json']:
 if(root/name).exists():shutil.copy2(root/name,dest/name)
manifest=[]
for f in sorted(dest.rglob('*')):
 if f.is_file():manifest.append({'path':str(f.relative_to(dest)),'bytes':f.stat().st_size,'sha256':sha(f.read_bytes())})
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'trial_directories':len(trials),'selected_runs':a.selected,'curated_files':len(manifest),'curated_bytes':sum(x['bytes']for x in manifest)}))
