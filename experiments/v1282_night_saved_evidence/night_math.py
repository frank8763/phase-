"""Importable, isolated math/audit jobs on existing Phase evidence only."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('NIGHT_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
import copy,hashlib,importlib.util,json,math,os,signal,time
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def rd(p):return json.loads(Path(p).read_text())
def validate_job(job,kind):
    assert type(job)is dict and kind in ['audit','timing'],'JOB_KIND'
    assert type(job.get('slot'))is int and job['slot']in([1,9,17]if kind=='audit'else range(17,25)),'FIXED_SLOTS_ONLY'
    assert type(job.get('cpu'))is int and job['cpu']in[2,3,4],'FIXED_CPUS_ONLY'
    assert type(job.get('deadline'))in[int,float]and math.isfinite(job['deadline'])and job['deadline']>time.monotonic()+1,'EXPIRED_JOB'
    assert set(job)==({'slot','cpu','deadline','label'}if kind=='audit'else{'slot','cpu','deadline'}),'NO_UNREGISTERED_JOB_KEYS'
    if kind=='audit':assert job['label']in[f'{p}_{job["slot"]}'for p in ['serial','parallel']],'OUTPUT_ESCAPE'
    return True
def metadata_boundary_job(job):
    validate_job(job,'audit')
    assert not any(x in sys.modules for x in ['mujoco','vehicle','torch','rclpy'])
    return dict(passed=True,slot=job['slot'],models=0,physical_native=0,science_imported=False)
def write_scope(event,args):
    paths=[]
    if event=='open':
        p,mode,flags=args
        if (isinstance(mode,str)and any(c in mode for c in 'wax+'))or(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):paths=[p]
    elif event in ['os.mkdir','os.remove','os.rmdir']:paths=[args[0]]
    elif event in ['os.rename','os.link','os.symlink']:paths=list(args[:2])
    for p in paths:
        assert isinstance(p,(str,bytes,os.PathLike)),'NO_DESCRIPTOR_MUTATION'
        dest=Path(os.fsdecode(p)).resolve()
        assert dest.is_relative_to(O)or dest.is_relative_to(Path('/tmp')),'ORIGINAL_EVIDENCE_READ_ONLY '+str(dest)
def pin(cpu):
    os.sched_setaffinity(0,{cpu});os.sched_setscheduler(0,os.SCHED_IDLE,os.sched_param(0))
    if os.getpriority(os.PRIO_PROCESS,0)<19:os.nice(19-os.getpriority(os.PRIO_PROCESS,0))
def native_audit_job(job):
    validate_job(job,'audit');pin(job['cpu']);sys.addaudithook(write_scope)
    start=time.monotonic();parent=R/'experiments/v1281_partial_reconnection_fixed24';sys.path.insert(0,str(parent))
    context=load('phase_night_audit_context',parent/'campaign_context.py')
    audit=load('phase_night_unchanged_base_native',parent/'base_safety.py')
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('NIGHT_NATIVE_AUDIT_JOB_600S')))
    signal.alarm(max(1,int(min(600,job['deadline']-time.monotonic()))))
    task=rd(parent/f'TASK_main_slot{job["slot"]:02}.json');out=O/job['label'];out.mkdir()
    answer=audit.audit(task,output_path=out/'AUDIT.json');signal.alarm(0)
    canonical=json.dumps(answer,ensure_ascii=False,sort_keys=True,allow_nan=False,default=lambda x:x.item()if hasattr(x,'item')else x.tolist())
    return dict(slot=job['slot'],label=job['label'],cpu=job['cpu'],passed=bool(answer['passed']),canonical=canonical,
        result_sha256=hashlib.sha256(canonical.encode()).hexdigest(),wall_s=time.monotonic()-start,
        analytical_cpp_native=answer.get('analytical_cpp_native'),models=0,physical_native=0)

def timing_job(job):
    validate_job(job,'timing');pin(job['cpu']);sys.addaudithook(write_scope)
    begin=time.monotonic();module=load('phase_night_nominal_math',R/'experiments/v1271_ew_joint_phase_validation/audit_chain.py');q=module.q;np=module.np
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('NIGHT_TIME_ABLATION_JOB_600S')))
    signal.alarm(max(1,int(min(600,job['deadline']-time.monotonic()))))
    raw=R/f'runs/v858_nav2_verified/v1281/main_slot{job["slot"]:02}'
    x=rd(raw/'EW_ONWARD_INPUT.json');selected=rd(raw/'EW_ONWARD_SELECTION.json')
    with np.load(raw/'EW_ONWARD_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
    if not selected['passed']:
        signal.alarm(0)
        return dict(slot=job['slot'],source_passed=False,propagated=False,diagnostic=selected,models=0,physical_native=0,analytical_cpp_native=0,wall_s=time.monotonic()-begin)
    wait=selected['wait_native'];shape=selected['rows'][1:]if wait else selected['rows']
    if wait:assert selected['rows'][0]==[0.,0.,wait,0]
    org=dict(q.initial(x['packet']),steering_load_episode=selected['initial_load']);g=q.Geometry(x,table)
    response=.04+2*math.hypot(.44,.375)*math.sin(.035/2)+2e-6;engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);trials=[]
    for delay in sorted(set([wait,*range(0,2000,50)])):
        assert time.monotonic()<job['deadline'],'NIGHT_ROOT_DEADLINE'
        rows=([[0.,0.,delay,0]]if delay else[])+shape;ss,uu,mm=engine.simulate(org,rows)
        proof,_=g.final(selected['input'],ss,uu,rows);cursor=0;env=[]
        for t,v,n,mode in rows:
            if mode:env.append(float(g.cycle(ss[cursor:cursor+1,:3])[0])-.02-math.hypot(.44,.375)*.1)
            cursor+=int(n)
        cycle=float(g.cycle(ss[-1:,:3])[0]);extra=proof['minimum_raw_m']>=q.REQUIRED+.022 and min(env)>=q.REQUIRED+response and cycle>=q.REQUIRED+response
        trials.append(dict(wait_native=delay,original_full_gate=bool(proof['passed']),all_extra_reserves=bool(extra),complete_passed=bool(proof['passed']and extra),
            minimum_raw_m=proof['minimum_raw_m'],terminal_cycle_m=cycle,mode_envelopes=env,failed_checks=[k for k,v in proof['checks'].items()if not v]))
        if delay==wait:
            assert proof['passed']and extra,'RECORDED_SOURCE_NOT_REPRODUCED'
            with np.load(raw/'EW_ONWARD_REFERENCE.npz')as z:err=max(float(abs(ss-z['states']).max()),float(abs(uu-z['controls']).max()),float(abs(mm-z['memory']).max()))
            assert err<=1e-8,'RECORDED_ARRAY_MISMATCH'
    signal.alarm(0)
    return dict(slot=job['slot'],source_passed=True,propagated=True,selected_wait_native=wait,reference_error=err,
        without_wait=next(t for t in trials if t['wait_native']==0),passing_wait_native=[t['wait_native']for t in trials if t['complete_passed']],
        trials=trials,analytical_cpp_native=engine.native,wall_s=time.monotonic()-begin,models=0,physical_native=0,
        scope='saved-state temporal mechanism ablation; no actual controller outcome')
