"""User-requested offline rendering, bounded; always restore the Phase review guard."""
import fcntl
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent
OUT=ROOT/'runs/report_materials_v945_20261109';guard=ROOT/'REVIEW_PENDING'
saved=guard.read_bytes();assert hashlib.sha256(saved).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
with(ROOT/'runs/v648_static_unknown/execution.lock').open('a+')as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not(OUT/'RENDER_LAUNCH02.json').exists()
source={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in CODE.iterdir()if p.is_file()}
record=dict(role='SAVED_STATE_VISUALIZATION_ONLY',new_integrations=0,source_sha256=source,started_unix=time.time(),wall_cap_s=605)
process=None
try:
    guard.unlink()
    with(OUT/'render02.console').open('x')as stream:
        process=subprocess.Popen([str(ROOT/'run_phase.sh'),str((CODE/'render_saved02.py').relative_to(ROOT))],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        record['pid']=process.pid;(OUT/'RENDER_LAUNCH02.json').write_text(json.dumps(record,indent=2)+'\n')
        record['exit_code']=process.wait(timeout=605)
finally:
    if process is not None and process.poll()is None:
        os.killpg(process.pid,signal.SIGTERM)
        try:process.wait(timeout=2)
        except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
    guard.write_bytes(saved);record['review_guard_restored']=guard.read_bytes()==saved
    record['closed_unix']=time.time();(OUT/'RENDER_LAUNCH02.json').write_text(json.dumps(record,indent=2)+'\n')
assert record['exit_code']==0,'SAVED_RENDER_FAILED'
