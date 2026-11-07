"""Bounded zero-model preparation archive with original input and read-back SHA."""
import hashlib
import json
from pathlib import Path
import signal
import zipfile

R=Path(__file__).resolve().parents[2]


def main():
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('PREPARATION_ARCHIVE_180S')));signal.alarm(180)
    out=R/'runs/v850_progress_consistent_return'
    target=R/'evidence/rpccr_v850_preparation_20261107';target.mkdir(exist_ok=False)
    inputs=json.loads((out/'saved_qualification/INPUT_SHA256.json').read_text())
    original=json.loads((out/'ORIGINAL_SOURCE_SHA256.json').read_text())
    paths={R/p for p in inputs}|{R/p for p in original}
    for directory in [R/'experiments/v850_progress_consistent_return',R/'experiments/v850_progress_consistent_worker',out]:
        paths.update(p for p in directory.rglob('*')if p.is_file()and'__pycache__'not in p.parts)
    paths.add(R/'docs/RPCCR_REAL_ROBOT_AND_CONTRIBUTION_20261107.md')
    for p,h in {**inputs,**original}.items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h
    manifest={}
    for p in sorted(paths):
        assert p.resolve().is_relative_to(R)
        raw=p.read_bytes();assert len(raw)<90*1024**2
        manifest[str(p.relative_to(R))]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    archive=target/'preparation.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for name in manifest:z.write(R/name,name)
    with zipfile.ZipFile(archive)as z:
        assert set(z.namelist())==set(manifest)
        for name,meta in manifest.items():
            raw=z.read(name);assert len(raw)==meta['bytes']and hashlib.sha256(raw).hexdigest()==meta['sha256']
    (target/'SOURCE_SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n')
    result=dict(status='PREPARATION_SOURCE_AND_DECOMPRESSED_SHA_PASS',files=len(manifest),archive_bytes=archive.stat().st_size,archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),original_sources_retained=True,old_evidence_not_overwritten=True,models=0,integrations=0,physical_or_navigation_pass=False)
    (target/'VERIFIED.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
