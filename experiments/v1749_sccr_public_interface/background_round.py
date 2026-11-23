"""One manually commanded background source round; no successor dispatch."""
import fcntl,hashlib,json,os,selectors,signal,subprocess,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
def put(p,v):
 temp=p.with_suffix(p.suffix+'.tmp');temp.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');temp.replace(p)
def main():
 os.sched_setaffinity(0,{5});begin=time.monotonic();wall=time.time();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert not(O/'BACKGROUND_ONCE_CLAIM.json').exists()and not(O/'SOURCE_OUTER_ONCE_CLAIM.json').exists()and not(O/'SOURCE_QUALIFICATION.json').exists()
 current=read(R/'CURRENT_EXPERIMENT.json');assert current['active_round']is None and current['active_math']is None and not current['models_now_authorized']
 original_review=(R/'REVIEW_PENDING').read_bytes()
 assert hashlib.sha256(original_review).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 put(O/'BACKGROUND_ONCE_CLAIM.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],boot_id=boot,started_unix=wall,started_monotonic=begin,maximum_wall_s=240,source_only=True,next_round_requires_new_user_command=True))
 current.update(status='BACKGROUND_SOURCE_ONLY_INTERFACE_QUALIFICATION',active_source_round=C.name,manual_review_after_every_round=True,automatic_next_round=False,models_now_authorized=False);put(R/'CURRENT_EXPERIMENT.json',current)
 process=None;console=bytearray();result=dict(passed=False,closed=False,models=0,physical_native=0,automatic_next_round=False,next_round_requires_new_user_command=True)
 try:
  process=subprocess.Popen(['taskset','-c','5','nice','-n','19',__import__('sys').executable,str(C/'source_owner.py')],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
  ident=dict(pid=process.pid,pgid=os.getpgid(process.pid),start_ticks=Path('/proc',str(process.pid),'stat').read_text().split()[21],boot_id=boot);put(O/'BACKGROUND_OWNED_SOURCE_OWNER.json',ident)
  selector=selectors.DefaultSelector();selector.register(process.stdout,selectors.EVENT_READ)
  while selector.get_map():
   assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.time()<wall+240 and time.monotonic()<begin+240
   for key,_ in selector.select(.2):
    block=os.read(key.fileobj.fileno(),16384)
    if not block:selector.unregister(key.fileobj);continue
    assert len(console)+len(block)<=512*1024;console.extend(block)
  process.wait(timeout=5);inner=read(O/'SOURCE_QUALIFICATION.json');outer=read(O/'SOURCE_OUTER_CLOSED.json')
  result.update(passed=bool(process.returncode==0 and inner['passed']and outer['passed']),returncode=process.returncode,source_qualification=inner,source_outer_closed=outer,source_recovery_pending=True,actual_navigation_authorized=False)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  if process is not None and process.poll()is None:
   stat=Path('/proc',str(process.pid),'stat').read_text().split();assert stat[21]==ident['start_ticks'];os.killpg(process.pid,signal.SIGTERM)
   try:process.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
  source_identity=O/'SOURCE_OWNED_CHILD.json'
  if source_identity.exists():
   owned=read(source_identity);statpath=Path('/proc')/str(owned['pid'])/'stat'
   if statpath.exists()and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==owned['boot_id']and statpath.read_text().split()[21]==owned['start_ticks']:
    os.killpg(owned['pgid'],signal.SIGTERM);end=time.monotonic()+5
    while statpath.exists()and time.monotonic()<end:time.sleep(.05)
    if statpath.exists()and statpath.read_text().split()[21]==owned['start_ticks']:os.killpg(owned['pgid'],signal.SIGKILL)
  try:
   with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
   (R/'REVIEW_PENDING').write_bytes(original_review)
  except BaseException as error:result.update(passed=False,safety_close_error=repr(error))
  (O/'background.console').write_bytes(console)
  result.update(closed=True,wall_s=time.monotonic()-begin,review_original=hashlib.sha256((R/'REVIEW_PENDING').read_bytes()).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66')
  put(O/'BACKGROUND_RESULT.json',result)
  text='# 本轮结果：等待用户审阅\n\n'+('源码软件资格通过。'if result['passed']else'本轮未通过，请查看原错误记录。')+'\n\n本轮仅检查原SCCR走廊core/六个原geometry helper绑定和当前因果/public输入；原planner查询/模型/导航/物理/重放均0。SOURCE通过不等于原算法query或导航通过。机制正式实验仍8/20关闭、12未执行。下一轮必须由用户看完结果后另下命令；没有自动启动phase04。当前query执行与整任务控制、安全、审核接口未获准入；下一步也不自动运行。\n'
  (O/'RESULT.md').write_text(text)
  current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='WAITING_USER_REVIEW_AFTER_SOURCE_QUALIFICATION',active_source_round=None,models_now_authorized=False,manual_review_after_every_round=True,automatic_next_round=False,latest_background_result=str((O/'BACKGROUND_RESULT.json').relative_to(R)),next_experiment='wait user review; no automatic SCCR query or navigation');put(R/'CURRENT_EXPERIMENT.json',current)
 print(json.dumps(dict(passed=result['passed'],closed=True,models=0,next_round_requires_new_user_command=True)));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
