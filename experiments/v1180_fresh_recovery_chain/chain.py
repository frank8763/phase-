"""Causal composition: live normal owner, observation, refresh, full recovery."""
from chain_tools import *
import types
sys.path.insert(0,str(R/'experiments/v1121_coupled_route_night'))
from source import Engine,initial,remaining_rows
sys.path.insert(0,str(R/'experiments/v1146_causal_certificate_refresh'))
from fast_cycle import certify
from refresh import causal_packets
sys.path.insert(0,str(R/'experiments/v1135_causal_batch'))
from joint_domain import Domain,NORMALS
def front(rows,n):
    answer=[]
    for t,v,k,m in rows:
        take=min(n,int(k))
        if take:answer.append((float(t),float(v),take,bool(m)));n-=take
        if n==0:break
    assert n==0;return answer
def current_input(v,setup,evidence):
    p=packet(v);p['coupled_episode']=bool(getattr(v,'_chain_episode',False));p['steering_motion_active']=bool(getattr(v.adapter,'_steering_motion_active',False));p['dynamic_discovered']=bool(evidence.first is not None)
    s=evidence.source(v);assert p['dynamic_discovered']and s['source_native_tick']<=p['native_tick']and 0<=s['source_age_s']<=.051
    return dict(setup=setup,packet=p,source=s,goal=[4.,-2.])
def fresh_evidence(v,setup):
    # Rebuild the original coefficient estimator from this run's own whitelist.
    clean,duplicates=causal_packets(v.sensor_rows,packet(v));causal=load('v1180_packet_estimator',R/'experiments/v1024_full_route_execution/causal.py');norm=load('v1180_norm_prior',R/'experiments/v1037_periodic_norm_source/periodic_norm.py');e=causal.Evidence(setup['known']);e.periodic=norm.PeriodicSupport()
    for scan in clean:e.update(scan)
    assert e.first is not None
    return e,dict(unique_packets=len(clean),duplicates=duplicates,largest_input_tick=clean[-1]['native_tick'],only_current_run_sensor_rows=True)
def joint_table(source):
    d=Domain(source['periodic']['vertices']);centers=(np.arange(256)+.5)*(2*np.pi/.32/256);upper,dual,res=d.table(centers);directions=np.array([[[nx,nx*np.sin(.32*t),nx*np.cos(.32*t),ny,ny*np.sin(.32*t),ny*np.cos(.32*t)]for nx,ny in NORMALS]for t in centers]);residual=directions-np.einsum('tnj,jk->tnk',dual,d.A);verified=np.einsum('tnj,j->tn',dual,d.b)+np.where(residual>=0,residual*d.upper,residual*d.lower).sum(2)+1e-8
    assert np.all(dual>=0)and abs(verified-upper).max()<=1e-9
    return dict(bounds=upper+.08*((2*np.pi/.32/256)/2+.075)+2e-7,centers=centers,dual=dual,residual=residual,A=d.A,b=d.b,lower=d.lower,upper_box=d.upper),d.calls
def execute(v,setup,original,end,evidence,out,packet_fn,output):
    entry=v.count;v._chain_phase='observation';v._chain_episode=False;v._chain_counts=dict(cpp_native=0,python_native=0,LP_calls=0);engine=Engine(setup);v._chain_engine=engine;certificates=[];mode=False;anchor=None;offset=0
    x=current_input(v,setup,evidence);dump(out/'OBSERVATION_ENTRY.json',x)
    # A frozen development library is activated only under its causal input
    # domain; old observations/control traces are not read by the live owner.
    library=read(R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/COUPLED_ENTRY.json')
    assert x['packet']['native_tick']==library['packet']['native_tick']and abs(x['packet']['sim_time']-library['packet']['sim_time'])<=1e-8,'OBSERVER_LIBRARY_CLOCK_DOMAIN'
    from scipy.spatial import ConvexHull
    nested=max(float((np.asarray(a)@ConvexHull(np.asarray(b)).equations[:,:3].T+ConvexHull(np.asarray(b)).equations[:,3]).max())for a,b in zip(x['source']['periodic']['vertices'],library['source']['periodic']['vertices']));assert nested<=2e-8,'OBSERVER_LIBRARY_SOURCE_DOMAIN'
    with np.load(R/'runs/v1144_saved_entry_relay/software/SOURCE.npz')as z:nominal=z['states'].copy()
    rows=read(R/'runs/v1144_saved_entry_relay/software/ROWS.json')['rows']
    sys.path.insert(0,str(R/'experiments/v1135_causal_batch'));from geometry import Geometry
    with np.load(R/'runs/v1135_causal_batch/domain/JOINT_TABLE.npz')as z:oldtable={k:z[k].copy()for k in ['bounds','centers']}
    # Its old upper support is valid only under the freshly verified nested set.
    geometry=Geometry(library,oldtable);maximum=np.zeros(3)
    def apply_rows(schedule,expected,phase,reference_offset=None):
        nonlocal mode,anchor,maximum
        index=0;v._chain_phase=phase
        for target,speed,count,park in schedule:
            if park and not mode:
                p=packet(v);assert previous.stopped(p),'PARKED_MODE_ENTRY_NOT_REST';anchor=np.array(p['body'][:3]);assert geometry.cycle(anchor[None,:])[0]-.02-np.hypot(.44,.375)*.1>=q.REQUIRED
            if abs(speed)>=.005:anchor=None
            for _ in range(int(count)):
                assert time.time()<end-180,'FULL_CHAIN_REPLAY_RESERVE';v.adapter.parked_target=float(target)if park else None
                v.step(float(speed),0. if park or speed==0 else float(speed)*math.tan(target)/.6,False)
                if park:v._chain_episode=True
                if abs(speed)>=.005:v._chain_episode=False
                index+=1;p=packet(v);previous.body_gate(p);actual=np.array(initial(dict(p,coupled_episode=v._chain_episode,steering_motion_active=bool(getattr(v.adapter,'_steering_motion_active',False))))['state']);delta=actual-expected[index];err=np.array([np.linalg.norm(delta[:2]),abs(np.arctan2(np.sin(delta[2]),np.cos(delta[2]))),abs(delta[6])]);maximum=np.maximum(maximum,err)
                if v.count%5==0:evidence.update(v.scan())
                assert(err<=[.04,.035,.015]).all(),'FRESH_OBSERVER_MODEL_RESPONSE'
                if reference_offset is not None:
                    d=actual-nominal[reference_offset+index];assert np.linalg.norm(d[:2])<=.04 and abs(np.arctan2(np.sin(d[2]),np.cos(d[2])))<=.035 and abs(d[6])<=.015,'FRESH_OBSERVER_REFERENCE'
                if anchor is not None:assert np.linalg.norm(actual[:2]-anchor[:2])<=.02 and abs(np.arctan2(np.sin(actual[2]-anchor[2]),np.cos(actual[2]-anchor[2])))<=.1
                if park:assert abs(actual[3])<=.01 and abs(v.d.ctrl[v.adapter.commands.ids[2:]]).max()<=1e-10
            mode=bool(park)
    while offset<len(nominal)-1:
        p=current_input(v,setup,evidence)['packet'];suffix=remaining_rows(rows,offset);first=suffix[0];n=int(first[2])if first[3]or offset>=12500 else min(8,int(first[2]));block=front(suffix,n)
        proof=[];pred=[]
        for schedule in [[(0.,0.,2200,0)],[*block,(0.,0.,2200,0)]]:
            ss,uu=engine.simulate(initial(p),schedule);pr,_=geometry.final(dict(library,packet=p,goal=ss[-1,:2].tolist(),safe_terminal_pose=ss[-1,:3].tolist()),ss,uu,schedule);proof.append(pr);pred.append(ss)
        certificates.append(dict(offset=offset,native=v.count,packet=p,current=proof[0],prospective=proof[1],prefix=n));assert proof[0]['passed'],'OBSERVER_CURRENT_STOP_REFUSED'
        if not proof[1]['passed']:break
        apply_rows(block,pred[1],'observation',offset);offset+=n
        if len(certificates)%100==0:dump(out/'PARTIAL_PROGRESS.json',dict(stage='fresh_observation',native=v.count,offset=offset))
    else:raise AssertionError('OBSERVER_EXPECTED_REFRESH_SEAM_NOT_REACHED')
    dump(out/'OBSERVER_CERTIFICATES.json',certificates);dump(out/'REFRESH_SEAM.json',dict(native=v.count,offset=offset,nested_observer_domain=nested,old_prospective_refused=True,new_causal_update_required=True))
    evidence,meta=fresh_evidence(v,setup);fresh=current_input(v,setup,evidence);dump(out/'REFRESH_INPUT.json',fresh);rest=remaining_rows(rows,offset);block=front(rest,8);assert all(not row[3]for row in block)
    proofs=[];pred=[]
    for schedule in [[(0.,0.,2200,0)],[*block,(0.,0.,2200,0)]]:
        ss,uu=engine.simulate(initial(fresh['packet']),schedule);pr=certify(dict(fresh,goal=ss[-1,:2].tolist(),safe_terminal_pose=ss[-1,:3].tolist()),ss,uu,schedule);proofs.append(pr);pred.append(ss)
    dump(out/'LIVE_REFRESH_PROOFS.json',dict(metadata=meta,current=proofs[0],prospective=proofs[1]));assert all(p['passed']for p in proofs),'FRESH_REFRESH_PROOF_REFUSED'
    apply_rows([*block,(0.,0.,2200,0)],pred[1],'refreshed_handoff');assert previous.stopped(packet(v)),'FRESH_HANDOFF_NOT_STOPPED'
    evidence,meta=fresh_evidence(v,setup);fresh=current_input(v,setup,evidence);fresh['safe_terminal_pose']=[4.,-1.85,0.];dump(out/'RECOVERY_INPUT.json',fresh)
    table,calls=joint_table(fresh['source']);v._chain_counts['LP_calls']=calls;np.savez_compressed(out/'LIVE_JOINT_TABLE.npz',**table)
    fixedrows=read(R/'experiments/v1163_joint_timing_repair/TASKS.json')['rows'];org=dict(q.initial(fresh['packet']),steering_load_episode=False);fast=q.accelerator.Engine(setup,q.model.parameters()['coefficients']);ss,uu,mm=fast.simulate(org,fixedrows);v._chain_counts['cpp_native']=engine.native+fast.native
    geometry=q.Geometry(fresh,table);proof=q.proof(geometry,fresh,ss,uu,q.requests_of(fixedrows),mm);dump(out/'LIVE_RECOVERY_REFERENCE_PROOF.json',proof)
    assert proof['passed'],'FRESH_FULL_RECOVERY_REFERENCE_REFUSED'
    reference=dict(states=ss,controls=uu,memory=mm);schedule=[(float(t),float(speed))for t,speed,n,m in fixedrows for _ in range(n)];np.savez_compressed(out/'LIVE_RECOVERY_REFERENCE.npz',**reference)
    policy=load('v1180_original_qualified_feedback',R/'experiments/v1179_frozen_recovery_native/policy_execution.py');policy.HISTORY=v.count;v._recovery_setup=setup;v._chain_phase='goal_recovery';v.adapter.parked_target=None
    answer=policy.run_policy(v,reference,schedule,lambda:time.time()<end-150,lambda p:dump(out/'PARTIAL_PROGRESS.json',p))
    shadow=v._recovery_shadow;shadowraw=np.minimum(*geometry.components(shadow[:,:3],np.arange(len(shadow))));assert shadowraw.min()>=q.REQUIRED and geometry.cycle(np.array(v.body()[:3])[None,:])[0]>=q.REQUIRED,'FRESH_COMPLETE_SHADOW_RAW_REFUSED'
    v._chain_counts['python_native']=v._recovery_python_native
    dump(out/'RECOVERY_POLICY_RESULT.json',answer);dump(out/'RECOVERY_POLICY_JOURNAL.json',v._recovery_journal);np.savez_compressed(out/'RECOVERY_SHADOW.npz',states=shadow)
    return dict(answer,root_native=entry,observer_native=offset,refresh_native=2208,live_source_native=fresh['packet']['native_tick'],observer_maximum_response=maximum,causal_sources_rebuilt_from_current_run=True,full_fresh_t0_navigation=True,formal_retained_commit=False,minimum_shadow_raw=float(shadowraw.min()),finite_known_course_library_not_independent_confirmation=True)
