"""Zero-model final audit and immutable raw evidence archive for five static rounds."""
import json,gzip,hashlib
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/v804_no_dynamic_static_contact';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();dump=lambda p,v:p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
assert(repo/'REVIEW_PENDING').exists()and read(root/'ROUND_WINDOW.json')['round_closed']and not(root/'FINALIZED.json').exists();freeze=read(own/'CANDIDATE_FREEZE.json');assert all(sha(repo/p)==h for p,h in freeze['files'].items())
c=read(root/'five01/COMPLETION.json');rows=[];nav=private=replay=0;exact=True
for x in c['records']:
 pair=repo/x['run'];r=x.get('result')or x.get('interrupted');audit=read(pair/'STATIC_RUN_AUDIT.json')if(pair/'STATIC_RUN_AUDIT.json').exists()else None;rp=read(pair/'NATIVE_REPLAY_AUDIT.json')if(pair/'NATIVE_REPLAY_AUDIT.json').exists()else None
 nav+=0 if r is None else r.get('physics_steps',0);private+=0 if r is None else r.get('prediction_steps',0);replay+=0 if rp is None else rp['replay_integration_steps'];exact&=r is not None and x.get('result')is not None and rp is not None
 full=bool(audit is not None and audit['status']=='PASS'and audit['strict_static_arrival']and len(x['audits'])==8 and all(v==0 for v in x['audits'].values())and rp['maximum_full_native_state_ctrl_error']<=1e-8)
 rows.append(dict(name=x['name'],seed=x['task']['seed'],outcome=None if r is None else r.get('outcome'),strict_static_success=full,metrics=None if audit is None else audit['metrics'],audit=x['audits']))
complete=bool(len(rows)==5 and c['status']=='FIVE_STATIC_DIAGNOSTIC_ROUNDS_COMPLETE'and all(len(x['audit'])==8 and all(v==0 for v in x['audit'].values())for x in rows));passed=sum(x['strict_static_success']for x in rows);result=dict(status='FIVE_STATIC_ROUNDS_AUDITED'if complete else'STATIC_FIVE_DIAGNOSTIC_INCOMPLETE',completed=complete,successes=passed,planned=5,executed=len(rows),unexecuted=5-len(rows),success_rate=passed/5 if complete else None,rows=rows,navigation_native=nav,private_native=private if exact else None,replay_native=replay if exact else None,accounts_exact=exact,source_unchanged=True,scope='one known static map, one route, five sensor-noise seeds; not dynamic or unknown acceptance or broad generalization',new_models_finalizer=0,new_integrations_finalizer=0,training_updates=0,stage_access=0,real_robot=0)
dump(root/'FINAL_INDEPENDENT_AUDIT.json',result)
dest=repo/'evidence/rpccr_no_dynamic_five_v803_20261104';assert not dest.exists();dest.mkdir();(dest/'blobs').mkdir();inventory=[]
for directory in [own,root]:
 for p in sorted(directory.rglob('*')):
  if not p.is_file()or'__pycache__'in p.parts or p.suffix=='.pyc':continue
  raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();encoding='identity'if p.suffix=='.gz'else'gzip';blob=dest/'blobs'/(h+('.raw'if encoding=='identity'else'.gz'));data=raw if encoding=='identity'else gzip.compress(raw,mtime=0)
  if blob.exists():assert blob.read_bytes()==data
  else:blob.write_bytes(data)
  inventory.append(dict(path=str(p.relative_to(repo)),bytes=len(raw),sha256=h,blob=str(blob.relative_to(dest)),encoding=encoding))
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
for row in inventory:
 data=(dest/row['blob']).read_bytes();raw=data if row['encoding']=='identity'else gzip.decompress(data);assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']==sha(repo/row['path'])
manifest=[dict(path=str(p.relative_to(dest)),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(dest.rglob('*'))if p.is_file()];dump(dest/'MANIFEST.json',manifest)
summary=dict(raw_files=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),manifest_entries=len(manifest),source_and_decompressed_SHA_readback=True,raw_deleted=False,archive=str(dest.relative_to(repo)))
text=['# V803 无动态完整场地五回合路径跟随对照','',f"实际状态：{result['status']}。严格安全到达 {passed}/{len(rows)} 已执行；计划5，未执行{5-len(rows)}。"+('完整五回合率 '+str(passed/5*100)+'%。'if complete else'未完成全分母，不报告五回合成功率。'),'', '同19静态实体/同WEST_EAST起终点/五噪声种子，动态actor及未知动态风险层均移除；原A*与控制器、完整静态8+320尾和全部静态物理门保持。不是动态验收或五地图泛化；到达.45不等于停稳。','', '|回合|种子|结果|严格到达|剩余目标m|最大原生横向误差m|墙钟s|','|---|---|---|---|---|---|---|']
for x in rows:
 m=x['metrics']or{};text.append(f"|{x['name']}|{x['seed']}|{x['outcome']}|{x['strict_static_success']}|{m.get('goal_remaining_m')}|{m.get('max_native_contour_m')}|{m.get('wall_s')}|")
text+=['',f'导航{nav}/私有{result["private_native"]}/完整重放{result["replay_native"]}原生；unknown/null不得当0。',f'原始归档{len(inventory)}来源/{summary["raw_bytes"]}字节，全部来源和解压SHA回读通过。原始runs保留。','REVIEW_PENDING恢复，五回合范围结束，不自动新动态/新算法或训练。']
report=repo/'docs/RPCCR_NO_DYNAMIC_FIVE_V803_REPORT.md';report.write_text('\n'.join(text)+'\n');dump(root/'FINALIZED.json',dict(status=result['status'],successes=passed,complete_five=complete,archive=summary,report=str(report.relative_to(repo)),no_further_navigation=True));print(json.dumps(dict(status=result['status'],successes=passed,archive=summary)))
