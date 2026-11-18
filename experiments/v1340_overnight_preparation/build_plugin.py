"""Build exactly prepared V1338 source using restored pinned ABI headers."""
import json
import os
from pathlib import Path
import subprocess
import hashlib

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1340_overnight_preparation'


def main():
    os.sched_setaffinity(0,{2,3,4,5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    source=R/'experiments/v1338_rpp_executable_pair';install=O/'install';(install/'lib').mkdir(parents=True,exist_ok=True)
    h=O/'headers';root=R/'runs/v856_nav2_foundation/rootfs/opt/ros/jazzy'
    includes=[root/'include',h/'opt/ros/jazzy/include',*[p for p in (h/'opt/ros/jazzy/include').iterdir() if p.is_dir()],h/'usr/include',h/'usr/include/eigen3']
    args=['g++','-std=c++17','-fPIC','-shared','-O2',str(source/'executable_rpp.cpp'),*[a for p in includes for a in ['-I',str(p)]],'-L'+str(root/'lib'),'-lnav2_regulated_pure_pursuit_controller','-o',str(install/'lib/libphase_executable_rpp.so')]
    result=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=90)
    previous=len(list(O.glob('compile*.console')));(O/('compile%02d.console'%previous)).write_text(result.stdout+result.stderr)
    proof=dict(passed=result.returncode==0,command=args,source_sha256=hashlib.sha256((source/'executable_rpp.cpp').read_bytes()).hexdigest(),models=0,physical_native=0)
    (O/('BUILD_RESULT%02d.json'%previous)).write_text(json.dumps(proof,indent=2)+'\n')
    assert result.returncode==0,result.stderr[-2400:]
    index=install/'share/ament_index/resource_index';(index/'packages').mkdir(parents=True,exist_ok=True);(index/'nav2_core__pluginlib__plugin').mkdir(parents=True,exist_ok=True)
    (index/'packages/phase_executable_rpp').write_text('');(index/'nav2_core__pluginlib__plugin/phase_executable_rpp').write_text('share/phase_executable_rpp/plugin.xml')
    share=install/'share/phase_executable_rpp';share.mkdir(exist_ok=True)
    (share/'plugin.xml').write_text('<class_libraries><library path="phase_executable_rpp"><class name="phase_rpp/ExecutableRPP" type="phase_rpp::ExecutableRPP" base_class_type="nav2_core::Controller"><description>Upstream RPP with paired executable projection and post-projection collision validation.</description></class></library></class_libraries>\n')
    (share/'package.xml').write_text('<package format="3"><name>phase_executable_rpp</name><version>0.1.0</version><description>Engineering vehicle RPP adaptation</description><maintainer email="phase@example.invalid">Phase</maintainer><license>Apache-2.0</license></package>\n')
    print(json.dumps(dict(passed=True,plugin_sha256=hashlib.sha256((install/'lib/libphase_executable_rpp.so').read_bytes()).hexdigest(),models=0,physical_native=0)))


if __name__=='__main__':main()
