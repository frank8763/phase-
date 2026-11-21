"""One immutable causal geometry contract selected by the public finite method."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1397_event_handoff_integration'))
from causal_bridge_field import all_future


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


method=exact('v1415_original_public_method',Path(__file__).with_name('method.py'))
Timed=exact('v1415_qualified_current_timed_geometry',R/'experiments/v1414_current_timed_geometry/geometry.py').Geometry
Periodic=exact('v1415_original_full_period_geometry',R/'experiments/v1396_rpp_rpc_retirement/geometry_contract.py').Geometry
KINDS={'ENGINEERING_COHERENT_MPPI_CURRENT_RESPONSE':'FULL_PERIOD_DISK',
       'ORIGINAL_TWO_ARC_CAPTURE_THEN_ENGINEERING_COHERENT_MPPI':'FULL_PERIOD_DISK',
       'ORIGINAL_BOUNDED_STEERING_THEN_GEAR_RELEASE_TIMED_REVERSE':'ORIGINAL_CAUSAL_TIME_POLYGONS'}


def bind(current,snapshot):
    value=copy.deepcopy(current);previous=value.pop('input_sha256');assert digest(value)==previous,'CURRENT_METHOD_INPUT_CHANGED'
    assert value['causal_snapshot_sha256']==digest(snapshot),'CURRENT_SNAPSHOT_SHA_CHANGED'
    spec=method.expected_spec(current)
    assert 'geometry_kind'not in value and 'causal_snapshot'not in value
    value.update(method_input_sha256=previous,causal_snapshot=copy.deepcopy(snapshot),geometry_kind=KINDS[spec['method']])
    value['input_sha256']=digest(value)
    return value


class GeometryBinding:
    def __init__(self,current,setup):
        value=copy.deepcopy(current);identity=value.pop('input_sha256');assert digest(value)==identity
        self.current=copy.deepcopy(current);self.input_sha256=identity
        snapshot=current['causal_snapshot'];assert digest(snapshot)==current['causal_snapshot_sha256']
        spec=method.expected_spec(current);self.geometry_kind=KINDS[spec['method']]
        assert current['geometry_kind']==self.geometry_kind,'METHOD_CAUSAL_GEOMETRY_CHANGED'
        origin=current['origin'];self.origin_native=origin['native_tick'];self.origin_sim_time=origin['sim_time']
        forecast=all_future(snapshot,current_native=self.origin_native,current_sim_time=self.origin_sim_time)
        assert forecast['periodic_source_tick']==current['bridge_forecast']['periodic_source_tick']
        for key in ['center','radius_m']:
            assert forecast[key]==current['bridge_forecast'][key],'FULL_PERIOD_ENCLOSURE_NOT_FROM_BOUND_COEFFICIENTS'
        if self.geometry_kind=='ORIGINAL_CAUSAL_TIME_POLYGONS':
            self.geometry=Timed(setup['known'],snapshot,origin_native=self.origin_native,origin_sim_time=self.origin_sim_time)
        else:self.geometry=Periodic(setup['known'],[*forecast['center'],forecast['radius_m']])

    def tube(self,states,native_tick):
        assert type(native_tick)is int and native_tick>=self.origin_native,'GEOMETRY_BEFORE_BOUND_CURRENT_ORIGIN'
        if self.geometry_kind=='ORIGINAL_CAUSAL_TIME_POLYGONS':return self.geometry.tube(states,native_tick)
        return self.geometry.tube(states)

    def actual(self,body,native_tick):
        assert type(native_tick)is int and native_tick>=self.origin_native
        return self.geometry.actual(body,native_tick)
