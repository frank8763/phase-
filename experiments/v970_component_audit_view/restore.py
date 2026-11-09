"""Selectively restore only the latest real component for zero-model readback."""
import hashlib,json,shutil,subprocess,tarfile,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v970_component_audit_view';GH=R/'tools/phase_storage_20261107/vendor/gh'
index=json.loads((R/'records/nav2_v968_20261109/RECORD_INDEX.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();restored=[]
with tempfile.TemporaryDirectory(prefix='readback_',dir=O)as temporary:
 p=Path(temporary)
 subprocess.run([str(GH),'release','download',index['release_tag'],'--repo',index['repository'],'--dir',str(p)],check=True,timeout=120)
 for group in index['archives']:
  manifest=json.loads((p/(group['group']+'.INVENTORY.json')).read_text());catalog={x['path']:x for x in manifest['files']};combined=p/'component_archive.tar.zst';h=hashlib.sha256()
  with combined.open('xb')as target:
   for part in group['parts']:
    f=p/part['name'];assert sha(f)==part['sha256']and f.stat().st_size==part['bytes'];b=f.read_bytes();h.update(b);target.write(b)
  assert h.hexdigest()==group['archive_sha256'];decoder=subprocess.Popen(['zstd','-q','-dc',str(combined)],stdout=subprocess.PIPE)
  with tarfile.open(fileobj=decoder.stdout,mode='r|')as archive:
   for member in archive:
    path=Path(member.name)
    if not member.isfile()or not member.name.startswith('runs/v858_nav2_verified/v968/closed_handoff/'):continue
    assert not path.is_absolute()and '..'not in path.parts
    target=R/path;target.parent.mkdir(exist_ok=True,parents=True);record=catalog[member.name]
    with archive.extractfile(member)as stream,target.open('xb')as output:shutil.copyfileobj(stream,output)
    assert sha(target)==record['sha256'];restored.append(record)
  assert decoder.wait()==0
(O/'RESTORE_RECEIPT.json').write_text(json.dumps(dict(passed=True,restored=restored,models=0,integrations=0,release_url=index['release_url']),indent=2)+'\n')
print('restored files',len(restored),'bytes',sum(x['bytes']for x in restored))
