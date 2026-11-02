"""Complete bounded-round content-addressed evidence, preserving raw runs."""
from pathlib import Path
import hashlib,json,gzip,argparse
repo=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('roots',nargs='+');a=p.parse_args()
dest=repo/'evidence/rpccr_dynamic_initialization_v697_20261102'
assert not(dest/'MANIFEST.json').exists(),'IMMUTABLE_ARCHIVE_EXISTS'
roundpath=repo/'runs/v697_rpccr_dynamic_initialization/ROUND_WINDOW.json'
assert json.loads(roundpath.read_text())['round_closed'],'ROUND_STILL_ACTIVE'
dest.mkdir(exist_ok=True);blobs=dest/'blobs';blobs.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
inventory=[]
for name in a.roots:
 root=repo/'runs'/name;assert root.is_dir() and name=='v697_rpccr_dynamic_initialization'
 for f in sorted(root.rglob('*')):
  if not f.is_file()or f.suffix in ['.lock','.pyc']or '__pycache__'in f.parts:continue
  raw=f.read_bytes();h=sha(raw);encoding='identity'if f.suffix=='.gz'else'gzip'
  data=raw if encoding=='identity'else gzip.compress(raw,mtime=0)
  target=blobs/(h+('.raw'if encoding=='identity'else'.gz'))
  if target.exists():assert target.read_bytes()==data
  else:target.write_bytes(data)
  inventory.append({'path':str(f.relative_to(repo)),'bytes':len(raw),'sha256':h,'blob':str(target.relative_to(dest)),'stored_encoding':encoding})
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress((json.dumps(inventory,indent=2)+'\n').encode(),mtime=0))
(dest/'README.md').write_text('# RP-CCR V697初始化解耦开发全证据\n\n完整保留本轮全部零导航预检、导航/条件重复、原始成功与失败、初始化/噪声来源及独立审计。以FINAL_INDEPENDENT_AUDIT和报告为实际结论；不将24预检计为24导航确认，不将工程修复包装为算法创新。旧V696失败和旧夜间账目不变；原始runs不删。\n\nRAW_INVENTORY逐原文件列SHA/字节及内容寻址blob，全部解压回读校验。报告../../docs/RPCCR_DYNAMIC_INITIALIZATION_V697_REPORT.md，协议../../experiments/v697_rpccr_dynamic_initialization/PROTOCOL.md。Stage/训练/实机0。\n')
manifest=[{'path':str(f.relative_to(dest)),'bytes':f.stat().st_size,'sha256':sha(f.read_bytes())}for f in sorted(dest.rglob('*'))if f.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Read back every original byte stream from the archive; never rely on write success.
for row in inventory:
 data=(dest/row['blob']).read_bytes();raw=gzip.decompress(data)if row['stored_encoding']=='gzip'else data
 assert len(raw)==row['bytes']and sha(raw)==row['sha256']
for row in manifest:assert sha((dest/row['path']).read_bytes())==row['sha256']
print(json.dumps({'status':'ALL_ARCHIVED_BYTES_VERIFIED','raw_files':len(inventory),'manifest_files':len(manifest),'raw_bytes':sum(x['bytes']for x in inventory),'stored_bytes':sum(x['bytes']for x in manifest),'raw_deleted':False}))
