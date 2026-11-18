from worker_context import *
def validate_parent(d,f):
    assert d.get('closed')and d.get('passed')and d.get('slot24_main_repeat_development_passed'),'SLOT24_MAIN_REPEAT_NOT_PASSED'
    assert d.get('source_unchanged')and d.get('guard_original')and f.get('closed')and f.get('slot24_main_repeat_development_passed')and f.get('manifest_readback'),'PARENT_ARCHIVE_SOURCE_REQUIRED'
    assert len(d.get('stages',[]))==2 and all(r['functional_passed']and r['safety_evidence_passed']for r in d['stages'])
    assert d['development_repeats']['slot24']['passed']and d['development_repeats']['slot24']['maximum_complete_state_ctrl_error']<=1e-8
def check_manifest(root):
    f=read(root/'FINALIZED.json');files=read(root/'LOCAL_MANIFEST.json')['files'];assert f['closed']and f['manifest_readback']and len(files)==f['files']
    assert all((R/n).stat().st_size==v['bytes']and sha(R/n)==v['sha256']for n,v in files.items()),'PARENT_ARCHIVE_MEMBER_CHANGED'
    return dict(files=len(files),bytes=sum(v['bytes']for v in files.values()),all_member_SHA_readback=True)
def verify_parent():
    root=R/'runs/v1280_slot24_repeat_clock';d=read(root/'COMPLETION.json');f=read(root/'FINALIZED.json');validate_parent(d,f)
    archives={n:check_manifest(R/'runs'/n)for n in ['v1280_slot24_repeat_clock','v1278_static_partial_reconnection','v1271_ew_joint_phase_validation','v1275_time_window_fixed24']}
    original=R/'experiments/v1275_time_window_fixed24'
    for n in ['live_entry.py','ns_live.py','ns_audit.py','audit_admission.py','ns_admission_audit.py','gates.py','ew_audit.py','audit_chain.py','audit_time.py']:
        assert(C/n).read_bytes()==(original/n).read_bytes(),'SUCCESS_BRANCH_SCIENCE_CHANGED '+n
    for n in ['owner.py','reconnect.py','transition_audit.py']:
        assert(C/n).read_bytes()==(R/'experiments/v1280_slot24_repeat_clock'/n).read_bytes(),'SLOT24_SOURCE_CHANGED '+n
    qualification=read(R/'runs/v1278_static_partial_reconnection/QUALIFICATION.json')
    assert qualification['unchanged_success_branches']==list(range(1,24))
    return dict(passed=True,slot24_actual_main_repeat_passed=True,previous23_success_branches_unchanged=True,
        fresh_three_route_runs_claimed=False,all_source_archives=archives,old_confirmation_or_development_rows_imported=0,
        parent_counts_separate=d['physical_counts'],models_here=0,physical_native_here=0)
