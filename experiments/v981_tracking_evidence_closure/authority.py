"""This repair has source-only authority; reject every physical entry."""

def authorized(*args, **kwargs):
    raise PermissionError('V981_SOURCE_ONLY_NO_MODEL_AUTHORITY')

ready_for_navigation = authorized
