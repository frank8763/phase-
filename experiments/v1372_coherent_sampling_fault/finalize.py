"""Zero-model separate accounting, 32MiB archive, source/member/reassembly readback."""
import fcntl
import gzip
import hashlib
import importlib.util
import subprocess
import sys
import tarfile
from component_context import *
from campaign import storage_bytes

def main():
    assert not (O/'FINALIZED.json').exists(),'ARCHIVE_ALREADY_CLOSED'
    summary=read(O/'COMPLETION.json');assert summary['closed']
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert (R/'REVIEW_PENDING').read_bytes()==(O/'REVIEW_PENDING.before').read_bytes()
    native=summary.get('native') or {};origin=41390;total=native.get('actual_total_native')
    counts=dict(canonical_vehicle_initializations=native.get('canonical_vehicle_initializations'),internal_factory_model_constructions=native.get('internal_factory_model_constructions'),
        actual_total_native=total,historical_reconstruction_native=native.get('historical_prefix_replay_native'),new_component_native=native.get('new_component_native'),
        own_replay_native=native.get('own_replay_native'),new_navigation=0,private_model_native=native.get('private_mujoco_native'),models_during_closure=0,
        unknown_counts=[k for k in ['actual_total_native','own_replay_native','new_component_native'] if native.get(k) is None])
    dump(O/'ACCOUNTING.json',counts)
    report='\n'.join(['# V1372 coherent sampling fault component','',
        'Component passed: '+str(summary['passed'])+'. Stop: '+str(summary.get('stop_reason'))+'.',
        'One component, no goal navigation. Four genuine expired observation refusals, then a fresh zero command and complete 200-native stop tail.',
        'Original prefix 41390 is reconstructed by integration and separately counted; no root/time teleport. Original failed V1370 records are unchanged.',
        'Accounting: '+json.dumps(counts,ensure_ascii=False)+'.',
        'Full actual-state/ctrl/contact own replay and independent producer-runtime sensor/clock/control audit are required. This does not validate a timed handoff, dynamic goal arrival, or new24.',
        'Raw evidence retained until remote SHA and downloaded restore verification; new-round one bounded sync only.'])+'\n'
    (O/'REPORT.md').write_text(report);(R/'docs/COHERENT_SAMPLING_V1372_REPORT.md').write_text(report)
    spec=importlib.util.spec_from_file_location('phase_original_archive_primitives',R/'experiments/v1370_overnight_controller_matrix/finalize.py')
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    directory=O/'archive';directory.mkdir(exist_ok=False);items=[]
    for root in [C,O,RAW]:
        for p in sorted(root.rglob('*')):
            if directory in p.parents:continue
            if p.is_symlink():
                assert p.name=='meshes_fixed';items.append(dict(path=str(p.relative_to(R)),symlink=str(p.readlink())))
            elif p.is_file():items.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=old.file_sha(p)))
    writer=old.Parts(directory,storage_bytes(),read(C/'CAMPAIGN_CONFIG.json')['storage_limit_bytes'])
    with gzip.GzipFile(fileobj=writer,mode='wb',compresslevel=3) as compressor,tarfile.open(fileobj=compressor,mode='w|') as archive:
        for item in items:
            info=tarfile.TarInfo(item['path'])
            if 'symlink' in item:info.type=tarfile.SYMTYPE;info.linkname=item['symlink'];archive.addfile(info)
            else:
                info.size=item['bytes']
                with (R/item['path']).open('rb') as f:archive.addfile(info,f)
    writer.finish_part();digest=hashlib.sha256()
    for part in writer.parts:
        p=directory/part['name'];assert old.file_sha(p)==part['sha256']
        with p.open('rb') as f:
            for block in iter(lambda:f.read(1048576),b''):digest.update(block)
    assert digest.hexdigest()==writer.digest.hexdigest();wanted={i['path']:i for i in items};seen=set()
    with tarfile.open(fileobj=old.Reader([directory/p['name'] for p in writer.parts]),mode='r|gz') as archive:
        for member in archive:
            assert member.name in wanted and member.name not in seen;seen.add(member.name);item=wanted[member.name]
            if 'symlink' in item:assert member.issym() and member.linkname==item['symlink']
            else:
                h=hashlib.sha256();f=archive.extractfile(member)
                for b in iter(lambda:f.read(1048576),b''):h.update(b)
                assert h.hexdigest()==item['sha256']
    assert seen==set(wanted) and sources()
    dump(O/'ARCHIVE_INDEX.json',dict(files=items,parts=writer.parts,archive_sha256=writer.digest.hexdigest(),archive_bytes=writer.total,
        local_members_and_reassembly_verified=True,remote_download_restore_verified=False,raw_deleted=False,models=0))
    dump(O/'FINALIZED.json',dict(passed=True,component_passed=summary['passed'],local_memberSHA_and_reassembly_verified=True,source_unchanged=True,models=0))
    fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
    with (O/'sync.console').open('x') as f:p=subprocess.run([sys.executable,'-B',str(C/'sync_results.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=120)
    dump(O/'SYNC_WORKER_EXIT.json',dict(returncode=p.returncode,models=0))
if __name__=='__main__':main()
