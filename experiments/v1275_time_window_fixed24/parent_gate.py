"""One unified candidate must pass both failing phases and exact repeats."""
from worker_context import *
def validate_parent(d,final):
    assert d.get('closed')and d.get('passed')and d.get('joint_phase_main_repeat_development_passed'),'JOINT_PHASE_PARENT_NOT_PASSED'
    assert d.get('source_unchanged')and d.get('guard_original')and final.get('closed')and final.get('joint_phase_main_repeat_development_passed')and final.get('manifest_readback'),'PARENT_SOURCE_OR_ARCHIVE'
    rows=d['stages'];assert [r['stage']for r in rows]==['slot18_main','slot18_repeat','slot19_main','slot19_repeat']
    assert all(r['functional_passed']and r['safety_evidence_passed']and r['result']['passed']and r['audit']['passed']for r in rows)
    pairs=d['development_repeats'];assert set(pairs)=={'slot18','slot19'}and all(p['passed']and p['maximum_complete_state_ctrl_error']<=1e-8 for p in pairs.values())
def check_manifest(root):
    final=read(root/'FINALIZED.json');assert final['manifest_readback'];files=read(root/'LOCAL_MANIFEST.json')['files'];assert len(files)==final['files']
    for n,v in files.items():
        p=R/n;assert p.is_file()and not p.is_symlink()and p.stat().st_size==v['bytes']and sha(p)==v['sha256'],'PARENT_MEMBER_CHANGED '+n
    return dict(files=len(files),bytes=sum(v['bytes']for v in files.values()),all_member_SHA_readback=True)
def verify_parent():
    parent=R/'runs/v1271_ew_joint_phase_validation';d=read(parent/'COMPLETION.json');f=read(parent/'FINALIZED.json');validate_parent(d,f);pm=check_manifest(parent)
    original=R/'experiments/v1265_ew_cli_fixed24'
    for name in ['live_entry.py','ns_live.py','ns_audit.py','audit_admission.py','ns_admission_audit.py']:
        assert(C/name).read_text()==(original/name).read_text().replace(original.name,C.name).replace('v1265','v1275').replace('V1265','V1275'),'UNCHANGED_WE_NS_BRANCH_DIFF '+name
    assert(C/'gates.py').read_bytes()==(original/'gates.py').read_bytes()
    saved=read(R/'runs/v1274_ew_joint_saved_entry/COMPLETION.json');assert saved['passed']and saved['source_unchanged']and [r['slot']for r in saved['records']]==[17,18,19]
    assert saved['records'][0]['original_success_arrays_unchanged']and saved['records'][0]['selected_wait_native']==0
    prev=read(R/'runs/v1264_ew_repeat_cli/COMPLETION.json');assert prev['passed']and prev['slot17_main_repeat_development_passed']
    prev17=check_manifest(R/'runs/v1264_ew_repeat_cli');original17=check_manifest(R/'runs/v1261_ew_reserved_validation')
    return dict(passed=True,joint_18_19_actual_main_repeat_passed=True,unchanged17_success_arrays_and_actual_pair_preserved=True,
        WE_NS_source_unchanged=True,fresh_three_route_runs_claimed=False,parent_manifest=pm,original17_pair_archive=prev17,
        original17_main_archive=original17,parent_counts_separate=d['physical_counts'],old_confirmation_or_development_rows_imported=0,models_here=0,physical_native_here=0)
