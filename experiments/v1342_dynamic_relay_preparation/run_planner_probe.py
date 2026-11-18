import importlib.util
import json
from pathlib import Path
import subprocess
import sys
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1342_dynamic_relay_preparation/planner';O.mkdir(exist_ok=False)
spec=importlib.util.spec_from_file_location('ros_namespace',R/'experiments/v856_nav2_foundation/ros_environment.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
env=module.environment();env.update(ROS_DOMAIN_ID='228',ROS_LOG_DIR=str(O/'ros_logs'),CUDA_VISIBLE_DEVICES='')
with (O/'probe.console').open('x') as log:r=subprocess.run(module.command(['/usr/bin/python3.12','-B',str(C/'planner_probe.py')]),cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=65)
print(json.dumps(dict(returncode=r.returncode,models=0)));raise SystemExit(r.returncode)
