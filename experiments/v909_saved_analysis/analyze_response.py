"""Independent read-only physical response reconstruction from saved native state."""
import hashlib,json,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];REC=R/'records/nav2_v909_20261109';RAW=R/'runs/v858_nav2_verified/v909'
def main():
    tasks=json.loads((R/'experiments/v909_timed_command_contract/PLATFORM_TASKS.json').read_text());rows=[]
    for index,task in enumerate(tasks):
        folder=RAW/f'platform_{index:02d}';result=folder/'QUALIFICATION.json'
        if not result.exists():continue
        original=json.loads(result.read_text());trace=folder/'physics/NATIVE_TRACE.npz'
        with np.load(trace)as z:q=z['qpos'];vel=z['qvel'];t=z['time']
        yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
        body=np.c_[q[:,:2],yaw,vel[:,0]*np.cos(yaw)+vel[:,1]*np.sin(yaw),vel[:,5]]
        commands=np.asarray(json.loads((folder/'physics/BODY_COMMANDS.json').read_text()),float)
        initial=body[199];v,w=task['command'];elapsed=np.arange(1,221)*.01;duration=np.minimum(elapsed,.2)
        expected_angle=initial[2]+w*duration
        if w==0:expected_xy=initial[:2]+v*duration[:,None]*[math.cos(initial[2]),math.sin(initial[2])]
        else:expected_xy=initial[:2]+v/w*np.column_stack((np.sin(expected_angle)-math.sin(initial[2]),math.cos(initial[2])-np.cos(expected_angle)))
        position_error=np.linalg.norm(body[200:,:2]-expected_xy,axis=1)
        yaw_error=abs(np.arctan2(np.sin(yaw[200:]-expected_angle),np.cos(yaw[200:]-expected_angle)))
        checks=dict(exact420steps=len(body)==420 and len(commands)==420 and np.max(abs(t-np.arange(1,421)*.01))<1e-10,
                    original_fixed_warm_commands=bool(np.max(abs(commands[:200,1:3]-task['warm']))<1e-12),
                    original_fixed_committed_commands=bool(np.max(abs(commands[200:220,1:3]-task['command']))<1e-12),
                    original_full200step_stop=bool(np.max(abs(commands[220:,1:3]))==0.),
                    full_saved_body_equivalence=bool(np.max(abs(np.load(folder/'BODY_SAMPLES.npz')['body']-body))<1e-8),
                    position_limit=float(position_error.max())<=.04,angle_limit=float(yaw_error.max())<=.035,
                    speed_limit=float(abs(body[:,3]).max())<=.13,yaw_rate_limit=float(abs(body[:,4]).max())<=.16,
                    stopped_by_half_second=bool(np.max(abs(body[269:,3:5]))<=.03))
        checks={k:bool(v)for k,v in checks.items()}
        rows.append(dict(index=index,task=task,checks=checks,passed=all(checks.values()),position_error_m=float(position_error.max()),yaw_error_rad=float(yaw_error.max()),
                         maximum_speed=float(abs(body[:,3]).max()),maximum_yaw_rate=float(abs(body[:,4]).max()),original_report_agrees=bool(original['passed']==all(checks.values())),native_trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest()))
    summary=dict(all18_qualified=len(rows)==18 and all(x['passed']for x in rows),analyzed=len(rows),unexecuted_or_no_complete_evidence=18-len(rows),rows=rows,
                 failure_count=sum(not x['passed']for x in rows),actual_analyzed_native=sum(420 for _ in rows),models_this_audit=0,integrations_this_audit=0,
                 scope='Native-state and delivered command reconstruction of fixed engineering response bounds; does not prove a universal dynamics envelope or navigation.')
    path=REC/'INDEPENDENT_RESPONSE_ANALYSIS.json';assert not path.exists();path.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items()if k!='rows'}))
if __name__=='__main__':main()
