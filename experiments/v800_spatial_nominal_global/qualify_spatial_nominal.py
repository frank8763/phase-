"""Saved forecasts exercise the actual modified select function; no model."""
import json,sys
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(own));sys.path.insert(1,str(repo/'experiments/v798_legacy_tracking_transplant'))
from serial_predictor import RobotPredictor,project_to_segment_path
from legacy_method import environment
from learned_proposer import Proposer
from actuator_commands import CommandMap
from self_geometry import containment_margin
from motion_tracker import install_time_gate
from exact_footprint import pose_values
read=lambda p:json.loads(p.read_text());raw=repo/'runs/v799_spatial_nominal_qualification'
assert read(raw/'FINALIZED.json')['qualification_passed']
out=repo/'runs/v800_spatial_nominal_global/pre_navigation';assert not out.exists();out.mkdir(parents=True)
pair=repo/'runs/v793_complete_joint_navigation/main_slot01/paired';protocol=read(pair/'STATIC_PROTOCOL.json')
states={x['step']:x for x in map(json.loads,(pair/'geometry_memory/motion_estimate.jsonl').open())}
plan=read(repo/'experiments/v799_spatial_nominal_qualification/FIXED_COMMANDS.json')['checkpoints']
replay=np.load(raw/'ORIGINAL_4936_NATIVE_REPLAY.npz');c=read(pair/'geometry_memory/ACTUATOR_COMMAND_CONTRACT.json');bounds=np.asarray(protocol['footprint_bounds'])
command=CommandMap.__new__(CommandMap);command.ids=c['ids'];command.lower=np.asarray(c['limits'])[:,0];command.upper=np.asarray(c['limits'])[:,1];command.rate=np.asarray(c['rate'])
rows=[]
for entry in plan:
    step=entry['step'];j=8*step-1
    real=SimpleNamespace(qpos=replay['qpos'][j],qvel=replay['qvel'][j],ctrl=replay['ctrl'][j],time=step*.08)
    q=real.qpos;current=np.r_[q[:2],np.arctan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))]
    env=environment(real,SimpleNamespace(opt=SimpleNamespace(timestep=.01)))
    predictor=RobotPredictor.__new__(RobotPredictor);predictor.command_map=command;predictor.enable_differential=True
    predictor.proposer=Proposer(repo/'runs/v690_visible_eight_meter/training_8m/proposer.json');predictor.prediction_steps=0
    pointer=[0]
    def saved_predict(self,real,target,ids,last,horizon=240,brake_after=80):
        i=pointer[0];pointer[0]+=1;gold=entry['candidates'][i]
        assert np.allclose(target,gold['target_command'],atol=1e-12,rtol=0)
        z=np.load(raw/('S%03d_R%02d_ORDINARY.npz'%(step,i)))
        self.last_forecast_qpos=z['qpos'];self.last_forecast_qvel=z['qvel'];self.last_self_bounds=z['self_bounds']
        self.prediction_self_margin=float(containment_margin(z['self_bounds'],bounds).min());self.prediction_self_contained=self.prediction_self_margin>=.002
        self.terminal_speed=float(np.linalg.norm(z['qvel'][-1,:2]));self.prediction_steps+=240
        return z['poses']
    predictor.predict=MethodType(saved_predict,predictor)
    field=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']),circles=np.asarray(protocol['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
    field.nominal_static_geometry=SimpleNamespace(**field.__dict__)
    install_time_gate(field,states[step],'predictive',protocol['known_circles'],protocol['known_rectangles'])
    feature=entry['candidates'][0]['features'];path=np.asarray(entry['reference_path'])
    proposal,gate=predictor.select(env,field,path,entry['index'],current,feature[10],feature[11],real.ctrl[command.ids])
    assert pointer[0]==25
    valid=[]
    for i,(actual,old)in enumerate(zip(predictor.last_diagnostics,entry['candidates'])):
        for k in ['features','target_command','first_command','minimum_clearance_m','self_domain_margin_m','terminal_speed_m_s']:
            assert np.max(abs(np.asarray(actual[k])-old[k]))<=1e-8,(step,i,k)
        z=np.load(raw/('S%03d_R%02d_ORDINARY.npz'%(step,i)));minimum=float(pose_values(field.nominal_static_geometry,z['poses']).min())
        assert abs(minimum-actual['nominal_spatial_minimum_clearance_m'])<=1e-10
        assert (actual['reason']is None)==(minimum>=.155)
        if actual['reason']is None:valid.append(actual)
    assert valid and proposal is not None
    winner=max(valid,key=lambda x:x['score']);assert np.array_equal(proposal,winner['first_command'])
    rows.append(dict(step=step,old_future_rejected=25,new_spatial_admissible=len(valid),selected_role=winner['proposal_role'],selected_future_nominal_minimum=winner['minimum_clearance_m'],requires_full_prefix_tail_gate=True))
result=dict(status='SPATIAL_NOMINAL_SAVED_SELECTION_QUALIFIED',records=rows,original_target_state_feature_values_exact=True,
    requires_full_causal_prefix_tail_before_any_execution=True,model_initializations=0,integrations=0)
(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
