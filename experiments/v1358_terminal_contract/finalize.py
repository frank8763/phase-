"""Offline zero-model report, source/raw archive and full local SHA readback."""
import csv
import fcntl
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
import time
from component_context import R,C,O,RAW,read,dump,sources


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1048576),b''):h.update(chunk)
    return h.hexdigest()


def main():
    assert not (O/'FINALIZED.json').exists(),'ONE_OFFLINE_CLOSURE'
    assert read(O/'COMPLETION.json')['closed']
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert (R/'REVIEW_PENDING').read_bytes()==(O/'REVIEW_PENDING.before').read_bytes()
    summary=read(O/'COMPLETION.json');rows=[];items=[]
    for row in summary['results']:
        task=next(t for t in read(C/'TASKS.json') if t['task_id']==row['task']);out=Path(task['output'])
        native=row.get('native') or {};physical=native.get('physical',{})
        actual=native.get('new_actual_native');replay=native.get('own_replay_native')
        lower=read(out/'PARTIAL.json').get('native',0) if (out/'PARTIAL.json').exists() else 0
        rows.append(dict(task=row['task'],branch=row['branch'],stage=row['stage'],role=row['role'],classification=row.get('classification','OPERATION_OR_EVIDENCE_STOP'),passed=row['passed'],actual_native=actual if actual is not None else 'unknown',actual_recorded_lower_bound=lower,own_replay_native=replay if replay is not None else 'unknown',goal_distance_m=physical.get('goal_distance_m'),minimum_actual_clearance_m=physical.get('minimum_actual_clearance_m'),bad_contacts=physical.get('bad_contacts'),first_actor_detection=physical.get('first_actor_detection'),worker_wall_s=native.get('wall_s')))
        for p in sorted(out.rglob('*')):
            if p.is_symlink():
                assert p.name=='meshes_fixed' and str(p.readlink())=='/home/linghu/catkin_ws/src/mk-mini/training/assets/mkmini_real/meshes_fixed'
                items.append(dict(path=str(p.relative_to(R)),kind='symlink',target=str(p.readlink()),bytes=len(str(p.readlink()).encode())))
            elif p.is_file() and 'cache' not in p.parts:items.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
    D=O/'offline_archive';D.mkdir()
    with (O/'TASK_ACCOUNTING.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]) if rows else ['task']);writer.writeheader();writer.writerows(rows)
    dump(O/'TASK_ACCOUNTING.json',dict(rows=rows,unexecuted=summary['unexecuted'],skipped_dependencies=summary['skipped_dependencies'],exact_actual_total=sum(x['actual_native'] for x in rows if isinstance(x['actual_native'],int)),unknown_actual_tasks=[x['task'] for x in rows if x['actual_native']=='unknown'],exact_replay_total=sum(x['own_replay_native'] for x in rows if isinstance(x['own_replay_native'],int)),unknown_replay_tasks=[x['task'] for x in rows if x['own_replay_native']=='unknown'],models_for_closure=0))
    report=['# 2026-11-19 bodygoal and terminal recovery consistency','',f"Closed: {summary['stop_reason']}. New root stops2026-11-19 17:00+0800 in ROUND_WINDOW;2GiB, all old deadlines unchanged. Frozen branch sources, no automatic tuning.",'','|Task|Result|Actual native|Own replay|Goal distance|','|---|---|---:|---:|---:|']
    report.extend(f"|{x['task']}|{x['classification']}|{x['actual_native']}|{x['own_replay_native']}|{x['goal_distance_m']}|" for x in rows)
    report.extend(['','Unexecuted: '+', '.join(summary['unexecuted']),'','Two fixed terminal variants on one exposedWE course; originalV1357staticpair reused and not counted anew. All old failures unchanged. Repeats not independent samples. Dynamic task uses causal publicmap/range occupancy and renewed exactfootprintlattice proposals pluslocalcontroller; no hiddenactortruth orRPCCRglobal guarantee. This is finite engineering development, not fixed24/newgeneralization/real-time or algorithm-superiority evidence. PriorRPCCRV1281fixed24success unchanged. Complete ownstate/control/contact replay and all audit gates required for each reported pass. Unknown counts explicitly retained.','', 'Raw originals kept; this offline archive has local SHA verification only. No network needed for the run. GitHub transport/remoteSHA/restore before any cleanup.'])
    report.extend(['','New predictor conditions on .25m bounded excursion; PERIODIC also assumes .32rad/s and estimates unknown coefficients only from corrupted returns. This is stronger prior information than V1354 speed-only, not arbitrary-motion robustness. No actor anchor/axis/phase truth online. V1358 preserves200ms expiry and cooperative evidence; uses actual bodygoal and nondecreasing knownclearance monitor. NESTED_SWEEP is conservative allfuture occupancy under declared periodic class.',''])
    text='\n'.join(report).rstrip()+'\n';(R/'docs/TERMINAL_CONTRACT_V1358_REPORT.md').write_text(text);(O/'REPORT.md').write_text(text)
    # Include the exact new source tree and compact closure state too.
    for root in [C]:
        for p in sorted(root.rglob('*')):
            if p.is_file() and not p.is_symlink():items.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
    for name in ['COMPLETION.json','TASK_ACCOUNTING.json','TASK_ACCOUNTING.csv','REPORT.md','ROUND_WINDOW.json']:
        p=O/name;items.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
    # Preserve all zero-model actual-ROS closure attempts, including red logs.
    for folder in sorted(RAW.glob('close_fixture*')):
        for p in sorted(folder.rglob('*')):
            assert not p.is_symlink(),'UNEXPECTED_CLOSURE_FIXTURE_SYMLINK'
            if p.is_file():items.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
    existing={x['path'] for x in items}
    for p in sorted(O.rglob('*')):
        if D in p.parents or not p.is_file() or p.is_symlink():continue
        relative=str(p.relative_to(R))
        if relative not in existing:
            items.append(dict(path=relative,bytes=p.stat().st_size,sha256=sha(p)));existing.add(relative)
    assert items and len({x['path'] for x in items})==len(items)
    archive=D/'overnight-evidence.tar.gz'
    assert sum(x.get('bytes',0) for x in items)*3 < read(C/'CAMPAIGN_CONFIG.json')['storage_limit_bytes'],'ARCHIVE_RESERVE_EXCEEDED_KEEP_RAW'
    with tarfile.open(archive,'w:gz',compresslevel=3,dereference=False) as tar:
        for item in items:tar.add(R/item['path'],arcname=item['path'],recursive=False)
    wanted={x['path']:x for x in items};seen=set()
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            item=wanted[member.name];assert member.name not in seen;seen.add(member.name)
            if item.get('kind')=='symlink':assert member.issym() and member.linkname==item['target']
            else:
                h=hashlib.sha256();stream=tar.extractfile(member)
                for chunk in iter(lambda:stream.read(1048576),b''):h.update(chunk)
                assert h.hexdigest()==item['sha256']
    assert seen==set(wanted)
    parts=[]
    with archive.open('rb') as stream:
        while True:
            data=stream.read(32*1024**2)
            if not data:break
            p=D/('overnight-evidence.tar.gz.part%03d'%len(parts));p.write_bytes(data);parts.append(dict(name=p.name,bytes=len(data),sha256=sha(p)))
    h=hashlib.sha256()
    for p in parts:
        assert sha(D/p['name'])==p['sha256']
        with (D/p['name']).open('rb') as stream:
            for data in iter(lambda:stream.read(1048576),b''):h.update(data)
    assert h.hexdigest()==sha(archive)
    dump(O/'OFFLINE_ARCHIVE_INDEX.json',dict(files=items,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,parts=parts,local_all_members_SHA_verified=True,raw_deleted=False,remote_verified=False,models=0))
    assert sources(),'FROZEN_SOURCE_CHANGED'
    dump(O/'FINALIZED.json',dict(passed=True,scientific_branch_passed=summary['passed'],scope='zero-model local evidence closure only',source_unchanged=True,local_archive_all_member_and_reassembled_SHA_passed=True,remote_backup_pending=True,raw_deleted=False,models=0,finished_unix=time.time()))
    print(json.dumps(dict(finalized=True,local_members=len(items),parts=len(parts),models=0)))


if __name__=='__main__':main()
