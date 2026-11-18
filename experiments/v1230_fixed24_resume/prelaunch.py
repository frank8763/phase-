"""Finish bounded zero-model storage/qualification, then launch exactly once."""
from pathlib import Path
import subprocess,json,hashlib,time,os,fcntl,traceback,sys
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;D=R/'records/nav2_v1228_checkpoint_20261116'
def read(p):return json.loads(p.read_text())
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def run(name,args,timeout,env):
 with(O/(name+'.console')).open('x')as log:
  p=subprocess.run(args,cwd=R,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
 assert p.returncode==0,name+' failed; retained logs, no model restart'

def main():
 assert not(O/'PRELAUNCH_STARTED.json').exists()and not(O/'ROUND_WINDOW.json').exists()
 dump(O/'PRELAUNCH_STARTED.json',dict(pid=os.getpid(),proc_start=Path('/proc/self/stat').read_text().split()[21],at=time.time(),models=0))
 end=time.monotonic()+900
 while not(D/'REMOTE_VERIFIED.json').exists():
  assert time.monotonic()<end,'REMOTE_READBACK_NOT_READY_NO_PHYSICAL_LAUNCH'
  if(D/'TRANSPORT03_ERROR.json').exists():raise AssertionError('ARCHIVE_TRANSPORT_FAILED_NO_PHYSICAL_LAUNCH')
  time.sleep(2)
 # Archive may be in its final few instructions while still holding the lock.
 f=(R/'runs/v648_static_unknown/execution.lock').open('a+')
 while True:
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);break
  except BlockingIOError:
   assert time.monotonic()<end,'LOCK_BUSY_NO_PHYSICAL_LAUNCH';time.sleep(1)
 fcntl.flock(f,fcntl.LOCK_UN)
 env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
 run('cleanup_parent',[sys.executable,'-B',str(C/'cleanup_parent.py')],90,env)
 # Bind every original scientific dependency, new operation and checkpoint.
 frozen=read(R/'experiments/v1228_terminal_reserve_confirmation/SOURCE_FREEZE.json')['files']
 for n,h in frozen.items():assert sha(R/n)==h,'INHERITED_SOURCE_CHANGED '+n
 for p in C.rglob('*'):
  if p.is_file()and '__pycache__'not in p.parts and p.name not in ['SOURCE_FREEZE.json','WORKER_FREEZE.json']:frozen[str(p.relative_to(R))]=sha(p)
 for p in O.rglob('*'):
  if p.is_file()and(p.name.endswith('_STATIC_SOURCE.json')or p.suffix=='.so' or p.name in ['CHECKPOINT_ROWS.json','CHECKPOINT_PAIRS.json']):frozen[str(p.relative_to(R))]=sha(p)
 for n in ['INVENTORY.json','REMOTE_VERIFIED.json','CLEANUP.json','CLEANUP_MANIFEST.json','ASSET_READBACKS.json']:
  p=D/n;frozen[str(p.relative_to(R))]=sha(p)
 for name in ['SOURCE_FREEZE.json','WORKER_FREEZE.json']:dump(C/name,dict(files=frozen,scientific_revisions=0))
 run('qualification',[sys.executable,'-B',str(C/'qualify.py')],240,env)
 assert read(O/'QUALIFICATION.json')['passed']and read(O/'ISOLATED_QUALIFICATION.json')['passed']
 assert not(O/'ROUND_WINDOW.json').exists()and not(O/'LAUNCH_RECEIPT.json').exists()
 auth=read(O/'AUTHORIZATION.json');auth.update(authorized=True,authorized_unix=time.time());dump(O/'AUTHORIZATION.json',auth)
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- 用户明确接受新独立3小时接续“好，开始下一步的实验”。V1230保持V1228科学0修订，原6已审核主/24t0/4NS开发及2精确重复检查点继承，新增只原7–24与主门后固定1/9/17；父V1228closed/20:30不改，合并仅称同科学同预注册池跨窗完成。GitHubRelease父10767成员压缩与每解压SHA回读后按清单清理父大件，保留main1完整重复基线；共享父+新2GiB/256MiB任务储备。接续源码、控制包、原模型/输入SHA不变，新增计数/基线/三正常首步/缓存2顺序/完整CLI和三隔离入口资格通过，准备一次模型前锁定10800秒双时钟离线后台启动。experiments/v1230_fixed24_resume/PROTOCOL.md。\n')
 run('start_once',[sys.executable,'-B',str(C/'start.py')],90,env)
 receipt=read(O/'LAUNCH_RECEIPT.json');dump(O/'PRELAUNCH_COMPLETED.json',dict(passed=True,qualification_complete=True,parent_backup_and_cleanup_verified=True,launch_receipt=receipt,new_window_locked=True,closed_unix=time.time()))
 print(json.dumps(dict(passed=True,stage='CAMPAIGN_LAUNCHED',**receipt)),flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as e:
  dump(O/'PRELAUNCH_ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),models_started=(O/'ROUND_WINDOW.json').exists(),no_automatic_retry=True));raise
