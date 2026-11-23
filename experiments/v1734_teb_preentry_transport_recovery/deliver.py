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

R=Path(__file__).resolve().parents[2];O=R/'runs/v1734_teb_preentry_transport_recovery';I=R/'runs/v1731_teb_runtime_recovery';TAG='phase-v1730-teb-runtime-source-20261123'
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



def deliver():
    sync_result=h.read(O/'SYNC_RESULT.json');assert sync_result['remote_verified']and not h.O.exists();assert h.read(I/'FINALIZED.json')['passed']
    assert h.base.usage()+(32+512)*1024**2<15*1024**3
    h.O.mkdir();h.dump(h.O/'CLAIM.json',dict(pid=os.getpid(),unix=time.time(),source_head=sync_result['head'],models=0,input_archive_index_sha256=h.sha(I/'ARCHIVE_INDEX.json'),original_sync_sha256=h.sha(O/'SYNC_RESULT.json'),new_IO_deadline_unix=DEADLINE,new_IO_monotonic_deadline=START_MONO+600,boot_id=BOOT,no_new_push_or_reseal=True))
    try:
        request=h.O/'CREATE_RELEASE.json';h.dump(request,dict(tag_name=TAG,target_commitish=sync_result['head'],name='Phase TEB pre-entry transport closure',body='Exact original TEB native runtime binding and pre-entry source ref timeout (compiler/loader/SOURCE all unexecuted),0optimizer/model/physics/replay or control outputs. Original RESULT/console/closedreview determine true builddependency outcome; buildrefusal is algorithm UNEXECUTED, not method failure. Exact author Gitblob/size/SHA and all retained source/build artifacts. Shared measuredclock/closure qualification referenced separately; no old DWA re-audit/replay/retry. New source Git containing exact build namespace/owner/IO source, runtime refonly/no secondpush. Actualremote everyblock/member/whole/indexSHA then exactduplicate transportcleanup.',draft=False,prerelease=False,make_latest='false'))
        lookup=subprocess.run([str(R/'tools/phase_storage_20261107/vendor/gh'),'api','repos/frank8763/phase-/releases/tags/'+TAG],cwd=R,capture_output=True,text=True,timeout=30)
        h.dump(h.O/'RELEASE_LOOKUP.json',dict(returncode=lookup.returncode,confirmed_missing=lookup.returncode!=0 and '404'in lookup.stderr,models=0))
        if lookup.returncode==0:
            release=json.loads(lookup.stdout);assert release['target_commitish']==sync_result['head'],'EXISTING_RELEASE_SOURCE_CONFLICT'
        else:
            assert '404'in lookup.stderr,'RELEASE_ABSENCE_NOT_CONFIRMED'
            release=json.loads(h.base.gh(['api','--method','POST','repos/frank8763/phase-/releases','--input',str(request)],timeout=90))
        h.dump(h.O/'RELEASE.json',dict(id=release['id'],url=release['html_url']))
        index=h.read(I/'ARCHIVE_INDEX.json')
        for row in index['parts']:h.ensure_uploaded(I/'archive'/row['name'],h.assets(h.read(h.O/'RELEASE.json')))
        h.ensure_uploaded(I/'ARCHIVE_INDEX.json',h.assets(h.read(h.O/'RELEASE.json')));known=h.assets(h.read(h.O/'RELEASE.json'))
        folder=h.O/'readback';folder.mkdir();reader=Reader(index['parts'],known,folder,h.download);count=verify(reader,index)
        assert len(reader.verified)==len(index['parts'])
        recovered=folder/'ARCHIVE_INDEX.json';h.download(recovered,known['ARCHIVE_INDEX.json']);assert h.sha(recovered)==h.sha(I/'ARCHIVE_INDEX.json')
        late=O/'late';late.mkdir()
        (late/'V1734_DELIVERY_HELPER.py.txt').write_bytes(Path(__file__).read_bytes())
        h.dump(late/'V1734_SCOPE.json',dict(scope='FIRST_TRANSPORT_WORKER_FOR_SEALED_PREENTRY_ARCHIVE',original_source_sync_timeout_retained=True,original_runtime_ref_timeout_retained=True,immutable_commit_actual_API_proof_sha256=h.sha(I/'PREENTRY_REMOTE_REF_PROOF.json'),no_second_push_or_ref_or_archive=True,late_helper_outside_original_archive=True,models=0))
        if (O/'PRECLAIM_ADAPTER_ERROR.json').exists():(late/'V1734_PRECLAIM_ADAPTER_ERROR.json').write_bytes((O/'PRECLAIM_ADAPTER_ERROR.json').read_bytes())
        rows=[dict(name=p.name,bytes=p.stat().st_size,sha256=h.sha(p))for p in sorted(late.iterdir())]
        h.dump(late/'V1734_LATE_INDEX.json',dict(files=rows,original_archive_index_sha256=h.sha(I/'ARCHIVE_INDEX.json')))
        for p in sorted(late.iterdir()):h.ensure_uploaded(p,h.assets(h.read(h.O/'RELEASE.json')))
        known=h.assets(h.read(h.O/'RELEASE.json'))
        for p in sorted(late.iterdir()):
            recovered_late=folder/p.name;h.download(recovered_late,known[p.name]);assert h.sha(recovered_late)==h.sha(p);recovered_late.unlink()
        proof=dict(passed=True,source_commit=sync_result['head'],release_url=release['html_url'],every_asset_actual_download_SHA=True,every_member_SHA_and_link_text=True,whole_archive_SHA=True,recovery_index_download_SHA=True,members=count,archive_bytes=index['archive_bytes'],every_late_asset_and_index_actual_download_SHA=True,immutable_source_commit_proof_only_no_current_ref_retry=True,models=0,physical_admission=False,verified_unix=time.time())
        h.dump(O/'FULL_REMOTE_VERIFIED.json',proof)
        entries=[]
        for row in index['parts']:
            path=I/'archive'/row['name'];st=path.lstat();assert path.is_file()and not path.is_symlink()and st.st_size==row['bytes']and h.sha(path)==row['sha256']
            entries.append(dict(path=str(path.relative_to(R)),sha256=row['sha256'],bytes=st.st_size,device=st.st_dev,inode=st.st_ino,mtime_ns=st.st_mtime_ns))
        h.dump(O/'TRANSPORT_CLEANUP_MANIFEST.json',dict(verified_remote_proof_sha256=h.sha(O/'FULL_REMOTE_VERIFIED.json'),entries=entries))
        for row in entries:
            path=R/row['path'];st=path.lstat();assert (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)==(row['device'],row['inode'],row['bytes'],row['mtime_ns'])and h.sha(path)==row['sha256'];path.unlink()
        recovered.unlink();folder.rmdir();h.dump(O/'TRANSPORT_CLEANUP.json',dict(passed=True,only_remote_verified_duplicate_transport_removed=True,archive_bytes=index['archive_bytes'],all_original_qualification_inputs_and_outputs_retained=True,exact_SHA_size_mtime_device_inode_manifest=True,cleanup_unix=time.time(),models=0));h.dump(h.O/'FINALIZED.json',proof)
    except BaseException as exc:h.dump(h.O/'ERROR.json',dict(error=repr(exc),traceback=traceback.format_exc(),unverified_originals_retained=True,models=0));raise


if __name__=='__main__':
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    assert len(sys.argv)==1
    deliver()
