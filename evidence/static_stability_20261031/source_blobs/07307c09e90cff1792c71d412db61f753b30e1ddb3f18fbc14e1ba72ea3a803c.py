"""Preserve all attempts and source versions, with selected full evidence.
No simulation or deletion. Original runs may be cleaned only after verification.
"""
import argparse,gzip,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('runs');p.add_argument('destination');p.add_argument('--selected',nargs='+',required=True);a=p.parse_args();root=Path(a.runs);dest=Path(a.destination);dest.mkdir(parents=True,exist_ok=False)
def sha(b):return hashlib.sha256(b).hexdigest()
def compressed(src,to):
    to.parent.mkdir(parents=True,exist_ok=True)
    with gzip.GzipFile(str(to),'wb',mtime=0)as f:f.write(src.read_bytes())
blobs=dest/'source_blobs';blobs.mkdir();ledger=[];inventory=[]
for run in sorted(x for x in root.iterdir()if x.is_dir()):
    record={'run':run.name,'source_hashes':{},'metadata':{}};paired=run/'paired'
    for source in sorted((run/'source_snapshot').glob('*')):
        if not source.is_file():continue
        b=source.read_bytes();h=sha(b);record['source_hashes'][source.name]=h;to=blobs/(h+source.suffix)
        if not to.exists():to.write_bytes(b)
    for f in sorted(run.rglob('*')):
        if not f.is_file()or any(x in {'cache','assets','frozen_original','source_snapshot'}for x in f.relative_to(run).parts):continue
        rel=str(f.relative_to(run));inventory.append({'run':run.name,'path':rel,'bytes':f.stat().st_size,'sha256':sha(f.read_bytes())})
        if f.suffix=='.json' and not f.name.startswith(('planning_','trace')):
            record['metadata'][rel]=json.loads(f.read_text())
        elif f.name=='v648_execution.jsonl':
            lines=f.read_text().splitlines();record.setdefault('execution',{})[rel]={'public_samples':len(lines),'last':json.loads(lines[-1])if lines else None}
    if paired.exists():
        completion=paired/'completion.json';record['accounting']='COMPLETION_PRESENT'if completion.exists()else 'NO_COMPLETION_NOT_SUCCESS'
    ledger.append(record)
    for console in run.glob('*.console'):
        compressed(console,dest/'consoles'/(run.name+'__'+console.name+'.gz'))
for f in root.glob('*.json'):shutil.copy2(f,dest/f.name)
for name in a.selected:
    paired=root/name/'paired';assert paired.is_dir(),name
    for f in sorted(paired.rglob('*')):
        if not f.is_file()or any(x in {'cache','assets','frozen_original'}for x in f.relative_to(paired).parts):continue
        to=dest/'selected'/name/f.relative_to(paired);to.parent.mkdir(parents=True,exist_ok=True)
        if f.suffix in {'.json','.jsonl'}:compressed(f,Path(str(to)+'.gz'))
        else:shutil.copy2(f,to)
(dest/'trial_ledger.json').write_text(json.dumps(ledger,indent=2,ensure_ascii=False))
with gzip.GzipFile(str(dest/'original_inventory.json.gz'),'wb',mtime=0)as f:f.write(json.dumps(inventory,indent=2).encode())
manifest=[{'path':str(f.relative_to(dest)),'bytes':f.stat().st_size,'sha256':sha(f.read_bytes())}for f in sorted(dest.rglob('*'))if f.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'run_directories':len(ledger),'selected':a.selected,'files':len(manifest),'bytes':sum(x['bytes']for x in manifest)}))
