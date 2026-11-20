import os
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def environment(out):
    ros=load('peer_qualification_ros_environment',R/'experiments/v856_nav2_foundation/ros_environment.py');env=ros.environment();install=R/'runs/v1340_overnight_preparation/install'
    env['AMENT_PREFIX_PATH']=str(install)+':'+env['AMENT_PREFIX_PATH'];env['LD_LIBRARY_PATH']=str(install/'lib')+':'+env['LD_LIBRARY_PATH'];env.update(ROS_DOMAIN_ID='225',ROS_LOG_DIR=str(out/'ros_logs'),CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');env.pop('LD_PRELOAD',None)
    return ros,env
