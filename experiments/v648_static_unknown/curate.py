"""Offline curation: preserve complete trial accounting and selected raw evidence."""
import argparse,gzip,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('runs');p.add_argument('destination');p.add_argument('--selected',nargs='+',required=True);a=p.parse_args();root=Path(a.runs);dest=Path(a.destination);dest.mkdir(parents=True,exist_ok=False)
trials=[];blobs=dest/'source_blobs';blobs.mkdir()
def sha(b):return hashlib.sha256(b).hexdigest()
for run in sorted(x for x in root.iterdir()if x.is_dir()):
 completion=next(iter(run.rglob('completion.json')),None);protocol=next(iter(run.rglob('STATIC_PROTOCOL.json')),None)
 record={'run':run.name,'completion':None if completion is None else json.loads(completion.read_text()),'protocol':None if protocol is None else json.loads(protocol.read_text()),'source_hashes':{}}
 metadata=run/'source_snapshot'/'SHA256.json'
 record['source_snapshot_metadata']=json.loads(metadata.read_text())if metadata.exists()else None
 record['source_capture_scope']='See original capture metadata; absence of a source snapshot means exact pre-run source is unavailable'
 captures=list((run/'source_snapshot').glob('*.py'))+list(run.glob('executed_runner.py'))
 for source in sorted(captures):
  b=source.read_bytes();h=sha(b);record['source_hashes'][source.name]=h
  target=blobs/(h+'.py')
  if not target.exists():target.write_bytes(b)
 for name in ['hard_floor_rejection.json','response.json','scene_geometry.json','sensor_geometry_sync.json','v648_nonphysical_mutation.json','probe.json','connectivity.json','point_map_connectivity.json','rejected_control.json']:
  for f in sorted(run.rglob(name)):
   diagnostic=json.loads(f.read_text())
   rel=str(f.relative_to(run))
   if len(f.read_bytes())>100000:
    target=dest/'diagnostics'/(run.name+'__'+f.name+'.gz');target.parent.mkdir(exist_ok=True)
    with gzip.open(target,'wb')as stream:stream.write(f.read_bytes())
    record.setdefault('diagnostics',{})[rel]={'compressed_file':str(target.relative_to(dest)),'sha256_uncompressed':sha(f.read_bytes()),'elapsed_s':diagnostic.get('elapsed_s'),'scope':diagnostic.get('scope')}
   else:record.setdefault('diagnostics',{})[rel]=diagnostic
 if completion is None:
  record['accounting']='No completion.json: infrastructure/probe only; do not count as completed navigation'
  for f in run.rglob('*.json'):
   if f.name in ['response.json','scene_geometry.json']:record.setdefault('probe',{})[f.name]={'diagnostic_key':str(f.relative_to(run))}
 for f in sorted(run.rglob('*_skipped.json')):record.setdefault('skipped_conditions',{})[f.stem]=json.loads(f.read_text())
 # Interrupted branches retain a concise physical-accounting record even if
 # the regular result writer was not reached.
 for execution in sorted(run.rglob('v648_execution.jsonl')):
  if(execution.parent/'result.json').exists():continue
  lines=execution.read_text().splitlines()
  last=None if not lines else json.loads(lines[-1])
  record.setdefault('partial_branches',[]).append({'branch':str(execution.parent.relative_to(run)),'completed_public_steps':len(lines),'last_audited_execution':last,'status':'INTERRUPTED_OR_INFRASTRUCTURE_FAILED_NOT_COMPLETED_NAVIGATION'})
 # Keep the original console, compressed. It is not navigation success evidence by itself.
 console=next(iter(root.glob(run.name+'.console*')),None)
 if console is not None:
  target=dest/'consoles'/(run.name+'.txt.gz');target.parent.mkdir(exist_ok=True)
  with gzip.open(target,'wb') as stream:stream.write(console.read_bytes())
 trials.append(record)
(dest/'trial_ledger.json').write_text(json.dumps(trials,ensure_ascii=False,indent=2,allow_nan=False))
for name in a.selected:
 paired=root/name/'paired';assert paired.is_dir(),name
 target=dest/'selected'/name;target.mkdir(parents=True)
 for f in sorted(paired.rglob('*')):
  if not f.is_file() or any(part in {'cache','assets','frozen_original'}for part in f.relative_to(paired).parts):continue
  rel=f.relative_to(paired);to=target/rel;to.parent.mkdir(parents=True,exist_ok=True)
  if f.suffix in {'.json','.jsonl'}:
   with gzip.open(str(to)+'.gz','wb')as stream:stream.write(f.read_bytes())
  else:shutil.copy2(f,to)
 xml=paired/'assets'/'isolated_indoor.xml'
 if xml.exists():shutil.copy2(xml,target/'initial_scene.xml')
# Narrow map snapshots preserve the old endpoint-accumulation diagnosis without duplicating full runs.
for run,file in [('static_pilot_07_seed2','planning_0590.json'),('static_pilot_08_seed2','planning_0178.json')]:
 src=root/run/'paired'/'memory'/file
 if not src.exists():
  candidates=sorted((root/run/'paired'/'memory').glob('planning_*.json'));src=candidates[-1]if candidates else None
 if src:
  to=dest/'map_counterexamples'/(run+'.json.gz');to.parent.mkdir(exist_ok=True)
  with gzip.open(to,'wb')as stream:stream.write(src.read_bytes())
for name in ['perception_property_check.json','perception_contract_check.json','exact_footprint_check.json','circle_memory_check.json','readiness_20261031.json','completed_branch_audits.json','round_accounting.json']:
 if(root/name).exists():shutil.copy2(root/name,dest/name)
figures=dest/'figures';figures.mkdir()
for filename in ['map_bottleneck.png','map_bottleneck.svg']:
 src=root/'map_connectivity_probe_16'/'paired'/filename
 if src.exists():shutil.copy2(src,figures/filename)
(dest/'README.md').write_text("""# 静态未知障碍开发证据 · 2026-10-31

当前报告：[STATIC_UNKNOWN_REPORT.md](../../docs/STATIC_UNKNOWN_REPORT.md)。在线候选源码已按 [DECISION_FREEZE.json](../../experiments/v648_static_unknown/DECISION_FREEZE.json) 冻结；仍属开发原型。

- `trial_ledger.json` 包含所有开发运行目录、结果/协议、初始化拒绝、主动中止、外部中断、探针和源码映射。不同版本、重复和场景不能合并为独立成功率。
- `selected/` 保留首个成功/重复及固定配置地图消融的完整接触、物理步摘要、公开状态、轨迹和规划输入输出，同时保留必要的失败对照。JSON/JSONL压缩后内容不改，接触日志原始压缩文件直接保存。
- `source_blobs/<sha256>.py` 对每次运行的源码快照去重；按该运行 `source_hashes` 的文件名和哈希可重建源目录。它们是历史证据，不是多个活动实验入口。
- `diagnostics/` 与 `figures/` 保存因果观测地图/评价真值的离线连通诊断，以及仅含机器人和地面的转向/制动响应探针。正连通不是连续SE(2)或动力学可达证明，评价真值不进入控制器。
- `map_counterexamples/` 保存旧点云积累的必要反例；新回波删失性质由独立合成测量检查支持，不把同期多项代码变化当单机制消融。
- `MANIFEST.json` 记录本包各文件的SHA256。原始迁移文件的旧哈希清单保持不变。

`initial_scene.xml` 为reset生成的XML；t0物体激活/关闭/位置以同运行的STATIC_PROTOCOL与sensor_geometry_sync为准。仅凭XML不能重建运行期模型状态。

同状态重复只验证可重复性；多帧圆柱经验包络尚未校准，不能写成形式化风险保证。所有SAC训练更新为0，Stage从未进入本轮运行的隔离空间。
""")
manifest=[]
for f in sorted(dest.rglob('*')):
 if f.is_file():manifest.append({'path':str(f.relative_to(dest)),'bytes':f.stat().st_size,'sha256':sha(f.read_bytes())})
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'trial_directories':len(trials),'selected_runs':a.selected,'curated_files':len(manifest),'curated_bytes':sum(x['bytes']for x in manifest)}))
