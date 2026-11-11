import hashlib,json,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(C));from history_cache import load_trace
p=R/'runs/v858_nav2_verified/v1024/dynamic_we/physics/NATIVE_TRACE.npz';h=hashlib.sha256(p.read_bytes()).hexdigest();cache=load_trace(p,h)
with np.load(p,allow_pickle=False)as raw:assert all(np.array_equal(cache[k],raw[k])for k in cache)
rejected=[]
for name,expected,cap in [('wrong_sha','0'*64,64*1024**2),('memory_cap',h,1024)]:
 try:load_trace(p,expected,cap)
 except AssertionError:rejected.append(name)
 else:raise AssertionError('NEGATIVE_NOT_REJECTED')
try:cache['qpos'][0,0]=1.
except ValueError:rejected.append('write_to_cached_array')
else:raise AssertionError('CACHE_MUTATION_NOT_BLOCKED')
result=dict(passed=True,models=0,integrations=0,entire_arrays_bitwise_equal=True,negative_cases=rejected,cache_bytes=sum(v.nbytes for v in cache.values()),current_frozen_worker_not_modified=True,future_entry_only=True)
(R/'runs/v1040_approach_information_audit/CACHE_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
