"""Independent local absolute-wall+monotonic cutoff; no experiment restart."""
import sys,json,time,os,signal,subprocess
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1121_coupled_route_night'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def same(pid,start):
 try:return Path('/proc',str(pid),'stat').read_text().split()[21]==str(start)
 except FileNotFoundError:return False

def main():
 w=json.loads((O/'ROUND_WINDOW.json').read_text());launch=json.loads((O/'LAUNCH_RECEIPT.json').read_text());reason=None
 while True:
  if(O/'COMPLETION.json').exists():break
  if Path('/proc/sys/kernel/random/boot_id').read_text().strip()!=w['boot_id']:reason='BOOT_AUTHORITY_INVALID';break
  if min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())<=0:reason='ABSOLUTE09_DEADLINE';break
  if not same(launch['leader_pid'],launch['leader_proc_start']):reason='MASTER_LEADER_DISAPPEARED';break
  time.sleep(min(15,max(.01,w['hard_stop_monotonic']-time.monotonic())))
 if reason:
  active=json.loads((O/'ACTIVE.json').read_text())if(O/'ACTIVE.json').exists()else {}
  for pid,start in [(active.get('pid'),active.get('proc_start')),(launch['leader_pid'],launch['leader_proc_start'])]:
   if pid and start and same(pid,start):
    try:os.killpg(int(pid),signal.SIGTERM)
    except ProcessLookupError:pass
  time.sleep(5)
  for pid,start in [(active.get('pid'),active.get('proc_start')),(launch['leader_pid'],launch['leader_proc_start'])]:
   if pid and start and same(pid,start):
    try:os.killpg(int(pid),signal.SIGKILL)
    except ProcessLookupError:pass
  guard=(O/'GUARD.bin').read_bytes();(R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',{'models_authorized':False,'watchdog_revoked':True});dump(O/'WATCHDOG_STOP.json',{'reason':reason,'at':time.time(),'models_restarted':False})
  if not(O/'COMPLETION.json').exists():
   summary={'closed':True,'three_route_passed':False,'fixed24_passed':False,'new24_denominator':None,'watchdog_reason':reason,'counts':'UNKNOWN; retain each persisted task result and raw prefix; never infer0','guard_restored':True,'closed_unix':time.time(),'raw_preserved':True};dump(O/'COMPLETION.json',summary);dump(O/'LEDGER.json',summary);(R/'docs/RPCCR_COUPLED_OVERNIGHT_V1121_REPORT.md').write_text('# V1121 watchdog closure\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n');p=R/'CURRENT_EXPERIMENT.json';cur=json.loads(p.read_text());cur.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_overnight=summary);dump(p,cur)
 try:
  with(O/'watchdog_finalize.console').open('x')as log:subprocess.run([sys.executable,'-B',str(C/'finalize.py')],cwd=R,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=300)
 except BaseException as e:dump(O/'WATCHDOG_FINALIZE_ERROR.json',{'error':repr(e),'models':0,'physical_integrations':0,'raw_preserved':True})
if __name__=='__main__':main()
