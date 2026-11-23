"""Compile exact author numerical sources on CPU4; never dlopen or solve."""
import hashlib,json,os,resource,signal,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1654_svg_cpu_core'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def put(p,v):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');t.replace(p)

def main():
 os.sched_setaffinity(0,{4})
 assert not(O/'BUILD_ONCE_CLAIM.json').exists()
 assert read(O/'CAPTURE_RESULT.json')['passed']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 current=read(R/'CURRENT_EXPERIMENT.json');assert current['active_round']is None and not current['models_now_authorized']
 usage=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0])
 assert usage+(64+32+512)*1024**2<15*1024**3
 own=O/'upstream/SVG_MPPI/src/mppi_controller'
 original=R/'runs/v1650_comparison_completion/author_intake/upstream/SVG_MPPI/src/mppi_controller'
 grid=O/'upstream/grid_map/grid_map_core'
 eigen=R/'runs/v1340_overnight_preparation/headers/usr/include/eigen3'
 files={}
 for root in [own,original,grid]:
  for p in root.rglob('*'):
   if p.is_file():files[str(p.relative_to(R))]=sha(p)
 eigen_inputs=read(O/'EIGEN_BUILD_INPUTS.json')['files']
 prior=read(R/'runs/v1340_overnight_preparation/ACTIVE_BUILD_HEADER_MANIFEST.json')
 prior_files={x['path']:x['sha256']for x in prior['headers']}
 assert len(eigen_inputs)==530 and all(prior_files.get(n)==h and sha(R/n)==h for n,h in eigen_inputs.items())
 files.update(eigen_inputs)
 for p in [O/'CAPTURE_RESULT.json',O/'EIGEN_BUILD_INPUTS.json',Path(__file__).resolve()]:files[str(p.relative_to(R))]=sha(p)
 # Resolve the original split intake without creating modified copies.
 # Use the first original include root for the already captured headers, then
 # the supplemental root containing the three previously missing members.
 cpp=[original/'src/mpc_base.cpp',original/'src/stein_variational_guided_mppi.cpp',own/'src/prior_samples_with_costs.cpp',*sorted((grid/'src').rglob('*.cpp'))]
 assert len(cpp)==17 and all(p.is_file()for p in cpp)
 output=O/'libphase_svg_author_cpu.so'
 command=['g++','-std=c++17','-O2','-fPIC','-fopenmp','-shared','-Wl,--no-undefined','-I'+str(original/'include'),'-I'+str(own/'include'),'-I'+str(grid/'include'),'-I'+str(eigen),*[str(p)for p in cpp],'-o',str(output)]
 assert all(sha(R/n)==h for n,h in files.items())
 put(O/'BUILD_INPUTS.json',dict(files=files,command=command,source_cpp_files=len(cpp),all_author_numeric_bodies_unmodified=True,models=0))
 put(O/'BUILD_ONCE_CLAIM.json',dict(unix=time.time(),monotonic=time.monotonic(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),maximum_wall_s=180,maximum_output_bytes=32*1024**2,cpu=4,models=0,FFI_loads=0,allruns_bytes=usage))
 start=time.monotonic();p=None;result=dict(closed=False,passed=False,compiled=False,models=0,FFI_loads=0,optimizer_calls=0,physical_native=0,replay_native=0)
 env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='')
 def limits():resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
 try:
  with(O/'build.console').open('xb')as log:
   p=subprocess.Popen(command,cwd=R,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True,preexec_fn=limits)
   try:p.wait(timeout=180)
   except subprocess.TimeoutExpired:
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=5)
    raise TimeoutError('AUTHOR_CPU_BUILD180_STOP')
  result['returncode']=p.returncode
  assert p.returncode==0,'AUTHOR_CORE_COMPILE_REFUSED'
  assert output.is_file()and 0<output.stat().st_size<=32*1024**2
  assert (O/'build.console').stat().st_size<=2*1024**2
  assert all(sha(R/n)==h for n,h in files.items()),'AUTHOR_OR_DEPENDENCY_SOURCE_MUTATED'
  result.update(passed=True,compiled=True,library_path=str(output.relative_to(R)),library_sha256=sha(output),library_bytes=output.stat().st_size,source_members=len(files),source_bodies_unchanged=True,no_library_load_or_constructor=True)
 except BaseException as error:result['first_error']=repr(error)
 finally:
  result.update(closed=True,wall_s=time.monotonic()-start,all_source_SHA_unchanged=all(sha(R/n)==h for n,h in files.items()))
  put(O/'BUILD_RESULT.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
