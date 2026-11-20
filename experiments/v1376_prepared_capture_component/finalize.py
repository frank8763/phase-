"""Zero-model component accounting and verified streaming archive."""
import gzip
import hashlib
import importlib.util
import subprocess
import sys
import tarfile
from component_context import *
from campaign import storage_bytes
def main():
    assert not (O/'FINALIZED.json').exists();summary=read(O/'COMPLETION.json');assert summary['closed']
    assert (R/'REVIEW_PENDING').read_bytes()==(O/'REVIEW_PENDING.before').read_bytes()
    rows=[]
    for row in summary['results']:
        n=row.get('native') or {};rows.append(dict(task=row['task'],passed=row['passed'],actual_total_native=n.get('actual_total_native'),historical_reconstruction_native=n.get('historical_prefix_replay_native'),new_component_native=n.get('new_component_native'),own_replay_native=n.get('own_replay_native'),position_error_m=n.get('position_error_m'),heading_error_rad=n.get('heading_error_rad'),error=n.get('error'),canonical_vehicle_initializations=n.get('canonical_vehicle_initializations'),internal_factory_model_constructions=n.get('internal_factory_model_constructions')))
    dump(O/'ACCOUNTING.json',dict(rows=rows,new_navigation=0,unknown=[x['task'] for x in rows if x['actual_total_native'] is None or x['own_replay_native'] is None],models_during_closure=0))
    report='\n'.join(['# V1376 measured RP-CCR capture component','',
        'Pose capture main/repeat passed: '+str(summary['passed'])+'. Stop: '+str(summary.get('stop_reason'))+'.',
        'Fixed original9390 reconstructed through actual integration; two measured-travel arcs and complete200-native braking/gear gates, original.12m/.20rad capture bounds. No Nav2 comparison result or full dynamic handoff/goalnavigation claimed.',
        'Actual state/control/contact own replay and full independent causal all-future22cm/physical15cm/control/stop audit required. Repeated states must match1e-8. New component, prefix, replay and unknown factory constructions kept separate.',
        'Counts: '+json.dumps(rows,ensure_ascii=False)+'.',
        'Unexecuted: '+json.dumps(summary['unexecuted'])+'. The32210 timed handoff remains unqualified; no full route or24 started.',
        '17:00 root cutoff, default2GiB day cap, single physicsCPU2, Stage isolated. Raw retained pending remote downloaded SHA/restore verification; one new-round bounded sync, no old retry.'])+'\n'
    (O/'REPORT.md').write_text(report);(R/'docs/PREPARED_CAPTURE_V1376_REPORT.md').write_text(report)
    with (R/'RESEARCH_STATUS.md').open('a') as f:f.write('\n- V1376测量反馈两弧捕获组件已闭：main/repeat全门='+str(summary['passed'])+'，未执行'+str(summary['unexecuted'])+'；无整路/24或RPP对比结论，32210时序仍未资格。见docs/PREPARED_CAPTURE_V1376_REPORT.md。REVIEW_PENDING原字节恢复，零模型归档。\n')
    spec=importlib.util.spec_from_file_location('phase_capture_archive_primitives',R/'experiments/v1370_overnight_controller_matrix/finalize.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    directory=O/'archive';directory.mkdir(exist_ok=False);items=[]
    for root in [C,O,RAW]:
        for p in sorted(root.rglob('*')):
            if directory in p.parents:continue
            if p.is_symlink():assert p.name=='meshes_fixed';items.append(dict(path=str(p.relative_to(R)),symlink=str(p.readlink())))
            elif p.is_file():items.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=old.file_sha(p)))
    writer=old.Parts(directory,storage_bytes(),2*1024**3)
    with gzip.GzipFile(fileobj=writer,mode='wb',compresslevel=3) as compressor,tarfile.open(fileobj=compressor,mode='w|') as archive:
        for item in items:
            info=tarfile.TarInfo(item['path'])
            if 'symlink' in item:info.type=tarfile.SYMTYPE;info.linkname=item['symlink'];archive.addfile(info)
            else:
                info.size=item['bytes']
                with (R/item['path']).open('rb') as f:archive.addfile(info,f)
    writer.finish_part();h=hashlib.sha256()
    for part in writer.parts:
        p=directory/part['name'];assert old.file_sha(p)==part['sha256']
        with p.open('rb') as f:
            for block in iter(lambda:f.read(1048576),b''):h.update(block)
    assert h.hexdigest()==writer.digest.hexdigest();wanted={x['path']:x for x in items};seen=set()
    with tarfile.open(fileobj=old.Reader([directory/p['name'] for p in writer.parts]),mode='r|gz') as archive:
        for member in archive:
            assert member.name in wanted and member.name not in seen;seen.add(member.name);item=wanted[member.name]
            if 'symlink' in item:assert member.issym() and member.linkname==item['symlink']
            else:
                h=hashlib.sha256();f=archive.extractfile(member)
                for block in iter(lambda:f.read(1048576),b''):h.update(block)
                assert h.hexdigest()==item['sha256']
    assert seen==set(wanted) and sources()
    dump(O/'ARCHIVE_INDEX.json',dict(files=items,parts=writer.parts,archive_sha256=writer.digest.hexdigest(),archive_bytes=writer.total,local_members_and_reassembly_verified=True,remote_download_restore_verified=False,raw_deleted=False,models=0))
    dump(O/'FINALIZED.json',dict(passed=True,capture_component_pair_passed=summary['passed'],local_memberSHA_and_reassembly_verified=True,source_unchanged=True,models=0))
    with (O/'sync.console').open('x') as f:p=subprocess.run([sys.executable,'-B',str(C/'sync_results.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=120)
    dump(O/'SYNC_WORKER_EXIT.json',dict(returncode=p.returncode,models=0))
if __name__=='__main__':main()
