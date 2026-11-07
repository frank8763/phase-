"""No model construction/integration: audit closed development and archive exact bytes."""
import gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/v793_complete_joint_navigation';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
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
 original_audits=all(item['audits'].get(s)==0 for s in ['audit_run.py','audit_forward_controller.py','audit_route_commitment.py','audit_projection_learning.py','audit_all_tail_geometry.py','audit_shadow_mode.py','audit_reentry.py','audit_complete_joint.py'])
 full=bool(r is not None and r.get('strict_safe_arrival',False)and original_audits and chain is not None and chain['status']=='PASS'and rr is not None and rr['maximum_full_native_state_ctrl_error']<=1e-8 and (item['role']!='SUCCESS_CONDITIONAL_REPEAT'or repeat is not None and repeat['passed']))
 records.append(dict(name=item['name'],task=item['task'],role=item['role'],run=item['run'],all_original_audits_passed=original_audits,full_chain_and_repeat_if_applicable_passed=full,result=r))
full=bool(source_ok and len(records)==6 and all(x['full_chain_and_repeat_if_applicable_passed']for x in records)and completion['status']=='THREE_ROUTE_MAIN_AND_REPEAT_PASSED')
result=dict(status='THREE_ROUTE_DEVELOPMENT_VERIFIED'if full else'GLOBAL_DYNAMIC_DEVELOPMENT_NOT_PASSED',development_passed=full,source_unchanged=source_ok,records=records,main_attempts=sum(x['role']=='MAIN_DEVELOPMENT'for x in records),repeat_attempts=sum(x['role']=='SUCCESS_CONDITIONAL_REPEAT'for x in records),planned_main=3,planned_repeat=3,new_confirmation_tasks=0,actual_navigation_native=actual,private_native=private if private_exact else None,replay_native=replay if replay_exact else None,private_account_exact=private_exact,replay_account_exact=replay_exact,new_integrations_finalizer=0,training_updates=0,stage_access=0,real_robot=0,declared_norm_speed_cap=.08,original_broader_class_passed=False)
dump(root/'FINAL_INDEPENDENT_AUDIT.json',result)
dest=repo/'evidence/rpccr_complete_joint_navigation_v793_20261104';assert not dest.exists(),'ARCHIVE_MUST_NOT_BE_OVERWRITTEN';dest.mkdir();(dest/'blobs').mkdir();inventory=[]
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
report=repo/'docs/RPCCR_COMPLETE_JOINT_V793_REPORT.md';text=['# RP-CCR V793 完整联合控制准入开发','',f"实际独立结论：**{result['status']}**。主任务尝试{result['main_attempts']}/计划3，完整重复尝试{result['repeat_attempts']}/计划3；新24确认0，未执行项不是失败样本。",'',f'实际导航原生{actual}、私有{result["private_native"]}、全状态控制重放{result["replay_native"]}。null为未知，不能当0。','']
for row in records:
 r=row['result'];text.append(f"- {row['name']} {row['task']['case_id']}："+(f"{r.get('outcome','INTERRUPTED')}；{r.get('public_steps')}公开/{r.get('physics_steps')}原生；首次发现{r.get('first_discovery_step')}；完整链及所需重复通过={row['full_chain_and_repeat_if_applicable_passed']}。"if r else'结果不完整，保留未知。'))
text+=['','唯一新增算法改动是普通控制准入不再截断于前三个，而按原得分顺序检查原有限去重首命令直至首个完整后备合格。保留V791参考分层和所有原时变风险、328完整后备及发现停车门；未增加动作或放宽阈值。V792的9个遗漏资格是局部证据，不等于本批必能到达。原19实体、传感、actor、网络、.08已声明先验和原物理阈值不改。三路线属于同一地图，更多全局规划次数本身不算动态全局成功。','','即使本开发通过也不等于新24确认或公平算法优势。若失败原证据保留，不重开、刷种子或降低门槛。训练/SAC/Stage/实机0。REVIEW_PENDING已恢复。',f"全证据{dest.relative_to(repo)}：{len(inventory)}来源逐来源与解压SHA回读通过，原始runs保留。"]
report.write_text('\n'.join(text)+'\n');dump(root/'FINALIZED.json',dict(status=result['status'],development_passed=full,archive=summary,report=str(report.relative_to(repo)),no_additional_simulations=True));print(json.dumps(dict(status=result['status'],archive=summary),indent=2))
