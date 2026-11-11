"""Restore only this relay's exact historical replay inputs, verifying all SHA."""
import hashlib,json,subprocess,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1047_day_relay_20261111';I=O/'inputs';index=json.loads((R/'records/nav2_v1039_20261111/RECORD_INDEX.json').read_text());record=index['archives'][0];part=record['parts'][0];p=I/part['name'];sha=lambda b:hashlib.sha256(b).hexdigest();assert p.stat().st_size==part['bytes']and sha(p.read_bytes())==part['sha256'];catalog={r['path']:r for r in json.loads((I/(record['group']+'.INVENTORY.json')).read_text())['files']};seen=set();selected=[];proc=subprocess.Popen(['zstd','-q','-dc',str(p)],stdout=subprocess.PIPE)
with tarfile.open(fileobj=proc.stdout,mode='r|')as tar:
 for member in tar:
  assert member.isfile()and member.name in catalog and member.name not in seen;row=catalog[member.name];h=hashlib.sha256();prefix='runs/v858_nav2_verified/v1039/approach/';suffix=member.name[len(prefix):]if member.name.startswith(prefix)else None;pick=I/'history'/suffix if suffix in ['physics/SETUP.json','physics/NATIVE_TRACE.npz','physics/BODY_COMMANDS.json','CAUSAL_EVIDENCE.json','FINAL_CAUSAL_SOURCE.json','RESULT.json']else None;target=None
  if pick:assert not pick.exists();pick.parent.mkdir(parents=True,exist_ok=True);target=pick.open('xb')
  stream=tar.extractfile(member)
  for block in iter(lambda:stream.read(1048576),b''):
   h.update(block)
   if target:target.write(block)
  if target:target.close()
  assert member.size==row['bytes']and h.hexdigest()==row['sha256'];seen.add(member.name)
  if pick:selected.append(dict(source=member.name,destination=str(pick.relative_to(R)),bytes=row['bytes'],sha256=row['sha256']))
while proc.stdout.read(1048576):pass
assert proc.wait(timeout=10)==0 and seen==set(catalog)and len(selected)==6
(O/'HISTORY_RESTORE.json').write_text(json.dumps(dict(passed=True,all_archive_members_verified=len(seen),selected=selected,models=0),indent=2)+'\n');p.unlink();print(json.dumps(dict(passed=True,restored=len(selected),all_members_verified=len(seen))))
