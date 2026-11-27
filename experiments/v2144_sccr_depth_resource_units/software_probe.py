"""Exercise new production extractor and packet validation without real renderer."""
import json,copy,os
import numpy as np
from context import C,load,digest,sha
depth=load('SCCR_actual_extractor_software',C/'depth.py')
raw=np.arange(4096,dtype=np.float32).reshape(64,64)%37/8
features=depth.saved_features(np,raw);assert np.array_equal(features,depth.independent(np,raw))and len(features)==24
p=dict(schema='ACTUAL_SHARED_DEPTH24_V1',native=0,sim_time=0.,own_body=[-4.,-2.,0.,0.,0.],depth24=features.tolist(),actual_render_available=True,producer_sha256=sha(C/'depth.py'),physical_authority=False);p['packet_sha256']=digest(p)
delivered=[depth.validate_packet(p,0,sha(C/'depth.py'))for _ in depth.METHODS];assert all(x==features.tolist()for x in delivered)
rejected=[]
for name,change,k in [('missing_actual_render',dict(actual_render_available=False),0),('missing_dimension',dict(depth24=p['depth24'][:-1]),0),('truth_field',dict(actor_xy=[0.,0.]),0),('stale_tick',{},5)]:
 bad=dict(p,**change);bad['packet_sha256']=digest({k:v for k,v in bad.items()if k!='packet_sha256'})
 try:depth.validate_packet(bad,k,sha(C/'depth.py'))
 except(AssertionError,KeyError,ValueError):rejected.append(name)
 else:raise AssertionError('SCCR_DEPTH_NEGATIVE_ACCEPTED:'+name)
try:depth.Sampler(None,np,None,None,{},None)
except AssertionError:rejected.append('unadmitted_renderer_before_mujoco_import')
else:raise AssertionError('UNADMITTED_RENDERER_ACCEPTED')
assert 'mujoco'not in __import__('sys').modules
print(json.dumps(dict(passed=True,production_extractor_and_packet_seam=True,all_ten_consumers=10,exact_patch_reference_error=float(abs(features-depth.independent(np,raw)).max()),negative_cases=rejected,models=0,actual_renderers=0,actual_renders=0,policy_calls=0,optimizer_queries=0,physics=0)))
