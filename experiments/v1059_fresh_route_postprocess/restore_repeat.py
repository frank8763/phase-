"""On-demand selected saved-state inputs; full streamed archive SHA checked."""
import hashlib,json,shutil,subprocess,tarfile,tempfile,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1056_fresh_route_regression';index=json.loads((R/'records/nav2_v1058_20261111/RECORD_INDEX.json').read_text());record=index['archives'][0];base='https://github.com/frank8763/phase-/releases/download/'+index['release_tag']+'/'
def main():
 assert not(O/'REPEAT_PREFIX_RESTORED.json').exists();seen=set();selected=[];whole=hashlib.sha256()
 with urllib.request.urlopen(base+record['group']+'.INVENTORY.json',timeout=20)as response:catalog={r['path']:r for r in json.load(response)['files']}
 with tempfile.TemporaryDirectory(dir=O,prefix='restore_')as temporary:
  parts=[]
  for row in record['parts']:
   p=Path(temporary)/row['name'];h=hashlib.sha256();size=0
   with urllib.request.urlopen(base+row['name'],timeout=60)as src,p.open('xb')as out:
    for b in iter(lambda:src.read(1048576),b''):out.write(b);h.update(b);whole.update(b);size+=len(b)
   assert size==row['bytes']and h.hexdigest()==row['sha256'];parts.append(p)
  assert whole.hexdigest()==record['archive_sha256'];cat=subprocess.Popen(['cat',*map(str,parts)],stdout=subprocess.PIPE);proc=subprocess.Popen(['zstd','-q','-dc'],stdin=cat.stdout,stdout=subprocess.PIPE);cat.stdout.close()
  with tarfile.open(fileobj=proc.stdout,mode='r|')as tar:
   for member in tar:
    assert member.isfile()and member.name in catalog and member.name not in seen;row=catalog[member.name];h=hashlib.sha256();prefix='runs/v858_nav2_verified/v1056/repeat_west_east/';suffix=member.name[len(prefix):]if member.name.startswith(prefix)else None;pick=R/member.name if suffix in ['physics/NATIVE_TRACE.npz','physics/SETUP.json','CAUSAL_EVIDENCE.json','RESULT.json']else None;target=None
    if pick:pick.parent.mkdir(parents=True,exist_ok=True);target=pick.open('xb')
    stream=tar.extractfile(member)
    for b in iter(lambda:stream.read(1048576),b''):
     h.update(b)
     if target:target.write(b)
    if target:target.close()
    assert h.hexdigest()==row['sha256']and member.size==row['bytes'];seen.add(member.name)
    if pick:selected.append(dict(source=member.name,path=str(pick.relative_to(R)),sha256=row['sha256'],bytes=row['bytes']))
  while proc.stdout.read(1048576):pass
  assert proc.wait()==0 and cat.wait()==0 and len(selected)==4 and seen==set(catalog)
 (O/'REPEAT_PREFIX_RESTORED.json').write_text(json.dumps(dict(passed=True,selected=selected,all_members_verified=len(seen),models=0,integrations=0),indent=2)+'\n');print(json.dumps(dict(passed=True,selected=len(selected),models=0)))
if __name__=='__main__':main()
