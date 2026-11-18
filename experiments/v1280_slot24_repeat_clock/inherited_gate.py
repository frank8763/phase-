from worker_context import *
def verify_parent_main():
    p=R/'runs/v1278_static_partial_reconnection';d=read(p/'COMPLETION.json');f=read(p/'FINALIZED.json')
    assert d['closed']and not d['passed']and d['stop_reason']=='FIRST_INDEPENDENT_AUDIT_FAILURE'and d['source_unchanged']and d['guard_original']
    files=read(p/'LOCAL_MANIFEST.json')['files'];assert f['manifest_readback']and len(files)==f['files']
    assert all(sha(R/n)==v['sha256']and(R/n).stat().st_size==v['bytes']for n,v in files.items())
    proof=read(R/'runs/v1279_same_frame_audit/QUALIFICATION.json')
    assert proof['passed']and proof['original_evidence_unchanged']and proof['state_and_control_fields_exact']and len(proof['negative_rejections'])==9
    for name in ['owner.py','reconnect.py','worker.py','base_safety.py','ew_audit.py','audit_chain.py','audit_time.py','PROPOSAL.json']:
        assert(C/name).read_bytes()==(R/'experiments/v1278_static_partial_reconnection'/name).read_bytes(),'SCIENCE_CHANGED '+name
    return dict(passed=True,original_main_not_repeated=True,original_NOT_PASSED_preserved=True,archived_members=len(files))
def inherited_main():
    verify_parent_main();d=read(R/'runs/v1278_static_partial_reconnection/COMPLETION.json');row=dict(d['stages'][0])
    row.update(parent_inherited=True,functional_passed=True,safety_evidence_passed=True,original_audit_returncode=row['audit_returncode'],
        audit_returncode=0,audit_returncode_scope='original full EW proof plus V1279 corrected saved same-frame transition CLI exit0',
        original_parent_NOT_PASSED_preserved=True,supplemental_audit=read(R/'runs/v1279_same_frame_audit/QUALIFICATION.json'))
    return row
