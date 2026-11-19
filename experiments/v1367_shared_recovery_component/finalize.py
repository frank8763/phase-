"""One zero-model component accounting/report and full local archive readback."""
import csv
import fcntl
import hashlib
from pathlib import Path
import subprocess
import sys
import tarfile
import time
from component_context import *


def file_sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda:f.read(1048576),b''):h.update(data)
    return h.hexdigest()


def main():
    assert not (O/'FINALIZED.json').exists();summary=read(O/'COMPLETION.json');assert summary['closed']
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert (R/'REVIEW_PENDING').read_bytes()==(O/'REVIEW_PENDING.before').read_bytes()
    rows=[]
    for row in summary['results']:
        task=next(t for t in read(C/'TASKS.json') if t['task_id']==row['task']);out=Path(task['output'])
        native=row.get('native') or (read(out/'RESULT.json') if (out/'RESULT.json').exists() else {})
        rows.append(dict(task=row['task'],branch=task['branch'],role=task['role'],passed=row.get('passed',False),
            initializations=native.get('canonical_vehicle_initializations'),historical_prefix_native=native.get('historical_prefix_replay_native'),
            new_component_native=native.get('new_component_native'),actual_total_native=native.get('actual_total_native',native.get('new_actual_native')),
            own_full_trace_replay_native=native.get('own_replay_native'),private_native=0,goal_distance_m=native.get('whole_goal_distance_m'),
            source_unchanged=native.get('source_unchanged'),error=native.get('error')))
    dump(O/'ACCOUNTING.json',dict(rows=rows,unexecuted=summary['unexecuted'],
        exact_historical_native=sum(z['historical_prefix_native'] for z in rows if isinstance(z['historical_prefix_native'],int)),
        exact_new_component_native=sum(z['new_component_native'] for z in rows if isinstance(z['new_component_native'],int)),
        unknown_component_counts=[z['task'] for z in rows if z['new_component_native'] is None],
        new_navigation_trials=0,models_during_closure=0))
    report=['# V1367 shared RPP/MPPI safe recovery component','',f"Closed: {summary.get('stop_reason')}. Complete component scope passed: {summary['passed']}.",'',
        '|Task|Passed|Historical prefix|New component|Full own replay|Component goal distance|','|---|---|---:|---:|---:|---:|']
    report.extend(f"|{z['task']}|{z['passed']}|{z['historical_prefix_native']}|{z['new_component_native']}|{z['own_full_trace_replay_native']}|{z['goal_distance_m']}|" for z in rows)
    report.extend(['','Unexecuted: '+', '.join(summary['unexecuted']),'',
        'Each task reconstructs original15105native history from true t0, then tracks the same safe first recovery segment with actual installed RPP or engineering coherent MPPI. Historical restoration is not new navigation. Unknown counts remain unknown. No root/time rewrite, truth-to-policy, training, new seed or new scene. Full qpos/qvel/ctrl/mocap/contact own replay and every independent gate required.',
        'Passing these components is not full dynamic arrival, fixed24 confirmation, fair statistical superiority or realtime/hardware validation. Original prior results/failures and expired17:00 window unchanged. This separately authorized window never extends.','',
        'Raw and selected archive remain local until downloaded remote SHA/member/restore verification. One new-round bounded30s push and5s readonly verification only.'])
    text='\n'.join(report).rstrip()+'\n';(O/'REPORT.md').write_text(text);(R/'docs/SHARED_RECOVERY_COMPONENT_V1367_REPORT.md').write_text(text)
    directory=O/'archive';directory.mkdir(exist_ok=False);items=[]
    for root in [C,O,RAW]:
        for p in sorted(root.rglob('*')):
            if directory in p.parents:continue
            if p.is_symlink():
                assert p.name=='meshes_fixed';items.append(dict(path=str(p.relative_to(R)),symlink=str(p.readlink())))
            elif p.is_file():items.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=file_sha(p)))
    assert len({z['path'] for z in items})==len(items)
    assert sum(z.get('bytes',0) for z in items)*3<2*1024**3
    archive=directory/'evidence.tar.gz'
    with tarfile.open(archive,'w:gz',compresslevel=3,dereference=False) as f:
        for item in items:f.add(R/item['path'],arcname=item['path'],recursive=False)
    wanted={z['path']:z for z in items};seen=set()
    with tarfile.open(archive,'r:gz') as f:
        for member in f:
            item=wanted[member.name];assert member.name not in seen;seen.add(member.name)
            if 'symlink' in item:assert member.issym() and member.linkname==item['symlink']
            else:
                stream=f.extractfile(member);h=hashlib.sha256()
                for data in iter(lambda:stream.read(1048576),b''):h.update(data)
                assert h.hexdigest()==item['sha256']
    assert seen==set(wanted);parts=[]
    with archive.open('rb') as f:
        for i in range(1000):
            data=f.read(32*1024**2)
            if not data:break
            part=directory/('evidence.tar.gz.part%03d'%i);part.write_bytes(data);parts.append(dict(name=part.name,bytes=len(data),sha256=file_sha(part)))
    h=hashlib.sha256()
    for part in parts:
        p=directory/part['name'];assert file_sha(p)==part['sha256']
        with p.open('rb') as f:
            for data in iter(lambda:f.read(1048576),b''):h.update(data)
    assert h.hexdigest()==file_sha(archive) and sources()
    dump(O/'ARCHIVE_INDEX.json',dict(files=items,parts=parts,archive_sha256=file_sha(archive),archive_bytes=archive.stat().st_size,
        local_members_and_reassembly_verified=True,remote_download_restore_verified=False,raw_deleted=False,models=0))
    dump(O/'FINALIZED.json',dict(passed=True,component_scope_passed=summary['passed'],local_memberSHA_and_reassembly_verified=True,
        whole_dynamic_goal_passed=False,source_unchanged=True,models=0,raw_deleted=False,finished_unix=time.time()))
    with (O/'sync.console').open('x') as log:p=subprocess.run([sys.executable,'-B',str(C/'sync_results.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=120)
    dump(O/'SYNC_WORKER_EXIT.json',dict(returncode=p.returncode,models=0))
    return 0


if __name__=='__main__':raise SystemExit(main())
