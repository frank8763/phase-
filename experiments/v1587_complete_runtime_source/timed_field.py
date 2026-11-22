"""Original V1414 geometry, current clock, prepared cache before fresh wire."""
import copy
import hashlib
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
SOURCE='experiments/v1414_current_timed_geometry/geometry.py'


class PreparedField:
    def __init__(self,*,known,snapshot,origin_native,origin_sim_time,maximum_native,guard):
        guard.check();guard.require_timed_geometry_preparation()
        path=R/SOURCE;assert hashlib.sha256(path.read_bytes()).hexdigest()==guard.source[SOURCE]
        s=importlib.util.spec_from_file_location('v1587_original_current_timed_field',path)
        module=importlib.util.module_from_spec(s);s.loader.exec_module(module)
        self.geometry=module.Geometry(copy.deepcopy(known),copy.deepcopy(snapshot),
            origin_native=origin_native,origin_sim_time=origin_sim_time)
        assert type(maximum_native)is int and 2200<=maximum_native<=10400
        self.origin=origin_native;self.end=origin_native+maximum_native
        for tick in range(origin_native,self.end+1,10):
            guard.check();self.geometry.polygon(tick)
        self.geometry.polygon(self.end)
        self.cells=frozenset(self.geometry.cache)
        path=Path(__file__).with_name('gates.py')
        assert hashlib.sha256(path.read_bytes()).hexdigest()==guard.source[str(path.relative_to(R))]
        s=importlib.util.spec_from_file_location('v1587_prepared_array_gates',path)
        checks=importlib.util.module_from_spec(s);s.loader.exec_module(checks)
        self.original_gate_module=checks.original(guard)

    def check_range(self,first,count):
        assert type(first)is int and type(count)is int and count>=1
        assert self.origin<=first and first+count-1<=self.end
        lo=self.geometry.cell(first);hi=self.geometry.cell(first+count-1)
        assert all(index in self.cells for index in range(lo,hi+1)),'UNPREPARED_CURRENT_TIME_CELL'
        assert frozenset(self.geometry.cache)==self.cells,'FROZEN_TIME_FIELD_CACHE_CHANGED'

    def tube(self,states,tick):
        self.check_range(tick,len(states));answer=self.geometry.tube(states,tick)
        assert frozenset(self.geometry.cache)==self.cells
        return answer

    def actual(self,body,tick):
        self.check_range(tick,1);answer=self.geometry.actual(body,tick)
        assert frozenset(self.geometry.cache)==self.cells
        return answer
