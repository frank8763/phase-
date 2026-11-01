"""Complete bounded-round content-addressed evidence, preserving raw runs."""
from pathlib import Path
import hashlib,json,gzip,argparse
repo=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('roots',nargs='+');a=p.parse_args()
dest=repo/'evidence/dynamic_discovery_v691_20261101'
assert not(dest/'MANIFEST.json').exists(),'IMMUTABLE_ARCHIVE_EXISTS'
roundpath=repo/'runs/v691_discovery_in_motion/ROUND_WINDOW.json'
assert json.loads(roundpath.read_text())['round_closed'],'ROUND_STILL_ACTIVE'
dest.mkdir(exist_ok=True);blobs=dest/'blobs';blobs.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
inventory=[]
for name in a.roots:
 root=repo/'runs'/name;assert root.is_dir()and name=='v691_discovery_in_motion'
 for f in sorted(root.rglob('*')):
  if not f.is_file()or f.suffix in ['.lock','.pyc']or '__pycache__'in f.parts:continue
  raw=f.read_bytes();h=sha(raw);encoding='identity'if f.suffix=='.gz'else'gzip'
  data=raw if encoding=='identity'else gzip.compress(raw,mtime=0)
  target=blobs/(h+('.raw'if encoding=='identity'else'.gz'))
  if target.exists():assert target.read_bytes()==data
  else:target.write_bytes(data)
  inventory.append({'path':str(f.relative_to(repo)),'bytes':len(raw),'sha256':h,'blob':str(target.relative_to(dest)),'stored_encoding':encoding})
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress((json.dumps(inventory,indent=2)+'\n').encode(),mtime=0))
(dest/'README.md').write_text('# V691行驶途中首次发现动态障碍全证据\n\n保存初始未观测/清空先验前置、原始测距因果发现、完整328原生步减速停车证书、新路线、实际继续移动但未到达的全分母证据。主任务408公开步未到达，条件完整重复未执行；检测、制动和重规划通过不代表完整任务通过。冻结V690网络，训练0。全部实际与未执行结果分列，不称原墙体场景动态稳定通过。\n\nRAW_INVENTORY逐原文件列SHA/字节与内容寻址blob，完整解压哈希回读后保留原始runs。旧失败/源码/协议/截止不改，Stage/实机0。报告../../docs/DYNAMIC_DISCOVERY_V691_REPORT.md。\n')
manifest=[{'path':str(f.relative_to(dest)),'bytes':f.stat().st_size,'sha256':sha(f.read_bytes())}for f in sorted(dest.rglob('*'))if f.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Read back every original byte stream from the archive; never rely on write success.
for row in inventory:
 data=(dest/row['blob']).read_bytes();raw=gzip.decompress(data)if row['stored_encoding']=='gzip'else data
 assert len(raw)==row['bytes']and sha(raw)==row['sha256']
for row in manifest:assert sha((dest/row['path']).read_bytes())==row['sha256']
print(json.dumps({'status':'ALL_ARCHIVED_BYTES_VERIFIED','raw_files':len(inventory),'manifest_files':len(manifest),'raw_bytes':sum(x['bytes']for x in inventory),'stored_bytes':sum(x['bytes']for x in manifest),'raw_deleted':False}))
