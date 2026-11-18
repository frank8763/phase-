"""Main is inherited only after immutable whole-source evidence verification."""
from worker_context import *
def verify_parent_main():
    p=R/'runs/v1261_ew_reserved_validation';d=read(p/'COMPLETION.json');f=read(p/'FINALIZED.json')
    assert d['closed']and not d['passed']and d['stop_reason']=='FIRST_INDEPENDENT_AUDIT_FAILURE'and d['source_unchanged']and d['guard_original']
    assert f['closed']and f['manifest_readback'];files=read(p/'LOCAL_MANIFEST.json')['files'];assert len(files)==f['files']
    for name,v in files.items():
        path=R/name;assert path.is_file()and path.stat().st_size==v['bytes']and sha(path)==v['sha256'],'IMMUTABLE_MAIN_MEMBER_CHANGED '+name
    raw=R/'runs/v858_nav2_verified/v1261/slot17_main';result=read(raw/'RESULT.json');audit=read(raw/'FINAL_INDEPENDENT_AUDIT.json')
    assert result['passed']and result['error']is None and result['replay']['passed']and result['own_replay_native']==result['new_actual_native']==audit['native_reviewed']==50262
    assert audit['passed']and audit['physical_audit_complete']and audit['actual_replay_verified']and audit['component']['passed']and audit['onward']['passed']
    assert result['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8 and result['physical']['bad_contacts']==0
    proof=read(R/'records/v1263_audit_cli_recovery_20261117/VERIFIED_SAVED_AUDIT.json')
    assert proof['failure_only_in_CLI_summary_print']and proof['all_archived_members_SHA_readback']and not proof['complete_repeat_executed']
    expected=R/'experiments/v1261_ew_reserved_validation'
    for name in ['ew_live.py','reserved_goal.py','worker.py','audit_chain.py','audit_refusal.py']:
        assert(C/name).read_text()==(expected/name).read_text().replace(expected.name,C.name).replace('v1261','v1264').replace('V1261','V1264'),'MAIN_SCIENCE_DIFFERENT '+name
    assert read(O/'AUDIT_CLI_QUALIFICATION.json')['passed'],'CORRECTED_REAL_AUDIT_CLI_REQUIRED'
    return dict(passed=True,models=0,physical_native=0,parent_original_NOT_PASSED_preserved=True,baseline_native=50262,files_SHA_readback=len(files))
def inherited_main():
    verify_parent_main();d=read(R/'runs/v1261_ew_reserved_validation/COMPLETION.json');row=dict(d['stages'][0])
    row.update(parent_inherited=True,functional_passed=True,safety_evidence_passed=True,
        original_audit_returncode=row['audit_returncode'],audit_returncode=0,
        audit_returncode_scope='new print-only CLI qualification exit0; original audit_rc1 preserved separately',
        parent_batch_status='NOT_PASSED',audit_cli_recovery='records/v1263_audit_cli_recovery_20261117/VERIFIED_SAVED_AUDIT.json')
    return row
