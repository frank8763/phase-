"""Full current owner plus explicit original stop-tail evidence per event kind."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=exact('v1422_complete_current_owner',R/'experiments/v1415_unified_causal_witness/event_owner.py')
sessions=exact('v1483_original_event_sessions',C/'session.py')
geometry=exact('v1483_current_MPPI_geometry',C/'geometry_binding.py')
controller=exact('v1483_MPPI_owner_identity',C/'controller_identity.py')
dispatch=exact('v1483_disclosed_shared_methods',C/'method_dispatch.py')
base=old.base
measured_identity=old.base.base.measured_identity

def stop_evidence(vehicle,request):
 required=sessions.event.validate_request(request);tick=vehicle.count
 assert request['actual']['wire']['native_tick']==tick and tick-request['brake_start']>=required
 assert len(vehicle.commands)==len(vehicle.rows)==tick and len(vehicle.contacts)==tick+1 and vehicle.audit.native_count==tick and vehicle.bad==0,'ACTUAL_STOP_TAIL_RECORD_COVERAGE'
 tail=vehicle.commands[-required:];assert len(tail)==required and all(row[1]==row[2]==0. and row[5]is False for row in tail),'ACTUAL_APPLIED_ZERO_STOP_TAIL_NOT_COMPLETE'
 assert max(abs(x)for x in vehicle.body()[3:])<=.003 and max(abs(x)for x in vehicle.steering_sample()[2:])<=.03 and max(abs(x)for x in vehicle.adapter.last[2:])<=1e-10
 return dict(event_kind=request['event']['kind'],required_native=required,actual_native=tick,applied_commands_sha256=sessions.event.digest(tail),no_extra_native_steps=True)

class OwnerRequest(old.OwnerRequest):
 def __init__(self,notice,*,output,vehicle,mode_memory,gear,run_id,last_event_index,now,controller_identity_sha256):
  output=Path(output).resolve();assert output.is_relative_to(R/'runs');self.output=output
  assert notice['kind']=='BRIDGE_CERTIFICATE_REQUEST_FILE'and notice['run_id']==run_id
  assert type(notice['event_index'])is int and notice['event_index']==last_event_index+1,'NATIVE_EVENT_SEQUENCE'
  path=R/notice['path'];expected=output/'cusp_requests'/('event%04d.json'%notice['event_index'])
  assert path==expected and path.resolve()==expected and not path.is_symlink(),'NATIVE_EVENT_FILE_ESCAPE'
  assert path.stat().st_size<=4*1024**2 and hashlib.sha256(path.read_bytes()).hexdigest()==notice['file_sha256'],'NATIVE_EVENT_FILE_CHANGED'
  packet=json.loads(path.read_text());request=packet['request'];self.session=sessions.Session(packet,controller_identity_sha256=controller_identity_sha256)
  assert request['run_id']==run_id and request['event_index']==notice['event_index']and request['request_sha256']==notice['request_sha256']
  assert notice['controller_identity_sha256']==self.session.controller_identity_sha256,'CUSP_NOTICE_CONTROLLER_CHANGED'
  stop=stop_evidence(vehicle,request)
  self.current=old.base.base.origin.bind(vehicle,request,mode_memory,packet['causal_snapshot'],gear=gear,now=now)
  self.method=dispatch.choose(request)
  self.current=old.base.finite_input(self.current,self.method,request['event']['geometry'])
  self.current['stop_evidence']=stop;value=dict(self.current);value.pop('input_sha256');self.current['input_sha256']=sessions.event.digest(value)
  self.current=controller.bind_current(self.current,packet['controller_binding'])
  self.current=geometry.bind(self.current,packet['causal_snapshot'])
  self.start_native=vehicle.count;self.start_full_state_sha256=measured_identity(vehicle)
  self.controller_memory=copy.deepcopy(self.current['origin']['controller_memory']);self.mode_history=copy.deepcopy(self.current['mode_history']);self.gear_memory=copy.deepcopy(self.current['gear_memory']);self.committed=False;self.closed=False

 def commit(self,**kwargs):
  identity=controller.verify_current(self.current)
  assert kwargs['generation']['controller_identity_sha256']==kwargs['audit']['controller_identity_sha256']==identity,'MPPI_CERTIFICATE_CONTROLLER_CHANGED'
  ready=super().commit(**kwargs)
  return dict(ready,controller_identity_sha256=identity)

 def reject(self,reason):
  return dict(super().reject(reason),controller_identity_sha256=self.current['controller_identity_sha256'])
