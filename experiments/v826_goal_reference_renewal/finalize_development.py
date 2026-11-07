"""No model construction/integration: audit closed development and archive exact bytes."""
import gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/v826_goal_reference_renewal';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
assert(repo/'REVIEW_PENDING').exists()and not(root/'FINALIZED.json').exists(),'EXISTING_FINALIZATION_MUST_ONLY_BE_VERIFIED'
freeze=read(own/'CANDIDATE_FREEZE.json');source_ok=all(sha(repo/p)==h for p,h in freeze['files'].items());assert source_ok
closed=read(root/'ROUND_WINDOW.json')if(root/'ROUND_WINDOW.json').exists()else None;assert closed['round_closed']
completion=read(root/'development01/COMPLETION.json')if(root/'development01/COMPLETION.json').exists()else dict(status='ZERO_MODEL_CALIBRATION_NOT_PASSED',records=[])
records=[];actual=private=replay=0;private_exact=replay_exact=True
for item in completion['records']:
 pair=repo/item['run'];r=item.get('result')or item.get('interrupted');rr=read(pair/'NATIVE_REPLAY_AUDIT.json')if(pair/'NATIVE_REPLAY_AUDIT.json').exists()else None;chain=read(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json')if(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json').exists()else None
 actual+=0 if r is None else r.get('physics_steps',0);private_exact&=r is not None and'prediction_steps'in r;private+=0 if r is None else r.get('prediction_steps',0);replay_exact&=rr is not None;replay+=0 if rr is None else rr['replay_integration_steps']
 repeat=read(pair/'EXACT_REPEAT_AUDIT.json')if(pair/'EXACT_REPEAT_AUDIT.json').exists()else None
 original_audits=all(item['audits'].get(s)==0 for s in ['audit_run.py','audit_forward_controller.py','audit_route_commitment.py','audit_projection_learning.py','audit_all_tail_geometry.py','audit_shadow_mode.py','audit_reentry.py','audit_complete_joint.py','audit_nominal_layers.py','audit_reactive.py','audit_proposal_separation.py','audit_tracked_norm.py','audit_goal_renewal.py'])
 full=bool(r is not None and r.get('strict_safe_arrival',False)and original_audits and chain is not None and chain['status']=='PASS'and rr is not None and rr['maximum_full_native_state_ctrl_error']<=1e-8 and (item['role']!='SUCCESS_CONDITIONAL_REPEAT'or repeat is not None and repeat['passed']))
 records.append(dict(name=item['name'],task=item['task'],role=item['role'],run=item['run'],all_original_audits_passed=original_audits,full_chain_and_repeat_if_applicable_passed=full,result=r))
full=bool(source_ok and len(records)==2 and all(x['full_chain_and_repeat_if_applicable_passed']for x in records)and completion['status']=='ONE_GOAL_RENEWAL_MAIN_AND_REPEAT_PASSED')
result=dict(status='ONE_GOAL_RENEWAL_DEVELOPMENT_VERIFIED'if full else'GOAL_RENEWAL_DEVELOPMENT_NOT_PASSED',development_passed=full,source_unchanged=source_ok,records=records,main_attempts=sum(x['role']=='MAIN_DEVELOPMENT'for x in records),repeat_attempts=sum(x['role']=='SUCCESS_CONDITIONAL_REPEAT'for x in records),planned_main=1,planned_repeat=1,new_confirmation_tasks=0,actual_navigation_native=actual if all(x.get('result') is not None for x in records) else None,private_native=private if private_exact else None,replay_native=replay if replay_exact else None,private_account_exact=private_exact,replay_account_exact=replay_exact,new_integrations_finalizer=0,training_updates=0,stage_access=0,real_robot=0,declared_norm_speed_cap=.08,original_broader_class_passed=False)
dump(root/'FINAL_INDEPENDENT_AUDIT.json',result)

# Archive only after independent saved-evidence evaluation; no model API here.
import os,subprocess,sys
report=repo/'docs/RPCCR_GOAL_REFERENCE_RENEWAL_V826_REPORT.md'
text=['# RP-CCR V826：新观测触发完整目标参考更新','',f'实际结论：{result["status"]}。原南北任务主尝试{result["main_attempts"]}/计划1；成功条件完整重复{result["repeat_attempts"]}/计划1，新确认0。','',
 f'实际导航{result["actual_navigation_native"]}/私有{result["private_native"]}/完整重放{result["replay_native"]}原生；null表示未知，不填0。资格阶段另账4000旧重放/24656私有/656分支/656完整重复，不混入导航或独立任务分母。','',
 '唯一科学变化为：当当前参考仅SAFE_PROGRESS_PREFIX，出现实际新命中、原12步最小规划间隔已满足且当前地图的目标引导恢复有限时，尝试原全局规划链。原A*、控制库/评分/网络、完整328动态安全尾和所有原风险/控制门保持；几何参考不授权实际控制。','']
for row in records:
 r=row['result'];text.append(f'- {row["name"]}：'+(f'{r.get("outcome","INTERRUPTED")}，{r.get("public_steps")}公开/{r.get("physics_steps")}原生，距目标{r.get("goal_distance_m",r.get("final_goal_distance_m"))}；全部审核及完整链/重复通过={row["full_chain_and_repeat_if_applicable_passed"]}。'if r else'实际结果未完成/未知。'))
 p=repo/row['run']/'GOAL_REFERENCE_RENEWAL_AUDIT.json'
 if p.exists():
  renewal=read(p);text.append(f'  首新增触发{renewal["first_trigger_step"]}，更新参考类别{renewal["first_updated_plan_status"]}；此前282公开/2256原生和原V821完整前缀最大误差{renewal["pre_trigger_native_max_error"]}。')
text += ['', '本轮只有同一已观察原南北任务的开发及条件重复；即使通过也不是三路线全表或新24验收，不把V820旧西东开发、V821失败、静态五回合或旧空白24/24混合成当前验收率。',
 '', '原V824零模型外层step错误和V825同原截止的唯一元数据入口接续均保留。V823最初root姿态查询对应run_static.pose实际入口；float32传感姿态核验是附加对照。V826冻结前的栅格引导None负例异常原样保留后补齐None处理，全部反馈和负例通过才冻结；实际模型阶段不允许再科学或接口修补。',
 '', '原19静态实体、小actor/原连续相位/欧氏速.08、3m原测距和5%漏检保持；actor真值只物理传感离线评价。发现前静态反应式合同仍较弱、公开3m起步排除先验；原更宽每轴.12类、任意遮挡、多actor、实时性、递归安全或RAS全面优势未建立。训练/SAC/Stage/实机0，current/runtime和冻结网络不改。',
 '', '根17:00:46.976+0800模型积分截止不重置；完成或失败后停止本轮，不自动三路线、新池、地图、算法比较或训练。原始证据保留、全来源/解压SHA回读及大blob无损传输分块后才写FINALIZED。']
report.write_text('\n'.join(text)+'\n')
dest=repo/'evidence/rpccr_goal_reference_renewal_v826_20261105';assert not dest.exists(),'ARCHIVE_MUST_NOT_BE_OVERWRITTEN';dest.mkdir();(dest/'blobs').mkdir()
previous=repo/'evidence/rpccr_goal_renewal_native_qualification_20261105'
old_blobs={x['path']:x for x in read(previous/'MANIFEST.json')if x['path'].startswith('blobs/')}
files={repo/p for p in freeze['files']};files.add(own/'CANDIDATE_FREEZE.json');files.add(report)
for directory in [root,own]:
 files.update(p for p in directory.rglob('*')if p.is_file()and p.suffix not in['.lock','.pyc']and'__pycache__'not in p.parts and p.name not in['finalize.console','transport.console'])
inventory=[]
for p in sorted(files):
 raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();encoding='identity'if p.suffix=='.gz'else'gzip';relative='blobs/'+h+('.raw'if encoding=='identity'else'.gz');blob=dest/relative
 if not blob.exists():
  if relative in old_blobs:os.link(previous/relative,blob)
  else:blob.write_bytes(raw if encoding=='identity'else gzip.compress(raw,mtime=0))
 inventory.append(dict(path=str(p.relative_to(repo)),bytes=len(raw),sha256=h,blob=relative,encoding=encoding))
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0));verified={}
for row in inventory:
 if row['blob']not in verified:
  data=(dest/row['blob']).read_bytes();raw=data if row['encoding']=='identity'else gzip.decompress(data);verified[row['blob']]=(len(raw),hashlib.sha256(raw).hexdigest())
 assert verified[row['blob']]==(row['bytes'],row['sha256'])and sha(repo/row['path'])==row['sha256']
manifest=[dict(path=str(p.relative_to(dest)),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(dest.rglob('*'))if p.is_file()];dump(dest/'MANIFEST.json',manifest)
assert all(sha(dest/x['path'])==x['sha256']for x in manifest)
transport=None
if any(x['bytes']>90*1024**2 for x in manifest):
 transport=str(dest.relative_to(repo))+'_transport'
 process=subprocess.run([sys.executable,'-B',str(repo/'experiments/global_day_20261104_analysis/transport_archive.py'),str(dest),str(repo/transport)],cwd=repo,capture_output=True,text=True,timeout=605)
 (root/'transport.console').write_text(process.stdout+process.stderr);assert process.returncode==0,'LOSSLESS_TRANSPORT_FAILED'
summary=dict(raw_files=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),all_source_and_decompressed_sha_verified=True,raw_deleted=False,archive=str(dest.relative_to(repo)),transport=transport)
dump(root/'FINALIZED.json',dict(status=result['status'],development_passed=full,archive=summary,report=str(report.relative_to(repo)),new_models_finalizer=0,new_integrations_finalizer=0,no_additional_simulations=True))
daypath=repo/'runs/goal_renewal_20261105/LEDGER.json';day=read(daypath);day.update(status='CLOSED_V826_DEVELOPMENT_PASSED'if full else'CLOSED_V826_DEVELOPMENT_NOT_PASSED',closed=True,active_simulation=False,navigation_master_pid=None,development_passed=full,new_navigation_attempts=result['main_attempts'],new_complete_repeat_attempts=result['repeat_attempts'],navigation_native=result['actual_navigation_native'],navigation_private_native=result['private_native'],navigation_replay_native=result['replay_native'],new_confirmation=0,no_more_physics=True,report=str(report.relative_to(repo)));dump(daypath,day)
p=repo/'CURRENT_EXPERIMENT.json';current=read(p);current.update(status='REVIEW_PENDING',state='REVIEW_PENDING',current_experiment='V826_CLOSED_GOAL_REFERENCE_RENEWAL',active_entrypoint=None,execution_window_closed=True,report=str(report.relative_to(repo)),finite_full_field_dynamic_acceptance_passed=False);current['goal_renewal_20261105'].update(closed=True,development_passed=full,report=str(report.relative_to(repo)),no_more_physics=True);dump(p,current)
print(json.dumps(read(root/'FINALIZED.json')),flush=True)
