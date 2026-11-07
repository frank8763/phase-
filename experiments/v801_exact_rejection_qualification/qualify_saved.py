"""Fixed old complete schedules, rejection equivalence and timing; no model."""
import gzip,json,hashlib,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco,mujoco.rollout
def forbidden(*args,**kwargs):raise AssertionError('ZERO_MODEL_INTEGRATION_FORBIDDEN')
for name in ['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,name,forbidden)
mujoco.rollout.rollout=forbidden
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(repo/'experiments/v800_spatial_nominal_global'));sys.path.insert(0,str(own))
from motion_tracker import install_time_gate
from rejection_witness import evaluate
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
auth=read(repo/'RPCCR_EXACT_ACCELERATION_AUTHORIZATION_20261104.json')
root=repo/'runs/v801_exact_rejection_qualification';assert not root.exists();root.mkdir()
assert(repo/'REVIEW_PENDING').exists()
start=time.time();deadline=min(start+900,auth['absolute_deadline_unix']);assert deadline-start>899
window=dict(started_unix=start,absolute_deadline_unix=deadline,limit_s=900,round_closed=False)
dump=lambda n,v:(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
dump('ROUND_WINDOW.json',window);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('SAVED_QUALIFICATION_900S')));signal.setitimer(signal.ITIMER_REAL,deadline-time.time())
status='RUNNING';records=[];error_max=0.;full_s=fast_s=0.;skipped=0
try:
    freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
    protocol=read(repo/'runs/v800_spatial_nominal_global/main_slot01/paired/STATIC_PROTOCOL.json');bounds=np.asarray(protocol['footprint_bounds'])
    base=dict(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']),circles=np.asarray(protocol['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
    def make(state):
        f=SimpleNamespace(**base);install_time_gate(f,state,'predictive',protocol['known_circles'],protocol['known_rectangles']);return f
    # Complete acceptance is never inferred from a subset, including near-threshold cases.
    synthetic=[]
    for name,values,expected_early in [
        ('ALL_PASS',np.full(328,.2),False),
        ('UNSAMPLED_FAIL',np.r_[.2,.2,.1,np.full(325,.2)],False),
        ('TERMINAL_FAIL',np.r_[np.full(327,.2),.1],True),
        ('EPSILON_GUARD_FULL_FALLBACK',np.r_[np.full(327,.2),.155-1e-9],False),
        ('EXACT_THRESHOLD_FULL_ACCEPT',np.full(328,.155),False)]:
        n=[0]
        def full(p,dt):n[0]+=1;return values.copy()
        f=SimpleNamespace(trajectory_values=full,causal_values_at_times=lambda p,t:values[np.rint(t/.01).astype(int)-1])
        r=evaluate(f,np.zeros((328,3)));assert r['rejected']==bool(values.min()<.155)
        assert r['full_minimum_not_evaluated']==expected_early and n[0]==int(not expected_early)
        synthetic.append(dict(name=name,rejected=r['rejected'],full_called=n[0]))
    oldpair=repo/'runs/v793_complete_joint_navigation/main_slot01/paired';oldstates={x['step']:x for x in map(json.loads,(oldpair/'geometry_memory/motion_estimate.jsonl').open())}
    qual=repo/'runs/v799_spatial_nominal_qualification';raw=read(qual/'RESULT.json');new_selected={}
    for record in raw['records']:
        field=make(oldstates[record['step']]);prefix=np.load(qual/(record['label']+'_PREFIX.npz'))
        q=prefix['qpos'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));first=np.c_[q[:,:2],yaw]
        best=None
        for i,tail in enumerate(record['detail']['candidates']):
            z=np.load(qual/(record['label']+'_TAIL_%02d.npz'%i));poses=np.vstack([first,z['poses']]);field.causal_values_at_times(poses[-1:],np.array([3.28]))
            if len(records)%2==0:
                t=time.perf_counter();original=field.trajectory_values(poses,.01);baseline=time.perf_counter()-t
                t=time.perf_counter();fast=evaluate(field,poses);accelerated=time.perf_counter()-t
            else:
                t=time.perf_counter();fast=evaluate(field,poses);accelerated=time.perf_counter()-t
                t=time.perf_counter();original=field.trajectory_values(poses,.01);baseline=time.perf_counter()-t
            assert abs(float(original.min())-tail['minimum_clearance_m'])<=1e-8
            assert fast['rejected']==bool(original.min()<.155)
            if fast['full_minimum_not_evaluated']:
                index=fast['witness_native_tick']-1;e=abs(float(original[index])-fast['witness_value_m']);assert e<=1e-10
                error_max=max(error_max,e);skipped+=1
            else:assert np.array_equal(fast['full_values'],original)
            clear_reject=tail['reason']=='TIME_CLEARANCE';assert fast['rejected']==clear_reject
            if tail['reason']is None:
                target=tail['target_command'];s=0. if tail['kind']=='BRAKE_ONLY'else next(s for s in[-.42722137342572125,-.2136106867128606,0.,.2136106867128606,.42722137342572125]if np.allclose(target, __import__('reserved_recovery').ReservedRecovery.target(s,target[2]),rtol=0,atol=1e-12))
                signed=tail['signed_displacement_m'];value=float(original.min())+.1*(signed if tail['kind']=='FORWARD_BRAKE'else-signed)-.02*abs(s)
                if best is None or value>best[0]:best=(value,i)
            full_s+=baseline;fast_s+=accelerated
            records.append(dict(source='V799',step=record['step'],rank=record['rank'],tail=i,original_rejected=clear_reject,
                early_rejected=fast['full_minimum_not_evaluated'],full_minimum_m=float(original.min()),witness_native_tick=fast['witness_native_tick'],witness_value_m=fast['witness_value_m'],full_seconds=baseline,fast_seconds=accelerated))
        if best is not None:assert record['append_summary']is not None and record['tail_files'][best[1]]['target_command']==record['append_summary']['reserve_target']
        else:assert record['append_summary']is None
        new_selected[record['label']]=None if best is None else best[1]
        if len(new_selected)%10==0:dump('PROGRESS.json',dict(commands=len(new_selected),schedules=len(records),early_rejections=skipped))
    pair=repo/'runs/v800_spatial_nominal_global/main_slot01/paired';states={x['step']:x for x in map(json.loads,(pair/'geometry_memory/motion_estimate.jsonl').open())}
    accepted=0
    for file in sorted((pair/'geometry_memory/ordinary_certificates').glob('*.npz')):
        step=int(file.stem.split('_')[-1]);z=np.load(file);field=make(states[step]);poses=np.vstack([z['prefix_poses'],z['poses']]);r=evaluate(field,poses)
        assert not r['rejected']and not r['full_minimum_not_evaluated']and abs(float(r['full_values'].min())-float(z['minimum_causal_clearance']))<=1e-8
        accepted+=1
    assert accepted==200 and len(new_selected)==75
    assert all(sha(repo/n)==h for n,h in freeze['files'].items())
    speedup=full_s/fast_s
    passed=bool(skipped>0 and speedup>=1.25)
    status='SAVED_REJECTION_EQUIVALENCE_QUALIFIED'if passed else'SAVED_REJECTION_EQUIVALENCE_NO_USEFUL_SPEEDUP'
    dump('DETAILS.json',records);dump('SELECTED_TAILS.json',new_selected)
    dump('RESULT.json',dict(status=status,qualified_for_global=passed,synthetic_tests=synthetic,V799_commands=75,V799_complete_schedules=len(records),V800_accepted_schedules=accepted,early_rejections=skipped,maximum_witness_vector_error=error_max,accepted_full_vectors_exact=True,selected_original_tails_exact=True,
        measured_original_geometry_s=full_s,measured_accelerated_geometry_s=fast_s,fixed_saved_geometry_speedup=speedup,
        new_models=0,new_integrations=0,new_actions=0,new_predictions=0,
        timing_limit='Geometry queries only, warm state cache and alternating order; not total navigation speedup or real-time proof.'))
except BaseException as e:
    status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()));raise
finally:
    signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-start);dump('ROUND_WINDOW.json',window)
