"""Initializer CLI: entry qualification has no models; numerical mode is scoped."""
import argparse
import ast
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import subprocess
import time
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','rclpy'}:raise AssertionError('INITIALIZER_ENTRY_NO_MODEL:'+name)

def install_guard(output):
 guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=output);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])

def qualify():
 raise RuntimeError('NEW_TASK_CACHE_QUALIFICATION_REQUIRED_OLD_SUITE_NOT_RERUN')

def main():
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--qualify-entry',action='store_true');g.add_argument('--prepare-admission',action='store_true');g.add_argument('--launch',action='store_true');g.add_argument('--run',action='store_true');a=p.parse_args()
 if a.prepare_admission or a.launch:
  os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));owner=exact('v1447_zero_model_schedule_owner',C/'owner.py')
  if a.prepare_admission:owner.prepare_admission();return 0
  result=owner.launch();print(json.dumps(dict(passed=result['passed'],closed=result['closed'])));return 0 if result['passed']else 1
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
 os.chdir(R);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply()
 if a.qualify_entry:return qualify()
 install_guard(O/'initializer_only');init=exact('v1447_numerical_initializer_runtime',C/'initializer.py');result=init.run(init.contract.read(O/'TASK.json'),init.contract.read(O/'APPROVAL.json'),init.contract.read(O/'INITIALIZER_WINDOW.json'));return 0 if result['passed']else 1

if __name__=='__main__':raise SystemExit(main())
