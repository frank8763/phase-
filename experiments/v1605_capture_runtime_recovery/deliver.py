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

R=Path(__file__).resolve().parents[2];O=R/'runs/v1605_capture_runtime_recovery';TAG='phase-v1603-current-capture-freshness-refused-20261122'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
h=load('v1401_bounded_delivery',R/'experiments/v1389_idempotent_storage_transfer/resume.py');h.O=O/'remote_delivery';h.W=h.O;h.base.TAG=TAG
Reader=load('v1401_original_stream_reader',R/'experiments/v1382_weekend_campaign/deliver_full9390_preparation.py').RemoteReader
verify=load('v1401_qualified_link_stream_verifier',R/'experiments/v1400_archive_link_schema/resume.py').verify_stream


def sync():
    assert not(O/'SYNC_CLAIM.json').exists()
    head='3a391cafbb43b65d7c41d29a84a94c4328930b65'
    h.dump(O/'SYNC_CLAIM.json',dict(head=head,unix=time.time(),models=0,maximum_ref_s=5,no_retry=True,push_executed=False))
    proof=dict(head=head,remote_verified=False,models=0,retry_allowed=False,push_executed=False,source_reused_from_V1604=True)
    try:
        ref=subprocess.run(['git','ls-remote','origin','refs/heads/main'],cwd=R,capture_output=True,text=True,timeout=5)
        proof['remote_verified']=ref.returncode==0 and ref.stdout.split()[0]==head
    except subprocess.TimeoutExpired:proof['error']='BOUNDED_REF_TIMEOUT'
    h.dump(O/'SYNC_RESULT.json',proof);print(json.dumps(proof))


def deliver():
    sync_result=h.read(O/'SYNC_RESULT.json');assert sync_result['remote_verified']and not h.O.exists();assert h.read(O/'FINALIZED.json')['passed']
    assert h.base.usage()+(32+512)*1024**2<15*1024**3
    h.O.mkdir();h.dump(h.O/'CLAIM.json',dict(pid=os.getpid(),unix=time.time(),source_head=sync_result['head'],models=0))
    try:
        request=h.O/'CREATE_RELEASE.json';h.dump(request,dict(tag_name=TAG,target_commitish=sync_result['head'],name='Phase actual5995 current capture source-age refusal',body='V1603 originalWE/RPP5995actual=5520originalRPP+475publicprefixzero/5996completeNplus1 gap0. RealCUSP complete5995history and1631causalrow content then finalwire_age_after_capture>200ms refused. Exactfinalage notsaved. Init1/internalmodelsunknown,0newmethod12private/current2200/bridge/Allocator/replay;full200tailfalse/error0. OriginalBYTE_GRANT_EXPIRED failure-save/tail/phase secondary retained in completeRESULT. Finalappendjournal1632rows2521709B wholeSHA/close passed,original24MiBROS writer11854812B/ROS_RESULTclosed/controllerexittrue. Prefixtelemetry not independentSafetyPASS,whole0/science12. Fullraw/source/errors kept;source3a391caf/refonly/no secondpush. Allremote block/member/whole/indexSHA before exact duplicate transport cleanup.',draft=False,prerelease=False,make_latest='false'))
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
