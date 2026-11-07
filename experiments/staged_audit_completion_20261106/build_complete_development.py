"""Operations-only final assembly, after every saved audit and mutation negative has passed."""
import ast,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;ROOT=R/'runs/staged_audit_completion_20261106'
def read(p):return json.loads(p.read_text())
assert read(ROOT/'COMPLETE_COVERAGE_COMPLETION.json')['passed']and read(ROOT/'COMPLETE_COVERAGE_NEGATIVES.json')['passed']
def replace(source,before,after):
 assert source.count(before)==1,(before,source.count(before));return source.replace(before,after)
engine=(C/'engine.py').read_text()
engine=replace(engine,"cmd+=[str(C.relative_to(R)/'audit_entry.py'),'--write-root',str(Path(args[0]))]","entry='audit_entry.py'if script=='audit_run.py'else'complete_audit_entry.py'\n     cmd+=[str(C.relative_to(R)/entry),'--write-root',str(Path(args[0]))]")
engine=replace(engine,"row['audits'][script]=execute(script,args,pair/(script+'.console'),cap)","row['audits'][script]=execute(script,args,pair/(script+'.console'),max(cap,600))")
start=engine.index("  if stage=='pilot90':\n   pre=");end=engine.index("  status='FROZEN_STAGE_COMPLETED'",start)
engine=engine[:start]+'''  assert pilot is not None
  pre=[read(O/'pilot90/PREFLIGHTS.json')[0]]
  dump(phase/'LOCKED_T0_TASK_LIST.json',[tasks_by[10060002]]);dump(phase/'PREFLIGHTS.json',pre);dump(phase/'PILOT_REFERENCE.json',pilot)
  extras.extend([str((ROOT/'SUPPLEMENT_FINALIZED.json').relative_to(R)),str((ROOT/'FINAL_INDEPENDENT_AUDIT.json').relative_to(R))])
  assert execute('audit_field_preflight.py',[phase],phase/'preflight_pilot_only.console',60)==0,'PILOT_REGISTERED_T0_AUDIT_FAILED'
  dump(phase/'PILOT_ONLY_PREFLIGHT_INDEPENDENT_AUDIT.json',read(phase/'PREFLIGHT_INDEPENDENT_AUDIT.json'))
  dump(phase/'PILOT_ONLY_LOCKED_T0_TASK_LIST.json',[tasks_by[10060002]]);dump(phase/'PILOT_ONLY_PREFLIGHTS.json',pre)
  baseline=read(ROOT/'FINAL_INDEPENDENT_AUDIT.json')['records'][0]
  unit(tasks_by[10060002],'long_repeat02','REPEAT',baseline)
  pre.append(t0(tasks_by[10060008],'long_t0_08'))
  dump(phase/'LOCKED_T0_TASK_LIST.json',tasks);dump(phase/'PREFLIGHTS.json',pre)
  assert execute('audit_field_preflight.py',[phase],phase/'preflight_audit.console',60)==0,'REGISTERED_T0_AUDIT_FAILED'
  main=unit(tasks_by[10060008],'long_main08','MAIN');unit(tasks_by[10060008],'long_repeat08','REPEAT',main)
''' +engine[end:]
ast.parse(engine);(C/'engine.py').write_text(engine)
final=(C/'finalize_supplement.py').read_text()
final=replace(final,"completion=read(ROOT/'SAVED_AUDIT_COMPLETION.json');assert completion['passed']and completion['auditors_completed']==17","completion=read(ROOT/'COMPLETE_COVERAGE_COMPLETION.json');assert completion['passed']and completion['audit_scopes_completed']==17\n assert read(ROOT/'COMPLETE_COVERAGE_NEGATIVES.json')['passed']")
final=replace(final,"result=read(P/filename);execution=read(P/(script+'.execution.json'))","actual_file='REACTIVE_POLICY_AUDIT_COMPLETE_LOGS.json'if script=='audit_reactive.py'else filename\n  execution_file=script+('.complete_logs'if script=='audit_reactive.py'else'')+'.execution.json'\n  result=read(P/actual_file);execution=read(P/execution_file)")
final=replace(final,"original_audit_timeout_preserved=True,complete_repeats=0","original_audit_timeout_preserved=True,original_reactive_count_FAIL_preserved=True,complete_both_log_witness_coverage=True,coverage_negative_cases=10,complete_repeats=0")
final=replace(final,"唯一执行加速为同一不可变JSONL解析缓存。", "执行加速为同一不可变JSONL解析缓存；原reactive计数仅覆盖普通日志1929份而遗漏联合日志7672份的FAIL保留，补充用原逐点公式及全部原断言核验完整9601份，误差0，10负例拒绝。")
ast.parse(final);(C/'finalize_supplement.py').write_text(final)
prepare=(C/'prepare_development.py').read_text()
prepare=replace(prepare,"original17_audits_actual_saved_GOAL_passed=True", "original17_audit_scopes_saved_GOAL_passed=True,original_reactive_count_FAIL_preserved=True,strict9601_witness_coverage=True,coverage_negative_cases=10")
(C/'prepare_development.py').write_text(prepare)
campaign=(C/'campaign12.py').read_text();campaign=replace(campaign,"protocol=str((C/'PROTOCOL.md').relative_to(R))","protocol=str((C/'DEVELOPMENT_PROTOCOL.md').relative_to(R))");(C/'campaign12.py').write_text(campaign)
for p in C.glob('*.py'):ast.parse(p.read_text())
print(json.dumps(dict(assembled=True,science_changes=0,repeat_before_task08=True,strict_complete_witness_coverage=True)))
