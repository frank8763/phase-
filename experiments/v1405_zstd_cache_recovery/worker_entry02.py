"""Bounded zstd restore and exact obsolete-cache cleanup, zero models."""
import fcntl
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import time
import traceback

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
TAG='phase-closed-zstd-cache-recovery-20261121';HEAD='17813a5f4161f7a41a0cbff6df11436eb3497724'


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


h=load('v1399_bounded_transport',R/'experiments/v1389_idempotent_storage_transfer/resume.py')
h.O=O;h.W=O;h.base.TAG=TAG
reader_module=load('v1399_qualified_stream_reader',R/'experiments/v1382_weekend_campaign/deliver_full9390_preparation.py')
RemoteReader=reader_module.RemoteReader


def verify_stream(reader,index):
    arc=load('v1405_original_zstd_verifier',R/'experiments/v1065_preflight_metadata_continuation/archive.py')
    def provider(row):
        path=reader.folder/row['name'];asset=reader.assets[row['name']]
        assert asset['size']==row['bytes'] and asset['digest']=='sha256:'+row['sha256']
        reader.download(path,asset);reader.verified.append(row['name']);return path,True
    arc.verify(index,index['files'],provider)
    return len(index['files'])


def validate_sources(plan):
    assert all(h.sha(R/name)==sha for name,sha in plan['protected_source_hashes'].items()), 'PROTECTED_SOURCE_CHANGED'
    tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0'))
    protected_inodes={tuple(row) for row in plan['protected_inodes']}
    for group in plan['groups']:
        for row in group['parts']+group.get('raw_files',[]):
            path=R/row['path'];assert str(path.relative_to(R)) not in tracked and not path.is_symlink()
            if path.exists():
                st=path.stat();assert (st.st_dev,st.st_ino) not in protected_inodes
                assert [st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns]==row['stat'] and h.sha(path)==row['sha256'], 'TRANSPORT_ORIGINAL_CHANGED'


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));os.chdir(R)
    subprocess.run(['ionice','-c','3','-p',str(os.getpid())],check=True)
    assert not (O/'CLAIM.json').exists()
    plan=h.read(O/'PLAN.json');assert h.read(O/'QUALIFICATION.json')['passed']
    assert all(h.sha(R/name)==sha for name,sha in h.read(O/'SOURCE_FREEZE02.json')['files'].items())
    validate_sources(plan);parent=h.read(R/'runs/v1382_weekend_campaign/LEDGER.json')
    assert parent['active_round'] is None and (R/'REVIEW_PENDING').exists()
    assert h.base.usage()+64*1024**2<10*1024**3
    start=time.monotonic();deadline=min(start+10800,parent['hard_stop_monotonic']-10)
    h.END=min(time.time()+10800,1795395600);h.base.END=h.END
    original_gh=h.base.gh;original_download=h.download
    def check():
        assert time.monotonic()<deadline and time.time()<h.END, 'TRANSPORT_DUAL_CLOCK_STOP'
        assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==parent['boot_id']
    def gh(*args,**kwargs):check();return original_gh(*args,**kwargs)
    def download(*args,**kwargs):check();return original_download(*args,**kwargs)
    h.base.gh=gh
    h.dump(O/'CLAIM.json',dict(pid=os.getpid(),started_unix=time.time(),hard_stop_monotonic=deadline,absolute_deadline_unix=h.END,models=0))
    completed=[]
    try:
        tag=json.loads(h.base.gh(['api',f'repos/frank8763/phase-/releases?per_page=100']))
        matches=[r for r in tag if r['tag_name']==TAG];assert len(matches)<=1
        if matches:release=matches[0]
        else:
            request=O/'CREATE_RELEASE.json';h.dump(request,dict(tag_name=TAG,target_commitish=HEAD,name='Phase closed zstd cache recovery',body='Zero-model closed zstd archive recovery. Original400MB assets and selected obsolete offline qualification cache; all actual part/member/reassembly/index restore required before exact approved cleanup, protected/current inputs and raw anchors preserved.',draft=False,prerelease=False,make_latest='false'))
            release=json.loads(h.base.gh(['api','--method','POST','repos/frank8763/phase-/releases','--input',str(request)],timeout=90))
        h.dump(O/'RELEASE.json',dict(id=release['id'],url=release['html_url']))
        for group in plan['groups']:
            check();name=group['name'];folder=O/name;folder.mkdir(exist_ok=False);links=folder/'upload';links.mkdir();readback=folder/'readback';readback.mkdir()
            assert h.sha(R/group['index_path'])==group['index_sha256'], 'ORIGINAL_INDEX_CHANGED'
            index=h.read(R/group['index_path']);assert h.sha(R/group['inventory_path'])==group['inventory_sha256'];index=dict(index,files=h.read(R/group['inventory_path'])['files']);remote_parts=[]
            for row in group['parts']:
                path=R/row['path'];linked=links/(name+'__'+path.name);os.link(path,linked)
                remote_parts.append(dict(name=linked.name,bytes=row['bytes'],sha256=row['sha256']))
            recovery=dict(index,parts=remote_parts,original_archive_index=group['index_path'],original_archive_index_sha256=group['index_sha256'])
            index_path=folder/(name+'__RECOVERY_INDEX.json');h.dump(index_path,recovery)
            for row in remote_parts:h.ensure_uploaded(links/row['name'],h.assets(h.read(O/'RELEASE.json')))
            h.ensure_uploaded(index_path,h.assets(h.read(O/'RELEASE.json')));known=h.assets(h.read(O/'RELEASE.json'))
            reader=RemoteReader(remote_parts,known,readback,download);count=verify_stream(reader,recovery)
            assert len(reader.verified)==len(remote_parts)
            recovered=readback/index_path.name;download(recovered,known[index_path.name]);assert h.sha(recovered)==h.sha(index_path)
            proof=dict(passed=True,release_url=release['html_url'],archive_sha256=index['archive_sha256'],archive_bytes=index['archive_bytes'],members=count,every_asset_actually_downloaded_SHA=True,every_member_SHA_or_link_text=True,recovery_index_download_SHA=True,models=0,physical_raw_deleted=False,verified_unix=time.time())
            h.dump(folder/'FULL_REMOTE_VERIFIED.json',proof)
            with (R/'runs/v648_static_unknown/execution.lock').open('r') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);current=h.read(R/'runs/v1382_weekend_campaign/LEDGER.json')
                assert current['active_round'] is None and h.sha(R/'REVIEW_PENDING')==current['review_pending_original_bytes_sha256']
                validate_sources(plan)
                h.dump(folder/'CLEANUP_CLAIM.json',dict(parts=group['parts'],raw_files=group.get('raw_files',[]),proof_sha256=h.sha(folder/'FULL_REMOTE_VERIFIED.json'),models=0))
                for row in group['parts']+group.get('raw_files',[]):(R/row['path']).unlink()
                for row in remote_parts:(links/row['name']).unlink()
            recovered.unlink();readback.rmdir();links.rmdir();h.dump(folder/'FINALIZED.json',dict(proof,only_plan_approved_verified_transport_and_offline_cache_removed=True))
            completed.append(name);h.dump(O/'PROGRESS.json',dict(completed=completed,remaining=[g['name'] for g in plan['groups'] if g['name'] not in completed],models=0))
        h.dump(O/'FINALIZED.json',dict(passed=True,completed=completed,runs_allocated_bytes=h.base.usage(),models=0,current_physical_anchors_deleted=False,obsolete_offline_cache_deleted_only_after_full_restore=True))
    except BaseException as exc:
        h.dump(O/'ERROR.json',dict(error=repr(exc),traceback=traceback.format_exc(),completed=completed,unverified_originals_retained=True,models=0));raise


if __name__=='__main__':main()
