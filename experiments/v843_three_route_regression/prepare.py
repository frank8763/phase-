"""Review real operations callsites, block first model in dry-run, freeze before one launch."""
import ast,copy,json,sys,time,importlib.abc
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('PREPARATION_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
from pathlib import Path
from common import *
from registration import prefix_anchor,ANCHORS,transform
assert read(ROOT/'QUALIFICATION.json')['passed']and not(C/'CANDIDATE_FREEZE.json').exists()
sys.path.insert(0,str(C));import engine
assert Path(engine.__file__).resolve()==C/'engine.py','WRONG_ENGINE_IMPORT'
for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
assert(C/'TASK_LIST.json').read_bytes()==(R/'experiments/v827_goal_route_validation/TASK_LIST.json').read_bytes()
assert len(tasks())==3 and{t['case_id']for t in tasks()}=={'WEST_EAST','NORTH_SOUTH','EAST_WEST'}
model_invocations=[];dry=ROOT/'operations_dry_run';dry.mkdir(exist_ok=False);stage=engine.Stage(time.time()+43200,phase=dry,raw=RAW)
class ModelBoundary(BaseException):pass
def block(script,args,log,cap,models=False,on_launch=None):
 model_invocations.append(dict(script=script,args=list(map(str,args)),cap=cap,models=models))
 assert script=='run_static.py'and models and '--feasibility-only'in args and args[args.index('--name')+1]=='v843_t0_slot02'and int(args[args.index('--seed')+1])==10010002 and cap==125,'FIRST_MODEL_CALL_INCORRECT'
 raise ModelBoundary('EXPECTED_FIRST_REAL_T0_BOUNDARY_NO_MODELS')
stage.execute=block
try:stage.run_steps()
except ModelBoundary:pass
else:raise AssertionError('MODEL_BOUNDARY_NOT_REACHED')
assert len(model_invocations)==1 and len(stage.rows)==0
dump(dry/'MODEL_BOUNDARY_CHECK.json',dict(passed=True,actual_engine_run_steps=True,invocations=model_invocations,models=0,integrations=0))
from repeat import compare
base=RAW/'long_main08/paired';repeated=compare(base,base);assert repeated['passed']and all(v==0 for v in repeated['full_native_errors'].values());dump(dry/'ACTUAL_SAVED_SELF_REPEAT_INTERFACE.json',repeated)
code=(C/'engine.py').read_text();assert "for t in tasks():self.t0(t)"in code and "main=self.unit(t,'MAIN');self.unit(t,'REPEAT',main)"in code
assert model_fits(10000,0,5705+720)and not model_fits(6000,0,5705+720)
snapshot=read(R/'experiments/staged_audit_completion_20261106/DEVELOPMENT_FREEZE.json');assert all(sha(R/p)==h for p,h in snapshot['files'].items())
assert not PHASE.exists()and all(not(RAW/n).exists()for n in names())
checks=dict(passed=True,real17_saved_auditors_passed=True,actual_source_assertions_preserved=True,three_t0_actual_saved_registration=True,first_real_model_boundary_checked=True,original_three_task_list_byte_exact=True,actual_saved_every_native_repeat_interface=True,current_os_identity_qualified=True,science_worker_byte_exact=True,scientific_revisions=0,models=0,integrations=0,new24=0)
dump(ROOT/'OPERATIONS_CHECK.json',checks)
files=dict(snapshot['files'])
for p in C.iterdir():
 if p.is_file()and p.name!='CANDIDATE_FREEZE.json':files[str(p.relative_to(R))]=sha(p)
for name in ['AUTHORIZATION.json','QUALIFICATION.json','OPERATIONS_CHECK.json']:
 p=ROOT/name;files[str(p.relative_to(R))]=sha(p)
for name in ['FINALIZED.json','FINAL_INDEPENDENT_AUDIT.json']:
 p=RAW/'development12'/name;files[str(p.relative_to(R))]=sha(p)
for seed,relative in ANCHORS.items():
 for name in ['dynamic_native.jsonl.gz','v648_execution.jsonl']:
  p=R/relative/name;files[str(p.relative_to(R))]=sha(p)
plan=R/'docs/RPCCR_THREE_ROUTE_V843_20261106_PLAN.md';files[str(plan.relative_to(R))]=sha(plan)
dump(C/'CANDIDATE_FREEZE.json',dict(files=files,frozen_unix=time.time(),scientific_worker='experiments/v842_staged_long_navigation/run_static.py',scientific_revisions=0,model_deadline_not_yet_created=True,new24=0))
dump(ROOT/'PREPARED.json',dict(freeze_sha256=sha(C/'CANDIDATE_FREEZE.json'),files=len(files),models=0,integrations=0,scope='three routes only, confirmation later'))
print(json.dumps(dict(status='FROZEN',files=len(files),models=0,integrations=0,new24=0)),flush=True)
