"""Track only this campaign's registered PIDs. Never restart or inspect Stage."""
import os,sys,signal,json,time,subprocess
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from resource_policy import apply
apply()
from authority import R,O,HARD_END

def same(pid,start):
 try:row=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split();return row[19]==start and row[0]!='Z'
 except FileNotFoundError:return False
pid=int(sys.argv[1]);start=sys.argv[2];window=json.loads((O/'ROUND_WINDOW.json').read_text())
while same(pid,start)and not(O/'COMPLETION.json').exists()and time.time()<HARD_END-8 and time.monotonic()<window['hard_stop_monotonic']-8:time.sleep(2)
if not(O/'COMPLETION.json').exists():
 active=json.loads((O/'ACTIVE.json').read_text())if(O/'ACTIVE.json').exists()else{}
 for target,stamp in [(active.get('pid'),active.get('pid_start')),(pid,start)]:
  if target and stamp and same(target,stamp):
   try:os.killpg(target,signal.SIGTERM)
   except ProcessLookupError:pass
   time.sleep(4)
   if same(target,stamp):
    try:os.killpg(target,signal.SIGKILL)
    except ProcessLookupError:pass
 (R/'REVIEW_PENDING').write_bytes((O/'GUARD.bin').read_bytes());(O/'APPROVAL.json').write_text(json.dumps(dict(models_authorized=False,closed=True))+'\n');(O/'WATCHDOG_STOP.json').write_text(json.dumps(dict(at=time.time(),reason='fixed deadline or registered driver disappeared',unknown_counts_must_be_reconstructed=True,no_model_restart=True))+'\n')
 with(O/'watchdog_finalize.console').open('x')as log:subprocess.Popen([sys.executable,'-B',str(C/'finalize_night.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
