"""Extend exact measured owner binding with the qualified finite method input."""
import copy
import importlib.util
from pathlib import Path
import sys

R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1404_route_bridge_session'))
import session
assert Path(session.__file__).resolve()==R/'experiments/v1404_route_bridge_session/session.py'
spec=importlib.util.spec_from_file_location('v1411_original_current_owner',R/'experiments/v1404_route_bridge_session/native_request.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)


def finite_input(current,method,geometry):
    value=copy.deepcopy(current);previous=value.pop('input_sha256')
    assert session.digest(value)==previous,'BASE_CURRENT_INPUT_CHANGED'
    assert 'method_spec'not in value and 'event_geometry'not in value
    value.update(base_input_sha256=previous,method_spec=copy.deepcopy(method),event_geometry=copy.deepcopy(geometry))
    value['input_sha256']=session.digest(value)
    return value


class OwnerRequest(base.OwnerRequest):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.current=finite_input(self.current,self.method,self.session.packet['request']['event']['geometry'])

    def commit(self,**kwargs):
        assert kwargs['audit']['input_sha256']==kwargs['generation']['input_sha256']==self.current['input_sha256'],'INDEPENDENT_AUDIT_WRONG_METHOD_INPUT'
        assert kwargs['audit']['qualified_method']==self.method['method'],'INDEPENDENT_AUDIT_WRONG_METHOD'
        return super().commit(**kwargs)
