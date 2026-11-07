"""Download public evidence, reconstruct archive and extract every member in temp."""
import hashlib,json,subprocess,tarfile,tempfile,time,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];REC=R/'records/nav2_v861_20261107'
def main():
 index=json.loads((REC/'RECORD_INDEX.json').read_text());group=index['archives'][0];base=f'https://github.com/{index["repository"]}/releases/download/{index["release_tag"]}/'
 with urllib.request.urlopen(base+group['group']+'.INVENTORY.json',timeout=60)as f:inventory=json.load(f)
 expected={x['path']:x for x in inventory['files']};assert inventory['archive_sha256']==group['archive_sha256'];cache=R/'runs/v861_restore_qualification';cache.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory(dir=cache)as folder:
  folder=Path(folder);archive=folder/'evidence.tar.zst';whole=hashlib.sha256()
  with archive.open('xb')as out:
   for row in group['parts']:
    size=0;h=hashlib.sha256()
    with urllib.request.urlopen(base+row['name'],timeout=120)as source:
     for b in iter(lambda:source.read(1048576),b''):out.write(b);whole.update(b);h.update(b);size+=len(b)
    assert size==row['bytes']and h.hexdigest()==row['sha256']
  assert whole.hexdigest()==group['archive_sha256'];proc=subprocess.Popen(['zstd','-q','-dc',str(archive)],stdout=subprocess.PIPE);seen=set();raw=0
  try:
   with tarfile.open(fileobj=proc.stdout,mode='r|')as tf:
    for member in tf:
     p=Path(member.name);assert not p.is_absolute()and'..'not in p.parts;assert member.name in expected and member.name not in seen;seen.add(member.name);row=expected[member.name];assert member.isfile()and row['type']=='file'and member.size==row['bytes'];target=folder/'expanded'/p;target.parent.mkdir(parents=True,exist_ok=True);source=tf.extractfile(member);h=hashlib.sha256()
     with target.open('xb')as out:
      for b in iter(lambda:source.read(1048576),b''):out.write(b);h.update(b);raw+=len(b)
     assert h.hexdigest()==row['sha256']
   assert proc.wait(timeout=20)==0 and seen==set(expected)
  finally:
   if proc.poll()is None:proc.terminate();proc.wait()
 result=dict(passed=True,public_part_download_sha_passed=True,whole_reassembly_sha_passed=True,actual_extracted_members_sha_passed=True,members=len(seen),raw_bytes=raw,model_initializations=0,model_integrations=0,temporary_restore_removed=True,verified_unix=time.time());(REC/'PUBLIC_RESTORE_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
