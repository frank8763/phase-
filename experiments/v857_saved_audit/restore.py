"""Restore V857 evidence by explicit request, never launch physics or overwrite differences."""
import argparse,hashlib,json,shutil,subprocess,tarfile,tempfile,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];INDEX=R/'records/v857_20261107/RECORD_INDEX.json'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--verify-only',action='store_true');ap.add_argument('--interface',action='store_true');a=ap.parse_args();index=json.loads((INDEX.with_name('INTERFACE_RECORD_INDEX.json')if a.interface else INDEX).read_text());base=f'https://github.com/{index["repository"]}/releases/download/{index["release_tag"]}/';cache=R/'runs/v857_restore_cache';cache.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory(dir=cache)as temp:
  p=Path(temp)/index['archive_name'];h=hashlib.sha256();size=0
  with urllib.request.urlopen(base+index['archive_name'],timeout=120)as source,p.open('xb')as target:
   for b in iter(lambda:source.read(1048576),b''):target.write(b);h.update(b);size+=len(b)
  assert size==index['archive_bytes']and h.hexdigest()==index['archive_sha256'];expected={x['path']:x for x in index['files']};seen=set();z=subprocess.Popen(['zstd','-q','-dc',str(p)],stdout=subprocess.PIPE)
  try:
   with tarfile.open(fileobj=z.stdout,mode='r|')as tar:
    for m in tar:
     name=Path(m.name);assert m.isfile()and not name.is_absolute()and'..'not in name.parts and m.name in expected and m.name not in seen;seen.add(m.name);target=R/name;assert target.resolve().is_relative_to(R);assert not target.is_symlink();row=expected[m.name];h=hashlib.sha256();stream=tar.extractfile(m);old=None
     if a.verify_only:
      for b in iter(lambda:stream.read(1048576),b''):h.update(b)
     elif target.exists():
      assert target.is_file();old=hashlib.sha256()
      with target.open('rb')as f:
       for b in iter(lambda:f.read(1048576),b''):old.update(b)
      assert old.hexdigest()==row['sha256'],'EXISTING_FILE_DIFFERS_NO_OVERWRITE'
      for b in iter(lambda:stream.read(1048576),b''):h.update(b)
     else:
      target.parent.mkdir(parents=True,exist_ok=True)
      with target.open('xb')as f:
       for b in iter(lambda:stream.read(1048576),b''):f.write(b);h.update(b)
      target.chmod(m.mode&0o777)
     assert m.size==row['bytes']and h.hexdigest()==row['sha256']
   assert z.wait(timeout=20)==0 and seen==set(expected)
  finally:
   if z.poll()is None:z.terminate();z.wait()
 print('REMOTE_ARCHIVE_AND_EVERY_MEMBER_SHA_VERIFIED; physics not run. Temporary download removed.')
if __name__=='__main__':main()
