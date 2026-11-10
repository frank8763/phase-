"""Two sequential software probes, no physical authority or fallback trial."""
import json,subprocess,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1008_nav2_normal_action_software'
sys.path.insert(0,str(R/'experiments/v856_nav2_foundation'))
from ros_environment import command,environment
rows=[]
for variant in ['red_original','green_explicit']:
    env=environment();env['AMENT_PREFIX_PATH']=str(R/'runs/v884_feasible_rpp/install')+':'+env['AMENT_PREFIX_PATH'];env['ROS_LOG_DIR']=str(O/(variant+'_roslogs'))
    with(O/(variant+'.console')).open('x')as log:
        result=subprocess.run(command(['/usr/bin/python3.12',str(C/'probe.py'),variant]),cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=260)
    p=O/(variant+'.RESULT.json');row=json.loads(p.read_text())if p.exists()else dict(passed=False,variant=variant,error='No completed installed software probe')
    rows.append(dict(returncode=result.returncode,report=row));(O/'RESULTS.json').write_text(json.dumps(dict(passed=all(x['returncode']==0 and x['report']['passed']for x in rows),models=0,vehicle_native_integrations=0,rows=rows),indent=2)+'\n')
    print(json.dumps(rows[-1]),flush=True);assert result.returncode==0,'FIRST_SOFTWARE_PROBE_FAILURE_NO_MORE_PROBES'
