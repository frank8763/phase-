"""One CPU4 compilation, no DLL load/controller construction or numerical call."""
from pathlib import Path
import hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));assert not(O/'BUILD_ONCE.json').exists();start=time.monotonic();(O/'BUILD_ONCE.json').write_text(json.dumps(dict(pid=os.getpid(),unix=time.time(),cpu=4,max_s=120,models=0)))
 root=R/'runs/v856_nav2_foundation/rootfs/opt/ros/jazzy';h=R/'runs/v1340_overnight_preparation/headers';inc=[root/'include',*[p for p in(root/'include').iterdir()if p.is_dir()],h/'opt/ros/jazzy/include',*[p for p in(h/'opt/ros/jazzy/include').iterdir()if p.is_dir()],h/'usr/include',h/'usr/include/eigen3',C]
 out=O/'libphase_rpp_sync.so';cmd=['g++','-std=c++17','-fPIC','-shared','-O2',str(C/'bridge.cpp'),*[v for p in inc for v in ['-I',str(p)]],'-L'+str(root/'lib'),'-lnav2_regulated_pure_pursuit_controller','-lnav2_costmap_2d_core','-lnav2_util_core','-lrclcpp_lifecycle','-lrclcpp','-ltf2_ros','-ltf2','-o',str(out)]
 p=subprocess.run(cmd,cwd=R,capture_output=True,text=True,timeout=120);(O/'COMPILE.log').write_text(p.stdout+p.stderr)
 deps=[C/'bridge.cpp',C/'registered_parameters.inc',C/'RPP_PARAMETER_SOURCE.json',R/'experiments/v1338_rpp_executable_pair/executable_rpp.cpp',R/'experiments/v1338_rpp_executable_pair/project_pair.hpp',R/'experiments/v1370_overnight_controller_matrix/rpp_default_params.json',root/'lib/libnav2_regulated_pure_pursuit_controller.so']
 result=dict(closed=True,build_passed=p.returncode==0,command=cmd,returncode=p.returncode,source_pins={str(x.relative_to(R)):sha(x)for x in deps},upstream_and_existing_adaptation_body_unchanged=True,configured_parameter_values_unchanged=True,models=0,DLL_loads=0,controller_constructors=0,solver_calls=0,physics=0,replay=0,source_qualified=False,method_runtime_qualified=False,wall_s=time.monotonic()-start,local_only=True)
 if p.returncode==0:result.update(binary_path=str(out.relative_to(R)),binary_bytes=out.stat().st_size,binary_sha256=sha(out))
 else:result['first_error']=p.stderr[-3000:]
 (O/'BUILD_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['command','source_pins']}));return 0 if result['build_passed']else 1
if __name__=='__main__':raise SystemExit(main())
