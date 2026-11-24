"""One failed-model-round sync and complete bounded archive readback."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--assignment',required=True);parser.add_argument('--sync',action='store_true');arguments=parser.parse_args()
FORMAL=R/'runs/v1643_formal_parent_metadata'
registered=json.loads((FORMAL/'TASKS_LOCKED.json').read_text())
assert arguments.assignment in[a['assignment_id']for row in registered['tasks']if row['task']['case_id']=='EAST_WEST'for a in row['assignments']]
ROUND=FORMAL/'rounds'/arguments.assignment
_admission=json.loads((ROUND/'FORMAL_ADMISSION.json').read_text())
_source_relative=Path(_admission['source_version_root'])
assert not _source_relative.is_absolute() and '..' not in _source_relative.parts
SOURCE=R/_source_relative
assert SOURCE.parent==R/'runs' and SOURCE.name=='v1818_prefix_auditor_exact_source'
assert hashlib.sha256((SOURCE/'SOURCE_FREEZE.json').read_bytes()).hexdigest()==_admission['source_freeze_sha256']
O=R/'runs'/C.name/arguments.assignment;O.mkdir(parents=True,exist_ok=True)
TAG='phase-v1818-'+arguments.assignment.replace('__','-').replace('_','-')+'-runtime-20261124'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
h=load('v1401_bounded_delivery',R/'experiments/v1389_idempotent_storage_transfer/resume.py');h.O=O/'remote_delivery';h.W=h.O;h.base.TAG=TAG
Reader=load('v1401_original_stream_reader',R/'experiments/v1382_weekend_campaign/deliver_full9390_preparation.py').RemoteReader
verify=load('v1401_qualified_link_stream_verifier',R/'experiments/v1400_archive_link_schema/resume.py').verify_stream

# A NEW standalone600s I/O window; never modify old deadline files or model authority.
import signal
START_WALL=time.time();START_MONO=time.monotonic();BOOT=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
DEADLINE=START_WALL+600
h.END=DEADLINE;h.base.ROOT_END=DEADLINE
original_gh=h.base.gh;original_download=h.download

def guard():
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT
    assert time.time()<DEADLINE and time.monotonic()<START_MONO+600,'NEW_IO_DUAL_CLOCK_DEADLINE'

def bounded_gh(*args,**kwargs):
    guard();answer=original_gh(*args,**kwargs);guard();return answer

def bounded_download(*args,**kwargs):
    guard();answer=original_download(*args,**kwargs);guard();return answer

h.base.gh=bounded_gh;h.download=bounded_download
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('NEW_IO600_HARD_STOP')))
signal.setitimer(signal.ITIMER_REAL,600)





def sync():
    assert not(O/'SYNC_CLAIM.json').exists()
    recovery=h.read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']
    path=R/recovery['source_sync_result_path'];assert h.sha(path)==recovery['source_sync_result_sha256']
    proof=h.read(path);assert proof['remote_verified']and proof['head']==recovery['source_commit']
    h.dump(O/'SYNC_CLAIM.json',dict(head=proof['head'],unix=time.time(),models=0,push_executed=False,ref_executed=False,no_retry=True))
    h.dump(O/'SYNC_RESULT.json',dict(head=proof['head'],remote_verified=True,push_executed=False,ref_executed=False,reused_exact_original_source_sync=True,original_source_proof_path=str(path.relative_to(R)),original_source_proof_sha256=h.sha(path),models=0))
    print(json.dumps(proof))


def deliver():
    sync_result=h.read(O/'SYNC_RESULT.json')
    if not sync_result['remote_verified']:sync_result=h.read(O/'IMMUTABLE_SOURCE_RECOVERY.json')
    assert sync_result['remote_verified']and not h.O.exists();assert h.read(O/'FINALIZED.json')['passed']
    assert h.base.usage()+(32+512)*1024**2<15*1024**3
    h.O.mkdir();h.dump(h.O/'CLAIM.json',dict(pid=os.getpid(),unix=time.time(),source_head=sync_result['head'],models=0))
    try:
        request=h.O/'CREATE_RELEASE.json';h.dump(request,dict(tag_name=TAG,target_commitish=sync_result['head'],name='Phase one current-source first-event closed evidence',body='Closed registered originalV1281 phase-comparison assignment '+arguments.assignment+'. Preserve actual source/numerical/physical/replay/wholegoal outcomes andallfirst-secondary/unknown,notarchivePASSasscience. Fixed scientific tasks/variants/seed/phase unchanged.0new model/physics/replay inbackup. Unique NS source-sync proof reused by SHA; no second push/ref;allactualremote everyblock/member/whole/indexSHA beforeexactduplicatecleanup. Alloriginalsretained.',draft=False,prerelease=False,make_latest='false'))
        lookup=subprocess.run([str(R/'tools/phase_storage_20261107/vendor/gh'),'api','repos/frank8763/phase-/releases/tags/'+TAG],cwd=R,capture_output=True,text=True,timeout=30)
        h.dump(h.O/'RELEASE_LOOKUP.json',dict(returncode=lookup.returncode,confirmed_missing=lookup.returncode!=0 and '404'in lookup.stderr,models=0))
        if lookup.returncode==0:
            release=json.loads(lookup.stdout);assert release['target_commitish']==sync_result['head'],'EXISTING_RELEASE_SOURCE_CONFLICT'
        else:
            assert '404'in lookup.stderr,'RELEASE_ABSENCE_NOT_CONFIRMED'
            release=json.loads(h.base.gh(['api','--method','POST','repos/frank8763/phase-/releases','--input',str(request)],timeout=90))
        h.dump(h.O/'RELEASE.json',dict(id=release['id'],url=release['html_url']))
        index=h.read(O/'ARCHIVE_INDEX.json')
        for row in index['parts']:h.ensure_uploaded(O/'archive'/row['name'],h.assets(h.read(h.O/'RELEASE.json')))
        h.ensure_uploaded(O/'ARCHIVE_INDEX.json',h.assets(h.read(h.O/'RELEASE.json')));known=h.assets(h.read(h.O/'RELEASE.json'))
        folder=h.O/'readback';folder.mkdir();reader=Reader(index['parts'],known,folder,h.download);count=verify(reader,index)
        assert len(reader.verified)==len(index['parts'])
        recovered=folder/'ARCHIVE_INDEX.json';h.download(recovered,known['ARCHIVE_INDEX.json']);assert h.sha(recovered)==h.sha(O/'ARCHIVE_INDEX.json')
        proof=dict(passed=True,source_commit=sync_result['head'],release_url=release['html_url'],every_asset_actual_download_SHA=True,every_member_SHA_and_link_text=True,whole_archive_SHA=True,recovery_index_download_SHA=True,members=count,archive_bytes=index['archive_bytes'],models=0,physical_admission=False,verified_unix=time.time())
        h.dump(O/'FULL_REMOTE_VERIFIED.json',proof)
        entries=[]
        for row in index['parts']:
            path=O/'archive'/row['name'];st=path.lstat();assert path.is_file()and not path.is_symlink()and st.st_size==row['bytes']and h.sha(path)==row['sha256']
            entries.append(dict(path=str(path.relative_to(R)),sha256=row['sha256'],bytes=st.st_size,device=st.st_dev,inode=st.st_ino,mtime_ns=st.st_mtime_ns))
        h.dump(O/'TRANSPORT_CLEANUP_MANIFEST.json',dict(verified_remote_proof_sha256=h.sha(O/'FULL_REMOTE_VERIFIED.json'),entries=entries))
        for row in entries:
            path=R/row['path'];st=path.lstat();assert (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)==(row['device'],row['inode'],row['bytes'],row['mtime_ns'])and h.sha(path)==row['sha256'];path.unlink()
        recovered.unlink();folder.rmdir();h.dump(O/'TRANSPORT_CLEANUP.json',dict(passed=True,only_remote_verified_duplicate_transport_removed=True,archive_bytes=index['archive_bytes'],all_original_qualification_inputs_and_outputs_retained=True,exact_SHA_size_mtime_device_inode_manifest=True,cleanup_unix=time.time(),models=0));h.dump(h.O/'FINALIZED.json',proof)
    except BaseException as exc:h.dump(h.O/'ERROR.json',dict(error=repr(exc),traceback=traceback.format_exc(),unverified_originals_retained=True,models=0));raise


if __name__=='__main__':
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    if '--sync'in sys.argv:sync()
    else:deliver()
