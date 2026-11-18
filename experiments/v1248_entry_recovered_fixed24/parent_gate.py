"""Fresh repaired branch + explicitly inherited unchanged-route evidence."""
from worker_context import *

def validate_parent(d,final):
 assert d.get('closed')and d.get('passed')and d.get('slot13_main_repeat_development_passed'),'SLOT13_PARENT_NOT_PASSED'
 assert d.get('source_unchanged')and d.get('guard_original'),'PARENT_SOURCE_OR_GUARD'
 assert final.get('closed')and final.get('slot13_main_repeat_development_passed')and final.get('manifest_readback'),'PARENT_NOT_FINALIZED'
 rows=d['stages'];assert [r['stage']for r in rows]==['slot13_main','slot13_repeat']
 assert all(r['functional_passed']and r['safety_evidence_passed']and r['result']['passed']and r['audit']['passed']for r in rows)
 pair=d['development_repeats'];assert set(pair)=={'slot13'}and pair['slot13']['passed']and pair['slot13']['maximum_complete_state_ctrl_error']<=1e-8

def check_manifest(root):
 final=read(root/'FINALIZED.json');assert final['manifest_readback']
 files=read(root/'LOCAL_MANIFEST.json')['files'];assert len(files)==final['files']
 for name,value in files.items():
  p=R/name;assert p.is_file()and not p.is_symlink()and p.stat().st_size==value['bytes']and sha(p)==value['sha256'],'PARENT_MEMBER_SHA_CHANGED '+name
 return dict(files=len(files),bytes=sum(v['bytes']for v in files.values()),all_member_SHA_readback=True)

def verify_parent():
 parent=R/'runs/v1247_slot13_entry_validation';d=read(parent/'COMPLETION.json');final=read(parent/'FINALIZED.json');validate_parent(d,final)
 actual=check_manifest(parent)
 source_parent=R/'experiments/v1247_slot13_entry_validation'
 for name in ['worker.py','live_entry.py','ns_live.py','route_dispatch.py','audit_admission.py','ns_admission_audit.py','audit_refusal.py']:
  assert(C/name).read_text()==(source_parent/name).read_text().replace('v1247','v1248').replace('V1247','V1248'),'SCIENCE_CHANGED '+name
 # The old failed-slot prefix witness comparison is conditional on that slot;
 # all actual native/safety/causal/admission checks stay present for every NS.
 expected=(source_parent/'ns_audit.py').read_text().replace('v1247','v1248').replace('V1247','V1248')
 a=expected.index(' prefix=read(');b=expected.index(' states=np.vstack',a)
 expected=expected[:a]+" if task['slot']==13:\n"+''.join(' '+line+'\n'for line in expected[a:b].splitlines())+expected[b:]
 assert(C/'ns_audit.py').read_text()==expected,'NATIVE_AUDIT_SCOPE_CHANGED'
 # Retained original single-stage source and complete execution byte logic.
 new=R/'experiments/v1246_entry_recovery_handoff';old=R/'experiments/v1241_fine_route_reconnection'
 for name in ['candidate_search.py','fallback_search.py','connection.py','admission.py','goal_entry.py','terminal.py','retained_source.py']:
  assert(new/'goal_package'/name).read_bytes()==(old/'goal_package'/name).read_bytes(),'UNCHANGED_SUCCESS_BRANCH_CHANGED '+name
 assert(new/'goal_package/old_source.py').read_bytes()==(old/'goal_package/current_goal_source.py').read_bytes()
 inherited=read(R/'runs/v1246_entry_recovery_handoff/INHERITED_OLD_SUCCESS_QUALIFICATION.json')
 boundary=read(R/'runs/v1246_entry_recovery_handoff/BOUNDARY_QUALIFICATION.json')
 assert inherited['passed']and len(inherited['cases'])==4 and boundary['passed']and 'original_success_exact_object_retained'in boundary['cases']
 # Verify readiness of every old successful NS confirmation input, without
 # integrating or treating it as a new confirmation result.
 loader=load('v1248_new_science_readiness',new/'package_loader.py');entry=loader.get_goal_entry()
 gate=entry.generate.__globals__['entry_status'];checked=[]
 old_confirmation=R/'runs/v1243_reconnected_fixed24'
 for row in read(old_confirmation/'RESULTS.json'):
  if row['role']!='main'or row['case_id']!='NORTH_SOUTH'or not(row['functional_passed']and row['safety_evidence_passed']):continue
  raw=R/'runs/v858_nav2_verified/v1243'/row['stage'];x=read(raw/'LIVE_GOAL_INPUT.json')
  with entry.np.load(raw/'LIVE_GOAL_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
  origin=entry.bind_current(x,x['packet'],False);tag,lower=gate(x,table,origin,origin,0)
  assert tag=='WHOLE_GOAL_READY','OLD_SUCCESS_WOULD_ENTER_NEW_RECOVERY'
  checked.append(dict(slot=row['slot'],status=tag,lower_m=lower))
 assert [r['slot']for r in checked]==[9,10,11,12]
 prior=R/'runs/v1237_night_metadata_entry';prior_d=read(prior/'COMPLETION.json');prior_f=read(prior/'FINALIZED.json')
 assert prior_d['source_unchanged']and prior_f['same_version_three_route_gate_passed']
 old_routes=check_manifest(prior)
 assert all(p['passed']and p['maximum_complete_state_ctrl_error']<=1e-8 for p in prior_d['development_repeats'].values())
 assert len(prior_d['development_repeats'])==5
 assert not any(t['role'].startswith('development_')for t in read(C/'TASKS.json'))
 return dict(passed=True,repaired_slot13_actual_main_repeat_passed=True,
   inherited_old_route_evidence_with_unchanged_success_branches=True,
   fresh_three_route_runs_claimed=False,old_successes_enter_same_unchanged_source=checked,
   all_confirmations_fresh_from_slot1=True,old_confirmation_or_development_rows_imported=0,
   parent_counts_separate=d['physical_counts'],parent_manifest=actual,old_route_manifest=old_routes,
   models_here=0,physical_native_here=0,analytical_propagations_here=0)
