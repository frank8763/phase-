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
        n=row.get('native') or {};rows.append(dict(task=row['task'],passed=row['passed'],actual_total_native=n.get('actual_total_native'),historical_reconstruction_native=n.get('historical_prefix_replay_native'),new_component_native=n.get('new_component_native'),own_replay_native=n.get('own_replay_native'),analytical_native=n.get('analytical_native'),analytical_step_inflight_unknown=n.get('analytical_step_inflight_unknown',n=={}),audit_analytical_native=row.get('audit',{}).get('audit_analytical_native'),position_error_m=n.get('position_error_m'),heading_error_rad=n.get('heading_error_rad'),error=n.get('error'),canonical_vehicle_initializations=n.get('canonical_vehicle_initializations'),internal_factory_model_constructions=n.get('internal_factory_model_constructions')))
    dump(O/'ACCOUNTING.json',dict(rows=rows,new_navigation=0,unknown=[x['task'] for x in rows if x['actual_total_native'] is None or x['own_replay_native'] is None],models_during_closure=0))
    report='\n'.join(['# V1383 original32210 timed handoff','',
        'Complete timed handoff pair passed: '+str(summary['passed'])+'. Stop: '+str(summary.get('stop_reason'))+'.',
        'Registered scope: canonical t0 reconstruction to32600 with full state/control/mocap/memory checks, then original32200 causal-time geometry and response-aware next-segment driving/braking main; full repeat only after all main gates pass. Actual executed coverage and any reconstruction failure are in the counts below. No whole route/new24.',
        'Admission requires a complete200-step response-model braking alternative from each new actual state/controller memory, original22cm predictive/15cm physical/12cm and.20rad endpoint/200 applied zero tail/full1e-8 state replay gates. A failed round does not establish these gates. Finite error bounds are empirical, not universal safety. Analytical work including independent branch recomputation is separate.',
        'Counts: '+json.dumps(rows,ensure_ascii=False)+'.',
        'Unexecuted: '+json.dumps(summary['unexecuted'])+'. Full32210 next-segment pair passed='+str(summary['passed'])+'; full9390 continuation remains unqualified, no original route or24 started.',
        'Monday09:00 campaign root cutoff,90min independent round,10GiB total temporary cap, single physicsCPU2, Stage isolated. Raw retained pending remote downloaded SHA/restore verification; one new-round bounded sync, no old retry.'])+'\n'
    (O/'REPORT.md').write_text(report);(R/'docs/EXACT_TIMED_HANDOFF_V1383_REPORT.md').write_text(report)
    with (R/'RESEARCH_STATUS.md').open('a') as f:f.write('\n- V1383原32210完整时序交接组件已闭：main/repeat全门='+str(summary['passed'])+'，未执行'+str(summary['unexecuted'])+'；仅此保存状态的交接资格随全门结果登记，无整路/24或RPP对比结论。见docs/EXACT_TIMED_HANDOFF_V1383_REPORT.md。REVIEW_PENDING原字节恢复，零模型归档。\n')
    spec=importlib.util.spec_from_file_location('phase_capture_archive_primitives',R/'experiments/v1370_overnight_controller_matrix/finalize.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    directory=O/'archive';directory.mkdir(exist_ok=False);items=[]
    for root in [C,O,RAW,R/'experiments/v1379_timed_response_preparation',R/'runs/v1379_timed_response_preparation']:
        for p in sorted(root.rglob('*')):
            if directory in p.parents:continue
            if p.is_symlink():assert p.name=='meshes_fixed';items.append(dict(path=str(p.relative_to(R)),symlink=str(p.readlink())))
            elif p.is_file():items.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=old.file_sha(p)))
    # Include every frozen source byte, with saved evidence inputs identified
    # by the full freeze and their retained historical archives, not duplicated.
    present={x['path'] for x in items}
    for name in read(C/'SOURCE_FREEZE.json')['files']:
        if name.startswith('runs/') or name in present:continue
        p=R/name
        assert p.is_file() and not p.is_symlink(),'FROZEN_SOURCE_FILE_REQUIRED '+name
        items.append(dict(path=name,bytes=p.stat().st_size,sha256=old.file_sha(p)));present.add(name)
    writer=old.Parts(directory,storage_bytes(),10*1024**3)
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
    dump(O/'FINALIZED.json',dict(passed=True,timed_handoff_pair_passed=summary['passed'],local_memberSHA_and_reassembly_verified=True,source_unchanged=True,models=0))
    ledger=read(DAY/'LEDGER.json');record=next(x for x in ledger['rounds'] if x['id']==C.name);record.update(finalized=True,full32210_handoff_qualified=summary['passed'],archive_index=str((O/'ARCHIVE_INDEX.json').relative_to(R)));ledger['latest_32210_handoff_qualified']=summary['passed'];dump(DAY/'LEDGER.json',ledger)
    with (O/'sync.console').open('x') as f:p=subprocess.run([sys.executable,'-B',str(C/'sync_results.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=120)
    dump(O/'SYNC_WORKER_EXIT.json',dict(returncode=p.returncode,models=0))
    if (O/'SYNC_RESULT.json').exists() and read(O/'SYNC_RESULT.json').get('remote_verified'):
        with (O/'delivery.console').open('x') as log:delivery=subprocess.run([sys.executable,'-B',str(R/'experiments/v1382_weekend_campaign/deliver_round.py'),str(O.relative_to(R))],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=900)
        dump(O/'DELIVERY_WORKER_EXIT.json',dict(returncode=delivery.returncode,models=0))
if __name__=='__main__':main()
