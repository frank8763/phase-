"""SHA-fixed release recovery using authenticated transport; never initializes ROS or a vehicle."""
import hashlib,json,os,subprocess,tarfile,tempfile,time,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v866_margin_qualification';GH=R/'tools/phase_storage_20261107/vendor/gh'
def main():
 which=sys.argv[1];index=R/('records/nav2_v856_20261107/RECORD_INDEX.json'if which=='runtime'else'records/nav2_v864_20261107/RECORD_INDEX.json');d=json.loads(index.read_text());group=next(x for x in d['archives']if x['group']==('v856-ros-runtime'if which=='runtime'else'v864-static-diagnosis-evidence'))
 def download(name):
  cache=O/'verified_transport_cache'/d['release_tag'];cache.mkdir(parents=True,exist_ok=True);target=cache/name
  if target.exists():return target.read_bytes()
  url=f'https://github.com/{d["repository"]}/releases/download/{d["release_tag"]}/{name}?phase_read={time.time_ns()}'
  proc=subprocess.run(['curl','--http1.1','-fLsS','--connect-timeout','10','--max-time','65',url],capture_output=True,timeout=70)
  if proc.returncode:
   (O/(which+'_DOWNLOAD_ERROR.json')).write_text(json.dumps(dict(name=name,returncode=proc.returncode,error=proc.stderr.decode(errors='replace'),models=0,integrations=0,at=time.time()),indent=2)+'\n')
   raise RuntimeError('RELEASE_DOWNLOAD_FAILED '+name)
  target.write_bytes(proc.stdout);return proc.stdout
 inventory=json.loads(download(group['group']+'.INVENTORY.json'));assert inventory['archive_sha256']==group['archive_sha256'];rows={x['path']:x for x in inventory['files']}
 selected=set(rows)if which=='runtime'else {name for name in rows if name.startswith(('runs/v858_nav2_verified/v864_static/main_ns/','runs/v865_global_margin_preparation/'))}
 with tempfile.TemporaryDirectory(dir=O)as temp:
  z=Path(temp)/'data.zst';whole=hashlib.sha256()
  with z.open('xb')as target:
   for part in group['parts']:
    data=download(part['name']);assert len(data)==part['bytes']and hashlib.sha256(data).hexdigest()==part['sha256'];target.write(data);whole.update(data)
  assert whole.hexdigest()==group['archive_sha256'];proc=subprocess.Popen(['zstd','-q','-dc',str(z)],stdout=subprocess.PIPE);seen=set();restored=[];links=[]
  try:
   with tarfile.open(fileobj=proc.stdout,mode='r|')as archive:
    for member in archive:
     assert member.name in rows and member.name not in seen;seen.add(member.name);row=rows[member.name];name=Path(member.name);assert not name.is_absolute()and'..'not in name.parts;p=R/name;assert p.resolve().is_relative_to(R)
     if row['type']=='symlink':
      assert member.issym()and member.linkname==row['link']and not Path(row['link']).is_absolute();assert(p.parent/row['link']).resolve().is_relative_to(R)
      if member.name in selected:links.append((p,row['link']));restored.append(member.name)
      continue
     assert member.isfile()and member.size==row['bytes'];data=archive.extractfile(member).read();assert hashlib.sha256(data).hexdigest()==row['sha256']
     if member.name not in selected:continue
     if p.exists():assert p.is_file()and not p.is_symlink()and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],'EXISTING_DIFFERENT '+str(p)
     else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);p.chmod(member.mode&0o777)
     restored.append(member.name)
   assert proc.wait(timeout=15)==0 and seen==set(rows)and set(restored)==selected
   for p,link in links:
    if p.is_symlink():assert os.readlink(p)==link
    else:assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.symlink_to(link)
  finally:
   if proc.poll()is None:proc.terminate();proc.wait()
 result=dict(passed=True,source=index.as_posix(),release=d['release_url'],group=group['group'],whole_and_members_sha_verified=True,restored_members=len(restored),all_group_members=len(rows),models=0,integrations=0,at=time.time());(O/(which+'_RESTORED.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
