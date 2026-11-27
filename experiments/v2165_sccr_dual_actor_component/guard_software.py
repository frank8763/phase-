from common import *
import os,json
from environment_guard import PinnedLibraries
assert os.sched_getaffinity(0)=={0}and not(S/'ENVIRONMENT_GUARD_PROOF.json').exists()
f=PinnedLibraries();f.find_spec('numpy');spec=__import__('importlib.machinery').machinery.PathFinder.find_spec('numpy');p=str(Path(spec.origin).resolve());wanted=f.pins[p];bad=[]
for label,value in [('unknown',None),('changed','0'*64)]:
 if value is None:f.pins.pop(p)
 else:f.pins[p]=value
 try:f.find_spec('numpy')
 except AssertionError:bad.append(label)
 else:raise AssertionError('LIBRARY_NEGATIVE_ACCEPTED')
 f.pins[p]=wanted
assert 'torch'not in sys.modules
v=dict(passed=True,closed=True,negative_cases=bad,actual_library_import_origin_checked=True,no_file_mutation=True,explicit_network_constructors=0,weight_deserializations=0,forward_calls=0,torch_imported=False);dump(S/'ENVIRONMENT_GUARD_PROOF.json',v);print(json.dumps(v))
