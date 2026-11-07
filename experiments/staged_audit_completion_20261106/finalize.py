"""Independent persisted stage finalization; no Mujoco import or integration."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('FINALIZER_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
import fcntl,json
from pathlib import Path
from evidence_rules import AUDITS,FUNCTIONAL_CHECKS,dump,read,sha,repeat_check
from archive import archive
C=Path(__file__).parent
ROOT=Path(__file__).resolve().parents[2]/'runs/staged_audit_completion_20261106'
R=Path(__file__).resolve().parents[2];W=R/'experiments/v842_staged_long_navigation';O=R/'runs/v842_staged_long_navigation';stage=sys.argv[1];assert stage in['development12'];P=O/stage
lock=(P/'finalize.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
if(P/'FINALIZED.json').exists():print('ALREADY_FINALIZED_NO_OVERWRITE');raise SystemExit(0)
assert read(P/'ROUND_WINDOW.json')['round_closed']and(R/'REVIEW_PENDING').read_bytes()==(P/'REVIEW_PENDING.before').read_bytes()
freeze=read(C/'DEVELOPMENT_FREEZE.json');source_ok=all(sha(R/n)==h for n,h in freeze['files'].items());rows=read(P/'RESULTS.json');expected=read(R/'runs/staged_90_then12_20261106/ZERO_MODEL_QUALIFICATION.json')['expected_audit_statuses'];records=[];counts=dict(navigation_native=0,private_native=0,replay_native=0);exact={k:True for k in counts}
sys.path.insert(0,str(W));from contact_fingerprint import compare_contacts
for row in rows:
 pair=R/row['run'];result=read(pair/'geometry_memory/result.json')if(pair/'geometry_memory/result.json').exists()else None;interrupted=read(pair/'geometry_memory/interrupted.json')if(pair/'geometry_memory/interrupted.json').exists()else None;actual=result or interrupted or {};replay=read(pair/'NATIVE_REPLAY_AUDIT.json')if(pair/'NATIVE_REPLAY_AUDIT.json').exists()else None
 for label,key in [('navigation_native','physics_steps'),('private_native','prediction_steps')]:
  n=actual.get(key);exact[label]&=result is not None and isinstance(n,int);counts[label]+=n if isinstance(n,int)else 0
 n=None if replay is None else replay.get('replay_integration_steps');exact['replay_native']&=isinstance(n,int);counts['replay_native']+=n if isinstance(n,int)else 0
 checks={}
 for script,filename,_ in AUDITS:
  data=read(pair/filename)if(pair/filename).exists()else {};checks[script]=bool(row['audits'].get(script)==0 and data.get('status')==expected[script]and all(data.get('checks',{}).values()))
 chain=read(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json')if(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json').exists()else None;failed=[]if chain is None else[k for k,v in chain['checks'].items()if not v]
 physical=bool(source_ok and result is not None and replay is not None and replay['status']=='MATCHED_RECORDED_PUBLIC_STATES'and replay['maximum_full_native_state_ctrl_error']<=1e-8 and replay['replay_integration_steps']==result['physics_steps']and all(checks.values())and chain is not None and not(set(failed)-FUNCTIONAL_CHECKS))
 functional=bool(physical and chain['status']=='PASS'and all(chain['checks'].values())and result['outcome']=='GOAL'and result['strict_safe_arrival']and result['goal_distance_m']<=.45);repeated=None
 if row['base']is not None and result is not None:
  baseline=R/row['base'];base_result=read(baseline/'geometry_memory/result.json');repeated=repeat_check(baseline,pair,base_result,result,compare_contacts);dump(pair/'FINAL_INDEPENDENT_REPEAT.json',repeated)
 records.append(dict(name=row['name'],role=row['role'],task=row['task'],run=row['run'],physical_passed=physical,functional_passed=functional,audit_statuses=checks,result=result,failed_functional_checks=failed,repeated=repeated))
expected_names=['pilot_main02']if stage=='pilot90'else['long_repeat02','long_main08','long_repeat08'];preflight=read(P/'PREFLIGHT_INDEPENDENT_AUDIT.json')if(P/'PREFLIGHT_INDEPENDENT_AUDIT.json').exists()else {};repeats=[x for x in records if x['role']=='REPEAT'];repeat_ok=all(x['repeated']is not None and x['repeated']['passed']for x in repeats)
passed=bool(source_ok and read(P/'COMPLETION.json')['status']=='FROZEN_STAGE_COMPLETED'and[n['name']for n in records]==expected_names and all(x['physical_passed']and x['functional_passed']for x in records)and preflight.get('status')=='PASS'and repeat_ok and all(exact.values()))
if stage=='development12':
 from limits import can_transition
 assert can_transition(read(ROOT/'SUPPLEMENT_FINALIZED.json'))
status=('PILOT_COMPLETE_CHAIN_VERIFIED'if stage=='pilot90'else'TWO_OLD_FAILURES_AND_TWO_COMPLETE_REPEATS_VERIFIED')if passed else'NOT_PASSED'
final=dict(status=status,development_passed=passed,independent_audit_passed=passed,complete_chain_passed=passed,native_replay_exact=all(exact.values()),source_unchanged=source_ok,preflight_passed=preflight.get('status')=='PASS',records=records,new_navigation_attempts=len(rows),planned_new_navigations=len(expected_names),complete_repeats=len(repeats),repeats_passed=repeat_ok,external_pilot_main_reused=1 if stage=='development12'else 0,not_independent_confirmation=True,new24=0,models_finalizer=0,integrations_finalizer=0)
for k,n in counts.items():final[k]=n if exact[k]else None;final['known_'+k]=n
final['accounts_exact']=exact;dump(P/'FINAL_INDEPENDENT_AUDIT.json',final)
report=R/f'docs/RPCCR_V842_{stage.upper()}_20261106_REPORT.md';report.write_text('# V842 '+stage+' 实际结果\n\n'+json.dumps(final,ensure_ascii=False,indent=2)+'\n\nV841科学决策保持；预算与任务注册/分项计时调整已冻结。资格/主/完整重复/旧参考/新确认分别记账；此处不是新24或三路线验收。完整发现链、原328/.155/.15/329执行657规划、自体控制、原生重放和全部新增336尾门保持。未知计数为null，旧失败/窗口/原件保持。\n')
saved=archive(R,P,W,report,C/'DEVELOPMENT_FREEZE.json',f'evidence/rpccr_v842_{stage}_20261106');dump(P/'FINALIZED.json',{k:v for k,v in final.items()if k!='records'}|saved|dict(report=str(report.relative_to(R))));print(json.dumps(read(P/'FINALIZED.json')))
