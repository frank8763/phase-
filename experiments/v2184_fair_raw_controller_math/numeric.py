"""Two once-only controller mathematics queries; never create an original plant."""
import gzip,hashlib,importlib.abc,importlib.util,json,os,selectors,signal,subprocess,sys,time,traceback
from pathlib import Path
from context import R,C,S,read,sha,put
from budget import check,RUNTIME_CAP
from fixture import build,digest,strict_domain,PARAMS,GRID

class NoPlant(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','jax','kernel','vehicle','factory'}:
            raise AssertionError('CONTROLLER_MATH_NO_PLANT_OR_LEARNED_POLICY:'+name)
def load(name,path,source):
    assert source[str(path.relative_to(R))]==sha(path)
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def dwa(np,common,known,source):
    from enum import Enum
    from types import SimpleNamespace
    helper=load('v2184_frozen_signed_gear_DWA_preparation',R/'experiments/v2182_fairness_mechanism_diagnosis/dwa_shared_path.py',source)
    cfg,config_proof=helper.configuration(source);tree,ast_proof=helper.source_ast(source)
    env=dict(np=np,math=__import__('math'),Enum=Enum,_phase_signed_gear_mask=helper.sample_allowed,_phase_segment_gear=common['gear'])
    exec(compile(tree,str(R/helper.UP),'exec'),env)
    config=SimpleNamespace(**cfg);config.robot_type=env['RobotType'].rectangle
    static=load('v2184_frozen_public_geometry_point_view',R/'experiments/v1922_dwa_five_admission_checked/obstacles.py',source).make(known)
    math=__import__('math');hits=[];scan=common['scan']
    for i,r in enumerate(scan['ranges']):
        if r<3.-1e-8:
            a=scan['yaw']+2*math.pi*i/32;hits.append([scan['xy'][0]+r*math.cos(a),scan['xy'][1]+r*math.sin(a)])
    end=common['local_rear_path'][-1];goal=[end[0]+.3*math.cos(end[2]),end[1]+.3*math.sin(end[2])]
    counters=dict(control_attempts=0,control_returns=0,dynamic_window_calls=0,trajectory_attempts=0,trajectory_returns=0,mathematical_motion_calls=0)
    for name,key in [('motion','mathematical_motion_calls'),('calc_dynamic_window','dynamic_window_calls')]:
        original=env[name]
        def counted(*a,_original=original,_key=key,**k):counters[_key]+=1;return _original(*a,**k)
        env[name]=counted
    original=env['predict_trajectory']
    def trajectory(*a,**k):
        counters['trajectory_attempts']+=1;value=original(*a,**k);counters['trajectory_returns']+=1;return value
    env['predict_trajectory']=trajectory
    record=dict(method='DWA_SIGNED_GEAR_SHARED_PATH',common_input_sha256=digest(common),configuration=cfg,configuration_proof=config_proof,upstream_AST_proof=ast_proof,planning_goal_body_xy=goal,points_sha256=digest(static+hits),query_started=False)
    try:
        counters['control_attempts']=1;record['query_started']=True
        raw,path=env['dwa_control'](np.asarray(common['body'],float),config,np.asarray(goal,float),np.asarray(static+hits,float));counters['control_returns']=1
        raw=np.asarray(raw,dtype='<f8');path=np.asarray(path,dtype='<f8');assert raw.shape==(2,)and path.ndim==2 and path.shape[1]==5 and len(path)<=128 and np.isfinite(raw).all()and np.isfinite(path).all(),'NONFINITE_DWA_OUTPUT'
        record.update(raw_twist=raw.tolist(),raw_double_bytes_hex=raw.tobytes().hex(),trajectory_shape=list(path.shape),trajectory_f64_bytes_hex=path.tobytes().hex())
        accepted=strict_domain(float(raw[0]),float(raw[1]),common['gear'],source)
        record.update(passed=True,strict_common_request=accepted,output_clipped_or_repaired=False)
    except BaseException as e:record.update(passed=False,first_error=repr(e),traceback=traceback.format_exc())
    record['mathematical_work_counts']=counters;record['original_plant_steps']=0;record['total_internal_work']=None
    return record

def rpp(np,common,source):
    front=load('v2184_frozen_native_costmap_representation',R/'experiments/v2046_rpp_remaining_three/current_map.py',source)
    request=dict(schema='PHASE_CURRENT_SOLVER_INPUT_V1',run_id='V2184_FIXED_HISTORICAL_MATH',method='RPP',native_tick=0,sim_time=0.,body=common['body'],steering=common['steering'],controller_memory=common['controller_memory'],scan=common['scan'],goal_xy=common['actual_global_goal_xy'],public_route=[p[:2]for p in common['local_rear_path']],measurement_source_packet_sha256=common['source_packet_sha256'],motion_class_prior_only=True,physical_authority=False)
    builder=front.Frontend(np,public_sha256=source[GRID],parameter_sha256=source[PARAMS]);grid=builder.build(request)
    path=[p[:3]for p in common['local_rear_path']];payload=json.dumps(dict(request=request,map=grid,path=path,common_input_sha256=digest(common)),sort_keys=True,separators=(',',':'),allow_nan=False).encode();assert len(payload)<=128*1024,'RPP_INPUT_PIPE_CAP_BEFORE_LOAD'
    ros=load('v2184_exact_ROS_readonly_namespace',R/'experiments/v856_nav2_foundation/ros_environment.py',source);env=ros.environment();env.update(ROS_DOMAIN_ID='184',ROS_LOG_DIR='/tmp/v2184_native_math_logs',ROS_LOGGING_DISABLE_FILE_LOGGING='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    command=ros.command(['/usr/bin/python3.12','-I','-B','-S',str(C/'rpp_worker.py')]);i=command.index('--bind');assert command[i+1:i+3]==[str(R/'runs'),str(R/'runs')];command[i]='--ro-bind'
    child=None;stdout=bytearray();stderr=bytearray();drained=False;record=dict(method='RPP_RAW_ABI2',common_input_sha256=digest(common),native_request_sha256=digest(request),costmap_logical_sha256=digest(grid),pipe_input_sha256=hashlib.sha256(payload).hexdigest(),pipe_input_bytes=len(payload),query_runtime_work_unknown=True,passed=False)
    try:
        child=subprocess.Popen(command,cwd=R,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        child.stdin.write(payload);child.stdin.close();sel=selectors.DefaultSelector()
        for stream in [child.stdout,child.stderr]:sel.register(stream,selectors.EVENT_READ)
        end=time.monotonic()+45
        while sel.get_map():
            assert time.monotonic()<end,'RPP_MATH_PEER45S'
            for key,_ in sel.select(.1):
                data=os.read(key.fileobj.fileno(),4096)
                if not data:sel.unregister(key.fileobj);continue
                (stdout if key.fileobj is child.stdout else stderr).extend(data)
                assert len(stdout)+len(stderr)<=32*1024,'RPP_MATH_CONSOLE32KIB_CAP'
        child.wait(timeout=3);drained=True;lines=[line[len(b'V2184_RPP_RESULT '):]for line in stdout.splitlines()if line.startswith(b'V2184_RPP_RESULT ')]
        assert len(lines)==1,'RPP_MATH_SINGLE_RESULT_REQUIRED';value=json.loads(lines[0]);record['native_worker']=value
        assert child.returncode==0 and value['closed']and value['first_error']is None,'RPP_MATH_NATIVE_WORKER_REFUSED'
        answer=value['answer'];assert answer['common_input_sha256']==digest(common)and answer['native_query_returned']and answer['reported_solver_calls']==1
        assert answer['returncode']==0 and answer['reported_poisoned']==0,'RPP_NATIVE_MATH_QUERY_REFUSED'
        raw=answer['raw_twist'];assert len(raw)==2 and all(type(v)in(int,float)for v in raw)
        record.update(passed=True,strict_common_request=strict_domain(raw[0],raw[1],common['gear'],source),output_clipped_or_repaired=False)
    except BaseException as e:record.update(passed=False,first_error=repr(e),traceback=traceback.format_exc())
    finally:
        if child is not None and child.poll()is None:
            child.terminate()
            try:child.wait(timeout=3)
            except subprocess.TimeoutExpired:child.kill();child.wait(timeout=3)
        record.update(returncode=None if child is None else child.returncode,stdout_lossless_hex=bytes(stdout).hex(),stderr_lossless_hex=bytes(stderr).hex(),console_complete=drained)
    return record

def execute(admission,window,source):
    sys.meta_path.insert(0,NoPlant());signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('NATIVE_MATH120S')));signal.alarm(120)
    check('runtime',extra=4096);out=S/'RUNTIME';assert out.is_dir()
    # Inner PID namespace identity is separate from the owner's real host child.
    put(out/'NAMESPACE_IDENTITY.json',dict(namespace_pid=os.getpid(),namespace_start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],boot_id=window['boot_id'],host_child_nonce=admission['host_child_nonce'],physical_allowed=False))
    start=time.monotonic();records=[];first=None;common=None
    try:
        import numpy as np
        common,known=build(source)
        records.append(dwa(np,common,known,source))
        # A valid method-level refusal does not cancel the independent method;
        # source/evidence exceptions escape and close this whole scope.
        assert all(sha(R/n)==h for n,h in source.items()),'SOURCE_CHANGED_AFTER_DWA'
        records.append(rpp(np,common,source))
        assert all(sha(R/n)==h for n,h in source.items()),'SOURCE_CHANGED_AFTER_RPP'
    except BaseException as e:first=dict(error=repr(e),traceback=traceback.format_exc())
    finally:signal.alarm(0)
    evidence=dict(schema=1,common_historical_input=common,methods=records,first_error=first,physical_plant_created=False,physical_steps=0,all_internal_work_unknown_where_unmeasured=True)
    raw=json.dumps(evidence,sort_keys=True,separators=(',',':'),allow_nan=False).encode();packed=gzip.compress(raw,mtime=0);assert len(packed)<=56*1024,'MATH_CAPSULE56KIB_CAPACITY_REFUSAL'
    check('runtime',extra=len(packed)+8192)
    with(out/'EVIDENCE.json.gz').open('xb')as f:f.write(packed)
    result=dict(closed=True,scope='FIXED_RAW_CONTROLLER_MATHEMATICAL_INPUT_NOT_PHYSICAL_CAPABILITY',passed=first is None and len(records)==2 and all(r['passed']for r in records),first_error=first,method_results=[dict(method=r['method'],passed=r['passed'],first_error=r.get('first_error'))for r in records],evidence_sha256=hashlib.sha256(packed).hexdigest(),evidence_raw_sha256=hashlib.sha256(raw).hexdigest(),evidence_bytes=len(packed),evidence_raw_bytes=len(raw),common_input_sha256=None if common is None else digest(common),original_plant_factory_calls=0,original_actual_native=0,original_replay_native=0,formal_assignments_executed=0,whole_goal_success=False,mechanism_gain_established=False,wall_s=time.monotonic()-start)
    put(out/'RESULT.json',result);check('runtime');print(json.dumps(result),flush=True)
    return 0 if result['passed']else 1
