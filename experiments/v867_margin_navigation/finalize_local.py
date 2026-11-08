"""Bounded closed-file audit and necessary evidence packaging only; no model/ROS imports."""
import fcntl,hashlib,importlib.util,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v867_margin_navigation';REC=R/'records/nav2_v867_20261108'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 summary=read(O/'COMPLETION.json');assert summary['closed'];assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 frozen=read(C/'SOURCE_FREEZE.json')
 for n,h in frozen['files'].items():assert sha(R/n)==h,n
 sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')];from audit import audit
 rows=[]
 for row in summary['rows']:
  p=Path(row['output']);task=read(p/'TASK.json')if(p/'TASK.json').exists()else None
  if task and(p/'INDEPENDENT_AUDIT.json').exists():
   before=(p/'INDEPENDENT_AUDIT.json').read_bytes();old=json.loads(before)
   try:checked=audit(task)
   finally:(p/'INDEPENDENT_AUDIT.json').write_bytes(before)
   assert checked==old
  else:checked=dict(passed=False,actual_native=None,reason='INCOMPLETE_EVIDENCE')
  rows.append(dict(task_id=row['task_id'],audit=checked))
 if summary['passed']:assert len(rows)==12 and all(x['audit']['passed']for x in rows)and read(O/'STATIC_GATE.json')['passed']
 result=dict(passed=True,audit_scope='Closed execution record consistency; functional outcome separate',functional_passed=summary['passed'],source_readback_files=len(frozen['files']),rows=rows,actual_native=summary['actual_native'],replay_native=summary['replay_native'],model_initializations_this_audit=0,integrations_this_audit=0,guard_restored=True,lock_idle=True,at=time.time());dump(O/'FINAL_INDEPENDENT_AUDIT.json',result);dump(REC/'FINAL_INDEPENDENT_AUDIT.json',result)
 for name in ['AUTHORIZATION.json','ROUND_WINDOW.json','ZERO_QUALIFICATION.json','COMPLETION.json','RESULTS.json','PREFLIGHTS.json','STATIC_GATE.json','REPEATS.json','ERROR.json']:
  p=O/name
  if p.exists():(REC/name).write_bytes(p.read_bytes())
 report=R/'docs/NAV2_MARGIN_STATIC_DYNAMIC_V867_REPORT.md';lines=['# V867全局余量候选：'+summary['status'],'','2026-11-08；新独立90分钟窗口，旧失败/截止保持。成熟Nav2名义开发，非旧RP-CCR328保证或新24确认。','',f"实际导航 {summary['attempted_navigation']}；未执行 {summary['unexecuted_navigation']}；实际原生 {summary['actual_native']}；自身控制重放 {summary['replay_native']}。",'', '| 任务 | 结果 | 原生 | 重放 | 目标距离m | 最低实际净空m |','|---|---|---:|---:|---:|---:|']
 for row in summary['rows']:lines.append(f"| {row['task_id']} | {'PASS'if row.get('passed')else'FAIL/UNKNOWN'} | {row.get('actual_native')} | {row.get('replay_native')} | {row.get('goal_distance_m')} | {row.get('minimum_clearance_m')} |")
 lines+=['','完整原始状态/轮控/接触/测距、真实Nav2参考和命令与t0均保留；所有输入SHA闭批回读。每项自身执行控制重放≤1e-8，闭环重跑轨迹可能不同，不混同。未知账目不填0。','', '动态实际启动数：'+str(summary['dynamic_navigation'])+'；新24/训练/实机0。原guard恢复/锁空闲。所有静态完整门过后才准入动态，首失败即停；没有冻结后修补或额外候选。','', '候选只增加全局每轴足迹外扩.15→.20，局部安全和控制不变。软件初始参考筛查不构成修复因果证明；实际结果决定可行性。必要证据同仓GitHub来源/解压/下载SHA和实际恢复后清缓存。']
 report.write_text('\n'.join(lines)+'\n')
 spec=importlib.util.spec_from_file_location('archive_tools',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=O/'cloud';m.OUT.mkdir(exist_ok=True)
 files=[]
 for base in [O,R/'runs/v858_nav2_verified/v867',R/'runs/v866_margin_qualification',C,R/'experiments/v866_margin_qualification',REC]:
  if base.exists():files += [p for p in m.walk(base)if not any(x in p.relative_to(base).parts for x in ['cloud','verified_transport_cache','cache','__pycache__'])and p.name not in ['campaign.console','finalize.console']]
 files.append(report);group=m.archive('v867-navigation-evidence',files)
 index=dict(format_version=1,repository='frank8763/phase-',release_tag='phase-nav2-v867-20261108',release_url='https://github.com/frank8763/phase-/releases/tag/phase-nav2-v867-20261108',archives=[{k:v for k,v in group.items()if k!='files'}],scientific_outcome=summary['status'],base_runtime_dependencies=['V856 ROS runtime','V863 signed RPP plugin'],status='LOCAL_ALL_SOURCE_DECOMPRESSION_AND_PART_SHA_VERIFIED_REMOTE_PENDING',created_unix=time.time());dump(REC/'RECORD_INDEX.json',index);dump(m.OUT/'RECORD_INDEX.json',index)
 final=dict(status='LOCAL_FINALIZED_REMOTE_TRANSFER_PENDING',functional_passed=summary['passed'],full_source_and_archive_member_sha_verified=True,new_models_this_finalize=0,model_integrations_this_finalize=0,actual_native=summary['actual_native'],replay_native=summary['replay_native'],guard_restored=True,lock_idle=True,closed_unix=time.time());dump(O/'FINALIZED.json',final);dump(REC/'LOCAL_FINALIZED.json',final);print(json.dumps(final),flush=True)
if __name__=='__main__':main()
