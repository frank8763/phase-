"""Independent original auditors, exact repeats, complete denominators and archive; no models."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('FINALIZER_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
import fcntl,json
from common import *
from repeat import compare
sys.path.insert(0,str(R/'experiments/staged_audit_completion_20261106'));from archive import archive
lock=(PHASE/'finalizer.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
if(PHASE/'FINALIZED.json').exists():print('ALREADY_FINALIZED_NO_OVERWRITE');raise SystemExit(0)
assert read(PHASE/'ROUND_WINDOW.json')['round_closed']and(R/'REVIEW_PENDING').read_bytes()==(PHASE/'REVIEW_PENDING.before').read_bytes()
source_ok=True
try:unchanged()
except AssertionError:source_ok=False
rows=read(PHASE/'RESULTS.json');expected=read(ROOT/'QUALIFICATION.json')['expected_audit_statuses'];records=[];counts={k:0 for k in ['navigation_native','private_native','replay_native']};exact={k:True for k in counts}
for row in rows:
 pair=R/row['run'];result=read(pair/'geometry_memory/result.json')if(pair/'geometry_memory/result.json').exists()else None;interrupted=read(pair/'geometry_memory/interrupted.json')if(pair/'geometry_memory/interrupted.json').exists()else None;actual=result or interrupted or{};replay=read(pair/'NATIVE_REPLAY_AUDIT.json')if(pair/'NATIVE_REPLAY_AUDIT.json').exists()else None
 for label,key in [('navigation_native','physics_steps'),('private_native','prediction_steps')]:
  value=actual.get(key);exact[label]&=result is not None and isinstance(value,int);counts[label]+=value if isinstance(value,int)else 0
 value=None if replay is None else replay.get('replay_integration_steps');exact['replay_native']&=isinstance(value,int);counts['replay_native']+=value if isinstance(value,int)else 0
 gates={}
 for script,filename,_ in AUDITS:
  data=read(pair/filename)if(pair/filename).exists()else{};execution=read(pair/(script+'.execution.json'))if(pair/(script+'.execution.json')).exists()else{}
  gates[script]=row['audits'].get(script)==0 and data.get('status')==expected[script]and all(data.get('checks',{}).values())and execution.get('passed')and execution.get('original_auditor_sha256')==sha(W/script)
  if script=='audit_run.py':
   metadata=execution.get('actual_model_metadata_reads',[]);gates[script]&=len(metadata)==1 and metadata[0]['completed_unix']<read(ROOT/'ROUND_WINDOW.json')['absolute_deadline_unix']and metadata[0]['sha256']==sha(pair/'scene_model.mjb')and not execution.get('metadata_proxy_import_only',True)
 chain=read(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json')if(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json').exists()else None;failed=[]if chain is None else[k for k,v in chain['checks'].items()if not v]
 physical=bool(source_ok and result is not None and replay is not None and replay['status']=='MATCHED_RECORDED_PUBLIC_STATES'and replay['replay_integration_steps']==result['physics_steps']and replay['maximum_full_native_state_ctrl_error']<=1e-8 and all(gates.values())and chain is not None and not(set(failed)-FUNCTIONAL_CHECKS))
 functional=bool(physical and chain['status']=='PASS'and all(chain['checks'].values())and result['outcome']=='GOAL'and result['strict_safe_arrival']and result['goal_distance_m']<=.45);repeat=None
 if row['base']is not None and result is not None:repeat=compare(R/row['base'],pair);dump(pair/'FINAL_INDEPENDENT_REPEAT.json',repeat)
 records.append(dict(name=row['name'],role=row['role'],task=row['task'],run=row['run'],navigation_started=row.get('navigation_started',False),physical_passed=physical,functional_passed=functional,repeat_passed=None if repeat is None else repeat['passed'],repeat=repeat,audit_statuses=gates,result=result,functional_failed_checks=failed,discovery_details=None if chain is None else chain['details']))
pre=read(PHASE/'PREFLIGHT_INDEPENDENT_AUDIT.json')if(PHASE/'PREFLIGHT_INDEPENDENT_AUDIT.json').exists()else{};passed=bool(source_ok and read(PHASE/'COMPLETION.json')['status']=='FROZEN_STAGE_COMPLETED'and complete_gate(records)and pre.get('status')=='PASS'and pre.get('tasks')==3 and all(exact.values()))
final=dict(status='THREE_ORIGINAL_ROUTES_AND_THREE_FULL_REPEATS_VERIFIED'if passed else'NOT_PASSED',development_passed=passed,combined_three_route_development_passed=passed,independent_audit_passed=passed,source_unchanged=source_ok,preflight_passed=pre.get('status')=='PASS',complete_chain_passed=passed,native_replay_exact=all(exact.values()),planned_main=3,planned_repeats=3,new_navigation_attempts=sum(bool(x['navigation_started'])for x in records),main_attempts=sum(x['navigation_started']and x['role']=='MAIN'for x in records),main_successes=sum(x['functional_passed']and x['role']=='MAIN'for x in records),complete_repeats=sum(x['role']=='REPEAT'and x['navigation_started']for x in records),repeats_passed=all(x['repeat_passed']for x in records if x['role']=='REPEAT'),unexecuted_navigation=6-sum(bool(x['navigation_started'])for x in records),records=records,new24=0,old_remaining16=0,not_independent_confirmation=True,model_initializations=None,models_finalizer=0,integrations_finalizer=0)
for k,value in counts.items():final[k]=value if exact[k]else None;final['known_'+k]=value
final['accounts_exact']=exact;dump(PHASE/'FINAL_INDEPENDENT_AUDIT.json',final)
report=R/'docs/RPCCR_THREE_ROUTE_V848_20261106_REPORT.md';report.write_text('# V848完整目标参考与首合格名义证书三路线回归实际结果\n\n'+json.dumps(final,ensure_ascii=False,indent=2)+'\n\n用户限定本轮只三路线回归，新24确认另议。原两旧失败开发及本轮主/重复/未执行分账，不混新确认。本候选两处已声明科学变化：完整目标参考优先，原名义rank首完整合格联合证书优先；不是V842决策等价。原全部阈值/物理模型/名义评分/证书内控制库/328+8/因果完整发现链和每原生重放均保持。旧失败原样保留；模型初始化未知不填0。\n')
saved=archive(R,PHASE,W,report,C/'CANDIDATE_FREEZE.json','evidence/rpccr_three_route_v848_20261106');dump(PHASE/'FINALIZED.json',{k:v for k,v in final.items()if k!='records'}|saved|dict(report=str(report.relative_to(R))));print(json.dumps(read(PHASE/'FINALIZED.json')),flush=True)
