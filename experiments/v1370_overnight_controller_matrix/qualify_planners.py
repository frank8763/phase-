"""Both preregistered modes on three original saved actual inputs, no models."""
import subprocess
import sys
from component_context import *
from campaign import ros_environment

def main():
    root=R/'runs/v858_nav2_verified/v1361/sweep_terminal_dynamic_main/planner_jobs';folder=O/'planner_qualification';folder.mkdir(exist_ok=False);rows=[]
    for index in [1,2,3]:
        original=read(root/('request%02d.json'%index))
        for mode in [0,1]:
            request=dict(original,planner_mode=mode);source=folder/('input%d_m%d.json'%(index,mode));target=folder/('result%d_m%d.json'%(index,mode));dump(source,request)
            ros,env=ros_environment(folder,'rpp');p=subprocess.run(ros.command(['/usr/bin/python3.12','-B',str(C/'route_worker.py'),str(source),str(target)]),cwd=R,env=env,capture_output=True,text=True,timeout=10)
            assert p.returncode==0 and target.exists();result=read(target);assert not result.get('error') and result['models']==result['physical_native']==0
            rows.append(dict(input=index,mode=mode,passed_entry=True,path_accepted=result['passed'],report=result.get('report')))
    dump(O/'PLANNER_QUALIFICATION.json',dict(passed=True,saved_inputs=3,modes=[0,1],cases=rows,models=0,physical_native=0));print(json.dumps(dict(passed=True,planner_cases=len(rows),models=0)))

if __name__=='__main__':main()
