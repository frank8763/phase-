"""Normalize representation, never state values or original1e-8 gate."""
import numpy as np

def compare(packet,expected,initial):
 a=np.asarray(initial(packet)['state'],dtype=float)
 b=np.asarray(initial(expected)['state'],dtype=float)
 assert a.shape==b.shape==(8,)and np.isfinite(a).all()and np.isfinite(b).all(),'INVALID_STATE_SHAPE_OR_NONFINITE'
 ca=np.asarray(packet['controller_memory']['last_ctrl'],dtype=float)
 cb=np.asarray(expected['controller_memory']['last_ctrl'],dtype=float)
 assert ca.shape==cb.shape==(4,)and np.isfinite(ca).all()and np.isfinite(cb).all(),'INVALID_CONTROLLER_STATE'
 ia=float(packet['controller_memory']['integral'])
 ib=float(expected['controller_memory']['integral'])
 assert np.isfinite(ia)and np.isfinite(ib),'NONFINITE_INTEGRAL'
 state=float(abs(a-b).max());control=float(abs(ca-cb).max());integral=abs(ia-ib)
 assert max(state,control,integral)<=1e-8,'SAVED_ENTRY_CHANGED'
 return {'passed':True,'maximum_state_error':state,'maximum_controller_error':control,'integral_error':integral,'same_original_tolerance':1e-8,'no_state_or_memory_mutation':True}
