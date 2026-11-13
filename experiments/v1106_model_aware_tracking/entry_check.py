"""Original dynamics agreement and model-aware selector entry, no physics."""
import sys,json,hashlib,importlib.abc,shutil,time,ast
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1106_model_aware_tracking'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','physical','vehicle','factory','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/rpccr_execution_core'));import kernel,numpy as np
sys.path.insert(0,str(C));from preview import Preview;import track
def main():
    for p in C.glob('*.py'):ast.parse(p.read_text())
    x=json.loads((R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json').read_text());origin=kernel.initial(x['packet']);memory=np.r_[origin['last_ctrl'],origin['integral']]
    original=kernel.Expander(x['setup']);binary=Path(original.lib._name);target=O/'analytical_dynamics.so'
    assert not target.exists();shutil.copyfile(binary,target);assert hashlib.sha256(binary.read_bytes()).digest()==hashlib.sha256(target.read_bytes()).digest()
    preview=Preview(x['setup']);error=0.;cases=0
    for speed in [.08,-.03]:
        targets=np.linspace(-track.CAP,track.CAP,5);ss,uu,_=preview.expand(origin['state'],memory,targets,speed,500)
        for k,t in enumerate(targets):
            s,u,_,_=kernel.predict(x['setup'],x['packet'],[dict(kind='move',gear=1 if speed>0 else-1,speed=speed,target=float(t),ticks=500)],tail=False)
            error=max(error,float(abs(ss[k]-s[1:]).max()),float(abs(uu[k]-u).max()));cases+=1
    assert error<=1e-8,'ORIGINAL_DYNAMICS_DIFFER'
    pg=json.loads((R/'runs/v1103_connected_reference/PATH_GEARS.json').read_text());g=pg['gear'];end=next((i for i,v in enumerate(g)if v!=g[0]),len(g));path=np.array(pg['path'])[:end+1];arc=np.r_[0.,np.linalg.norm(np.diff(path[:,:2],axis=0),axis=1).cumsum()]
    progress=track.project_arc(np.array(origin['state']),path,arc,0.);started=time.monotonic();t,v,ss,uu,cost=track.select(preview,np.array(origin['state']),memory,path,arc,progress,g[0]);elapsed=time.monotonic()-started
    s,u,_,_=kernel.predict(x['setup'],x['packet'],[dict(kind='move',gear=g[0],speed=v,target=t,ticks=25)],tail=False)
    selected_error=max(float(abs(ss-s[1:]).max()),float(abs(uu-u).max()));assert selected_error<=1e-8
    # Ensure progress cannot leap across a self-near later part of a section.
    assert track.project_arc(path[-1],path,arc,0.)<=.25+1e-12
    unsafe=np.zeros((1,25,8));unsafe[:,:,1]=.041;line=np.array([[0.,0.,0.],[1.,0.,0.]])
    assert track.prefix_cross(unsafe,line)[0]>.04,'REAL_DEVIATION_NOT_REFUSED'
    # Full-state stop construction must preserve a nonzero lateral component.
    state=np.array(origin['state']);state[4]=.002
    stop_s,stop_u,stop_r=track.complete_stop(x['setup'],x['packet'],state,memory)
    assert np.array_equal(stop_s[0],state)and stop_s[0,4]==.002 and len(stop_r)==2200
    refused=[]
    for name in ['mujoco','physical','vehicle','factory','torch','rclpy']:
        try:__import__(name)
        except AssertionError:refused.append(name)
    assert len(refused)==6
    result=dict(passed=True,original_dynamics_cases=cases,maximum_cpp_python_error=error,selected_block_error=selected_error,selected_target=t,selector_wall_s=elapsed,first_candidate_count=22,preview_native=preview.native,original_python_calibration_native=cases*500+25,full_state_stop_calibration_native=2200,nonzero_lateral_stop_preserved=True,progress_jump_refused=True,true_04m_deviation_refused=True,imports_refused=refused,binary=str(binary.relative_to(R)),binary_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),models=0,physical_integrations=0)
    (O/'ENTRY_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
