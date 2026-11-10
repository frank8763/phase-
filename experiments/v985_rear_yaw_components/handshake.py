"""Pure-data startup contract; this module cannot import or initialize a model."""
from dataclasses import dataclass,field
import hashlib,json,math
from pathlib import Path

NODES=('map_server','planner_server','controller_server','behavior_server',
       'velocity_smoother','collision_monitor','bt_navigator')
class ProtocolError(RuntimeError):pass
def require(condition,message):
    if not condition:raise ProtocolError(message)
def file_sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def verify_sources(root,manifest):
    data=json.loads(Path(manifest).read_text());root=Path(root).resolve()
    for relative,expected in data['files'].items():
        p=root/relative;require(p.resolve().is_relative_to(root),'SOURCE_OUTSIDE_PHASE')
        require(p.is_file()and file_sha(p)==expected,'FROZEN_SOURCE_CHANGED '+relative)
def authorized(task,receipt,now,freeze_sha):
    """Fail before any ROS or physics import if a future user authority is absent."""
    require(receipt.get('models_authorized') is True,'MODELS_NOT_AUTHORIZED')
    require(receipt.get('scope')=='ONE_STATIC_WEST_EAST','WRONG_AUTHORIZATION_SCOPE')
    require(receipt.get('source_freeze_sha256')==freeze_sha,'SOURCE_AUTHORITY_MISMATCH')
    require(receipt.get('run_id')==task['run_id'],'RUN_AUTHORITY_MISMATCH')
    require(receipt.get('task_sha256')==hashlib.sha256(json.dumps(task,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'TASK_AUTHORITY_MISMATCH')
    start=receipt.get('started_unix');end=receipt.get('deadline_unix')
    require(isinstance(start,(float,int))and isinstance(end,(float,int))and math.isfinite(start)and math.isfinite(end),'ABSOLUTE_WINDOW_REQUIRED')
    require(start<=now<end-30 and end>start,'EXPIRED_OR_NOT_STARTED_WINDOW')
    require(task['case_id']=='WEST_EAST'and task['seed']==10010001 and task['dynamic'] is False,'TASK_SCOPE_CHANGED')
    require(task['wall_limit_s']==180 and task['brake_s']==2.,'TASK_BUDGET_CHANGED')
    return float(end)
@dataclass
class Startup:
    run_id:str
    phase:str='WAITING'
    armed_at:float|None=None
    command:dict|None=None
    last_sequence:int=-1
    events:list=field(default_factory=list)
    def receive(self,packet,now,native_tick,sim_time):
        require(packet.get('run_id')==self.run_id,'FOREIGN_RUN')
        kind=packet.get('kind')
        if kind=='stop':
            self.phase='STOPPING';self.events.append(dict(event='STOP',at=now));return
        if kind=='arm':
            if self.phase!='WAITING':
                self.events.append(dict(event='DUPLICATE_ARM_IGNORED',at=now));return
            require(native_tick==0 and abs(sim_time)<1e-12,'PHYSICS_ADVANCED_BEFORE_ARM')
            require(packet.get('native_tick')==0 and packet.get('sim_time')==0.,'ARM_NOT_FOR_T0')
            require(set(packet.get('states',{}))==set(NODES),'INCOMPLETE_ACTIVE_SET')
            require(all(packet['states'][name]==3 for name in NODES),'NODE_NOT_ACTIVE')
            for name in NODES:
                measured=packet.get('checked_at',{}).get(name)
                require(isinstance(measured,(int,float))and math.isfinite(measured)and -.05<=now-measured<=1.,'STALE_ACTIVE_PROOF')
            issued=packet.get('issued_at');require(isinstance(issued,(int,float))and math.isfinite(issued)and -.05<=now-issued<=.2,'STALE_ARM')
            self.phase='RUNNING';self.armed_at=now;self.events.append(dict(event='ARMED_AT_T0',at=now,native_tick=0,states=dict(packet['states']),checked_at=dict(packet['checked_at']),issued_at=issued));return
        require(kind=='command','UNKNOWN_PACKET')
        require(self.phase=='RUNNING','COMMAND_BEFORE_ARM')
        seq=packet.get('sequence');require(type(seq)is int and seq>self.last_sequence,'NONINCREASING_COMMAND_SEQUENCE')
        issued=packet.get('issued_at');require(isinstance(issued,(int,float))and math.isfinite(issued)and -.05<=now-issued<=.2,'STALE_OR_FUTURE_COMMAND')
        require(all(isinstance(packet.get(k),(int,float))and math.isfinite(packet[k])for k in ['v','w']),'NONFINITE_BODY_COMMAND')
        self.last_sequence=seq;self.command=dict(packet)
    def controls(self,now):
        if self.phase!='RUNNING' or self.command is None or now-self.command['issued_at']>.2:return 0.,0.,True
        return float(self.command['v']),float(self.command['w']),False
    def step(self,vehicle,now):
        """The only production seam allowed to call Vehicle.step."""
        require(self.armed_at is not None,'NATIVE_STEP_BEFORE_ARM')
        v,w,stale=self.controls(now);vehicle.step(v,w,stale)
def policy_packet(run_id,vehicle,snapshot,snapshot_at,now,phase):
    """Truth stripping belongs to the real send path, not only the tests."""
    return dict(kind='observation',run_id=run_id,phase=phase,native_tick=vehicle.count,
                sim_time=float(vehicle.d.time),sent_at=now,body_measured_at=now,
                scan_measured_at=snapshot_at,initial_snapshot=phase=='WAITING',
                body=list(vehicle.body()),scan={k:snapshot[k]for k in ['native_tick','time','ranges']})
def require_goal_allowed(observation,run_id,now):
    require(observation is not None and observation.get('run_id')==run_id,'GOAL_WITHOUT_CURRENT_BACKEND')
    require(observation.get('phase')=='RUNNING','GOAL_BEFORE_ARM_ACK')
    require(-.05<=now-observation['sent_at']<=.25,'GOAL_WITH_STALE_BACKEND')
