"""Bounded isolated fixed-state diagnostic; never auto-start a navigator."""
import os,time,json,hashlib,subprocess,signal,fcntl
from pathlib import Path
repo=Path(__file__).resolve().parents[2];src=Path(__file__).resolve().parent
root=repo/'runs/v692_discovery_escape_diagnosis';root.mkdir(exist_ok=False)
lock=(root/'window.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
dump=lambda p,x:p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
started=time.time();ledger={'started_unix':started,'absolute_deadline_unix':started+3600,'limit_s':3600,'round_closed':False,'pid':os.getpid(),'fixed_diagnostic_attempts':1,'new_navigation_tasks':0,'training_updates':0,'private_cap':35000,'single_cpu':True,'stage_access':0,'real_robot':0}
dump(root/'ROUND_WINDOW.json',ledger)
files=[*src.glob('*.py'),*src.glob('*.md'),*(repo/'experiments/v691_discovery_in_motion').glob('*.py'),*(repo/'experiments/v691_discovery_in_motion').glob('*.md')]
freeze={str(p.relative_to(repo)):sha(p)for p in files};dump(root/'SOURCE_FREEZE.json',freeze)
status='FAILED';code=None
try:
    with(root/'probe.console').open('w')as f:
        proc=subprocess.Popen([str(repo/'run_phase.sh'),str(src.relative_to(repo)/'probe.py')],cwd=repo,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
        try:code=proc.wait(timeout=185)
        except BaseException:
            os.killpg(proc.pid,signal.SIGTERM)
            try:proc.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
            raise
    assert code==0,'PROBE_FAILED'
    assert all(sha(repo/p)==h for p,h in freeze.items()),'FROZEN_SOURCE_CHANGED'
    result=json.loads((root/'fixed408/COMPLETION.json').read_text());status=result['status']
finally:
    ledger.update(status=status,child_exit=code,elapsed_s=time.time()-started,round_closed=status!='FIXED_STATE_CERTIFICATE_FOUND')
    dump(root/'ROUND_WINDOW.json',ledger);dump(root/'ACTIVE.json',{'status':status,'diagnostic_completed':True,'navigation_active':False})
    print(status,flush=True)
