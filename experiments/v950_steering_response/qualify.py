"""Zero-model entry/task authority and fixed command schedule qualification."""
import ast
import importlib.abc
import importlib.util
import json
import sys
from pathlib import Path


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical'}:
            raise AssertionError('FORBIDDEN_MODEL_IMPORT '+name)


sys.meta_path.insert(0,NoModel())
CODE=Path(__file__).resolve().parent;ROOT=CODE.parents[1]
OUT=ROOT/'runs/v950_steering_response';OUT.mkdir(exist_ok=True)
sys.path[:0]=[str(CODE),str(ROOT/'experiments/v945_rpccr_observation_liveness')]
from worker import controls
from authority import authorized
tasks=json.loads((CODE/'TASKS.json').read_text())
original=json.loads((ROOT/'experiments/v909_timed_command_contract/PLATFORM_TASKS.json').read_text())
checks=dict(nineteen_fixed_tasks=len(tasks)==19,all_outputs_unique=len({t['output']for t in tasks})==19,
            old18_science_exact=all({k:v for k,v in task.items()if k not in{'index','output'}}=={k:v for k,v in old.items()if k!='output'}for task,old in zip(tasks[:18],original)),
            full_schedule_8360=sum(420 if i<18 else 800 for i in range(19))==8360,
            three_phase_handoff=[controls(18,i,tasks[18])for i in[0,199,200,399,400,599,600,799]]==[tasks[18]['warm'],tasks[18]['warm'],[0.,0.],[0.,0.],tasks[18]['command'],tasks[18]['command'],[0.,0.],[0.,0.]],
            no_reverse_handoff=all(controls(18,i,tasks[18])[0]>=0 for i in range(800)))
for p in CODE.glob('*.py'):ast.parse(p.read_text(),str(p))
checks['all_python_parse']=True
try:authorized()
except (FileNotFoundError,AssertionError):checks['pre_authority_rejects_before_model_import']=True
else:checks['pre_authority_rejects_before_model_import']=False
checks['new_adapter_array_gate']=json.loads((ROOT/'runs/v949_steering_handoff/QUALIFICATION.json').read_text())['passed']
result=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,
            scope='Fixed schedule and entry interface; not new physical model/response audit.')
(OUT/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result));assert result['passed']
