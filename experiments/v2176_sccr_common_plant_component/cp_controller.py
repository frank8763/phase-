"""Pinned prospective controller-only/shared-route adapter, no native environment."""
from context import load,R
_impl=load('SCCR_CP_persistent_source_adapter',R/'experiments/v2175_sccr_persistent_controller/controller.py')
Controller=_impl.Controller
IDENTITY=_impl.IDENTITY
