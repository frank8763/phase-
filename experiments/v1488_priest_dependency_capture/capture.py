"""Five fixed official release metadata reads. Never download or import a wheel."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback
import urllib.request
R=Path(__file__).resolve().parents[2];O=R/'runs/v1488_priest_dependency_capture'

def put(path,value):
 t=path.with_suffix(path.suffix+'.tmp');t.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');t.replace(path)
def used():
 seen=set();total=0
 for root,dirs,files in os.walk(R/'runs',followlinks=False):
  for p in [Path(root)]+[Path(root)/n for n in files]:
   s=p.lstat();key=(s.st_dev,s.st_ino)
   if key not in seen:seen.add(key);total+=s.st_blocks*512
 return total

def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 scope=json.loads((O/'METADATA_SCOPE.json').read_text());assert not(O/'ONCE_CLAIM.json').exists()
 with(O/'ONCE_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),started_unix=time.time(),models=0),f)
 def expired(*_):raise TimeoutError('DEPENDENCY_METADATA_SCOPE_EXPIRED')
 signal.signal(signal.SIGALRM,expired);signal.alarm(100)
 records=[];total=0
 try:
  parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text());assert parent['active_round']is None and not parent['models_now_authorized']
  assert time.time()<scope['absolute_root_deadline_unix']and used()+scope['maximum_total_response_bytes']+scope['root_reserve_bytes']<scope['all_runs_limit_bytes']
  from packaging.tags import sys_tags,parse_tag
  from packaging.requirements import Requirement
  from packaging.utils import canonicalize_name
  tags=set(sys_tags());chosen={};metadata=[]
  for package,version in scope['packages']:
   assert len(records)<scope['maximum_metadata_requests']and time.time()<scope['absolute_root_deadline_unix']
   url='https://pypi.org/pypi/'+package+'/'+version+'/json'
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Phase-bounded-dependency-source/1'}),timeout=15)as response:
    assert response.geturl()==url and response.status==200
    raw=response.read(scope['maximum_each_response_bytes']+1)
   assert len(raw)<=scope['maximum_each_response_bytes'];total+=len(raw);assert total<=scope['maximum_total_response_bytes']
   path=O/(package+'-'+version+'.pypi.json');path.write_bytes(raw)
   record=dict(name=package,version=version,url=url,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());records.append(record);put(O/'PARTIAL_INDEX.json',dict(records=records,total_bytes=total,models=0))
   data=json.loads(raw);assert canonicalize_name(data['info']['name'])==canonicalize_name(package)and data['info']['version']==version
   compatible=[]
   for row in data['urls']:
    name=row['filename']
    if row['packagetype']!='bdist_wheel'or row['yanked']or any(x in name.lower()for x in ['cuda','rocm']):continue
    wheel_tags=parse_tag('-'.join(name[:-4].split('-')[-3:]))
    if tags&wheel_tags:compatible.append(row)
   assert len(compatible)==1,('EXACT_ONE_NATIVE_WHEEL_REQUIRED',package,[x['filename']for x in compatible])
   row=compatible[0];assert row['url'].startswith('https://files.pythonhosted.org/')
   chosen[canonicalize_name(package)]=dict(name=package,version=version,filename=row['filename'],wheel_url=row['url'],bytes=row['size'],sha256=row['digests']['sha256'],requires_python=data['info']['requires_python'],requires_dist=data['info']['requires_dist']or[],wheel_not_downloaded=True,compatibility_not_runtime_qualified=True)
   metadata.append(data)
  versions={canonicalize_name(p):v for p,v in scope['packages']}
  for p in ['numpy','matplotlib']:versions[canonicalize_name(p)]=importlib.metadata.version(p)
  checks=[]
  for wheel in chosen.values():
   for text in wheel['requires_dist']:
    req=Requirement(text)
    if req.marker is not None and not req.marker.evaluate({'extra':''}):continue
    name=canonicalize_name(req.name);version=versions.get(name)
    if version is None:version=importlib.metadata.version(req.name)
    assert req.specifier.contains(version,prereleases=False),('DEPENDENCY_CONSTRAINT_REFUSED',text,version)
    checks.append(dict(package=wheel['name'],requirement=text,chosen_version=version,satisfied=True))
  put(O/'SELECTED_WHEELS.json',dict(wheels=list(chosen.values()),total_wheel_bytes=sum(x['bytes']for x in chosen.values()),active_dependency_constraints=checks,metadata_only=True,wheel_download_executed=False,install_executed=False,runtime_qualified=False))
  put(O/'COMPLETION.json',dict(passed=True,closed=True,scope='OFFICIAL_RELEASE_METADATA_ONLY',metadata_requests=len(records),total_metadata_bytes=total,records=records,all_active_declared_constraints_satisfied=True,canonical_interpreter=sys.executable,models=0,optimizer_calls=0,physical_native=0,author_or_JAX_imported=False,wheel_downloads=0,install_executed=False,runtime_qualified=False,closed_unix=time.time()))
 except BaseException as e:
  put(O/'FIRST_ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),partial_records=records,models=0))
  put(O/'COMPLETION.json',dict(passed=False,closed=True,metadata_requests=len(records),models=0,optimizer_calls=0,physical_native=0,runtime_qualified=False));raise
 finally:signal.alarm(0)
if __name__=='__main__':main()
