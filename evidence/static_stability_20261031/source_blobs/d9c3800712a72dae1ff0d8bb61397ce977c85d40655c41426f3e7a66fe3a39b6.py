import mujoco,json,os
from pathlib import Path
spec=mujoco.MjSpec.from_file('/home/linghu/catkin_ws/src/mk-mini/training/assets/mkmini_real/mkmini_mobile_manipulator_v1.xml')
print('add_sensor',spec.add_sensor.__doc__)
print('sensor types',mujoco.mjtSensor.mjSENS_FRAMEPOS,mujoco.mjtSensor.mjSENS_FRAMEQUAT)
print('geom example',spec.geoms[0].name,spec.geoms[0].id)
