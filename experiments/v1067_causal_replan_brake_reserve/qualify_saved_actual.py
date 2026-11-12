"""New saved auditor on the archived V1056 actual main; zero new models."""
import sys,json,urllib.request,shutil,subprocess,tarfile,tempfile,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from resource_policy import apply
apply()
from kernel import *
import archive as arc
index=json.loads((R/'records/nav2_v1056_20261111/RECORD_INDEX.json').read_text());record=index['archives'][0];base='https://github.com/frank8763/phase-/releases/download/'+index['release_tag']+'/';prefix='runs/v858_nav2_verified/v1056/main_west_east/';cache=O/'qualification_readback';cache.mkdir(exist_ok=False);restored=[]
try:
 with urllib.request.urlopen(base+record['group']+'.INVENTORY.json?phase_readback=v1067-20261112',timeout=60)as f:inventory=json.load(f)['files']
 def provider(part):
  path=cache/part['name']
  with urllib.request.urlopen(base+part['name']+'?phase_readback=v1067-20261112',timeout=60)as source,path.open('xb')as out:shutil.copyfileobj(source,out,1048576)
  observed=dict(name=part['name'],expected_bytes=part['bytes'],actual_bytes=path.stat().st_size,expected_sha256=part['sha256'],actual_sha256=arc.sha(path),read_only_no_sync=True);dump(O/('RESTORE_'+part['name']+'.json'),observed)
  return path,False
 arc.verify(record,inventory,provider);cat=subprocess.Popen(['cat',*[str(cache/p['name'])for p in record['parts']]],stdout=subprocess.PIPE);zstd=subprocess.Popen(['zstd','-q','-dc'],stdin=cat.stdout,stdout=subprocess.PIPE);cat.stdout.close();lookup={x['path']:x for x in inventory}
 with tarfile.open(fileobj=zstd.stdout,mode='r|')as tar:
  for member in tar:
   if not member.name.startswith(prefix):continue
   path=R/member.name;row=lookup[member.name];assert member.isfile()and path.resolve().is_relative_to(R)
   if path.exists():assert arc.sha(path)==row['sha256'];continue
   path.parent.mkdir(parents=True,exist_ok=True)
   with tar.extractfile(member)as source,path.open('xb')as out:shutil.copyfileobj(source,out,1048576)
   assert arc.sha(path)==row['sha256'];restored.append(row)
 assert zstd.wait()==0 and cat.wait()==0
finally:shutil.rmtree(cache)
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from audit import audit_native
out=R/prefix;fixture=O/'saved_actual_fixture';fixture.mkdir(exist_ok=False)
for original in out.rglob('*'):
 if original.is_file():
  path=fixture/original.relative_to(out);path.parent.mkdir(parents=True,exist_ok=True);path.symlink_to(original)
segments=[]
for label in ['STATIC','BRAKE','APPROACH']:
 journal=out/(label+'_EXECUTION.json')
 if journal.exists():
  j=json.loads(journal.read_text());segments.append(dict(path=str((out/(label+'_PLAN.json')).relative_to(R)),origin_native=j['origin_native'],executed_native=j['executed_native'],label=label))
dump(fixture/'DIRECT_SEGMENTS.json',segments);setup=json.loads((out/'physics/SETUP.json').read_text());preflight=O/'PREFLIGHTS.json';assert not preflight.exists();dump(preflight,dict(qualified_archived_input=dict(setup=setup)))
try:
 task=dict(output=str(fixture),case_id='WEST_EAST',goal_xy=[4.,-2.],preflight_task_id='qualified_archived_input');audit_out=O/'qualification_actual_audit';proof=audit_native(task,audit_out);assert proof['passed'];shutil.copyfile(audit_out/'FINAL_INDEPENDENT_AUDIT.json',O/'QUALIFIED_ARCHIVED_ACTUAL_AUDIT.json');dump(O/'SAVED_ACTUAL_QUALIFICATION.json',dict(passed=True,scope='new generic saved auditor on archived V1056 actual main; zero new models',original_release=index['release_tag'],source_members_SHA_verified=True,fully_audited_native=50728,restored_files=len(restored),models=0,integrations=0));dump(O/'SAVED_ACTUAL_RESTORE_RECEIPT.json',dict(restored_files=restored,old_release=index['release_tag'],all_source_SHA_verified=True));print(json.dumps(dict(passed=True,fully_audited_native=50728,models=0)))
finally:preflight.unlink()
