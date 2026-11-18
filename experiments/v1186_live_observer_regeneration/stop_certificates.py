"""Original complete stop contract on current-state regenerated maneuvers."""
from current_state_tools import original,R,O
import json,time,math
q=original.q;np=q.np
def flags_before(rows):
    coupled=active=load=False;answer=[dict(coupled_episode=False,steering_motion_active=False,steering_load_episode=False)]
    for turn,speed,n,mode in rows:
        for _ in range(int(n)):
            if mode:coupled=True;load=False
            elif speed<=-.005:coupled=False;load=False
            elif speed>=.005:coupled=False;load=True
            active=bool(mode);answer.append(dict(coupled_episode=coupled,steering_motion_active=active,steering_load_episode=load))
    return answer
def forecast(x,state,memory,ticks):
    import recovery_source
    p=recovery_source.forecast_packet(x['packet'],state,memory,ticks);p['body_lateral']=float(state[4]);return p
def prove(engine,g,x,p,origin,block):
    proofs=[];predictions=[]
    for schedule in [[(0.,0.,2200,0)],[*block,(0.,0.,2200,0)]]:
        ss,uu,mm=engine.simulate(origin,schedule);target=ss[-1,:3].tolist();pr,_=g.final(dict(x,packet=p,goal=target[:2],safe_terminal_pose=target),ss,uu,schedule)
        proofs.append(pr);predictions.append(ss)
    return proofs,predictions
def certify_reference(x,table,rows,states,memory,deadline,checkpoint=lambda _:None):
    engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);g=q.Geometry(x,table);flags=flags_before(rows);offset=0;records=[]
    while offset<len(states)-1:
        assert time.monotonic()<deadline,'STOP_CERTIFICATE_QUALIFICATION_DEADLINE'
        suffix=original.remaining_rows(rows,offset);first=suffix[0];n=int(first[2])if first[3]or first[1]==0. else min(8,int(first[2]));block=original.front(suffix,n)
        p=forecast(x,states[offset],memory[offset],offset);origin=dict(state=states[offset],last_ctrl=memory[offset,:4],integral=float(memory[offset,4]),**flags[offset]);p.update({k:v for k,v in flags[offset].items()if k!='steering_load_episode'})
        proofs,_=prove(engine,g,x,p,origin,block);record=dict(offset=offset,prefix=n,current_passed=proofs[0]['passed'],prospective_passed=proofs[1]['passed'],current_raw=proofs[0]['minimum_raw_m'],prospective_raw=proofs[1]['minimum_raw_m'],failed=[k for proof in proofs for k,v in proof['checks'].items()if not v]);records.append(record)
        if not all(p['passed']for p in proofs):return dict(passed=False,records=records,failed_offset=offset,analytical_cpp_native=engine.native)
        offset+=n
        if len(records)%100==0:checkpoint(dict(stage='complete_stop_certificates',offset=offset,certificates=len(records),cpp_native=engine.native))
    return dict(passed=True,records=records,analytical_cpp_native=engine.native)
def main():
    import fcntl,signal
    f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('TWO_CERTIFICATIONS_600S')));signal.alarm(600);results=[]
    for slot in['01','02']:
        x=json.loads((R/('runs/v858_nav2_verified/v1185/main_slot'+slot+'/OBSERVATION_ENTRY.json')).read_text());plan=json.loads((O/('REFUGE_'+slot+'.json')).read_text())
        with np.load(O/('REFUGE_'+slot+'.npz'))as z:ss=z['states'].copy();mm=z['memory'].copy()
        with np.load(O/('TABLE_'+slot+'.npz'))as z:table={k:z[k].copy()for k in z.files}
        result=certify_reference(x,table,plan['rows'],ss,mm,time.monotonic()+280,lambda p:q.dump(O/'STOP_CERT_PROGRESS.json',dict(slot=slot,**p)));q.dump(O/('STOP_CERT_'+slot+'.json'),result);results.append(dict(slot=slot,passed=result['passed'],certificates=len(result['records']),failed_offset=result.get('failed_offset'),cpp_native=result['analytical_cpp_native']))
    q.dump(O/'STOP_CERT_RESULT.json',dict(passed=all(r['passed']for r in results),cases=results,models=0,new_mujoco_native=0));print(json.dumps(results))
if __name__=='__main__':main()
