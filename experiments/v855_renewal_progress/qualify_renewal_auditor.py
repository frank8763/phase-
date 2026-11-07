"""Positive/negative saved-metadata fixture for the actual renewal auditor, no models."""
import copy,gzip,importlib.abc,json,sys
from pathlib import Path
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('NO_MODELS')
sys.meta_path.insert(0,Block())
from common import *
sys.path.insert(0,str(W))
import numpy as np
from renewal_independent import verify
from reference_certificate_audit import independent_values
from self_geometry import containment_margin
p=R/'runs/v851_profile_output_worker/v851_main_slot01/paired';protocol=read(p/'STATIC_PROTOCOL.json');act=read(p/'geometry_memory/ACTUATOR_COMMAND_CONTRACT.json');c=json.load(gzip.open(p/'geometry_memory/progress_certificates/certificate_0304.json.gz','rt'));s=c['one_cycle_continuation'];x={}
for key in ['qpos','qvel','poses','controls']:
    a=np.asarray(s['extra_'+key]);x['extra_'+key]=np.vstack((a,np.repeat(a[-1:,:],120,axis=0))).tolist()
limit=np.asarray(act['limits']);rate=np.asarray(act['rate']);last=np.asarray(c['controls'])[-1];target=np.r_[np.asarray(c['target'])[:2],0.,0.]if 'reference_following'not in c else np.r_[np.asarray(c['reference_following']['targets'])[-1,:2],0.,0.];commands=[]
for _ in range(0,128,8):
    last=np.clip(np.clip(target,limit[:,0],limit[:,1]),last-rate,last+rate);commands.extend([last.copy()for _ in range(8)])
x['extra_controls']=np.asarray(commands).tolist()
a=np.asarray(s['extra_self_bounds']);x['extra_self_bounds']=np.vstack((a,np.repeat(a[-1:,:],120,axis=0))).tolist();values=independent_values(np.vstack((c['prefix_poses'],c['poses'],x['extra_poses'])),c['forecast_state'],protocol);x.update(total_native_ticks=456,minimum_clearance_m=float(values.min()),minimum_self_margin_m=float(containment_margin(np.asarray(x['extra_self_bounds']),np.asarray(protocol['footprint_bounds'])).min()),terminal_speed_m_s=float(np.linalg.norm(np.asarray(x['extra_qvel'])[-1,:2])),absolute_end_time=c['created_time']+4.56,no_future_observations_assumed=True,required=True);c['renewal_reserve']=x
proof=verify(c,protocol,act);negative=[]
for key in ['pose','control','time','successor_speed']:
    bad=copy.deepcopy(c)
    if key=='pose':bad['renewal_reserve']['extra_poses'][-1][0]+=.1
    if key=='control':bad['renewal_reserve']['extra_controls'][-1][2]+=.1
    if key=='time':bad['renewal_reserve']['absolute_end_time']+=.01
    if key=='successor_speed':bad['one_cycle_continuation']['terminal_speed_m_s']=.1
    try:verify(bad,protocol,act)
    except AssertionError:negative.append(key)
    else:raise AssertionError('NEGATIVE_ACCEPTED_'+key)
result=dict(passed=True,proof=proof,negative_rejected=negative,fixture='Synthetic metadata continuation of saved304 settled pose; no new physical prediction or dynamics qualification claimed',models=0,integrations=0);dump(ROOT/'RENEWAL_AUDITOR_QUALIFICATION.json',result);print(json.dumps(result))
