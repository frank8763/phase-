from pathlib import Path
import os,json,copy,hashlib
import numpy as np
from assemble import *
S=R/'runs/v2155_sccr_full_observation_assembly';assert os.sched_getaffinity(0)=={0}and not(S/'RESULT.json').exists();cases=[]
for i in range(40):
 p=dict(native=i*5,sim_time=i*.05,body=[-4.+i*.01,-2.,i*.01,0.,0.],goal_xy=[4.,-2.],path_world=[[-4.,-2.],[-3.,-2.],[4.,-2.]],wp_index=1,previous_body_command=[.08,.001],core_lidar36_raw_m=np.linspace(.2,5.,36).tolist(),rendered_depth24=np.linspace(.01,.9,24).tolist(),phase6_lidar32=np.linspace(.03,.8,32).tolist(),phase7_depth15=np.linspace(.04,.7,15).tolist(),phase17_lidar32=np.linspace(.05,.6,32).tolist(),phase17_depth15=np.linspace(.06,.5,15).tolist(),producer_proof=dict(explicit_synthetic_fixture=True,actual_fresh_sensor=False))
 obs,z=build(np,p,lambda x:np.array([.2,-.1],np.float32),developer_fixture=True)
 assert np.array_equal(obs[42:66],np.asarray(p['rendered_depth24'],np.float32))and np.array_equal(obs[66:98],np.asarray(p['phase6_lidar32'],np.float32))and np.array_equal(obs[107:122],np.asarray(p['phase7_depth15'],np.float32))and np.array_equal(obs[127:129],np.array([.2,-.1],np.float32))and np.array_equal(obs[129:161],np.asarray(p['phase17_lidar32'],np.float32))and np.array_equal(obs[166:181],np.asarray(p['phase17_depth15'],np.float32))
 cases.append(dict(native=p['native'],observation_sha256=hashlib.sha256(obs.tobytes()).hexdigest()))
negative=[]
def reject(name,q,fixture=True):
 try:build(np,q,lambda _:np.zeros(2,np.float32),developer_fixture=fixture)
 except(AssertionError,ValueError,KeyError):negative.append(name)
 else:raise AssertionError('SCCR_ASSEMBLY_NEGATIVE_ACCEPTED:'+name)
q=copy.deepcopy(p);q.pop('phase7_depth15');reject('missing_separate_depth_block',q)
q=copy.deepcopy(p);q['actor_phase']=1.;reject('private_truth_field',q)
q=copy.deepcopy(p);q['phase6_lidar32'][0]=float('nan');reject('nonfinite_sensor',q)
q=copy.deepcopy(p);q['sim_time']+=.01;reject('future_sensor_clock',q)
q=copy.deepcopy(p);q['phase17_depth15']=[1.]*14;reject('dimension_padding_not_allowed',q)
reject('unqualified_actual_producer',p,False)
files={str(x.relative_to(R)):sha(x)for x in [BASE,DEPTH,PHASE6,PHASE7,RESIDUAL,PHASE17,SENSOR6,SENSOR14,SUMMARY7,Path(__file__),Path(__file__).with_name('assemble.py')]}
v=dict(passed=True,closed=True,synthetic_packet_cases=40,negative_cases=negative,model_initializations=0,policy_deserializations=0,policy_inferences=0,renderer_constructors=0,actual_sensor_acquisitions=0,physics=0,replay=0,formal_tasks=0,original_assembly_AST_only=True,complete_186_builder_software_prepared=True,actual_full186_or_full_SCCR_not_qualified=True,Phase21_risk_fusion_pending=True,source_SHA256=files,cases=cases)
raw=json.dumps(v,indent=2).encode()+b'\n';assert len(raw)<256*1024;(S/'RESULT.json').write_bytes(raw);print(json.dumps({k:v for k,v in v.items()if k not in ['source_SHA256','cases']}))
