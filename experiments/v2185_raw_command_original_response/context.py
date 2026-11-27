"""New predictor-math authority, unavailable until genuine source/remote gates."""
import hashlib,json,os,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
PARENT=R/'runs/v2184_fair_raw_controller_math'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):assert Path(p).stat().st_size<=2*1024**2;return json.loads(Path(p).read_bytes())
def files(path=None,seen=None):
    p=(S/'SOURCE_FREEZE.json'if path is None else Path(path)).resolve();seen=set()if seen is None else seen
    assert p.is_relative_to(R/'runs')and p.name=='SOURCE_FREEZE.json'and p not in seen and len(seen)<64
    assert p.stat().st_size<=4*1024**2;seen.add(p);x=json.loads(p.read_bytes());out={}
    if 'inherit_freeze_path'in x:
        q=R/x['inherit_freeze_path'];assert sha(q)==x['inherit_freeze_sha256'];out.update(files(q,seen))
    assert all(n not in out or out[n]==h for n,h in x['files'].items());out.update(x['files']);return out

def require_admission():
    assert(S/'NUMERICAL_ADMISSION.json').exists(),'V2185_RESPONSE_MATH_NOT_ADMITTED'
    a=read(S/'NUMERICAL_ADMISSION.json');w=read(S/'ROUND_WINDOW.json')
    assert a['scope']=='FIXED_V2184_OUTPUTS_ORIGINAL_RESPONSE_MATH'and a['original_plant_allowed']is False
    assert a['predictor_constructions_allowed']==4 and a['maximum_predictor_steps']==8830 and a['profile_native_lengths']==[2210,2205,2210,2205]
    assert a['source_freeze_sha256']==sha(S/'SOURCE_FREEZE.json')
    qualification=read(S/'SOURCE_QUALIFICATION.json');remote=read(S/'SOURCE_REMOTE_CLOSURE.json')
    assert qualification['passed']and remote['passed']and remote['all_frozen_members_actual_remote_covered']
    assert qualification['source_freeze_sha256']==remote['source_freeze_sha256']==sha(S/'SOURCE_FREEZE.json')
    assert(S/'RUNTIME_ONCE.json').exists()and not(S/'COMPLETION.json').exists()
    assert os.sched_getaffinity(0)=={2}and os.environ.get('PHASE_REPO')==str(R)
    assert w['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    assert w['absolute_deadline_unix']-w['started_unix']==5400 and w['normal_end_unix']-w['started_unix']==4200
    assert time.time()<w['absolute_deadline_unix']and time.monotonic()<w['hard_stop_monotonic']
    assert os.environ.get('PHASE_RESPONSE_MATH_NONCE')==a['host_child_nonce']
    source=files();assert all(sha(R/n)==h for n,h in source.items())
    from budget import check
    check('runtime')
    return a,w,source
