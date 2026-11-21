"""Exact new task/output native CLI; no full route admission is manufactured."""
import argparse
import ast
import importlib.util
import json
import os
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def original_guard(output):
 source=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(source.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=output);exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),scope);sys.addaudithook(scope['write_guard'])

def main():
 p=argparse.ArgumentParser();p.add_argument('task');p.add_argument('--binding-qualification',action='store_true');a=p.parse_args()
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
 os.chdir(R);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply();task=json.loads(Path(a.task).read_text());assert task in json.loads((C/'TASKS.json').read_text())
 if a.binding_qualification:
  original_guard(O);entry=exact('v1456_targeted_closure_binding',C/'binding_entry.py');return entry.qualify(task)
 out=Path(task['output']);assert out.is_relative_to(O)and out.is_dir();original_guard(out)
 life=exact('v1456_actual_latest_lifecycle',C/'lifecycle.py');budget=exact('v1456_exact_frozen_budget',C/'budget.py')
 q=budget.complete_admission();approval=json.loads((O/'APPROVAL.json').read_text());window=json.loads((O/'ROUND_WINDOW.json').read_text());budget.clocks(window,json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text()),reserve_s=q['limits']['finalization_reserve_s'])
 result=life.run(task,approval,window)
 return 0 if result.get('functional_passed')and result.get('replay',{}).get('passed')and result.get('independent_allocation',{}).get('passed')and result.get('fullstate_prefix_before_contact',{}).get('complete')and not result.get('first_error')and not result.get('save_errors')else 1
if __name__=='__main__':raise SystemExit(main())
