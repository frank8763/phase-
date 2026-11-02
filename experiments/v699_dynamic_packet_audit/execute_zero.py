"""Single bounded offline source, packet, chain and rejection verification."""
import copy,difflib,fcntl,gzip,hashlib,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
import numpy as np

repo=Path(__file__).resolve().parents[2];src=Path(__file__).resolve().parent;parent=repo/'experiments/v697_rpccr_dynamic_initialization'
root=repo/'runs/v699_dynamic_packet_audit';root.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
freeze=read(src/'SOURCE_FREEZE.json')
def unchanged():assert all(sha(repo/n)==h for n,h in freeze['files'].items()),'FROZEN_INPUT_CHANGED'
unchanged();assert (repo/'REVIEW_PENDING').exists(),'REVIEW_GUARD_MUST_REMAIN'
lock=(root/'execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
phase_lock=(repo/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(phase_lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(phase_lock,fcntl.LOCK_UN)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});started=time.time();deadline=started+900
window={'started_unix':started,'absolute_deadline_unix':deadline,'limit_s':900,'pid':os.getpid(),'scope':'ZERO_INTEGRATION_AUDIT_REPAIR_ONLY','simulation_integrations':0,'training_updates':0,'new_navigation_trials':0,'review_guard_retained':True,'closed':False};dump(root/'ROUND_WINDOW.json',window)
status='RUNNING';results=[];negative_results=[];error=None
def execute(args,log,cap=45):
    unchanged();assert time.time()+cap+2<deadline,'INSUFFICIENT_OFFLINE_BUDGET'
    dump(root/'ACTIVE.json',{'script_args':args,'started_unix':time.time(),'cap_s':cap})
    with log.open('w') as stream:
        process=subprocess.Popen([sys.executable,'-B',str(src/'zero_runner.py'),*args],stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try:return process.wait(timeout=cap)
        except BaseException:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
            raise
def pair_fixture(original,name,packets):
    fixture=root/'negative_fixtures'/name;(fixture/'geometry_memory').mkdir(parents=True)
    for filename in ['STATIC_PROTOCOL.json','DYNAMIC_PROTOCOL.json','INITIAL_UNSEEN.json']:(fixture/filename).symlink_to(original/filename)
    cell=fixture/'geometry_memory';original_cell=original/'geometry_memory'
    for filename in ['motion_estimate.jsonl','v648_execution.jsonl','model_admission.jsonl','FIRST_DISCOVERY.json','DISCOVERY_BRAKE_COMPLETION.json','discovery_stop_certificate.json.gz','ACTUATOR_COMMAND_CONTRACT.json','result.json']:
        (cell/filename).symlink_to(original_cell/filename)
    for p in original_cell.glob('planning_*.json'):(cell/p.name).symlink_to(p)
    (cell/'sensor_packets.jsonl.gz').write_bytes(gzip.compress(('\n'.join(json.dumps(p) for p in packets)+'\n').encode(),mtime=0))
    return fixture
try:
    old=(parent/'audit_discovery.py').read_text();new=(src/'audit_discovery.py').read_text();normalized=new
    header="import sys\nsys.path.insert(1,str(Path(__file__).resolve().parents[2]/'experiments/v697_rpccr_dynamic_initialization'))\nfrom ray_packet_contract import saved_rays_equal\n"
    assert normalized.count(header)==1;normalized=normalized.replace(header,'')
    normalized=normalized.replace("p.add_argument('--output-dir',required=True);",'')
    line="output_dir=Path(a.output_dir).resolve();repo=Path(__file__).resolve().parents[2];assert output_dir.is_relative_to(repo/'runs'),'OUTPUT_MUST_BE_RUNS';output_dir.mkdir(parents=True,exist_ok=True)\n"
    assert normalized.count(line)==1;normalized=normalized.replace(line,'')
    for a,b in [("saved_rays_equal(rays(initial['packet']),initial['packet']['rays'])","np.array_equal(rays(initial['packet']),initial['packet']['rays'])"),("saved_rays_equal(rr,packet['rays'])","np.array_equal(rr,packet['rays'])")]:
        assert normalized.count(a)==1;normalized=normalized.replace(a,b)
    tail="target=output_dir/('INITIAL_UNSEEN_AUDIT_V699.json' if a.preflight else 'DISCOVERY_CHAIN_AUDIT_V699.json')\nwith target.open('x') as stream:stream.write(json.dumps(out,indent=2)+'\\n')\nprint(json.dumps({'status':out['status'],'checks':out['checks']},indent=2));assert out['status']=='PASS'"
    oldtail="(root/('INITIAL_UNSEEN_AUDIT.json'if a.preflight else'DISCOVERY_CHAIN_AUDIT.json')).write_text(json.dumps(out,indent=2)+'\\n');print(json.dumps(out,indent=2));assert out['status']=='PASS'"
    assert normalized.count(tail)==1;normalized=normalized.replace(tail,oldtail)
    assert normalized==old,'UNDECLARED_AUDIT_COMPUTATION_CHANGED'
    dump(root/'SOURCE_CHANGE_PROOF.json',{'status':'ONLY_TWO_SCHEMA_COMPARISONS_IMPORT_ARGUMENT_OUTPUT_CHANGED','original_sha256':sha(parent/'audit_discovery.py'),'new_sha256':sha(src/'audit_discovery.py'),'all_other_original_computation_byte_exact':True,'schema_comparison_replacements':2,'simulation_steps':0})
    (root/'AUDITOR_DIFF.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='frozen_V697/audit_discovery.py',tofile='new_V699/audit_discovery.py')))
    assert execute(['validate_contract.py'],root/'contract.console',120)==0,'CONTRACT_OR_MUTATION_TEST_FAILED'
    assert read(root/'CONTRACT_VALIDATION.json')['status']=='STRICT_EMPTY_PACKET_CONTRACT_VERIFIED'
    records=read(repo/'runs/v698_rpccr_dynamic_confirmation/confirmation01/PREFLIGHTS.json')
    for record in records:
        output=root/('t0_slot%02d'%record['task']['slot']);code=execute(['audit_discovery.py',str(repo/record['run']),'--preflight','--output-dir',str(output)],root/('t0_slot%02d.console'%record['task']['slot']))
        result=read(output/'INITIAL_UNSEEN_AUDIT_V699.json');original=read(repo/record['run']/'INITIAL_UNSEEN_AUDIT.json')
        assert code==0 and result==original,'PREFLIGHT_AUDIT_CHANGED'
    records=read(repo/'runs/v698_rpccr_dynamic_confirmation/confirmation01/RESULTS.json')
    for record in records:
        slot=record['task']['slot'];pair=repo/record['run'];output=root/('slot%02d'%slot)
        code=execute(['audit_discovery.py',str(pair),'--output-dir',str(output)],root/('slot%02d.console'%slot))
        result=read(output/'DISCOVERY_CHAIN_AUDIT_V699.json');original=read(pair/'DISCOVERY_CHAIN_AUDIT.json')
        changed_checks=[k for k in original['checks'] if original['checks'][k]!=result['checks'][k]]
        expected=[] if slot<=12 else ['all_raw_packets_reconstructed']
        assert code==0 and result['status']=='PASS' and changed_checks==expected and result['details']==original['details'],'UNEXPECTED_CHAIN_AUDIT_CHANGE'
        results.append({'slot':slot,'original_status':original['status'],'new_offline_status':result['status'],'changed_checks':changed_checks,'all_original_physical_causal_metrics_exact':True});dump(root/'CHAIN_COMPARISONS.json',results)
    pair=repo/records[-1]['run']
    with gzip.open(pair/'geometry_memory/sensor_packets.jsonl.gz','rt') as stream:packets=[json.loads(line) for line in stream]
    mutated=copy.deepcopy(packets);index=next(i for i,p in enumerate(mutated) if p['rays']);before=mutated[index]['rays'][0][4];mutated[index]['rays'][0][4]=float(np.nextafter(before,np.inf));fixture=pair_fixture(pair,'one_ulp',mutated);output=root/'negative_one_ulp'
    code=execute(['audit_discovery.py',str(fixture),'--output-dir',str(output)],root/'negative_one_ulp.console')
    audit=read(output/'DISCOVERY_CHAIN_AUDIT_V699.json');assert code!=0 and audit['status']=='FAIL' and [k for k,v in audit['checks'].items() if not v]==['all_raw_packets_reconstructed'],'FULL_AUDIT_ACCEPTED_TRUE_VALUE_CHANGE'
    negative_results.append({'case':'one_ulp_in_saved_range','packet_step':packets[index]['step'],'column':4,'before':before,'after':mutated[index]['rays'][0][4],'auditor_exit':code,'status':audit['status'],'passed':True})
    mutated=copy.deepcopy(packets);index=next(i for i,p in enumerate(mutated) if not p['rays']);mutated[index]['rays']=[[]];fixture=pair_fixture(pair,'malformed_empty',mutated);output=root/'negative_malformed_empty'
    code=execute(['audit_discovery.py',str(fixture),'--output-dir',str(output)],root/'negative_malformed_empty.console')
    assert code!=0 and not (output/'DISCOVERY_CHAIN_AUDIT_V699.json').exists() and 'EACH_RAY_MUST_HAVE_SEVEN_FIELDS' in (root/'negative_malformed_empty.console').read_text(),'FULL_AUDIT_ACCEPTED_MALFORMED_SCHEMA'
    negative_results.append({'case':'empty_row_instead_of_empty_list','packet_step':packets[index]['step'],'auditor_exit':code,'status':'SCHEMA_ERROR_NOT_PASS','passed':True});dump(root/'FULL_AUDIT_NEGATIVE_CASES.json',negative_results)
    unchanged();status='AUDIT_REPAIR_VALIDATED_ONLY'
except BaseException as e:error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()};status='ZERO_ANALYSIS_FAILED'
finally:
    window.update(closed=True,status=status,elapsed_s=time.time()-started);dump(root/'ROUND_WINDOW.json',window)
    dump(root/'COMPLETION.json',{'status':status,'error':error,'chain_comparisons':results,'negative_full_audit_cases':negative_results,'old_confirmation_status':'NOT_PASSED','new_simulation_integrations':0,'new_navigation_trials':0,'new_training_updates':0,'review_guard_retained':(repo/'REVIEW_PENDING').exists(),'elapsed_s':window['elapsed_s']})
    dump(root/'ACTIVE.json',{'status':status,'completed':True});print(json.dumps({'status':status,'error':error,'elapsed_s':window['elapsed_s']},indent=2))
assert status=='AUDIT_REPAIR_VALIDATED_ONLY'
