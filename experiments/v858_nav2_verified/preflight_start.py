"""Sequential native t0 preparation, preserving every failed scene query."""
import json,subprocess,time,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OUT=R/'runs/v858_nav2_verified'
def main():
 tasks=[t for t in json.loads((C/'TASK_LIST.json').read_text())if t['stage']in ['static_main','dynamic_main']];(OUT/'preflights').mkdir(exist_ok=True);guard=(R/'REVIEW_PENDING').read_bytes();rows=[]
 try:
  (R/'REVIEW_PENDING').unlink()
  for task in tasks:
   assert time.time()<1794052800-120
   with(OUT/'preflights'/(task['id']+'.console')).open('w')as f:p=subprocess.run([str(R/'run_phase.sh'),str((C/'preflight.py').relative_to(R)),str(OUT/(task['id']+'.task.json'))],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=90)
   rp=OUT/'preflights'/(task['id']+'.RESULT.json');res=json.loads(rp.read_text())if rp.exists()else dict(passed=False,reason='NO_RESULT');rows.append(dict(id=task['id'],result=res,returncode=p.returncode));(OUT/'PREFLIGHT_RESULTS.json').write_text(json.dumps(dict(passed=len(rows)==6 and all(r['result']['passed']for r in rows),rows=rows,native_integrations=0),indent=2)+'\n')
   if p.returncode!=0 or not res['passed']:break
 finally:(R/'REVIEW_PENDING').write_bytes(guard)
 print(json.dumps(dict(completed=len(rows),passed=len(rows)==6 and all(r['result']['passed']for r in rows))),flush=True)
if __name__=='__main__':main()
