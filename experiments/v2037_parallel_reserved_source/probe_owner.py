"""One source-bound nonphysical MPPI RNG preload probe before formal claims."""
from pathlib import Path
import importlib.util,json,os,subprocess,time,hashlib
R=Path(__file__).resolve().parents[2];S=R/'runs/v2037_parallel_reserved_source';O=S/'lanes/common_02__MPPI';C=R/'experiments/v2039_mppi02_reserved_census'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
 os.sched_setaffinity(0,{5});assert read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed'];assert not(O/'RNG_PROBE_ONCE.json').exists()and not(O/'PILOT_ONCE_CLAIM.json').exists()
 put(O/'RNG_PROBE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),maximum_s=300,models=0,controller_constructors=0,optimizer_queries=0))
 now=time.time();mono=time.monotonic();put(O/'RNG_PROBE_ADMISSION.json',dict(scope='MPPI_PRECONSTRUCTOR_RNG_PROBE',models_authorized=False,source_freeze_sha256=sha(S/'SOURCE_FREEZE.json'),deadline_unix=now+300,deadline_monotonic=mono+300));out=O/'rng_probe_output';out.mkdir()
 ros=load('original_readonly_ROS_namespace',R/'experiments/v856_nav2_foundation/ros_environment.py');cmd=ros.command(['/usr/bin/python3.12','-I','-B','-S',str(C/'rng_probe.py')]);i=cmd.index('--bind');assert cmd[i+1:i+3]==[str(R/'runs'),str(R/'runs')];cmd[i]='--ro-bind';j=cmd.index('--chdir');cmd[j:j]=['--bind',str(out),str(out)];env=ros.environment();overlay=R/'runs/v931_deadband_consistent_mppi/install';env.update(PHASE_REPO=str(R),CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',ROS_LOG_DIR='/tmp/rng_probe',ROS_LOGGING_DISABLE_FILE_LOGGING='1',ROS_DOMAIN_ID='239',AMENT_PREFIX_PATH=str(overlay)+':/opt/ros/jazzy',LD_LIBRARY_PATH=str(overlay/'lib')+':'+env['LD_LIBRARY_PATH'],LD_PRELOAD=str(R/'runs/v1319_mppi_coherent_sampling/libcoherent.so'),PHASE_COHERENT_NOISE='1')
 with(O/'rng_probe.console').open('xb')as f:p=subprocess.run(['taskset','-c','6','nice','-n','19',*cmd],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=300)
 result=read(out/'RESULT.json')if(out/'RESULT.json').exists()else dict(passed=False,closed=True,first_error='RNG_PROBE_RESULT_MISSING',actual_controller_constructors=None,actual_optimizer_queries=None,models=0)
 put(O/'RNG_RUNTIME_PROBE_RESULT.json',dict(passed=p.returncode==0 and result['passed'],closed=True,returncode=p.returncode,native_result=result,no_formal_slot_claimed=True,models=0,wall_s=time.monotonic()-mono));print(json.dumps(read(O/'RNG_RUNTIME_PROBE_RESULT.json')));return 0 if p.returncode==0 and result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
