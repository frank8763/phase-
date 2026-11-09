"""Bounded actual ROS software checks. Never launches a vehicle/native worker."""
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; CODE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'experiments/v856_nav2_foundation'))
from ros_environment import command, environment

if len(sys.argv)!=2 or sys.argv[1] not in {'probe','callback_probe','qualify_supervisor','qualify_startup'}:
    raise SystemExit('Choose one fixed zero-model software qualification')
name=sys.argv[1];out=ROOT/'runs/v948_forward_navigation';out.mkdir(exist_ok=True)
env=environment();env['AMENT_PREFIX_PATH']=str(ROOT/'runs/v884_feasible_rpp/install')+':'+env['AMENT_PREFIX_PATH']
attempt=1
while (out/(name+str(attempt).zfill(2)+'.console')).exists():attempt+=1
env['PHASE_SOFTWARE_ATTEMPT']=str(attempt).zfill(2)
env['ROS_LOG_DIR']=str(out/(name+str(attempt).zfill(2)+'_ros_logs'))
os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:3]))
with (out/(name+str(attempt).zfill(2)+'.console')).open('x')as console:
    result=subprocess.run(command(['/usr/bin/python3.12','-B',str(CODE/(name+'.py'))]),cwd=ROOT,
                          env=env,stdout=console,stderr=subprocess.STDOUT,timeout=125)
print(name,result.returncode)
raise SystemExit(result.returncode)
