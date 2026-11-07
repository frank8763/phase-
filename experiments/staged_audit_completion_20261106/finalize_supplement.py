"""Separate independent decision and source/SHA archive; preserve original FAIL."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('FINALIZER_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
import fcntl,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;ROOT=R/'runs/staged_audit_completion_20261106';W=R/'experiments/v842_staged_long_navigation';P=ROOT/'reference/paired'
sys.path.insert(0,str(R/'experiments/staged_90_then12_20261106'));from evidence_rules import AUDITS,dump,read,sha;from archive import archive
with(ROOT/'supplement_finalizer.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not(ROOT/'SUPPLEMENT_FINALIZED.json').exists(),'EXISTING_ARCHIVE_NO_OVERWRITE'
 completion=read(ROOT/'COMPLETE_COVERAGE_COMPLETION.json');assert completion['passed']and completion['audit_scopes_completed']==17
 assert read(ROOT/'COMPLETE_COVERAGE_NEGATIVES.json')['passed']
 assert(R/'REVIEW_PENDING').read_bytes()==(ROOT/'REVIEW_PENDING.before').read_bytes()
 original=read(R/'runs/v842_staged_long_navigation/pilot90/FINALIZED.json');assert original['status']=='NOT_PASSED'
 frozen=read(W/'CANDIDATE_FREEZE.json');assert all(sha(R/p)==h for p,h in frozen['files'].items())
 assert all(sha(R/x['path'])==x['sha256']for x in read(ROOT/'ORIGINAL_EVIDENCE_FREEZE.json'))
 expected=read(R/'runs/staged_90_then12_20261106/ZERO_MODEL_QUALIFICATION.json')['expected_audit_statuses'];checks={}
 for script,filename,_ in AUDITS:
  actual_file='REACTIVE_POLICY_AUDIT_COMPLETE_LOGS.json'if script=='audit_reactive.py'else filename
  execution_file=script+('.complete_logs'if script=='audit_reactive.py'else'')+'.execution.json'
  result=read(P/actual_file);execution=read(P/execution_file)
  checks[script]=result['status']==expected[script]and all(result.get('checks',{}).values())and execution['passed']and execution['integrations']==0 and execution['original_auditor_sha256']==sha(W/script)
 assert all(checks.values())
 metadata=read(P/'audit_run.py.execution.json')['actual_model_metadata_reads'];assert len(metadata)==1 and metadata[0]['completed_unix']<read(ROOT/'AUTHORIZATION.json')['original_model_deadline_unix']and metadata[0]['sha256']==sha(P/'scene_model.mjb')
 chain=read(P/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json');assert chain['status']=='PASS'and all(chain['checks'].values())
 replay=read(P/'NATIVE_REPLAY_AUDIT.json');result=read(P/'geometry_memory/result.json');assert replay['maximum_full_native_state_ctrl_error']<=1e-8 and replay['replay_integration_steps']==result['physics_steps']==5800 and result['strict_safe_arrival']and result['goal_distance_m']<=.45
 early=read(P/'EARLY_JOINT_AUDIT.json');assert early['budget_only_native_prefix']==3112 and early['budget_only_native_error']<=1e-8
 record=dict(name='pilot_main02',role='PILOT_MAIN',task=read(R/'experiments/v842_staged_long_navigation/TASK_LIST.json')[0],run='runs/v842_staged_long_navigation/pilot_main02/paired',audit_view=str(P.relative_to(R)),physical_passed=True,functional_passed=True,audit_statuses=checks,result=result,discovery_chain=chain['details'],repeated=None)
 final=dict(status='SUPPLEMENTAL_PILOT_COMPLETE_CHAIN_VERIFIED',development_passed=True,independent_audit_passed=True,complete_chain_passed=True,native_replay_exact=True,source_unchanged=True,preflight_passed=True,records=[record],new_pilot_navigation=0,new_replay_integrations=0,new_metadata_model_reads=1,metadata_integrations=0,original_navigation_native=5800,original_private_native=14253664,original_replay_native=5800,original_batch_status_preserved='NOT_PASSED',original_audit_timeout_preserved=True,original_reactive_count_FAIL_preserved=True,complete_both_log_witness_coverage=True,coverage_negative_cases=10,complete_repeats=0,new24=0,completed_unix=time.time())
 dump(ROOT/'FINAL_INDEPENDENT_AUDIT.json',final)
 report=R/'docs/RPCCR_V842_AUDIT_SUPPLEMENT_20261106_REPORT.md';report.write_text('# V842已到达轨迹独立补充审核\n\n'+json.dumps(final,ensure_ascii=False,indent=2)+'\n\n原闭批NOT_PASSED及120秒超时不修改；本补充保留全部17原检查，执行加速为同一不可变JSONL解析缓存；原reactive计数仅覆盖普通日志1929份而遗漏联合日志7672份的FAIL保留，补充用原逐点公式及全部原断言核验完整9601份，误差0，10负例拒绝。不是重跑导航、独立新样本或新24验收。\n')
 paths=['runs/v842_staged_long_navigation/pilot_main02','runs/v842_staged_long_navigation/pilot_t0_02','runs/v842_staged_long_navigation/pilot90'];dump(ROOT/'ARCHIVE_EXTRA_PATHS.json',paths)
 sources=dict(frozen['files']);sources.update({str(p.relative_to(R)):sha(p)for p in C.glob('*')if p.is_file()});dump(ROOT/'SUPPLEMENT_SOURCE_FREEZE.json',dict(files=sources))
 saved=archive(R,ROOT,W,report,ROOT/'SUPPLEMENT_SOURCE_FREEZE.json','evidence/rpccr_v842_audit_supplement_20261106')
 dump(ROOT/'SUPPLEMENT_FINALIZED.json',{k:v for k,v in final.items()if k!='records'}|saved|dict(report=str(report.relative_to(R))))
 print(json.dumps(read(ROOT/'SUPPLEMENT_FINALIZED.json')),flush=True)
