"""Archive the closed zero-integration audit validation without changing evidence."""
import gzip
import hashlib
import json
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
root = repo / 'runs/v699_dynamic_packet_audit'
dest = repo / 'evidence/rpccr_dynamic_audit_v699_20261102'
read = lambda path: json.loads(path.read_text())
sha = lambda data: hashlib.sha256(data).hexdigest()
assert read(root / 'ROUND_WINDOW.json')['closed']
assert read(root / 'COMPLETION.json')['status'] == 'AUDIT_REPAIR_VALIDATED_ONLY'
assert read(root / 'MISSING_KEY_NEGATIVE_TEST.json')['status'] == 'MISSING_KEY_REJECTION_VERIFIED'
assert (repo / 'REVIEW_PENDING').exists()
assert not dest.exists(), 'ARCHIVE_ALREADY_EXISTS_DO_NOT_OVERWRITE'
dest.mkdir()
blobs = dest / 'blobs'
blobs.mkdir()
inventory = []
paths = sorted(path for path in root.rglob('*') if path.is_file())
paths += [repo / 'runs/v699_zero_analysis.console']
for path in paths:
    if path.suffix in ('.lock', '.pyc') or '__pycache__' in path.parts:
        continue
    assert path.resolve().is_relative_to(repo / 'runs'), 'EXTERNAL_SOURCE_REJECTED'
    raw = path.read_bytes()
    digest = sha(raw)
    encoding = 'identity' if path.suffix == '.gz' else 'gzip'
    data = raw if encoding == 'identity' else gzip.compress(raw, mtime=0)
    blob = blobs / (digest + ('.raw' if encoding == 'identity' else '.gz'))
    if blob.exists():
        assert blob.read_bytes() == data
    else:
        blob.write_bytes(data)
    row = {'path': str(path.relative_to(repo)), 'bytes': len(raw), 'sha256': digest,
           'blob': str(blob.relative_to(dest)), 'stored_encoding': encoding}
    if path.is_symlink():
        row['read_only_original_fixture_reference'] = str(path.resolve().relative_to(repo))
    inventory.append(row)
(dest / 'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(
    (json.dumps(inventory, indent=2) + '\n').encode(), mtime=0))
(dest / 'README.md').write_text(
    '# RP-CCR V699空观测审计修复全证据\n\n'
    '独立零积分验证，未新增导航/预测/重放积分或训练。24原预检和13原发现链复核；'
    '前12结论不变，第13仅合法空JSON维度检查改变。严格数值/删射线/错误格式/缺键负例全部拒绝。'
    '原V698 NOT_PASSED、11未执行主任务、3未执行重复及所有旧原始证据均保持。\n\n'
    'RAW_INVENTORY记录每个新结果与完整负例夹具的来源、字节、SHA及内容寻址blob。'
    '夹具中的只读旧文件引用也完整按字节归档，注明原来源；篡改数据只在新夹具中。'
    '所有blob完整解压哈希回读，原始runs不删除。源码/协议由同仓库Git保存。\n\n'
    '[报告](../../docs/RPCCR_DYNAMIC_AUDIT_V699_REPORT.md)，'
    '[协议](../../experiments/v699_dynamic_packet_audit/PROTOCOL.md)。'
    '归档通过不是完整动态确认通过。\n')
manifest = [{'path': str(p.relative_to(dest)), 'bytes': p.stat().st_size,
             'sha256': sha(p.read_bytes())} for p in sorted(dest.rglob('*')) if p.is_file()]
(dest / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
for row in inventory:
    data = (dest / row['blob']).read_bytes()
    raw = gzip.decompress(data) if row['stored_encoding'] == 'gzip' else data
    assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
    assert sha((repo / row['path']).read_bytes()) == row['sha256']
for row in manifest:
    assert sha((dest / row['path']).read_bytes()) == row['sha256']
print(json.dumps({'status': 'ALL_ARCHIVED_BYTES_VERIFIED', 'raw_files': len(inventory),
                  'manifest_files': len(manifest), 'raw_bytes': sum(r['bytes'] for r in inventory),
                  'stored_bytes': sum(r['bytes'] for r in manifest), 'raw_deleted': False}))
