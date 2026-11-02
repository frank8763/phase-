"""Content-address every finished scientific output; preserve all originals."""
import gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v704_bootstrap_repair';dest=repo/'evidence/rpccr_bootstrap_repair_v704_20261102'
read=lambda p:json.loads(p.read_text());digest=lambda b:hashlib.sha256(b).hexdigest()
assert read(root/'ROUND_WINDOW.json')['round_closed'],'ROUND_STILL_RUNNING'
if (dest/'MANIFEST.json').exists():
    for row in read(dest/'MANIFEST.json'):assert digest((dest/row['path']).read_bytes())==row['sha256']
    with gzip.open(dest/'RAW_INVENTORY.json.gz','rt') as f:inventory=json.load(f)
    for row in inventory:
        data=(dest/row['blob']).read_bytes();raw=gzip.decompress(data) if row['stored_encoding']=='gzip' else data
        assert len(raw)==row['bytes'] and digest(raw)==row['sha256']
    print(json.dumps({'status':'EXISTING_COMPLETE_ARCHIVE_REVERIFIED','raw_files':len(inventory)}));raise SystemExit(0)
dest.mkdir(exist_ok=True);blobs=dest/'blobs';blobs.mkdir(exist_ok=True)
c=read(root/'repair01/COMPLETION.json');roots={root}
for record in c['results']:
    pair=(repo/record['run']).resolve();assert pair.is_relative_to(root) and pair.parent.name==record['name']
    if not pair.parent.exists():continue
inventory=[]
for directory in sorted(roots):
    for path in sorted(directory.rglob('*')):
        if not path.is_file() or path.suffix in ['.lock','.pyc'] or '__pycache__' in path.parts:continue
        if path.parent==root and path.name in ['finalize.console','FINALIZED.json']:continue
        raw=path.read_bytes();h=digest(raw);encoding='identity' if path.suffix=='.gz' else 'gzip';data=raw if encoding=='identity' else gzip.compress(raw,mtime=0)
        target=blobs/(h+('.raw' if encoding=='identity' else '.gz'))
        if target.exists():assert target.read_bytes()==data
        else:target.write_bytes(data)
        inventory.append({'path':str(path.relative_to(repo)),'bytes':len(raw),'sha256':h,'blob':str(target.relative_to(dest)),'stored_encoding':encoding})
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress((json.dumps(inventory,indent=2)+'\n').encode(),mtime=0))
(dest/'README.md').write_text('# V704初始化修复与旧轨迹校准全证据\n\n保存4项零积分预检、2旧slot14校准的全部实际/失败/未执行与物理/传感/控制/重放/计算对照审核。以FINAL_INDEPENDENT_AUDIT和报告为结论，证据完整不代表新任务成功。原V702/V703失败不变，原始runs保留。RAW_INVENTORY给出原文件SHA、字节和内容寻址blob，全部解压回读。收尾操作文件FINALIZED/finalize.console不纳入科学快照。报告../../docs/RPCCR_BOOTSTRAP_REPAIR_V704_REPORT.md，协议../../experiments/v704_bootstrap_repair/PROTOCOL.md。Stage/训练/实机0。\n')
manifest=[{'path':str(p.relative_to(dest)),'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())} for p in sorted(dest.rglob('*')) if p.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in inventory:
    data=(dest/row['blob']).read_bytes();raw=gzip.decompress(data) if row['stored_encoding']=='gzip' else data
    assert len(raw)==row['bytes'] and digest(raw)==row['sha256']
for row in manifest:assert digest((dest/row['path']).read_bytes())==row['sha256']
print(json.dumps({'status':'ALL_ARCHIVED_BYTES_VERIFIED','raw_files':len(inventory),'manifest_files':len(manifest),'stored_bytes':sum(x['bytes'] for x in manifest),'raw_deleted':False}))
