"""Selected exact evidence restore; no model import, no simulation."""
import argparse,hashlib,json,urllib.request,subprocess,tarfile,tempfile,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];D=R/'records/nav2_v1077_v1078_20261112'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prefix',default='runs/v858_nav2_verified/v1078/');ap.add_argument('--model-only',action='store_true');args=ap.parse_args();assert args.prefix.startswith('runs/')and '..'not in Path(args.prefix).parts;index=json.loads((D/'RECORD_INDEX.json').read_text());base='https://github.com/frank8763/phase-/releases/download/'+index['release_tag']+'/';cache=R/'runs/v1077_v1078_restore_cache';cache.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory(dir=cache)as temp:
  temp=Path(temp)
  if args.model_only:
   x=index['selected_model_asset'];p=temp/x['name']
   with urllib.request.urlopen(base+x['name'],timeout=60)as src,p.open('xb')as out:shutil.copyfileobj(src,out,1048576)
   assert p.stat().st_size==x['compressed_bytes']and sha(p)==x['compressed_sha256'];out=cache/'canonical_NS.mjb'
   if out.exists():assert sha(out)==x['model_sha256']
   else:
    with out.open('xb')as f:subprocess.run(['zstd','-q','-dc',str(p)],stdout=f,check=True)
   assert out.stat().st_size==x['model_bytes']and sha(out)==x['model_sha256'];print(json.dumps(dict(passed=True,model_path=str(out),models_loaded=0,integrations=0)));return
  record=index['archives'][0]
  with urllib.request.urlopen(base+record['group']+'.INVENTORY.json',timeout=60)as f:inventory=json.load(f)['files']
  catalog={x['path']:x for x in inventory};parts=[];total=hashlib.sha256()
  for x in record['parts']:
   p=temp/x['name'];assert p.parent==temp
   with urllib.request.urlopen(base+x['name'],timeout=60)as src,p.open('xb')as out:shutil.copyfileobj(src,out,1048576)
   assert p.stat().st_size==x['bytes']and sha(p)==x['sha256'];parts.append(p)
   with p.open('rb')as f:
    for b in iter(lambda:f.read(1048576),b''):total.update(b)
  assert total.hexdigest()==record['archive_sha256'];cat=subprocess.Popen(['cat',*[str(p)for p in parts]],stdout=subprocess.PIPE);zstd=subprocess.Popen(['zstd','-q','-dc'],stdin=cat.stdout,stdout=subprocess.PIPE);cat.stdout.close();restored=0
  try:
   with tarfile.open(fileobj=zstd.stdout,mode='r|')as tar:
    for member in tar:
     assert member.isfile()and member.name in catalog
     if not member.name.startswith(args.prefix):continue
     p=R/member.name;assert not Path(member.name).is_absolute()and '..'not in Path(member.name).parts and p.resolve().is_relative_to(R);x=catalog[member.name]
     if p.exists():assert not p.is_symlink()and sha(p)==x['sha256'];continue
     p.parent.mkdir(parents=True,exist_ok=True)
     with tar.extractfile(member)as src,p.open('xb')as out:shutil.copyfileobj(src,out,1048576)
     assert p.stat().st_size==x['bytes']and sha(p)==x['sha256'];restored+=1
   assert zstd.wait()==0 and cat.wait()==0
  finally:
   for p in [zstd,cat]:
    if p.poll()is None:p.kill();p.wait()
  print(json.dumps(dict(passed=True,restored_files=restored,models=0,integrations=0)))
if __name__=='__main__':main()
