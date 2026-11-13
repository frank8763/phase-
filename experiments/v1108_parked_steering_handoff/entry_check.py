"""Saved NOMINAL cusp steering-only qualification; no physical model."""
import sys,json,ast,hashlib,importlib.abc
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1108_parked_steering_handoff'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','physical','vehicle','factory','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/rpccr_execution_core'));import kernel,numpy as np
sys.path.insert(0,str(C));from prediction import Predictor,initial;from parked_control import Adapter;import track
from recovery_source import forecast_packet
def main():
    for p in C.glob('*.py'):ast.parse(p.read_text())
    x=json.loads((R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json').read_text());parent=R/'runs/v1107_reference_frame_alignment'
    with np.load(parent/'CONTROLLER_SOURCE.npz')as z:state=z['states'][3641].copy();last=z['controls'][3640].copy()
    memory=np.r_[last,0.];packet=forecast_packet(x['packet'],state,memory,3641);origin=initial(packet);origin['state']=state.copy()
    def fresh():
        p=Predictor(x['setup'],origin,kernel.PARAMETERS);p.adapter.__class__=Adapter;return p
    p=fresh();p.adapter.parked_target=track.CAP;ss=[p.state.copy()];uu=[];mode=[];stable=0
    for i in range(600):
        s,u=p.step(0.,0.,False);ss.append(s);uu.append(u);mode.append(1)
        ready=abs(s[6]-track.CAP)<=.005 and abs(s[7])<=.015 and np.max(abs(s[3:6]))<=.003
        stable=stable+1 if ready else 0
        if stable>=10:break
    assert stable>=10,'SAVED_CUSP_STEERING_NOT_SETTLED'
    alignment=len(uu);assert np.array_equal(np.array(uu)[:,2:],np.zeros((alignment,2)))
    p.adapter.parked_target=None
    for _ in range(2200):s,u=p.step(0.,0.,False);ss.append(s);uu.append(u);mode.append(0)
    ss=np.array(ss);uu=np.array(uu);rr=np.zeros((len(uu),3));a,b=kernel.ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(ss[:,:3]);low=float(np.minimum(a,b).min());cc,_=kernel.checks(ss,uu,rr,packet,x['setup'],ss[-1,:2],low,kernel.REQUIRED);cc.pop('goal_upper');assert all(cc.values()),cc
    # Explicit mode log regenerates states/controls; no body reset is used.
    replay=fresh();error=0.
    for k,flag in enumerate(mode):
        replay.adapter.parked_target=track.CAP if flag else None;s,u=replay.step(0.,0.,False);error=max(error,float(abs(s-ss[k+1]).max()),float(abs(u-uu[k]).max()))
    assert error<=1e-8
    negative=[]
    def refused(name,fn):
        try:fn()
        except AssertionError:negative.append(name);return
        raise AssertionError('NEGATIVE_ACCEPTED '+name)
    def command(v,w,mv,target=track.CAP,rear=0.):
        q=fresh();q.adapter.parked_target=target;q.adapter.last[2:]=rear;return q.adapter.compute(v,w,mv,0.,False)
    refused('moving_body',lambda:command(0.,0.,.01));refused('drive_during_alignment',lambda:command(.08,0.,0.));refused('nonzero_rear',lambda:command(0.,0.,0.,rear=.001));refused('steering_target_outside_cap',lambda:command(0.,0.,0.,target=track.CAP+.001))
    refused('missing_mode_log',lambda:track.replay(x,ss,uu,rr))
    # New wrapper must delegate ordinary driving exactly to the old allocator.
    base_origin=initial(x['packet']);new=Predictor(x['setup'],base_origin,kernel.PARAMETERS);new.adapter.__class__=Adapter;old=Predictor(x['setup'],base_origin,kernel.PARAMETERS);ordinary_error=0.
    for _ in range(250):
        s,u=new.step(-.03,0.,False);s0,u0=old.step(-.03,0.,False);ordinary_error=max(ordinary_error,float(abs(s-s0).max()),float(abs(u-u0).max()))
    assert ordinary_error<=1e-8
    refused_import=[]
    for name in ['mujoco','physical','vehicle','factory','torch','rclpy']:
        try:__import__(name)
        except AssertionError:refused_import.append(name)
    assert len(refused_import)==6
    np.savez_compressed(O/'NOMINAL_CUSP_ALIGNMENT_QUALIFICATION.npz',states=ss,controls=uu,requests=rr,modes=mode,steering_target=track.CAP)
    q=dict(passed=True,saved_nominal_cusp_native=3641,not_actual_vehicle_state=True,alignment_native=alignment,complete_tail_native=2200,minimum_full_cycle_raw_m=low,checks=cc,maximum_mode_replay_error=error,ordinary_allocator_error=ordinary_error,negative_cases=negative,imports_refused=refused_import,rear_targets_zero=True,physical_response_not_yet_qualified=True,analytical_work=dict(cpp_native=0,python_native=2*(alignment+2200)+500),models=0,physical_integrations=0)
    (O/'ENTRY_QUALIFICATION.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q))
if __name__=='__main__':main()
