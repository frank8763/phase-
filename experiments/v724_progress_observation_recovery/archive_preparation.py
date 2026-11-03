"""Zero-integration audit and archive of the completed fixed-state diagnosis."""
import gzip,hashlib,json
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2]
read=lambda p:json.loads(p.read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
root=repo/'runs/v723_recovery_observability_probe';result=read(root/'RESULT.json');records=read(root/'CANDIDATES.json')
assert result['status']=='FIXED_TWO_STATE_RECOVERY_DIAGNOSIS_COMPLETE'
assert result['records']==records and len(records)==52
details=[]
for step in [92,133]:
 rows=[x for x in records if x['checkpoint']==step]
 assert [x['index']for x in rows]==list(range(26))
 for row in rows:
  data=np.load(root/('CHECKPOINT_%03d_CANDIDATE_%02d.npz'%(step,row['index'])))
  assert all(np.isfinite(data[k]).all()for k in data.files)
  assert data['qpos'].shape==(328,20)and data['qvel'].shape==(328,19)and data['controls'].shape==(328,4)and data['poses'].shape==(328,3)
  assert np.max(abs(data['controls'][:,:2]))<=.52+1e-12 and np.max(abs(data['controls'][:,2:]))<=12+1e-12
  assert np.all(abs(np.diff(data['controls'],axis=0))<=np.array([.1,.1,.7,.7])+1e-12)
  if row['admissible']:
   assert row['validation_steps']==328 and row['full_native_state_error']<=1e-8 and row['minimum_causal_clearance_m']>=.155 and row['self_domain_margin_m']>=.002 and row['terminal_speed_m_s']<=.025
  else:assert row['validation_steps']==0 and row['reason']is not None
 details.append(dict(checkpoint=step,checked_candidates=len(rows),safe_reverse=sum(x['admissible']and x['kind']=='REVERSE_BRAKE'for x in rows),safe_forward=sum(x['admissible']and x['kind']=='FORWARD_BRAKE'for x in rows)))
assert result['original_replay_steps']==1064 and result['private_prediction_integrations']==52*320+16
assert result['candidate_scene_validation_integrations']==sum(x['validation_steps']for x in records)==4592
assert result['bad_contacts']==0 and result['minimum_actual_native_clearance_m']>=.15 and result['original_replay_full_state_error']==0
freeze=read(repo/'experiments/v723_recovery_observability_probe/SOURCE_FREEZE.json')
assert all(sha((repo/n).read_bytes())==h for n,h in freeze['files'].items())
out=dict(status='FIXED_DIAGNOSIS_SAVED_EVIDENCE_AND_ACCOUNTS_VERIFIED',details=details,original_replay_steps=1064,private_prediction_integrations=16656,scene_validation_integrations=4592,new_navigation_samples=0,new_integrations_in_audit=0,scope='Checks saved arrays, commands, immutable executed source, validation records and counts; does not perform a second independent native integration.')
cal=repo/'runs/v724_recovery_selection_calibration';(cal/'DIAGNOSTIC_EVIDENCE_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n')
(repo/'docs/RPCCR_RECOVERY_DIAGNOSIS_V723_REPORT.md').write_text('''# RP-CCR两次退让前诊断与修订依据

原V721第92/133步各固定26条完整328原生尾，共52候选。合格反向尾分别12/2条，合格前向均0；不能据此强行前进或声称全局无解。全部14合格尾在原场景副本逐原生验证，完整状态误差0、最低实际净空0.269484960m、障碍/穿透/未知接触0。

原选择的目标进展约−0.488/−0.220m；新V724规则在相同合格反向集合可选−0.205/−0.199m，几何潜在可见格也较高。潜力不保证未来真实观测，更不作为安全准入证据。V724只检验这种恢复选择能否改善同一旧任务，尚无到达结论。

原重放1064、私有预测16656、合格尾场景验证4592，全部准确；新导航0、训练0。独立零积分核验52份完整状态/控制数组、合法命令、原执行冻结源码和完整账目；不是第二次独立原生积分。原V721失败及所有旧窗口不变。

V724启动前校准原92/133两状态的进展、潜力和重复计算一致，选择原候选18/23。第一校准入口因语法错误未执行，第二启动因误写解释器路径未执行，第三零积分校准通过；三个日志全保留，新增初始化/积分均0。未据此修改原安全、任务或物理结果。

证据：evidence/rpccr_recovery_diagnosis_v723_20261103；原始runs保留。完整场地动态验收和公平算法对比尚未通过或执行。
''')
dest=repo/'evidence/rpccr_recovery_diagnosis_v723_20261103';dest.mkdir(exist_ok=False);(dest/'blobs').mkdir();inventory=[]
paths=[p for p in root.rglob('*')if p.is_file()and p.suffix!='.lock']+[p for p in cal.rglob('*')if p.is_file()]+list((repo/'runs').glob('v724_selection_calibration*.console'))
for p in sorted(paths):
 raw=p.read_bytes();h=sha(raw);blob='blobs/'+h+'.gz';target=dest/blob
 if target.exists():assert gzip.decompress(target.read_bytes())==raw
 else:target.write_bytes(gzip.compress(raw,mtime=0))
 inventory.append(dict(path=str(p.relative_to(repo)),bytes=len(raw),sha256=h,blob=blob,stored_encoding='gzip'))
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress((json.dumps(inventory,indent=2)+'\n').encode(),mtime=0))
(dest/'README.md').write_text('# V723固定诊断及V724零积分校准\n\n保留全部候选、原验证/失败记录、校准日志及独立账目。无新增导航样本，归档完整不表示到达或动态验收通过。\n')
manifest=[dict(path=str(p.relative_to(dest)),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in sorted(dest.rglob('*'))if p.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in inventory:
 raw=gzip.decompress((dest/row['blob']).read_bytes());assert len(raw)==row['bytes']and sha(raw)==row['sha256']
for row in manifest:assert sha((dest/row['path']).read_bytes())==row['sha256']
print(json.dumps(dict(status='ALL_DIAGNOSTIC_AND_CALIBRATION_BYTES_READBACK_VERIFIED',raw_files=len(inventory),manifest_files=len(manifest),raw_deleted=False)))
