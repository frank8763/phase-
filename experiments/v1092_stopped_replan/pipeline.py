"""Finite recovery: execute, actually stop, sense, then replan; at most eight."""
import sys,types,time,math,json
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];CORE=R/'experiments/rpccr_execution_core'
sys.path.insert(0,str(C));import corridor
sys.path.insert(0,str(R/'experiments/v1091_certified_exit'));import stop
import live_reference as live
from physical_ops import bind,dump
from braking_reserve import Adapter
from kernel import virtual
original=types.ModuleType('unchanged_complete_goal_owner');original.__file__=str(CORE/'fresh_pipeline.py');exec(compile((CORE/'fresh_pipeline.py').read_text(),original.__file__,'exec'),original.__dict__)
configure=original.configure
def eligible(error):return str(error)=='LIVE_COMPLETE_STATIC_REFERENCE_REQUIRED'or str(error).startswith("('NO_LIVE_COMPLETE_DYNAMIC_REFERENCE'")
def execute(v,setup,goal_seed,end,evidence,out,packet_fn,output):
    import mujoco as mj
    started=time.monotonic();events=[];segments=__import__('owner')._active_corridor_result['_direct_segments']
    for renewal in range(9):
        bind(v,Adapter,mj);packet=packet_fn(v,True);packet['speed_episode']=False;source=evidence.source(v)
        if np.linalg.norm(np.asarray(v.body()[:2])-goal_seed['goal'])<=.45:
            assert np.linalg.norm(v.d.qvel[:2])<=.03 and abs(v.body()[4])<=.03,'ACTUAL_GOAL_STOP_REQUIRED'
            return dict(passed=True,mode='FINITE_GLOBAL_TO_ACTUAL_GOAL',root_native=events[0]['origin_native']if events else v.count,active_corridor_stages=len(events),total_recovery_wall_s=time.monotonic()-started)
        assert renewal<8,'EIGHT_FINITE_RECOVERY_EPISODES_EXHAUSTED'
        assert np.linalg.norm(v.d.qvel[:2])<=.03 and abs(v.body()[4])<=.03,'REPLAN_REQUIRES_ACTUAL_STOP'
        q=corridor.construct(setup,packet,source,output,goal_seed['goal'])
        stage=dict(stage=renewal,packet=packet,source=source,goal=goal_seed['goal'],
                   selected_proof=q['proof'],candidates=q['candidates'],requests=q['requests'].tolist(),
                   origin_native=v.count,policy='FINITE_GLOBAL_TO_ACTUAL_GOAL')
        events.append(stage);dump(out/'ACTIVE_CORRIDOR_STAGES.json',events)
        origin=np.array(v.body()[:2]);cursor=0;maximum=np.zeros(3)
        while cursor<len(q['requests']):
            assert time.time()<end-120,'CORRIDOR_REPLAY_RESERVE'
            at=packet_fn(v,True);at['speed_episode']=False;remaining=q['requests'][cursor:]
            certificate,states,controls=corridor.proof(setup,at,source,remaining)
            if not certificate['passed']:
                # A rejected future proposal causes the qualified real brake,
                # never direct process exit and never continued rejected input.
                folder=out/('rejected_stop_%02d'%renewal);folder.mkdir(exist_ok=False)
                dump(folder/'REJECTED_FUTURE.json',dict(packet=at,source=source,requests=remaining.tolist(),proof=certificate))
                stopped=stop.execute(v,setup,at,source,folder,stop.REJECTION,lambda scan:evidence.update(scan))
                with np.load(folder/'CERTIFIED_EXIT_PLAN.npz')as saved:
                    stop_states=saved['states'];stop_controls=saved['controls'];stop_requests=saved['requests']
                path=folder/'DIRECT_STOP.json'
                dump(path,dict(passed=True,scope='CERTIFIED_REJECTION_STOP',packet=at,source=source,
                               planned_body_requests=stop_requests.tolist(),state_path=stop_states.tolist(),
                               predicted_actuator_controls=stop_controls.tolist(),proof=stopped['proof'],
                               rejected_future=str((folder/'REJECTED_FUTURE.json').relative_to(R))))
                segments.append(dict(path=str(path.relative_to(R)),origin_native=stopped['start_native'],executed_native=2200,label='CERTIFIED_REJECTION_STOP'))
                dump(out/'DIRECT_SEGMENTS.json',segments);stage['rejected_future_stopped']=True;break
            count=len(remaining)if np.array_equal(remaining,np.zeros_like(remaining))else min(125,len(remaining)-2200)
            assert count>0
            path=out/('ACTIVE_CORRIDOR_%02d_%05d.json'%(renewal,cursor))
            dump(path,dict(passed=True,scope='FULL_CYCLE_FINITE_ACTIVE_CORRIDOR',packet=at,source=source,
                           stage=renewal,first_in_stage=cursor==0,planned_body_requests=remaining.tolist(),
                           state_path=states.tolist(),predicted_actuator_controls=controls.tolist(),proof=certificate))
            row=dict(path=str(path.relative_to(R)),origin_native=v.count,executed_native=0,label='ACTIVE_CORRIDOR',source_kind='FINITE_RECOVERY_NOT_ARRIVAL');segments.append(row)
            try:
                for i,request in enumerate(remaining[:count]):
                    v.step(*request);body=np.asarray(v.body());angle=body[2]-states[i+1,2]
                    difference=[np.linalg.norm(body[:2]-states[i+1,:2]),abs(math.atan2(math.sin(angle),math.cos(angle))),abs(virtual(v.steering_sample()[:2])-states[i+1,6])]
                    maximum=np.maximum(maximum,difference)
                    assert np.all(maximum<=[.04,.035,.015]),'CORRIDOR_LOCAL_TRACKING'
                    assert abs(body[3])<=.13 and abs(body[4])<=.16,'CORRIDOR_BODY_CAP'
                    if v.count%5==0:evidence.update(v.scan())
            finally:row['executed_native']=v.count-row['origin_native'];dump(out/'DIRECT_SEGMENTS.json',segments)
            cursor+=count;dump(out/'PARTIAL.json',dict(phase='STOPPED_FINITE_REPLAN',stage=renewal,native=v.count,executed_corridor_native=cursor,total_corridor_native=len(q['requests'])))
        assert np.linalg.norm(v.d.qvel[:2])<=.03 and abs(v.body()[4])<=.03,'FINITE_EPISODE_ACTUAL_STOP_REQUIRED'
        stage.update(end_native=v.count,actual_motion_m=float(np.linalg.norm(np.asarray(v.body()[:2])-origin)),maximum_local_tracking=maximum.tolist())
        dump(out/'ACTIVE_CORRIDOR_STAGES.json',events);continue
    raise AssertionError('NO_COMPLETE_GOAL_AFTER_EIGHT_FINITE_EPISODES')
