"""Actual isolated NumPy values through the SAME production console serializer; no solve."""
import json,math
import numpy as np
from serialization import dumps
from context import R,C,sha
v=dict(boolean=np.bool_(True),floating=np.float64(.125),integer=np.int64(7),array=np.asarray([[1.,2.],[3.,4.]]))
assert json.loads(dumps(v))==dict(boolean=True,floating=.125,integer=7,array=[[1.,2.],[3.,4.]])
rejected=[]
for name,value in [('nan',np.float64(float('nan'))),('inf',np.asarray([float('inf')])),('unknown',object())]:
 try:dumps(value)
 except (ValueError,TypeError):rejected.append(name)
 else:raise AssertionError('NONFINITE_OR_FOREIGN_NATIVE_JSON_ACCEPTED:'+name)
try:dumps(v,allow_nan=True)
except AssertionError:rejected.append('allow_nan_override')
else:raise AssertionError('ALLOW_NAN_OVERRIDE')
print(dumps(dict(passed=True,real_numpy_types=True,negatives=rejected,new_NLP=0,model_imports=0,physics=0,serializer_sha256=sha(C/'serialization.py'))))
