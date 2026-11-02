"""No-physics source proof and shadow transaction rejection checks."""
import fcntl,gzip,hashlib,importlib.util,json,os,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).resolve().parent;parent=repo/'experiments/v697_rpccr_dynamic_initialization'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=repo/'runs/v702_setup';out.mkdir(exist_ok=False)
same=[];changed=[]
for p in parent.glob('*.py'):
    if not (own/p.name).exists():continue
    (same if sha(p)==sha(own/p.name) else changed).append(p.name)
assert set(changed)=={'run_static.py','recovery_supervisor.py','reserved_recovery.py'}
new=(own/'run_static.py').read_text();line="\n    dump(out/'ABLATION_PROTOCOL.json',{'mode':os.environ.get('PHASE_RECOVERY_ABLATION','FULL'),'control_difference':'commit certified return versus shadow-evaluate and keep old tail','same_safety_gates':True,'matched_return_evaluation':True,'training_updates':0})"
assert new.count(line)==1 and new.replace(line,'').replace("/'v702_rpccr_prospective_compute'/a.name","/'v697_rpccr_dynamic_initialization'/a.name")==(parent/'run_static.py').read_text()
new=(own/'reserved_recovery.py').read_text();start=new.index('        if not commit:\n');end=new.index("        directory=self.cell/'handover_certificates'",start)
restored=(new[:start]+new[end:]).replace('def try_handover(self,real,proposal,field,state,step,metadata,commit=True):','def try_handover(self,real,proposal,field,state,step,metadata):').replace('        assert type(commit) is bool\n','')
assert restored==(parent/'reserved_recovery.py').read_text()
new=(own/'recovery_supervisor.py').read_text();start=new.index('    def try_return(');end=new.index('    def _try_return_impl(',start)
restored=new[:start]+new[end:].replace('def _try_return_impl(', 'def try_return(',1)
start=restored.index("        if summary.get('shadow_only'):");end=restored.index('        self.successes+=1;',start)
restored=(restored[:start]+restored[end:]).replace(",commit=os.environ.get('PHASE_RECOVERY_ABLATION','FULL')=='FULL'",'').replace('import json,math,os','import json,math')
assert restored==(parent/'recovery_supervisor.py').read_text()
sys.path.insert(0,str(own));spec=importlib.util.spec_from_file_location('v702_contract_unit',own/'reserved_recovery.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);Original=module.ReservedRecovery
class Candidate:
    def __init__(self,predictor,mj,ids,cell):
        self.predictor=predictor;self.cache={'created_step':10,'qpos':np.zeros((1,2)),'qvel':np.zeros((1,2)),'controls':np.zeros((1,4))};self.last_attempt={'status':'APPENDABLE_BACKUP_FOUND'}
        self.expected=(np.zeros(2),np.zeros(2));self.expected_ctrl=np.zeros(4);self.last_prefix_qpos=np.zeros(2);self.last_prefix_qvel=np.zeros(2)
    def admit_nominal(self,*args):self.predictor.prediction_steps+=328;return {'status':'BACKUP_CANDIDATE_VERIFIED'}
module.ReservedRecovery=Candidate
def make():
    x=Original.__new__(Original);x.predictor=SimpleNamespace(prediction_steps=0);x.mj=None;x.ids=[0,1,2,3];x.cell=out;x.cache={'created_step':1,'nested':[1,2,3]};x.cursor=32;x.expected=object();x.expected_ctrl=object();x.finish_pending=False;x.executing=True;x.handovers=4;x.check_current_contract=lambda real:(0.,0.);return x
real=SimpleNamespace(qpos=np.zeros(2),qvel=np.zeros(2),ctrl=np.zeros(4),time=1.)
tests=[];x=make();old=(x.cache,x.cursor,x.expected,x.expected_ctrl,x.finish_pending,x.executing,x.handovers)
summary=x.try_handover(real,np.zeros(4),None,{},10,{},commit=False)
assert summary['shadow_only'] and x.cache is old[0] and x.cursor==old[1] and x.expected is old[2] and x.expected_ctrl is old[3] and x.finish_pending==old[4] and x.executing==old[5] and x.handovers==old[6] and x.cache=={'created_step':1,'nested':[1,2,3]}
assert not list((out/'handover_certificates').glob('*')) and list((out/'shadow_handover_certificates').glob('*'))
tests.append('shadow_preserves_all_retained_contract_fields_and_writes_no_actual_certificate')
y=make();summary=y.try_handover(real,np.zeros(4),None,{},11,{},commit=True)
assert not y.executing and y.cursor==0 and y.handovers==5 and list((out/'handover_certificates').glob('*'))
assert x.predictor.prediction_steps==y.predictor.prediction_steps==328
tests.append('same_candidate_work_shadow_and_commit_branch')
z=make()
try:z.try_handover(real,np.zeros(4),None,{},12,{},commit='False')
except AssertionError:pass
else:raise AssertionError('NON_BOOL_COMMIT_ACCEPTED')
tests.append('non_boolean_commit_rejected')
def reject(real):raise RuntimeError('BROKEN_OLD_STATE')
z=make();z.check_current_contract=reject
try:z.try_handover(real,np.zeros(4),None,{},12,{},commit=False)
except RuntimeError as e:assert str(e)=='BROKEN_OLD_STATE' and z.predictor.prediction_steps==0
else:raise AssertionError('BROKEN_OLD_CONTRACT_IGNORED')
tests.append('broken_old_contract_rejected_before_candidate_work')
spec=importlib.util.spec_from_file_location('v702_supervisor_unit',own/'recovery_supervisor.py');sup=importlib.util.module_from_spec(spec);spec.loader.exec_module(sup);saved=os.environ.get('PHASE_RECOVERY_ABLATION');os.environ['PHASE_RECOVERY_ABLATION']='UNREGISTERED'
try:
    try:sup.RecoverySupervisor(out).try_return(None,None,None,None,None,None,None,0)
    except AssertionError:pass
    else:raise AssertionError('UNKNOWN_MODE_ACCEPTED')
finally:
    if saved is None:os.environ.pop('PHASE_RECOVERY_ABLATION',None)
    else:os.environ['PHASE_RECOVERY_ABLATION']=saved
tests.append('unknown_mode_rejected_before_real_state_access')
tasks=read(own/'TASK_LIST.json');assert [x['seed'] for x in tasks]==list(range(99010001,99010005)) and [x['initial_motion_direction'] for x in tasks]==['POSITIVE_Y']*2+['NEGATIVE_Y']*2
used=[]
for directory in (repo/'experiments').iterdir():
    if not directory.is_dir() or directory==own:continue
    for path in directory.glob('*TASK*.json'):
        if any(str(seed) in path.read_text() for seed in range(99010001,99010005)):used.append(str(path.relative_to(repo)))
assert not used,'NEW_TASK_SEED_PREVIOUSLY_REGISTERED'
plan=read(own/'EXECUTION_PLAN.json');assert len(plan)==12 and len([x for x in plan if x['role']=='PROSPECTIVE_MAIN'])==8 and [x['repeat_of'] for x in plan if x['role']=='FULL_REPEAT']==['full1','shadow1']
old=read(repo/'experiments/v701_rpccr_recovery_ablation/CANDIDATE_FREEZE.json');assert all(sha(repo/n)==h for n,h in old['files'].items())
assert read(repo/'runs/v701_rpccr_recovery_ablation/FINALIZED.json')['status']=='MECHANISM_DIAGNOSTIC_EVIDENCE_COMPLETE'
assert read(repo/'runs/v700_rpccr_dynamic_continuation/FINALIZED.json')['status']=='FINITE_MOVING_DISCOVERY_SAME24_CONTINUATION_PASS'
for p in own.glob('*.py'):compile(p.read_text(),str(p),'exec')
with (repo/'runs/v648_static_unknown/execution.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
result={'status':'V702_ZERO_INTEGRATION_SETUP_VALIDATED','unchanged_parent_modules':same,'changed_parent_modules':changed,'all_other_parent_computation_byte_exact':True,'shadow_contract_tests':tests,'new_task_previously_registered_files':used,'new_tasks':4,'fixed_navigation_executions':12,'old_frozen_inputs_unchanged':len(old['files']),'review_guard_present':(repo/'REVIEW_PENDING').exists(),'simulation_integrations':0,'training_updates':0}
(out/'VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='unchanged_parent_modules'},indent=2))
