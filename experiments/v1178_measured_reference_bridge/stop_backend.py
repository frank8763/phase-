"""Fixed original causal geometry and same stateful C++ model, one per process."""
from pathlib import Path
import sys,os,time,hashlib
C=Path(__file__).resolve().parent;R=C.parents[1]
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
sys.path.insert(0,str(C))
_engine=None;_geom=None;_q=None;_core=None
def initialize(counter,gate,freeze):
    global _engine,_geom,_q,_core
    from bridge_tools import q,np,load,sha,R
    assert all(sha(R/p)==h for p,h in freeze.items())
    import json
    x=json.loads((R/'runs/v1160_safe_terminal_connection/SELECTED.json').read_text());xinput=x['input']
    with np.load(R/x['table_path'])as z:table={k:z[k].copy()for k in ['bounds','centers']}
    _q=q;_engine=q.accelerator.Engine(xinput['setup'],q.model.parameters()['coefficients']);_geom=q.Geometry(xinput,table)
    with gate:slot=counter.value;counter.value+=1
    assert slot<4;_core=[2,3,4,5][slot]
    policy=load('v1178_qualified_idle_policy',R/'experiments/v1176_multicore_stop_backend/policy.py');policy.configure(_core)
def evaluate(job):
    q=_q;np=q.np;tick=job['offset'];org=job['origin'];before=_engine.native;t=time.perf_counter()
    ss,uu,mm=_engine.simulate(org,[(0.,0.,2200,0)]);assert _engine.native-before==2200
    static,dynamic=_geom.components(ss[:,:3],tick+np.arange(2201));raw=np.minimum(static,dynamic);lo=float(raw.min());arg=int(raw.argmin());setup=_engine.setup;lim=np.array(setup['limits']);rate=np.array(setup['slew_per_second'])*.01
    checks=dict(raw=lo>=q.REQUIRED,body=bool((abs(ss[:,3:6])<=[.13,.03,.16]).all()),ctrl=bool((uu>=lim[:,0]-1e-10).all()and(uu<=lim[:,1]+1e-10).all()),slew=bool((abs(np.diff(np.vstack([org['last_ctrl'],uu]),axis=0))<=rate+1e-10).all()),complete=ss.shape==(2201,8)and mm.shape==(2201,5),rest=bool(abs(ss[-50:,3:6]).max()<=.003 and abs(ss[-50:,7]).max()<=.015),finite=bool(np.isfinite(ss).all()and np.isfinite(uu).all()))
    def dig(a):return hashlib.sha256(np.ascontiguousarray(a,dtype=np.float64).tobytes()).hexdigest()
    return dict(id=job['id'],offset=tick,passed=all(checks.values()),checks=checks,minimum_raw=lo,static_min=float(static.min()),dynamic_min=float(dynamic.min()),worst_tail_native=arg,worst_reference_relative_native=tick+arg,minimum_kind='static'if static[arg]<=dynamic[arg]else'causal_dynamic',origin_state=org['state'],origin_memory=[*org['last_ctrl'],org['integral']],core=_core,pid=os.getpid(),completed_analytical_native=2200,state_sha256=dig(ss),ctrl_sha256=dig(uu),memory_sha256=dig(mm),wall_s=time.perf_counter()-t)
