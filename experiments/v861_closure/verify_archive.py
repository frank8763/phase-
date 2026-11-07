"""Read-only source/member/part verification of the existing closed archive."""
import hashlib,json,subprocess,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];OUT=R/'runs/v861_startup_gate/cloud'
def digest(path):
 h=hashlib.sha256()
 with path.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 idx=json.loads((OUT/'RECORD_INDEX.json').read_text());group=idx['archives'][0];inventory=json.loads((OUT/(group['group']+'.INVENTORY.json')).read_text());expected={x['path']:x for x in inventory['files']};parts=group['parts'];assert len(parts)==1,'THIS_ROUND_HAS_ONE_PART'
 p=OUT/parts[0]['name'];assert digest(p)==parts[0]['sha256']==group['archive_sha256'];assert p.stat().st_size==parts[0]['bytes'];seen=set();changed=[];proc=subprocess.Popen(['zstd','-q','-dc',str(p)],stdout=subprocess.PIPE)
 try:
  with tarfile.open(fileobj=proc.stdout,mode='r|')as tf:
   for member in tf:
    assert member.name in expected and member.name not in seen;seen.add(member.name);row=expected[member.name];assert member.isfile()and member.size==row['bytes'];h=hashlib.sha256();stream=tf.extractfile(member)
    for b in iter(lambda:stream.read(1048576),b''):h.update(b)
    assert h.hexdigest()==row['sha256'];original=R/member.name
    if not original.is_file()or digest(original)!=row['sha256']:changed.append(member.name)
  assert proc.wait(timeout=20)==0 and seen==set(expected)
 finally:
  if proc.poll()is None:proc.terminate();proc.wait()
 result=dict(passed=not changed,source_members=len(seen),part_sha_verified=True,decompressed_members_sha_verified=True,source_changed_since_archive=changed,model_initializations=0,native_integrations=0);(R/'records/nav2_v861_20261107/LOCAL_ARCHIVE_READBACK.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed'];print(json.dumps(result))
if __name__=='__main__':main()
