"""Observe only the registered relay PID and active child; never restart work."""
import json,os,signal,sys,time
from pathlib import Path
from kernel import O,R,HARD_END,dump,remaining_root

def same(pid,start):
 try:
  row=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split();return row[19]==start and row[0]!='Z'
 except FileNotFoundError:return False

def main():
 pid=int(sys.argv[1]);start=sys.argv[2]
 while not(O/'COMPLETION.json').exists()and same(pid,start)and remaining_root()>8:time.sleep(2)
 if (O/'COMPLETION.json').exists():return
 active=json.loads((O/'ACTIVE.json').read_text())if(O/'ACTIVE.json').exists()else{}
 if active.get('pid')and active.get('pid_start')and same(active['pid'],active['pid_start']):
  try:os.killpg(active['pid'],signal.SIGTERM)
  except ProcessLookupError:pass
  time.sleep(3)
  if same(active['pid'],active['pid_start']):
   try:os.killpg(active['pid'],signal.SIGKILL)
   except ProcessLookupError:pass
 if same(pid,start):
  try:os.killpg(pid,signal.SIGTERM)
  except ProcessLookupError:pass
 (R/'REVIEW_PENDING').write_bytes((O/'GUARD.bin').read_bytes());dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'WATCHDOG_STOP.json',dict(at=time.time(),reason='driver exit or fixed absolute deadline',model_restarted=False,counts_unknown_until_saved_evidence_audit=True))
if __name__=='__main__':main()
