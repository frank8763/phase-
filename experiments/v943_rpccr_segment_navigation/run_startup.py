"""Bounded ROS pregoal software fixture only; never launches the native worker."""
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent
OUT=ROOT/'runs/v943_rpccr_segment_navigation'
sys.path.insert(0,str(ROOT/'experiments/v856_nav2_foundation'))
from ros_environment import command,environment
env=environment();env['AMENT_PREFIX_PATH']=str(ROOT/'runs/v884_feasible_rpp/install')+':'+env['AMENT_PREFIX_PATH']
env['ROS_LOG_DIR']=str(OUT/'startup_ros_logs')
with (OUT/'startup.console').open('x') as console:
    p=subprocess.run(command(['/usr/bin/python3.12',str(CODE/'qualify_startup.py')]),
                     cwd=ROOT,env=env,stdout=console,stderr=subprocess.STDOUT,timeout=100.)
assert p.returncode==0,'FULL_STARTUP_QUALIFICATION_FAILED'
