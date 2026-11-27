"""Original runtime ndarray scalar JSON seam, zero scipy/model imports."""
import json,sys
from pathlib import Path
import numpy as np
from common import C,S,put
value=dict(a=np.bool_(True),b=np.float64(.1),c=np.int64(2),nested=[np.bool_(False),np.array([1.,2.])])
try:json.dumps(value,allow_nan=False)
except TypeError:pass
else:raise AssertionError('OLD_NUMPY_SERIALIZATION_BUG_NOT_REPRODUCED')
path=S/'software/SCALAR_WRITER.json';put(path,value);assert json.loads(path.read_text())==dict(a=True,b=.1,c=2,nested=[False,[1.,2.]])
try:put(S/'software/INVALID_NAN.json',dict(x=np.float64('nan')))
except ValueError:pass
else:raise AssertionError('NAN_ACCEPTED')
print(json.dumps(dict(passed=True,old_error_reproduced=True,actual_production_put_tested=True,NaN_refused=True,models=0,solvers=0,only_representational_conversion=True)))
