"""Independent saved native trace/contact diagnosis; zero simulator imports or steps."""
import ast,gzip,hashlib,json,math,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v856_nav2_foundation';OUT=ROOT/'closed_analysis';OUT.mkdir(exist_ok=True);P=ROOT/'entry01/vehicle_qualification01'
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=np.load(P/'NATIVE_TRACE.npz');commands=np.asarray(json.loads((P/'BODY_COMMANDS.json').read_text()));contacts=json.load(gzip.open(P/'CONTACTS.json.gz','rt'));setup=json.loads((P/'SETUP.json').read_text());result=json.loads((P/'RESULT.json').read_text());xml=ET.parse(P/'paired/assets/isolated_indoor.xml').getroot();declarations=[]
def geoms(body):
    for g in body.findall('geom'):declarations.append(dict(geom_id=len(declarations),body_name=body.get('name','world'),geom=g.attrib))
    for b in body.findall('body'):geoms(b)
geoms(xml.find('worldbody'));qpos=a['qpos'];qvel=a['qvel'];ctrl=a['ctrl'];n=len(qpos);assert n==1100 and len(contacts)==1101 and np.max(abs(a['time']-np.arange(1,n+1)*.01))<1e-10
# Generalized-velocity indexing independently derived from declared body/joint order.
vel_index={};off=0
for b in xml.find('worldbody').iter('body'):
    for joint in list(b):
        if joint.tag=='freejoint':vel_index[joint.get('name')]=list(range(off,off+6));off+=6
        elif joint.tag=='joint':vel_index[joint.get('name')]=[off];off+=1
assert off==qvel.shape[1]
yaw=np.arctan2(2*(qpos[:,3]*qpos[:,6]+qpos[:,4]*qpos[:,5]),1-2*(qpos[:,5]**2+qpos[:,6]**2));body=qvel[:,0]*np.cos(yaw)+qvel[:,1]*np.sin(yaw)
window=slice(250,390);vmean=float(body[window].mean());assert abs(vmean-result['steady_forward_m_s'])<1e-12
nativecontacts=contacts[1:];counts=Counter(row[2]for tick in nativecontacts for row in tick);self_ticks=sum(any(row[2]=='robot_self_contact'for row in tick)for tick in nativecontacts);pairs={}
for tick in nativecontacts:
 for g1,g2,kind,dist in tick:
  if kind!='robot_self_contact':continue
  key=f'{min(g1,g2)}:{max(g1,g2)}';p=pairs.setdefault(key,dict(geom_ids=[min(g1,g2),max(g1,g2)],declarations=[declarations[min(g1,g2)],declarations[max(g1,g2)]],records=0,minimum_distance_m=1e9,maximum_penetration_m=0));p['records']+=1;p['minimum_distance_m']=min(p['minimum_distance_m'],dist);p['maximum_penetration_m']=max(p['maximum_penetration_m'],-dist)
front=[vel_index[k][0]for k in ['left_front_wheel_joint','right_front_wheel_joint']];rear=[vel_index[k][0]for k in ['left_rear_wheel_joint','right_rear_wheel_joint']];target=ctrl[window][:,setup['actuator_ids'][2:]];actual=qvel[window][:,rear]
checks=dict(native_trace_coverage=n==result['actual_native'],exact_times=True,full_actual_replay_record_passed=json.loads((P/'REPLAY.json').read_text())['passed'],same_qualification_metric=abs(vmean-result['steady_forward_m_s'])<1e-12,front_chassis_pairs_present=all(k in pairs for k in ['23:25','23:27']),obstacle_unknown_contact_absent=not any(counts[k]for k in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']))
diagnosis=dict(scope='SAVED_NATIVE_ZERO_MODEL_DIAGNOSIS',new_model_initializations=0,new_integrations=0,actual_native=n,replay_native=result['replay_native'],steady_interval_native_ticks=[251,390],commanded_forward_m_s=.2,actual_mean_forward_m_s=vmean,mean_body_tracking_error_m_s=.2-vmean,actual_to_command_ratio=vmean/.2,mean_rear_target_rad_s=target.mean(0).tolist(),mean_rear_actual_rad_s=actual.mean(0).tolist(),mean_front_actual_rad_s=qvel[window][:,front].mean(0).tolist(),robot_self_contact_ticks=self_ticks,robot_self_contact_pairs=list(pairs.values()),all_contact_type_counts=dict(counts),checks=checks,independent_audit_passed=all(checks.values()),confirmed='Native body speed failed the preregistered gate; front wheel/chassis penetrating contacts are present.',inference='Interpenetrating wheel/chassis collision geometry is a plausible source of drag and steering disturbance. Its causal share and sufficiency have not been measured by an ablation. Raising PI gains alone is not yet justified.',old_rpccr_failures_reclassified=False,model_xml_is_construction_record='Legacy initialization also mutates compiled parameters; the saved MJB remains the actual model of record. XML joint/actuator limits are not substituted for actual SETUP limits.',inputs={str(p.relative_to(R)):sha(p)for p in [P/'NATIVE_TRACE.npz',P/'BODY_COMMANDS.json',P/'CONTACTS.json.gz',P/'SETUP.json',P/'REPLAY.json',P/'RESULT.json',P/'paired/assets/isolated_indoor.xml']})
dump(OUT/'DIAGNOSIS.json',diagnosis)
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
fig,axs=plt.subplots(3,1,figsize=(9,8),sharex=True,constrained_layout=True);t=a['time'];axs[0].step(t,commands[:,1],where='post',label='Requested body speed');axs[0].plot(t,body,label='Native body speed');axs[0].set_ylabel('Speed (m/s)');axs[0].legend();axs[0].grid(alpha=.2)
axs[1].plot(t,ctrl[:,setup['actuator_ids'][2:]].mean(1),label='Rear wheel target');axs[1].plot(t,qvel[:,rear].mean(1),label='Rear wheel actual');axs[1].plot(t,qvel[:,front].mean(1),label='Front wheel actual');axs[1].set_ylabel('Wheel speed (rad/s)');axs[1].legend();axs[1].grid(alpha=.2)
penetration=np.asarray([max([-row[3]for row in tick if row[2]=='robot_self_contact']+[0.])for tick in nativecontacts]);axs[2].plot(t,penetration*1000,label='Wheel/chassis self penetration');axs[2].set_ylabel('Penetration (mm)');axs[2].set_xlabel('Native simulation time (s), wall-paced at 100 Hz');axs[2].legend();axs[2].grid(alpha=.2);fig.suptitle('V856 native actuator qualification: under-speed and internal contacts')
fig.savefig(OUT/'VEHICLE_RESPONSE.png',dpi=160);fig.savefig(OUT/'VEHICLE_RESPONSE.pdf');plt.close(fig)
print(json.dumps(dict(checks=checks,steady_forward=vmean,self_contact_ticks=self_ticks,pairs=list(pairs)),indent=2))
