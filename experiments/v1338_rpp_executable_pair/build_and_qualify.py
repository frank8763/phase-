"""Build fresh plugin and test production math; no physical imports."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1338_rpp_executable_pair'


def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')


def main():
    os.sched_setaffinity(0,{2,3,4,5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    O.mkdir(exist_ok=True);install=O/'install';(install/'lib').mkdir(parents=True,exist_ok=True)
    rows=json.loads((R/'runs/v858_nav2_verified/v1337/rpp_main/ROS_COMMANDS.json').read_text())
    spec=importlib.util.spec_from_file_location('real_unchanged_boundary',R/'experiments/v1288_baseline_interface/contract.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    rejected=[]
    for i,row in enumerate(rows):
        try:module.twist(row['v'],row['w'])
        except ValueError as error:rejected.append(dict(index=i,error=str(error),v=row['v'],w=row['w']))
    assert len(rejected)==1 and rejected[0]['index']==len(rows)-1
    payload=''.join(f"{row['v']:.17g} {row['w']:.17g}\n" for row in rows)
    q=O/'qualify_pair'
    subprocess.run(['g++','-std=c++17','-O2',str(C/'qualify_pair.cpp'),'-o',str(q)],cwd=R,check=True,timeout=30)
    test=subprocess.run([str(q)],input=payload,capture_output=True,text=True,check=True,timeout=15)
    proof=json.loads(test.stdout);assert proof['saved_rows']==898 and proof['changed_rows']==1
    row=rows[-1];projected_w=max(-abs(row['v'])/1.32,min(abs(row['v'])/1.32,row['w']))
    module.twist(row['v'],projected_w)
    proof.update(original_real_boundary_rejection=rejected,projected_rejected_pair=[row['v'],projected_w],angular_change=abs(projected_w-row['w']),old_legal897_rows_identity=True,models=0,physical_native=0)
    dump(O/'PAIR_QUALIFICATION.json',proof)
    h=O/'headers';root=R/'runs/v856_nav2_foundation/rootfs/opt/ros/jazzy'
    inc=[root/'include',h/'opt/ros/jazzy/include',*[p for p in (h/'opt/ros/jazzy/include').iterdir() if p.is_dir()],h/'usr/include',h/'usr/include/eigen3',Path('/usr/include/opencv4')]
    args=['g++','-std=c++17','-fPIC','-shared','-O2',str(C/'executable_rpp.cpp'),*[v for p in inc for v in ['-I',str(p)]],'-L'+str(root/'lib'),'-lnav2_regulated_pure_pursuit_controller','-o',str(install/'lib/libphase_executable_rpp.so')]
    build=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=90)
    (O/'compile.console').write_text(build.stdout+build.stderr);dump(O/'BUILD_RESULT.json',dict(passed=build.returncode==0,command=args,models=0,physical_native=0))
    assert build.returncode==0,build.stderr[-1800:]
    index=install/'share/ament_index/resource_index';(index/'packages').mkdir(parents=True,exist_ok=True);(index/'nav2_core__pluginlib__plugin').mkdir(parents=True,exist_ok=True)
    (index/'packages/phase_executable_rpp').write_text('');(index/'nav2_core__pluginlib__plugin/phase_executable_rpp').write_text('share/phase_executable_rpp/plugin.xml')
    share=install/'share/phase_executable_rpp';share.mkdir(exist_ok=True)
    (share/'plugin.xml').write_text('<class_libraries><library path="phase_executable_rpp"><class name="phase_rpp/ExecutableRPP" type="phase_rpp::ExecutableRPP" base_class_type="nav2_core::Controller"><description>Upstream RPP plus executable paired projection and postprojection collision recheck.</description></class></library></class_libraries>\n')
    (share/'package.xml').write_text('<package format="3"><name>phase_executable_rpp</name><version>0.1.0</version><description>Engineering vehicle RPP adaptation</description><maintainer email="phase@example.invalid">Phase</maintainer><license>Apache-2.0</license></package>\n')
    print(json.dumps(dict(pair_qualification_passed=True,saved_rows=898,changed=1,random_pairs=100000,plugin_built=True,models=0,physical_native=0)))


if __name__=='__main__':main()
