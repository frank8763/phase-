"""Complete bounded-round content-addressed evidence, preserving raw runs."""
from pathlib import Path
import hashlib,json,gzip,argparse
repo=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('roots',nargs='+');a=p.parse_args()
dest=repo/'evidence/dynamic_renewable_backup_v674_round_20261101'
assert not(dest/'MANIFEST.json').exists(),'IMMUTABLE_ARCHIVE_EXISTS'
roundpath=repo/'runs/v674_dynamic_renewable_backup/ROUND_WINDOW.json'
assert json.loads(roundpath.read_text())['round_closed'],'ROUND_STILL_ACTIVE'
dest.mkdir(exist_ok=True);blobs=dest/'blobs';blobs.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
inventory=[]
for name in a.roots:
 root=repo/'runs'/name;assert root.is_dir()and name.startswith(('v674_','v675_'))
 for f in sorted(root.rglob('*')):
  if not f.is_file()or f.suffix in ['.lock','.pyc']or '__pycache__'in f.parts:continue
  raw=f.read_bytes();h=sha(raw);encoding='identity'if f.suffix=='.gz'else'gzip'
  data=raw if encoding=='identity'else gzip.compress(raw,mtime=0)
  target=blobs/(h+('.raw'if encoding=='identity'else'.gz'))
  if target.exists():assert target.read_bytes()==data
  else:target.write_bytes(data)
  inventory.append({'path':str(f.relative_to(repo)),'bytes':len(raw),'sha256':h,'blob':str(target.relative_to(dest)),'stored_encoding':encoding})
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress((json.dumps(inventory,indent=2)+'\n').encode(),mtime=0))
(dest/'README.md').write_text('# V674有界后备续接开发全证据：未通过\n\n两次导航均未到达，扩大检查确认两版本各10公开步裁剪前原始证书命令与实际ctrl不同。V675原FAIL及V674原较窄检查PASS都保留，不能用模型内部裁剪解释回填原始命令契约通过。\n\n完整保留本轮全部导航、固定重放/私有诊断、失败账目、原始控制/测距/接触/原生状态、模型/XML、冻结源码和协议。每个原文件经RAW_INVENTORY映射到内容寻址blob；gzip只压缩，不改原字节。原始runs全部保留，尚未因本地归档删除。\n\n导航、重放、私有预测与独立确认严格分账；未到达不能因证据PASS或中途切回成功而改称验收通过。源与原截止、失败结论不回写，静态V657保持原结论。完整结论见../../docs/DYNAMIC_RENEWABLE_BACKUP_V674_REPORT.md及本包ROUND_WINDOW/FINAL_ANALYSIS对应原路径。\n')
manifest=[{'path':str(f.relative_to(dest)),'bytes':f.stat().st_size,'sha256':sha(f.read_bytes())}for f in sorted(dest.rglob('*'))if f.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Read back every original byte stream from the archive; never rely on write success.
for row in inventory:
 data=(dest/row['blob']).read_bytes();raw=gzip.decompress(data)if row['stored_encoding']=='gzip'else data
 assert len(raw)==row['bytes']and sha(raw)==row['sha256']
for row in manifest:assert sha((dest/row['path']).read_bytes())==row['sha256']
print(json.dumps({'status':'ALL_ARCHIVED_BYTES_VERIFIED','raw_files':len(inventory),'manifest_files':len(manifest),'raw_bytes':sum(x['bytes']for x in inventory),'stored_bytes':sum(x['bytes']for x in manifest),'raw_deleted':False}))
