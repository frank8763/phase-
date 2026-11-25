"""Namespace and finite queue admission only; original model runtime reused."""
import ast,copy,fcntl,importlib.abc,importlib.util,json,os,runpy,sys,time,traceback
from pathlib import Path
from context import R,C,O
import hashlib
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def main():
    start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
    load('v1919_immutable_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
    class Ban(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0]in {'numpy','mujoco','torch','jax','ctypes','kernel','vehicle','factory','planner','fast_predict','rclpy','OpenGL','chain_tools'}:raise AssertionError('SOURCE_NO_NUMERICS:'+name)
    sys.meta_path.insert(0,Ban())
    with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
    lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    files={};result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,source_only=True,actual_runtime_qualified=False)
    try:
        prior=R/'runs/v1913_dwa_night_qualified';rec=read(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert rec['passed']and rec['all_frozen_members_remote_chain_covered']and not rec['uncovered_members']
        assert read(prior/'SOURCE_QUALIFICATION.json')['passed']and read(prior/'SOURCE_OUTER_CLOSED.json')['passed']
        files.update(read(prior/'SOURCE_FREEZE.json')['files'])
        inherited=[dict(root=str(prior.relative_to(R)),freeze_sha256=sha(prior/'SOURCE_FREEZE.json'),recovery_path=str((prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]
        old=R/'experiments/v1912_dwa_hybrid_evidence';new=R/'experiments/v1922_dwa_five_admission_checked';unchanged=[]
        for p in old.glob('*.py'):
            expected=p.read_text().replace('v1912_dwa_hybrid_evidence','v1922_dwa_five_admission_checked').replace('v1913_dwa_night_qualified','v1923_dwa_five_checked_queue')
            assert expected==(new/p.name).read_text(),'PRODUCTION_CHANGED:'+p.name
            unchanged.append(p.name)
        # Reuse the already-real numerical/model/codec/audit checks by SHA;
        # the new source check executes no duplicate old numerical suite.
        for rid in ['common_06__DWA','common_07__DWA']:
            base=prior/'rounds'/rid;m=read(base/'actual/RESULT.json');assert m['closed']and m['independent_audit']['passed']and m['replay']['passed']and not m['secondary_errors']
            assert m['predictive_evidence_accounting']['unspent_audit_holds']=={}and not m['predictive_evidence_accounting']['poisoned']
            assert read(base/'POST_ROUND_STORAGE_BARRIER.json')['passed']
        for n,h in read(O/'PRIOR_CLOSED_BARRIERS.json')['proof_paths_SHA256'].items():assert sha(R/n)==h and read(R/n)['passed']
        recovery=R/'runs/v1917_dwa_day_transport_recovery/episode01/RESULT.json';assert read(recovery)['passed']and read(recovery)['closed']
        probes=read(R/'runs/v1917_dwa_day_transport_recovery/READONLY_TRANSPORT_PROBES.json');assert next(x for x in probes['probes']if x['client']=='gh_http1')['passed']
        for folder in ['v1917_dwa_day_transport_recovery','v1922_dwa_five_admission_checked','v1923_dwa_five_checked_queue','v1924_dwa_checked_source_recovery','v1925_dwa_checked_runtime_recovery']:
            for p in(R/'experiments'/folder).iterdir():
                if p.is_file():
                    if p.suffix=='.py':ast.parse(p.read_text())
                    files[str(p.relative_to(R))]=sha(p)
        for n in ['AUTHORIZATION.json','PLAN_LOCKED.json','PRIOR_CLOSED_BARRIERS.json']:
            p=O/n;files[str(p.relative_to(R))]=sha(p)
        for p in(O/'rounds').rglob('*.json'):files[str(p.relative_to(R))]=sha(p)
        for p in [recovery,R/'runs/v1917_dwa_day_transport_recovery/DAY_AUTHORIZATION.json',R/'runs/v1917_dwa_day_transport_recovery/READONLY_TRANSPORT_PROBES.json',prior/'SOURCE_QUALIFICATION_PROOF.json',prior/'SOFTWARE_CHECK_PROOF.json']:
            files[str(p.relative_to(R))]=sha(p)
        contract=load('v1919_fixed_remaining5',C/'contract.py');plan=read(O/'PLAN_LOCKED.json');registry=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json')
        assert contract.validate(plan,registry);auth=read(O/'AUTHORIZATION.json');boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert contract.time_admission(auth,time.time(),boot)
        assert auth['overall_calendar_deadline_unix']is None
        ledger=read(R/'runs/v1805_common_algorithm_registry/LEDGER.json')
        for row in plan['assignments']:
            slot=next(x for x in ledger['slots']if x['method']=='DWA'and x['task_id']==row['common_task']);assert not slot['registered']and not slot['closed']
            assert not(R/row['output_root']/'PILOT_ONCE_CLAIM.json').exists()
        negative=[]
        for kind in ['order','method','task','output']:
            bad=copy.deepcopy(plan)
            if kind=='order':bad['assignments'][0]['order']=4
            if kind=='method':bad['assignments'][0]['method']='TEB'
            if kind=='task':bad['assignments'][0]['common_task']='common_07'
            if kind=='output':bad['assignments'][0]['output_root']='runs/other'
            try:contract.validate(bad,registry)
            except (AssertionError,KeyError):negative.append(kind)
            else:raise AssertionError('BAD_PLAN_ACCEPTED')
        for kind in ['boot','late']:
            try:contract.time_admission(auth,time.time()if kind=='boot'else auth['deadline_unix']-7199,'wrong'if kind=='boot'else boot)
            except AssertionError:negative.append(kind)
            else:raise AssertionError('BAD_TIME_ACCEPTED')
        try:runpy.run_path(str(new/'pilot_entry.py'),run_name='__main__')
        except AssertionError as e:assert str(e)=='DWA_NAVIGATION_NOT_ADMITTED';negative.append('realCLI_before_model')
        else:raise AssertionError('CLI_ACCEPTED')
        # Check the exact failure-sensitive transport entry points and retry
        # limits in the real production files, rather than merely setting flags.
        transport=R/'experiments/v1925_dwa_checked_runtime_recovery'
        driver=(transport/'deliver.py').read_text();episode=(transport/'episode.py').read_text()
        assert 'for episode in [1,2]:'in driver and 'timeout=610'in driver and "'--source-sync'"in driver
        assert "folder=D/'resumable_readback';folder.mkdir(exist_ok=True)"in episode
        assert 'ensure_uploaded'in episode and 'verify(reader,index)'in episode and "FULL_REMOTE_VERIFIED.json"in episode
        software=dict(passed=True,reused_exact_production_runtime=True,unchanged_modules=unchanged,prior_real_capture_audit_replay_tasks=['common_06__DWA','common_07__DWA'],old_software_proof_path=str((prior/'SOFTWARE_CHECK_PROOF.json').relative_to(R)),old_software_proof_sha256=sha(prior/'SOFTWARE_CHECK_PROOF.json'),real_transport_recovery_path=str(recovery.relative_to(R)),real_transport_recovery_sha256=sha(recovery),same_archive_two_finite_transport_episodes=True,partial_download_reused_not_duplicated=True,models=0,negative_cases=negative)
        put(O/'SOFTWARE_CHECK_PROOF.json',software)
        assert all(sha(R/n)==h for n,h in files.items())
        put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=inherited));put(O/'SOURCE_QUALIFICATION_PROOF.json',software);put(O/'SOURCE_FREEZE.json',dict(files=files,models_authorized=False))
        result.update(passed=True,source_members=len(files),negative_cases=len(negative),unchanged_runtime_modules=len(unchanged))
    except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=files,models_authorized=False))
    finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
    print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
