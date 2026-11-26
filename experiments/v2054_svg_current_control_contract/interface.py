from pathlib import Path
import hashlib,importlib.util,json,math
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
WIRE=R/'experiments/v1938_current_causal_solver_wire/wire.py';FRONT=R/'experiments/v2036_svg_causal_route_frontend/frontend.py';BRIDGE=R/'experiments/v1665_svg_phase_vehicle_contract/bridge.py'
class CurrentControl:
 def __init__(self,source,*,run_id):
  for p in [WIRE,FRONT,BRIDGE]:assert source[str(p.relative_to(R))]==sha(p),'SVG_BRIDGE_SOURCE_CHANGED'
  self.source=source;self.run_id=run_id;self.wire=load('pinned_shared_current_wire',WIRE).CurrentWire(source,run_id=run_id,method='SVG-MPPI');self.front=load('pinned_current_causal_svg_map',FRONT);self.bridge=load('pinned_measured_svg_actuator_state',BRIDGE);self.pending=None;self.closed=False;self.poisoned=False;self.sequence=0
 def frame(self,np,receipt,*,goal_xy,rear_path,gear):
  assert not self.closed and not self.poisoned and self.pending is None,'SVG_CLOSED_POISONED_OR_INFLIGHT';self.poisoned=True
  assert type(gear)is int and gear==1,'SVG_AUTHOR_FORWARD_REFERENCE_ONLY_REVERSE_UNQUALIFIED'
  request=self.wire.request(receipt,goal_xy=goal_xy,public_route=[p[:2]for p in rear_path]);p=receipt['packet'];origin=self.bridge.decode(p,expected_native=request['native_tick'],expected_sim_time=request['sim_time'],expected_packet_sha256=receipt['packet_sha256']);maps=self.front.build(np,request,rear_path,public_sha256=self.source[str(self.front.PUBLIC.relative_to(R))]);self.pending=dict(origin=origin,request=request,maps_sha256=digest(maps));self.poisoned=False
  return dict(request=request,author_state=origin['author_state'],maps=maps,source_receipt_sha256=receipt['packet_sha256'],maps_sha256=self.pending['maps_sha256'],physical_authority=False)
 def proposal(self,raw,*,now):
  assert not self.closed and not self.poisoned and self.pending is not None,'SVG_REPLY_WITHOUT_ORIGIN';self.poisoned=True
  assert set(raw)=={'run_id','origin_native_tick','input_sha256','map_sha256','steering','collision_rate'},'SVG_REPLY_UNDECLARED_FIELDS';origin=self.pending['origin'];request=self.pending['request'];assert raw['run_id']==self.run_id and raw['origin_native_tick']==origin['origin_native']and raw['input_sha256']==digest(request)and raw['map_sha256']==self.pending['maps_sha256'],'SVG_FOREIGN_REPLY_ORIGIN'
  assert len(raw['steering'])==14 and all(type(x)in[int,float]and math.isfinite(x)and abs(x)<=.45 for x in raw['steering']),'SVG_RAW_AUTHOR_OUTPUT_DOMAIN';rate=raw['collision_rate'];assert type(rate)in[int,float]and math.isfinite(rate)and 0<=rate<=1,'SVG_RAW_COLLISION_RATE_DOMAIN'
  candidate=self.bridge.request(raw['steering'][0],longitudinal_speed=.08,declared_gear=1,origin=origin,expected_origin_sha256=origin['origin_packet_sha256']);v,w,_=candidate['body_request'];reply=dict(schema='PHASE_CURRENT_SOLVER_REPLY_V1',run_id=self.run_id,method='SVG-MPPI',origin_native_tick=origin['origin_native'],input_sha256=digest(request),sequence=self.sequence,issued_at=now,v=v,w=w);checked=self.wire.reply(reply,now=now);self.sequence+=1;self.pending=None;self.poisoned=False
  return dict(body_request=checked['request'],raw_first_author_steering=raw['steering'][0],full_author_steering=raw['steering'],author_collision_rate=rate,physical_authority=False,actual_execution_permitted=False,original5native_plus2200_fullstate_response_required=True,independent_actual_capture_replay_audit_required=True,source_origin=checked['origin'])
 def close(self):self.closed=True;self.wire.close()
