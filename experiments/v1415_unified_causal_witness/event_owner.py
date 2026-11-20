"""Full coefficient snapshot and geometry kind are part of the immutable input."""
import importlib.util
from pathlib import Path

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


base=exact('v1415_original_current_method_owner',R/'experiments/v1411_native_guarded_execution/event_owner.py')
geometry=exact('v1415_complete_geometry_input',C/'geometry_binding.py')


class OwnerRequest(base.OwnerRequest):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.current=geometry.bind(self.current,self.session.packet['causal_snapshot'])

    def commit(self,**kwargs):
        assert kwargs['generation']['geometry_kind']==kwargs['audit']['geometry_kind']==self.current['geometry_kind'],'AUDIT_GEOMETRY_KIND_CHANGED'
        assert kwargs['generation']['causal_snapshot_sha256']==kwargs['audit']['causal_snapshot_sha256']==self.current['causal_snapshot_sha256']
        return super().commit(**kwargs)
