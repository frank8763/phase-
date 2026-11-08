"""Rootless headers from exactly recorded Debian packages; no host/old runtime changes."""
import concurrent.futures,hashlib,io,json,os,subprocess,tarfile,time,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v884_feasible_rpp';ROOT=R/'runs/v856_nav2_foundation/rootfs/opt/ros/jazzy'
PACKAGES='rclcpp rclcpp-lifecycle rclcpp-action rclcpp-components nav2-core nav2-costmap-2d nav2-util nav2-voxel-grid nav2-msgs nav2-common nav-msgs geometry-msgs std-msgs sensor-msgs visualization-msgs builtin-interfaces unique-identifier-msgs action-msgs actionlib-msgs lifecycle-msgs service-msgs std-srvs map-msgs tf2 tf2-ros tf2-geometry-msgs tf2-msgs tf2-sensor-msgs angles pluginlib class-loader rcpputils rcutils rcl rcl-lifecycle rcl-action rcl-interfaces rmw rosidl-runtime-c rosidl-runtime-cpp rosidl-typesupport-interface rosidl-typesupport-c rosidl-typesupport-cpp rosidl-typesupport-introspection-c rosidl-typesupport-introspection-cpp tracetools statistics-msgs rcl-logging-interface rcl-yaml-param-parser ament-index-cpp rmw-dds-common bond bondcpp type-description-interfaces'.split()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    estimates=json.loads((R/'records/nav2_v856_20261107/DEPENDENCY_ESTIMATE.json').read_text())['packages_to_fetch'];digests=json.loads((R/'records/nav2_v856_20261107/PACKAGE_SHA256.json').read_text());by_name={x['filename'].split('_')[0]:x for x in estimates};headers=O/'headers';headers.mkdir(exist_ok=True);downloads=O/'debs';downloads.mkdir(exist_ok=True)
    previous=json.loads((O/'HEADER_PROVENANCE.json').read_text())['packages']if(O/'HEADER_PROVENANCE.json').exists()else[];done={x['package']for x in previous}
    names=set('ros-jazzy-'+name for name in [*PACKAGES,'libstatistics-collector','message-filters','tf2-bullet','tf2-eigen','behaviortree-cpp','behaviortree-cpp-v3','smclib']);names.update(n for n in by_name if n.startswith('ros-jazzy-rosidl-'))
    selected=[by_name[name]for name in sorted(names)if name in by_name and by_name[name]['filename']not in done];records=list(previous)
    def fetch(row):
        target=downloads/row['filename'];expected=digests[row['filename']]
        if not target.exists():
            with urllib.request.urlopen(row['url'],timeout=25)as response:target.write_bytes(response.read())
        assert sha(target)==expected and target.stat().st_size==row['download_bytes'];return row,target,expected
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        for row,p,h in pool.map(fetch,selected):
            proc=subprocess.Popen(['dpkg-deb','--fsys-tarfile',str(p)],stdout=subprocess.PIPE);count=0
            with tarfile.open(fileobj=proc.stdout,mode='r|')as tf:
                for member in tf:
                    name=Path(member.name);parts=name.parts
                    if not member.isfile()or'..'in parts or name.is_absolute()or not str(name).startswith('opt/ros/jazzy/include/'):continue
                    target=headers/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(tf.extractfile(member).read());count+=1
            assert proc.wait(timeout=15)==0;records.append(dict(package=row['filename'],url=row['url'],sha256=h,header_files=count));p.unlink()
    (O/'HEADER_PROVENANCE.json').write_text(json.dumps(dict(passed=True,packages=records,all_exact_old_package_sha_verified=True,host_and_existing_runtime_unchanged=True,models=0),indent=2)+'\n')
    # Additional exact Ubuntu development headers are isolated in this build root too.
    ubuntu=json.loads((C/'UBUNTU_HEADER_LOCK.json').read_text())
    for row in ubuntu['packages']:
        # Skip an already verified extraction; a clean build downloads only the pinned DEB.
        marker=headers/('.ubuntu-'+row['package'])
        if marker.exists():continue
        target=downloads/(row['package']+'.deb')
        with urllib.request.urlopen(row['url'],timeout=25)as response:target.write_bytes(response.read())
        assert sha(target)==row['sha256']
        proc=subprocess.Popen(['dpkg-deb','--fsys-tarfile',str(target)],stdout=subprocess.PIPE)
        with tarfile.open(fileobj=proc.stdout,mode='r|')as tf:
            for member in tf:
                name=Path(member.name)
                if member.isfile()and not name.is_absolute()and '..'not in name.parts and str(name).startswith('usr/include/'):
                    path=headers/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(tf.extractfile(member).read())
        assert proc.wait(timeout=15)==0;target.unlink();marker.write_text(row['sha256']+'\n')
    (O/'UBUNTU_HEADER_PROVENANCE.json').write_text(json.dumps(ubuntu,indent=2)+'\n')
    install=O/'install';(install/'lib').mkdir(parents=True,exist_ok=True);includes=[ROOT/'include',headers/'opt/ros/jazzy/include'];includes += [p for p in (headers/'opt/ros/jazzy/include').iterdir()if p.is_dir()];args=['g++','-std=c++17','-fPIC','-shared','-O2',str(C/'feasible_rpp.cpp'),*[v for p in includes for v in ['-I',str(p)]],'-I'+str(headers/'usr/include'),'-I'+str(headers/'usr/include/eigen3'),'-I/usr/include/opencv4','-L'+str(ROOT/'lib'),'-lnav2_regulated_pure_pursuit_controller','-o',str(install/'lib/libphase_feasible_rpp.so')]
    attempt=2
    while(O/f'compile{attempt:02d}.console').exists():attempt+=1
    result=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=45);(O/f'compile{attempt:02d}.console').write_text(result.stdout+result.stderr)
    status=dict(passed=result.returncode==0,returncode=result.returncode,models=0,integrations=0,host_runtime_not_modified=True,source_sha256=sha(C/'feasible_rpp.cpp'),headers_bytes=sum(p.stat().st_size for p in headers.rglob('*')if p.is_file()))
    if result.returncode==0:
        share=install/'share';idx=share/'ament_index/resource_index';(idx/'packages').mkdir(parents=True,exist_ok=True);(idx/'nav2_core__pluginlib__plugin').mkdir(parents=True,exist_ok=True);(idx/'packages/phase_feasible_rpp').write_text('');(idx/'nav2_core__pluginlib__plugin/phase_feasible_rpp').write_text('share/phase_feasible_rpp/plugin.xml');(share/'phase_feasible_rpp').mkdir(exist_ok=True);(share/'phase_feasible_rpp/plugin.xml').write_text('<class_libraries><library path="phase_feasible_rpp"><class name="phase_feasible_rpp/FeasibleRPP" type="phase_feasible_rpp::FeasibleRPP" base_class_type="nav2_core::Controller"><description>Upstream1.3.13 RPP feasible native curvature before original collision check.</description></class></library></class_libraries>\n');(share/'phase_feasible_rpp/package.xml').write_bytes((C/'package.xml').read_bytes());status['plugin_sha256']=sha(install/'lib/libphase_feasible_rpp.so')
    (O/'BUILD_RESULT.json').write_text(json.dumps(status,indent=2)+'\n');print(json.dumps(status),flush=True);print(result.stderr[-2000:],flush=True)
if __name__=='__main__':main()
