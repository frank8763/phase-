"""Original CPU/static or dynamic canonical factory and exact control replay."""
from afternoon_tools import R,load
original=load('afternoon_canonical_cpu_physical',R/'experiments/v1114_coupled_steering_mode/physical.py')
create=original.create
replay=original.replay
