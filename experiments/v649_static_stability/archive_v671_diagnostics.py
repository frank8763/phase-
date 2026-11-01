"""Explicit diagnostic evidence archive; omit reproducible installed dependency tree."""
from pathlib import Path
import json,gzip,hashlib,shutil
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v671_dynamic_consistency_diagnosis';dest=repo/'evidence/dynamic_structure_diagnosis_v671_20261101';assert not(dest/'MANIFEST.json').exists();dest.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for f in root.iterdir():
 if f.is_file()and(f.suffix=='.json'or f.name.endswith('.jsonl.gz')):shutil.copy2(f,dest/f.name)
for name in ['private_probe','temporal_lp_import_failure']:
 source=root/name;target=dest/name;target.mkdir(exist_ok=True)
 for f in source.iterdir():
  if f.is_file():shutil.copy2(f,target/f.name)
for f in(repo/'runs').glob('v671_*.console'):
 d=dest/'consoles';d.mkdir(exist_ok=True);shutil.copy2(f,d/f.name)
extra=dest/'dependency_metadata';extra.mkdir(exist_ok=True)
for name in ['METADATA','WHEEL','RECORD','INSTALLER']:
 f=root/'analysis_dependencies/scipy-1.15.3.dist-info'/name
 if f.exists():shutil.copy2(f,extra/name)
blobs=dest/'source_blobs';blobs.mkdir(exist_ok=True);ledger=[]
groups=[('frozen_private_probe',root/'probe_source_snapshot'),('final_diagnostic_source',repo/'experiments/v671_dynamic_consistency_diagnosis'),('lp_import_failure_source',root/'temporal_lp_import_failure')]
for label,src in groups:
 hashes={}
 for f in src.iterdir():
  if f.is_file()and f.suffix in ['.py','.md']:
   h=sha(f);hashes[f.name]=h;target=blobs/(h+f.suffix)
   if not target.exists():shutil.copy2(f,target)
 ledger.append({'run':label,'source_hashes':hashes,'metadata':{'scope':'diagnostic source stage, not independent navigation trial'}})
(dest/'trial_ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
(dest/'README.md').write_text('# V671失败分解与原论文指导诊断\n\n0新导航的只读/固定控制诊断，依赖原V670完整控制/测距/模型，原档均保留；相关来源哈希、两个实际开发结果的全轮账目、输入验证、原缺依赖错误和LP32次结果全部收录。\n\n固定48/192/300/650四检查点100机器人私有控制，共24000积分；原控制重放至650共5200原生，完整状态误差0、接触0。原probe的scope文字遗留at3，但实际记录明确4点×25，不改原字段，见PRIVATE_PROBE_PROTOCOL与records。\n\n1545包联合位置速度/165未来网格核验PASS；非凸并集只增1个固定安全候选。32个数学LP保留时序约束只略收紧部分y速度界，不证明信息论不可辨识，也不是第三在线候选。SciPy1.15.3仅独立安装在runs/analysis_dependencies，未改冻结环境/控制器。安装树为公开可重建依赖，不复制整包；记录版本、RECORD/METADATA与输入/源码SHA。原未执行LP错误保留。\n\n全轮只V672/V673两个同开发几何导航且均未到达；FINAL_ANALYSIS分列所有积分与失败，不把数学/物理核验PASS当作通行PASS。0训练/实机/Stage访问，原5400秒截止未延长，无第三候选、重复或新池。\n\n报告 ../../docs/DYNAMIC_STRUCTURE_V673_REPORT.md；原论文核对 ../../docs/DYNAMIC_LITERATURE_FAILURE_ANALYSIS_V671.md。\n')
manifest=[{'path':str(f.relative_to(dest)),'bytes':f.stat().st_size,'sha256':sha(f)}for f in sorted(dest.rglob('*'))if f.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'files':len(manifest),'source_references':sum(len(x['source_hashes'])for x in ledger),'bytes':sum(x['bytes']for x in manifest)}))
