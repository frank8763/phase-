"""Extend the already-bound owner input with its one fixed finite method."""
import copy
import importlib.util
from pathlib import Path
import sys

R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1404_route_bridge_session'))
spec=importlib.util.spec_from_file_location('phase_v1406_owner_current_request',R/'experiments/v1404_route_bridge_session/native_request.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)


class OwnerRequest(base.OwnerRequest):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        value=copy.deepcopy(self.current);previous=value.pop('input_sha256')
        value.update(base_input_sha256=previous,method_spec=copy.deepcopy(self.method),event_geometry=copy.deepcopy(self.session.packet['request']['event']['geometry']))
        value['input_sha256']=base.digest(value);self.current=value
