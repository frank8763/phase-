"""Independent goal evidence auditor: never imports the goal executor."""
import copy
import json
import math
from pathlib import Path
import sys

R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1186_live_observer_regeneration'))
from current_state_tools import q,np,validate_input
COUNTS=dict(cpp_native=0,partial_unknown=False)


class CountedEngine:
    def __init__(self,setup):self.engine=q.accelerator.Engine(setup,q.model.parameters()['coefficients'])
    @property
    def native(self):return self.engine.native
    def simulate(self,*args):
        before=self.engine.native
        try:return self.engine.simulate(*args)
        finally:
            COUNTS['cpp_native']+=self.engine.native-before
            if self.engine.in_call:COUNTS['partial_unknown']=True


class OffsetGeometry:
    def __init__(self,geometry,offset):self.geometry,self.offset=geometry,offset
    def components(self,poses,ticks):return self.geometry.components(poses,np.asarray(ticks)+self.offset)
    def cycle(self,poses):return self.geometry.cycle(poses)


def load_bundle(path):
    path=Path(path)
    def read(name):return json.loads((path/name).read_text())
    def arrays(name):
        with np.load(path/name,allow_pickle=False)as z:return {k:z[k].copy()for k in z.files}
    b=dict(result=read('RESULT.json'),trace=arrays('EXECUTED.npz'),journal=read('JOURNAL.json'),
        initial=read('INITIAL_SELECTION.json'),initial_ref=arrays('INITIAL_REFERENCE.npz'))
    if (path/'HANDOFF_PACKET.json').exists():
        b.update(handoff=read('HANDOFF_PACKET.json'),onward=read('ONWARD_SELECTION.json'),onward_ref=arrays('ONWARD_REFERENCE.npz'))
    return b


def origin_at(state,memory,load):
    return dict(state=np.asarray(state),last_ctrl=np.asarray(memory[:4]),integral=float(memory[4]),
        coupled_episode=False,steering_motion_active=False,steering_load_episode=bool(load))


def close(a,b,label):
    a=np.asarray(a);b=np.asarray(b)
    assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all(),label+'_SHAPE_FINITE'
    assert not a.size or float(abs(a-b).max())<=1e-8,label


def verify(x,table,b,initial_load,external=None):
    validate_input(x);assert type(initial_load)is bool
    t=b['trace'];r=b['result'];j=b['journal'];n=len(t['controls']);start=x['packet']['native_tick']
    assert n==r['native']==len(j)==len(t['requests']) and n>=2200,'NATIVE_COVERAGE'
    assert t['states'].shape==(n+1,8) and t['memory'].shape==(n+1,5) and t['shadow'].shape==(n+1,8)
    assert t['controls'].shape==(n,4) and t['requests'].shape==(n,3)
    for a in t.values():assert np.isfinite(a).all()
    if external is not None:
        for key in ['states','controls','memory','requests']:close(t[key],external[key],'EXTERNAL_NATIVE_'+key)
    initial=dict(q.initial(x['packet']),steering_load_episode=initial_load)
    close(t['states'][0],initial['state'],'INITIAL_STATE')
    close(t['memory'][0],np.r_[initial['last_ctrl'],initial['integral']],'INITIAL_MEMORY')
    assert np.array_equal(t['memory'][1:,:4],t['controls']),'MEMORY_CONTROL_COVERAGE'
    assert (t['requests'][:,2]==0).all() and (t['requests'][-2200:]==0).all(),'FULL_FINAL_STOP'
    flags=[initial_load]
    for vr,wr,_ in t['requests']:
        assert 0<=vr<=.12,'FORWARD_ONLY'
        flags.append(True if vr>=.005 else flags[-1])
    engine=CountedEngine(x['setup'])
    geometry=q.Geometry(x,table)
    generations=r['generations'];assert len(generations)==(2 if 'handoff'in b else 1)
    expected_offsets=[0]
    if 'handoff'in b:expected_offsets.append(int(b['initial']['prefix_native']))
    segments=[]
    for index,offset in enumerate(expected_offsets):
        generation=generations[index];assert generation['offset']==offset,'GENERATION_ABSOLUTE_OFFSET'
        o=origin_at(t['states'][offset],t['memory'][offset],flags[offset])
        close(generation['origin']['state'],o['state'],'CARRIED_STATE')
        close(generation['origin']['last_ctrl'],o['last_ctrl'],'CARRIED_CTRL')
        assert abs(generation['origin']['integral']-o['integral'])<=1e-8,'CARRIED_INTEGRAL'
        assert generation['origin']['steering_load_episode']is flags[offset],'CARRIED_MODE'
        selection=b['initial'if index==0 else'onward'];saved=b['initial_ref'if index==0 else'onward_ref']
        rows=selection['rows'];assert rows and all(not mode and speed in [0.,.12] and type(count)is int and count>0 for turn,speed,count,mode in rows),'SOURCE_COMMANDS'
        ss,uu,mm=engine.simulate(o,rows)
        for key,value in [('states',ss),('controls',uu),('memory',mm)]:close(saved[key],value,'SOURCE_'+key)
        local=copy.deepcopy(x);local['packet']['controller_memory']['last_ctrl']=o['last_ctrl'].tolist()
        proof=q.proof(OffsetGeometry(geometry,offset),local,ss,uu,q.requests_of(rows),mm)
        assert proof['passed'],'REBUILT_SOURCE_PROOF'
        assert selection['passed'] and abs(selection['proof']['minimum_raw_m']-proof['minimum_raw_m'])<=1e-8,'SOURCE_PROOF_RECORD'
        if index==0 and 'handoff'in b:
            rows=selection['prefix_rows'];count=sum(row[2]for row in rows)
            assert count==expected_offsets[1] and rows[-1]==[0.,0.,2200,0],'COMPLETE_PREFIX_STOP'
            close(q.requests_of(rows),q.requests_of(selection['rows'])[:count],'PREFIX_SOURCE_BINDING')
            ss=ss[:count+1]
            h=b['handoff'];p=h['packet']
            assert h['native_offset']==count and p['native_tick']==start+count,'HANDOFF_NATIVE_TIME'
            assert abs(p['sim_time']-(x['packet']['sim_time']+.01*count))<=1e-8,'HANDOFF_ABSOLUTE_CLOCK'
            assert h['source_clock_unchanged']==x['source']['source_native_tick'],'SOURCE_CLOCK_REWRITE'
            close(q.initial(p)['state'],t['states'][count],'HANDOFF_PACKET_STATE')
            close(q.initial(p)['last_ctrl'],t['memory'][count,:4],'HANDOFF_PACKET_CTRL')
            assert abs(q.initial(p)['integral']-t['memory'][count,4])<=1e-8
            assert abs(t['states'][count,3:6]).max()<=.003 and abs(t['states'][count,7])<=.015,'HANDOFF_REST'
        segments.append((offset,rows,ss,'refuge_prefix'if index==0 and 'handoff'in b else'goal_reference'))
    cursor=0;reference_map=[];stop_positions=[]
    for offset,rows,ref,phase in segments:
        assert offset==cursor
        local_index=0
        for turn,speed,count,mode in rows:
            if speed==0. and count>=2200:stop_positions.append((cursor,int(count)))
            for _ in range(count):
                row=j[cursor]
                assert row['native']==start+cursor+1 and row['phase']==phase and row['reference_index']==local_index+1,'JOURNAL_NATIVE_PHASE'
                if speed==0.:vr=wr=0.
                else:vr,wr,_=q.tracking.request(t['states'][cursor],ref[local_index],float(turn),float(speed))
                close(t['requests'][cursor],[vr,wr,0.],'CAUSAL_FEEDBACK_REQUEST')
                reference_map.append(ref[local_index+1]);cursor+=1;local_index+=1
        assert local_index==len(ref)-1
    target=segments[-1][2][-1,:3];final_ref=segments[-1][2][-1]
    capture=0
    while cursor<n-2200:
        row=j[cursor];assert row['phase']=='capture' and row['native']==start+cursor+1
        vr,wr,status=q.capture.request(t['states'][cursor],target);assert status=='CAPTURING'
        close(t['requests'][cursor],[vr,wr,0.],'CAPTURE_REQUEST')
        reference_map.append(final_ref);cursor+=1;capture+=1
    assert capture<=600 and capture==r['capture_native']
    while cursor<n:
        row=j[cursor];assert row['phase']=='final_stop' and row['native']==start+cursor+1
        close(t['requests'][cursor],[0.,0.,0.],'FINAL_STOP_REQUEST')
        reference_map.append(final_ref);cursor+=1
    assert len(reference_map)==n
    delta=t['states'][1:]-np.asarray(reference_map)
    pose=np.c_[np.linalg.norm(delta[:,:2],axis=1),abs(np.arctan2(np.sin(delta[:,2]),np.cos(delta[:,2])))]
    assert (pose<=[.04,.035]).all(),'REFERENCE_MONITOR'
    # Rebuild allocation from each actual measured velocity, not shadow velocity.
    adapter=q.model.Predictor(x['setup'],initial).adapter
    for i,(vr,wr,_)in enumerate(t['requests']):
        close(np.r_[adapter.last,adapter.integral],t['memory'][i],'ACTUAL_ALLOCATION_MEMORY')
        u=adapter.compute(float(vr),float(wr),float(t['states'][i,3]),float(t['states'][i,5]),False)
        close(u,t['controls'][i],'ACTUAL_ACTUATOR_ALLOCATION')
    close(np.r_[adapter.last,adapter.integral],t['memory'][-1],'FINAL_ALLOCATION_MEMORY')
    shadow,_,_=engine.simulate(initial,[q.accelerator.row(float(v),float(w))for v,w,_ in t['requests']])
    close(shadow,t['shadow'],'INDEPENDENT_SHADOW')
    delta=t['states']-shadow
    response=np.c_[np.linalg.norm(delta[:,:2],axis=1),abs(np.arctan2(np.sin(delta[:,2]),np.cos(delta[:,2]))),abs(delta[:,6])]
    assert (response<=[.04,.035,.015]).all(),'RESPONSE_MONITOR'
    for i,row in enumerate(j):
        close(row['response_error'],response[i+1],'RESPONSE_ERROR_RECORD')
        close(row['pose_error'],pose[i],'POSE_ERROR_RECORD')
    assert len(r['scheduled_stops'])==len(stop_positions)
    for record,(offset,count)in zip(r['scheduled_stops'],stop_positions):
        assert record['offset']==offset
        o=origin_at(t['states'][offset],t['memory'][offset],flags[offset])
        close(record['origin']['state'],o['state'],'STOP_ORIGIN')
        close(record['origin']['last_ctrl'],o['last_ctrl'],'STOP_CTRL_MEMORY')
        assert abs(record['origin']['integral']-o['integral'])<=1e-8 and record['origin']['steering_load_episode']is flags[offset]
        ss,uu,mm=engine.simulate(o,[(0.,0.,count,0)])
        local=copy.deepcopy(x);local['goal']=ss[-1,:2].tolist();local['packet']['controller_memory']['last_ctrl']=o['last_ctrl'].tolist()
        tail=q.proof(OffsetGeometry(geometry,offset),local,ss,uu,q.requests_of([(0.,0.,count,0)]),mm)
        assert tail['passed'],'CURRENT_FULL_STOP'
        assert abs(record['proof']['minimum_raw_m']-tail['minimum_raw_m'])<=1e-8,'STOP_PROOF_RECORD'
    proof=q.proof(geometry,x,t['states'],t['controls'],t['requests'],t['memory'])
    sp=q.proof(geometry,x,shadow,t['controls'],t['requests'],t['memory'])
    assert proof['passed'] and sp['passed'],'COMPLETE_EXECUTED_PROOF'
    assert r['passed'] and abs(r['proof']['minimum_raw_m']-proof['minimum_raw_m'])<=1e-8,'FALSE_PASS_RECORD'
    assert np.linalg.norm(t['states'][-1,:2]-target[:2])<=.025
    angle=t['states'][-1,2]-target[2];assert abs(math.atan2(math.sin(angle),math.cos(angle)))<=.1
    return dict(passed=True,native_reviewed=n,generations=len(generations),full_stop_certificates=len(stop_positions),
        minimum_raw_m=proof['minimum_raw_m'],analytical_cpp_native=engine.native,models=0,new_mujoco_native=0,
        external_native_trace_bound=external is not None,physical_audit_complete=False)
