"""Pure entry/negative tests; no scientific propagation or Phase lock use."""
from pathlib import Path
import ast,concurrent.futures,copy,hashlib,json,multiprocessing,sys,time
import coordinator as gate
import night_math
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
def rejected(fn):
    try:fn()
    except (AssertionError,ValueError):return True
    raise AssertionError('NEGATIVE_ACCEPTED')
def main():
    O.mkdir(exist_ok=True);assert not(O/'ROUND_WINDOW.json').exists(),'NO_QUALIFY_AFTER_LAUNCH'
    for p in C.glob('*.py'):ast.parse(p.read_text())
    assert not(O/'LAUNCH_RECEIPT.json').exists(),'NO_DUPLICATE_LAUNCH'
    checks=[]
    w=dict(absolute_deadline_unix=1000.,hard_stop_monotonic=200.,boot_id='test_boot')
    assert gate.remaining(w,now=900,mono=100,boot='test_boot')==100;checks.append('dual_clock_remaining')
    assert gate.remaining(w,now=1001,mono=100,boot='test_boot')<0;checks.append('absolute_expired')
    assert gate.remaining(w,now=900,mono=201,boot='test_boot')<0;checks.append('monotonic_expired')
    assert rejected(lambda:gate.remaining(w,now=900,mono=100,boot='other'));checks.append('wrong_boot_rejected')
    d=dict(closed=True,source_unchanged=True,guard_original=True)
    f=dict(closed=True,source_unchanged=True,guard_original=True,manifest_readback=True)
    assert gate.parent_ready(d,f);checks.append('closed_archive_gate')
    # A safe functional parent failure is diagnosable, never relabeled passed.
    assert gate.parent_ready(dict(d,passed=False),f);checks.append('parent_failure_diagnosis_only_authority')
    for field in d:
        x=dict(d);x[field]=False;assert not gate.parent_ready(x,f);checks.append('parent_'+field+'_rejected')
    for field in f:
        x=dict(f);x[field]=False;assert not gate.parent_ready(d,x);checks.append('archive_'+field+'_rejected')
    j=dict(slot=17,cpu=2,label='serial_17',deadline=time.monotonic()+60)
    assert night_math.validate_job(j,'audit');checks.append('registered_audit_job')
    for field,bad in [('slot',18),('cpu',1),('label','../../parent'),('deadline',0.),('deadline',float('nan'))]:
        x=dict(j);x[field]=bad;assert rejected(lambda:night_math.validate_job(x,'audit'));checks.append('job_'+field+'_rejected')
    assert rejected(lambda:night_math.validate_job(dict(j,output='elsewhere'),'audit'));checks.append('extra_job_key_rejected')
    assert rejected(lambda:night_math.write_scope('open',(str(R/'runs/v1275_time_window_fixed24/RESULTS.json'),'w',0)));checks.append('original_write_rejected')
    assert rejected(lambda:night_math.write_scope('os.rename',(str(O/'a'),str(R/'REVIEW_PENDING'),-1,-1)));checks.append('rename_escape_rejected')
    night_math.write_scope('open',(str(O/'probe.json'),'w',0));checks.append('night_write_allowed')
    with concurrent.futures.ProcessPoolExecutor(max_workers=1,mp_context=multiprocessing.get_context('spawn'))as pool:
        spawn=pool.submit(night_math.metadata_boundary_job,j).result(timeout=30)
    assert spawn['passed']and spawn['models']==spawn['physical_native']==0;checks.append('stable_spawn_metadata_boundary')
    parent=R/'runs/v858_nav2_verified/v1275/main_slot17'
    selection=json.loads((parent/'EW_ONWARD_SELECTION.json').read_text())
    assert selection['passed']and selection['wait_native']in range(0,2000,50)
    assert all(k in selection for k in ['initial_load','rows','input']);checks.append('real_saved_selection_fields')
    import_source=(R/'experiments/v1275_time_window_fixed24/base_safety.py').read_text()
    assert 'def audit(task,result_override=None,output_path=None):'in import_source;checks.append('original_output_path_seam_present')
    summary=dict(passed=True,checks=checks,spawn=spawn,models=0,physical_native=0,analytical_propagation=0,
        original_scientific_functions_reused=True,full_runtime_audit_and_ablation_not_yet_executed=True,
        runtime_requires_parent_finalized_sha_readback_and_unique_phase_lock=True,
        code_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in C.glob('*.py')})
    gate.dump(O/'QUALIFICATION.json',summary);print(json.dumps({k:summary[k]for k in ['passed','models','physical_native','full_runtime_audit_and_ablation_not_yet_executed']}))
if __name__=='__main__':main()
