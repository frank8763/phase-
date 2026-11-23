"""One CPU4 wrapper compile and static ELF symbol check; zero DLL loads."""
from pathlib import Path
import hashlib,json,os,resource,signal,subprocess,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def put(p,x):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');t.replace(p)
def main():
 os.sched_setaffinity(0,{4});O.mkdir(exist_ok=True)
 assert not(O/'BUILD_ONCE_CLAIM.json').exists()
 prior=R/'runs/v1655_svg_original_build_flags';result=read(prior/'BUILD_RESULT.json')
 library=R/result['library_path'];assert result['passed']and sha(library)==result['library_sha256']
 frozen=read(prior/'BUILD_INPUTS.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
 inputs=dict(frozen)
 for p in C.iterdir():
  if p.is_file():inputs[str(p.relative_to(R))]=sha(p)
 inputs[str(library.relative_to(R))]=sha(library);inputs[str((prior/'BUILD_RESULT.json').relative_to(R))]=sha(prior/'BUILD_RESULT.json')
 original=R/'runs/v1650_comparison_completion/author_intake/upstream/SVG_MPPI/src/mppi_controller/include'
 extra=R/'runs/v1654_svg_cpu_core/upstream/SVG_MPPI/src/mppi_controller/include'
 grid=R/'runs/v1654_svg_cpu_core/upstream/grid_map/grid_map_core/include'
 eigen=R/'runs/v1340_overnight_preparation/headers/usr/include/eigen3'
 out=O/'libphase_svg_bridge.so'
 command=['g++','-std=c++17','-O2','-fPIC','-fopenmp','-shared','-Wl,--no-undefined','-DEIGEN_FUNCTORS_PLUGIN="grid_map_core/eigen_plugins/FunctorsPlugin.hpp"','-DEIGEN_DENSEBASE_PLUGIN="grid_map_core/eigen_plugins/DenseBasePlugin.hpp"',*['-I'+str(p)for p in [original,extra,grid,eigen]],str(C/'bridge.cpp'),'-L'+str(prior),'-lphase_svg_author_cpu','-Wl,-rpath,$ORIGIN/../v1655_svg_original_build_flags','-o',str(out)]
 usage=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert usage+(64+32+512)*1024**2<15*1024**3
 put(O/'BUILD_INPUTS.json',dict(files=inputs,command=command,models=0))
 put(O/'BUILD_ONCE_CLAIM.json',dict(unix=time.time(),maximum_wall_s=60,cpu=4,models=0,FFI_loads=0))
 start=time.monotonic();answer=dict(passed=False,closed=False,models=0,FFI_loads=0,constructor_calls=0,optimizer_calls=0,physical_native=0,replay_native=0)
 try:
  with(O/'build.console').open('xb')as stream:
   process=subprocess.Popen(command,cwd=R,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
   try:process.wait(timeout=60)
   except subprocess.TimeoutExpired:
    os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5);raise TimeoutError('WRAPPER_BUILD60_STOP')
  assert process.returncode==0,'SVG_WRAPPER_COMPILE_FAILED'
  symbols=subprocess.run(['nm','-D','--defined-only',str(out)],capture_output=True,text=True,timeout=10)
  assert symbols.returncode==0
  required=['phase_svg_abi_version','phase_svg_state_dimension','phase_svg_control_dimension','phase_svg_error','phase_svg_create','phase_svg_set_maps','phase_svg_solve','phase_svg_call_counts','phase_svg_destroy']
  names={line.split()[-1]for line in symbols.stdout.splitlines()if line.split()}
  assert set(required)<=names and all(sha(R/n)==h for n,h in inputs.items())
  assert 0<out.stat().st_size<=8*1024**2
  (O/'ELF_SYMBOLS.txt').write_text(symbols.stdout)
  answer.update(passed=True,compiled=True,required_symbols=required,library_path=str(out.relative_to(R)),library_sha256=sha(out),library_bytes=out.stat().st_size,source_members=len(inputs),all_source_unchanged=True,no_library_load=True)
 except BaseException as error:answer['first_error']=repr(error)
 finally:
  answer.update(closed=True,wall_s=time.monotonic()-start);put(O/'BUILD_RESULT.json',answer)
 print(json.dumps(answer));return 0 if answer['passed']else 1
if __name__=='__main__':raise SystemExit(main())
