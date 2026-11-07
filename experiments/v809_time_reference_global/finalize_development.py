"""No model construction/integration: audit closed development and archive exact bytes."""
import gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/v809_time_reference_global';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
assert(repo/'REVIEW_PENDING').exists()and not(root/'FINALIZED.json').exists(),'EXISTING_FINALIZATION_MUST_ONLY_BE_VERIFIED'
freeze=read(own/'CANDIDATE_FREEZE.json');source_ok=all(sha(repo/p)==h for p,h in freeze['files'].items());assert source_ok
closed=read(root/'ROUND_WINDOW.json')if(root/'ROUND_WINDOW.json').exists()else read(root/'pre_navigation/ROUND_WINDOW.json');assert closed['round_closed']
completion=read(root/'development01/COMPLETION.json')if(root/'development01/COMPLETION.json').exists()else dict(status='ZERO_MODEL_CALIBRATION_NOT_PASSED',records=[])
records=[];actual=private=replay=0;private_exact=replay_exact=True
for item in completion['records']:
 pair=repo/item['run'];r=item.get('result')or item.get('interrupted');rr=read(pair/'NATIVE_REPLAY_AUDIT.json')if(pair/'NATIVE_REPLAY_AUDIT.json').exists()else None;chain=read(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json')if(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json').exists()else None
 actual+=0 if r is None else r.get('physics_steps',0);private_exact&=r is not None and'prediction_steps'in r;private+=0 if r is None else r.get('prediction_steps',0);replay_exact&=rr is not None;replay+=0 if rr is None else rr['replay_integration_steps']
 repeat=read(pair/'EXACT_REPEAT_AUDIT.json')if(pair/'EXACT_REPEAT_AUDIT.json').exists()else None
 original_audits=all(item['audits'].get(s)==0 for s in ['audit_run.py','audit_forward_controller.py','audit_route_commitment.py','audit_projection_learning.py','audit_all_tail_geometry.py','audit_shadow_mode.py','audit_reentry.py','audit_complete_joint.py','audit_nominal_layers.py','audit_reactive.py','audit_time_reference.py'])
 full=bool(r is not None and r.get('strict_safe_arrival',False)and original_audits and chain is not None and chain['status']=='PASS'and rr is not None and rr['maximum_full_native_state_ctrl_error']<=1e-8 and (item['role']!='SUCCESS_CONDITIONAL_REPEAT'or repeat is not None and repeat['passed']))
 records.append(dict(name=item['name'],task=item['task'],role=item['role'],run=item['run'],all_original_audits_passed=original_audits,full_chain_and_repeat_if_applicable_passed=full,result=r))
full=bool(source_ok and len(records)==6 and all(x['full_chain_and_repeat_if_applicable_passed']for x in records)and completion['status']=='THREE_TIME_REFERENCE_MAIN_AND_REPEAT_PASSED')
result=dict(status='THREE_TIME_REFERENCE_DEVELOPMENT_VERIFIED'if full else'REACTIVE_DYNAMIC_DEVELOPMENT_NOT_PASSED',development_passed=full,source_unchanged=source_ok,records=records,main_attempts=sum(x['role']=='MAIN_DEVELOPMENT'for x in records),repeat_attempts=sum(x['role']=='SUCCESS_CONDITIONAL_REPEAT'for x in records),planned_main=3,planned_repeat=3,new_confirmation_tasks=0,actual_navigation_native=actual,private_native=private if private_exact else None,replay_native=replay if replay_exact else None,private_account_exact=private_exact,replay_account_exact=replay_exact,new_integrations_finalizer=0,training_updates=0,stage_access=0,real_robot=0,declared_norm_speed_cap=.08,original_broader_class_passed=False)
dump(root/'FINAL_INDEPENDENT_AUDIT.json',result)
dest=repo/'evidence/rpccr_time_reference_global_v809_20261104';assert not dest.exists(),'ARCHIVE_MUST_NOT_BE_OVERWRITTEN';dest.mkdir();(dest/'blobs').mkdir();inventory=[]
for directory in [root,own]:
 for p in sorted(directory.rglob('*')):
  if not p.is_file()or p.suffix in['.lock','.pyc']or'__pycache__'in p.parts:continue
  raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();encoding='identity'if p.suffix=='.gz'else'gzip';blob=dest/'blobs'/(h+('.raw'if encoding=='identity'else'.gz'));data=raw if encoding=='identity'else gzip.compress(raw,mtime=0)
  if blob.exists():assert blob.read_bytes()==data
  else:blob.write_bytes(data)
  inventory.append(dict(path=str(p.relative_to(repo)),bytes=len(raw),sha256=h,blob=str(blob.relative_to(dest)),encoding=encoding))
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
for row in inventory:
 data=(dest/row['blob']).read_bytes();raw=data if row['encoding']=='identity'else gzip.decompress(data);assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']and sha(repo/row['path'])==row['sha256']
manifest=[dict(path=str(p.relative_to(dest)),sha256=sha(p),bytes=p.stat().st_size)for p in sorted(dest.rglob('*'))if p.is_file()];dump(dest/'MANIFEST.json',manifest)
for row in manifest:assert sha(dest/row['path'])==row['sha256']
summary=dict(raw_files=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),manifest_entries=len(manifest),all_source_and_decompressed_readback_verified=True,raw_deleted=False,archive=str(dest.relative_to(repo)))
report=repo/'docs/RPCCR_TIME_REFERENCE_GLOBAL_V809_REPORT.md';text=['# RP-CCR V809 雷达触发完整场地动态开发','',f"实际结论：**{result['status']}**。主尝试{result['main_attempts']}/计划3；成功条件完整重复{result['repeat_attempts']}/计划3，新确认0。",'', '障碍仍是原物理场景的小型actor，在线只接收原始有噪声测距。发现前跟随已知静态全局参考，证书仅覆盖静态/自体/控制；发现后原估计外集合、完整328动态合同、停车/重规划恢复。此处主动移除旧未见域的在线鲁棒约束，明确更弱的反应式课程，不能声称旧未知域保证保留。','', f"实际导航{actual}/私有{result['private_native']}/完整重放{result['replay_native']}原生；null是未知。"]
for row in records:
 r=row['result'];text.append(f"- {row['name']}："+(f"{r.get('outcome','INTERRUPTED')}；{r.get('public_steps')}公开/{r.get('physics_steps')}原生，首次发现{r.get('first_discovery_step')}；完整链及全部所需审核通过={row['full_chain_and_repeat_if_applicable_passed']}。"if r else'未完成/未知。'))
text+=['', '唯一科学新变化是V808资格已核验的时间标记参考，原执行控制安全合同不变。原V807失败不改写，本次不是新池确认。', '同WEST_EAST/原10010001/原相位、19静态体及原actor、测距/噪声/模型/控制库不改；软墙钟1200/硬1500，不是实时。全部实际净空.15/原预测.155/完整自体合法ctrl速率/无根改写/原生重放门保持；发现前静态合同并不提供隐藏actor保证。', '同原地图三路线已观察任务的开发和重复，不是新24验收或统计优势。与静态五回合、旧空白24/24各分账。原失败不覆盖，停止后不刷种子/新版本/第三导航；训练/Stage/实机0，REVIEW_PENDING恢复。',f"全证据{dest.relative_to(repo)}：{len(inventory)}来源/{summary['raw_bytes']}原始字节，来源与解压SHA回读通过；原始runs不删除。"]
report.write_text('\n'.join(text)+'\n');dump(root/'FINALIZED.json',dict(status=result['status'],development_passed=full,archive=summary,report=str(report.relative_to(repo)),no_additional_simulations=True));print(json.dumps(dict(status=result['status'],archive=summary),indent=2))
