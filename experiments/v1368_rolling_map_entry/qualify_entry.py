"""Actual CPU backend and native/two ROS full CLI imports, zero vehicle models."""
import importlib.util
import subprocess
import sys
from component_context import *
from campaign import native_environment,ros_environment


def main():
    assert not (O/'ROUND_WINDOW.json').exists() and not (O/'USER_WINDOW.json').exists()
    s=importlib.util.spec_from_file_location('exact_cpu_isolation',R/'tools/isolate.py');isolation=importlib.util.module_from_spec(s);s.loader.exec_module(isolation)
    env=native_environment();p=subprocess.run(isolation.command(C/'backend_check.py',writable=True),cwd=R,env=env,capture_output=True,text=True,timeout=30)
    (O/'backend_entry.console').write_text(p.stdout+p.stderr);assert p.returncode==0,'CPU_BACKEND_ENTRY_FAILURE'
    backend=json.loads(p.stdout.strip().splitlines()[-1]);dump(O/'BACKEND_QUALIFICATION.json',backend)
    rows=[]
    for branch in ['rpp','mppi']:
        task=C/('ENTRY_'+branch+'.json')
        if not rows:
            p=subprocess.run([sys.executable,'-B',str(C/'native_component.py'),str(task),'--entry-check'],cwd=R,env=env,capture_output=True,text=True,timeout=45)
            (O/'native_entry.console').write_text(p.stdout+p.stderr);assert p.returncode==0,'NATIVE_ENTRY_FAILURE';rows.append(dict(kind='native',proof=json.loads(p.stdout.strip().splitlines()[-1])))
        ros,renv=ros_environment(O,branch)
        p=subprocess.run(ros.command(['/usr/bin/python3.12','-B',str(C/'ros_component.py'),str(task),'--entry-check']),cwd=R,env=renv,capture_output=True,text=True,timeout=30)
        (O/(branch+'_entry.console')).write_text(p.stdout+p.stderr);assert p.returncode==0,'ROS_ENTRY_FAILURE'
        rows.append(dict(kind='ros',branch=branch,proof=json.loads(p.stdout.strip().splitlines()[-1])))
    assert sources()
    dump(O/'FULL_ENTRY_QUALIFICATION.json',dict(passed=True,entries=rows,backend=backend,models=0,physical_native=0))
    print(json.dumps(dict(passed=True,entries=len(rows),models=0,physical_native=0)))


if __name__=='__main__':main()
