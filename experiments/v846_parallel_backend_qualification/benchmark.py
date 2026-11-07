"""Two fixed batched robot-and-floor physics benchmarks. No reward or learning."""
import gc
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback
from types import SimpleNamespace

import numpy as np

REPO = Path(__file__).resolve().parents[2]
OWN = Path(__file__).resolve().parent
ROOT = REPO / 'runs/v846_parallel_backend_qualification'
W = REPO / 'experiments/v842_staged_long_navigation'
PAIR = REPO / 'runs/v842_staged_long_navigation/v843_main_slot02/paired'
sys.path.insert(0, str(ROOT / 'deps'))
sys.path.insert(0, str(W))
import mujoco
import mujoco_warp as mjw
import warp as wp
from serial_predictor import RobotPredictor


def save(name, value):
    path = ROOT / name
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def main():
    deadline = float(os.environ['PHASE_GPU_BACKEND_DEADLINE'])
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('GPU_PARALLEL_BACKEND_DEADLINE')))
    signal.setitimer(signal.ITIMER_REAL, max(.01, deadline-time.time()))
    counts = dict(cpu_reference_native=0, gpu_completed_world_steps=0,
                  training_updates=0, navigation=0, confirmation=0)
    rows, started = [], time.perf_counter()
    status = 'RUNNING'
    try:
        freeze = json.loads((OWN / 'FREEZE.json').read_text())
        assert all(hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h for p,h in freeze['files'].items())
        wp.config.kernel_cache_dir = str(ROOT / 'warp_cache')
        wp.init()
        device = wp.get_device('cuda:0')
        assert device.is_cuda
        protocol = json.loads((PAIR / 'STATIC_PROTOCOL.json').read_text())
        # The scene is read once for existing robot physical parameters only.
        scene = mujoco.MjModel.from_binary_path(str(PAIR/'scene_model.mjb'))
        predictor = RobotPredictor(SimpleNamespace(model=scene), REPO/'runtime/mk-mini', mujoco, mujoco.mj_step)
        model, ids = predictor.model, predictor.command_map.ids
        assert model.nmocap==0 and not any(model.geom_bodyid[i]==0 and int(model.geom_type[i])!=int(mujoco.mjtGeom.mjGEOM_PLANE) for i in range(model.ngeom))
        host = mujoco.MjData(model)
        host.qpos[:] = protocol['start_qpos']
        mujoco.mj_forward(model,host)
        # First commands obey original amplitude and public slew limits.
        baseline_command = np.array([-.05,-.05,.7,.7])
        predictor.command_map.assert_first(baseline_command,np.zeros(4))
        host.ctrl[ids]=baseline_command
        for _ in range(10):
            mujoco.mj_step(model,host)
            counts['cpu_reference_native']+=1
        before=time.perf_counter()
        for _ in range(512):
            mujoco.mj_step(model,host)
            counts['cpu_reference_native']+=1
        cpu_s=time.perf_counter()-before
        cpu=dict(measured_native=512,wall_s=cpu_s,world_steps_per_second=512/cpu_s,
                 qpos=host.qpos.tolist(),qvel=host.qvel.tolist())
        save('MODEL_METADATA.json',dict(nq=model.nq,nv=model.nv,nu=model.nu,nbody=model.nbody,
                 ngeom=model.ngeom,dt=float(model.opt.timestep),rendering=False,old_arena_entities=0,
                 old_scene_copied_to_worlds=False,model_initializations=None,
                 physical_parameters_source='Existing robot-only predictor copied from original scene metadata'))
        for nworld in [64,128]:
            assert time.time()<deadline
            before=time.perf_counter()
            with wp.ScopedDevice(device):
                gpu_model=mjw.put_model(model)
                initial=mujoco.MjData(model)
                initial.qpos[:]=protocol['start_qpos']
                mujoco.mj_forward(model,initial)
                data=mjw.put_data(model,initial,nworld=nworld,nconmax=128,njmax=512)
                command=np.zeros((nworld,model.nu),np.float32)
                for index in range(nworld):
                    target=np.array([.05*(index%3-1),.05*(index%3-1),.7 if index%2==0 else-.7,.7 if index%2==0 else-.7])
                    predictor.command_map.assert_first(target,np.zeros(4))
                    command[index,ids]=target
                data.ctrl.assign(command)
                for _ in range(8):
                    mjw.step(gpu_model,data)
                wp.synchronize_device(device)
                counts['gpu_completed_world_steps']+=8*nworld
                setup_s=time.perf_counter()-before
                t0=data.time.numpy().copy()
                before=time.perf_counter()
                with wp.ScopedCapture(device=device)as capture:
                    for _ in range(8):
                        mjw.step(gpu_model,data)
                wp.synchronize_device(device)
                capture_s=time.perf_counter()-before
                tc=data.time.numpy().copy()
                captured_ticks=np.rint((tc-t0)/float(model.opt.timestep)).astype(int)
                assert np.all(captured_ticks==captured_ticks[0]) and captured_ticks[0]in[0,8]
                counts['gpu_completed_world_steps']+=int(captured_ticks.sum())
                samples=[]
                for index in range(64):
                    assert time.time()<deadline
                    before=time.perf_counter()
                    wp.capture_launch(capture.graph)
                    wp.synchronize_device(device)
                    samples.append(1000.*(time.perf_counter()-before))
                    counts['gpu_completed_world_steps']+=8*nworld
                qpos,qvel=data.qpos.numpy(),data.qvel.numpy()
                nefc,nacon=data.nefc.numpy(),data.nacon.numpy()
                assert np.isfinite(qpos).all()and np.isfinite(qvel).all()
                assert np.all(abs(np.linalg.norm(qpos[:,3:7],axis=1)-1.)<1e-3)
                assert int(np.max(nefc))<512 and int(np.max(nacon))<nworld*128,'GPU_CONTACT_OR_CONSTRAINT_BUFFER_LIMIT'
                same=float(np.max(abs(qpos[0]-qpos[6])))
                different=float(np.max(abs(qpos[0]-qpos[1])))
                assert same<=1e-6 and different>1e-6,'PARALLEL_WORLD_IDENTITY_OR_ISOLATION_FAILURE'
                free,total=device.free_memory,device.total_memory
                measured_s=sum(samples)/1000.
                row=dict(nworld=nworld,setup_and_compile_s=setup_s,graph_capture_s=capture_s,
                    capture_executed_ticks_per_world=int(captured_ticks[0]),measured_ticks_per_world=512,
                    measured_total_world_steps=nworld*512,measured_wall_s=measured_s,
                    world_steps_per_second=nworld*512/measured_s,
                    batch_8tick_latency_ms=dict(p50=float(np.percentile(samples,50)),p95=float(np.percentile(samples,95)),maximum=max(samples)),
                    batch_8tick_samples_ms=samples,identical_input_qpos_max_error=same,
                    different_input_qpos_max_difference=different,maximum_constraints=int(np.max(nefc)),
                    total_contact_counter=int(np.max(nacon)),device_memory_free_bytes=free,
                    device_memory_total_bytes=total,rendering=False,training_updates=0)
                rows.append(row)
                np.savez_compressed(ROOT/f'worlds{nworld}_final.npz',qpos=qpos,qvel=qvel,ctrl=command,nefc=nefc,nacon=nacon)
                save('PARTIAL.json',dict(records=rows,counts=counts))
                print(json.dumps({k:v for k,v in row.items()if k!='batch_8tick_samples_ms'}),flush=True)
                del data,gpu_model,capture
            gc.collect()
        status='PARALLEL_PHYSICS_BACKEND_QUALIFIED'
        save('RESULT.json',dict(status=status,records=rows,cpu_reference=cpu,counts=counts,
             elapsed_s=time.perf_counter()-started,new_policy_trained=False,
             online_latency_guaranteed=False,dynamic_acceptance_passed=False,
             same_original_full_model=False,original_robot_physical_properties_preserved=True))
    except BaseException as error:
        status='STOPPED_EXCEPTION'
        save('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc(),
             completed_counts=counts,uncounted_in_flight_gpu_world_steps_possible=True))
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        save('COMPLETION.json',dict(status=status,closed=True,counts=counts,records_completed=len(rows),
             elapsed_s=time.perf_counter()-started,no_automatic_training=True,models_initializations=None))


if __name__=='__main__':
    main()
