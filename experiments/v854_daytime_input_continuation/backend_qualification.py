"""Fixed robot-only CPU batch equivalence/timing, no navigation or training."""
import fcntl,gzip,json,os,signal,sys,time
from types import SimpleNamespace
from common import *
for name in ['runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1','runtime/mk-mini/experiments/phase_rpccr_p0b68_v1','runtime/mk-mini/training/phase14_lidar_depth_nav/envs','experiments/v733_early_low_translation_scan','experiments/v753_coupled_progress_repaired']:sys.path.insert(0,str(R/name))
sys.path.insert(0,str(W))
import numpy as np
import mujoco
from geometry_predictor import RobotPredictor
from dynamic_scene import Motion
from self_geometry import containment_margin
from native_batch import rollout_existing_sequences


def main():
    unchanged();out=ROOT/'cpu_batch_qualification';out.mkdir(exist_ok=False);end=min(DEADLINE,time.time()+600);signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('CPU_BATCH_600S')));signal.setitimer(signal.ITIMER_REAL,end-time.time());lock=(R/'runs/v648_static_unknown/execution.lock').open('rb');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});pair=R/'runs/v851_profile_output_worker/v851_main_slot01/paired';cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');motion=Motion(read(pair/'DYNAMIC_PROTOCOL.json'));m=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];motion.apply(m,d);mujoco.mj_forward(m,d);replay=0;status='RUNNING';predictor=None
    try:
        for i,row in enumerate(map(json.loads,gzip.open(cell/'dynamic_native.jsonl.gz','rt'))):
            if i>=399*8:break
            assert time.time()<end;d.ctrl[:]=row['actual_ctrl'];mujoco.mj_step(m,d);replay+=1;motion.apply(m,d);assert max(np.max(abs(d.qpos-row['qpos_full'])),np.max(abs(d.qvel-row['qvel_full'])))<=1e-8
        predictor=RobotPredictor(SimpleNamespace(model=m,data=d),R/'runtime/mk-mini',mujoco,mujoco.mj_step);ids=predictor.command_map.ids;last=d.ctrl[ids].copy();targets=np.array([[s,s,w,w]for s in[-.3,0.,.3]for w in[-8.,0.,8.]])
        seq=np.array([predictor.command_map.sequence(t,last,240,80)for t in targets]);serial=[];started=time.perf_counter()
        for target in targets:
            poses=predictor.predict(d,target,ids,last,240,80);serial.append(dict(qpos=predictor.last_forecast_qpos.copy(),qvel=predictor.last_forecast_qvel.copy(),poses=poses.copy(),self_bounds=predictor.last_self_bounds.copy(),minimum_self_margin=predictor.prediction_self_margin,terminal_speed=predictor.terminal_speed))
        serial_s=time.perf_counter()-started;started=time.perf_counter();batch=rollout_existing_sequences(predictor,d,seq);batch_s=time.perf_counter()-started;errors={k:max(float(np.max(abs(np.asarray(a[k])-np.asarray(b[k]))))for a,b in zip(serial,batch))for k in serial[0]};passed=all(x<=1e-8 for x in errors.values())
        status='CPU_BATCH_EQUIVALENCE_PASS'if passed else'CPU_BATCH_EQUIVALENCE_NOT_PASSED_NO_ADOPTION';np.savez_compressed(out/'FULL_ARRAYS.npz',controls=seq,serial_qpos=np.array([x['qpos']for x in serial]),serial_qvel=np.array([x['qvel']for x in serial]),batch_qpos=np.array([x['qpos']for x in batch]),batch_qvel=np.array([x['qvel']for x in batch]),serial_self=np.array([x['self_bounds']for x in serial]),batch_self=np.array([x['self_bounds']for x in batch]));dump(out/'RESULT.json',dict(status=status,passed=passed,errors=errors,serial_wall_s=serial_s,batch_wall_s=batch_s,measured_ratio=serial_s/batch_s,old_replay_native=replay,private_native=predictor.prediction_steps,actual_branches=0,new_navigation=0,training_updates=0,automatically_adopted_in_navigation=False,scope='Only fixed original CPU predictor nine controls, full array equivalence. Single CPU sequential batch; not real-time or GPU validation.'))
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);dump(out/'COMPLETION.json',dict(status=status,old_replay_native=replay,private_native=None if predictor is None else predictor.prediction_steps,closed=True))


if __name__=='__main__':main()
