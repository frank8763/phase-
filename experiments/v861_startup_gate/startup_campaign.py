"""Six predeclared fresh ROS namespaces, no physical model or navigation actions."""
import json,os,subprocess,sys,time,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v861_startup_gate';sys.path.insert(0,str(R/'experiments/v856_nav2_foundation'))
from ros_environment import command,environment
def main():
 rows=[]
 with(O/'STARTUP_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),started_unix=time.time(),physical_vehicle_models=0),f)
 for mode in ['automatic','gated']:
  for slot in ['01','02','03']:
   for path,h in json.loads((C/'SOFTWARE_FREEZE.json').read_text())['files'].items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==h
   with(O/(mode+slot+'.console')).open('w')as f:p=subprocess.run(command(['/usr/bin/python3.12',str(C/'cold_probe.py'),mode,slot]),env=environment(),cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=65)
   rp=O/(mode+slot)/'RESULT.json';d=json.loads(rp.read_text())if rp.exists()else dict(passed=False,error='PROCESS_ENTRY_FAILED');rows.append(dict(mode=mode,slot=slot,returncode=p.returncode,result=d));(O/'SOFTWARE_PROGRESS.json').write_text(json.dumps(dict(rows=rows,physical_vehicle_models=0,native_integrations=0),indent=2)+'\n')
 result=dict(closed=True,rows=rows,gated_all_three_passed=len(rows)==6 and all(x['result']['passed']for x in rows if x['mode']=='gated'),automatic_passed=sum(x['result']['passed']for x in rows if x['mode']=='automatic'),physical_vehicle_models=0,native_integrations=0,closed_unix=time.time());(O/'SOFTWARE_COMPLETION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
