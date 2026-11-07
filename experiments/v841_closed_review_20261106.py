"""Closed V841 outcome, whole-source archive/decompression and transport verification; zero models."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('CLOSED_REVIEW_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
import fcntl,gzip,hashlib,json,zipfile
from pathlib import Path
from datetime import datetime,timezone,timedelta
import numpy as np
R=Path(__file__).resolve().parents[1];out=R/'runs/v841_closed_review_20261106';out.mkdir(exist_ok=False);read=lambda p:json.loads(p.read_text());dump=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');digests={}
def sha(p):
 p=p.resolve()
 if p not in digests:
  h=hashlib.sha256()
  with p.open('rb')as f:
   for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
  digests[p]=h.hexdigest()
 return digests[p]
root=R/'runs/early_joint_90_20261106';stage=R/'runs/v841_early_joint';pair=stage/'main_slot01/paired';cell=pair/'geometry_memory';closed=read(root/'ROUND_WINDOW.json');assert closed['round_closed']and read(root/'COMPLETION.json')['status']=='STOPPED_SINGLE_SCENE_NOT_PASSED'
assert(R/'REVIEW_PENDING').read_bytes()==(root/'REVIEW_PENDING.before').read_bytes()
with(R/'runs/v648_static_unknown/execution.lock').open('rb')as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
freeze=read(R/'experiments/v841_early_joint/CANDIDATE_FREEZE.json');assert all(sha(R/n)==h for n,h in freeze['files'].items());archives=[];exclude=[];blob_cache={}
for label in ['rpccr_early_joint_v841_qualification_20261106','rpccr_early_joint_v841_20261106']:
 archive=R/'evidence'/label;inventory=json.load(gzip.open(archive/'RAW_INVENTORY.json.gz','rt'))
 for x in inventory:
  blob=archive/x['blob'];key=(sha(blob),x['encoding'])
  if key not in blob_cache:
   h=hashlib.sha256();size=0
   opener=blob.open if x['encoding']=='identity'else lambda mode:gzip.open(blob,mode)
   with opener('rb')as f:
    for b in iter(lambda:f.read(4*1024**2),b''):h.update(b);size+=len(b)
   blob_cache[key]=(size,h.hexdigest())
  assert blob_cache[key]==(x['bytes'],x['sha256'])and sha(R/x['path'])==x['sha256'],x['path']
 for x in read(archive/'MANIFEST.json'):assert(archive/x['path']).stat().st_size==x['bytes']and sha(archive/x['path'])==x['sha256']
 transport=R/'evidence'/(label+'_transport');large=read(transport/'TRANSPORT_MANIFEST.json')['entries']
 for x in large:
  h=hashlib.sha256();size=0
  for chunk in x['chunks']:
   p=R/chunk['path'];assert p.stat().st_size==chunk['bytes']and sha(p)==chunk['sha256']and chunk['bytes']<=32*1024**2
   with p.open('rb')as f:
    for b in iter(lambda:f.read(4*1024**2),b''):h.update(b);size+=len(b)
  assert size==x['bytes']and h.hexdigest()==x['sha256']==sha(R/x['original_blob']);exclude.append(x['original_blob'])
 archives.append(dict(archive=str(archive.relative_to(R)),sources=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),all_source_and_decompressed_sha_verified=True,large_blobs=len(large),chunks_reassembled_sha_verified=True))
ops=R/'evidence/rpccr_early_joint_90_ops_20261106';m=read(ops/'MANIFEST.json')
with zipfile.ZipFile(ops/'OPERATIONS_SNAPSHOT.zip')as z:
 for x in m['inventory']:
  b=z.read(x['path']);assert len(b)==x['bytes']and hashlib.sha256(b).hexdigest()==x['sha256']
ls=lambda p:[json.loads(s)for s in p.open()];events=ls(cell/'early_joint_decisions.jsonl');ad=ls(cell/'model_admission.jsonl');e=ls(cell/'v648_execution.jsonl');native=read(cell/'result.json');audit=read(stage/'FINAL_INDEPENDENT_AUDIT.json');chain=read(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json');original=R/'runs/v830_ranked_return_development/main_slot01/paired/geometry_memory';old_e=ls(original/'v648_execution.jsonl');old_ad=ls(original/'model_admission.jsonl');goal=np.array([4.,-2.]);joint=sum(len(p['detail']['candidates'])for x in events for p in x['probes']);selected=[next(p for p in x['probes']if p['rank']==x['selected_rank'])for x in events]
result=dict(status='CLOSED_REVIEW_VERIFIED_NOT_PASSED',checked_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),stopped_at=datetime.fromtimestamp(closed['started_unix']+closed['elapsed_s'],timezone(timedelta(hours=8))).isoformat(),direct_stop='single_navigation_original1200s_soft_wall_cap; global5400s_is_total_window_not_one_navigation_cap',global_elapsed_s=closed['elapsed_s'],single_navigation_elapsed_s=native['elapsed_s'],outcome=native['outcome'],main_attempts=1,complete_chain_successes=0,conditional_repeats_executed=0,new24_executed=0,public_steps=native['public_steps'],navigation_native=native['physics_steps'],private_native=native['prediction_steps'],replay_native=audit['replay_native'],post_stop_displacement_m=chain['details']['post_stop_actual_displacement_m'],goal_distance_m=native['goal_distance_m'],end_speed_m_s=float(np.linalg.norm(e[-1]['qvel_full'][:2])),end_is_not_actual_stationary_stop=True,physical_audits_passed=17,minimum_actual_clearance_m=native['minimum_dynamic_native_clearance_m'],obstacle_or_unknown_contacts=0,full_native_replay_error=read(pair/'NATIVE_REPLAY_AUDIT.json')['maximum_full_native_state_ctrl_error'],first_trigger=295,pre_trigger_native_exact=2360,joint_public_cycles=len(events),joint_probes=sum(len(x['probes'])for x in events),joint_complete_tails=joint,joint_admitted_every_cycle=all(x['selected_rank']is not None for x in events),selected_reference_tails=sum(p['summary']['recovery_kind']=='REFERENCE_FOLLOW_BRAKE'for p in selected),old_same389_goal_distance_m=float(np.linalg.norm(np.asarray(old_e[len(e)-1]['qpos_full'])[:2]-goal)),old_same389_private_native=old_ad[len(e)-1]['prediction_steps_total'],same_index_comparison_is_descriptive_different_post295_states=True,archives=archives,operation_snapshot_entries_verified=len(m['inventory']),frozen_source_files_verified=len(freeze['files']),review_original_bytes_restored=True,execution_lock_idle=True,new_models=0,new_integrations=0,network_calls=0,raw_deleted=False,not_proven_would_arrive_with_more_time=True)
dump(out/'CHECK_CLOSED.json',result);dump(out/'GIT_RAW_BLOBS_EXCLUDED.json',exclude)
report=R/'docs/RPCCR_EARLY_JOINT_V841_CLOSED_REVIEW_20261106.md'
report.write_text('# V841结束检查与直接原因\n\n结论：完整动态单场景未通过；资格组件通过不能替代导航。\n\n'+json.dumps(result,ensure_ascii=False,indent=2)+'\n\n单次导航仍采用原1200秒软上限；用户选定90分钟是资格、主、条件重复和各模型审核合计根窗口。达到单次上限即按预注册停止，不能用剩余时间延长原任务。389公开=31.12秒仿真，末仍有合法MODEL_SAFE_COMMAND、前向完整证书，末速约.132m/s；并非原库全拒、碰撞或已物理停稳。发现后位移.9688m不足1m、目标3.1535m未达.45m。\n\n第295步后94周期均联合找到完整合格尾，284首命令/6981完整尾；94次实际选择全部原FORWARD_BRAKE，沿参考新尾没有获选。同389公开旧私有2202472、新4463680，约2.03倍；两轨迹在295之后不同，只作固定步数描述，不当等价加速或统计优势。额外搜索每步开销增加而当前没有完整导航收益证据；不能据预算终止声称物理无解，也不能声称延长就能到达。\n\n下一步仅设计：先剖分并压低完整尾联合计算、检查当前选择目标为何持续偏向原前向尾；任何决策等价优化必须保存同输入/同选择/完整向量证据，若改变触发频率或评分则属于新候选，需另行冻结有界验证。当前轮不追加模型、不延长、不新池或训练，旧失败和所有冻结归档保持。\n')
# Correct operation-only pointers; archived original operation snapshots remain unchanged.
c=read(R/'CURRENT_EXPERIMENT.json');c.update(source_revision='V841_EARLY_JOINT_SINGLE_SCENE_BOUNDED_WALL_NOT_PASSED',decision_freeze='experiments/v841_early_joint/CANDIDATE_FREEZE.json',report=str(report.relative_to(R)));c['early_joint_90_20261106'].update(closed_review=str((out/'CHECK_CLOSED.json').relative_to(R)),closed=True,new_confirmation=0,no_more_models_or_integrations=True);dump(R/'CURRENT_EXPERIMENT.json',c)
l=read(root/'LEDGER.json');l.update(candidates_started=1,qualification_actual_native=336,qualification_repeat_native=336,qualification_old_replay_native=2360,qualification_private_native=38400,navigation_native=3112,navigation_private_native=4463680,navigation_replay_native=3112,main_attempts=1,main_successes=0,complete_repeats=0,new_confirmation=0,closed_review=str((out/'CHECK_CLOSED.json').relative_to(R)));dump(root/'LEDGER.json',l)
with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- V841闭批核查：单导航1200秒软预算终止389公开/3112原生、距目标3.153457m；发现后位移.968781m，17审核及全原生重放误差0/最低实际.305892278m/无障碍或未知接触，但全链未通过、条件重复/新24均0。295前2360原生精确，之后94周期284首命令/6981完整尾全部有合格证书，94次均选择原FORWARD_BRAKE，新沿参考尾0次获选；私有4463680对旧同389步2202472约2.03倍，非同状态性能结论。90分钟为根总窗，非单导航90分钟；本轮未延长重跑。两原归档全来源/解压SHA及所有大blob32MiB重组回读，原件保留，REVIEW_PENDING原字节恢复/锁空闲，操作计数与当前报告指针已零模型补正。详见docs/RPCCR_EARLY_JOINT_V841_CLOSED_REVIEW_20261106.md。\n')
print(json.dumps(dict(status=result['status'],archives=archives,goal_distance_m=result['goal_distance_m'],models=0,integrations=0)))
