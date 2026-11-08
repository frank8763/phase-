"""Publish post-cleanup small records without another source push or any model execution."""
import base64,hashlib,json,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];REC=R/'records/nav2_v864_20261107';GH=R/'tools/phase_storage_20261107/vendor/gh';TAG='phase-nav2-v864-20261107';RELEASE_ID=437972602
def read(p):return json.loads(p.read_text())
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def verify_upload(path):
 subprocess.run([str(GH),'release','upload',TAG,str(path),'--repo','frank8763/phase-'],cwd=R,check=True,timeout=60)
 raw=subprocess.run([str(GH),'api',f'repos/frank8763/phase-/releases/{RELEASE_ID}/assets?per_page=100&phase_read={time.time_ns()}'],capture_output=True,text=True,check=True,timeout=20).stdout
 asset=next(x for x in json.loads(raw)if x['name']==path.name);h=hashlib.sha256(path.read_bytes()).hexdigest();assert asset['digest']=='sha256:'+h and asset['size']==path.stat().st_size
 content=subprocess.run([str(GH),'release','download',TAG,'--repo','frank8763/phase-','--pattern',path.name,'--output','-'],cwd=R,capture_output=True,check=True,timeout=60).stdout;assert hashlib.sha256(content).hexdigest()==h
 return dict(passed=True,url=asset['browser_download_url'],sha256=h,bytes=len(content),server_digest_matched=True,download_sha_verified=True,at=time.time())
def main():
 assert read(REC/'CLEANUP_RESULT.json')['passed']and read(REC/'PUBLIC_RESTORE_QUALIFICATION.json')['passed'];sync=read(REC/'SOURCE_SYNC_RESULT.json');assert sync['remote_head_verified']
 manifest=verify_upload(REC/'CLEANUP_FILES.jsonl.gz');dump(REC/'CLEANUP_MANIFEST_REMOTE_VERIFIED.json',manifest)
 final=dict(status='CLOSED_FAILED_STATIC_REGRESSION_ARCHIVED_AND_TEMP_CLEANED',functional_passed=False,v864_attempted_navigation=1,v864_unexecuted_navigation=4,actual_native=3845,replay_native=3845,mujoco_private_native=0,complete_navigation_repeats=0,old_v863_we_pass_preserved=True,dynamic_navigation=0,new24=0,training=0,real_robot=0,v865_new_configuration_qualified=False,v865_models_authorized=False,root_model_deadline_expired=True,no_new_window_created=True,source_commit=sync['source_commit'],source_remote_head_verified=True,public_release='https://github.com/frank8763/phase-/releases/tag/'+TAG,public_all175_members_restore_verified=True,cleanup_bytes=read(REC/'CLEANUP_RESULT.json')['total_bytes'],review_pending_original_restored=True,execution_lock_idle=True,no_automatic_additional_models=True,stop_reason='First NS RPP collision rejection; four dependent runs stopped. Original22:33:58 model deadline expired; V865 remains config-only preparation.',at=time.time());dump(REC/'FINALIZED.json',final)
 p=R/'CURRENT_EXPERIMENT.json';d=read(p);d['v864_rpp_static_regression'].update(storage_status='PUBLIC_RELEASE_VERIFIED_RESTORED_AND_TEMP_CLEANED',release_url=final['public_release'],finalized='records/nav2_v864_20261107/FINALIZED.json');dump(p,d)
 p=R/'RESEARCH_STATUS.md';p.write_text(p.read_text()+'\n\n- V864失败批与V865未完成准备的必要175来源归档约8.05MB附件，公开GitHub Release及源039de44a9faa99946c8dfdcd590d8436688dcecd已验证；全部分块/解压/下载SHA和实际175成员恢复通过，按6350文件清单清理217039337字节临时运行库/原始记录/重复缓存。结论仍NS失败/后4未执行、V865新配置未资格，无新增模型窗口。收尾元数据另存同Release POST_CLOSURE_RECEIPT，原guard恢复/锁空闲，无第二源码push。\n')
 post=dict(format_version=1,kind='POST_CLOSURE_ZERO_MODEL_RECEIPT',finalized=final,small_records={},closure_sources={},current_experiment_snapshot=d,research_status_append='V864 closure: public175members restored;217039337 bytes removed;failed static remains;no new model window.',no_second_source_push=True)
 for f in sorted(REC.rglob('*')):
  if not f.is_file()or f.name.startswith('POST_CLOSURE_')or f.name=='CLEANUP_FILES.jsonl.gz':continue
  data=f.read_bytes();entry=dict(sha256=hashlib.sha256(data).hexdigest())
  try:entry['text']=data.decode('utf-8')
  except UnicodeDecodeError:entry['source_commit_reference']=sync['source_commit']
  post['small_records'][str(f.relative_to(R))]=entry
 for f in sorted((R/'experiments/v864_closure').glob('*.py')):
  data=f.read_bytes();post['closure_sources'][str(f.relative_to(R))]=dict(sha256=hashlib.sha256(data).hexdigest(),text=data.decode())
 receipt=REC/'POST_CLOSURE_RECEIPT.json';assert not receipt.exists();dump(receipt,post);verification=verify_upload(receipt);verification.update(includes_post_cleanup_records_and_new_closure_scripts=True,source_pushes_this_round=1);dump(REC/'POST_CLOSURE_VERIFIED.json',verification);print(json.dumps(verification),flush=True)
if __name__=='__main__':main()
