"""Explicit canonical execution module; avoid legacy generic module-name collision."""
from afternoon_tools import R,load
m=load('afternoon_original_component_execution',R/'experiments/v1114_coupled_steering_mode/execution.py')
applied_step=m.applied_step
complete_stop_source=m.complete_stop_source
execute_complete_stop=m.execute_complete_stop
