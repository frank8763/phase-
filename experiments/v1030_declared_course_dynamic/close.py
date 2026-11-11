"""Zero-model closure for a NEW scene, with bounded verified cloud retention."""
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1030_declared_course_dynamic';D=R/'records/nav2_v1030_20261111';REPORT=R/'docs/RPCCR_DECLARED_COURSE_V1030_REPORT.md';GH=R/'tools/phase_storage_20261107/vendor/gh';TAG='phase-new-declared-dynamic-course-v1030-20261111'
s=importlib.util.spec_from_file_location('v1030_archive',R/'experiments/v1020_terminal_two_route_development/archive.py');arc=importlib.util.module_from_spec(s);s.loader.exec_module(arc)
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def sha(p):return arc.sha(p)
def command(args,seconds=30):
 p=subprocess.run(list(map(str,args)),cwd=R,capture_output=True,text=True,timeout=seconds);assert p.returncode==0,(p.stdout+p.stderr)[-1500:];return p.stdout

def main():
 assert not(O/'CLOSURE_CLAIM.json').exists();dump(O/'CLOSURE_CLAIM.json',dict(at=time.time(),models=0));lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert json.loads((O/'APPROVAL.json').read_text())['models_authorized']is False
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 done=json.loads((O/'COMPLETION.json').read_text());tasks=json.loads((C/'TASKS.json').read_text());counts={k:0 for k in ['model_initializations','navigation_native','own_replay_native','private_mujoco_native']};unknown=[];rows=[]
 for task in tasks:
  out=Path(task['output']);p=out/'RESULT.json'
  if not p.exists():
   if out.exists():unknown.append(dict(task_id=task['task_id'],field='all_missing_final_counts'))
   continue
  result=json.loads(p.read_text());row=dict(task_id=task['task_id'],passed=result['passed'],error=result.get('error'),actual_goal_m=result.get('physical',{}).get('goal_distance_m'),source_searches=result.get('source_searches'))
  for key in counts:
   if result.get(key)is None:unknown.append(dict(task_id=task['task_id'],field=key))
   else:counts[key]+=result[key]
  rows.append(row)
 summary=dict(passed=done['passed'],closed=True,scene='V1029_ORIGINAL_MAP_OPEN_RECOVERY_SIDE_ACTOR',new_easier_course_only=True,original_dynamic_acceptance_passed=False,new24_executed=0,counts=counts,unknown_counts=unknown,rows=rows,unexecuted=done['unexecuted'],stop_reason=done['error'],training_updates=0,hardware_steps=0,guard_original=True,execution_lock_idle=True,models_authorized=False)
 D.mkdir(exist_ok=True)
 for p in O.glob('*.json'):
  if p.name not in ['CLOSURE_CLAIM.json']:shutil.copyfile(p,D/p.name)
 dump(D/'FINAL_SUMMARY.json',summary)
 REPORT.write_text('# V1030 新声明较容易课程的动态开发\n\n'+('PASS本新课程开发'if done['passed']else'NOT_PASSED')+'；**不是原动态任务或24验收通过**。原V1025窄通道失败保持。\n\n只将actor运动中心从[3,-1]改为[1.3,-2]，原19静态体/起终点/车辆/控制/.155预测/.15实际/.04m与.035rad跟踪/200原生完整尾/.45到达及.08末点余量/原测距有界噪声5%漏检不变。周期集合裁剪向量化与89保存更新全部逐数组精确。车辆速度仍.03m/s；.08车速研究未通过未执行。新模型/初态因actor构造位置改变而另存，不冒称旧模型SHA。\n\n真实测距发现、刹停、原因果完整动态路线、实际续行>=1m、目标与完整停稳/全原生状态控制接触重放/成功重复均必须。没有完整路线就停，不能用短前缀凑成功。发现前仅已知静态反应式合同。新课程预演是软件传感器夹具，不是实际成功；实际结果如下：\n\n```json\n'+json.dumps(summary,indent=2,ensure_ascii=False)+'\n```\n\n按仿真时钟运行，搜索时车和actor不积分；不称实时、实机或递归保证。下一步仍需原困难课程回迁、三路线/独立确认及公平比较，不混旧成功/失败分母。旧V1024入口Path错误、V1025唯一入口接续和旧闭批均保持。\n')
 current=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());current.update(status='REVIEW_PENDING',source_revision='V1030_CLOSED',active_entrypoint=None,active_run=None,active_window=None);current['v1030_new_course_summary']=summary;dump(R/'CURRENT_EXPERIMENT.json',current)
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n\n- FINAL V1030仅新声明较容易课程：'+('主及重复全通过'if done['passed']else'NOT_PASSED')+'；actor中心[3,-1]→[1.3,-2]，其余原19静态/起终点/车/控制/雷达5%漏检/全部安全门不改，原V1025失败不升级。新分账'+json.dumps(counts)+'，未知'+json.dumps(unknown)+'，未执行'+json.dumps(done['unexecuted'])+'；不作原任务/24验收，训练实机0，REVIEW_PENDING/执行锁关闭。见docs/RPCCR_DECLARED_COURSE_V1030_REPORT.md。\n')
 if(O/'campaign.console').exists():shutil.copyfile(O/'campaign.console',O/'campaign.console.closed_prefix')
 folders=[C,R/'experiments/v1029_declared_course_source',O,R/'runs/v1030_declared_course_dynamic',R/'runs/v1029_declared_course_source',R/'runs/v858_nav2_verified/v1030',D]
 files=set()
 for folder in folders:files.update(p for p in arc.walk(folder)if p.name not in ['campaign.console','CLOSURE_CLAIM.json']and p.suffix not in ['.pyc','.so','.lock'])
 # Preserve selected previous failure witnesses without restarting/syncing it.
 for name in ['DYNAMIC_COMPLETE_PLAN.json','FINAL_INDEPENDENT_AUDIT.json','RESULT.json']:
  p=R/'runs/v858_nav2_verified/v1024/dynamic_we'/name
  if p.exists():files.add(p)
 for folder in [R/'runs/v1026_saved_complete_diagnosis',R/'runs/v1027_timed_speed_source',R/'runs/v1028_speed_response']:
  files.update(p for p in arc.walk(folder)if p.suffix=='.json')
 files.update([REPORT,R/'CURRENT_EXPERIMENT.json'])
 record,inventory=arc.package(R,files,O/'cloud','v1030-new-declared-course',lambda:sum(p.stat().st_size for p in arc.walk(O))<2*1024**3)
 dump(D/'RECORD_INDEX.json',dict(repository='frank8763/phase-',release_tag=TAG,archives=[record],summary=summary))
 paths=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md',str(REPORT.relative_to(R)),str(C.relative_to(R)),'experiments/v1029_declared_course_source',str(D.relative_to(R))]
 command(['git','add','--',*paths]);command(['git','diff','--cached','--check','--',*paths]);command(['git','commit','--only','-m','Record bounded new-course dynamic development without upgrading original failures','--',*paths]);head=command(['git','rev-parse','HEAD']).strip()
 assert not(O/'SOURCE_SYNC_CLAIM.json').exists();dump(O/'SOURCE_SYNC_CLAIM.json',dict(commit=head,one_push=True));sync=dict(commit=head,remote_verified=False)
 try:command(['git','push','origin','HEAD:main'],30)
 except BaseException as e:sync['push_error']=repr(e)
 try:sync['remote_head']=command(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_verified']=sync['remote_head']==head
 except BaseException as e:sync['verification_error']=repr(e)
 dump(D/'SOURCE_SYNC_RESULT.json',sync)
 def gh(args,seconds=120):return command([GH,*args,'--repo','frank8763/phase-'],seconds)
 try:
  assert sync['remote_verified'],'SOURCE_REMOTE_UNVERIFIED'
  notes=O/'RELEASE_NOTES.md';notes.write_text('New easier declared actor-anchor course only; original dynamic task/24 not passed. See report and per-member SHA. Source '+head+'\n')
  gh(['release','create',TAG,'--target',head,'--title','Phase V1030 new declared dynamic development course','--notes-file',notes,'--latest=false'],30)
  gh(['release','upload',TAG,*list((O/'cloud').iterdir()),D/'RECORD_INDEX.json',D/'FINAL_SUMMARY.json',D/'SOURCE_SYNC_RESULT.json',REPORT],150)
  back=O/'readback';back.mkdir(exist_ok=False)
  def provider(part):
   gh(['release','download',TAG,'--pattern',part['name'],'--dir',back],150);return back/part['name'],True
  arc.verify(record,inventory,provider);verified=dict(passed=True,all_remote_part_and_decompressed_member_sha_verified=True,source_commit=head,release_url='https://github.com/frank8763/phase-/releases/tag/'+TAG,models=0);dump(D/'REMOTE_VERIFIED.json',verified)
  mapping={x['path']:x for x in inventory};deleted=[]
  for folder in [R/'runs/v858_nav2_verified/v1030',R/'runs/v1029_declared_course_source']:
   for p in list(arc.walk(folder)):
    if p.suffix in ['.lock','.so']:continue
    row=mapping[str(p.relative_to(R))];assert p.stat().st_size==row['bytes']and sha(p)==row['sha256'];deleted.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size));p.unlink()
   for base,dirs,names in os.walk(folder,followlinks=False):
    for name in dirs+names:
     p=Path(base,name)
     if p.is_symlink():p.unlink()
  cleanup=dict(passed=True,deleted_bytes=sum(x['bytes']for x in deleted),manifest=deleted,models=0,remote_required_records_verified=True,old_unverified_actual_raw_untouched=True);dump(D/'CLEANUP.json',cleanup);gh(['release','upload',TAG,D/'REMOTE_VERIFIED.json',D/'CLEANUP.json'],30);shutil.rmtree(O/'cloud');shutil.rmtree(back)
 except BaseException as e:dump(D/'REMOTE_PENDING.json',dict(error=repr(e),raw_retained=True,no_automatic_retry=True,models=0))
 command(['git','add','--',str(D.relative_to(R))]);command(['git','commit','--only','-m','Keep V1030 delivery receipts without a second push','--',str(D.relative_to(R))]);dump(O/'CLOSED.json',dict(science_closed=True,models_authorized=False,remote_verified=(D/'REMOTE_VERIFIED.json').exists(),summary=summary));print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
