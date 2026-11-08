"""Selective, immutable public evidence recovery; no ROS/model execution."""
import hashlib,json,subprocess,tarfile,tempfile,time,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v864_rpp_static_regression'
def main():
 idx=json.loads((R/'records/nav2_v863_execution_20261107/RECORD_INDEX.json').read_text());g=idx['archives'][0];base=f'https://github.com/{idx["repository"]}/releases/download/{idx["release_tag"]}/'
 gh=R/'tools/phase_storage_20261107/vendor/gh'
 inventory=json.loads(subprocess.run([str(gh),'release','download',idx['release_tag'],'--repo',idx['repository'],'--pattern',g['group']+'.INVENTORY.json','--output','-'],capture_output=True,check=True,timeout=45).stdout)
 rows={r['path']:r for r in inventory['files']};frozen=json.loads((R/'experiments/v863_rpp_preparation/SOURCE_FREEZE.json').read_text())['files'];selected={name for name in frozen if not(R/name).is_file()};selected|={name for name in rows if name.startswith('runs/v858_nav2_verified/v863_rpp_static/')};assert selected<=set(rows)
 with tempfile.TemporaryDirectory(dir=O)as folder:
  z=Path(folder)/'evidence.zst';whole=hashlib.sha256()
  with z.open('xb')as target:
   for part in g['parts']:
    h=hashlib.sha256();size=0
    data=subprocess.run([str(gh),'release','download',idx['release_tag'],'--repo',idx['repository'],'--pattern',part['name'],'--output','-'],capture_output=True,check=True,timeout=60).stdout
    target.write(data);h.update(data);whole.update(data);size=len(data)
    assert size==part['bytes']and h.hexdigest()==part['sha256']
  assert whole.hexdigest()==g['archive_sha256'];proc=subprocess.Popen(['zstd','-q','-dc',str(z)],stdout=subprocess.PIPE);seen=set();restored=[]
  try:
   with tarfile.open(fileobj=proc.stdout,mode='r|')as archive:
    for member in archive:
     assert member.name in rows and member.name not in seen;seen.add(member.name);row=rows[member.name];assert member.isfile()and row['type']=='file'and member.size==row['bytes'];source=archive.extractfile(member);h=hashlib.sha256();data=source.read();h.update(data);assert h.hexdigest()==row['sha256']
     if member.name not in selected:continue
     name=Path(member.name);assert not name.is_absolute()and'..'not in name.parts;p=R/name;assert p.resolve().is_relative_to(R)
     if p.exists():assert p.is_file()and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
     else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);p.chmod(member.mode&0o777)
     restored.append(member.name)
   assert proc.wait(timeout=15)==0 and seen==set(rows)and set(restored)==selected
  finally:
   if proc.poll()is None:proc.terminate();proc.wait()
 result=dict(passed=True,release=idx['release_url'],whole_archive_sha_verified=True,all_members_sha_verified=len(seen),selected_members=len(restored),paths=restored,model_initializations=0,integrations=0,verified_unix=time.time());(O/'RESTORED_INPUTS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='paths'}))
if __name__=='__main__':main()
