"""Finite canonical-vehicle reverse/zero-drive/restart component, no navigation."""
import fcntl
import importlib.abc
import signal
import sys
import time
import traceback
from component_context import *
from native_component import binding
from gear_handoff import GearHandoff


def main():
    task=read(sys.argv[1]);window=read(O/'ROUND_WINDOW.json');authorize(task,window)
    assert task['stage']=='component' and task['dynamic'] is False
    if '--entry-check' in sys.argv:
        class NoPhysical(importlib.abc.MetaPathFinder):
            def find_spec(self,name,*extra):
                if name.split('.')[0] in {'mujoco','vehicle','torch'}:raise AssertionError('ENTRY_MODELS_FORBIDDEN '+name)
        sys.meta_path.insert(0,NoPhysical())
        old,Adapter,factory,replay=binding()
        print(json.dumps(dict(passed=True,actual_adapter_binding=True,models=0,physical_native=0)));return 0
    assert not (R/'REVIEW_PENDING').exists(),'REVIEW_HOLD'
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    out=Path(task['output']);old,Adapter,factory,replay=binding();np=old.np
    result=dict(passed=False,scope='reverse_zero_drive_measured_rest_component_not_navigation',
        canonical_vehicle_initializations=0,new_actual_native=0,own_replay_native=0,private_mujoco_native=0,training_updates=0)
    v=None;in_step=False;creating=False;journal=[];gate=GearHandoff();begin=time.monotonic()
    def deadline(*args):raise TimeoutError('COMPONENT_HARD_DEADLINE')
    signal.signal(signal.SIGALRM,deadline);signal.signal(signal.SIGTERM,deadline)
    signal.setitimer(signal.ITIMER_REAL,min(280.,max(.01,remaining(window)-10)))
    def step(vr,wr,phase):
        nonlocal in_step
        assert remaining(window)>100 and time.monotonic()-begin<180,'COMPONENT_ROOT_RESERVE'
        body=list(v.body());enc=v.steering_sample().copy();request=[vr,wr,False]
        vr,wr,proof=gate.select(vr,wr,native_tick=v.count,body=body,last_ctrl=v.adapter.last,encoders=enc)
        row=dict(before_native=v.count,phase=phase,upstream_request=request,request=[vr,wr,False],
            body=body,encoders=enc,last_ctrl=v.adapter.last.copy(),integral=v.adapter.integral,gear_handoff=proof,applied=False)
        journal.append(row);v.adapter.parked_target=None;in_step=True;v.step(vr,wr,False);in_step=False;row['applied']=True
        if v.count%5==0:v.scan()
        return row
    try:
        import mujoco as mj
        creating=True;v=factory.create_vehicle(out/'physics',task);creating=False;result['canonical_vehicle_initializations']=1;old.pin()
        previous=v.adapter;v.adapter=Adapter(v.m,mj,v.dt,encoders=previous.encoders);v.adapter.virtual_rate=.6;v.adapter.last=previous.last.copy();v.adapter.integral=previous.integral
        dump(out/'INITIAL_PACKET.json',old.packet(v));v.scan()
        for _ in range(200):step(-.08,0.,'INITIAL_REVERSE')
        reverse_origin=v.count
        for _ in range(100):
            step(0.,0.,'ZERO_DRIVE_INTERRUPTION')
            if abs(v.adapter.last[2:]).max()<=1e-10:break
        feedback=old.packet(v);stimulus=abs(v.adapter.last[2:]).max()<=1e-10 and abs(feedback['body'][3])>.003
        dump(out/'RESTART_STIMULUS.json',dict(stimulus_reproduced=stimulus,packet=feedback,initial_reverse_end=reverse_origin))
        assert stimulus,'PHYSICAL_REVERSE_RESTART_STIMULUS_NOT_REPRODUCED'
        restart=v.count;release=None
        for _ in range(300):
            row=step(-.08,0.,'FRESH_REVERSE_RESTART')
            if row['gear_handoff']['released']:release=dict(native_tick=row['before_native'],body=row['body'],proof=row['gear_handoff'],xy=list(v.body()[:2]))
        after=list(v.body());distance=0. if release is None else float(np.linalg.norm(np.asarray(after[:2])-release['xy']))
        result['component_checks']=dict(actual_moving_zero_drive_stimulus=stimulus,
            same_gear_reentry_held200=release is not None and release['native_tick']-restart>=200,
            released_at_measured_rest=release is not None and release['proof']['measured_rest'],
            resumed_reverse_motion=after[3]<-.02 and distance>=.02)
        dump(out/'COMPONENT_RELEASE.json',dict(restart_native=restart,release=release,actual_post_release_distance_m=distance,after_body=after))
        for _ in range(200):step(0.,0.,'COMPLETE_STOP_TAIL')
        final=old.packet(v);dump(out/'FINAL_PACKET.json',final)
        result['component_checks'].update(final_body_stopped=max(abs(x) for x in final['body'][3:])<=.003,
             final_drive_zero=abs(v.adapter.last[2:]).max()<=1e-10)
        result['passed']=all(result['component_checks'].values())
    except BaseException as exc:
        result.update(passed=False,error=repr(exc),traceback=traceback.format_exc())
        if v is not None and not in_step and remaining(window)>120:
            try:
                for _ in range(200):step(0.,0.,'COMPLETE_STOP_TAIL')
                dump(out/'FINAL_PACKET.json',old.packet(v));result['error_stop_tail_completed']=True
            except BaseException as stopping:result['stop_tail_error']=repr(stopping)
    finally:
        result.update(new_actual_native=None if in_step else v.count if v is not None else 0,
             canonical_vehicle_initializations=None if creating else result['canonical_vehicle_initializations'],model_native_inflight_unknown=in_step)
        dump(out/'APPLIED_JOURNAL.json',journal)
        if v is not None:
            try:result['physical']=v.finish();result['evidence_saved']=True
            except BaseException as exc:result.update(passed=False,save_error=repr(exc))
            if result.get('evidence_saved') and not in_step:
                try:
                    proof=replay(v,min(time.time()+120,window['absolute_deadline_unix']-5),out/'physics')
                    result.update(replay=proof,own_replay_native=proof['replay_native'],passed=result['passed'] and proof['passed'])
                except BaseException as exc:result.update(passed=False,replay_error=repr(exc))
        result.update(closed=True,source_unchanged=sources(),wall_s=time.monotonic()-begin)
        dump(out/'RESULT.json',result);signal.setitimer(signal.ITIMER_REAL,0);fcntl.flock(lock,fcntl.LOCK_UN)
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
