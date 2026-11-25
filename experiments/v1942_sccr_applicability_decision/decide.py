"""Finite current-contract applicability decision, static source only."""
from pathlib import Path
import ast,hashlib,json,os,time
R=Path(__file__).resolve().parents[2];O=R/'runs/v1942_sccr_applicability_decision'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));assert not(O/'ONCE.json').exists();(O/'ONCE.json').write_text(json.dumps(dict(pid=os.getpid(),unix=time.time(),models=0)))
 old=R/'experiments/v1805_common_algorithm_registry/PROTOCOL.md';assert 'Input permissions only public static geometry and causal32ray measurements'in old.read_text()
 prep=R/'runs/v1937_sccr_frozen_policy_bridge/PREPARATION_RESULT.json';p=json.loads(prep.read_text());assert p['trained_observation_shape']==[186]and p['camera_depth_dimensions']==50 and p['underlying_fusion_also_reads_depth']
 source=R/'runtime/mk-mini/training/phase21_risk_switch_fusion_sac/envs/mkmini_phase21_v2_corridor_detect_control_failed.py';tree=ast.parse(source.read_text());fn=next(n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=='_phase21_sensor_points');fields=sorted({n.value for n in ast.walk(fn)if isinstance(n,ast.Constant)and isinstance(n.value,str)and n.value.startswith('phase17c_last_')});assert 'phase17c_last_depth'in fields and 'phase17c_last_lidar'in fields
 ledger=R/'runs/v1805_common_algorithm_registry/LEDGER.json';before=sha(ledger);d=json.loads(ledger.read_text());slots=[r for r in d['slots']if r['method']=='SCCR'];assert len(slots)==12 and all(not r['registered']and not r['closed']for r in slots)
 result=dict(closed=True,disposition='APPLICABILITY_BLOCKED_ORIGINAL_FULL_SCCR_SENSOR_CONTRACT',formal_slots_remaining_unexecuted=12,measured_algorithm_failure=False,models=0,inference=0,physical_native=0,replay_native=0,training=0,source_pins={str(x):sha(x)for x in [old,prep,source]},original_sensor_function_AST_sha256=hashlib.sha256(ast.dump(fn,include_attributes=False).encode()).hexdigest(),direct_sensor_dependencies=fields,original_observation_dim=186,unprovided_camera_depth_features=50,current_shared_measurements='public static geometry+causal32ray',no_zero_fill_or_truth_permission_expansion=True,no_masked_variant_substitution=True,no_original_case_retry=True,next_method='RPP',ledger_unchanged_SHA256=before,local_not_remote=True);assert sha(ledger)==before
 (O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
