"""Complete bounded-round content-addressed evidence, preserving raw runs."""
from pathlib import Path
import hashlib,json,gzip,argparse
repo=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('roots',nargs='+');a=p.parse_args()
dest=repo/'evidence/dynamic_current_info_v683_round_20261101'
assert not(dest/'MANIFEST.json').exists(),'IMMUTABLE_ARCHIVE_EXISTS'
roundpath=repo/'runs/v683_dynamic_current_state_diagnosis/ROUND_WINDOW.json'
assert json.loads(roundpath.read_text())['round_closed'],'ROUND_STILL_ACTIVE'
dest.mkdir(exist_ok=True);blobs=dest/'blobs';blobs.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
inventory=[]
for name in a.roots:
 root=repo/'runs'/name;assert root.is_dir()and name.startswith(('v683_','v684_','v685_'))
 for f in sorted(root.rglob('*')):
  if not f.is_file()or f.suffix in ['.lock','.pyc']or '__pycache__'in f.parts:continue
  raw=f.read_bytes();h=sha(raw);encoding='identity'if f.suffix=='.gz'else'gzip'
  data=raw if encoding=='identity'else gzip.compress(raw,mtime=0)
  target=blobs/(h+('.raw'if encoding=='identity'else'.gz'))
  if target.exists():assert target.read_bytes()==data
  else:target.write_bytes(data)
  inventory.append({'path':str(f.relative_to(repo)),'bytes':len(raw),'sha256':h,'blob':str(target.relative_to(dest)),'stored_encoding':encoding})
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress((json.dumps(inventory,indent=2)+'\n').encode(),mtime=0))
(dest/'README.md').write_text('# V683–V685信息消融、拒绝的因果修订与末端分量全证据\n\nV683只公开准确当前状态，753公开/6024原生未到达，明确特权信息不计未知算法成功；原信息计数FAIL与原COMPLETION保留，V2零积分核对全部754决策。V684在49/227/245前置没有注册增量，未导航。V685只复算原18条240步预测，误差0，末端全部仅动态外覆盖拒绝；实际未来仅后见评价，未给在线控制。原初始化/辅助字段失败全部保留并计账。\n\nRAW_INVENTORY逐原文件列SHA/字节与内容寻址blob。全部归档后解压逐字节/哈希回读，原始runs保留。旧窗口/失败/模型/源码保持；同原V683截止，没有新窗口或刷种子。1特权导航、0新因果导航/确认/重复/训练/实机/Stage。完整报告见../../docs/DYNAMIC_INFO_VALIDATION_V683_REPORT.md。\n')
manifest=[{'path':str(f.relative_to(dest)),'bytes':f.stat().st_size,'sha256':sha(f.read_bytes())}for f in sorted(dest.rglob('*'))if f.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Read back every original byte stream from the archive; never rely on write success.
for row in inventory:
 data=(dest/row['blob']).read_bytes();raw=gzip.decompress(data)if row['stored_encoding']=='gzip'else data
 assert len(raw)==row['bytes']and sha(raw)==row['sha256']
for row in manifest:assert sha((dest/row['path']).read_bytes())==row['sha256']
print(json.dumps({'status':'ALL_ARCHIVED_BYTES_VERIFIED','raw_files':len(inventory),'manifest_files':len(manifest),'raw_bytes':sum(x['bytes']for x in inventory),'stored_bytes':sum(x['bytes']for x in manifest),'raw_deleted':False}))
