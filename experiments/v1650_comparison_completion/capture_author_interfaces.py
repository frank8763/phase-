"""Bounded exact author-interface capture; never imports or executes author code."""
import base64,hashlib,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2]
D=R/'runs/v1650_comparison_completion/author_intake'
FILES={
 'TEB':['README.md','LICENSE','CMakeLists.txt','package.xml','include/teb_local_planner/planner_interface.h','include/teb_local_planner/optimal_planner.h','include/teb_local_planner/robot_footprint_model.h','src/optimal_planner.cpp'],
 'SVG_MPPI':['README.md','LICENSE','src/mppi_controller/CMakeLists.txt','src/mppi_controller/package.xml','src/mppi_controller/config/mppi_controller.yaml','src/mppi_controller/include/mppi_controller/mpc_base.hpp','src/mppi_controller/src/mpc_base.cpp','src/mppi_controller/include/mppi_controller/stein_variational_guided_mppi.hpp','src/mppi_controller/src/stein_variational_guided_mppi.cpp','src/mppi_controller/include/mppi_controller/common.hpp']}

def main():
 os.sched_setaffinity(0,{5})
 claim=D/'INTERFACE_CAPTURE_ONCE_CLAIM.json'
 with claim.open('x')as f:json.dump(dict(unix=time.time(),maximum_members=18,maximum_total_bytes=512*1024,models=0,source_execution=False),f)
 owners={x['method']:x for x in json.loads((D/'RESULT.json').read_text())['rows']}
 rows=[];used=0
 for label,names in FILES.items():
  tree=json.loads((D/(label+'_TREE.json')).read_text())
  objects={x['path']:x for x in tree['tree']if x['type']=='blob'}
  owner=owners[label];assert tree['sha']==owner['tree']
  for name in names:
   entry=objects[name];assert entry['size']<=128*1024 and used+entry['size']<=512*1024
   row=dict(method=label,repository=owner['repository'],commit=owner['commit'],path=name,git_blob_sha1=entry['sha'],expected_bytes=entry['size'],models=0)
   try:
    reply=subprocess.run([str(R/'tools/phase_storage_20261107/vendor/gh'),'api','repos/'+owner['repository']+'/git/blobs/'+entry['sha']],capture_output=True,timeout=20)
    assert reply.returncode==0,'BOUNDED_AUTHOR_BLOB_READ_REFUSED'
    blob=json.loads(reply.stdout);assert blob['sha']==entry['sha']and blob['encoding']=='base64'
    raw=base64.b64decode(blob['content']);assert len(raw)==entry['size']
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==entry['sha']
    raw.decode('utf-8');target=D/'upstream'/label/name;target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb')as f:f.write(raw)
    assert target.read_bytes()==raw
    used+=len(raw);row.update(passed=True,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),saved_path=str(target.relative_to(R)))
   except BaseException as error:row.update(passed=False,error=repr(error),retry_allowed=False)
   rows.append(row)
   (D/'INTERFACE_CAPTURE_PROGRESS.json').write_text(json.dumps(dict(rows=rows,bytes=used,models=0),indent=2)+'\n')
 result=dict(closed=True,passed=all(x['passed']for x in rows),rows=rows,bytes=used,read_requests=len(rows),models=0,physical_native=0,source_imported=False,compiled=False,interfaces_not_yet_runtime_qualified=True,recorded_unix=time.time())
 (D/'INTERFACE_CAPTURE_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=result['passed'],captured=sum(x['passed']for x in rows),planned=18,bytes=used,models=0)))
if __name__=='__main__':main()
