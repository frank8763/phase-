"""Phase-only lowest-priority single-core policy; never inspect other jobs."""
import os,subprocess

_state=None
_pid=None
def apply():
 global _state,_pid
 if _pid==os.getpid():return _state
 os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['MUJOCO_GL']='osmesa'
 os.environ['PYOPENGL_PLATFORM']='osmesa';os.environ['LIBGL_ALWAYS_SOFTWARE']='1';os.environ['GALLIUM_DRIVER']='llvmpipe';os.environ['LP_NUM_THREADS']='1';os.environ['MESA_GLTHREAD']='false'
 from pathlib import Path
 lib=Path(__file__).resolve().parents[2]/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'
 real=lib/'libOSMesa.so.8.0.0'
 assert real.is_file()
 for name in ['libOSMesa.so.8','libOSMesa.so']:
  link=lib/name
  if not link.exists():link.symlink_to(real.name)
  assert link.resolve()==real.resolve(),'CPU_RENDERER_LINK_ESCAPED'
 os.environ['LD_LIBRARY_PATH']=str(lib)+((':'+os.environ['LD_LIBRARY_PATH'])if os.environ.get('LD_LIBRARY_PATH')and str(lib)not in os.environ['LD_LIBRARY_PATH']else'')
 for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
 assert 2 in os.sched_getaffinity(0),'PHASE_CPU2_NOT_AVAILABLE'
 os.sched_setaffinity(0,{2});priority=os.getpriority(os.PRIO_PROCESS,0)
 if priority<19:os.nice(19-priority)
 os.sched_setscheduler(0,os.SCHED_IDLE,os.sched_param(0))
 subprocess.run(['ionice','-c','3','-p',str(os.getpid())],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3)
 _pid=os.getpid();_state=dict(cpu_affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0),scheduler=os.sched_getscheduler(0),gpu_visible=os.environ['CUDA_VISIBLE_DEVICES'],mujoco_gl=os.environ['MUJOCO_GL'],io_class=3,stage_process_access=False)

 return _state
