"""Fixed old-state compound-control qualification, with actual causal sensing.

Actor truth is used exclusively by sensor backend and physical/coverage audits.
No candidate, CEM objective or certificate receives actor configuration.
"""
import copy, fcntl, gzip, hashlib, json, math, os, signal, sys, time, traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
import mujoco.rollout

repo = Path(os.environ['PHASE_REPO']); own = Path(__file__).parent
source = repo/'experiments/v793_complete_joint_navigation'
sys.path.insert(0, str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'))
sys.path.insert(0, str(source)); sys.path.insert(0, str(own))
sys.path.insert(1, str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
sys.path.insert(1, str(repo/'experiments/v733_early_low_translation_scan'))
sys.path.insert(1, str(repo/'experiments/v753_coupled_progress_repaired'))
from legacy_method import schedule, environment, guidance, OriginalNominal
from learned_proposer import Proposer
from corridor_method import metrics as route_metrics, score as corridor_score
from retained_schedule import prepare as retain, current as check_retained, fingerprint, portion
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry, containment_margin, quaternion_matrices
from geometry_predictor import RobotPredictor
from exact_footprint import pose_values
from motion_tracker import Tracker, install_time_gate
from motion_evaluator import check_forecast
from renewal_state import encode
from sensor_model import packet as sensed_packet
from packet_contract import packet_equal
from canonical_sensor_pose import sensor_pose
from unseen_prior import clearance as unseen_clearance, set_public_origin

root = repo/'runs/v798_legacy_tracking_transplant'; root.mkdir(exist_ok=False)
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name, value):
    (root/name).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
def poses(q):
    q = np.asarray(q)
    return np.c_[q[:, :2], np.arctan2(2*(q[:, 3]*q[:, 6]+q[:, 4]*q[:, 5]),
                                      1-2*(q[:, 5]**2+q[:, 6]**2))]

os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
started = float(os.environ['PHASE_V798_STARTED'])
deadline = float(os.environ['PHASE_V798_DEADLINE'])
assert abs(deadline-started-1200) < 1e-6 and time.time() < deadline
window = dict(started_unix=started, absolute_deadline_unix=deadline, limit_s=1200,
              round_closed=False, pid=os.getpid())
dump('ROUND_WINDOW.json', window)
def timeout(*_): raise TimeoutError('V798_FIXED_ABSOLUTE_COMPONENT_STOP')
signal.signal(signal.SIGALRM, timeout); signal.setitimer(signal.ITIMER_REAL, deadline-time.time())
predictor = None; original_replay = validation = branch_replay = packets = 0
minimum = self_minimum = float('inf'); max_error = 0.; bad_contacts = 0
records = []; status = 'RUNNING'; context = 'ORIGINAL_REPLAY'; baseline_error=0.
contactlog = None
try:
    freeze = read(own/'INPUT_FREEZE.json')
    assert all(sha(repo/n) == h for n, h in freeze['files'].items()), 'FROZEN_INPUT_CHANGED'
    with (repo/'runs/v648_static_unknown/execution.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        pair = repo/'runs/v793_complete_joint_navigation/main_slot01/paired'
        cell = pair/'geometry_memory'
        protocol = read(pair/'STATIC_PROTOCOL.json'); config = read(pair/'DYNAMIC_PROTOCOL.json')
        motion = Motion(config)
        noise = read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap']
        rows = [json.loads(s) for s in (cell/'v648_execution.jsonl').read_text().splitlines()]
        # Only the preregistered prefix is parsed from the large belief log.
        beliefs = {}
        with (cell/'motion_estimate.jsonl').open() as stream:
            for line in stream:
                value = json.loads(line)
                if value['step'] in [200]: beliefs[value['step']] = value
                if value['step'] >= 200: break
        with gzip.open(cell/'sensor_packets.jsonl.gz', 'rt') as stream:
            old_packets = [json.loads(line) for line in stream]
        for p in old_packets:
            assert packet_equal(p, sensed_packet(p['xy'], p['yaw'], p['time'], p['step'],
                                                 protocol, motion, noise)), 'SENSOR_BACKEND_CHANGED'
        set_public_origin(protocol['start_qpos'][:2])
        tracker = Tracker(); trackers = {}; states = {}
        for p in old_packets:
            _, state = tracker.update_packet(p, protocol['known_rectangles'], protocol['known_circles'])
            if p['step'] in [200]:
                old = {k:v for k,v in beliefs[p['step']].items() if k != 'step'}
                assert state == old, 'ORIGINAL_CAUSAL_BELIEF_NOT_EXACT'
                trackers[p['step']] = copy.deepcopy(tracker); states[p['step']] = state
            if p['step'] >= 200: break
        dump('SENSOR_CAUSAL_CALIBRATION.json', dict(original_packets=len(old_packets),
            regenerated_all_raw_packets_exact=True, regenerated_prefix_states_exact=[200],
            model_initializations=0, integrations=0))
        m = mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb')); d = mujoco.MjData(m)
        d.qpos[:] = protocol['start_qpos']; motion.apply(m, d); mujoco.mj_forward(m, d)
        geometry = SelfGeometry(m, mujoco)
        catalog = GeometryCatalog(m, mujoco, pair/'assets/isolated_indoor.xml')
        bounds = np.asarray(protocol['footprint_bounds']); fixed_geom = m.geom_pos.copy()
        static = SimpleNamespace(half=np.array([.44, .375]), center_local=np.zeros(2),
            rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),
            circles=np.asarray(protocol['known_circles']).reshape(-1,3), sensor_points=[],
            sensor_extra=0., config=SimpleNamespace(lower=-5., upper=5.))
        predictor = RobotPredictor(SimpleNamespace(model=m, data=d), repo/'runtime/mk-mini',
                                   mujoco, mujoco.mj_step)
        ids = predictor.command_map.ids
        contract=read(own/'ACTUATOR_CONTRACT.json')
        assert ids==contract['ids'] and np.array_equal(predictor.command_map.lower,contract['lower']) and np.array_equal(predictor.command_map.upper,contract['upper']), 'ACTUATOR_CONTRACT_CHANGED'
        contactlog = gzip.open(root/'ACTUAL_NATIVE.jsonl.gz', 'wt')
        state_spec = mujoco.mjtState.mjSTATE_INTEGRATION
        def integration(data):
            v = np.empty(mujoco.mj_stateSize(m, state_spec))
            mujoco.mj_getState(m, data, v, state_spec); return v
        def physical(data, public):
            global minimum, self_minimum, bad_contacts
            box = geometry.actual(m, data); margin = float(containment_margin(box, bounds))
            true = SimpleNamespace(**{**static.__dict__, 'half':(box[2:]-box[:2])/2,
                'center_local':(box[2:]+box[:2])/2,
                'circles':np.asarray([*protocol['known_circles'], [*motion.xy(data.time), config['radius_m']]])})
            clearance = float(pose_values(true, poses(data.qpos[None]))[0])
            contacts = [catalog.classify(c, original_replay+validation+branch_replay, public,
                                         float(data.time)) for c in data.contact]
            bad_contacts += sum(c['contact_type'] in ['robot_obstacle_contact',
                              'robot_obstacle_penetration', 'unknown_contact'] for c in contacts)
            minimum = min(minimum, clearance); self_minimum = min(self_minimum, margin)
            contactlog.write(json.dumps(dict(context=context, account_native=original_replay+validation+branch_replay,
                public=public, time=float(data.time), clearance=clearance, self_margin=margin,
                qpos=data.qpos.tolist(), qvel=data.qvel.tolist(), ctrl=data.ctrl.tolist(),
                mocap=data.mocap_pos.tolist(), contacts=contacts))+'\n')
            assert clearance >= .15 and margin >= 0 and bad_contacts == 0, 'PHYSICAL_SAFETY_EXCEPTION'
            assert np.array_equal(m.geom_pos, fixed_geom), 'STATIC_MODEL_CHANGED'
            return [clearance, margin]
        snapshots = {}; original = []; native_rows = []
        with gzip.open(cell/'dynamic_native.jsonl.gz', 'rt') as stream:
            for i, line in enumerate(stream):
                if i == 1600: break
                native_rows.append(json.loads(line))
        for row in rows[:200]:
            d.ctrl[:] = row['ctrl']
            for _ in range(8):
                mujoco.mj_step(m, d); original_replay += 1; motion.apply(m, d)
                mujoco.mj_kinematics(m, d); mujoco.mj_collision(m, d)
                old = native_rows[original_replay-1]
                error = max(float(np.max(abs(d.qpos-old['qpos_full']))),
                            float(np.max(abs(d.qvel-old['qvel_full']))),
                            float(np.max(abs(d.ctrl-old['actual_ctrl']))))
                max_error = max(max_error, error); assert error <= 1e-8, 'ORIGINAL_NATIVE_REPLAY_CHANGED'
                physical(d, row['step']); original.append(integration(d))
            step = row['step']+1
            assert abs(float(d.time)-step*.08) < 1e-8
            if step in [200]:
                snap = mujoco.MjData(m); mujoco.mj_copyData(snap, m, d); snapshots[step] = snap
        np.savez_compressed(root/'ORIGINAL_REPLAY.npz', integration=original)

        def predict_controls(real, controls):
            pm = predictor.model; pd = predictor.data; mujoco.mj_resetData(pm, pd)
            for name in ['qpos', 'qvel', 'act', 'qacc_warmstart']:
                getattr(pd,name)[:] = getattr(real,name)
            pd.time = float(real.time); pd.ctrl[:] = 0.; mujoco.mj_forward(pm, pd)
            ss = mujoco.mjtState.mjSTATE_FULLPHYSICS
            initial = np.empty(mujoco.mj_stateSize(pm, ss)); mujoco.mj_getState(pm,pd,initial,ss)
            full = np.zeros((1,328,pm.nu)); full[0][:,ids] = controls
            forecast, sensor = mujoco.rollout.rollout(pm,pd,initial,full,
                initial_warmstart=real.qacc_warmstart.copy(), persistent_pool=True)
            predictor.prediction_steps += 328
            q = forecast[0,:,1:1+pm.nq].copy(); v = forecast[0,:,1+pm.nq:1+pm.nq+pm.nv].copy()
            packet = sensor[0]; geoms = packet[:,7:].reshape(328,-1,7)
            boxes = predictor.self_geometry.bounds(geoms[:,:,:3],quaternion_matrices(geoms[:,:,3:]),
                                                    packet[:,:3],packet[:,3:7])
            pd.qpos[:] = q[-1]; pd.qvel[:] = v[-1]; mujoco.mj_kinematics(pm,pd)
            boxes = np.vstack([boxes,predictor.self_geometry.actual(pm,pd)])
            return dict(qpos=q,qvel=v,controls=controls,poses=poses(q),self_bounds=boxes)

        reference=np.asarray(read(own/'REFERENCE_PATH.json')['path'],float)
        assert reference.shape[1]==4 and np.all(reference[:,3]==1)
        assert float(pose_values(static,reference[:,:3]).min())>=.155
        def evaluate(real, state, tracker_now, parameters, label, offset=0., utility=False):
            controls = schedule(parameters,real.ctrl[ids],predictor.command_map)
            z = predict_controls(real, controls)
            field = copy.copy(static)
            install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
            assert offset == 0.
            values = field.trajectory_values(z['poses'],.01)
            static_values = pose_values(static,z['poses'])
            margin = float(containment_margin(z['self_bounds'],bounds).min())
            speed = float(np.linalg.norm(z['qvel'][-1,:2]))
            angular = float(np.linalg.norm(z['qvel'][-1,3:6]))
            progress = float(np.linalg.norm(real.qpos[:2]-protocol['goal_xy'])-
                             np.linalg.norm(z['qpos'][-1,:2]-protocol['goal_xy']))
            detail=route_metrics(poses(real.qpos[None])[0],z['poses'],reference)
            safe=bool(values.min()>=.155 and margin>=.002 and speed<=.025 and angular<=.025)
            admissible=bool(safe and detail['arc_progress_m']>=-.01)
            score=corridor_score(detail,float(values.min()),margin,speed,angular)
            np.savez_compressed(root/(label+'.npz'),**z,initial_qpos=real.qpos,
                initial_qvel=real.qvel,initial_ctrl=real.ctrl[ids],initial_time=float(real.time),
                causal_values=values,static_values=static_values,parameters=parameters)
            return dict(label=label,parameters=parameters.tolist(),admissible=admissible,
                clearance_m=float(values.min()),static_minimum_m=float(static_values.min()),
                self_margin_m=margin,terminal_speed_m_s=speed,terminal_angular_rad_s=angular,
                progress_m=progress,safety_admissible=safe,score=score,**detail),z

        legacy_calibration_error=0.;route_index=11
        proposer=Proposer(repo/'runs/v690_visible_eight_meter/training_8m/proposer.json')
        assert proposer.sha256=='fc9d3132c912033e2ec04cd8ae1ce236c818c484d5b96961c6f3dc1b0548b527'
        def optimize(real,state,tracker_now,step,role,count):
            global route_index,legacy_calibration_error
            current=poses(real.qpos[None])[0]
            route_index,steer,speed=guidance(reference,current,route_index)
            env=environment(real,m);entries=[];predictions=[]
            def callback(target):
                label=f'S{step}_{role}_N{len(entries):02d}'
                r,z=evaluate(real,state,tracker_now,target,label)
                entries.append(r);predictions.append(z);return z
            legacy=OriginalNominal(predictor.command_map,proposer,callback)
            field=copy.copy(static);install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
            before=(integration(real).copy(),real.ctrl.copy())
            _,gate=legacy.select(env,field,reference,route_index,current,steer,speed,real.ctrl[ids])
            assert np.array_equal(integration(real),before[0])and np.array_equal(real.ctrl,before[1]),'LEGACY_PROPOSER_MUTATED_REAL'
            assert len(entries)==len(legacy.last_diagnostics)<=19
            best=None;best_z=None
            for r,z,diag in zip(entries,predictions,legacy.last_diagnostics):
                r['legacy_diagnostic']=diag;r['route_index']=route_index
                r['legacy_score']=diag.get('score')
                r['admissible']=bool(r['admissible']and diag['reason']is None)
                if diag.get('score')is not None:r['score']=diag['score']
                if r['admissible']and(best is None or r['score']>best['score']):best=r;best_z=z
            if step==200 and role=='R00':
                old=next(json.loads(line)for line in(cell/'control_decisions.jsonl').open()if json.loads(line)['step']==200 and json.loads(line).get('stage')=='NOMINAL')
                gold=[x for x in old['candidates']if x['proposal_role']!='DIFFERENTIAL']
                assert len(gold)==len(entries)==19
                for r,g in zip(entries,gold):
                    diag=r['legacy_diagnostic']
                    for key in ['features','target_command','first_command','terminal_speed_m_s','self_domain_margin_m','minimum_clearance_m','score']:
                        e=float(np.max(abs(np.asarray(diag[key])-np.asarray(g[key]))));legacy_calibration_error=max(legacy_calibration_error,e)
                        assert e<=1e-8,('ORIGINAL_LEGACY_200_MISMATCH',key,e)
                    assert diag['proposal_role']==g['proposal_role']and diag['reason']==g['reason']
                dump('LEGACY_200_CALIBRATION.json',dict(candidates=19,maximum_error=legacy_calibration_error,full_legacy_pipeline_identical=False))
            dump(f'S{step}_{role}_CANDIDATES.json',entries)
            dump('ACTIVE.json',dict(step=step,role=role,private=predictor.prediction_steps,original_replay=original_replay,validation=validation,branch_replay=branch_replay,packets=packets,best=None if best is None else best['label']))
            print(json.dumps(dict(role=role,proposals=len(entries),admissible=sum(x['admissible']for x in entries),best=best)),flush=True)
            return best,best_z

        def coverage(state):
            result=check_forecast(config,state); assert result['passed'], 'EXECUTION_COVERAGE_FAILURE'
            if state['center'] is None:
                times=state['time']+np.arange(657)*.01
                truth=np.array([motion.xy(t) for t in times])
                excess=float(tracker_current.recursive_unseen_domain.point_lower(truth,times).max())
                assert excess<=1e-7, 'PLANNING_COVERAGE_FAILURE'
            else:
                from union_belief import future_cells
                times=np.arange(657)*.01; lo,hi=future_cells(state['outer_state_cells'],times)
                truth=np.array([motion.xy(state['time']+t) for t in times])
                excess=float(np.maximum(lo-truth[:,None,:],truth[:,None,:]-hi).max(axis=2).min(axis=1).max())
                assert excess<=1e-7, 'PLANNING_COVERAGE_FAILURE'
            return dict(execution=result,planning_samples=657,planning_excess_m=excess)

        def actual(real,z,tracker_now,public_start,label,replaying=False):
            global validation,branch_replay,packets,max_error,context,tracker_current,baseline_error
            context=label; tracker_current=tracker_now; native=[]; observations=[]; safety=[]
            for tick,c in enumerate(z['controls']):
                if tick%8==0:predictor.command_map.assert_first(c,real.ctrl[ids])
                else:assert np.array_equal(c,real.ctrl[ids]), 'NONPUBLIC_COMMAND_CHANGE'
                real.ctrl[:]=0.;real.ctrl[ids]=c;mujoco.mj_step(m,real)
                if replaying:branch_replay+=1
                else:validation+=1
                motion.apply(m,real);mujoco.mj_kinematics(m,real);mujoco.mj_collision(m,real)
                safe=physical(real,public_start+tick//8+1);safety.append(safe)
                error=max(float(np.max(abs(real.qpos-z['qpos'][tick]))),
                          float(np.max(abs(real.qvel-z['qvel'][tick]))))
                max_error=max(max_error,error);assert error<=1e-8,'FORECAST_REAL_FULL_NATIVE_MISMATCH'
                native.append(integration(real))
                if tick%8==7:
                    public=public_start+tick//8+1;xy,yaw=sensor_pose(real.qpos)
                    p=sensed_packet(xy,yaw,float(real.time),public,protocol,motion,noise)
                    _,state=tracker_now.update_packet(p,protocol['known_rectangles'],protocol['known_circles'])
                    observations.append(dict(packet=p,state=state,coverage=coverage(state)));packets+=1
            np.savez_compressed(root/(label+'_ACTUAL.npz'),integration=native,safety=safety)
            (root/(label+'_OBSERVATIONS.json.gz')).write_bytes(gzip.compress(json.dumps(observations).encode(),mtime=0))
            return state,observations,np.asarray(native)

        step=200;snap=snapshots[step];mujoco.mj_copyData(d,m,snap)
        baseline_tracker=trackers[step];baseline_state=states[step]
        assert baseline_state['center']is None
        target=np.zeros(4);predictor.predict(d,target,ids,d.ctrl[ids],328,160)
        calibration_q=predictor.last_forecast_qpos.copy();calibration_v=predictor.last_forecast_qvel.copy()
        calibration=predict_controls(d,schedule(np.zeros(4),d.ctrl[ids],predictor.command_map))
        calibration_error=max(float(np.max(abs(calibration['qpos']-calibration_q))),float(np.max(abs(calibration['qvel']-calibration_v))))
        assert calibration_error<=1e-8,'CONTROL_SEQUENCE_PREDICTOR_CALIBRATION_FAILURE'
        dump('CALIBRATION.json',dict(maximum_native_error=calibration_error))
        tracker_main=copy.deepcopy(baseline_tracker);state=baseline_state;public=200
        cache=None;cursor=0;chunks=[];first_discovery=None;handover=[]
        stopped_reason='MAXIMUM_32_REPLANS_FINISH_RETAINED_TAIL';first_candidates_error=None
        for refresh in range(32):
            role=f'R{refresh:02d}';old_fingerprint=fingerprint(cache);old_cursor=cursor
            old_match=None if cache is None else check_retained(cache,cursor,d,predictor.command_map)
            before=(d.qpos.copy(),d.qvel.copy(),d.ctrl.copy(),float(d.time))
            chosen,z=optimize(d,state,tracker_main,200,role,48)
            assert fingerprint(cache)==old_fingerprint and cursor==old_cursor,'PROPOSALS_MUTATED_RETAINED_CERTIFICATE'
            assert all(np.array_equal(getattr(d,k),v)for k,v in zip(['qpos','qvel','ctrl'],before[:3]))and d.time==before[3],'PROPOSALS_MUTATED_REAL_STATE'
            record=dict(refresh=refresh,public_start=public,selected=chosen,actual_executed=False,
                        old_retained_label=None if cache is None else cache['label'],old_cursor=cursor,
                        old_fingerprint_unchanged=True,old_state_match=old_match)
            records.append(record);dump('BRANCHES.json',records)
            if chosen is None:
                stopped_reason='NEW_CERTIFICATE_REJECTED_EXECUTE_OLD_RETAINED_TAIL';break
            candidate=retain(d,z,np.asarray(chosen['parameters']),chosen,state,predictor.command_map,public)
            assert fingerprint(cache)==old_fingerprint and cursor==old_cursor,'PREPARE_MUTATED_OLD_CERTIFICATE'
            # Commit controller metadata only after the entire new proof is valid.
            handover.append(dict(refresh=refresh,old_label=None if cache is None else cache['label'],
                old_cursor=cursor,old_state_match=old_match,new_label=candidate['label'],
                created_step=public,created_time=float(d.time),new_remaining_native_after_prefix=296))
            cache=candidate;cursor=0
            check_retained(cache,cursor,d,predictor.command_map)
            prefix=portion(cache,0,32);label=f'S200_{role}_PREFIX'
            state,obs,native=actual(d,prefix,tracker_main,public,label)
            chunks.append(dict(label=label,certificate=cache['label'],start=0,end=32,public_start=public,
                               predictions=prefix,observations=obs,integration=native))
            public+=4;cursor=32;check_retained(cache,cursor,d,predictor.command_map)
            record.update(actual_executed=True,public_end=public,actual_end_xy=d.qpos[:2].tolist(),
                actual_absolute_goal_progress_m=float(8.-np.linalg.norm(d.qpos[:2]-protocol['goal_xy'])))
            dump('BRANCHES.json',records);dump('HANDOVERS.json',handover)
            for value in obs:
                if value['state']['center']is not None and first_discovery is None:
                    first_discovery=dict(step=value['packet']['step'],time=value['packet']['time'],xy=value['packet']['xy'])
            if first_discovery is not None:
                stopped_reason='FIRST_DISCOVERY_FINISH_CURRENT_RETAINED_SCHEDULE';break
        if cache is not None and cursor<328:
            match=check_retained(cache,cursor,d,predictor.command_map)
            suffix=portion(cache,cursor,328);label='S200_FINAL_RETAINED_TAIL'
            state,obs,native=actual(d,suffix,tracker_main,public,label)
            chunks.append(dict(label=label,certificate=cache['label'],start=cursor,end=328,
                               public_start=public,predictions=suffix,observations=obs,integration=native))
            public+=(328-cursor)//8;cursor=328;check_retained(cache,cursor,d,predictor.command_map)
            for value in obs:
                if value['state']['center']is not None and first_discovery is None:
                    first_discovery=dict(step=value['packet']['step'],time=value['packet']['time'],xy=value['packet']['xy'])
            dump('FINAL_RETAINED_TAIL.json',dict(certificate=cache['label'],start=chunks[-1]['start'],
                end=328,initial_state_match=match,completed=True,public_end=public,
                terminal_speed_m_s=float(np.linalg.norm(d.qvel[:2])),terminal_angular_rad_s=float(np.linalg.norm(d.qvel[3:6]))))
        main_terminal=(d.qpos.copy(),d.qvel.copy(),float(d.time))
        maximum_progress=None;crossed=False;arc_progress=0.
        if chunks:
            main_q=np.concatenate([x['predictions']['qpos']for x in chunks])
            main_p=poses(main_q);maximum_progress=float(np.max(8.-np.linalg.norm(main_q[:,:2]-protocol['goal_xy'],axis=1)))
            crossed=bool(np.any(main_q[:,0]>=0.))
            arc_progress=route_metrics(poses(snap.qpos[None])[0],main_p,reference)['arc_progress_m']
        mujoco.mj_copyData(d,m,snap);repeat_tracker=copy.deepcopy(baseline_tracker);repeat_errors=[];manifest=[]
        for chunk in chunks:
            _,observed,executed=actual(d,chunk['predictions'],repeat_tracker,chunk['public_start'],chunk['label']+'_REPEAT',True)
            error=float(np.max(abs(executed-chunk['integration'])))
            assert error<=1e-8 and observed==chunk['observations'],'WHOLE_RETAINED_MPC_REPEAT_OR_SENSOR_MISMATCH'
            repeat_errors.append(error);manifest.append({k:chunk[k]for k in ['label','certificate','start','end','public_start']})
        if chunks:
            assert max(np.max(abs(d.qpos-main_terminal[0])),np.max(abs(d.qvel-main_terminal[1])),abs(float(d.time)-main_terminal[2]))<=1e-8
        dump('EXECUTED_CHUNKS.json',manifest)
        qualified=bool(chunks and crossed and maximum_progress>=2.9791448279582813+.20 and arc_progress>=1.)
        assert original_replay==1600 and predictor.prediction_steps<=200080
        assert validation<=1320 and branch_replay==validation and packets*8==validation+branch_replay
        assert all(sha(repo/n)==h for n,h in freeze['files'].items()),'FROZEN_INPUT_CHANGED_AFTER_RUN'
        status='LEGACY_PROPOSER_TRANSPLANT_COMPLETE'
        dump('RESULT.json',dict(status=status,records=records,component_qualified=qualified,
            stopped_reason=stopped_reason,attempted_replans=len(records),committed_replans=len(handover),
            executed_chunks=len(chunks),old_best_absolute_progress_m=2.9791448279582813,
            maximum_absolute_goal_progress_m=maximum_progress,reference_arc_progress_m=arc_progress,
            central_root_center_crossed=crossed,first_discovery=first_discovery,
            legacy_200_calibration_error=legacy_calibration_error,original_nominal_proposer_transplanted=True,full_legacy_pipeline_identical=False,
            whole_branch_repeat_errors=repeat_errors,original_replay_native=original_replay,
            private_integrations=predictor.prediction_steps,actual_validation_native=validation,
            branch_replay_native=branch_replay,actual_packets=packets,maximum_native_error=max_error,
            minimum_actual_clearance_m=minimum,minimum_actual_self_margin_m=self_minimum,bad_contacts=bad_contacts,
            final_tail_completed=cache is None or cursor==328,new_complete_navigation=0,new_confirmation=0,
            training_updates=0,real_robot=0,stage_access=0,full_global_dynamic_passed=False,
            active_information_reward_used=False,physical_model_initializations_occurred=True,
            exact_model_constructor_count=None,wall_s=time.time()-started,
            simulated_main_branch_s=validation*.01,
            simulation_clock_only_not_real_time=True))

except BaseException as error:
    status='STOPPED_EXCEPTION'
    dump('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
    raise
finally:
    signal.alarm(0)
    if contactlog is not None:contactlog.close()
    window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
    dump('COMPLETION.json',dict(status=status,round_closed=True,original_replay_native=original_replay,
        private_integrations=None if predictor is None else predictor.prediction_steps,
        actual_validation_native=validation,branch_replay_native=branch_replay,actual_packets=packets,
        accounting_exact=status=='LEGACY_PROPOSER_TRANSPLANT_COMPLETE',
        interrupted_counter_values_are_lower_bounds=status=='STOPPED_EXCEPTION',
        possible_inflight_private_upper_extra_native=328 if status=='STOPPED_EXCEPTION'else 0,
        possible_inflight_scene_upper_extra_native=1 if status=='STOPPED_EXCEPTION'else 0))
