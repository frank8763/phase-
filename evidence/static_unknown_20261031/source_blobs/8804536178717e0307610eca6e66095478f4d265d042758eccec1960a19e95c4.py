import argparse,fcntl,hashlib,json,os,signal,sys,time,types,traceback
from pathlib import Path
from instrumentation import dump
p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=73105157);p.add_argument('--name',default='diagnostic_01');p.add_argument('--physical',action='store_true');a=p.parse_args()
repo=Path(os.environ['PHASE_REPO']);out=Path(os.environ['PHASE_RUNS'])/'v648_static_unknown'/a.name
out.mkdir(exist_ok=False,parents=True)
os.environ['RPCCR_SEED']=str(a.seed);os.environ['V541_OUTPUT_DIR']=str(out/'paired')
source=(repo/'current/runner.py').read_text()
replacements=[
("    out = __import__('pathlib').Path(__file__).resolve().parents[2] / 'output_v630'","    out = __import__('pathlib').Path(__import__('os').environ['V541_OUTPUT_DIR'])"),
("def main():","def main():\n    from instrumentation import Audit\n    _v648_audit = Audit()"),
("            recorder=ContactRecorder(catalog,cell)","            recorder=ContactRecorder(catalog,cell)\n            _v648_audit.begin(env,cell,branch)" + ("\n            from instrumentation import install_physical_contract\n            dump_physical = install_physical_contract(env)\n            save(cell/'physical_contract.json',dump_physical)" if a.physical else "")),
("                answer=original_mj(m,d,*args,**kwargs)","                _v648_audit.before_native(m,d)\n                answer=original_mj(m,d,*args,**kwargs)\n                _v648_audit.after_native(m,d)"),
("                                field, path, stats = F.search(world)","                                _v648_audit.before_search(world,step)\n                                field, path, stats = F.search(world)\n                                _v648_audit.after_search(path,stats,field)"),
("                _v625_after = _v625_snapshot_path()","                _v648_audit.after_public(env,step)\n                _v625_after = _v625_snapshot_path()")]
for old,new in replacements:
    assert source.count(old)==1,(old,source.count(old));source=source.replace(old,new)
(out/'executed_runner.py').write_text(source)
sys.path.insert(0,str(repo/'current'))
gui=types.ModuleType('v115_live_view');gui.tick=lambda *a,**k:None;gui.close=lambda *a,**k:None;sys.modules['v115_live_view']=gui
module=types.ModuleType('v648_executed');module.__file__=str(repo/'current/runner.py')
start=time.monotonic()
def timeout(*_):raise TimeoutError('V648_HARD_900S_BUDGET')
signal.signal(signal.SIGALRM,timeout);signal.alarm(900)
status='FAILED';err=None
try:
    with (out/'single_instance.lock').open('w') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        exec(compile(source,module.__file__,'exec'),module.__dict__)
        module.main();status='COMPLETE'
except BaseException as e:
    err={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()};print(json.dumps(err),flush=True)
finally:
    signal.alarm(0)
    dump((out/'paired' if (out/'paired').exists() else out)/'completion.json',{'status':status,'seed':a.seed,'error':err,'elapsed_s':time.monotonic()-start,'original_runner_sha256':hashlib.sha256((repo/'current/runner.py').read_bytes()).hexdigest(),'executed_runner_sha256':hashlib.sha256(source.encode()).hexdigest()})
if status!='COMPLETE':sys.exit(1)
