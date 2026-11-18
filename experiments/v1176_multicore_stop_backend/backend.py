"""Independent stop jobs; spawn processes isolate the C++ global counter."""
from pathlib import Path
import sys,os,importlib.util,time,hashlib,json,concurrent.futures,multiprocessing
C=Path(__file__).resolve().parent;R=C.parents[1]
# A child imports this module before NumPy/legacy imports: preserve original
# allowed CPUs and configure thread limits, then reapply assigned core in init.
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
sys.path.insert(0,str(C))
from policy import configure,CORES
_engine=None;_q=None;_geometry=None;_policy=None;_freeze=None;_jobs=None
def initialize(core,shared_jobs,freeze):
    global _engine,_q,_geometry,_policy,_freeze,_jobs
    if core is None:
        # Each child gets a stable unique assignment from the parent's shared
        # counter; no process-name assumptions or other-job process inventory.
        counter,gate=shared_jobs
        with gate:
            slot=counter.value;counter.value+=1
        assert slot<4;core=CORES[slot]
    s=importlib.util.spec_from_file_location('v1176_fixed_bindings',R/'experiments/v1160_safe_terminal_connection/search.py');q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
    import numpy as np
    qref=importlib.import_module('kernel').ref
    inp=json.loads((R/'runs/v1173_rate_preconditioned_input/INPUTS.json').read_text())
    assert all(q.sha(R/p)==h for p,h in freeze.items()),'CHILD_SOURCE_CHANGED'
    _q=q;_engine=q.accelerator.Engine(inp['setup'],q.model.parameters()['coefficients']);_geometry=qref._old.Geometry(inp['setup']['known'],None);_freeze=freeze
    _policy=configure(core)
    assert len(os.sched_getaffinity(0))==1 and core in os.sched_getaffinity(0)

def evaluate(job):
    assert _engine is not None
    q=_q;np=q.np;t=time.perf_counter();origin=job['origin'];before=_engine.native
    ss,uu,mem=_engine.simulate(origin,[(0.,0.,2200,0)])
    work=_engine.native-before;assert work==2200 and not _engine.in_call,'COUNTER_OR_COMPLETION'
    raw=_geometry.clearances(ss[:,:3])[0];setup=_engine.setup;lim=np.array(setup['limits']);rate=np.array(setup['slew_per_second'])*.01
    checks=dict(raw=float(raw.min())>=q.REQUIRED,body=bool((abs(ss[:,3:6])<=[.13,.03,.16]).all()),ctrl=bool((uu>=lim[:,0]-1e-10).all()and(uu<=lim[:,1]+1e-10).all()),slew=bool((abs(np.diff(np.vstack([origin['last_ctrl'],uu]),axis=0))<=rate+1e-10).all()),rest=bool(abs(ss[-50:,3:6]).max()<=.003 and abs(ss[-50:,7]).max()<=.015),complete=ss.shape==(2201,8)and uu.shape==(2200,4)and mem.shape==(2201,5),memory=bool(np.array_equal(mem[1:,:4],uu)),finite=bool(np.isfinite(ss).all()and np.isfinite(uu).all()and np.isfinite(mem).all()))
    def digest(x):
        x=np.ascontiguousarray(x,dtype=np.float64);h=hashlib.sha256();h.update(str(x.shape).encode());h.update(x.tobytes());return h.hexdigest()
    return dict(id=job['id'],plan=job['plan'],offset=job['offset'],passed=all(checks.values()),checks=checks,minimum_raw=float(raw.min()),state_sha256=digest(ss),ctrl_sha256=digest(uu),memory_sha256=digest(mem),completed_analytical_native=work,pid=os.getpid(),core=_policy['affinity'][0],wall_s=time.perf_counter()-t)

def serial(jobs,freeze):
    t=time.perf_counter();initialize(2,None,freeze);setup=time.perf_counter()-t;t=time.perf_counter();out=[evaluate(j)for j in jobs]
    return out,dict(setup_s=setup,execution_s=time.perf_counter()-t,worker_resources=[_policy])

def parallel(jobs,freeze):
    context=multiprocessing.get_context('spawn');counter=context.Value('i',0);gate=context.Lock()
    started=time.perf_counter()
    with concurrent.futures.ProcessPoolExecutor(max_workers=4,mp_context=context,initializer=initialize,initargs=(None,(counter,gate),freeze))as pool:
        results=list(pool.map(evaluate,jobs,chunksize=8))
    elapsed=time.perf_counter()-started
    return results,dict(end_to_end_including_startup_shutdown_s=elapsed,workers=len({r['pid']for r in results}),cores=sorted({r['core']for r in results}))
