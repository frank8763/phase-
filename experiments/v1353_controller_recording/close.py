"""Zero-model closure of both software batches; archive and read back all raw."""
import fcntl
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
import time

R=Path(__file__).resolve().parents[2]
O=R/'runs/v1353_controller_recording'
E=R/'records/shared_controller_v1353_20261119'


def sha(data):return hashlib.sha256(data).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def main():
    E.mkdir(exist_ok=False)
    completion=json.loads((O/'COMPLETION.json').read_text())
    independent=json.loads((O/'INDEPENDENT_AUDIT.json').read_text())
    assert completion['passed'] and completion['closed'] and independent['passed']
    assert completion['models']==completion['physical_native']==0
    with (R/'runs/v648_static_unknown/execution.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
    frozen=json.loads((R/'experiments/v1353_controller_recording/SOURCE_FREEZE.json').read_text())['files']
    assert all(sha((R/p).read_bytes())==h for p,h in frozen.items())
    # Prove that the public grid and saved planner requests use the same known layout.
    field=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text())
    for index in [1,4,8]:
        saved=json.loads((R/('runs/v1350_bounded_complete_search/RESULT_%02d_MODE0.json'%index)).read_text())
        assert all(field[k]==saved['request']['known'][k] for k in ['known_rectangles','known_circles'])
    files=sorted(p for name in ['v1352_shared_controller_probe','v1353_controller_recording']
                 for p in (R/'runs'/name).rglob('*') if p.is_file() and p.name!='FINALIZED.json')
    manifest={str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in files}
    dump(E/'RAW_MANIFEST.json',dict(files=manifest,models=0,physical_native=0,raw_deletion_authorized=False))
    archive=E/'RAW_EVIDENCE.tar.gz'
    with tarfile.open(archive,'x:gz') as tar:
        for p in files:tar.add(p,arcname=str(p.relative_to(R)),recursive=False)
    restored={}
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            assert member.isfile() and member.name in manifest and not member.name.startswith('/') and '..' not in Path(member.name).parts
            data=tar.extractfile(member).read();restored[member.name]=dict(bytes=len(data),sha256=sha(data))
    assert restored==manifest,'ARCHIVE_MEMBER_READBACK_FAILED'
    dump(E/'ARCHIVE_VERIFICATION.json',dict(passed=True,members=len(manifest),archive_bytes=archive.stat().st_size,
         archive_sha256=sha(archive.read_bytes()),all_members_readback_sha_equal=True,public_map_matches_saved_geometry=True,
         local_raw_retained=True,remote_download_verified=False,models=0,physical_native=0))
    dump(O/'FINALIZED.json',dict(passed=True,closed_unix=time.time(),software_interface_cases=6,
         local_archive_and_member_sha_verified=True,source_unchanged=True,vehicle_initializations=0,
         physical_native=0,navigation_trials=0,archive=str(archive.relative_to(R)),remote_backup_pending=True))
    print(json.dumps(dict(local_finalized=True,members=len(manifest),archive_bytes=archive.stat().st_size,models=0)))


if __name__=='__main__':main()
