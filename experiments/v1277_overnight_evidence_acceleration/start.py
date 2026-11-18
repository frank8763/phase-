"""One bounded offline waiter; parent current batch is never touched."""
from pathlib import Path
import ast,datetime,fcntl,hashlib,json,os,subprocess,sys,time
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
def main():
    assert not(O/'LAUNCH_RECEIPT.json').exists()and not(O/'ROUND_WINDOW.json').exists(),'ONE_OVERNIGHT_NO_RESTART'
    auth=json.loads((O/'AUTHORIZATION.json').read_text());assert auth['authorized']and auth['models_authorized']is False
    qualification=json.loads((O/'QUALIFICATION.json').read_text())
    assert qualification['passed'],'NIGHT_QUALIFICATION_REQUIRED'
    assert all(hashlib.sha256((C/n).read_bytes()).hexdigest()==h for n,h in qualification['code_sha256'].items()),'QUALIFIED_CODE_CHANGED'
    assert auth['hard_stop_local']=='2026-11-18T09:00:00+08:00'
    ceiling=datetime.datetime.fromisoformat(auth['hard_stop_local']).timestamp();now=time.time();mono=time.monotonic();assert ceiling>now
    for p in C.glob('*.py'):ast.parse(p.read_text())
    # Freeze inherited parent science, operation and every night file before
    # the waiter is dispatched. Mutable parent results are checked after closure.
    base=json.loads((R/'experiments/v1275_time_window_fixed24/SOURCE_FREEZE.json').read_text())['files']
    def sha(p):
        h=hashlib.sha256()
        with p.open('rb')as f:
            for b in iter(lambda:f.read(1048576),b''):h.update(b)
        return h.hexdigest()
    assert all(sha(R/n)==v for n,v in base.items()),'PARENT_FROZEN_SOURCE_CHANGED'
    for p in C.glob('*'):
        if p.is_file()and p.name!='SOURCE_FREEZE.json':base[str(p.relative_to(R))]=sha(p)
    for p in[O/'AUTHORIZATION.json',O/'QUALIFICATION.json']:base[str(p.relative_to(R))]=sha(p)
    (C/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files=base),indent=2)+'\n')
    w=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=ceiling,hard_stop_monotonic=mono+(ceiling-now),
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),models_authorized=False,new_physical_integrations_authorized=False)
    (O/'ROUND_WINDOW.json').write_text(json.dumps(w,indent=2)+'\n')
    env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    with(O/'coordinator.console').open('x')as log:
        p=subprocess.Popen(['/usr/bin/nice','-n','19',sys.executable,'-B',str(C/'coordinator.py')],cwd=R,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    receipt=dict(pid=p.pid,proc_start=Path('/proc',str(p.pid),'stat').read_text().split()[21],zero_model_waiter=True,hard_stop_local=auth['hard_stop_local'],offline_capable=True)
    (O/'LAUNCH_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
