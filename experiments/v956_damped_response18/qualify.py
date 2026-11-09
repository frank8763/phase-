"""Full actual worker/evaluator seams with explicitly nonphysical data fixtures."""
import ast
import contextlib
import importlib.abc
import io
import json
import math
import os
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoModel())
CODE=Path(__file__).resolve().parent;ROOT=CODE.parents[1];OUT=ROOT/'runs/v956_damped_response18'
sys.path.insert(0,str(CODE))
from worker import execute,controls
from evaluate import evaluate
from authority import authorized
from result_contract import save_child,read_parent

tasks=json.loads((CODE/'TASKS.json').read_text())
original=json.loads((ROOT/'experiments/v909_timed_command_contract/PLATFORM_TASKS.json').read_text())
checks=dict(exact_original18_science=len(tasks)==18 and all({k:v for k,v in t.items()if k not in{'index','output'}}=={k:v for k,v in o.items()if k!='output'}for t,o in zip(tasks,original)),
    unique_outputs=len({x['output']for x in tasks})==18)


class NonphysicalFixture:
    def __init__(self,task):
        self.task=task;self.count=0;self.rows=[];self.pose=np.zeros(3);self.last=np.zeros(5)
        self.adapter=SimpleNamespace(mode='DRIVING')
    def body(self):return self.last
    def steering_sample(self):return np.zeros(4)
    def step(self,v,w):
        a=self.pose[2];dt=.01
        if abs(w)<1e-10:self.pose[:2]+=v*dt*np.array([math.cos(a),math.sin(a)])
        else:self.pose[:2]+=[v/w*(math.sin(a+w*dt)-math.sin(a)),-v/w*(math.cos(a+w*dt)-math.cos(a))]
        self.pose[2]+=w*dt;self.last=np.r_[self.pose,v,w];self.count+=1;self.rows.append(self.last.copy())
    def finish(self):return dict(actual_native=self.count,fully_recorded_native=len(self.rows),minimum_actual_clearance_m=.5,bad_contacts=0,fixture_only=True)


fixtures=[]
for index,task in enumerate(tasks):
    model=NonphysicalFixture(task);progress={}
    item,arrays=execute(model,task,1e99,lambda v,d:dict(passed=True,replay_native=v.count,fixture_only=True),progress,
        clock=lambda:0.,sleep=lambda _:None,monotonic=lambda:0.)
    checks['actual_worker_fixture_'+str(index)]=item['passed']and item['evaluated_samples']==220 and len(arrays['body'])==420
    fixtures.append(dict(index=index,passed=item['passed'],fixture_loop_ticks=model.count,physical_models=0,physical_integrations=0))
    checks['original_schedule_'+str(index)]=all(controls(tick,task)==(task['warm']if tick<200 else task['command']if tick<220 else[0.,0.])for tick in range(420))

old=ROOT/'runs/v858_nav2_verified/v953/response_01'
with np.load(old/'BODY_AND_STEERING.npz')as f:metric,_=evaluate(f['body'],f['steering'],f['origin'],tasks[1])
checks['real_old_encoder_failure_red']=not metric['checks']['final_measured_steering_neutral']
saved=json.loads((old/'QUALIFICATION.json').read_text())
checks['real_old_position_and_heading_exact']=abs(metric['position_residual_max_m']-saved['position_residual_max_m'])<1e-12 and abs(metric['angle_residual_max_rad']-saved['angle_residual_max_rad'])<1e-12

# Exact full12-second straight and entire2-second final brake evaluation.
data=np.zeros((1800,5));servo=np.zeros((1800,4));origin=np.zeros(5)
data[400:,0]=.1*np.minimum(np.arange(1,1401)*.01,12.);data[400:1600,3]=.1
metric,expected=evaluate(data,servo,origin,dict(command=[.1,0.]),handoff=True)
checks['full_handoff_array_1400_samples']=expected.shape==(1400,3)and metric['evaluated_samples']==1400 and all(metric['checks'].values())
late=data.copy();late[1599,0]+=.05
metric,_=evaluate(late,servo,origin,dict(command=[.1,0.]),handoff=True)
checks['late_twelfth_second_position_fault_red']=not metric['checks']['bounded_position']
late=data.copy();late[-1,2]=.04
metric,_=evaluate(late,servo,origin,dict(command=[.1,0.]),handoff=True)
checks['final_brake_heading_fault_red']=not metric['checks']['bounded_rotation']
try:evaluate(data[:600],servo[:600],origin,dict(command=[.1,0.]),handoff=True)
except AssertionError:checks['truncated_two_second_handoff_rejected']=True
else:checks['truncated_two_second_handoff_rejected']=False

# Actual factory guard function and original result writer/reader, with no model.
case=OUT/'writer_fixture';case.mkdir(exist_ok=False)
path=ROOT/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py'
function=next(x for x in ast.parse(path.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard')
namespace=dict(Path=Path,os=os,OUT=case)
exec(compile(ast.Module(body=[function],type_ignores=[]),str(path),'exec'),namespace)
write=Path.write_text
def scoped(p,*args,**kwargs):
    namespace['write_guard']('open',(str(p),'w',os.O_CREAT|os.O_WRONLY|os.O_TRUNC));return write(p,*args,**kwargs)
try:
    Path.write_text=scoped
    try:(OUT/'old_invalid_result.json').write_text('{}')
    except PermissionError:checks['original_bad_parent_write_rejected']=True
    else:checks['original_bad_parent_write_rejected']=False
    sample=dict(index=4,passed=False,fixture_only=True);stream=io.StringIO()
    with contextlib.redirect_stdout(stream):save_child(case,sample)
finally:Path.write_text=write
console=OUT/'writer_fixture.console';console.write_text(stream.getvalue())
checks['guarded_full_child_parent_roundtrip']=read_parent(console,case)==sample
try:authorized()
except (FileNotFoundError,AssertionError):checks['no_authority_before_model_rejected']=True
else:checks['no_authority_before_model_rejected']=False
checks['controller_qualification']=json.loads((ROOT/'runs/v955_damped_stopped_alignment/ZERO_MODEL_QUALIFICATION.json').read_text())['passed']
for folder in [CODE,ROOT/'experiments/v955_damped_stopped_alignment']:
    for p in folder.glob('*.py'):ast.parse(p.read_text(),str(p))
checks['all_source_ast']=True
result=dict(passed=bool(all(checks.values())),checks={k:bool(v)for k,v in checks.items()},fixtures=fixtures,
    models=0,integrations=0,fixture_loop_ticks=sum(r['fixture_loop_ticks']for r in fixtures),
    scope='Actual worker loop/evaluator and factory write guard with explicit nonphysical fixtures. No empirical response qualification.')
(OUT/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k!='fixtures'},indent=2));assert result['passed']
