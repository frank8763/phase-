"""Keep the review guard and isolate one zero-integration diagnostic."""
import fcntl,hashlib,importlib.util,json,os,signal,subprocess,time
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).resolve().parent;root=repo/'runs/v703_bootstrap_trace';root.mkdir(exist_ok=False)
assert (repo/'REVIEW_PENDING').exists()
with (repo/'runs/v648_static_unknown/execution.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
freeze=json.loads((repo/'experiments/v702_rpccr_prospective_compute/CANDIDATE_FREEZE.json').read_text())
def unchanged():assert all(hashlib.sha256((repo/n).read_bytes()).hexdigest()==h for n,h in freeze['files'].items())
unchanged();os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
spec=importlib.util.spec_from_file_location('v703_read_only_zero_namespace',repo/'tools/isolate.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
started=time.time();command=module.command(own/'trace_once.py',writable=True)
with (root/'console.txt').open('w') as stream:
    process=subprocess.Popen(command,cwd=repo,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
    try:code=process.wait(timeout=50)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGTERM)
        try:process.wait(timeout=2)
        except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
        code=124
unchanged();value={'outer_exit':code,'elapsed_s':time.time()-started,'outer_limit_s':50,'old_frozen_inputs_unchanged':len(freeze['files']),'original_v702_closed':True,'new_integrations':0,'review_guard_retained':True,'result_present':(root/'RESULT.json').exists()}
(root/'COMPLETION.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
