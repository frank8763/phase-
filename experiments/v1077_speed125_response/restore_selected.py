"""Bounded selected evidence restore; no model or integration imports."""
import sys,json,hashlib,urllib.request,concurrent.futures,subprocess,tarfile,shutil,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));from common import *
paths();from resource_policy import apply
apply();index=json.loads((R/'records/nav2_v1067_20261112/RECORD_INDEX.json').read_text());rec=index['archives'][0];base='https://github.com/frank8763/phase-/releases/download/'+index['release_tag']+'/';catalog={x['path']:x for x in json.loads((O/'ARCHIVE_INVENTORY.json').read_text())['files']};prefix='runs/v858_nav2_verified/v1067/A_main_north_south/physics/';wanted=[prefix+x for x in ['NATIVE_TRACE.npz','BODY_COMMANDS.json','SENSORS.json.gz','CONTACTS.json.gz','INITIAL_STATE.npz','SETUP.json']];cache=O/'restore_cache';cache.mkdir(exist_ok=False);out=O/'restored_NS';out.mkdir(exist_ok=False)
def get(part):
 p=cache/part['name'];assert p.parent==cache
 with urllib.request.urlopen(base+part['name'],timeout=45)as f,p.open('xb')as dest:shutil.copyfileobj(f,dest,1048576)
 assert p.stat().st_size==part['bytes']and sha(p)==part['sha256'];return p
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:parts=list(pool.map(get,rec['parts']))
h=hashlib.sha256()
for p in parts:
 with p.open('rb')as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
assert h.hexdigest()==rec['archive_sha256'];cat=subprocess.Popen(['cat',*[str(p)for p in parts]],stdout=subprocess.PIPE);zstd=subprocess.Popen(['zstd','-q','-dc'],stdin=cat.stdout,stdout=subprocess.PIPE);cat.stdout.close();seen=[]
try:
 with tarfile.open(fileobj=zstd.stdout,mode='r|')as tar:
  for member in tar:
   assert member.isfile()and member.name in catalog
   if member.name not in wanted:continue
   path=out/Path(member.name).name;row=catalog[member.name];assert path.parent==out and not path.exists()
   with tar.extractfile(member)as src,path.open('xb')as dest:shutil.copyfileobj(src,dest,1048576)
   assert path.stat().st_size==row['bytes']and sha(path)==row['sha256'];seen.append(dict(source_member=member.name,path=str(path.relative_to(R)),bytes=row['bytes'],sha256=row['sha256']))
 assert zstd.wait(timeout=10)==0 and cat.wait(timeout=10)==0 and len(seen)==len(wanted)
finally:
 for p in [zstd,cat]:
  if p.poll()is None:p.kill();p.wait()
result=dict(passed=True,all_parts_sha_verified=True,archive_combined_sha_verified=True,selected_members_sha_verified=True,files=seen,models=0,integrations=0);dump(O/'RESTORED_NS.json',result);shutil.rmtree(cache);print(json.dumps(dict(passed=True,selected_files=len(seen),selected_bytes=sum(x['bytes']for x in seen))))
