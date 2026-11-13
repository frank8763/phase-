"""Regression at the actual saved-state metric seam; zero new prediction."""
import sys,json,importlib.abc
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1105_interpolated_lookahead'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','physical','vehicle','torch','factory','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/rpccr_execution_core'));import kernel
sys.path.insert(0,str(C));import track,numpy as np
def main():
    straight=np.array([[0.,0.,0.],[.12,0.,0.]])
    assert abs(track.path_distance([.06,0.],straight))<1e-12,'SPARSE_VERTEX_IS_NOT_CROSS_TRACK'
    assert abs(track.path_distance([.06,.041],straight)-.041)<1e-12,'TRUE_04M_DEVIATION_MUST_STILL_FAIL'
    assert abs(track.path_distance([-.02,0.],straight)-.02)<1e-12,'SEGMENT_ENDPOINT_CLAMP'
    assert abs(track.path_distance([.03,.04],np.zeros((2,3)))-.05)<1e-12,'DEGENERATE_SEGMENT'
    corner=np.array([[0.,0.,0.],[1.,0.,0.],[1.,1.,0.]])
    assert abs(track.path_distance([.8,.2],corner)-.2)<1e-12,'CORNER_MUST_NOT_BE_DIAGONAL_SHORTCUT'
    old=R/'runs/v1103_connected_reference';p=json.loads((old/'PATH_GEARS.json').read_text());g=p['gear'];end=next((i for i,v in enumerate(g)if v!=g[0]),len(g));path=np.array(p['path'])[:end+1]
    with np.load(old/'CONTROLLER_SOURCE.npz')as z:states=z['states'].copy()
    measured=max(track.path_distance(s,path)for s in states)
    reference=json.loads((old/'TRACKING_METRIC_DIAGNOSIS.json').read_text())['maximum_continuous_polyline_distance_m']
    assert abs(measured-reference)<=1e-12 and measured<.04,'SAVED155_REGRESSION'
    body=np.array(json.loads((R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json').read_text())['packet']['body'])
    target=track.lookahead_target(body,path,0,.25)
    assert abs(np.linalg.norm(target-body[:2])-.25)<=1e-12,'FIXED25CM_TARGET_REQUIRED'
    for direction in [-1,1]:
        line=np.array([[0.,0.,0.],[direction,0.,0.]])
        assert np.max(abs(track.lookahead_target([0.,0.],line,0)-[direction*.25,0.]))<=1e-12,'FORWARD_REVERSE_TARGET'
    short=np.array([[0.,0.,0.],[.1,0.,0.]])
    assert np.array_equal(track.lookahead_target([0.,0.],short,0),[.1,0.]),'LOOK_THROUGH_CUSP'
    bend=np.array([[0.,0.,0.],[.1,0.,0.],[.1,.4,0.]])
    assert np.max(abs(track.lookahead_target([0.,0.],bend,0)-[.1,np.sqrt(.25**2-.1**2)]))<=1e-12,'CORNER_INTERPOLATION'
    repeated=np.array([[0.,0.,0.],[0.,0.,0.],[1.,0.,0.]])
    assert np.max(abs(track.lookahead_target([0.,0.],repeated,0)-[.25,0.]))<=1e-12,'REPEATED_TARGET_POINTS'
    sparse=np.array([[0.,0.,0.],[1.,0.,0.]]);dense=np.c_[np.arange(0.,1.01,.1),np.zeros((11,2))]
    assert np.max(abs(track.lookahead_target([0.,0.],sparse,0)-track.lookahead_target([0.,0.],dense,0)))<=1e-12,'SAMPLING_DENSITY_ALIAS'
    saved=R/'runs/v1104_polyline_tracking/CONTROLLER_SOURCE.npz'
    with np.load(saved)as z:history=z['states'].copy()
    error=0.
    for state in history:
        cursor=int(np.linalg.norm(path[:,:2]-state[:2],axis=1).argmin());target=track.lookahead_target(state,path,cursor)
        error=max(error,abs(float(np.linalg.norm(target-state[:2]))-.25))
    assert error<=1e-12,'SAVED1001_INTERPOLATION_RADIUS'
    refused=[]
    for name in ['mujoco','physical','vehicle','torch','factory','rclpy']:
        try:__import__(name)
        except AssertionError:refused.append(name)
    assert len(refused)==6
    result=dict(passed=True,lookahead_source_case=True,lookahead_synthetic_cases=6,saved_interpolation_states=len(history),maximum_radius_error_m=error,metric_cases=5,saved_state_count=len(states),maximum_saved_polyline_distance_m=measured,threshold_m=.04,imports_refused=refused,new_predictions=0,models=0,physical_integrations=0)
    (O/'ENTRY_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
