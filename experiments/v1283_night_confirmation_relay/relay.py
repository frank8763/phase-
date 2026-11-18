"""One offline dispatch; failure never chooses a new candidate or retries."""
from pathlib import Path
import fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
P=R/'runs/v1280_slot24_repeat_clock';NEXT=R/'runs/v1281_partial_reconnection_fixed24'
END=1794963600.
def read(p):return json.loads(p.read_text())
def dump(p,x):
    t=p.with_suffix('.tmp');t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def alive(d):
    try:s=Path('/proc',str(d['pid']),'stat').read_text().split();return s[2]!='Z'and s[21]==str(d['proc_start'])
    except FileNotFoundError:return False
def decide(d,f):
    return bool(d.get('closed')and d.get('passed')and d.get('slot24_main_repeat_development_passed')and d.get('source_unchanged')and d.get('guard_original')and f.get('closed')and f.get('manifest_readback')and f.get('slot24_main_repeat_development_passed'))
def main():
    assert not(O/'STARTED.json').exists()and not(NEXT/'ROUND_WINDOW.json').exists(),'ONE_NIGHT_RELAY_NO_RESTART'
    lock=(O/'relay.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    frozen=read(C/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
    w=read(O/'ROUND_WINDOW.json');assert w['absolute_deadline_unix']==END
    dump(O/'STARTED.json',dict(pid=os.getpid(),proc_start=Path('/proc/self/stat').read_text().split()[21],models=0,physical_native=0))
    launch=read(P/'LAUNCH_RECEIPT.json');watch=read(P/'WATCHDOG_LAUNCH.json');pw=read(P/'ROUND_WINDOW.json')
    reason='UNKNOWN';error=None;started=False;child=None
    def halt(*_):raise TimeoutError('NIGHT_09_HARD_STOP')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt)
    signal.setitimer(signal.ITIMER_REAL,max(.1,min(END-time.time(),w['hard_stop_monotonic']-time.monotonic())-10))
    try:
        while True:
            assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id'],'BOOT_CHANGED_NO_RESUME'
            assert min(END-time.time(),w['hard_stop_monotonic']-time.monotonic())>10980,'INSUFFICIENT_NIGHT_FOR_FIXED_3H_NO_LAUNCH'
            if(P/'COMPLETION.json').exists()and not read(P/'COMPLETION.json').get('passed'):
                reason='PARENT_FAILED_NO_CONFIRMATION';break
            if(P/'FINALIZED.json').exists()and not alive(launch)and not alive(watch):
                assert decide(read(P/'COMPLETION.json'),read(P/'FINALIZED.json')),'PARENT_FULL_GATE_FAILED'
                assert all(sha(R/n)==h for n,h in frozen.items()),'NIGHT_FROZEN_SOURCE_CHANGED'
                f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
                assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
                c=R/'experiments/v1281_partial_reconnection_fixed24'
                for name,seconds in [('qualify.py',180),('freeze_ready.py',120),('start.py',120)]:
                    with(O/(name+'.console')).open('x')as log:
                        child=subprocess.Popen([sys.executable,'-B',str(c/name)],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                        rc=child.wait(timeout=seconds)
                    assert rc==0,'ONE_SHOT_'+name+'_FAILED_NO_RETRY'
                    child=None
                started=True;reason='ONE_FROZEN_FIXED24_STARTED';break
            if time.time()>pw['absolute_deadline_unix']+300 or time.monotonic()>pw['hard_stop_monotonic']+300:reason='PARENT_FINALIZE_LIMIT';break
            time.sleep(3)
    except BaseException as exc:error=dict(error=repr(exc),traceback=traceback.format_exc());reason='NIGHT_RELAY_REJECTED_NO_RETRY'
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        if child and child.poll()is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
        # Qualification scripts restore guard themselves. Restore only if our
        # helper failed and no physical confirmation was dispatched.
        if not started and not(NEXT/'LAUNCH_RECEIPT.json').exists():
            f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            guard=(P/'GUARD.bin').read_bytes();assert hashlib.sha256(guard).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
            (R/'REVIEW_PENDING').write_bytes(guard)
        dump(O/'COMPLETION.json',dict(closed=True,reason=reason,error=error,confirmation_started=started,models=0,physical_native=0,no_retry=True,closed_unix=time.time()))
        print((O/'COMPLETION.json').read_text())
if __name__=='__main__':main()
