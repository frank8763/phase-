"""Zero-model last-second actor/scan/control analysis and measured trajectory figure."""
import gzip,hashlib,importlib.util,json,math,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v888_exact_lidar_dynamic';REC=R/'records/nav2_v888_20261108';RAW=R/'runs/v858_nav2_verified/v888/main_we'
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
    assert json.loads((O/'COMPLETION.json').read_text())['closed']
    p=RAW/'physics';setup=json.loads((p/'SETUP.json').read_text());native=json.loads((RAW/'RESULT.json').read_text());config=setup['actor']
    sensor=load('saved_exact_original_sensor',R/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs/phase14_sensor_utils.py')
    sensors=json.loads(gzip.decompress((p/'SENSORS.json.gz').read_bytes()));tail=[]
    for row in sensors:
        if row['time']<native['actual_native']*.01-2.:continue
        env=SimpleNamespace(robot_xy=np.asarray(row['xy'],np.float32),robot_yaw=row['yaw'],map_min=-5.,map_max=5.,rect_obstacles=np.asarray(setup['known']['known_rectangles'],np.float32),circle_obstacles=np.asarray(setup['known']['known_circles'],np.float32))
        without=sensor.get_lidar_features(env,32,3.)*3.;raw=np.asarray(row['raw_lidar'])*3.;values=np.asarray(row['ranges'])
        hits=np.where((raw<without-1e-5)&(values<2.94))[0]
        tail.append(dict(native_tick=row['native_tick'],sim_s=row['time'],valid_actor_rays=hits.tolist(),corrupted_ranges_m=values[hits].tolist()))
    with np.load(p/'NATIVE_TRACE.npz')as z:
        times=z['time'].copy();clear=z['clearance'].copy();position=z['qpos'][:,:2].copy();speeds=np.linalg.norm(z['qvel'][:,:2],axis=1);last=z['qpos'][-1].copy()
    commands=np.asarray(json.loads((p/'BODY_COMMANDS.json').read_text()));recent=commands[-100:];valid=[r for r in tail if r['valid_actor_rays']];decomposition=json.loads((O/'CLEARANCE_DECOMPOSITION.json').read_text())
    report=dict(status='DYNAMIC_CLEARANCE_GATE_FAILED_NOT_TIMING',actual_native=native['actual_native'],fully_recorded_native=native['fully_recorded_native'],failed_final_native_snapshot_saved=(p/'FAILED_NATIVE_STATE.npz').is_file(),full_replay_status=native['replay_status'],replay_native=None,replay_not_executed_because_final_accepted_trace_record_absent=True,last2s_scan_frames=len(tail),last2s_frames_with_surviving_actor_return=len(valid),last_surviving_actor_return=None if not valid else valid[-1],last100_native_commanded_linear_minmax=recent[:,1].min().item(),last100_native_commanded_linear_max=recent[:,1].max().item(),last100_native_actual_speed_minmax=[float(speeds[-100:].min()),float(speeds[-100:].max())],decomposition=decomposition,observed_pre_failure_collision_monitor_approach_messages=True,causal_limits=['Static clearance lower bound proves the dynamic actor is the actual clearance minimum source here','Current reactive footprint approach generated late deceleration, while the actor kept moving; this is not a proof of a unique internal Nav2 bug','Local costmap states were not archived; do not claim an exact costmap reconstruction or isolate sparse returns versus actuator lag','Stopping alone does not guarantee a stationary safe gap against a moving obstacle','Original .15m gate remains unchanged; no rounding waiver or new physical replay is authorized in this closed batch'],models=0,integrations=0)
    (REC/'FAILURE_ANALYSIS.json').write_text(json.dumps(report,indent=2)+'\n');(O/'LAST_TWO_SECONDS_ACTOR_RETURNS.json').write_text(json.dumps(tail,indent=2)+'\n')
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle,Circle
    fig,axes=plt.subplots(1,2,figsize=(12,4.6),constrained_layout=True)
    ax=axes[0]
    for x,y,hx,hy in setup['known']['known_rectangles']:ax.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,color='0.78'))
    for x,y,r in setup['known']['known_circles']:ax.add_patch(Circle((x,y),r,color='0.78'))
    actor=np.asarray(config['anchor_xy'])+config['amplitude_m']*np.sin(config['omega_rad_s']*times[:,None]+config['phase_rad'])*np.asarray(config['axis_xy'])
    ax.plot(position[:,0],position[:,1],color='#2369bd',label='Actual vehicle trajectory')
    ax.plot(actor[:,0],actor[:,1],color='#e07428',label='Actor motion (evaluation only)')
    ax.scatter(*native['first_actor_detection']['xy'],color='#008b5a',marker='o',label='First actual detection')
    ax.scatter(*native['final_body'][:2],color='#b32025',marker='x',s=70,label='Clearance stop')
    ax.scatter(*setup['case']['goal_xy'],color='black',marker='*',s=100,label='Original goal')
    ax.set(xlim=(-4.6,4.7),ylim=(-3.6,.6),aspect='equal',xlabel='x (m)',ylabel='y (m)',title='V888 actual run: no goal arrival');ax.legend(fontsize=7,loc='lower left');ax.grid(alpha=.2)
    ax=axes[1];mask=times>=66.;ax.plot(times[mask],clear[mask],label='Recorded actual clearance (m)',color='#2369bd');ax.axhline(.15,color='#b32025',linestyle='--',label='Unchanged 0.15 m floor');ax.scatter(native['actual_native']*.01,native['minimum_actual_clearance_m'],color='#b32025',marker='x',label='Failed native snapshot')
    ax2=ax.twinx();ax2.plot(times[mask],speeds[mask],color='#008b5a',alpha=.7,label='Actual speed (m/s)');ax2.set_ylabel('Actual speed (m/s)',color='#008b5a');ax.set(xlabel='Simulation time (s)',ylabel='Clearance (m)',title='Actor closes gap as vehicle slows');ax.grid(alpha=.2);ax.legend(fontsize=7,loc='upper right')
    fig.savefig(REC/'DYNAMIC_FAILURE_TRAJECTORY.png',dpi=150);plt.close(fig)
    print(json.dumps(report),flush=True)
if __name__=='__main__':main()
