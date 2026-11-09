"""Compile and run actual production-header regression without vehicle models."""
import json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v931_deadband_consistent_mppi';H=O/'headers';ROOT=R/'runs/v856_nav2_foundation/rootfs/opt/ros/jazzy'
label=sys.argv[1];source=sys.argv[2]if len(sys.argv)>2 else'qualify_deadband.cpp'
includes=[H/'opt/ros/jazzy/include',*[p for p in(H/'opt/ros/jazzy/include').iterdir()if p.is_dir()],H/'usr/include',H/'usr/include/eigen3',Path('/usr/include/opencv4')]
exe=O/(label+'.bin');args=['g++','-std=c++17','-O2',str(C/source),*[v for p in includes for v in['-I',str(p)]],'-L'+str(ROOT/'lib'),'-Wl,--allow-shlib-undefined','-lmppi_controller','-o',str(exe)]
p=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=90);(O/(label+'.compile.console')).write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr[-1500:]
sys.path.insert(0,str(R/'experiments/v856_nav2_foundation'));from ros_environment import command,environment
p=subprocess.run(command([str(exe)]),cwd=R,env=environment(),capture_output=True,text=True,timeout=20);(O/(label+'.console')).write_text(p.stdout+p.stderr);(O/(label+'.RUN.json')).write_text(json.dumps(dict(returncode=p.returncode,command=args,models=0,integrations=0),indent=2)+'\n');print(p.returncode,p.stdout,p.stderr)
if p.returncode==0:(O/(label+'.json')).write_text(p.stdout)
sys.exit(p.returncode)
