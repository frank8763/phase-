from common import R,C,S,O,read,put,sha,load
import fcntl,json,os,selectors,signal,subprocess,time,traceback
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));assert not(S/'OWNER_ONCE.json').exists()and not(S/'COMPLETION.json').exists()and not(O/'NATIVE_ONCE.json').exists()and not(O/'RESULT.json').exists();lock=(S/'owner.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert read(S/'SOURCE_QUALIFICATION.json')['passed']and read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed'];files=read(S/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());O.mkdir(exist_ok=True)
 start=time.monotonic();now=time.time();boot=R.joinpath('/proc/sys/kernel/random/boot_id').read_text().strip();put(S/'OWNER_ONCE.json',dict(pid=os.getpid(),unix=now,CPU7=True,models=0,maximum_wall_s=360));put(S/'ADMISSION.json',dict(no_physics=True,constructor_cap=1,query_cap=1,source_freeze_sha256=sha(S/'SOURCE_FREEZE.json'),recovery_sha256=sha(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json'),boot_id=boot,deadline_unix=now+300,deadline_monotonic=start+300));namespace=load('SVG_actual_readonly_namespace',C/'namespace.py');cmd,env=namespace.command(C/'native.py');result=dict(passed=False,closed=False,models=0,physics_native=0,replay_native=0,formal_common_tasks=0,first_error=None);p=None;i=None
 try:
  p=subprocess.Popen(['taskset','-c','7','nice','-n','19','ionice','-c','3',*cmd],cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True);i=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=R.joinpath('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],boot_id=boot,CPU=7);put(S/'OWNED_CHILD.json',i);sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ);total=0
  with(S/'native.console').open('xb')as f:
   while sel.get_map():
    assert time.monotonic()-start<360 and time.time()<now+360 and R.joinpath('/proc/sys/kernel/random/boot_id').read_text().strip()==boot,'SVG_OWNER_DUAL_CLOCK_STOP'
    assert sum(q.stat().st_blocks*512 for q in O.rglob('*')if q.is_file())<=1024**2,'SVG_NATIVE_OUTPUT_1MIB_CAP'
    for key,_ in sel.select(.2):
     b=os.read(key.fileobj.fileno(),16384)
     if not b:sel.unregister(key.fileobj);continue
     total+=len(b);assert total<=64*1024,'SVG_OWNER_CONSOLE_64KIB_CAP';f.write(b);f.flush()
  p.wait(timeout=5);machine=read(O/'RESULT.json');same=all(sha(R/n)==h for n,h in files.items());result.update(passed=bool(p.returncode==0 and machine['passed']and machine['closed']and same),native_result=machine,native_result_sha256=sha(O/'RESULT.json'),all_source_SHA_after=True if same else False)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  if p is not None and p.poll()is None:
   q=R.joinpath('/proc',str(p.pid),'stat');assert q.exists()and q.read_text().split(') ',1)[1].split()[19]==i['start_ticks'];os.killpg(i['pgid'],signal.SIGTERM)
   try:p.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(i['pgid'],signal.SIGKILL);p.wait(timeout=5)
  if p is not None:result['returncode']=p.returncode
  result.update(closed=True,wall_s=time.monotonic()-start,whole_navigation_passed=False,full_vehicle_safety_qualified=False,global_Phase_model_locks_REVIEW_and_MPPI_owner_not_modified=True);put(S/'COMPLETION.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
