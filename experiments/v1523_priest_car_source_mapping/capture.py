"""One bounded immutable public-source capture; never execute an author module."""
import ast,fcntl,hashlib,json,os,time,urllib.request,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 data=json.dumps(v,indent=2,allow_nan=False).encode()+b'\n';assert len(data)<2*1024**2;t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(data);t.replace(p)
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));O.mkdir(exist_ok=True);start=time.monotonic()
 with(O/'ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models=0,sourcecapture=True,per_asset_attempts=1),f)
 result=dict(closed=False,source_capture_completed=False,models=0,analytical_native=0,physical_native=0,optimizer_calls=0,Allocator_recomputations=0,replay_native=0,author_imported_or_executed=False,rows=[],attempts=0,bytes=0)
 try:
  with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized'];assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
   seen=set();usage=0
   for root,ds,fs in os.walk(R/'runs',followlinks=False):
    for path in [Path(root)]+[Path(root)/n for n in fs]:
     st=path.lstat();key=(st.st_dev,st.st_ino)
     if key not in seen:seen.add(key);usage+=st.st_blocks*512
   assert usage+554*1024**2<10*1024**3
   tree_path=R/'runs/v1484_baseline_disposition_priest/TREE.json';tree=read(tree_path);prior=read(R/'runs/v1484_baseline_disposition_priest/AUTHOR_SOURCE_REVIEW.json');assert tree['sha']==prior['tree']and tree['truncated']is False;members={x['path']:x for x in tree['tree']if x['type']=='blob'}
   names=['priest/src/mpc_cem_dynamic.py','priest/src/mpc_expert.py','priest/src/planner_cem_dynamic.py','priest/src/planner_holonomic.py','point-to-point-navigation/2d_comparison/CEM.py','point-to-point-navigation/2d_comparison/Optim_part.py','point-to-point-navigation/2d_comparison/casadi_solver.py'];assert len(names)<=12
   assert all(n not in {x['path']for x in prior['source_members']}for n in names);assert sum(members[n]['size']for n in names)<=2*1024**2
   put(O/'CAPTURE_PLAN.json',dict(commit=prior['commit'],tree_sha=tree['sha'],tree_file_sha256=sha(tree_path),names=names,allruns_before_bytes=usage,reserved_peak_bytes=usage+554*1024**2))
   for name in names:
    assert time.time()+20<1795395600 and time.monotonic()-start<280
    row=members[name];assert row['size']<=512*1024;url='https://raw.githubusercontent.com/fatemeh-rastgar/PRIEST/'+prior['commit']+'/'+name;result['attempts']+=1
    request=urllib.request.Request(url,headers={'User-Agent':'Phase-bounded-source-review'})
    with urllib.request.urlopen(request,timeout=20)as stream:data=stream.read(row['size']+1)
    assert len(data)==row['size']and hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['sha'],'PINNED_GIT_BLOB_SIZE_OR_SHA_MISMATCH'
    target=O/'upstream'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);assert target.read_bytes()==data
    entry=dict(path=str(target.relative_to(R)),upstream_path=name,url=url,bytes=len(data),git_blob_sha1=row['sha'],sha256=hashlib.sha256(data).hexdigest(),raw_verified_before_parse=True)
    result['rows'].append(entry);result['bytes']+=len(data);put(O/'CAPTURE_PREFIX.json',result)
    parsed=ast.parse(data.decode());entry['functions']=[dict(name=x.name,first_line=x.lineno,last_line=x.end_lineno)for x in ast.walk(parsed)if isinstance(x,ast.FunctionDef)];entry['relevant_source_lines']=[dict(line=i,text=line)for i,line in enumerate(data.decode().splitlines(),1)if any(word in line.lower()for word in ['steer','curvature','num_distribution','decentral','wheelbase'])];put(O/'CAPTURE_PREFIX.json',result)
   result.update(source_capture_completed=True,all_exact_Gitblob_size_SHA256_readback=True,car_demo_mapping_established=False,interpretation='seven additional relevant members inspected only; exact paper car-case steering-cost and three-distribution recipe not mapped; not proof no such author implementation exists',scientific_revision_added=False)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  result.update(closed=True,wall_s=time.monotonic()-start);put(O/'RESULT.json',result);put(O/'CLOSED_SOURCE_INDEX.json',{str(p.relative_to(R)):sha(p)for p in C.iterdir()if p.is_file()});print(json.dumps({k:result[k]for k in ['closed','source_capture_completed','attempts','bytes','models','car_demo_mapping_established']if k in result}))
if __name__=='__main__':main()
