"""Fault-injection tests actual monitor with real child processes, zero models."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from worker_monitor import monitor

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1340_overnight_preparation'


def main():
    rows=[]
    for mode in ['success','functional_reject','control_reject','missing_receipt','native_fault','hang','storage','root']:
        with tempfile.TemporaryDirectory(dir=O) as directory:
            out=Path(directory);jobs=[];begin=time.monotonic()
            actualmode='hang' if mode in ['storage','root'] else mode
            for role in ['ros','native']:
                jobs.append(subprocess.Popen([sys.executable,'-B',str(C/'fake_worker.py'),role,actualmode,directory],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True))
            error=None
            try:
                proof=monitor(jobs,out,remaining=lambda:0 if mode=='root' else 100,task_seconds=.6,drain_seconds=.45,storage_check=lambda:mode!='storage',poll_s=.01)
            except AssertionError as exc:error=str(exc)
            if mode in ['hang','root','storage']:
                assert error is not None and all(p.poll() is not None for p in jobs)
            elif mode=='native_fault':
                assert json.loads((out/'RESULT.json').read_text())['error']=='NATIVE_SAFETY_ANOMALY'
            else:
                result=json.loads((out/'RESULT.json').read_text())
                assert result['closed'] and result['evidence_saved'] and result['complete_stop'] and result['replay']['passed']
                assert result['passed']==(mode=='success')
                if mode=='missing_receipt':assert not (out/'ROS_RESULT.json').exists()
            rows.append(dict(mode=mode,passed=True,wall_s=time.monotonic()-begin,error=error,all_processes_closed=all(p.poll() is not None for p in jobs)))
    result=dict(passed=True,cases=rows,tests=len(rows),real_subprocess_monitor_used=True,models=0,physical_native=0,training_updates=0)
    (O/'MONITOR_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='cases'}))


if __name__=='__main__':main()
