"""Only real Nav2 software on explicitly nonphysical saved-state peers."""
import json
import subprocess
import sys
from pathlib import Path

R=Path(__file__).resolve().parents[2]
C=Path(__file__).parent
O=R/'runs/v991_coordinated_components'
sys.path.insert(0,str(R/'experiments/v856_nav2_foundation'))
from ros_environment import command,environment

if __name__=='__main__':
    attempt=int(sys.argv[1]) if len(sys.argv)>1 else 1
    qualification=json.loads((O/'ZERO_MODEL_ENTRY_QUALIFICATION.json').read_text())
    assert qualification['passed']
    env=environment()
    env['AMENT_PREFIX_PATH']=str(R/'runs/v884_feasible_rpp/install')+':'+env['AMENT_PREFIX_PATH']
    results=[]
    for index in [0,1]:
        env['ROS_LOG_DIR']=str(O/f'software_case{index}_attempt{attempt}_ros_logs')
        with (O/f'software_case{index}_attempt{attempt}.console').open('x') as console:
            outcome=subprocess.run(command(['/usr/bin/python3.12',str(C/'software_fixture.py'),str(index),str(attempt)]),cwd=R,env=env,stdout=console,stderr=subprocess.STDOUT,timeout=110)
        report=O/f'SOFTWARE_CASE{index}_attempt{attempt}.json'
        results.append(dict(index=index,returncode=outcome.returncode,report=json.loads(report.read_text()) if report.exists() else None))
        if report.exists():
            data=json.loads(report.read_text())
            assert data['shutdown']['passed'] and not data['shutdown']['callback_errors'],'CALLBACK_SHUTDOWN_UNQUALIFIED'
            assert 'The following exception was never retrieved' not in (O/f'software_case{index}_attempt{attempt}.console').read_text(),'UNRETRIEVED_CALLBACK_EXCEPTION'
        (O/f'SOFTWARE_RESULTS_attempt{attempt}.json').write_text(json.dumps(dict(passed=all(x['returncode']==0 for x in results),completed=len(results),models=0,integrations=0,results=results),indent=2)+'\n')
        assert outcome.returncode==0,f'FIRST_SOFTWARE_FAILURE_CASE_{index}'
    (O/'SOFTWARE_QUALIFICATION.json').write_text(json.dumps(dict(passed=True,attempt=attempt,models=0,integrations=0,results=results),indent=2)+'\n')
