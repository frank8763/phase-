"""Restore V1061 software evidence on demand, with all source/part hashes."""
import argparse,hashlib,importlib.util,json,shutil,subprocess,tarfile,tempfile,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];D=R/'records/nav2_v1067_20261112';TAG='phase-causal-recovery-v1067-20261112';BASE='https://github.com/frank8763/phase-/releases/download/'+TAG+'/'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prefix',default='runs/v858_nav2_verified/v1067/');a=ap.parse_args();assert not Path(a.prefix).is_absolute()and '..'not in Path(a.prefix).parts
 index=json.loads((D/'RECORD_INDEX.json').read_text());assert index['release_tag']==TAG;record=index['archives'][0];spec=importlib.util.spec_from_file_location('v1061_restore_archive',R/'experiments/v1067_causal_replan_brake_reserve/archive.py');arc=importlib.util.module_from_spec(spec);spec.loader.exec_module(arc)
 cache=R/'runs/v1067_restore_cache';cache.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory(dir=cache)as temporary:
  temp=Path(temporary)
  with urllib.request.urlopen(BASE+record['group']+'.INVENTORY.json',timeout=60)as f:inventory=json.load(f)['files']
  def provider(part):
   name=part['name'];assert Path(name).name==name;path=temp/name
   with urllib.request.urlopen(BASE+name,timeout=60)as src,path.open('xb')as out:shutil.copyfileobj(src,out,1048576)
   return path,False
  arc.verify(record,inventory,provider);catalog={row['path']:row for row in inventory};cat=subprocess.Popen(['cat',*[str(temp/p['name'])for p in record['parts']]],stdout=subprocess.PIPE);zstd=subprocess.Popen(['zstd','-q','-dc'],stdin=cat.stdout,stdout=subprocess.PIPE);cat.stdout.close();restored=[]
  try:
   with tarfile.open(fileobj=zstd.stdout,mode='r|')as tar:
    for member in tar:
     assert member.isfile()and member.name in catalog
     if not member.name.startswith(a.prefix):continue
     path=R/member.name;assert not Path(member.name).is_absolute()and '..'not in Path(member.name).parts and path.resolve().is_relative_to(R);row=catalog[member.name]
     if path.exists():assert not path.is_symlink()and arc.sha(path)==row['sha256'];continue
     path.parent.mkdir(parents=True,exist_ok=True)
     with tar.extractfile(member)as src,path.open('xb')as out:shutil.copyfileobj(src,out,1048576)
     assert arc.sha(path)==row['sha256'];restored.append(member.name)
   assert zstd.wait()==0 and cat.wait()==0
  finally:
   for p in [zstd,cat]:
    if p.poll()is None:p.kill();p.wait()
 print(json.dumps(dict(passed=True,restored_files=len(restored),all_parts_and_members_SHA_verified=True,models=0)))
if __name__=='__main__':main()
