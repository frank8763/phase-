"""Exact original source intake for a standalone CPU compile, no code imports."""
import base64,hashlib,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1654_svg_cpu_core'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(v,indent=2)+'\n');t.replace(p)

def main():
 os.sched_setaffinity(0,{5})
 with(O/'CAPTURE_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),maximum_source_bytes=512*1024,models=0),f)
 selection=json.loads((O/'GRID_MAP_SELECTION.json').read_text())
 jobs=[dict(repository=selection['repository'],commit=selection['commit'],label='grid_map',**x)for x in selection['members']]
 original=R/'runs/v1650_comparison_completion/author_intake'
 tree=json.loads((original/'SVG_MPPI_TREE.json').read_text());members={x['path']:x for x in tree['tree']if x['type']=='blob'}
 for name in ['src/mppi_controller/include/mppi_controller/prior_samples_with_costs.hpp','src/mppi_controller/src/prior_samples_with_costs.cpp','src/mppi_controller/include/mppi_controller/mpc_template.hpp']:
  jobs.append(dict(repository='kohonda/proj-svg_mppi',commit='f4fb7b74f12d4568790213aab26dd6f0538d1925',label='SVG_MPPI',**members[name]))
 assert len(jobs)==41 and sum(x['size']for x in jobs)<=512*1024
 rows=[];total=0
 for item in jobs:
  row=dict(repository=item['repository'],commit=item['commit'],path=item['path'],git_blob_sha1=item['sha'],expected_bytes=item['size'])
  try:
   p=subprocess.run([str(R/'tools/phase_storage_20261107/vendor/gh'),'api','repos/'+item['repository']+'/git/blobs/'+item['sha']],capture_output=True,timeout=20)
   assert p.returncode==0,'BOUNDED_BLOB_FETCH_REFUSED'
   blob=json.loads(p.stdout);assert blob['sha']==item['sha']and blob['encoding']=='base64'
   raw=base64.b64decode(blob['content']);assert len(raw)==item['size']
   assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==item['sha']
   raw.decode('utf-8');target=O/'upstream'/item['label']/item['path'];target.parent.mkdir(parents=True,exist_ok=True)
   with target.open('xb')as stream:stream.write(raw)
   total+=len(raw);assert total<=512*1024 and target.read_bytes()==raw
   row.update(passed=True,sha256=sha(target),saved_path=str(target.relative_to(R)),bytes=len(raw))
  except BaseException as error:row.update(passed=False,error=repr(error),retry_allowed=False)
  rows.append(row);put(O/'CAPTURE_PROGRESS.json',dict(rows=rows,source_bytes=total,models=0))
 # Reuse existing exact Eigen package evidence; no package install or old rerun.
 eigen=R/'runs/v1340_overnight_preparation/headers/usr/include/eigen3'
 manifest=json.loads((R/'runs/v1340_overnight_preparation/ACTIVE_BUILD_HEADER_MANIFEST.json').read_text())
 eigen_files={str(p.relative_to(R)):sha(p)for p in eigen.rglob('*')if p.is_file()}
 assert eigen_files and (eigen/'Eigen/Core').is_file()
 put(O/'EIGEN_BUILD_INPUTS.json',dict(files=eigen_files,prior_manifest_path='runs/v1340_overnight_preparation/ACTIVE_BUILD_HEADER_MANIFEST.json',prior_manifest_sha256=sha(R/'runs/v1340_overnight_preparation/ACTIVE_BUILD_HEADER_MANIFEST.json'),models=0,no_install=True))
 result=dict(closed=True,passed=all(x['passed']for x in rows),members=len(rows),source_bytes=total,rows=rows,eigen_members=len(eigen_files),models=0,FFI_loads=0,compiled=False,recorded_unix=time.time())
 put(O/'CAPTURE_RESULT.json',result);print(json.dumps(dict(passed=result['passed'],members=len(rows),source_bytes=total,eigen_members=len(eigen_files),models=0)))

if __name__=='__main__':main()
