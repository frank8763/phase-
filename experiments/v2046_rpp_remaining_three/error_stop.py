"""Tag exact original error-stop BEFORE its first callback."""
from context import SOURCE,R,load
_original=load('v1806_exact_original_error_tail',R/'experiments/v1691_dwa_receding_navigation/error_stop.py')
_shared=load('v1806_shared_closure_phase',R/'experiments/v1694_shared_observation_closure/contract.py')
def complete(vehicle,progress):return _shared.complete_closure(vehicle,progress,_original.complete)
