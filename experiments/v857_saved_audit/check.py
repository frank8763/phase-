"""Reproduce and isolate V857 contact type error without importing a simulator."""
import ast,copy,fcntl,gzip,hashlib,json,math,os,sys
from pathlib import Path
import numpy as np
from contacts import contact_equal
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OUT=R/'runs/v857_assembly_contact';OLD=R/'runs/v856_nav2_foundation/entry01/vehicle_qualification01';REC=R/'records/v857_20261107'
def main():
    source=R/'experiments/v857_assembly_contact/component.py';tree=ast.parse(source.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='contact_equal');ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),ns)
    expected=json.load(gzip.open(OLD/'CONTACTS.json.gz','rt'))[1];saved=json.load(gzip.open(OUT/'old_replay/CONTACTS.json.gz','rt'))[0]
    as_live=[tuple(x)for x in saved];checks={}
    checks['original_comparator_rejects_equal_list_tuple']=not ns['contact_equal'](as_live,expected)
    checks['stored_values_match_semantically']=contact_equal(as_live,expected)
    checks['json_roundtrip_matches']=contact_equal(json.loads(json.dumps(as_live)),as_live)
    changed=copy.deepcopy(expected);changed[0][0]+=1;checks['geom_tamper_rejected']=not contact_equal(as_live,changed)
    changed=copy.deepcopy(expected);changed[0][2]='unknown_contact';checks['type_tamper_rejected']=not contact_equal(as_live,changed)
    changed=copy.deepcopy(expected);changed[0][3]+=1e-5;checks['distance_tamper_rejected']=not contact_equal(as_live,changed)
    changed=copy.deepcopy(expected);changed[0][3]=float('nan');checks['nonfinite_rejected']=not contact_equal(as_live,changed)
    checks['missing_contact_rejected']=not contact_equal(as_live,expected[:-1]);checks['extra_contact_rejected']=not contact_equal(as_live,[*expected,expected[-1]])
    new=np.load(OUT/'old_replay/NATIVE_TRACE.npz');old=np.load(OLD/'NATIVE_TRACE.npz');errors={k:float(np.max(abs(new[k][0]-old[k][0])))if new[k][0].size else 0. for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};checks['one_recorded_native_state_exact']=max(errors.values())==0.
    result=json.loads((OUT/'RESULT.json').read_text());checks['only_one_old_replay_native']=result['counts']['old_replay_native']==1 and sum(result['counts'][k]for k in ['same_control_actual_native','same_control_replay_native','closed_loop_actual_native','closed_loop_replay_native','private_native'])==0
    checks['round_closed']=json.loads((OUT/'ROUND_WINDOW.json').read_text())['round_closed'];checks['guard_original_bytes_restored']=(R/'REVIEW_PENDING').read_bytes()==(OUT/'REVIEW_PENDING.before').read_bytes()
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);checks['lock_idle']=True;fcntl.flock(lock,fcntl.LOCK_UN)
    checks['frozen_inputs_unchanged']=all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in json.loads((R/'experiments/v857_assembly_contact/SOURCE_FREEZE.json').read_text())['files'].items())
    assert all(checks.values());audit=dict(passed=True,scope='ZERO_MODEL_SAVED_DATA_AND_SERIALIZATION_SEAM_ONLY',checks=checks,first_native_state_error=errors,original_frozen_batch_passed=False,first_failure_preserved=True,full_1100_replay_unexecuted=True,new_model_variant_executed_native=0,new_model_initializations=0,new_integrations=0,scientific_hypothesis_outcome='NOT_YET_TESTED',cause='Original comparator compared tuple[:3] with JSON list[:3] directly; representation inequality, not different physical contact.')
    (OUT/'SAVED_INTERFACE_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n');(REC/'SAVED_INTERFACE_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
