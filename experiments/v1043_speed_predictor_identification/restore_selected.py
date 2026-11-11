"""Selective verified restoration; original output directories are never written."""
import hashlib,json,subprocess,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1043_speed_predictor_identification';I=O/'input';index=json.loads((R/'records/nav2_v1032_20261111/RECORD_INDEX.json').read_text());record=index['archives'][0];part=record['parts'][0];path=I/part['name'];sha=lambda b:hashlib.sha256(b).hexdigest();assert path.stat().st_size==part['bytes']and sha(path.read_bytes())==part['sha256'];inventory=json.loads((I/(record['group']+'.INVENTORY.json')).read_text())['files'];catalog={r['path']:r for r in inventory};seen=set();selected=[];proc=subprocess.Popen(['zstd','-q','-dc',str(path)],stdout=subprocess.PIPE)
with tarfile.open(fileobj=proc.stdout,mode='r|')as tar:
 for member in tar:
  assert member.isfile()and member.name in catalog and member.name not in seen;row=catalog[member.name];h=hashlib.sha256();pick=None
  for task in ['straight','left']:
   prefix='runs/v858_nav2_verified/v1032/'+task+'/'
   if member.name.startswith(prefix)and member.name[len(prefix):]in ['physics/SETUP.json','physics/NATIVE_TRACE.npz','physics/BODY_COMMANDS.json','REGENERATED_PROFILE.json','ACTUAL_INITIAL_PACKET.json','RESULT.json']:pick=I/'selected'/task/member.name[len(prefix):]
  target=None
  if pick:assert not pick.exists();pick.parent.mkdir(parents=True,exist_ok=True);target=pick.open('xb')
  stream=tar.extractfile(member)
  for block in iter(lambda:stream.read(1048576),b''):
   h.update(block)
   if target:target.write(block)
  if target:target.close()
  assert h.hexdigest()==row['sha256']and member.size==row['bytes'];seen.add(member.name)
  if pick:selected.append(dict(source=member.name,destination=str(pick.relative_to(R)),**row))
while proc.stdout.read(1048576):pass
assert proc.wait(timeout=10)==0 and seen==set(catalog);assert len(selected)==12
result=dict(passed=True,models=0,integrations=0,release_tag=index['release_tag'],all_archive_members_verified=len(seen),restored=selected,old_paths_untouched=True)
(O/'RESTORE.json').write_text(json.dumps(result,indent=2)+'\n');path.unlink();print(json.dumps(dict(passed=True,restored=len(selected),all_members_verified=len(seen))))
