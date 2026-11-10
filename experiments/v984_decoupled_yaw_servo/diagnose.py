"""Observed V982 actuator/body residuals; no plant identification or model calls."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from control_fixture import R

S=R/'runs/v983_saved_transient_diagnosis';O=R/'runs/v984_decoupled_yaw_servo'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    receipt=json.loads((S/'REMOTE_RESTORE_RECEIPT.json').read_text())
    for row in receipt['files']:assert sha(R/row['path'])==row['sha256'],row['path']
    xml=R/'runtime/mk-mini/training/assets/mkmini_real/mkmini_mobile_manipulator_indoor_v1.xml'
    root=ET.parse(xml).getroot();joint={};nq=nv=0
    for node in root.find('worldbody').iter():
        if node.tag not in {'joint','freejoint'}:continue
        kind='free'if node.tag=='freejoint'else node.get('type','hinge')
        joint[node.get('name')]=dict(id=len(joint),qpos=nq,qvel=nv)
        a,b={'free':(7,6),'ball':(4,3),'hinge':(1,1),'slide':(1,1)}[kind];nq+=a;nv+=b
    contract=json.loads((S/'physics/MODEL_BUILD_CONTRACT.json').read_text())
    drivers=contract['interface']['drivers']
    for d in drivers:
        n=root.find('actuator').find("*[@name='%s']"%d['name'])
        assert joint[n.get('joint')]['id']==d['new_joint_id'][0]
    left=joint['left_rear_wheel_joint']['qvel'];right=joint['right_rear_wheel_joint']['qvel']
    with np.load(S/'physics/NATIVE_TRACE.npz')as z:q=z['qpos'];v=z['qvel'];ctrl=z['ctrl']
    assert q.shape[1]==nq and v.shape[1]==nv
    cmd=np.asarray(json.loads((S/'physics/BODY_COMMANDS.json').read_text()),float)
    yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
    vx=v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw);vy=-v[:,0]*np.sin(yaw)+v[:,1]*np.cos(yaw);w=v[:,5]
    # Fixed active interval ending at the originally recorded fault, no fitting.
    fault=json.loads((S/'ONLINE_TRACKING_FAULT.json').read_text())['packet']['native_tick']
    sl=slice(6119,fault);rms=lambda x:float(np.sqrt(np.mean(x[sl]**2)))
    steering=q[:,[joint['left_front_steer_joint']['qpos'],joint['right_front_steer_joint']['qpos']]]
    ks=[]
    for delta,y in zip(steering.T,[.27,-.27]):
        tangent=np.tan(delta);ks.append(tangent/(.6+y*tangent))
    rear=.12*(v[:,right]-v[:,left])/.54
    commanded=.12*(ctrl[:,3]-ctrl[:,2])/.54
    witness=[]
    for tick in [6165,6175,6200,6213]:
        i=tick-1
        witness.append(dict(native_tick=tick,requested_v_w=cmd[i,1:3].tolist(),map_measured_v_w=cmd[i,3:5].tolist(),
             actual_body_v_w=[float(vx[i]),float(w[i])],actual_rear_velocity=v[i,[left,right]].tolist(),
             rear_velocity_target=ctrl[i,2:4].tolist(),actual_front_steering=steering[i].tolist()))
    result=dict(models=0,integrations=0,source='V982 saved complete native trace; original Release member SHA checked',
        source_inventory='records/nav2_v982_20261110/RECORD_INDEX.json',input_files=receipt['files'],
        xml_addresses_only=dict(path=str(xml.relative_to(R)),sha256=sha(xml),nq=nq,nv=nv,joints=joint,
             actual_actuator_metadata_source='saved MODEL_BUILD_CONTRACT, not unmodified XML gain defaults'),
        actual_rear_servos=[{k:d[k]for k in ['name','new_joint_id','new_gain','new_bias','new_force_range']}for d in drivers[2:]],
        fixed_active_native_interval=[6120,fault],samples=fault-6119,
        residual_rms=dict(body_yaw_minus_measured_rear_differential_rad_s=rms(w-rear),
            body_yaw_minus_commanded_rear_differential_rad_s=rms(w-commanded),
            body_yaw_minus_steering_kinematic_rad_s=rms(w-vx*np.mean(ks,axis=0)),
            center_lateral_velocity_m_s=rms(vy),rear_axle_lateral_velocity_m_s=rms(vy-.30*w),
            front_axle_lateral_velocity_m_s=rms(vy+.30*w)),witnesses=witness,
        hypothesis_results=dict(reference_point_as_dominant_cause_supported=False,
            body_yaw_follows_measured_rear_difference_more_closely_than_steering=True,
            original_rear_velocity_servos_exist=True,
            no_body_yaw_feedback_in_original_driving_adapter=True,
            unique_physical_root_cause_proven=False,new_feedback_stability_or_tracking_proven=False),
        conclusion='Observed rear-wheel/body transient supports testing bounded rear-only body-yaw feedback. Correlation does not identify friction, servo load or wheel slip uniquely; no new response trajectory is inferred.')
    e=result['residual_rms'];assert e['body_yaw_minus_measured_rear_differential_rad_s']<e['body_yaw_minus_steering_kinematic_rad_s']
    assert e['rear_axle_lateral_velocity_m_s']>e['center_lateral_velocity_m_s']
    (O/'ACTUATION_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k]for k in ['fixed_active_native_interval','samples','residual_rms','hypothesis_results']}))
if __name__=='__main__':main()
