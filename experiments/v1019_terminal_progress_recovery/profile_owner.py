"""Single owner: original Nav2 finite tubes or one committed recovery profile."""
import hashlib,importlib.util,json,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=load('v1004_original_ingress',R/'experiments/v968_rpp_closed_loop_night/native_contract.py')
law=load('v1004_qualified_allocator',R/'experiments/v993_steering_transient_diagnosis/vehicle_control.py')

def switch(vehicle,cls):
    import mujoco as mj
    old=vehicle.adapter;before={k:np.asarray(getattr(vehicle.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
    body=vehicle.body();enc=vehicle.steering_sample()
    assert abs(np.asarray(body[3:])).max()<=.03 and abs(np.asarray(enc[2:])).max()<=.03,'SWITCH_NOT_ACTUALLY_STOPPED'
    assert abs(old.last[2:]).max()<=1e-10,'SWITCH_REAR_TARGETS_NOT_STOPPED'
    new=cls(vehicle.m,mj,vehicle.dt,encoders=old.encoders)
    assert type(new.commands)is type(old.commands)and new.commands.ids==old.commands.ids
    new.last=old.last.copy();new.integral=float(old.integral);new.mode=old.mode
    if cls is law.Adapter:new.virtual_rate=.6
    vehicle.adapter=new
    assert all(np.array_equal(v,np.asarray(getattr(vehicle.d,k)))for k,v in before.items()),'SWITCH_WROTE_PHYSICAL_STATE'
    return dict(native_tick=vehicle.count,adapter='V993'if cls is law.Adapter else'V958',last_ctrl=new.last.tolist(),integral=new.integral,physical_state_unchanged=True)


def valid_capture(plan,states):
    return plan.get('goal_capture')is True and plan.get('terminal_goal_distance_upper_m') is not None and abs(plan['terminal_goal_distance_upper_m']-(float(np.linalg.norm(states[-1,:2]-plan['original_goal']))+.08))<=1e-12 and plan['terminal_goal_distance_upper_m']<=.45

class Startup(base.Startup):
    def bind_vehicle(self,vehicle,out):
        self.vehicle=vehicle;self.out=Path(out);self.profile=None;self.holding=False;self.profile_index=0
        self.profiles=[];self.switches=[];self.active_profile_id=None
        vehicle.profile_status=dict(active=False,completed_id=None,released_id=None)
    def receive(self,packet,now,native_tick,sim_time):
        kind=packet.get('kind');self._journals()
        if kind not in {'commit_profile','release_profile'}and not(kind=='command'and(self.profile is not None or self.holding)):
            return super().receive(packet,now,native_tick,sim_time)
        prior=None if self.command is None else self.command['sequence']
        row=dict(packet=packet,received_at=now,native_tick=native_tick,sim_time=sim_time,prior_sequence=prior,retained_sequence=prior)
        try:
            assert packet['run_id']==self.run_id and self.phase=='RUNNING','PROFILE_FOREIGN_OR_STOPPED'
            if kind=='command':row['decision']='PROFILE_OWNER_IGNORED';return
            assert 0<=now-packet['issued_at']<=.05,'PROFILE_DELIVERY_OVER_50MS'
            if kind=='release_profile':
                assert self.profile is None and self.holding and packet['profile_id']==self.active_profile_id,'PROFILE_NOT_COMPLETE'
                self.switches.append(switch(self.vehicle,law.base.Adapter));self.holding=False;self.command=None
                self.vehicle.profile_status['released_id']=self.active_profile_id;row['retained_sequence']=None;row['decision']='PROFILE_RELEASED';return
            assert self.profile is None and not self.holding,'PROFILE_ALREADY_OWNS_CONTROL'
            path=Path(packet['path']);assert path.resolve().is_relative_to(self.out.resolve())and path.is_file()and path.stat().st_size<=4*1024*1024,'PROFILE_FILE_SCOPE'
            raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==packet['sha256'],'PROFILE_SHA_CHANGED'
            record=json.loads(raw);plan=record['plan'];states=np.asarray(plan['state_path']);requests=np.asarray(plan['planned_body_requests'],float)
            assert plan['passed']and plan['status']=='CAUSAL_PLANNED_INPUT_REFERENCE'and 200<len(requests)<=4208 and states.shape==(len(requests)+1,8)
            assert np.isfinite(states).all()and np.isfinite(requests).all()and requests.shape==(len(requests),3)
            assert np.all(requests[:-200,0]==.03)and np.all(requests[-200:]==[0.,0.,0.])and np.all(requests[:,2]==0.)
            assert np.max(abs(requests[:,1]))<=.03*.758770385+1e-10,'PROFILE_REQUEST_OUTSIDE_QUALIFIED_DOMAIN'
            assert plan['source_native_tick']==record['source']['source_native_tick']<=plan['body_native_tick']==record['packet']['native_tick']<=native_tick
            assert np.linalg.norm(np.asarray(self.vehicle.body()[:2])-states[0,:2])<=.002 and abs(self.vehicle.body()[2]-states[0,2])<=.002,'PROFILE_INITIAL_POSE_DRIFT'
            assert np.max(abs(self.vehicle.adapter.last-plan['initial']['last_ctrl']))<=1e-8 and abs(self.vehicle.adapter.integral-plan['initial']['integral'])<=1e-8,'PROFILE_INITIAL_MEMORY_CHANGED'
            assert plan['minimum_raw_full_cycle_clearance_m']>=plan['required_raw_clearance_m']and (plan['actual_goal_progress_lower_m']>=.4 or valid_capture(plan,states)),'PROFILE_WITHOUT_FULL_CYCLE_OR_PROGRESS_OR_GOAL'
            pid=packet['profile_id'];assert pid==len(self.profiles)+1,'PROFILE_ORDER_CHANGED'
            self.switches.append(switch(self.vehicle,law.Adapter));self.command=None
            self.active_profile_id=pid;self.profile_index=0;self.profile=record
            self.profiles.append(dict(profile_id=pid,path=str(path),sha256=packet['sha256'],start_native_tick=native_tick,completed=False))
            self.vehicle.profile_status=dict(active=True,profile_id=pid,completed_id=self.vehicle.profile_status['completed_id'],released_id=self.vehicle.profile_status['released_id'])
            row['decision']='PROFILE_COMMITTED';row['retained_sequence']=None
        except BaseException as e:row.update(decision='REJECTED_ABORT',error=repr(e));raise
        finally:self.receipts.append(row)
    def step(self,vehicle,now):
        if self.profile is None and not self.holding:
            super().step(vehicle,now);self.execution[-1]['owner']='NAV2_FINITE_TUBE';return
        request=[0.,0.,False]if self.profile is None or self.phase!='RUNNING'else self.profile['plan']['planned_body_requests'][self.profile_index]
        row=dict(native_tick=vehicle.count+1,at=now,phase=self.phase,sequence=None,controls=request,completed=False,
            owner='COMMITTED_RECOVERY'if self.profile is not None else'RECOVERY_STOP_HOLD',profile_id=self.active_profile_id,profile_index=self.profile_index)
        self.execution.append(row);vehicle.step(*request);row['completed']=True
        body=vehicle.body();assert abs(body[3])<=.13 and abs(body[4])<=.16,'EMPIRICAL_BODY_BOUND_EXCEEDED'
        if self.profile is None or self.phase!='RUNNING':return
        self.profile_index+=1;expected=self.profile['plan']['state_path'][self.profile_index]
        p=float(np.linalg.norm(np.asarray(body[:2])-expected[:2]));d=body[2]-expected[2];a=abs(math.atan2(math.sin(d),math.cos(d)))
        assert p<=.04 and a<=.035,'COMMITTED_RECOVERY_ACTUAL_TRACKING_FAILED'
        if self.profile_index==len(self.profile['plan']['planned_body_requests']):
            if self.profile['plan'].get('goal_capture'):assert np.linalg.norm(np.asarray(body[:2])-self.profile['plan']['original_goal'])<=.45,'ACTUAL_GOAL_CAPTURE_FAILED'
            self.profiles[-1].update(completed=True,end_native_tick=vehicle.count);self.profile=None;self.holding=True
            vehicle.profile_status.update(active=False,completed_id=self.active_profile_id,end_native_tick=vehicle.count)
    def save(self,out):
        Path(out,'PROFILE_EXECUTION.json').write_text(json.dumps(dict(profiles=getattr(self,'profiles',[]),adapter_switches=getattr(self,'switches',[])),indent=2)+'\n')
