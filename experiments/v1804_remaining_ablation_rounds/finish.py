"""Metadata-only closure and human report for exactly one assignment."""
import fcntl,hashlib,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;ROOT=R/'runs/v1643_formal_parent_metadata';SOURCE=R/'runs/v1802_closure_grant_refresh';PARSER=__import__('argparse').ArgumentParser();PARSER.add_argument('--assignment',required=True);ARGS=PARSER.parse_args();AID=ARGS.assignment;O=ROOT/'rounds'/AID
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
 os.sched_setaffinity(0,{5});completion=read(O/'COMPLETION.json');assert completion['closed']and completion['review_restored']and completion['lock_idle']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 identity=read(O/'OWNED_CHILD.json');stat=Path('/proc')/str(identity['pid'])/'stat'
 if stat.exists():assert stat.read_text().split()[21]!=identity['start_ticks']
 if(O/'actual/RESULT.json').exists():
  subprocess.run([__import__('sys').executable,str(C/'close.py'),'--assignment',AID],check=True,cwd=R)
 else:
  frozen=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
  record=dict(closed=True,passed=False,machine_RESULT_missing=True,canonical_owner_counts_preserved=dict(canonical_vehicle_initializations=completion.get('canonical_vehicle_initializations'),actual_native=completion.get('actual_native'),own_replay_native=completion.get('own_replay_native')),console_path=str((O/'formal.console').relative_to(R)),console_sha256=sha(O/'formal.console'),outer_first_error=completion.get('first_error'),source_members=len(frozen),all_source_SHA_verified_after_child_exit=True,model_factory_actual_replay_counts_unknown=True,models_not_assumed_zero=True,no_reconstructed_RESULT=True)
  assert not(O/'CONSOLE_RECOVERED_FAILURE_RECORD.json').exists();put(O/'CONSOLE_RECOVERED_FAILURE_RECORD.json',record)
  assert not(O/'RUNTIME_CLOSED_REVIEW.json').exists();put(O/'RUNTIME_CLOSED_REVIEW.json',dict(record,formal_assignment_id=AID,actual_native=completion.get('actual_native'),own_replay_native=completion.get('own_replay_native'),internal_factory_model_constructions=None,full_modelwork_total=None,actual_original_goal_reached=None,independent_full_goal_audit=None,first_error=completion.get('first_error'),review_original=True,execution_idle=True,owned_child_gone=True,remote_runtime_recovery_pending=True))
  ledger=read(ROOT/'FORMAL_LEDGER.json');row=next(x for x in ledger['rows']if x['assignment_id']==AID);row.update(registered=True,closed=True,status='CLOSED_TECHNICAL_CENSOR_RECOVERY_PENDING',model_result=False,actual_native=completion.get('actual_native'),own_replay_native=completion.get('own_replay_native'),source_version_root=str(SOURCE.relative_to(R)),completion_path=str((O/'COMPLETION.json').relative_to(R)),completion_sha256=sha(O/'COMPLETION.json'),scientific_classification='MACHINE_RESULT_MISSING_COUNTS_UNKNOWN');put(ROOT/'FORMAL_LEDGER.json',ledger)
 review=read(O/'RUNTIME_CLOSED_REVIEW.json');ledger=read(ROOT/'FORMAL_LEDGER.json');closed=[x for x in ledger['rows']if x.get('closed')];ledger.update(registered_assignments=sum(bool(x.get('registered'))for x in ledger['rows']),closed_assignments=len(closed),unexecuted_assignments=20-sum(bool(x.get('registered'))for x in ledger['rows']),closed_non_success_assignments=sum(not x.get('model_result',False)for x in closed),closed_successful_assignments=sum(bool(x.get('model_result',False)and x.get('owner_passed',False))for x in closed),closed_actual_native_known_sum=sum(x['actual_native']for x in closed if type(x.get('actual_native'))is int),closed_own_replay_native_known_sum=sum(x['own_replay_native']for x in closed if type(x.get('own_replay_native'))is int),closed_native_counts_unknown_assignments=[x['assignment_id']for x in closed if type(x.get('actual_native'))is not int or type(x.get('own_replay_native'))is not int],recorded_unix=time.time());put(ROOT/'FORMAL_LEDGER.json',ledger)
 physical=review.get('physical_telemetry')or{};replay=review.get('replay')or{};full=review.get('independent_full_goal_audit')or{}
 text='# EW formal assignment：单项后台实验结果\n\n'+'完整合格成功：'+str(review['passed'])+'。以原机器RESULT与独立审核为准，不按进程退出码或到达位置推断成功。\n\n'
 text+='|项目|本轮记录|\n|---|---|\n'
 for name,value in [('actual native',review.get('actual_native')),('自身replay native',review.get('own_replay_native')),('记录到达原目标',review.get('actual_original_goal_reached')),('最终目标距离m',physical.get('goal_distance_m')),('实际最小净空m',physical.get('minimum_actual_clearance_m')),('坏接触',physical.get('bad_contacts')),('完整独立审核PASS',full.get('passed')),('replay最大误差',replay.get('maximum_qpos_qvel_ctrl_mocap_error')),('首错误',review.get('first_error'))]:text+='|'+name+'|'+str(value).replace('\n',' ')+'|\n'
 text+='\n模型工作只按原q1159恢复子集记录，normal/static/其他FFI和内部总量未知。不改原安全门/源/seed，不重跑旧case。正式表'+str(ledger['closed_assignments'])+'/20关闭、'+str(ledger['unexecuted_assignments'])+'项未执行；旧weekend与pilot账独立。\n\n原证据位于common study ROOT/rounds/本assignment。本报告在同轮远端闭环之前生成；闭环完成后另有补充，不能将归档PASS当科学成功。\n\n本轮完成后由通宵父controller核完整闭环与安全；只有父controller可准入下一锁定项。\n'
 (R/('docs/EW_'+AID+'_V1804_REPORT.md')).write_text(text)
 print(json.dumps(dict(closed=True,scientific_passed=review['passed'],actual_native=review.get('actual_native'),own_replay_native=review.get('own_replay_native'),next_round_requires_user_command=True)))
if __name__=='__main__':main()
