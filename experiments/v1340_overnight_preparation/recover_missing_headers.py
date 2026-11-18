"""Bounded transport recovery of exactly original package bytes, never upgrades."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import urllib.request

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1340_overnight_preparation'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')


def main():
    old=json.loads((R/'runs/v931_deadband_consistent_mppi/HEADER_PROVENANCE.json').read_text())['packages']
    estimates={x['filename']:x for x in json.loads((R/'records/nav2_v856_20261107/DEPENDENCY_ESTIMATE.json').read_text())['packages_to_fetch']}
    ubuntu=json.loads((R/'experiments/v931_deadband_consistent_mppi/UBUNTU_HEADER_LOCK.json').read_text())['packages']
    header=O/'headers';download=O/'debs';header.mkdir(exist_ok=True);download.mkdir(exist_ok=True)
    rows=[dict(x,filename=x['package'],expected_bytes=estimates[x['package']]['download_bytes'],kind='ros') for x in old]
    rows.extend(dict(x,filename=x['package']+'.deb',expected_bytes=None,kind='ubuntu') for x in ubuntu)
    failed={x['package'] for x in json.loads((O/'EXACT_HEADER_RESTORE_RESULT.json').read_text())['errors']}
    rows=[x for x in rows if x['filename'] in failed]
    def fetch(row):
        path=download/row['filename'];errors=[]
        # Verified local copies of three immutable numerical-header packages.
        local=R/'runs/v1314_mppi_critic_trace'/row['filename']
        if local.is_file() and sha(local)==row['sha256']:return row,local,'existing_byte_identical_package',errors
        hosts=['https://mirrors.ustc.edu.cn','https://mirror.iscas.ac.cn'] if row['kind']=='ros' else ['https://mirrors.ustc.edu.cn','https://archive.ubuntu.com']
        for host in hosts:
            url=row['url'].replace('https://mirrors.tuna.tsinghua.edu.cn',host)
            try:
                with urllib.request.urlopen(url,timeout=20) as response:data=response.read()
                assert hashlib.sha256(data).hexdigest()==row['sha256'],'EXACT_PACKAGE_SHA_MISMATCH'
                if row['expected_bytes'] is not None:assert len(data)==row['expected_bytes']
                path.write_bytes(data);return row,path,url,errors
            except Exception as error:errors.append(dict(url=url,error_type=type(error).__name__,reason='BOUNDED_ALTERNATE_TRANSPORT'))
        return row,None,None,errors
    results=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for row,path,url,attempt_errors in pool.map(fetch,rows):
            if path is None:errors.append(dict(package=row['filename'],attempts=attempt_errors));continue
            # Each extraction is from a fully SHA-verified DEB. No old root modified.
            count=0;proc=subprocess.Popen(['dpkg-deb','--fsys-tarfile',str(path)],stdout=subprocess.PIPE)
            with tarfile.open(fileobj=proc.stdout,mode='r|') as tar:
                for member in tar:
                    p=Path(member.name)
                    if not member.isfile() or p.is_absolute() or '..' in p.parts:continue
                    if not (str(p).startswith('opt/ros/jazzy/include/') or str(p).startswith('usr/include/')):continue
                    dest=header/p;dest.parent.mkdir(parents=True,exist_ok=True);data=tar.extractfile(member).read()
                    if dest.exists():assert dest.read_bytes()==data,'OVERLAPPING_HEADER_CHANGED'
                    else:dest.write_bytes(data)
                    count+=1
            assert proc.wait(timeout=15)==0
            results.append(dict(package=row['filename'],url=url,sha256=row['sha256'],header_files=count,earlier_attempts=attempt_errors))
            print(json.dumps(dict(extracted=row['filename'],headers=count)),flush=True)
    proof=dict(passed=not errors,packages=results,errors=errors,old_runtime_modified=False,versions_changed=False,models=0)
    dump(O/'EXACT_HEADER_MISSING_RECOVERY.json',proof)
    assert not errors,'PINNED_HEADER_RESTORE_INCOMPLETE'
    print(json.dumps(dict(passed=True,packages=len(results),models=0)),flush=True)


if __name__=='__main__':main()
