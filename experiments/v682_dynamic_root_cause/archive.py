"""Archive zero-integration diagnosis outputs, with inherited input provenance."""
from pathlib import Path
import json,gzip,hashlib
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v682_dynamic_root_cause';dest=repo/'evidence/dynamic_root_cause_v682_20261101';assert not dest.exists();assert json.loads((root/'COMPLETION.json').read_text())['robot_integrations']==0;dest.mkdir();blobs=dest/'blobs';blobs.mkdir();sha=lambda b:hashlib.sha256(b).hexdigest();inventory=[]
for f in sorted(root.rglob('*')):
 if not f.is_file()or f.suffix=='.lock':continue
 raw=f.read_bytes();h=sha(raw);target=blobs/(h+'.gz');target.write_bytes(gzip.compress(raw,mtime=0));inventory.append({'path':str(f.relative_to(repo)),'bytes':len(raw),'sha256':h,'blob':str(target.relative_to(dest))})
(dest/'RAW_INVENTORY.json').write_text(json.dumps(inventory,indent=2)+'\n')
(dest/'INHERITED_INPUTS.json').write_text(json.dumps({'original_navigation_archive':'evidence/dynamic_forward_reserve_v679_round_20261101','original_navigation_evidence_commit':'3b6ec22a367094a76c1bb2174b9f199fe20a96da','input_sha256':json.loads((root/'ANALYSIS.json').read_text())['input_sha256'],'scope':'prior frozen V680 navigation; zero new navigation/replay/private robot prediction'},indent=2)+'\n')
(dest/'README.md').write_text('# V682动态根因零积分复核\n\n完整804帧停止后分析、精确当前状态几何反事实、真实进展分解和测距分辨率检查；机器人积分/新导航/训练/实机/Stage均0。继承的原输入来自V679–V681原始证据包，SHA可核验。未重开旧窗、未修改旧算法或失败，未证明新成功或全因果无解。结论见../../docs/DYNAMIC_ROOT_CAUSE_V682.md。\n\n每项输出解压逐字节核验，原始runs保留。真实未来只用于评价器反事实，未给在线算法。\n')
manifest=[{'path':str(f.relative_to(dest)),'bytes':f.stat().st_size,'sha256':sha(f.read_bytes())}for f in sorted(dest.rglob('*'))if f.is_file()];(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in inventory:
 raw=gzip.decompress((dest/row['blob']).read_bytes());assert sha(raw)==row['sha256']and len(raw)==row['bytes']and raw==(repo/row['path']).read_bytes()
for row in manifest:assert sha((dest/row['path']).read_bytes())==row['sha256']
print(json.dumps({'status':'ALL_DIAGNOSIS_BYTES_VERIFIED','raw_files':len(inventory),'manifest_files':len(manifest),'robot_integrations':0,'raw_deleted':False}))
