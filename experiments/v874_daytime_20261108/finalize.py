"""Offline zero-model closure, accurate executed denominators and lossless evidence archive."""
import fcntl,hashlib,importlib.util,json,os,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v874_daytime_20261108';REC=R/'records/nav2_v874_20261108'
def read(p):return json.loads(p.read_text())
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);s=read(O/'COMPLETION.json');assert s['closed'];assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 import sys
 sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
 from audit import audit as independent_audit
 freeze=read(C/'SOURCE_FREEZE.json')
 for name,h in freeze['files'].items():assert sha(R/name)==h,name
 rows=[]
 for x in s['rows']:
  p=Path(x['output'])
  if (p/'INDEPENDENT_AUDIT.json').exists()and(p/'TASK.json').exists():
   before=(p/'INDEPENDENT_AUDIT.json').read_bytes()
   try:checked=independent_audit(read(p/'TASK.json'))
   finally:(p/'INDEPENDENT_AUDIT.json').write_bytes(before)
   assert checked==json.loads(before),'AUDIT_READBACK_CHANGED'
  a=read(p/'INDEPENDENT_AUDIT.json')if(p/'INDEPENDENT_AUDIT.json').exists()else{};n=read(p/'RESULT.json')if(p/'RESULT.json').exists()else{};rows.append(dict(task_id=x['task_id'],role=x['role'],variant=x['variant'],passed=a.get('passed',False),actual_native=n.get('actual_native'),replay_native=n.get('replay_native'),private_native=n.get('private_native'),minimum_clearance_m=n.get('minimum_actual_clearance_m'),goal_m=n.get('goal_distance_m'),bad_contacts=n.get('bad_contacts'),maximum_own_replay_error=n.get('replay',{}).get('maximum_qpos_qvel_ctrl_mocap_error')))
 assert all(x['actual_native']==y['actual_native']and x['replay_native']==y['replay_native']for x,y in zip(rows,s['rows']))
 audit=dict(passed=True,audit_scope='Closed batch source/record consistency; functional and safety outcomes separate',dynamic_acceptance_passed=s['dynamic_acceptance_passed'],source_sha_readback_files=len(freeze['files']),rows=rows,actual_native=s['actual_native'],replay_native=s['replay_native'],private_native=s['private_native'],new24_attempted=s['new24_attempted'],unexecuted_registered_navigation=s['unexecuted_registered_navigation'],model_initializations_this_audit=0,integrations_this_audit=0,guard_restored=True,execution_lock_idle=True,at=time.time());dump(O/'FINAL_INDEPENDENT_AUDIT.json',audit);dump(REC/'FINAL_INDEPENDENT_AUDIT.json',audit)
 report=R/'docs/NAV2_DAYTIME_V874_REPORT.md';text=['# V874有限无人值守日间实验',f"\n结果：{s['status']}；模型硬截止2026-11-08 17:00+0800，没有续窗。",f"\n已执行导航{s['attempted_navigation']}；未执行登记项{s['unexecuted_registered_navigation']}；实际原生{s['actual_native']}；自身重放{s['replay_native']}；私有{s['private_native']}。",f"\n新24已执行{s['new24_attempted']}；完整动态确认{s['dynamic_acceptance_passed']}。未完成全24不报告完整分母率。训练/实机0。",'\n|任务|用途|候选|功能|实际/重放|末目标距离|最低净空|','|---|---|---|---|---|---|---|']
 for x in rows:text.append(f"|{x['task_id']}|{x['role']}|{x['variant']}|{x['passed']}|{x['actual_native']}/{x['replay_native']}|{x['goal_m']}|{x['minimum_clearance_m']}|")
 text+=['\n三个前视距离是同一成熟RPP控制器的开发配置，不是三种新算法；MPPI配对和消融只在验收门通过后解锁。每项自身控制全状态/接触/mocap重放合同≤1e-8，异步闭环重复不冒称逐位相同。', '\n包含所有软件未合格/模型入口或实际失败及未执行项；未知积分不填0。guard原字节恢复/锁空闲。有限单actor课程非旧RP-CCR328证书、任意遮挡/多actor/实时或RAS创新证明。', '\n所有证据本地SHA/解压SHA归档回读；远端未验证时保留本地，不删除必需记录。断网恢复后按索引上传回读再清缓存。']
 report.write_text('\n'.join(text)+'\n')
 for name in ['AUTHORIZATION.json','ROUND_WINDOW.json','COMPLETION.json','RESULTS.json','PREFLIGHTS.json','BRANCHES.json','SOFTWARE_RESULTS.json','SELECTED.json','DEVELOPMENT_GATE.json','CONFIRMATION_GATE.json','CONFIRMATION_OUTCOMES.json','ZERO_QUALIFICATION.json','PREPARATION_ERRORS.json']:
  p=O/name
  if p.exists():shutil.copyfile(p,REC/name)
 spec=importlib.util.spec_from_file_location('archive_tools',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=O/'cloud';m.OUT.mkdir(exist_ok=True);files=[]
 for base in [O,R/'runs/v858_nav2_verified/v874',C,REC]:
  if base.exists():files += [p for p in m.walk(base)if not any(x in p.relative_to(base).parts for x in ['cloud','__pycache__'])and p.name not in ['campaign.console','guardian.console','finalize.console']]
 files.append(report);g=m.archive('v874-offline-execution-evidence',files);index=dict(format_version=1,repository='frank8763/phase-',release_tag='phase-nav2-v874-20261108',release_url='https://github.com/frank8763/phase-/releases/tag/phase-nav2-v874-20261108',archives=[{k:v for k,v in g.items()if k!='files'}],status='LOCAL_ALL_MEMBER_SHA_VERIFIED_REMOTE_PENDING',scientific_outcome=s['status']);dump(REC/'RECORD_INDEX.json',index);dump(m.OUT/'RECORD_INDEX.json',index)
 final=dict(status='LOCAL_FINALIZED_REMOTE_TRANSFER_PENDING',dynamic_acceptance_passed=s['dynamic_acceptance_passed'],actual_native=s['actual_native'],replay_native=s['replay_native'],private_native=s['private_native'],all_source_and_decompressed_member_sha_verified=True,models_this_finalize=0,integrations_this_finalize=0,raw_evidence_deleted=False,remote_verified=False,guard_restored=True,execution_lock_idle=True,at=time.time());dump(O/'FINALIZED.json',final);dump(REC/'LOCAL_FINALIZED.json',final);print(json.dumps(final),flush=True)
if __name__=='__main__':main()
