"""Explicit event-aware session, same complete-certificate transition rules."""
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=exact('v1422_original_session',R/'experiments/v1404_route_bridge_session/session.py')
event=exact('v1422_declared_ordered_event',C/'event_contract.py')

def prepare_request(envelope,segment,geometry,tracker,*,run_id,event_index,brake_start,now,event_kind='CUSP_NEXT_SEGMENT_CHECK',plan_index=None,ordered_segments=None,completed_bridge_events=0):
 if event_kind=='CUSP_NEXT_SEGMENT_CHECK':return old.prepare_request(envelope,segment,geometry,tracker,run_id=run_id,event_index=event_index,brake_start=brake_start,now=now)
 assert event_kind=='ORDERED_ROUTE_FIRST_SEGMENT_CHECK'
 snapshot=tracker.snapshot();forecast=old.all_future(snapshot,current_native=envelope['wire']['native_tick'],current_sim_time=envelope['wire']['sim_time'])
 request=event.ordered_request(envelope,segment,geometry,forecast,run_id=run_id,event_index=event_index,brake_start=brake_start,now=now,plan_index=plan_index,ordered_segments=ordered_segments,completed_bridge_events=completed_bridge_events)
 return dict(kind='BRIDGE_CERTIFICATE_REQUEST',request=request,causal_snapshot=snapshot,coefficient_snapshot_sha256=event.digest(snapshot),physical_admission=False)

class Session(old.Session):
 def __init__(self,packet):
  event.validate_request(packet['request']);super().__init__(packet)
