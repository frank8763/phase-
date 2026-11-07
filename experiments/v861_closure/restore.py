"""Restore one archived V858-V860 group on demand; verify parts, members, and no path escape."""
import argparse,hashlib,json,os,shutil,subprocess,tarfile,tempfile,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];INDEX=R/'records/nav2_v861_20261107/RECORD_INDEX.json'
def location(name):
 p=Path(name);assert not p.is_absolute()and'..'not in p.parts,'UNSAFE_ARCHIVE_PATH';target=R/p;assert target.resolve().is_relative_to(R),'PATH_ESCAPE';return target
def main():
 ap=argparse.ArgumentParser();ap.add_argument('group',nargs='?');ap.add_argument('--list',action='store_true');a=ap.parse_args();index=json.loads(INDEX.read_text())
 if a.list:
  print(json.dumps([{k:v for k,v in x.items()if k!='parts'}for x in index['archives']],indent=2));return
 group=next(g for g in index['archives']if g['group']==a.group);base=f'https://github.com/{index["repository"]}/releases/download/{index["release_tag"]}/'
 with urllib.request.urlopen(base+a.group+'.INVENTORY.json',timeout=60)as f:inventory=json.load(f)
 assert inventory['archive_sha256']==group['archive_sha256'];expected={x['path']:x for x in inventory['files']}
 cache=R/'runs/nav2_restore_cache';cache.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory(dir=cache)as temp:
  temp=Path(temp);combined=temp/'archive.tar.zst';whole=hashlib.sha256()
  with combined.open('xb')as combinedstream:
   for row in group['parts']:
    h=hashlib.sha256();size=0
    with urllib.request.urlopen(base+row['name'],timeout=120)as source:
     for b in iter(lambda:source.read(1048576),b''):combinedstream.write(b);h.update(b);whole.update(b);size+=len(b)
    assert size==row['bytes']and h.hexdigest()==row['sha256'],'PART_SHA_MISMATCH'
  assert whole.hexdigest()==group['archive_sha256'];process=subprocess.Popen(['zstd','-q','-dc',str(combined)],stdout=subprocess.PIPE);seen=set();links=[]
  try:
   with tarfile.open(fileobj=process.stdout,mode='r|')as archive:
    for member in archive:
     assert member.name in expected and member.name not in seen;seen.add(member.name);row=expected[member.name];target=location(member.name)
     if row['type']=='symlink':
      assert member.issym()and member.linkname==row['link'];assert not Path(member.linkname).is_absolute();assert(target.parent/member.linkname).resolve().is_relative_to(R);links.append((target,member.linkname));continue
     assert member.isfile()and member.size==row['bytes'];source=archive.extractfile(member);h=hashlib.sha256()
     if target.exists():
      assert target.is_file()and not target.is_symlink();old=hashlib.sha256()
      with target.open('rb')as f:
       for b in iter(lambda:f.read(1048576),b''):old.update(b)
      assert old.hexdigest()==row['sha256'],'EXISTING_FILE_DIFFERS_NO_OVERWRITE'
      for b in iter(lambda:source.read(1048576),b''):h.update(b)
     else:
      target.parent.mkdir(parents=True,exist_ok=True)
      with target.open('xb')as f:
       for b in iter(lambda:source.read(1048576),b''):f.write(b);h.update(b)
      target.chmod(member.mode&0o777)
     assert h.hexdigest()==row['sha256'],'DECOMPRESSED_MEMBER_SHA_MISMATCH'
   assert process.wait(timeout=20)==0 and seen==set(expected)
   for target,link in links:
    if target.is_symlink():assert os.readlink(target)==link
    else:assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True);target.symlink_to(link)
  finally:
   if process.poll()is None:process.terminate();process.wait()
 print('RESTORED: every part and member SHA verified; temporary compressed download removed.')
if __name__=='__main__':main()
