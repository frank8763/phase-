"""Exact startup environment for the bounded repaired entry. No model imports."""
from pathlib import Path
import fcntl,hashlib,json,os,subprocess,sys,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    a=read(O/'USER_AUTHORIZATION.json')
    assert a.get('authorized') is True,'NO_NEW_ENTRY_AUTHORIZATION'
    assert not(O/'ROUND_WINDOW.json').exists()and not(O/'COMPLETION.json').exists(),'CLOSED_OR_STARTED_ENTRY'
    w=read(R/'runs/v1204_goal_audit_worker/ROUND_WINDOW.json')
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id']
    assert min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())>1700,'ORIGINAL_DEADLINE_RESERVE'
    for name in ['WORKER_FREEZE.json','CAMPAIGN_FREEZE.json','ENTRY_QUALIFICATION_FREEZE.json']:
        assert all(sha(R/p)==h for p,h in read(C/name)['files'].items()),name
    assert read(O/'QUALIFICATION.json')['passed'] and read(O/'FULL_CLI_QUALIFICATION.json')['passed']
    check=read(R/'runs/v1208_runtime_launch_environment/QUALIFICATION.json');assert check['passed']and check['models']==check['native_steps']==0
    lib=R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'
    assert sha(lib/'libOSMesa.so.8.0.0')==check['mesa_sha256']
    env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(lib),PYOPENGL_PLATFORM='osmesa',MUJOCO_GL='osmesa',CUDA_VISIBLE_DEVICES='',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    with (O/'campaign.console').open('x')as f:
        child=subprocess.Popen(['/usr/bin/taskset','-c','2','/usr/bin/nice','-n','19','/usr/bin/ionice','-c','3',sys.executable,'-B',str(C/'campaign.py')],cwd=R,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
    d=dict(submitted=True,pid=child.pid,proc_start=Path('/proc',str(child.pid),'stat').read_text().split()[21],submitted_unix=time.time(),original_deadline_unix=w['absolute_deadline_unix'],startup_library_directory=str(lib),scope=a['scope'])
    (O/'BACKGROUND_SUBMISSION.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d))
if __name__=='__main__':main()
