"""Actual scoped child writer/parent reader and immutable schedule, zero models."""
import ast
import contextlib
import importlib.abc
import io
import json
import os
import sys
from pathlib import Path


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoModel())
ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent
OUT=ROOT/'runs/v953_stop_align_components';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(CODE))
from worker import controls
from result_contract import save_child,read_parent
from authority import authorized
tasks=json.loads((CODE/'TASKS.json').read_text());old=json.loads((ROOT/'experiments/v909_timed_command_contract/PLATFORM_TASKS.json').read_text())
checks=dict(nineteen_fixed_tasks=len(tasks)==19,
    original18_task_science=all({k:v for k,v in t.items()if k not in{'index','output'}}=={k:v for k,v in o.items()if k!='output'}for t,o in zip(tasks[:18],old)),
    outputs_unique=len({t['output']for t in tasks})==19,
    planned_native9360=sum(420 if i<18 else 1800 for i in range(19))==9360,
    forward_handoff_no_reverse=all(controls(18,i,tasks[18])[0]>=0 for i in range(1800)),
    twelve_second_forward_segment=sum(controls(18,i,tasks[18])==[.1,0.]for i in range(1800))==1200)
for i,t in enumerate(tasks[:18]):
    checks['response_schedule_'+str(i)]=all(controls(i,j,t)==(t['warm']if j<200 else t['command']if j<220 else[0.,0.])for j in range(420))
case=OUT/'writer_fixture';case.mkdir(exist_ok=False)
pilot=ROOT/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py'
tree=ast.parse(pilot.read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='write_guard')
ns=dict(Path=Path,os=os,OUT=case)
exec(compile(ast.Module(body=[function],type_ignores=[]),str(pilot),'exec'),ns)
guard=ns['write_guard'];original=Path.write_text
def scoped_write(path,*args,**kwargs):
    guard('open',(str(path),'w',os.O_CREAT|os.O_WRONLY|os.O_TRUNC))
    return original(path,*args,**kwargs)
try:
    Path.write_text=scoped_write
    try:(OUT/'bad_old_operation_result.json').write_text('{}')
    except PermissionError:checks['old_parent_directory_write_is_red']=True
    else:checks['old_parent_directory_write_is_red']=False
    sample=dict(index=3,passed=False,actual_native=420,replay_native=420,private_native=0,models_attempted=1)
    stream=io.StringIO()
    with contextlib.redirect_stdout(stream):save_child(case,sample)
finally:Path.write_text=original
console=OUT/'writer_fixture.console';console.write_text(stream.getvalue())
checks['real_scoped_writer_parent_roundtrip']=read_parent(console,case)==sample
missing=OUT/'model_init_failed_no_case';sample_missing=dict(index=0,passed=False,models_attempted=1,actual_native=0,replay_native=0,private_native=0)
stream=io.StringIO()
with contextlib.redirect_stdout(stream):save_child(missing,sample_missing)
console=OUT/'early_failure_fixture.console';console.write_text(stream.getvalue())
checks['early_model_failure_metadata_roundtrip']=read_parent(console,missing)==sample_missing
try:authorized()
except (FileNotFoundError,AssertionError):checks['no_authority_rejected_before_model']=True
else:checks['no_authority_rejected_before_model']=False
for path in [*CODE.glob('*.py'),*(ROOT/'experiments/v952_stopped_steering_alignment').glob('*.py')]:ast.parse(path.read_text(),str(path))
checks['all_source_ast']=True
checks['new_controller_qualification']=json.loads((ROOT/'runs/v952_stopped_steering_alignment/ZERO_MODEL_QUALIFICATION.json').read_text())['passed']
result=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,
    scope='Real factory write_guard function and complete child-writer/parent-reader exchange, model import blocked. Not a physical initialization or dynamics response test.')
(OUT/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));assert result['passed']
