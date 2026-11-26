"""Independent CPU6/7 lane owner; never modifies global REVIEW or model lock."""
from common import R,C,ROOT,O,LANE,LANES,read,put,sha,load,lane_usage
import fcntl,os,selectors,signal,subprocess,time,traceback

def main():
 assert LANE in LANES;os.sched_setaffinity(0,{LANES[LANE]});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));assert not(O/'OWNER_ONCE.json').exists()and not(O/'RESULT.json').exists()and not(O/'NATIVE_ONCE.json').exists()and not(O/'OWNED_CHILD.json').exists()
 lock=(O/'owner.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);source=read(ROOT/'SOURCE_FREEZE.json');recovery=read(ROOT/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert read(ROOT/'SOURCE_QUALIFICATION.json')['passed']and recovery['passed']and recovery['all_frozen_members_remote_chain_covered'];assert all(sha(R/n)==h for n,h in source['files'].items())
 start=time.monotonic();now=time.time();boot=__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip();put(O/'OWNER_ONCE.json',dict(pid=os.getpid(),cpu=LANES[LANE],lane=LANE,started_unix=now,maximum_wall_s=300));put(O/'ADMISSION.json',dict(lane=LANE,cpu=LANES[LANE],no_physics=True,constructor_cap=1,query_cap=1,source_freeze_sha256=sha(ROOT/'SOURCE_FREEZE.json'),input_sha256=sha(O/'INPUT.json'),recovery_sha256=sha(ROOT/'CURRENT_SOURCE_REMOTE_RECOVERY.json'),boot_id=boot,deadline_unix=now+300,deadline_monotonic=start+300))
 namespace=load('parallel_lane_namespace',C/'namespace.py');cmd,env=namespace.command(LANE,C/'native.py');result=dict(passed=False,closed=False,lane=LANE,cpu=LANES[LANE],first_error=None,MuJoCo_initializations=0,physics_native=0,replay_native=0,common_formal_tasks=0,controller_counts_unknown=True);p=None;console=bytearray();identity=None
 try:
  p=subprocess.Popen(['nice','-n','19','ionice','-c','3',*cmd],cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True);stat=__import__('pathlib').Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split();identity=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=stat[19],boot_id=boot,cpu=LANES[LANE]);put(O/'OWNED_CHILD.json',identity);sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
  with(O/'native.console').open('xb')as f:
   while sel.get_map():
    assert time.monotonic()-start<300 and time.time()<now+300 and __import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot,'LANE_DUAL_CLOCK_300S_STOP'
    for key,_ in sel.select(.1):
     block=os.read(key.fileobj.fileno(),16384)
     if not block:sel.unregister(key.fileobj);continue
     assert lane_usage()+len(block)+4096<8*1024**2,'MPPI_LANE_8MIB_EVIDENCE_CAP';assert len(console)+len(block)<=4*1024**2,'LANE_CONSOLE_4MIB_STOP';console.extend(block);f.write(block);f.flush()
  p.wait(timeout=5);machine=read(O/'RESULT.json');allsource=all(sha(R/n)==h for n,h in source['files'].items());result.update(passed=bool(p.returncode==0 and machine['passed']and machine['closed']and allsource),native_result_sha256=sha(O/'RESULT.json'),native_result=machine,controller_counts_unknown=False,all_source_SHA_after_child=allsource)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  if p is not None and p.poll()is None:
   stat=__import__('pathlib').Path('/proc',str(p.pid),'stat');assert stat.exists()and stat.read_text().split(') ',1)[1].split()[19]==identity['start_ticks'];os.killpg(identity['pgid'],signal.SIGTERM)
   try:p.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(identity['pgid'],signal.SIGKILL);p.wait(timeout=5)
  if p is not None:result['returncode']=p.returncode
  result.update(closed=True,wall_s=time.monotonic()-start,global_REVIEW_and_execution_lock_not_modified=True);put(O/'COMPLETION.json',result)
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
