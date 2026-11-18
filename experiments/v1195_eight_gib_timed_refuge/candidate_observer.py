"""Regenerate a certified observation refuge; never call it goal arrival."""
from current_state_tools import original,R,O,validate_input
import math,time,json,copy
q=original.q;np=q.np
def candidate_rows(turn,ticks,cut):
    warm=json.loads((R/'runs/v1144_saved_entry_relay/software/ROWS.json').read_text())['rows']
    rows=original.front(warm,int(cut))+[(0.,0.,2200,0)]
    if ticks:rows=[(float(turn),.08,int(ticks),0),(0.,0.,2200,0)]+rows
    return rows
def synthesize(x,table,deadline,checkpoint=lambda _:None):
    validate_input(x)
    g=q.Geometry(x,table);e=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);org=dict(q.initial(x['packet']),steering_load_episode=False);trials=[];best=None
    catalog=[(0.,0)]+[(t,n)for n in[200,400,600,800]for t in[0.,-.16,-.24,-.32,-.42722137342572125]]
    for turn,ticks in catalog:
        for cut in[11400, 11800]:
            assert time.monotonic()<deadline,'CURRENT_OBSERVER_SYNTHESIS_BUDGET'
            rows=candidate_rows(turn,ticks,cut);ss,uu,mm=e.simulate(org,rows);one=dict(x,goal=ss[-1,:2].tolist(),safe_terminal_pose=ss[-1,:3].tolist());proof,_=g.final(one,ss,uu,rows)
            progress=float(np.linalg.norm(np.array(x['packet']['body'][:2])-x['goal'])-np.linalg.norm(ss[-1,:2]-x['goal']));proof['checks']['observation_progress']=progress>=.5;proof['passed']=bool(all(proof['checks'].values()))
            target=np.array([1.68, -1.18, -0.74]);distance=float(np.linalg.norm(ss[-1,:2]-target[:2]));yaw=abs(math.atan2(math.sin(ss[-1,2]-target[2]),math.cos(ss[-1,2]-target[2])));rank=(distance+.2*yaw,-proof['minimum_raw_m'],len(uu))
            trials.append(dict(turn=turn,stage_native=ticks,cut=cut,passed=proof['passed'],raw=proof['minimum_raw_m'],progress=progress,refuge_guide_distance=distance,failed=[k for k,v in proof['checks'].items()if not v]))
            if proof['passed']and(best is None or rank<best[0]):best=(rank,rows,ss,uu,mm,proof,trials[-1])
        checkpoint(dict(stage='current_refuge_proposals',done=len(trials),eligible=sum(t['passed']for t in trials),cpp_native=e.native))
    answer=dict(passed=best is not None,trials=trials,analytical_cpp_native=e.native,scope='observation refuge only; original goal remains separate live synthesis',models=0,new_mujoco_native=0)
    if best:
        _,rows,ss,uu,mm,proof,selection=best;answer.update(rows=rows,states=ss,controls=uu,memory=mm,proof=proof,selected=selection,current_entry_native=x['packet']['native_tick'],current_clock=x['packet']['sim_time'])
    return answer
def main():
    import fcntl,signal
    f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('REFUGE_300S')));signal.alarm(300);answers=[]
    for slot in['01','02']:
        x=json.loads((R/('runs/v858_nav2_verified/v1185/main_slot'+slot+'/OBSERVATION_ENTRY.json')).read_text())
        with np.load(O/('TABLE_'+slot+'.npz'))as z:table={k:z[k].copy()for k in z.files}
        result=synthesize(x,table,time.monotonic()+130,lambda p:q.dump(O/'REFUGE_PROGRESS.json',dict(slot=slot,**p)))
        if result['passed']:np.savez_compressed(O/('REFUGE_'+slot+'.npz'),**{k:result.pop(k)for k in['states','controls','memory']})
        q.dump(O/('REFUGE_'+slot+'.json'),result);answers.append(dict(slot=slot,passed=result['passed'],selected=result.get('selected'),cpp_native=result['analytical_cpp_native']))
    q.dump(O/'REFUGE_RESULT.json',dict(cases=answers,passed=all(r['passed']for r in answers),models=0,new_mujoco_native=0));print(json.dumps(answers))
if __name__=='__main__':main()
