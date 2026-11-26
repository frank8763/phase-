from pathlib import Path
import hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 os.sched_setaffinity(0,{6});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));assert not(O/'BUILD_ONCE.json').exists();(O/'BUILD_ONCE.json').write_text(json.dumps(dict(unix=time.time(),CPU=6,models=0)))
 start=time.monotonic();inc=R/'runs/v1340_overnight_preparation/headers/usr/include';binary=O/'libphase_mppi_rng.so';unit=O/'standalone';commands=[['g++','-std=c++17','-O2','-shared','-fPIC','-I'+str(inc),str(C/'rng.cpp'),'-ldl','-o',str(binary)],['g++','-std=c++17','-O2','-I'+str(inc),str(C/'standalone.cpp'),'-o',str(unit)]]
 logs=[]
 for cmd in commands:
  p=subprocess.run(cmd,cwd=R,capture_output=True,text=True,timeout=90);logs.append(p.stdout+p.stderr);assert p.returncode==0,p.stderr[-4000:]
 p=subprocess.run([str(unit)],cwd=R,capture_output=True,text=True,timeout=15);assert p.returncode==0;p=json.loads(p.stdout)
 (O/'COMPILE.log').write_text('\n'.join(logs));proof=dict(passed=True,binary_path=str(binary.relative_to(R)),binary_sha256=sha(binary),binary_bytes=binary.stat().st_size,standalone=p,algorithm_DLLs=0,constructors=0,optimizer_calls=0,models=0,physical_native=0,replay_native=0,actual_plugin_engine_binding_not_yet_executed=True,wall_s=time.monotonic()-start,source_pins={str(q.relative_to(R)):sha(q)for q in [C/'rng.cpp',C/'standalone.cpp',inc/'xtensor/xrandom.hpp',O/'RNG_SCHEDULE_LOCKED.json']})
 (O/'BUILD_RESULT.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
