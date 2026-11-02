"""Zero-physics source isolation and retained-contract negative tests."""
import fcntl,hashlib,importlib.util,json,os
from pathlib import Path
from types import SimpleNamespace
repo=Path(__file__).resolve().parents[2];own=Path(__file__).resolve().parent;parent=repo/'experiments/v697_rpccr_dynamic_initialization'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=repo/'runs/v701_setup';out.mkdir(exist_ok=False)
changed=[];unchanged=[]
for p in parent.glob('*.py'):
    if p.name in ['execute.py','audit_final.py']:continue
    q=own/p.name
    if sha(q)==sha(p):unchanged.append(p.name)
    else:changed.append(p.name)
assert set(changed)=={'run_static.py','recovery_supervisor.py'}
old=(parent/'run_static.py').read_text();new=(own/'run_static.py').read_text()
declaration="\n    dump(out/'ABLATION_PROTOCOL.json',{'mode':os.environ.get('PHASE_RECOVERY_ABLATION','FULL'),'only_disabled_mechanism':'intermediate certified recovery return' if os.environ.get('PHASE_RECOVERY_ABLATION','FULL')=='COMPLETE_TAIL' else None,'same_safety_gates':True,'training_updates':0})"
assert new.count(declaration)==1
assert new.replace(declaration,'').replace("/'v701_rpccr_recovery_ablation'/a.name","/'v697_rpccr_dynamic_initialization'/a.name")==old
old=(parent/'recovery_supervisor.py').read_text();new=(own/'recovery_supervisor.py').read_text()
start=new.index("        mode=os.environ.get('PHASE_RECOVERY_ABLATION','FULL')")
end=new.index('        if self.path is None or self.first_step is None:return None',new.index('            return None\n',start)+len('            return None\n'))
insertion=new[start:end]
assert new[:start]+new[end:]==old.replace('import json,math','import json,math,os')
spec=importlib.util.spec_from_file_location('v701_supervisor_contract_only',own/'recovery_supervisor.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
saved=os.environ.get('PHASE_RECOVERY_ABLATION');tests=[]
try:
    calls=[];cache={'created_step':41,'unchanged_nested':[1,2,3]};sentinel=object()
    def checked(data):
        assert data is sentinel;calls.append(data);return 0.,0.
    reserved=SimpleNamespace(cache=cache,cursor=32,check_current_contract=checked)
    env=SimpleNamespace(data=sentinel)
    supervisor=module.RecoverySupervisor(out);supervisor.path=[1];supervisor.first_step=42
    os.environ['PHASE_RECOVERY_ABLATION']='COMPLETE_TAIL'
    assert supervisor.try_return(env,None,None,reserved,None,None,None,46) is None
    assert reserved.cache is cache and reserved.cursor==32 and reserved.cache=={'created_step':41,'unchanged_nested':[1,2,3]} and len(calls)==1
    tests.append('suppressed_valid_return_preserves_identical_cache_and_cursor')
    def rejected(data):raise RuntimeError('OLD_CONTRACT_INVALID')
    reserved.check_current_contract=rejected
    try:supervisor.try_return(env,None,None,reserved,None,None,None,50)
    except RuntimeError as e:assert str(e)=='OLD_CONTRACT_INVALID'
    else:raise AssertionError('ABLATION_IGNORED_BROKEN_OLD_CONTRACT')
    tests.append('broken_old_contract_rejected_before_suppression')
    os.environ['PHASE_RECOVERY_ABLATION']='UNREGISTERED'
    try:supervisor.try_return(env,None,None,reserved,None,None,None,50)
    except AssertionError:pass
    else:raise AssertionError('UNKNOWN_MODE_ACCEPTED')
    tests.append('unregistered_mode_rejected')
    os.environ['PHASE_RECOVERY_ABLATION']='FULL';supervisor.path=None
    assert supervisor.try_return(env,None,None,None,None,None,None,50) is None
    tests.append('full_original_empty_reference_control_flow')
finally:
    if saved is None:os.environ.pop('PHASE_RECOVERY_ABLATION',None)
    else:os.environ['PHASE_RECOVERY_ABLATION']=saved
assert read(repo/'runs/v700_rpccr_dynamic_continuation/FINAL_INDEPENDENT_AUDIT.json')['status']=='FINITE_MOVING_DISCOVERY_SAME24_CONTINUATION_PASS'
tasks=read(own/'TASK_LIST.json');alltasks=read(repo/'experiments/v698_rpccr_dynamic_confirmation/TASK_LIST.json');assert tasks==[alltasks[x-1] for x in [14,20]]
inventory=[]
for record in read(repo/'runs/v700_rpccr_dynamic_continuation/FINAL_INDEPENDENT_AUDIT.json')['records']:
    if record['repeat']:continue
    pair=repo/record['run'];cell=pair/'geometry_memory';result=read(cell/'result.json');file=cell/'handover_attempts.jsonl';hands=[json.loads(s) for s in file.read_text().splitlines()] if file.exists() else []
    inventory.append({'slot':record['slot'],'backup_steps':result['backup_steps'],'successful_returns':sum(x['status']=='CERTIFIED_RETURN' for x in hands),'attempts':len(hands)})
assert [x['slot'] for x in inventory if x['successful_returns']]==[14,20,22]
assert [x['slot'] for x in inventory if x['successful_returns']][:2]==[x['slot'] for x in tasks]
for p in own.glob('*.py'):compile(p.read_text(),str(p),'exec')
freeze=read(repo/'experiments/v700_rpccr_dynamic_continuation/CANDIDATE_FREEZE.json')
assert all(sha(repo/n)==h for n,h in freeze['files'].items())
with (repo/'runs/v648_static_unknown/execution.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
result={'status':'V701_SOURCE_AND_CONTRACT_VALIDATED_ZERO_INTEGRATION','unchanged_parent_modules':unchanged,'changed_parent_modules':changed,'all_other_parent_computation_byte_exact':True,'unit_contract_tests':tests,'original24_mechanism_inventory':inventory,'selected_old_tasks':[14,20],'selection_rule':'First two original slots that actually executed certified return; selected diagnostics, not independent confirmation.','old_frozen_inputs_unchanged':len(freeze['files']),'simulation_integrations':0,'training_updates':0,'guard_present':(repo/'REVIEW_PENDING').exists()}
(out/'VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['unchanged_parent_modules','original24_mechanism_inventory']},indent=2))
