"""Exercise the real inherited write policy without importing a model/factory."""
import ast
import hashlib
import importlib.abc
import importlib.util
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
OUT=ROOT/'runs/v951_component_output_entry';OUT.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('prepared_entry',CODE/'worker.py')
entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
pilot=ROOT/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py'
tree=ast.parse(pilot.read_text());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='write_guard')
case=ROOT/'runs/v858_nav2_verified/v950/response_01'
namespace=dict(Path=Path,os=os,OUT=case)
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(pilot),'exec'),namespace)
guard=namespace['write_guard'];checks={}
old=ROOT/'runs/v950_steering_response/CASE_01_RESULT.json'
try:guard('open',(str(old),'w',os.O_CREAT|os.O_WRONLY))
except PermissionError:checks['original_scope_bug_red']=True
else:checks['original_scope_bug_red']=False
new=entry.target_path(OUT/'CASE_01_RESULT.json',case)
guard('open',(str(new),'w',os.O_CREAT|os.O_WRONLY))
checks['new_exact_final_target_allowed']=new==case/'QUALIFICATION.json'
guard('open',(str(entry.target_path(case/'QUALIFICATION.json',case)),'w',os.O_CREAT|os.O_WRONLY))
checks['original_case_result_allowed']=True
for p in CODE.glob('*.py'):ast.parse(p.read_text(),str(p))
checks['all_sources_parse']=True
checks['first_case_independent_recovery']=json.loads((ROOT/'runs/v950_steering_response/ACCOUNTING_RECOVERED.json').read_text())['passed']
base=json.loads((ROOT/'experiments/v950_steering_response/SOURCE_FREEZE.json').read_text())['files']
checks['all_frozen_science_unchanged']=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in base.items())
result=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,
            scope='Actual factory write_guard function, model import blocked. Same immutable scientific worker; output-only wrapper.')
(OUT/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result));assert result['passed']
