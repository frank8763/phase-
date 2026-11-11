"""Bounded zero-model closure, archive readback, single new-round Git push."""
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1024_full_route_execution';D=R/'records/nav2_v1024_20261111';REPORT=R/'docs/RPCCR_FULL_ROUTE_EXECUTION_V1024_REPORT.md';GH=R/'tools/phase_storage_20261107/vendor/gh';TAG='phase-full-input-route-v1024-20261111'
spec=importlib.util.spec_from_file_location('v1024_verified_archive',R/'experiments/v1020_terminal_two_route_development/archive.py');archive=importlib.util.module_from_spec(spec);spec.loader.exec_module(archive)
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(args,cap=30):
 p=subprocess.run(list(map(str,args)),cwd=R,capture_output=True,text=True,timeout=cap);assert p.returncode==0,(p.stdout+p.stderr)[-1200:];return p.stdout

def main():
 assert not(O/'ZERO_MODEL_CLOSURE_CLAIM.json').exists();dump(O/'ZERO_MODEL_CLOSURE_CLAIM.json',dict(at=time.time(),models=0))
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert json.loads((O/'APPROVAL.json').read_text())['models_authorized']is False
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 done=json.loads((O/'COMPLETION.json').read_text());tasks=json.loads((C/'TASKS.json').read_text());counts=dict(model_initializations=0,navigation_native=0,own_replay_native=0,private_mujoco_native=0);unknown=[];task_rows=[]
 for task in tasks:
  p=Path(task['output'])/'RESULT.json'
  if not p.exists():
   if Path(task['output']).exists():unknown.append(dict(task_id=task['task_id'],field='all_physical_counts'))
   continue
  result=json.loads(p.read_text());task_rows.append(dict(task_id=task['task_id'],passed=result['passed'],status=result.get('status'),error=result.get('error'),goal=result.get('physical',{}).get('goal_distance_m'),maximum_position_m=json.loads((Path(task['output'])/'OWNER_EVENTS.json').read_text()).get('maximum_position_m')if(Path(task['output'])/'OWNER_EVENTS.json').exists()else None))
  for field in counts:
   if result.get(field)is None:unknown.append(dict(task_id=task['task_id'],field=field))
   else:counts[field]+=result[field]
 summary=dict(passed=done['passed'],closed=True,counts=counts,unknown_counts=unknown,tasks=task_rows,unexecuted=done['unexecuted'],stop_reason=done['error'],new24_executed=0,training_updates=0,hardware_steps=0,models_authorized=False,guard_original=True,execution_lock_idle=True)
 D.mkdir(exist_ok=True)
 for name in ['COMPLETION.json','ROUND_WINDOW.json','APPROVAL.json','START_RECEIPT.json','OWNER_QUALIFICATION.json','ENTRY_QUALIFICATION.json','IMPORT_QUALIFICATION.json','QUEUE_QUALIFICATION.json','FINAL_SOURCE_QUALIFICATION.json','PREPARATION_ERRORS.json']:
  if(O/name).exists():shutil.copyfile(O/name,D/name)
 dump(D/'FINAL_SUMMARY.json',summary)
 REPORT.write_text('# V1024 完整目标输入路线开发\n\n'+('PASS有限开发'if done['passed']else'NOT_PASSED')+'。新90分钟根窗，所有旧批与旧截止保持，首次异常停止依赖。\n\n```json\n'+json.dumps(summary,indent=2,ensure_ascii=False)+'\n```\n\n原0.155预测/0.15实际/0.04m与0.035rad跟踪/200完整停车尾/原目标0.45和0.08末点余量保持。V1023用逐原生输入预测替代稀疏几何参考，去掉仅稀疏参考所需的额外误差，原空间延迟20ms余量保持0.088534210m，原始净空准入0.243534210m。一个实际控制者，未启动Nav2 ROS控制动作；不能继承旧版24验收、称算法优越或实时。发现前仅已知静态反应式合同；原测距发现后撤销静态后缀，原因果完整200停车及固定20秒保持观察后，一次完整动态整周期安全输入搜索，拒绝不执行短前缀。低阶模型无长轨迹误差定理，实际跟踪超限即停。\n\n动态全链/原生安全/完整控制状态重放与成功重复均需通过；未执行不作0/24，静态/动态/重复分账。训练/SAC/实机0。Stage隔离。无自动新物理、候选、路线或窗口。必要证据远端来源SHA与解压回读完成后再清缓存。\n')
 current=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());current.update(status='REVIEW_PENDING',source_revision='V1024_CLOSED',active_entrypoint=None,active_run=None,active_window=None);current['v1024_summary']=summary;dump(R/'CURRENT_EXPERIMENT.json',current)
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n\n- FINAL V1024新完整输入路线开发：'+('全部门通过'if done['passed']else'NOT_PASSED')+'；精确已知分账'+json.dumps(counts,ensure_ascii=False)+'；未知'+json.dumps(unknown,ensure_ascii=False)+'；未执行'+json.dumps(done['unexecuted'],ensure_ascii=False)+'。首次失败/旧窗不变，REVIEW_PENDING原字节/锁空闲，训练实机/新24为0；详见docs/RPCCR_FULL_ROUTE_EXECUTION_V1024_REPORT.md。\n')
 if(O/'campaign.console').exists():shutil.copyfile(O/'campaign.console',O/'campaign.console.closed_prefix')
 files=[]
 for folder in [C,R/'experiments/v1023_dense_input_route',O,R/'runs/v1023_dense_input_route',R/'runs/v858_nav2_verified/v1024',D]:
  files.extend(p for p in archive.walk(folder)if p.name not in ['campaign.console','ZERO_MODEL_CLOSURE_CLAIM.json']and p.suffix not in ['.so','.pyc','.lock'])
 files.extend([REPORT,R/'CURRENT_EXPERIMENT.json']);record,catalog=archive.package(R,files,O/'cloud','v1024-full-input-route-evidence',lambda:sum(p.stat().st_size for p in archive.walk(O))<2*1024**3)
 index=dict(repository='frank8763/phase-',release_tag=TAG,summary=summary,archives=[record]);dump(D/'RECORD_INDEX.json',index)
 # Review and commit only this new work, leaving unrelated user changes alone.
 paths=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md',str(REPORT.relative_to(R)),str(C.relative_to(R)),'experiments/v1023_dense_input_route',str(D.relative_to(R))]
 run(['git','add','--',*paths]);run(['git','diff','--cached','--check','--',*paths]);run(['git','commit','--only','-m','Record bounded complete input route development and native audits','--',*paths])
 head=run(['git','rev-parse','HEAD']).strip();sync_claim=O/'SOURCE_SYNC_CLAIM.json';assert not sync_claim.exists();dump(sync_claim,dict(commit=head,one_push=True,models=0));sync=dict(commit=head,remote_verified=False)
 try:sync['push_output']=run(['git','push','origin','HEAD:main'],30)[-1500:]
 except BaseException as e:sync['push_error']=repr(e)
 try:sync['remote_head']=run(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_verified']=sync['remote_head']==head
 except BaseException as e:sync['verify_error']=repr(e)
 dump(D/'SOURCE_SYNC_RESULT.json',sync)
 def gh(args,cap=30):return run([GH,*args,'--repo','frank8763/phase-'],cap)
 try:
  notes=O/'RELEASE_NOTES.md';notes.write_text('Finite full-route development; original failures remain. See report and RECORD_INDEX.json. No new24, training or hardware. Source commit '+head+'\n')
  assert sync['remote_verified'],'SOURCE_REMOTE_HEAD_NOT_VERIFIED'
  gh(['release','create',TAG,'--target',head,'--title','Phase V1024 complete input route development','--notes-file',notes,'--latest=false'])
  assets=list((O/'cloud').iterdir())+[D/'RECORD_INDEX.json',D/'FINAL_SUMMARY.json',D/'SOURCE_SYNC_RESULT.json',REPORT];gh(['release','upload',TAG,*assets],120)
  back=O/'readback';back.mkdir(exist_ok=False)
  def provider(part):
   gh(['release','download',TAG,'--pattern',part['name'],'--dir',back]);return back/part['name'],True
  archive.verify(record,catalog,provider)
  final=dict(passed=True,all_remote_decompressed_member_sha_verified=True,source_commit=head,release_url='https://github.com/frank8763/phase-/releases/tag/'+TAG,models=0,raw_retained=False)
  dump(D/'REMOTE_VERIFIED.json',final)
  # Delete only paths in the verified archive; never follow a resource symlink.
  mapping={x['path']:x for x in catalog};deleted=[]
  for folder in [R/'runs/v858_nav2_verified/v1024',R/'runs/v1023_dense_input_route']:
   for p in list(archive.walk(folder)):
    if p.suffix=='.so':deleted.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,reason='regenerable_analytical_binary'));p.unlink();continue
    row=mapping[str(p.relative_to(R))];assert sha(p)==row['sha256'];deleted.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size));p.unlink()
   # Resource links are unlinked themselves; their targets are never accessed.
   for base,dirs,names in os.walk(folder,followlinks=False):
    for name in dirs+names:
     p=Path(base,name)
     if p.is_symlink():p.unlink()
  dump(D/'CLEANUP.json',dict(passed=True,deleted=deleted,bytes=sum(x['bytes']for x in deleted),remote_verified=True,models=0));gh(['release','upload',TAG,D/'REMOTE_VERIFIED.json',D/'CLEANUP.json'])
  shutil.rmtree(O/'cloud');shutil.rmtree(back)
 except BaseException as e:dump(D/'REMOTE_PENDING.json',dict(error=repr(e),raw_retained=True,no_automatic_retry=True,models=0))
 run(['git','add','--',str(D.relative_to(R))]);run(['git','commit','--only','-m','Record V1024 delivery receipts without second push','--',str(D.relative_to(R))])
 dump(O/'CLOSED.json',dict(science_closed=True,models_authorized=False,remote_verified=(D/'REMOTE_VERIFIED.json').exists(),summary=summary))
 print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
