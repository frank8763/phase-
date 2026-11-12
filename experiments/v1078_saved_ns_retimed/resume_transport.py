# Operational zero-model transport repair; no scientific task retry.
from pathlib import Path
import urllib.request,json,hashlib,time,subprocess,tarfile,shutil,sys
R=Path.cwd();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();O=R/'runs/v1077_speed125_response';rec=json.loads((R/'records/nav2_v1067_20261112/RECORD_INDEX.json').read_text())['archives'][0];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cache=O/'restore_cache';base='https://github.com/frank8763/phase-/releases/download/phase-causal-recovery-v1067-20261112/';errors=[]
for part in rec['parts']:
 p=cache/part['name']
 if p.stat().st_size==part['bytes']and sha(p)==part['sha256']:continue
 errors.append(dict(part=part['name'],bytes=p.stat().st_size,expected_bytes=part['bytes'],sha256=sha(p),expected_sha256=part['sha256'],never_accepted_as_evidence=True));(O/'TRANSPORT_TRUNCATION.json').write_text(json.dumps(dict(errors=errors,models=0,integrations=0),indent=2)+'\n');size=p.stat().st_size;assert 0<size<part['bytes'];req=urllib.request.Request(base+part['name'],headers={'Range':f'bytes={size}-','User-Agent':'Phase-evidence-resume'});
 with urllib.request.urlopen(req,timeout=30)as f:
  mode='ab'if f.status==206 and f.headers.get('Content-Range','').startswith(f'bytes {size}-')else'wb';assert f.status in [200,206]
  with p.open(mode)as out:shutil.copyfileobj(f,out,1048576)
 assert p.stat().st_size==part['bytes']and sha(p)==part['sha256'],'RESUMED_PART_SHA_FAILED'
parts=[cache/p['name']for p in rec['parts']];h=hashlib.sha256()
for p in parts:
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
assert h.hexdigest()==rec['archive_sha256'];cat=subprocess.Popen(['cat',*[str(p)for p in parts]],stdout=subprocess.PIPE);zstd=subprocess.Popen(['zstd','-q','-dc'],stdin=cat.stdout,stdout=subprocess.PIPE);cat.stdout.close();catalog={x['path']:x for x in json.loads((O/'ARCHIVE_INVENTORY.json').read_text())['files']};prefix='runs/v858_nav2_verified/v1067/A_main_north_south/physics/';wanted={prefix+x for x in ['NATIVE_TRACE.npz','BODY_COMMANDS.json','SENSORS.json.gz','CONTACTS.json.gz','INITIAL_STATE.npz','SETUP.json']};out=O/'restored_NS';seen=[]
try:
 with tarfile.open(fileobj=zstd.stdout,mode='r|')as tar:
  for member in tar:
   assert member.isfile()and member.name in catalog
   if member.name not in wanted:continue
   row=catalog[member.name];p=out/Path(member.name).name;assert p.parent==out and not p.exists()
   with tar.extractfile(member)as f,p.open('xb')as dest:shutil.copyfileobj(f,dest,1048576)
   assert p.stat().st_size==row['bytes']and sha(p)==row['sha256'];seen.append(dict(source_member=member.name,path=str(p.relative_to(R)),bytes=row['bytes'],sha256=row['sha256']))
 assert zstd.wait(timeout=10)==0 and cat.wait(timeout=10)==0 and len(seen)==len(wanted)
finally:
 for p in [zstd,cat]:
  if p.poll()is None:p.kill();p.wait()
(O/'RESTORED_NS.json').write_text(json.dumps(dict(passed=True,all_parts_sha_verified=True,archive_combined_sha_verified=True,selected_members_sha_verified=True,transport_truncation_retained=True,files=seen,models=0,integrations=0),indent=2)+'\n');shutil.rmtree(cache);print(json.dumps(dict(passed=True,files=len(seen),bytes=sum(x['bytes']for x in seen))),flush=True)
