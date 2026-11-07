"""Phase-only rootless ROS2 namespace using verified extracted binary dependencies."""
import os
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OUT=R/'runs/v856_nav2_foundation';ROOTFS=OUT/'rootfs'

def environment():
    prefix='/opt/ros/jazzy';libdirs=[prefix+'/lib',prefix+'/lib/x86_64-linux-gnu',str(ROOTFS/'usr/lib/x86_64-linux-gnu'),str(ROOTFS/'usr/lib'),str(ROOTFS/'lib/x86_64-linux-gnu'),str(ROOTFS/'usr/lib/x86_64-linux-gnu/blas'),str(ROOTFS/'usr/lib/x86_64-linux-gnu/lapack')]
    env=dict(os.environ,AMENT_PREFIX_PATH=prefix,CMAKE_PREFIX_PATH=prefix,LD_LIBRARY_PATH=':'.join(libdirs),PYTHONPATH=':'.join([prefix+'/lib/python3.12/site-packages',prefix+'/local/lib/python3.12/dist-packages',str(ROOTFS/'usr/lib/python3/dist-packages')]),PATH=prefix+'/bin:/usr/bin:/bin',ROS_DISTRO='jazzy',ROS_VERSION='2',ROS_PYTHON_VERSION='3',ROS_DOMAIN_ID='156',ROS_LOCALHOST_ONLY='1',RMW_IMPLEMENTATION='rmw_fastrtps_cpp',RCUTILS_LOGGING_BUFFERED_STREAM='1',ROS_LOG_DIR=str(OUT/'ros_logs'),PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    return env

def command(args):
    # Standalone qualification hides all /home except this Phase repository.
    return ['bwrap','--die-with-parent','--new-session','--unshare-all','--ro-bind','/','/','--tmpfs','/home','--tmpfs','/tmp','--dev','/dev','--proc','/proc','--ro-bind',str(R),str(R),'--bind',str(R/'runs'),str(R/'runs'),'--ro-bind',str(ROOTFS/'opt'),'/opt','--setenv','HOME','/tmp','--chdir',str(R),*args]
