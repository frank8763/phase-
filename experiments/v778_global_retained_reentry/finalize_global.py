"""Zero-integration independent closure and complete raw archive readback."""
import datetime,gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/v778_global_retained_reentry';dest=repo/'evidence/rpccr_global_reentry_v778_20261103';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
assert read(root/'ROUND_WINDOW.json')['round_closed'];assert (repo/'REVIEW_PENDING').exists();assert not (root/'FINALIZED.json').exists(),'EXISTING_CLOSURE_MUST_ONLY_BE_VERIFIED'
freeze=read(own/'CANDIDATE_FREEZE.json');source_ok=all(sha(repo/n)==h for n,h in freeze['files'].items());completed=read(root/'development01/COMPLETION.json');records=[];actual=0;private=0;replay=0;private_known=True;replay_known=True
required={'INDEPENDENT_CANONICAL_AUDIT.json':'ALL_PHYSICAL_STATE_COMMAND_CHECKS_PASS','EARLY_SCAN_AUDIT.json':'EARLY_SCAN_CONTRACT_AND_BANK_PASS','SAVED_TAIL_GEOMETRY_AUDIT.json':'ALL_SAVED_TAIL_GEOMETRY_DIRECTION_SCHEDULE_PASS','REENTRY_INDEPENDENT_AUDIT.json':'GLOBAL_REENTRY_SAVED_EVIDENCE_VERIFIED'}
for item in completed['records']:
 pair=repo/item['run'];cell=pair/'geometry_memory';r=read(cell/'result.json')if(cell/'result.json').exists()else read(cell/'interrupted.json')if(cell/'interrupted.json').exists()else None;audits={name:read(pair/name)if(pair/name).exists()else None for name in required}
 statuses={name:value is not None and value.get('status')==expected and all(value.get('checks',{}).values())for(name,expected),value in zip(required.items(),audits.values())}
 for script,exitcode in item['audits'].items():statuses[script]=exitcode==0
 rr=read(pair/'NATIVE_REPLAY_AUDIT.json')if(pair/'NATIVE_REPLAY_AUDIT.json').exists()else None
 chain=read(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json')if(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json').exists()else None
 actual+=0 if r is None else r['physics_steps'];private_known&=r is not None and 'prediction_steps'in r;private+=0 if r is None else r.get('prediction_steps',0);replay_known&=rr is not None;replay+=0 if rr is None else rr['replay_integration_steps']
 records.append(dict(name=item['name'],result=r,audit_checks=statuses,all_available_original_and_new_audits_passed=bool(statuses and all(statuses.values())and len(item['audits'])==7),full_native_replay_passed=rr is not None and rr['status']=='MATCHED_RECORDED_PUBLIC_STATES'and rr['maximum_full_native_state_ctrl_error']<=1e-8,discovery_chain=chain,full_functional_passed=r is not None and r.get('strict_safe_arrival',False)and chain is not None and chain['status']=='PASS'))
full=bool(source_ok and len(records)==2 and all(x['all_available_original_and_new_audits_passed']and x['full_native_replay_passed']and x['full_functional_passed']for x in records)and read(root/'repeat01/paired/EXACT_REPEAT_AUDIT.json')['passed'])if len(records)==2 else False
out=dict(status='GLOBAL_SINGLE_TASK_MAIN_AND_REPEAT_VERIFIED'if full else'GLOBAL_DYNAMIC_NOT_PASSED',source_unchanged=source_ok,global_single_task_passed=full,records=records,original_task_seed=10010001,main_tasks_attempted=sum(x['name']=='main01'for x in records),repeats_attempted=sum(x['name']=='repeat01'for x in records),conditional_repeat_unexecuted=not any(x['name']=='repeat01'for x in records),new_confirmation_tasks=0,actual_navigation_native=actual,private_native=private if private_known else None,replay_native=replay if replay_known else None,private_account_exact=private_known,replay_account_exact=replay_known,training_updates=0,stage_access=0,real_robot=0,conditional_nonpenetrating_map_motion_class=True,new_integrations_this_finalizer=0)
dump(root/'FINAL_INDEPENDENT_AUDIT.json',out)
# Archive all raw outputs plus source. Preserve originals. Exact source/decompression readback.
assert not dest.exists(),'ARCHIVE_MUST_NOT_BE_OVERWRITTEN';dest.mkdir();(dest/'blobs').mkdir();inventory=[]
for directory in [root,own]:
 for p in sorted(directory.rglob('*')):
  if not p.is_file()or p.suffix in['.lock','.pyc']or'__pycache__'in p.parts:continue
  raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();encoding='identity'if p.suffix=='.gz'else'gzip';blob=dest/'blobs'/(h+('.raw'if encoding=='identity'else'.gz'));data=raw if encoding=='identity'else gzip.compress(raw,mtime=0)
  if blob.exists():assert blob.read_bytes()==data
  else:blob.write_bytes(data)
  inventory.append(dict(path=str(p.relative_to(repo)),bytes=len(raw),sha256=h,blob=str(blob.relative_to(dest)),encoding=encoding))
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
for x in inventory:
 data=(dest/x['blob']).read_bytes();raw=data if x['encoding']=='identity'else gzip.decompress(data);assert len(raw)==x['bytes']and hashlib.sha256(raw).hexdigest()==x['sha256']and sha(repo/x['path'])==x['sha256']
manifest=[dict(path=str(p.relative_to(dest)),sha256=sha(p),bytes=p.stat().st_size)for p in sorted(dest.rglob('*'))if p.is_file()];dump(dest/'MANIFEST.json',manifest)
for x in manifest:assert sha(dest/x['path'])==x['sha256']
summary=dict(raw_files=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),manifest_entries=len(manifest),all_source_and_decompressed_readback_verified=True,raw_deleted=False,archive=str(dest.relative_to(repo)))
report=repo/'docs/RPCCR_GLOBAL_REENTRY_V778_REPORT.md';text=['# RP-CCR完整场地动态 V778 实际结果','',f"独立终审：**{out['status']}**。本轮按用户要求回到原完整场地从起点至目标的导航；不是从保存中间状态出发的局部组件。",'',f"原任务10010001，主任务尝试{out['main_tasks_attempted']}，条件重复尝试{out['repeats_attempted']}；新24确认0。导航原生{actual}、私有{out['private_native']}、控制重放{out['replay_native']}；未知计数以null保留。",'']
for x in records:
 r=x['result'];text += [f"- {x['name']}："+(f"{r['outcome']}，{r['public_steps']}公开/{r['physics_steps']}原生，目标距离{r.get('goal_distance_m')}m；发现{r.get('first_discovery_step')}，再接入{r.get('retained_reentry_successes')}次。"if r else'没有完整结果，未验证。'),f"  原及新审核完备通过={x['all_available_original_and_new_audits_passed']}；完整功能链通过={x['full_functional_passed']}。"]
text += ['', '方法只将MAP_HISTORY条件可达域和保留尾因果再接入接到原全局控制流程。新条件明确要求未知actor不穿透已知实体；不代表原任意运动类无条件保证。原地图19实体、小actor尺寸/运动、传感噪声、.15实际/.155预测、完整328时域和状态重放门未放宽。','', '未通过时必须继续解决当前真实失败，不能宣称完整场地动态验收已通过。单任务开发即使通过也不等于三路线24项新确认，更不能代替公平外部算法对比、复杂地图/多actor/遮挡泛化或RAS录用判断。','',f"全证据：`{dest.relative_to(repo)}`，{len(inventory)}原文件，全部来源及解压哈希回读通过。原始runs保留。训练/SAC/Stage/实机0，旧失败/截止永久保留，REVIEW_PENDING恢复。"]
report.write_text('\n'.join(text)+'\n');dump(root/'FINALIZED.json',dict(status=out['status'],archive=summary,report=str(report.relative_to(repo)),no_additional_simulations=True))
print(json.dumps(dict(status=out['status'],archive=summary),indent=2))
