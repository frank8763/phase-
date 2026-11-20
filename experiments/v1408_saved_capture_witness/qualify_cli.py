"""Complete-method producer imports/real RPC/failure saves, zero models."""
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
io=exact('v1406_qualified_atomic_json',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));os.chdir(R);O.mkdir(exist_ok=False)
    parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and not parent['models_now_authorized']and time.time()<1795395600-400
    assert read(R/'runs/v1401_model_origin_qualification/COMPLETION.json')['passed']
    with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    saved=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(saved).hexdigest()==parent['review_pending_original_bytes_sha256']
    started=time.monotonic();deadline=min(started+300,parent['hard_stop_monotonic']-10)
    io.atomic(O/'CLAIM.json',dict(started_unix=time.time(),hard_stop_monotonic=deadline,models=0,maximum_production_entries=3,maximum_peer_launches=1))
    current=read(R/'runs/v1398_current_event_witness/peer_qualification02/CURRENT_INPUT.json')
    import math
    previous=current.pop('input_sha256');b=current['origin']['body'];p=current['next_segment']['poses'][0];rear=[b[0]-.3*math.cos(b[2]),b[1]-.3*math.sin(b[2]),b[2]]
    geometry=dict(start_distance_m=math.dist(rear[:2],p[:2]),start_heading_rad=abs(math.atan2(math.sin(rear[2]-p[2]),math.cos(rear[2]-p[2]))),minimum_clearance_m=.21)
    dispatch=exact('v1406_qualification_current_dispatch',R/'experiments/v1404_route_bridge_session/method_dispatch.py')
    request=dict(event=dict(body=b,geometry=geometry),next_segment=current['next_segment'],actual=dict(feedback=dict(gear_memory=current['gear_memory'])))
    current.update(base_input_sha256=previous,event_geometry=geometry,method_spec=dispatch.choose(request))
    current['input_sha256']=hashlib.sha256(json.dumps(current,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    fixed=read(R/'runs/v1401_model_origin_qualification/FIXED_INPUTS.json');setup=read(R/fixed['setup_file'])
    files={}
    for freeze in ['runs/v1398_current_event_witness/INPUT_PEER_SOURCE_FREEZE.json','runs/v1398_current_event_witness/CPU2_ENTRY_SOURCE_FREEZE.json','runs/v1402_current_witness_evidence/EVIDENCE_SOURCE_FREEZE.json']:
        for name,h in read(R/freeze)['files'].items():assert name not in files or files[name]==h;files[name]=h
    for p in C.glob('*'):
        if p.is_file():files[str(p.relative_to(R))]=sha(p)
    files['experiments/v1398_current_event_witness/modeled_client.py']=sha(R/'experiments/v1398_current_event_witness/modeled_client.py')
    assert all(sha(R/n)==h for n,h in files.items())
    env=dict(os.environ);env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');env.pop('LD_PRELOAD',None)
    peer=None;log=None;result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,physical_admission=False,entries=[],fixture_not_new_actual_measurement=True)
    try:
        for mode,flag in [('entry','--entry-check'),('rpc','--rpc-check'),('early_failure','--injected-early-failure')]:
            assert time.monotonic()<deadline-65
            out=O/mode;out.mkdir();io.atomic(out/'CURRENT_INPUT.json',current);io.atomic(out/'SETUP.json',setup)
            authority=dict(scope='ZERO_MODEL_PRODUCTION_QUALIFICATION',maximum_model_constructions=0,maximum_model_steps=0,models_authorized=False,current_input_sha256=current['input_sha256'],tested_source_hashes=files,boot_id=parent['boot_id'],run_id='v1408-lossless-complete-method-rpc-only',hard_stop_monotonic=deadline,absolute_deadline_unix=min(time.time()+deadline-time.monotonic(),1795395600))
            io.atomic(out/'APPROVAL.json',authority)
            if mode=='rpc':
                helper=exact('v1406_original_peer_environment',R/'experiments/v1396_rpp_rpc_retirement/peer_environment.py');ros,peer_env=helper.environment(out)
                log=(out/'peer.console').open('x');peer=subprocess.Popen(ros.command(['taskset','-c','3','/usr/bin/python3.12','-B',str(C/'modeled_peer.py'),str(out),authority['run_id']]),cwd=R,env=peer_env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                until=time.monotonic()+10
                while not(out/'peer.sock').exists():assert peer.poll()is None and time.monotonic()<until;time.sleep(.02)
            (R/'REVIEW_PENDING').unlink()
            try:p=subprocess.run(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'production_entry.py').relative_to(R)),str(out),flag],cwd=R,env=env,capture_output=True,text=True,timeout=min(65,max(1,deadline-time.monotonic()-10)))
            finally:(R/'REVIEW_PENDING').write_bytes(saved)
            (out/'entry.console').write_text(p.stdout+p.stderr)
            if mode=='early_failure':
                proof=read(out/'RESULT.json');assert p.returncode==1 and proof['error']=="RuntimeError('QUALIFIED_INJECTED_BEFORE_ANY_MODEL_CALL')"and proof['analytical_native']==0 and not proof['analytical_inflight_unknown']and proof['explicit_predictor_constructions']==0 and not proof['model_call_started']and not proof['evidence_write_errors'];entry=dict(mode=mode,first_error_saved=True,known_zero_model_count=True,passed=True)
            else:
                assert p.returncode==0,p.stderr[-1800:]
                proof=read(out/('ENTRY_CHECK.json'if mode=='entry'else'RESULT.json'));assert proof['passed']and proof['analytical_native']==0 and proof['actual_cpu']==[2];entry=dict(mode=mode,passed=True,models=0,analytical_native=0)
            if mode=='rpc':
                peer.wait(timeout=10);peer_proof=read(out/'PEER_RESULT.json');assert peer.returncode==0 and peer_proof['passed']and peer_proof['synthetic_scan_messages']==0 and peer_proof['controller_exited']
                accepted=read(out/'MODELED_ACCEPTED.json');assert len(accepted)==2 and all(x['input_sha256']==current['input_sha256']and x['not_measured_response']for x in accepted)
                entry['real_original_plugin_callbacks']=2;entry['actual_production_rpc_client']=True;peer=None;log.close();log=None
            result['entries'].append(entry)
        result['passed']=len(result['entries'])==3
    except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        if peer is not None and peer.poll()is None:
            os.killpg(peer.pid,signal.SIGTERM)
            try:peer.wait(timeout=8)
            except subprocess.TimeoutExpired:os.killpg(peer.pid,signal.SIGKILL);peer.wait(timeout=3)
        if log is not None:log.close()
        (R/'REVIEW_PENDING').write_bytes(saved);result.update(closed=True,closed_unix=time.time(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==saved);io.atomic(O/'QUALIFICATION.json',result)
    if result['passed']:io.atomic(O/'SOURCE_FREEZE.json',dict(files=files,qualification='runs/v1403_current_witness_cli/QUALIFICATION.json',models=0,complete_finite_numerical_witness_not_yet_qualified=True,physical_admission=False))
    print(json.dumps({k:v for k,v in result.items()if k!='traceback'}));return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
