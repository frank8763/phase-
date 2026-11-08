"""Public HTTP1.1 download, all archive/member SHAs, actual one-member-at-a-time restore."""
import hashlib,json,subprocess,tarfile,tempfile,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];REC=R/'records/nav2_v867_20261108'
def download(url,path):subprocess.run(['curl','--http1.1','-fLsS','--connect-timeout','10','--max-time','120',url+'?phase_read='+str(time.time_ns()),'-o',str(path)],check=True,timeout=125)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def qualify(index,cache):
 base=f'https://github.com/{index["repository"]}/releases/download/{index["release_tag"]}/';cache.mkdir(parents=True,exist_ok=True);counts=[]
 with tempfile.TemporaryDirectory(dir=cache)as folder:
  folder=Path(folder)
  for g in index['archives']:
   inv=folder/'inventory.json';download(base+g['group']+'.INVENTORY.json',inv);inventory=json.loads(inv.read_text());assert inventory['archive_sha256']==g['archive_sha256'];expected={x['path']:x for x in inventory['files']};assert len(expected)==len(inventory['files']);archive=folder/'group.tar.zst';whole=hashlib.sha256()
   with archive.open('wb')as out:
    for part in g['parts']:
     p=folder/'part';download(base+part['name'],p);assert p.stat().st_size==part['bytes']and sha(p)==part['sha256']
     with p.open('rb')as f:
      for b in iter(lambda:f.read(1048576),b''):out.write(b);whole.update(b)
     p.unlink()
   assert whole.hexdigest()==g['archive_sha256'];proc=subprocess.Popen(['zstd','-q','-dc',str(archive)],stdout=subprocess.PIPE);seen=set();total=0
   try:
    with tarfile.open(fileobj=proc.stdout,mode='r|')as tf:
     for m in tf:
      p=Path(m.name);assert not p.is_absolute()and'..'not in p.parts and m.name in expected and m.name not in seen;row=expected[m.name];seen.add(m.name);assert row['type']=='file'and m.isfile()and m.size==row['bytes'];target=folder/'restored_member';h=hashlib.sha256()
      with target.open('xb')as out:
       source=tf.extractfile(m)
       for b in iter(lambda:source.read(1048576),b''):out.write(b);h.update(b);total+=len(b)
      assert h.hexdigest()==row['sha256']and sha(target)==row['sha256'];target.unlink()
    assert proc.wait(timeout=20)==0 and seen==set(expected)
   finally:
    if proc.poll()is None:proc.terminate();proc.wait(timeout=5)
   counts.append(dict(group=g['group'],actual_restored_members=len(seen),raw_bytes=total));archive.unlink()
 return dict(passed=True,groups=counts,public_part_download_sha_passed=True,whole_reassembly_sha_passed=True,actual_extracted_members_sha_passed=True,members=sum(x['actual_restored_members']for x in counts),model_initializations=0,integrations=0,temporary_restore_removed=True,at=time.time())
def main():
 result=qualify(json.loads((REC/'RECORD_INDEX.json').read_text()),R/'runs/v867_restore_qualification');(REC/'PUBLIC_RESTORE_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
