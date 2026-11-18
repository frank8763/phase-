"""New opt-in resource budget. Never inspects or controls another job."""
import os,subprocess
from pathlib import Path
CORES=(2,3,4,5)
def configure(core):
    assert core in CORES
    p=Path(f'/sys/devices/system/cpu/cpu{core}/topology');assert p.exists()
    for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
    os.environ['CUDA_VISIBLE_DEVICES']=''
    os.sched_setaffinity(0,{core});os.sched_setscheduler(0,os.SCHED_IDLE,os.sched_param(0))
    if os.getpriority(os.PRIO_PROCESS,0)<19:os.nice(19-os.getpriority(os.PRIO_PROCESS,0))
    subprocess.run(['ionice','-c','3','-p',str(os.getpid())],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3)
    return dict(pid=os.getpid(),affinity=sorted(os.sched_getaffinity(0)),scheduler=os.sched_getscheduler(0),nice=os.getpriority(os.PRIO_PROCESS,0),core_id=(p/'core_id').read_text().strip(),gpu_computation=False,other_processes_inspected=False)
