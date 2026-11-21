"""Read only historical source; classify ownership seams without importing it."""
import ast,fcntl,hashlib,json,os,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;BASE=R/'experiments/v1281_partial_reconnection_fixed24'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));start=time.monotonic()
 with(O/'ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models=0),f)
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized'];assert time.time()<1795395600
  seen=set();usage=0
  for root,ds,fs in os.walk(R/'runs',followlinks=False):
   for p in [Path(root)]+[Path(root)/n for n in fs]:
    st=p.lstat();key=(st.st_dev,st.st_ino)
    if key not in seen:seen.add(key);usage+=st.st_blocks*512
  assert usage+554*1024**2<10*1024**3
  worker=read(BASE/'WORKER_FREEZE.json')['files'];parentfiles=read(BASE/'PARENT_BINDINGS.json')['files'];freeze=read(BASE/'SOURCE_FREEZE.json');known=dict(worker);known.update(parentfiles);known.update(freeze.get('files',{}));names=['worker.py','worker_context.py','route_dispatch.py','owner.py','live_entry.py','reconnect.py','base_safety.py','prestep.py'];rows=[]
  for name in names:
   p=BASE/name;key=str(p.relative_to(R));h=sha(p);assert known.get(key)==h,'HISTORICAL_SOURCE_SHA_BINDING_MISSING_OR_CHANGED:'+key;source=p.read_text();tree=ast.parse(source);functions=[]
   for fn in [x for x in ast.walk(tree)if isinstance(x,ast.FunctionDef)]:
    calls=[]
    for node in ast.walk(fn):
     if isinstance(node,ast.Call):
      label=ast.unparse(node.func)
      if any(x in label.lower()for x in ['predict','native','compute','pool','executor','affinity','step','reserve','factory','create','load','execute','renew']):calls.append(dict(line=node.lineno,call=label,expression=ast.unparse(node)[:600]))
    if calls:functions.append(dict(function=fn.name,first_line=fn.lineno,last_line=fn.end_lineno,calls=calls))
   rows.append(dict(path=key,sha256=h,functions=functions,static_inspection_only=True))
  reconnect=next(x for x in rows if x['path'].endswith('/reconnect.py'));text=(BASE/'reconnect.py').read_text();assert 'ProcessPoolExecutor(max_workers=4'in text and 'cpu=2+i%4'in text and 'kernel.predict'in text
  result=dict(closed=True,source_audit_completed=True,models=0,analytical_native=0,physical_native=0,Allocator_recomputations=0,replay_native=0,optimizer_calls=0,new_scientific_revision=False,all_selected_original_SHA_bound=True,rows=rows,source_count=len(rows),unresolved_dynamic_import_and_backend_paths=True,full_graph_coverage_not_established=True,historical_parallel_model_path_identified=True,not_currently_executable_under_CPU2_single_owner=True,old_deadlines_and_storage_caps_not_renewed=True,route_target='originalWE10060001 only; no fresh task',current_admission=False,allruns_allocated_bytes=usage,source_scope_peak_bytes=usage+554*1024**2,wall_s=time.monotonic()-start)
  assert time.monotonic()-start<120;raw=json.dumps(result,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<2*1024**2;(O/'RESULT.json').write_bytes(raw);(O/'CLOSED_SOURCE_INDEX.json').write_text(json.dumps({str(p.relative_to(R)):sha(p)for p in C.iterdir()if p.is_file()},indent=2)+'\n');print(json.dumps(dict(closed=True,source_count=len(rows),models=0,old_worker_not_executed=True,parallel_model_migration_needed=True)))
if __name__=='__main__':main()
