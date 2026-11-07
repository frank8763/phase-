"""Exact public and every-native-state comparison, no model or integration."""
import gzip,json
from itertools import zip_longest
import numpy as np
from common import W,read,repeat_check
import sys
sys.path.insert(0,str(W));from contact_fingerprint import compare_contacts
def compare(base,pair):
 out=repeat_check(base,pair,read(base/'geometry_memory/result.json'),read(pair/'geometry_memory/result.json'),compare_contacts)
 errors={k:0. for k in ['qpos_full','qvel_full','actual_ctrl','mocap_pos']};count=0;equal_length=True
 with gzip.open(base/'geometry_memory/dynamic_native.jsonl.gz','rt')as a,gzip.open(pair/'geometry_memory/dynamic_native.jsonl.gz','rt')as b:
  for x,y in zip_longest(a,b):
   if x is None or y is None:equal_length=False;break
   x,y=json.loads(x),json.loads(y);count+=1
   for key in errors:errors[key]=max(errors[key],float(np.max(abs(np.asarray(x[key])-np.asarray(y[key])))))
 out['full_native_errors']=errors;out['compared_native_steps']=count;out['checks']['every_native_state_ctrl_mocap']=equal_length and count==read(base/'geometry_memory/result.json')['physics_steps']and all(v<=1e-8 for v in errors.values());out['passed']=all(out['checks'].values());out['new_integrations']=0
 return out
