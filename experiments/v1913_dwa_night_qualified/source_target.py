"""Once new source/API/evidence-service qualification; zero numerical models."""
import ast,copy,fcntl,hashlib,importlib.util,json,os,runpy,sys,time,traceback
from pathlib import Path
from context import C,O,R
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def main():
    start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
    load('v1913_source_immutable_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
    class Ban(__import__('importlib.abc',fromlist=['MetaPathFinder']).MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0]in {'mujoco','torch','jax','kernel','vehicle','factory','planner','fast_predict','rclpy','OpenGL','chain_tools','runtime','model','qualify'}:raise AssertionError('SOURCE_NO_MODEL:'+name)
    sys.meta_path.insert(0,Ban())
    with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
    lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    files={};result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,source_only=True,actual_runtime_qualified=False,numpy_saved_array_operations=True,numpy_internal_library_loads=None)
    try:
        prior=R/'runs/v1889_teb_remaining_exact';rec=read(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json')
        assert rec['passed']and rec['all_frozen_members_remote_chain_covered']and not rec['uncovered_members']
        for k,v in [('index_path','index_sha256'),('full_remote_proof_path','full_remote_proof_sha256')]:assert sha(R/rec[k])==rec[v]
        files.update(read(prior/'SOURCE_FREEZE.json')['files'])
        inherited=[dict(root=str(prior.relative_to(R)),freeze_sha256=sha(prior/'SOURCE_FREEZE.json'),recovery_path=str((prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]
        real=R/'runs/v1911_dwa_resource_bootstrap_reconstruction'
        assert read(real/'COMPLETION.json')['passed']and read(real/'RESULT.json')['passed']
        assert read(real/'RESULT.json')['model_work']['python_completed_native']==19860
        assert read(real/'RESULT.json')['physical_native']==0 and read(real/'RESULT.json')['real_regeneration_arrays_byte_equal']==36
        for base in [R/'runs/v1909_dwa_real_reconstruction',R/'runs/v1910_dwa_single_writer_reconstruction',real]:
            assert read(base/'COMPLETION.json')['closed']and read(base/'COMPLETION.json')['child_exited']
            for p in base.rglob('*'):
                if p.is_file()and '__pycache__'not in p.parts:files[str(p.relative_to(R))]=sha(p)
        files.update(read(real/'SOURCE_IDENTITY.json')['files'])
        for folder in ['v1912_dwa_hybrid_evidence','v1913_dwa_night_qualified','v1914_dwa_hybrid_source_recovery','v1915_dwa_hybrid_runtime_recovery','v1909_dwa_real_reconstruction','v1910_dwa_single_writer_reconstruction','v1911_dwa_resource_bootstrap_reconstruction']:
            for p in(R/'experiments'/folder).iterdir():
                if p.is_file():
                    if p.suffix=='.py':ast.parse(p.read_text())
                    files[str(p.relative_to(R))]=sha(p)
        # Pure recipe/codec/escrow dependencies are copied by SHA, not declared
        # remotely inherited when their latest bytes were only local.
        for folder in ['v1902_dwa_lossless_evidence','v1903_dwa_durable_proof_pack','v1907_dwa_reconstruction_contract']:
            for p in(R/'experiments'/folder).iterdir():
                if p.is_file():files[str(p.relative_to(R))]=sha(p)
        for n in ['AUTHORIZATION.json','PLAN_LOCKED.json','PRIOR_CLOSED_BARRIERS.json']:
            p=O/n;files[str(p.relative_to(R))]=sha(p)
        for p in(O/'rounds').rglob('*.json'):files[str(p.relative_to(R))]=sha(p)
        for n,h in read(O/'PRIOR_CLOSED_BARRIERS.json')['proof_paths_SHA256'].items():assert sha(R/n)==h and read(R/n)['passed']
        contract=load('v1913_original_tasks_contract',C/'contract.py');plan=read(O/'PLAN_LOCKED.json');registry=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json')
        assert contract.validate(plan,registry)
        boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();auth=read(O/'AUTHORIZATION.json');assert contract.time_admission(auth,time.time(),boot)
        ledger=read(R/'runs/v1805_common_algorithm_registry/LEDGER.json')
        for row in plan['assignments']:
            slot=next(x for x in ledger['slots']if x['method']=='DWA'and x['task_id']==row['common_task']);assert not slot['registered']and not slot['closed']
            assert not(R/row['output_root']/'PILOT_ONCE_CLAIM.json').exists()
        old=R/'experiments/v1863_remaining_routes_dwa';new=R/'experiments/v1912_dwa_hybrid_evidence';unchanged=[]
        changed={'driver.py','resources.py','navigation.py','audit_component.py'}
        for p in old.glob('*.py'):
            if p.name in changed:continue
            expected=p.read_text().replace(old.name,new.name).replace('v1866_remaining_common_matrix','v1913_dwa_night_qualified')
            assert expected==(new/p.name).read_text(),'UNRELATED_CHANGE:'+p.name;unchanged.append(p.name)
        nav=(new/'navigation.py').read_text()
        nav=nav.replace("  proof['hybrid_evidence']=binding['predictive_arrays'].persist(proof,dict(states=ss,controls=uu,memory=mm,requests=np.asarray(requests,float)))","  quota.save_npz(out/proof['arrays'],dict(states=ss,controls=uu,memory=mm,requests=np.asarray(requests,float)),np)")
        nav=nav.replace("save(f'cycle_{cycle:04d}_executed.json',cycles[-1])","save('DWA_EXECUTED_CYCLES.json',cycles)")
        assert nav==(old/'navigation.py').read_text(),'NORMAL_NUMERICAL_CONTROL_CHANGED'
        assert sha(new/'resources.py')==sha(R/'experiments/v1879_capture_before_nplus1_checked/resources.py')
        negative=[]
        for kind in ['order','method','task','output']:
            bad=copy.deepcopy(plan)
            if kind=='order':bad['assignments'][0]['order']=5
            if kind=='method':bad['assignments'][0]['method']='RP-CCR'
            if kind=='task':bad['assignments'][0]['common_task']='common_05'
            if kind=='output':bad['assignments'][0]['output_root']='runs/other'
            try:contract.validate(bad,registry)
            except (AssertionError,KeyError):negative.append(kind)
            else:raise AssertionError('FALSE_PLAN_ACCEPTED:'+kind)
        for kind in ['late','boot']:
            try:contract.time_admission(auth,auth['deadline_unix']-7199 if kind=='late'else time.time(),'wrong'if kind=='boot'else boot)
            except AssertionError:negative.append(kind)
            else:raise AssertionError('FALSE_CLOCK_ACCEPTED:'+kind)
        try:runpy.run_path(str(new/'pilot_entry.py'),run_name='__main__')
        except AssertionError as e:assert str(e)=='DWA_NAVIGATION_NOT_ADMITTED';negative.append('real_CLI_refusal_before_model')
        else:raise AssertionError('MODEL_WITHOUT_ADMISSION')
        software=load('v1913_production_service_software',C/'software_check.py').run(files)
        assert software['passed'];put(O/'SOFTWARE_CHECK_PROOF.json',software)
        assert all(sha(R/n)==h for n,h in files.items())
        put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=inherited))
        put(O/'SOURCE_QUALIFICATION_PROOF.json',dict(passed=True,unchanged_production_modules=unchanged,normal_decision_and_all_numerical_source_unchanged=True,only_evidence_resource_paths_changed=True,software_proof_sha256=sha(O/'SOFTWARE_CHECK_PROOF.json'),real_reconstruction_proof_sha256=sha(real/'RESULT.json'),models=0,analytical_native=0,physical_native=0,actual_pipeline_qualified=False))
        put(O/'SOURCE_FREEZE.json',dict(files=files,models_authorized=False));result.update(passed=True,source_members=len(files),negative_cases=len(negative)+len(software['negative_cases']))
    except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=files,models_authorized=False))
    finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
    print(json.dumps(result),flush=True);return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
