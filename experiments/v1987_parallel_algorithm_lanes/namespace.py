"""Readonly Phase namespace, only one lane output directory writable."""
from common import R,C,ROOT,LANES,load

def command(lane,script):
 assert lane in LANES
 ros=load('original_Phase_readonly_ros_namespace',R/'experiments/v856_nav2_foundation/ros_environment.py');out=ROOT/'lanes'/lane;cmd=ros.command(['/usr/bin/python3.12','-I','-B','-S',str(script)]);i=cmd.index('--bind');assert cmd[i+1:i+3]==[str(R/'runs'),str(R/'runs')];cmd[i]='--ro-bind';position=cmd.index('--chdir');cmd[position:position]=['--bind',str(out),str(out)]
 env=ros.environment();env.update(PHASE_ALGORITHM_LANE=lane,ROS_DOMAIN_ID='206'if lane=='MPPI'else'207',ROS_LOG_DIR='/tmp/phase_parallel_algorithm_logs',ROS_LOGGING_DISABLE_FILE_LOGGING='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',PHASE_REPO=str(R))
 if lane=='MPPI':
  overlay=R/'runs/v931_deadband_consistent_mppi/install';env.update(AMENT_PREFIX_PATH=str(overlay)+':/opt/ros/jazzy',LD_LIBRARY_PATH=str(overlay/'lib')+':'+env['LD_LIBRARY_PATH'],LD_PRELOAD=str(R/'runs/v1319_mppi_coherent_sampling/libcoherent.so'),PHASE_COHERENT_NOISE='1')
 else:
  env.pop('LD_PRELOAD',None);env.pop('PHASE_COHERENT_NOISE',None)
 return cmd,env
