"""Complete bounded-round content-addressed evidence, preserving raw runs."""
from pathlib import Path
import hashlib,json,gzip,argparse
repo=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('roots',nargs='+');a=p.parse_args()
dest=repo/'evidence/dynamic_forward_reserve_v679_round_20261101'
assert not(dest/'MANIFEST.json').exists(),'IMMUTABLE_ARCHIVE_EXISTS'
roundpath=repo/'runs/v679_dynamic_forward_reserve/ROUND_WINDOW.json'
assert json.loads(roundpath.read_text())['round_closed'],'ROUND_STILL_ACTIVE'
dest.mkdir(exist_ok=True);blobs=dest/'blobs';blobs.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
inventory=[]
for name in a.roots:
 root=repo/'runs'/name;assert root.is_dir()and name.startswith(('v679_','v680_','v681_'))
 for f in sorted(root.rglob('*')):
  if not f.is_file()or f.suffix in ['.lock','.pyc']or '__pycache__'in f.parts:continue
  raw=f.read_bytes();h=sha(raw);encoding='identity'if f.suffix=='.gz'else'gzip'
  data=raw if encoding=='identity'else gzip.compress(raw,mtime=0)
  target=blobs/(h+('.raw'if encoding=='identity'else'.gz'))
  if target.exists():assert target.read_bytes()==data
  else:target.write_bytes(data)
  inventory.append({'path':str(f.relative_to(repo)),'bytes':len(raw),'sha256':h,'blob':str(target.relative_to(dest)),'stored_encoding':encoding})
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress((json.dumps(inventory,indent=2)+'\n').encode(),mtime=0))
(dest/'README.md').write_text('# V679–V681完整有界诊断与失败证据\n\nV679固定状态前进尾诊断、V680唯一实际未知动态导航804公开未到达、V681第49输入路线前置失败未导航。0到达/重复/独立确认/新几何/训练/实机/Stage。私有阳性只说明有限后备库增量，未作为成功导航。完整原始日志、模型/XML、源码冻结、控制/状态/测距/接触/原生日志、各次前置结果及累计分账全部保存。\n\nRAW_INVENTORY逐原文件列SHA/字节与内容寻址blob；全部逐字节解压/哈希回读。原始runs保留，原失败/COMPLETION与旧截止不改写。结论见../../docs/DYNAMIC_FORWARD_RESERVE_V679_REPORT.md；下一时序结构只是未执行规格。\n')
manifest=[{'path':str(f.relative_to(dest)),'bytes':f.stat().st_size,'sha256':sha(f.read_bytes())}for f in sorted(dest.rglob('*'))if f.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Read back every original byte stream from the archive; never rely on write success.
for row in inventory:
 data=(dest/row['blob']).read_bytes();raw=gzip.decompress(data)if row['stored_encoding']=='gzip'else data
 assert len(raw)==row['bytes']and sha(raw)==row['sha256']
for row in manifest:assert sha((dest/row['path']).read_bytes())==row['sha256']
print(json.dumps({'status':'ALL_ARCHIVED_BYTES_VERIFIED','raw_files':len(inventory),'manifest_files':len(manifest),'raw_bytes':sum(x['bytes']for x in inventory),'stored_bytes':sum(x['bytes']for x in manifest),'raw_deleted':False}))
