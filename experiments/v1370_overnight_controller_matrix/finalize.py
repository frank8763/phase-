"""Zero-model complete accounting and streaming32MiB lossless archive readback."""
import fcntl
import gzip
import hashlib
import subprocess
import sys
import tarfile
import time
from component_context import *
from campaign import storage_bytes

def file_sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for data in iter(lambda:f.read(1048576),b''):h.update(data)
    return h.hexdigest()

class Parts:
    def __init__(self,directory,base,limit):self.directory=directory;self.base=base;self.limit=limit;self.parts=[];self.stream=None;self.size=0;self.total=0;self.digest=hashlib.sha256()
    def write(self,data):
        count=len(data);self.digest.update(data)
        while data:
            if self.stream is None:
                self.path=self.directory/('evidence.tar.gz.part%03d'%len(self.parts));self.stream=self.path.open('xb');self.size=0
            part=data[:32*1024**2-self.size];assert self.base+self.total+len(part)<self.limit-64*1024**2,'ARCHIVE_STORAGE_LIMIT'
            self.stream.write(part);self.size+=len(part);self.total+=len(part);data=data[len(part):]
            if self.size==32*1024**2:self.finish_part()
        return count
    def finish_part(self):
        if self.stream is not None:
            self.stream.close();self.parts.append(dict(name=self.path.name,bytes=self.size,sha256=file_sha(self.path)));self.stream=None
    def flush(self):
        if self.stream is not None:self.stream.flush()

class Reader:
    def __init__(self,paths):self.paths=iter(paths);self.stream=None
    def read(self,n):
        result=bytearray()
        while len(result)<n:
            if self.stream is None:
                path=next(self.paths,None)
                if path is None:break
                self.stream=path.open('rb')
            block=self.stream.read(n-len(result))
            if block:result.extend(block)
            else:self.stream.close();self.stream=None
        return bytes(result)

def main():
    assert not (O/'FINALIZED.json').exists();summary=read(O/'COMPLETION.json');assert summary['closed']
    with (R/'runs/v648_static_unknown/execution.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert (R/'REVIEW_PENDING').read_bytes()==(O/'REVIEW_PENDING.before').read_bytes()
    tasks={t['task_id']:t for t in read(C/'TASKS.json')};rows=[]
    for row in summary['results']:
        t=tasks[row['task']];native=row.get('native') or {};component=t['stage']=='component'
        rows.append(dict(task=row['task'],branch=t['branch'],stage=t['stage'],role=t['role'],candidate=t.get('candidate'),slot=t.get('slot'),classification=row.get('classification'),passed=row['passed'],
            canonical_vehicle_initializations=native.get('canonical_vehicle_initializations'),internal_factory_model_constructions=native.get('internal_factory_model_constructions'),
            actual_total_native=native.get('actual_total_native',native.get('new_actual_native')),historical_prefix_native=native.get('historical_prefix_replay_native',0),
            new_component_native=native.get('new_component_native') if component else 0,new_navigation_native=native.get('new_actual_native') if not component else 0,
            own_replay_native=native.get('own_replay_native'),goal_distance_m=native.get('whole_goal_distance_m'),error=native.get('error'),ros_error=(row.get('ros') or {}).get('error')))
    dump(O/'ACCOUNTING.json',dict(rows=rows,planned=len(tasks),attempted=len(rows),unexecuted=summary['unexecuted'],skipped_dependencies=summary['skipped_dependencies'],reused_not_new=['V1368_RPP_recovery_main'],models_during_closure=0,unknown_counts=[x['task'] for x in rows if x['actual_total_native'] is None or x['own_replay_native'] is None]))
    lines=['# V1370 overnight exposed-controller development matrix','',f"Closed: {summary.get('stop_reason')}; any complete dynamic development pair passed: {summary['passed']}.",'',
        f"Planned conditional tasks: {len(tasks)}; attempted: {len(rows)}; unexecuted: {len(summary['unexecuted'])}. Hard cutoff: 2026-11-20 09:00 +0800. Temporary campaign cap:10GiB.",'',
        '|Task|Stage|Classification|Actual native|Historical prefix|Own replay|Distance|','|---|---|---|---:|---:|---:|---:|']
    lines += [f"|{x['task']}|{x['stage']}|{x['classification']}|{x['actual_total_native']}|{x['historical_prefix_native']}|{x['own_replay_native']}|{x['goal_distance_m']}|" for x in rows]
    lines += ['', 'Ordinary safe complete functional failures advance other frozen branches; safety/control/source/evidence faults stop. Recovery/static success dependencies cannot be bypassed. Not fresh24 confirmation or statistical superiority. Adapted RPP three lookaheads and engineering coherent MPPI remain two controller families. All eight phases are original exposed WE cases, not new maps or independent confirmation. Historical reconstruction/repeats are counted separately. No training/hardware/Stage access.',
        'Exact physical state/control/contact own replay and the independent producer-runtime audit are mandatory. Unknown factory construction counts remain unknown. Raw files are retained until remote downloaded SHA/member/restore verification. Archive success is not scientific acceptance.']
    report='\n'.join(lines).rstrip()+'\n';(O/'REPORT.md').write_text(report);(R/'docs/OVERNIGHT_CONTROLLER_MATRIX_V1370_REPORT.md').write_text(report)
    with (R/'RESEARCH_STATUS.md').open('a') as f:f.write('\n- V1370夜间队列已闭：'+str(summary.get('stop_reason'))+'；实际尝试'+str(len(rows))+'、未执行'+str(len(summary['unexecuted']))+'，动态开发pair存在全门通过='+str(summary['passed'])+'；原八WE开发矩阵不是新24确认，所有分母/未知分账见docs/OVERNIGHT_CONTROLLER_MATRIX_V1370_REPORT.md。REVIEW_PENDING恢复，零模型归档/单次同步。\n')
    directory=O/'archive';directory.mkdir(exist_ok=False);items=[]
    for root in [C,O,RAW]:
        for p in sorted(root.rglob('*')):
            if directory in p.parents:continue
            if p.is_symlink():
                assert p.name=='meshes_fixed';items.append(dict(path=str(p.relative_to(R)),symlink=str(p.readlink())))
            elif p.is_file():items.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=file_sha(p)))
    assert len({x['path'] for x in items})==len(items);writer=Parts(directory,storage_bytes(),read(C/'CAMPAIGN_CONFIG.json')['storage_limit_bytes'])
    with gzip.GzipFile(fileobj=writer,mode='wb',compresslevel=3) as compressor, tarfile.open(fileobj=compressor,mode='w|') as archive:
        for item in items:
            info=tarfile.TarInfo(item['path'])
            if 'symlink' in item:info.type=tarfile.SYMTYPE;info.linkname=item['symlink'];archive.addfile(info)
            else:
                info.size=item['bytes']
                with (R/item['path']).open('rb') as f:archive.addfile(info,f)
    writer.finish_part();h=hashlib.sha256()
    for part in writer.parts:
        p=directory/part['name'];assert file_sha(p)==part['sha256']
        with p.open('rb') as f:
            for block in iter(lambda:f.read(1048576),b''):h.update(block)
    assert h.hexdigest()==writer.digest.hexdigest();wanted={x['path']:x for x in items};seen=set()
    with tarfile.open(fileobj=Reader([directory/x['name'] for x in writer.parts]),mode='r|gz') as archive:
        for member in archive:
            assert member.name in wanted and member.name not in seen;seen.add(member.name);item=wanted[member.name]
            if 'symlink' in item:assert member.issym() and member.linkname==item['symlink']
            else:
                digest=hashlib.sha256();stream=archive.extractfile(member)
                for block in iter(lambda:stream.read(1048576),b''):digest.update(block)
                assert digest.hexdigest()==item['sha256']
    assert seen==set(wanted) and sources()
    dump(O/'ARCHIVE_INDEX.json',dict(files=items,parts=writer.parts,archive_sha256=writer.digest.hexdigest(),archive_bytes=writer.total,local_members_and_reassembly_verified=True,remote_download_restore_verified=False,raw_deleted=False,models=0))
    dump(O/'FINALIZED.json',dict(passed=True,any_dynamic_development_pair_passed=summary['passed'],local_memberSHA_and_reassembly_verified=True,source_unchanged=True,raw_deleted=False,models=0,finished_unix=time.time()))
    with (O/'sync.console').open('x') as log:p=subprocess.run([sys.executable,'-B',str(C/'sync_results.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=120)
    dump(O/'SYNC_WORKER_EXIT.json',dict(returncode=p.returncode,models=0))
    return 0

if __name__=='__main__':raise SystemExit(main())
