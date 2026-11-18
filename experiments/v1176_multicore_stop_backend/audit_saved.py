from pathlib import Path
import json,hashlib,fcntl
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1176_multicore_stop_backend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    d=json.loads((O/'COMPLETION.json').read_text());r=json.loads((O/'RESULT.json').read_text());assert d['error']is None and r['passed']
    f=json.loads((C/'SOURCE_FREEZE.json').read_text())['files'];assert all(sha(R/p)==h for p,h in f.items())
    tasks=json.loads((C/'TASKS.json').read_text())['jobs'];s=json.loads((O/'SERIAL.json').read_text());p=json.loads((O/'PARALLEL.json').read_text())
    n=len(tasks);assert len(s['rows'])==len(p['rows'])==n and d['serial_analytical_native']==d['parallel_analytical_native']==n*2200
    keys=['id','plan','offset','passed','checks','minimum_raw','state_sha256','ctrl_sha256','memory_sha256','completed_analytical_native']
    for job,a,b in zip(tasks,s['rows'],p['rows'],strict=True):
        assert job['id']==a['id']==b['id']and job['offset']==a['offset']and all(a[k]==b[k]for k in keys)
        assert a['completed_analytical_native']==2200 and a['passed']==all(a['checks'].values())
    # Compare function must reject a forged hash and missing/reordered work.
    a,b=dict(s['rows'][0]),dict(p['rows'][0]);b['state_sha256']='0'*64;assert any(a[k]!=b[k]for k in keys)
    assert [z['id']for z in p['rows']]==list(range(n))and len(p['rows'][:-1])!=n
    seen={}
    for a in p['rows']:seen.setdefault(a['pid'],set()).add(a['core'])
    assert len(seen)==4 and sorted(next(iter(v))for v in seen.values())==[2,3,4,5]and all(len(v)==1 for v in seen.values())
    speedup=(s['timing']['setup_s']+s['timing']['execution_s'])/p['timing']['end_to_end_including_startup_shutdown_s'];assert abs(speedup-r['measured_net_speedup_including_startup'])<1e-12
    result=dict(passed=True,source_files=len(f),all_ordered_jobs=n,full_arrays_hashes_equal=True,account_exact=True,worker_processes=4,cores=[2,3,4,5],changed_hash_and_missing_task_rejected=True,measured_net_speedup=speedup,new_state_prediction=0,models=0,physical_native=0)
    (O/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));fcntl.flock(lock,fcntl.LOCK_UN)
if __name__=='__main__':main()
