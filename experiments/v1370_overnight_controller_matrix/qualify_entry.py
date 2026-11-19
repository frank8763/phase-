"""Real native/ROS import entry for every controller/stage, zero vehicle models."""
import importlib.util
import subprocess
import sys
from component_context import *
from campaign import native_environment,ros_environment

def main():
    spec=importlib.util.spec_from_file_location('phase_overnight_cpu_isolation',R/'tools/isolate.py');isolation=importlib.util.module_from_spec(spec);spec.loader.exec_module(isolation)
    env=native_environment();p=subprocess.run(isolation.command(C/'backend_check.py',writable=True),cwd=R,env=env,capture_output=True,text=True,timeout=30)
    (O/'backend_entry.console').write_text(p.stdout+p.stderr);assert p.returncode==0;backend=json.loads(p.stdout.strip().splitlines()[-1]);dump(O/'BACKEND_QUALIFICATION.json',backend)
    rows=[]
    for stage in ['component','static','dynamic']:
        path=C/('ENTRY_rpp_default_'+stage+'.json');script='recovery_native.py' if stage=='component' else 'route_native.py'
        if stage!='dynamic':
            p=subprocess.run([sys.executable,'-B',str(C/script),str(path),'--entry-check'],cwd=R,env=env,capture_output=True,text=True,timeout=45)
            (O/(stage+'_native_entry.console')).write_text(p.stdout+p.stderr);assert p.returncode==0,'NATIVE_ENTRY '+stage;rows.append(dict(stage=stage,kind='native',proof=json.loads(p.stdout.strip().splitlines()[-1])))
        for config in read(C/'CAMPAIGN_CONFIG.json')['configs']:
            path=C/('ENTRY_'+config['branch']+'_'+stage+'.json');ros,renv=ros_environment(O,config['kind']);script='recovery_ros.py' if stage=='component' else 'route_ros.py'
            p=subprocess.run(ros.command(['/usr/bin/python3.12','-B',str(C/script),str(path),'--entry-check']),cwd=R,env=renv,capture_output=True,text=True,timeout=30)
            (O/(config['branch']+'_'+stage+'_entry.console')).write_text(p.stdout+p.stderr);assert p.returncode==0,'ROS_ENTRY '+config['branch']+' '+stage
            rows.append(dict(stage=stage,branch=config['branch'],kind='ros',proof=json.loads(p.stdout.strip().splitlines()[-1])))
    assert sources();dump(O/'FULL_ENTRY_QUALIFICATION.json',dict(passed=True,entries=rows,backend=backend,models=0,physical_native=0));print(json.dumps(dict(passed=True,entries=len(rows),models=0)))

if __name__=='__main__':main()
