"""New exact recovery of two pending closed archives; no old worker reruns."""
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

R=Path(__file__).resolve().parents[2]
C=Path(__file__).resolve().parent
O=R/'runs'/C.name
TAG='phase-v1556-closed-offline-transport-recovery-20261122'
GROUPS={'v1354':'runs/v1354_fast_stamped_pipeline','v1357':'runs/v1357_expiry_evidence_relay'}
REVIEW='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


h=load('v1556_existing_bounded_delivery',R/'experiments/v1389_idempotent_storage_transfer/resume.py')
h.O=O/'delivery';h.W=h.O;h.base.TAG=TAG
Reader=load('v1556_existing_stream_reader',R/'experiments/v1382_weekend_campaign/deliver_full9390_preparation.py').RemoteReader
verify=load('v1556_existing_member_verifier',R/'experiments/v1400_archive_link_schema/resume.py').verify_stream


def preflight():
    assert time.time()<1795395600
    parent=h.read(R/'runs/v1382_weekend_campaign/LEDGER.json')
    assert parent['active_round']is None and parent['active_math_round']is None and not parent['models_now_authorized']
    assert h.sha(R/'REVIEW_PENDING')==REVIEW
    with(R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert h.base.usage()+(32+4+512)*1024**2<10*1024**3,'CLOSED_TRANSPORT_READBACK_PEAK_REFUSED'
    return h.read(R/'runs/v1554_lossless_witness_stream/SOURCE_FREEZE.json')['files']


def plan():
    source=preflight();assert not(O/'PLAN.json').exists()
    assert all(h.sha(R/name)==value for name,value in source.items())
    tracked=set(subprocess.run(['git','ls-files','-z'],cwd=R,capture_output=True,check=True,timeout=10).stdout.decode().split('\0'))
    groups=[]
    for key,folder in GROUPS.items():
        original=R/folder/'OFFLINE_ARCHIVE_INDEX.json'
        index=h.read(original)
        assert index['local_all_members_SHA_verified']and not index['remote_verified']
        target=R/folder/'offline_archive/overnight-evidence.tar.gz'
        assert not target.is_symlink()and str(target.relative_to(R))not in source and str(target.relative_to(R))not in tracked
        stat=target.stat();assert stat.st_nlink==1 and stat.st_size==index['archive_bytes']and h.sha(target)==index['archive_sha256']
        parts=[];digest=hashlib.sha256()
        for row in index['parts']:
            path=R/folder/'offline_archive'/row['name']
            assert path.is_file()and not path.is_symlink()and path.stat().st_size==row['bytes']and h.sha(path)==row['sha256']
            with path.open('rb')as stream:
                for block in iter(lambda:stream.read(1024**2),b''):digest.update(block)
            parts.append(dict(name=key+'.'+row['name'],bytes=row['bytes'],sha256=row['sha256'],source=str(path.relative_to(R))))
        assert digest.hexdigest()==index['archive_sha256']
        groups.append(dict(id=key,original_index=str(original.relative_to(R)),original_index_sha256=h.sha(original),
            target=str(target.relative_to(R)),sha256=index['archive_sha256'],bytes=stat.st_size,
            allocated=stat.st_blocks*512,device=stat.st_dev,inode=stat.st_ino,mtime_ns=stat.st_mtime_ns,nlink=stat.st_nlink,
            archive_bytes=index['archive_bytes'],archive_sha256=index['archive_sha256'],parts=parts,files=index['files']))
    h.dump(O/'PLAN.json',dict(unix=time.time(),groups=groups,expected_allocated_release=sum(g['allocated']for g in groups),
        frozen_source_manifest_sha256=h.sha(R/'runs/v1554_lossless_witness_stream/SOURCE_FREEZE.json'),
        all_original_parts_and_raw_retained=True,not_current_input_or_recovery_anchor=True,models=0,remote_verified=False))


def deliver():
    source=preflight()
    assert not(h.O/'CLAIM.json').exists()
    assert h.read(R/'runs/v1554_lossless_witness_stream/CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
    expected=h.read(O/'PLAN.json')
    h.O.mkdir();h.dump(h.O/'CLAIM.json',dict(pid=os.getpid(),unix=time.time(),models=0,scope='EXISTING_CLOSED_ARCHIVE_BYTES_ONLY'))
    try:
        head=subprocess.run(['git','rev-parse','HEAD'],cwd=R,capture_output=True,text=True,check=True,timeout=5).stdout.strip()
        # Only the new source batch's already-pushed head is used. This worker
        # has no git push path and never restarts an old source transfer.
        sync=h.read(R/'runs/v1555_lossless_stream_source_recovery/SYNC_RESULT.json')
        assert sync['remote_verified'];head=sync['head']
        request=h.O/'CREATE_RELEASE.json'
        h.dump(request,dict(tag_name=TAG,target_commitish=head,name='Phase verified closed offline transport recovery',
            body='New recovery of exact closedV1354/V1357 offlinearchive bytes; no oldfinalizer/sourcepush/model/physics rerun. Alloriginalraw/parts retained; onlyredundant whole-tarcopies eligible afterfull actualremote block/member/whole/index SHA and exactstat protection. No science/navPASS.',draft=False,prerelease=False,make_latest='false'))
        command=[str(R/'tools/phase_storage_20261107/vendor/gh'),'api','repos/frank8763/phase-/releases/tags/'+TAG]
        lookup=subprocess.run(command,cwd=R,capture_output=True,text=True,timeout=30)
        h.dump(h.O/'RELEASE_LOOKUP.json',dict(returncode=lookup.returncode,confirmed_missing=lookup.returncode!=0 and '404'in lookup.stderr))
        if lookup.returncode==0:
            release=json.loads(lookup.stdout);assert release['target_commitish']==head
        else:
            assert '404'in lookup.stderr
            release=json.loads(h.base.gh(['api','--method','POST','repos/frank8763/phase-/releases','--input',str(request)],timeout=90))
        h.dump(h.O/'RELEASE.json',dict(id=release['id'],url=release['html_url']))
        links=O/'transport_links';links.mkdir()
        proofs=[]
        for group in expected['groups']:
            assert h.sha(R/group['original_index'])==group['original_index_sha256']
            index=dict(files=group['files'],parts=[{k:v for k,v in row.items()if k!='source'}for row in group['parts']],archive_bytes=group['archive_bytes'],archive_sha256=group['archive_sha256'],original_index_sha256=group['original_index_sha256'],models=0)
            index_path=O/(group['id']+'.INDEX.json');h.dump(index_path,index)
            for row in group['parts']:
                path=R/row['source'];assert h.sha(path)==row['sha256']and path.stat().st_size==row['bytes']
                dest=links/row['name'];assert not dest.exists();os.link(path,dest)
                assert dest.stat().st_ino==path.stat().st_ino and dest.stat().st_dev==path.stat().st_dev
                h.ensure_uploaded(dest,h.assets(h.read(h.O/'RELEASE.json')))
            h.ensure_uploaded(index_path,h.assets(h.read(h.O/'RELEASE.json')))
            known=h.assets(h.read(h.O/'RELEASE.json'))
            folder=h.O/(group['id']+'_readback');folder.mkdir()
            reader=Reader(index['parts'],known,folder,h.download)
            count=verify(reader,index)
            assert len(reader.verified)==len(index['parts'])
            recovered=folder/index_path.name;h.download(recovered,known[index_path.name]);assert h.sha(recovered)==h.sha(index_path)
            proof=dict(passed=True,group=group['id'],members=count,archive_bytes=index['archive_bytes'],
                every_asset_actual_download_SHA=True,every_member_SHA_and_link_text=True,whole_archive_SHA=True,
                recovery_index_download_SHA=True,index_sha256=h.sha(index_path),original_index_sha256=group['original_index_sha256'],
                release_url=release['html_url'],verified_unix=time.time(),models=0)
            h.dump(O/(group['id']+'.FULL_REMOTE_VERIFIED.json'),proof)
            recovered.unlink();folder.rmdir()
            for row in group['parts']:
                link=links/row['name'];assert h.sha(link)==row['sha256'];link.unlink()
            proofs.append(proof)
        links.rmdir()
        assert all(h.sha(R/name)==value for name,value in source.items())
        h.dump(O/'FULL_REMOTE_VERIFIED.json',dict(passed=True,groups=proofs,models=0,all_originals_retained=True))
    except BaseException as error:
        h.dump(O/'ERROR.json',dict(first_error=repr(error),traceback=traceback.format_exc(),models=0,unverified_originals_retained=True));raise


def clean():
    source=preflight();assert not(O/'CLEANUP_CLAIM.json').exists()
    full=h.read(O/'FULL_REMOTE_VERIFIED.json');assert full['passed']
    assert h.read(R/'runs/v1554_lossless_witness_stream/CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
    planned=h.read(O/'PLAN.json')
    tracked=set(subprocess.run(['git','ls-files','-z'],cwd=R,capture_output=True,check=True,timeout=10).stdout.decode().split('\0'))
    with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert h.sha(R/'REVIEW_PENDING')==REVIEW
        assert all(h.sha(R/name)==value for name,value in source.items())
        for group in planned['groups']:
            proof=h.read(O/(group['id']+'.FULL_REMOTE_VERIFIED.json'))
            assert proof['passed']and proof['original_index_sha256']==group['original_index_sha256']
            path=R/group['target'];assert not path.is_symlink()and path.resolve()==path and path.is_relative_to(R/'runs')
            assert group['target']not in source and group['target']not in tracked
            stat=path.stat()
            assert (stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_nlink)==(group['device'],group['inode'],group['bytes'],group['mtime_ns'],1)
            assert h.sha(path)==group['sha256']
        h.dump(O/'CLEANUP_CLAIM.json',dict(unix=time.time(),exact_targets=[g['target']for g in planned['groups']],models=0))
        for group in planned['groups']:(R/group['target']).unlink()
        h.dump(O/'CLEANUP_RESULT.json',dict(passed=True,allocated_bytes_released=planned['expected_allocated_release'],
            exact_files=[g['target']for g in planned['groups']],all_original_parts_and_raw_retained=True,
            remote_recovery_proof_sha256=h.sha(O/'FULL_REMOTE_VERIFIED.json'),models=0,remaining_allruns=h.base.usage()))


if __name__=='__main__':
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    assert sys.argv[1:]in [['--plan'],['--deliver'],['--clean']]
    {'--plan':plan,'--deliver':deliver,'--clean':clean}[sys.argv[1]]()
