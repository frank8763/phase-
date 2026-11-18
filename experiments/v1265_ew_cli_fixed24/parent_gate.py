"""Actual EW parent plus explicitly unchanged WE/NS branch evidence; no models."""
from worker_context import *
def validate_parent(d,final):
    assert d.get('closed')and d.get('passed')and d.get('slot17_main_repeat_development_passed'),'EW_PARENT_NOT_PASSED'
    assert d.get('source_unchanged')and d.get('guard_original')and final.get('closed')and final.get('manifest_readback')and final.get('slot17_main_repeat_development_passed'),'PARENT_SOURCE_OR_ARCHIVE'
    rows=d['stages'];assert [r['stage']for r in rows]==['slot17_main','slot17_repeat']and all(r['functional_passed']and r['safety_evidence_passed']and r['result']['passed']and r['audit']['passed']for r in rows)
    pair=d['development_repeats'];assert set(pair)=={'slot17'}and pair['slot17']['passed']and pair['slot17']['maximum_complete_state_ctrl_error']<=1e-8
def check_manifest(root):
    final=read(root/'FINALIZED.json');assert final['manifest_readback'];files=read(root/'LOCAL_MANIFEST.json')['files'];assert len(files)==final['files']
    for n,v in files.items():
        p=R/n;assert p.is_file()and not p.is_symlink()and p.stat().st_size==v['bytes']and sha(p)==v['sha256'],'PARENT_MEMBER_CHANGED '+n
    return dict(files=len(files),bytes=sum(v['bytes']for v in files.values()),all_member_SHA_readback=True)
def verify_parent():
    parent=R/'runs/v1264_ew_repeat_cli';d=read(parent/'COMPLETION.json');f=read(parent/'FINALIZED.json');validate_parent(d,f);pm=check_manifest(parent)
    assert d.get('original_parent_NOT_PASSED_preserved')and d['stages'][0].get('parent_inherited')
    saved=read(R/'records/v1263_audit_cli_recovery_20261117/VERIFIED_SAVED_AUDIT.json');assert saved['saved_full_independent_audit_passed']and saved['all_archived_members_SHA_readback']
    main_archive=check_manifest(R/'runs/v1261_ew_reserved_validation')
    old=R/'experiments/v1248_entry_recovered_fixed24'
    for n in ['live_entry.py','ns_live.py','ns_audit.py','audit_admission.py','ns_admission_audit.py']:
        assert(C/n).read_text()==(old/n).read_text().replace('v1248','v1265').replace('V1248','V1265'),'UNCHANGED_BRANCH_CHANGED '+n
    assert(C/'gates.py').read_bytes()==(old/'gates.py').read_bytes()
    prior=R/'runs/v1248_entry_recovered_fixed24';pd=read(prior/'COMPLETION.json');pf=read(prior/'FINALIZED.json')
    rows=[r for r in pd['stages']if r['role']=='main'and r['case_id']in['WEST_EAST','NORTH_SOUTH']]
    assert len(rows)==16 and all(r['functional_passed']and r['safety_evidence_passed']for r in rows)
    oldm=check_manifest(prior)
    assert not any(t['role'].startswith('development_')for t in read(C/'TASKS.json'))
    return dict(passed=True,EW_actual_slot17_main_repeat_passed=True,WE_NS_success_branches_unchanged=True,
        fresh_three_route_runs_claimed=False,all_confirmations_fresh_from_slot1=True,old_confirmation_or_development_rows_imported=0,
        parent_counts_separate=d['physical_counts'],parent_manifest=pm,original_main_archive=main_archive,unchanged_WE_NS_manifest=oldm,models_here=0,physical_native_here=0)
