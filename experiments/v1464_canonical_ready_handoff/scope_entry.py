"""Real CPU3 production phase import and unchanged scope-source reuse only."""
import argparse
import ast
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;F=R/'experiments/v1460_live_event_pipe_close';FO=R/'runs'/F.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*_):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch'}:raise AssertionError('PHASE_IMPORT_MODELS_FORBIDDEN:'+name)

def ros_phase():
 assert sorted(os.sched_getaffinity(0))==[3];sys.meta_path.insert(0,NoModels());sys.path.insert(0,str(C))
 import rclpy
 from rclpy.node import Node
 def forbidden(*_,**__):raise AssertionError('PHASE_IMPORT_ROS_NODE_OR_CONTROLLER_FORBIDDEN')
 rclpy.init=forbidden;Node.__init__=forbidden;subprocess.Popen=forbidden
 module=exact('v1464_real_production_ROS_phase_source',C/'route_ros.py')
 try:__import__('phase_budget')
 except ModuleNotFoundError:old_red=True
 else:raise AssertionError('OLD_IMPLICIT_PHASE_IMPORT_RED_NOT_REPRODUCED')
 now=time.time();mono=time.monotonic();window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=now+5400,hard_stop_monotonic=mono+5400,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 limits=module.read(C/'LIMITS.json');phase=module.phase_clock(window,limits)
 assert Path(phase.__class__.__init__.__code__.co_filename)==R/'experiments/v1449_route_initializer_binding/phase_budget.py'
 end=phase.enter('normal');assert abs(end['absolute_deadline_unix']-(now+4140))<1e-6 and abs(end['hard_stop_monotonic']-(mono+4140))<1e-6
 assert phase.caps==limits['phase_wall_caps_s']and not any(x in sys.modules for x in ['mujoco','vehicle','factory','torch'])
 print(json.dumps(dict(passed=True,old_implicit_phase_import_refused=old_red,real_production_ROS_import=True,explicit_phase_source='experiments/v1449_route_initializer_binding/phase_budget.py',normal_cap_s=4140,actual_cpu=[3],ROS_nodes=0,controller_processes=0,models=0,physical_native=0)))

def qualify(task):
 raise RuntimeError('NEW_CANONICAL_READY_FAILFAST_AND_COOPERATIVE_STOP_QUALIFICATION_NOT_IMPLEMENTED')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--ros-phase',action='store_true');a=p.parse_args();assert a.ros_phase;ros_phase()
