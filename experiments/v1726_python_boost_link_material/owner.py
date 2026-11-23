"""One exact material batch per once claim; no downloaded program is run."""
import argparse,fcntl,http.client,importlib.util,json,os,signal,subprocess,time,traceback,urllib.parse,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;ROOT=R/'runs'/C.name;D=R/'runs/v1727_python_boost_recovery'
read=lambda p:json.loads(p.read_text())
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 args=argparse.ArgumentParser();args.add_argument('--batch',required=True);opt=args.parse_args()
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));m=load('v1726_exact_materials',C/'materials.py');sha=m.sha
 owner_lock=(ROOT/'OWNER.lock').open('a+');fcntl.flock(owner_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 config=read(C/'CONFIG.json');assert sha(ROOT/'BATCHES_LOCKED.json')==config['plan_sha256'];plan=read(ROOT/'BATCHES_LOCKED.json');tasks={x['id']:x for x in plan['batches']};assert opt.batch in tasks;task=tasks[opt.batch]
 O=ROOT/'rounds'/opt.batch;O.mkdir(parents=True,exist_ok=True)
 assert not any((O/n).exists()for n in ['ONCE_CLAIM.json','RESULT.json','OWNED_CHILD.json'])
 cur=read(R/'CURRENT_EXPERIMENT.json');assert cur['active_round']is None and not cur['models_now_authorized'];assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 prior=ROOT/'rounds'/task['predecessor']if task['predecessor']else R/'runs/v1724_teb_focal_header_build';barrier=read(prior/'POST_ROUND_STORAGE_BARRIER.json');assert barrier['passed']and all(sha(R/n)==h for n,h in barrier['proof_paths_SHA256'].items())
 if(prior/'ONCE_CLAIM.json').exists():assert not Path('/proc',str(read(prior/'ONCE_CLAIM.json')['owner_pid'])).exists()
 for mapping in [plan['source_inputs_SHA256'],plan['host_tools_SHA256']]:assert all(sha(Path(n)if n.startswith('/')else R/n)==h for n,h in mapping.items())
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 sync=read(D/'SOURCE_SYNC_RESULT.json');assert sync['remote_verified'];sources=[C/n for n in ['owner.py','materials.py','prepare.py','PROTOCOL.md','CONFIG.json','link_inputs.py']]
 for p in sources:assert subprocess.check_output(['git','show',sync['head']+':'+str(p.relative_to(R))],cwd=R)==p.read_bytes()
 used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used+(224+32+32+512)*1024**2<15*1024**3
 meter=m.Meter(O);now=time.time();start=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 def guard(closing=False):
  cap=5400 if closing else 4200;assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.time()<now+cap and time.monotonic()<start+cap,'NATIVE_BATCH_DUAL_CLOCK'
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('NATIVE_BATCH5400_HARD_STOP')));signal.setitimer(signal.ITIMER_REAL,5400)
 meter.put(O/'ONCE_CLAIM.json',dict(owner_pid=os.getpid(),unix=now,monotonic=start,boot_id=boot,batch_id=task['id'],plan_sha256=config['plan_sha256'],source_commit=sync['head'],source_files_SHA256={str(p.relative_to(R)):sha(p)for p in sources},allruns_bytes=used,models_authorized=False))
 meter.put(O/'ROUND_WINDOW.json',dict(started_unix=now,started_monotonic=start,normal_end_unix=now+4200,normal_end_monotonic=start+4200,root_end_unix=now+5400,root_end_monotonic=start+5400,boot_id=boot))
 result=dict(passed=False,closed=False,batch_id=task['id'],package_downloads=0,package_executions=0,compiler_calls=0,optimizer_calls=0,models=0,physical_native=0,replay_native=0,method_outcome=None,first_error=None,package_reuses=0)
 connections={};requests=[];records=[];entries={};excluded=[];prefix=O/'sysroot';meter.mkdir(prefix);meter.mkdir(O/'packages')
 def connection(host):
  if host not in connections:connections[host]=http.client.HTTPSConnection(host,timeout=30)
  return connections[host]
 try:
  for ordinal,pkg in enumerate(task['packages'],1):
   guard();size=int(pkg['Size']);assert size<=32*1024**2;meter.permit(size+64*1024**2);file=O/'packages'/Path(pkg['Filename']).name;assert not file.exists()
   bases=[pkg['base_url']]
   bases.append('https://mirrors.ustc.edu.cn/ros/ubuntu'if pkg['source']=='ROS_SIGNED'else'https://archive.ubuntu.com/ubuntu')
   received=False
   reuse=R/'runs/v1712_root_member_materials/rounds/03_runtime_base_01/packages'/file.name
   if reuse.is_file():
    assert reuse.is_file()and reuse.stat().st_size==size and sha(reuse)==pkg['SHA256'];file=reuse;received=True;result['package_reuses']+=1
   for attempt,base in enumerate([]if received else bases,1):
    parsed=urllib.parse.urlsplit(base+'/'+pkg['Filename']);assert parsed.scheme=='https'and parsed.hostname in ['mirrors.tuna.tsinghua.edu.cn','mirrors.ustc.edu.cn','archive.ubuntu.com'];body=bytearray();row=dict(package=pkg['Package'],url=parsed.geturl(),attempt=attempt,passed=False)
    try:
     conn=connection(parsed.hostname);conn.request('GET',parsed.path,headers={'User-Agent':'Phase-exact-native-build-inputs','Accept-Encoding':'identity','Connection':'keep-alive'});response=conn.getresponse();assert response.status==200,('HTTP_STATUS',response.status)
     while True:
      guard();block=response.read(128*1024)
      if not block:break
      assert len(body)+len(block)<=size;body.extend(block)
     assert len(body)==size and hashlib.sha256(body).hexdigest()==pkg['SHA256'],'NATIVE_DEB_SHA_SIZE'
     meter.write(file,body);row.update(passed=True,bytes=len(body),sha256=pkg['SHA256']);received=True;result['package_downloads']+=1;break
    except Exception as error:
     row['error']=repr(error)
     if body:meter.write(O/'packages'/(file.name+'.attempt'+str(attempt)+'.partial'),body)
     if parsed.hostname in connections:connections.pop(parsed.hostname).close()
    finally:requests.append(row);meter.put(O/'REQUESTS.json',requests)
   assert received,('BOTH_EXACT_PACKAGE_CARRIERS_REFUSED',pkg['Package'])
   detail=m.extract(file,prefix,meter,pkg['Package'],entries,excluded);records.append(dict(pkg,deb_path=str(file.relative_to(R)),**detail));meter.reconcile()
   meter.put(O/'INTAKE_PROGRESS.json',dict(completed=ordinal,total=len(task['packages']),last_package=pkg['Package'],task_allocated_bytes=meter.total,models=0,package_execution=False))
  guard(closing=True)
  for row in entries.values():
   p=prefix/row['path']
   if row['type']in ['regular','hardlink']:assert not p.is_symlink()and p.stat().st_size==row['bytes']and sha(p)==row['sha256']and(p.lstat().st_mode&0o777)==row['mode']
   elif row['type']=='symlink':assert p.is_symlink()and os.readlink(p)==row['target']
   else:assert p.is_dir()and not p.is_symlink()
  meter.put(O/'PACKAGE_MANIFEST.json',dict(packages=records,original_debs_retained=True,plan_sha256=config['plan_sha256'],models=0),closing=True)
  meter.put(O/'UNPACK_MANIFEST.json',dict(prefix=str(prefix.relative_to(R)),entries=entries,excluded_entries=excluded,selected_materials_only_not_full_package_install=True,all_selected_SHA_size_mode_link_verified=True,host_uid_gid_replication_not_claimed=True,models=0),closing=True)
  actual=meter.reconcile();assert actual<224*1024**2
  result.update(passed=True,recovered_packages=len(records),selected_entries=len(entries),excluded_entries=len(excluded),all_selected_SHA_size_mode_link_verified=True,task_allocated_bytes_before_result=actual,ABI_or_build_qualified=False)
 except BaseException as error:result['first_error']=dict(error=repr(error),traceback=traceback.format_exc())
 finally:
  for conn in connections.values():conn.close()
  signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,wall_s=time.monotonic()-start,review_original=sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66',completed_extractions=len(records),download_attempts=len(requests),completed_package_records=records);meter.put(O/'RESULT.json',result,closing=True)
 print(json.dumps({k:v for k,v in result.items()if k!='completed_package_records'}),flush=True);return 0
if __name__=='__main__':raise SystemExit(main())
