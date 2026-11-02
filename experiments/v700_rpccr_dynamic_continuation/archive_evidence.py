"""Content-address every finished scientific output; preserve all originals."""
import gzip,hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v700_rpccr_dynamic_continuation';dest=repo/'evidence/rpccr_dynamic_continuation_v700_20261102'
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
c=read(root/'continuation01/COMPLETION.json');roots={root}
for record in c['results']:
    if record.get('origin')!='V700_NEW_EXECUTION':continue
    pair=(repo/record['run']).resolve();assert pair.parent.name.startswith('v700_') and pair.is_relative_to(repo/'runs/v697_rpccr_dynamic_initialization')
    if pair.parent.exists():roots.add(pair.parent)
original=repo/'evidence/rpccr_dynamic_confirmation_v698_20261102'
references=[]
for row in read(original/'MANIFEST.json'):
    path=original/row['path'];assert digest(path.read_bytes())==row['sha256'];references.append({'path':str(path.relative_to(repo)),'sha256':row['sha256'],'bytes':row['bytes']})
with gzip.open(original/'RAW_INVENTORY.json.gz','rt') as stream:original_inventory=json.load(stream)
for row in original_inventory:
    data=(original/row['blob']).read_bytes();raw=gzip.decompress(data) if row['stored_encoding']=='gzip' else data
    assert len(raw)==row['bytes'] and digest(raw)==row['sha256']
(dest/'ORIGINAL_EVIDENCE_REFERENCES.json').write_text(json.dumps({'scope':'Imported original V698 evidence, not new navigation; originals preserved and completely reverified.','files':references,'original_raw_files_verified':len(original_inventory)},indent=2)+'\n')
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
(dest/'README.md').write_text('# V700 RP-CCR动态原清单接续全证据\n\n原V698 NOT_PASSED保持，旧完整证据以ORIGINAL_EVIDENCE_REFERENCES引用并全部解压回读。保存本次原冻结24任务、全部尝试/失败/未执行、三项条件重复及全部原始物理/控制/传感/源模型审计。以FINAL_INDEPENDENT_AUDIT和报告为实际结论，不凭归档完成或进程exit0宣称验收。工人来源为冻结V697，原V696/V697与旧夜间证据不改。\n\nRAW_INVENTORY逐原文件列SHA/字节和内容寻址blob；全部解压哈希回读。收尾仍在写的finalize.console及FINALIZED.json是操作状态，不纳入科学数据快照；原始文件都保留。报告../../docs/RPCCR_DYNAMIC_CONTINUATION_V700_REPORT.md，协议../../experiments/v700_rpccr_dynamic_continuation/PROTOCOL.md。Stage/训练/实机0。\n')
manifest=[{'path':str(p.relative_to(dest)),'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())} for p in sorted(dest.rglob('*')) if p.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in inventory:
    data=(dest/row['blob']).read_bytes();raw=gzip.decompress(data) if row['stored_encoding']=='gzip' else data
    assert len(raw)==row['bytes'] and digest(raw)==row['sha256']
for row in manifest:assert digest((dest/row['path']).read_bytes())==row['sha256']
print(json.dumps({'status':'ALL_ARCHIVED_BYTES_VERIFIED','raw_files':len(inventory),'manifest_files':len(manifest),'stored_bytes':sum(x['bytes'] for x in manifest),'raw_deleted':False}))
