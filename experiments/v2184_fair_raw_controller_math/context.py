"""Explicit new math-only authority, no numeric imports or implicit launch."""
import hashlib,json,os,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
REVIEW_SHA='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
    p=Path(p);assert p.stat().st_size<=2*1024**2
    return json.loads(p.read_bytes())
def put(p,v):
    p=Path(p);assert p.resolve().is_relative_to(S.resolve())
    raw=json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'
    assert len(raw)<=32*1024
    with p.open('xb')as f:f.write(raw)
def source_files(path=None,seen=None):
    path=(S/'SOURCE_FREEZE.json'if path is None else Path(path)).resolve();seen=set()if seen is None else seen
    assert path not in seen and len(seen)<64;seen.add(path);assert path.is_relative_to((R/'runs').resolve()) and path.name=='SOURCE_FREEZE.json'
    assert path.stat().st_size<=4*1024**2,'SOURCE_FREEZE_FILE4MIB_CAP'
    x=json.loads(path.read_bytes());files={}
    if 'inherit_freeze_path'in x:
        q=R/x['inherit_freeze_path'];assert sha(q)==x['inherit_freeze_sha256'];files.update(source_files(q,seen))
    assert all(n not in files or files[n]==h for n,h in x['files'].items())
    files.update(x['files']);return files
def numerical_admission():
    assert(S/'NUMERICAL_ADMISSION.json').is_file(),'NEW_NATIVE_MATH_NOT_ADMITTED'
    a=read(S/'NUMERICAL_ADMISSION.json');w=read(S/'ROUND_WINDOW.json')
    assert a['scope']=='FIXED_SAVED_COMMON_INPUT_RAW_CONTROLLER_MATH'and a['original_plant_allowed']is False
    assert a['controller_math_allowed']is True and a['allowed_queries']=={'DWA':1,'RPP':1}
    assert a['source_freeze_sha256']==sha(S/'SOURCE_FREEZE.json')
    assert read(S/'SOURCE_QUALIFICATION.json')['passed']and read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
    from budget import check
    check('runtime')
    assert(S/'RUNTIME_ONCE.json').is_file()and not(S/'COMPLETION.json').exists()and not(S/'RUNTIME/RESULT.json').exists()
    assert os.sched_getaffinity(0)=={2}and os.environ.get('PHASE_REPO')==str(R)
    assert w['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    assert w['absolute_deadline_unix']-w['started_unix']==5400 and w['normal_end_unix']-w['started_unix']==4200
    assert time.time()<w['absolute_deadline_unix']and time.monotonic()<w['hard_stop_monotonic']
    assert os.environ.get('PHASE_NATIVE_MATH_NONCE')==a['host_child_nonce']
    files=source_files();assert all(sha(R/n)==h for n,h in files.items())
    return a,w,files
