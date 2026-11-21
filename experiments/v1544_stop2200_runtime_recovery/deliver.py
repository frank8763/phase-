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

R=Path(__file__).resolve().parents[2];O=R/'runs/v1544_stop2200_runtime_recovery';TAG='phase-v1542-original2200-current-stop-qualified-20261122'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
h=load('v1401_bounded_delivery',R/'experiments/v1389_idempotent_storage_transfer/resume.py');h.O=O/'remote_delivery';h.W=h.O;h.base.TAG=TAG
Reader=load('v1401_original_stream_reader',R/'experiments/v1382_weekend_campaign/deliver_full9390_preparation.py').RemoteReader
verify=load('v1401_qualified_link_stream_verifier',R/'experiments/v1400_archive_link_schema/resume.py').verify_stream


def sync():
    assert not(O/'SYNC_CLAIM.json').exists()
    original=h.read(R/'runs/v1543_stop_horizon_source_recovery/SYNC_RESULT.json')
    head=original['head'];assert original['remote_verified']and head=='28fc2d6a3e2649aa64d7ac860b23749641fdb588'
    h.dump(O/'SYNC_CLAIM.json',dict(head=head,unix=time.time(),models=0,ref_only_no_second_push=True))
    proof=dict(head=head,remote_verified=False,models=0,retry_allowed=False,push_executed=False)
    try:
        p=subprocess.run(['git','ls-remote','origin','refs/heads/main'],cwd=R,capture_output=True,text=True,timeout=5)
        proof['remote_verified']=p.returncode==0 and p.stdout.split()[0]==head
    except subprocess.TimeoutExpired:proof['error']='BOUNDED_REF_TIMEOUT_5'
    h.dump(O/'SYNC_RESULT.json',proof);print(json.dumps(proof))


def deliver():
    sync_result=h.read(O/'SYNC_RESULT.json');assert sync_result['remote_verified']and not h.O.exists();assert h.read(O/'FINALIZED.json')['passed']
    assert h.base.usage()+64*1024**2<10*1024**3
    h.O.mkdir();h.dump(h.O/'CLAIM.json',dict(pid=os.getpid(),unix=time.time(),source_head=sync_result['head'],models=0))
    try:
        request=h.O/'CREATE_RELEASE.json';h.dump(request,dict(tag_name=TAG,target_commitish=sync_result['head'],name='Phase saved-current original2200 stop-component qualified',body='V1542once saved-current original2200stop horizon under science9/baseobserverepoch8 qualified: CPP2200+independentfreshPython2200/all8arrayerrors0/tube.442958114752; currentfullperiodgeometry not originalqGeometry/search/actualqualification. InternalAllocatorconstructorunknown.0nominal/physical/replay/optimizer; no realtime claim. Current archive performs0newmodel work. Inherited original model and saved-actual recovery chains linked, not duplicated in full. No freshwire/actual policy/RPCCR-from-t0/whole-route admission. Source archive complete is not numerical or navigation PASS.',draft=False,prerelease=False,make_latest='false'))
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
        for row in index['parts']:assert h.sha(O/'archive'/row['name'])==row['sha256']
        for row in index['parts']:(O/'archive'/row['name']).unlink()
        recovered.unlink();folder.rmdir();h.dump(O/'TRANSPORT_CLEANUP.json',dict(passed=True,only_remote_verified_duplicate_transport_removed=True,archive_bytes=index['archive_bytes'],all_original_qualification_inputs_and_outputs_retained=True,models=0));h.dump(h.O/'FINALIZED.json',proof)
    except BaseException as exc:h.dump(h.O/'ERROR.json',dict(error=repr(exc),traceback=traceback.format_exc(),unverified_originals_retained=True,models=0));raise


if __name__=='__main__':
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    if '--sync'in sys.argv:sync()
    else:deliver()
