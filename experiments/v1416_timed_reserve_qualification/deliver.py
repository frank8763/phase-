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

R=Path(__file__).resolve().parents[2];O=R/'runs/v1416_timed_reserve_qualification';TAG='phase-v1416-current-timed-reserve-qualified-20261121'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
h=load('v1401_bounded_delivery',R/'experiments/v1389_idempotent_storage_transfer/resume.py');h.O=O/'remote_delivery';h.W=h.O;h.base.TAG=TAG
Reader=load('v1401_original_stream_reader',R/'experiments/v1382_weekend_campaign/deliver_full9390_preparation.py').RemoteReader
verify=load('v1401_qualified_link_stream_verifier',R/'experiments/v1400_archive_link_schema/resume.py').verify_stream


def sync():
    assert not(O/'SYNC_CLAIM.json').exists();head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();h.dump(O/'SYNC_CLAIM.json',dict(head=head,unix=time.time(),models=0,one_push_only=True))
    proof=dict(head=head,remote_verified=False,models=0,retry_allowed=False)
    try:
        p=subprocess.run(['git','push','origin','HEAD:main'],cwd=R,capture_output=True,text=True,timeout=30);proof['push_returncode']=p.returncode
        p=subprocess.run(['git','ls-remote','origin','refs/heads/main'],cwd=R,capture_output=True,text=True,timeout=5);proof['remote_verified']=p.returncode==0 and p.stdout.split()[0]==head
    except subprocess.TimeoutExpired as exc:proof['error']='BOUNDED_SYNC_TIMEOUT_'+str(exc.timeout)
    h.dump(O/'SYNC_RESULT.json',proof);print(json.dumps(proof))


def deliver():
    sync_result=h.read(O/'SYNC_RESULT.json');assert sync_result['remote_verified']and not h.O.exists();assert h.read(O/'FINALIZED.json')['passed']
    assert h.base.usage()+64*1024**2<10*1024**3
    h.O.mkdir();h.dump(h.O/'CLAIM.json',dict(pid=os.getpid(),unix=time.time(),source_head=sync_result['head'],models=0))
    try:
        request=h.O/'CREATE_RELEASE.json';h.dump(request,dict(tag_name=TAG,target_commitish=sync_result['head'],name='Phase current timed reserve qualified; full branch saved before gate',body='Bound current timed reserve qualification passed:400 exact analytical steps,2 explicit Predictors,callback200 vs independentfresh200 all state/control error0,tube0.224976416839. Complete branch/proof saved before admission; zero physics/navigation. Unified full causal snapshot/method/geometry source and production zero-model refusal/partial save checks included; all original failed rounds preserved. Not full finite response or physical/whole-route admission.',draft=False,prerelease=False,make_latest='false'))
        release=json.loads(h.base.gh(['api','--method','POST','repos/frank8763/phase-/releases','--input',str(request)],timeout=90));h.dump(h.O/'RELEASE.json',dict(id=release['id'],url=release['html_url']))
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
