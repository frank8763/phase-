"""Accurate physical accounting and symlink-aware source-complete local archive."""
import gzip
import hashlib
import importlib.util
import subprocess
import sys
import tarfile
from component_context import *
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
    assert not (O/'FINALIZED.json').exists();summary=read(O/'COMPLETION.json');assert summary['closed']
    assert (R/'REVIEW_PENDING').read_bytes()==(O/'REVIEW_PENDING.before').read_bytes()
    rows=[]
    for row in summary['results']:
        n=row.get('native') or {};a=row.get('audit') or {}
        rows.append(dict(task=row['task'],passed=row['passed'],actual_total_native=n.get('actual_total_native'),historical_reconstruction_native=n.get('historical_prefix_replay_native'),new_component_native=n.get('new_component_native'),own_replay_native=n.get('own_replay_native'),native_analytical_native=n.get('analytical_native'),analytical_unknown=n.get('analytical_step_inflight_unknown',not bool(n)),audit_analytical_native=a.get('audit_analytical_native'),canonical_vehicle_initializations=n.get('canonical_vehicle_initializations'),internal_factory_model_constructions=n.get('internal_factory_model_constructions'),position_error_m=n.get('position_error_m'),heading_error_rad=n.get('heading_error_rad'),error=n.get('error'),audit_error=a.get('error')))
    dump(O/'ACCOUNTING.json',dict(rows=rows,new_navigation=0,unexecuted=summary['unexecuted'],models_during_closure=0))
    report='\n'.join(['# OriginalRPP full9390 actual continuation','',
        'Main and complete-repeat all gates passed: '+str(summary['passed'])+'. Stop: '+str(summary.get('stop_reason'))+'.',
        'Registered canonical t0 reconstruction to actual captured10775, then original RPP lookahead.6/speed.1 on unchanged49-point forward segment with actual acquired scan/body and original9360 causal ball; no whole route or24.',
        'Original .12m/.20rad endpoint, .22m complete current-state200-step braking tube/.15m actual, legal control/slew/contact/root guards, fixed predicted-reference rear2cm/yaw.1rad/time.2s membership, complete200 applied zero tail, own replay and complete pair full state/control/mocap<=1e-8. Passing applies only to this finite saved component. Model error assumptions do not prove universal future response, recursive safety or real-time operation.',
        'Counts: '+json.dumps(rows,ensure_ascii=False)+'.',
        'Unexecuted: '+json.dumps(summary['unexecuted'])+'. Actual originalRPP full9390 qualification='+str(summary['passed'])+'; original full32210 V1383 is separately qualified. An original-route batch still requires its own preregistration and event-based integration.'])+'\n'
    (O/'REPORT.md').write_text(report);(R/'docs/FULL9390_ACTUAL_V1396_REPORT.md').write_text(report)
    with (R/'RESEARCH_STATUS.md').open('a') as stream:stream.write('\n- V1396原9390完整前进段实际main/repeat全门='+str(summary['passed'])+'，未执行'+str(summary['unexecuted'])+'，原RPP/真实扫描/固定响应/完整200尾/源状态审核结果按保存记录，非原整路或24。docs/FULL9390_ACTUAL_V1396_REPORT.md。\n')
    inventory=load('full9390_archive_inventory',R/'experiments/v1391_handoff_archive_recovery/archive.py').inventory
    archive_io=load('full9390_archive_io',R/'experiments/v1382_weekend_campaign/storage_preserve.py')
    paths=set()
    for root in [C,O,RAW]:
        paths.update(p for p in root.rglob('*') if (p.is_file() or p.is_symlink()) and '__pycache__' not in p.parts)
    paths.update([R/'docs/FULL9390_ACTUAL_V1396_REPORT.md',R/'runs/v1393_full9390_preparation/PREDICTED_RESPONSE.npz',R/'runs/v1393_full9390_preparation/FIXED_INPUTS.json',R/'runs/v1393_full9390_preparation/ANALYSIS_RESULT.json'])
    items=inventory(sorted(paths),read(C/'SOURCE_FREEZE.json')['files']);wanted={x['path']:x for x in items};directory=O/'archive';directory.mkdir(exist_ok=False);before=archive_io.usage()
    class BoundedParts(archive_io.Parts):
        def write(self,data):
            assert before+self.total+len(data)+4*1024**2<10*1024**3,'TOTAL_TEMPORARY_ARCHIVE_CAP'
            return super().write(data)
    writer=BoundedParts(directory,'v1396-full9390')
    with gzip.GzipFile(fileobj=writer,mode='wb',compresslevel=3,mtime=0) as compressor,tarfile.open(fileobj=compressor,mode='w|') as archive:
        for row in items:
            member=tarfile.TarInfo(row['path'])
            if 'symlink' in row:member.type=tarfile.SYMTYPE;member.linkname=row['symlink'];archive.addfile(member)
            else:
                member.size=row['bytes']
                with (R/row['path']).open('rb') as stream:archive.addfile(member,stream)
    writer.finish();whole=hashlib.sha256();parts=[]
    for row in writer.parts:
        p=directory/row['name'];assert row['bytes']<=32*1024**2 and archive_io.sha(p)==row['sha256'];parts.append(p)
        with p.open('rb') as stream:
            for block in iter(lambda:stream.read(1024**2),b''):whole.update(block)
    assert whole.hexdigest()==writer.digest.hexdigest();seen=set()
    with tarfile.open(fileobj=archive_io.Reader(parts),mode='r|gz') as archive:
        for member in archive:
            assert member.name in wanted and member.name not in seen;row=wanted[member.name]
            if 'symlink' in row:assert member.issym() and member.linkname==row['symlink']
            else:
                assert member.isfile() and member.size==row['bytes'];h=hashlib.sha256();stream=archive.extractfile(member)
                for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
                assert h.hexdigest()==row['sha256']
            seen.add(member.name)
    assert seen==set(wanted) and sources()
    dump(O/'ARCHIVE_INDEX.json',dict(files=items,parts=writer.parts,archive_bytes=writer.total,archive_sha256=writer.digest.hexdigest(),local_members_and_reassembly_verified=True,remote_download_restore_verified=False,raw_deleted=False,models=0))
    dump(O/'FINALIZED.json',dict(passed=True,full9390_pair_passed=summary['passed'],local_memberSHA_and_reassembly_verified=True,source_unchanged=True,models=0))
    ledger=read(DAY/'LEDGER.json');record=next(x for x in ledger['rounds'] if x['id']==C.name);record.update(status='CLOSED',closed=True,finalized=True,full9390_handoff_qualified=summary['passed'],archive_index=str((O/'ARCHIVE_INDEX.json').relative_to(R)));ledger['latest_9390_handoff_qualified']=summary['passed']
    fields={'actual_total_native':'actual_total_native','historical_reconstruction_native':'historical_reconstruction_native','new_component_native':'new_component_native','own_replay_native':'own_replay_native','native_analytical_native':'native_analytical_native','independent_audit_analytical_native':'audit_analytical_native','canonical_vehicle_initializations':'canonical_vehicle_initializations'}
    for total,key in fields.items():
        if all(x[key] is not None for x in rows):ledger[total]=ledger.get(total,0)+sum(x[key] for x in rows)
        else:ledger[total+'_additional_unknown_tasks']=[x['task'] for x in rows if x[key] is None]
    dump(DAY/'LEDGER.json',ledger)
    pointer=read(R/'CURRENT_EXPERIMENT.json');pointer['latest_v1396'].update(full9390_handoff_qualified=summary['passed'],finalized=True);dump(R/'CURRENT_EXPERIMENT.json',pointer)
    with (O/'sync.console').open('x') as log:p=subprocess.run([sys.executable,'-B',str(C/'sync_results.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=120)
    dump(O/'SYNC_WORKER_EXIT.json',dict(returncode=p.returncode,models=0))
    if (O/'SYNC_RESULT.json').exists() and read(O/'SYNC_RESULT.json').get('remote_verified'):
        with (O/'delivery.console').open('x') as log:p=subprocess.run([sys.executable,'-B',str(R/'experiments/v1382_weekend_campaign/deliver_round.py'),str(O.relative_to(R))],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=900)
        dump(O/'DELIVERY_WORKER_EXIT.json',dict(returncode=p.returncode,models=0))
if __name__=='__main__':main()
