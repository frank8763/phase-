"""Only remotely restored, hash-listed closed cache files may be removed."""
import sys,json,hashlib,fcntl
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,data):path.write_text(json.dumps(data,indent=2)+'\n')
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    pinned=set(json.loads((R/'experiments/v1092_stopped_replan/SOURCE_FREEZE.json').read_text())['files'])
    for version in ['v1091','v1092']:
        O=R/'runs'/('v1091_certified_exit'if version=='v1091'else'v1092_stopped_replan');D=R/'records'/('nav2_'+version+'_20261113')
        assert json.loads((D/'REMOTE_VERIFIED.json').read_text())['all_parts_and_decompressed_members_sha_verified']
        assert not(D/'CLEANUP.json').exists()
        if version=='v1091':
            x=json.loads((O/'ARCHIVE_INDEX.json').read_text());inventory=x['inventory'];groups=[(x['archive'],O/'cloud')]
        else:
            x=json.loads((D/'RECORD_INDEX.json').read_text());inventory=[row for name in x['archive_inventories']for row in json.loads((D/name).read_text())['files']];groups=list(zip(x['archives'],[O/'cloud',O/'review_cloud']))
        catalog={row['path']:row for row in inventory};candidates=[]
        root=R/'runs/v858_nav2_verified'/version
        for path in root.rglob('*'):
            key=str(path.relative_to(R))
            if not path.is_file()or path.is_symlink()or key in pinned or path.stat().st_size<=1024**2:continue
            row=catalog.get(key)
            if row is not None:
                assert sha(path)==row['sha256'];candidates.append(row)
        for record,cloud in groups:
            for part in record['parts']:
                path=cloud/part['name'];assert path.stat().st_size==part['bytes']and sha(path)==part['sha256']
                candidates.append(dict(path=str(path.relative_to(R)),bytes=part['bytes'],sha256=part['sha256']))
        dump(D/'CLEANUP_MANIFEST.json',dict(remote_verified=True,files=candidates))
        for row in candidates:
            path=R/row['path'];assert path.resolve().is_relative_to(R/'runs')and not path.is_symlink()and sha(path)==row['sha256'];path.unlink()
        assert all(sha(R/path)==value for path,value in json.loads((R/'experiments/v1092_stopped_replan/SOURCE_FREEZE.json').read_text())['files'].items())
        result=dict(passed=True,logical_bytes_removed=sum(row['bytes']for row in candidates),files_removed=len(candidates),all_removed_files_remotely_sha_verified=True,frozen_inputs_and_small_reproduction_packets_retained=True)
        dump(D/'CLEANUP.json',result);print(json.dumps(dict(version=version,**result)),flush=True)
if __name__=='__main__':main()
