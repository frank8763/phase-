"""Close V847 once, without loading or advancing any physical model."""
import importlib.abc
import sys


class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name == 'mujoco' or name.startswith('mujoco.'):
            raise RuntimeError('DIAGNOSTIC_CLOSURE_FORBIDS_MODELS')


sys.meta_path.insert(0, NoModels())
import fcntl
import hashlib
import json
from pathlib import Path
import zipfile

R = Path(__file__).resolve().parents[2]
OWN = R/'experiments/v847_gpu_reference_diagnosis'
OUT = R/'runs/v847_gpu_reference_diagnosis'


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for b in iter(lambda: stream.read(4*1024**2), b''): h.update(b)
    return h.hexdigest()


def main():
    assert not (OUT/'FINALIZED.json').exists(), 'NO_OVERWRITE'
    with (R/'runs/v648_static_unknown/execution.lock').open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    read = lambda p: json.loads(p.read_text())
    assert read(OUT/'GPU_OUTER_COMPLETION.json')['guard_exact']
    refs = read(OUT/'references/COMPLETION.json')
    assert len(refs['records']) == 4
    witness = read(OUT/'GPU_FAILURE_WITNESS.json')
    files = {}
    for freeze in ['FREEZE.json', 'REFERENCE_FREEZE.json']:
        for p, h in read(OWN/freeze)['files'].items():
            assert sha(R/p) == h, p
            files[p] = R/p
    report = R/'docs/RPCCR_GPU_REFERENCE_V847_20261106_REPORT.md'
    summary = dict(status='DIAGNOSIS_CLOSED_NOT_BACKEND_OR_NAVIGATION_ACCEPTANCE',
                   gpu=witness, reference_queries=refs['records'],
                   counts=witness['current_counts'], model_metadata_reads=2,
                   metadata_integrations=0, training=0, new24=0,
                   gpu_original_assertion_passed=False,
                   complete_reference_witnesses=refs['complete_references'])
    report.write_text('# V847 GPU与目标参考诊断\n\n'+json.dumps(summary, ensure_ascii=False, indent=2)+
        '\n\n64世界同输入初态和控制误差0；root位置差2.384e-6m、关节最大2.551e-5，未通过原1e-6断言。缓冲未满；不能将其判为世界串扰，也不能追认物理一致性合格。实测约10.5万世界步/秒仅为吞吐，不是安全控制时延。原失败及源码保持。\n\n四固定原因果参考中，1198双向搜索1.764秒得到距目标.184608m的完整参考，旧前向只返回距目标2.374880m的前缀；另三例仍非完整目标，未作导航成功结论。参考资格不代替完整328安全证书、实际物理及发现链验收。后续另冻结一个候选，禁止修改本诊断源重跑。\n')
    for base in [OWN, OUT]:
        for p in base.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.lock', '.pyc']:
                files[str(p.relative_to(R))] = p
    files[str(report.relative_to(R))] = report
    target = R/'evidence/rpccr_gpu_reference_v847_20261106'
    target.mkdir(exist_ok=False)
    archive = target/'RAW.zip'
    inventory = []
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as z:
        for name, p in sorted(files.items()):
            h = sha(p); z.write(p, name)
            inventory.append(dict(path=name, bytes=p.stat().st_size, sha256=h))
    with zipfile.ZipFile(archive) as z:
        for row in inventory:
            h = hashlib.sha256(); n = 0
            with z.open(row['path']) as stream:
                for b in iter(lambda: stream.read(4*1024**2), b''): h.update(b); n += len(b)
            assert h.hexdigest() == row['sha256'] and n == row['bytes'] and sha(files[row['path']]) == row['sha256']
    manifest = dict(inventory=inventory, zip_sha256=sha(archive), zip_bytes=archive.stat().st_size,
                    all_sources_and_decompressed_sha_verified=True, raw_deleted=False)
    if archive.stat().st_size > 90*1024**2:
        parts = []; h = hashlib.sha256()
        with archive.open('rb') as stream:
            for i, b in enumerate(iter(lambda: stream.read(32*1024**2), b'')):
                p = target/f'RAW.zip.part{i:03d}'; p.write_bytes(b); h.update(p.read_bytes())
                parts.append(dict(path=p.name, bytes=len(b), sha256=sha(p)))
        assert h.hexdigest() == manifest['zip_sha256']
        manifest.update(parts=parts, recombined_sha_verified=True)
        restore = R/'evidence/rpccr_gpu_parallel_v846_20261106/restore.py'
        (target/'restore.py').write_bytes(restore.read_bytes())
    (target/'MANIFEST.json').write_text(json.dumps(manifest, indent=2)+'\n')
    result = summary | dict(archive=str(target.relative_to(R)), source_and_decompressed_sha_verified=True,
                            models_finalizer=0, integrations_finalizer=0, closed=True)
    (OUT/'FINALIZED.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['gpu','reference_queries']}))


if __name__ == '__main__': main()
