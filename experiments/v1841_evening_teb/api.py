"""C POD layout and metadata only. Numerical calls require a later admission."""
import ctypes as c
class Config(c.Structure):
 _fields_=[('abi',c.c_uint32),('vertices',c.c_uint32)]+[(n,c.c_double)for n in ['forward','backward','omega','acceleration','angular_acceleration','wheelbase','min_turning_radius','obstacle_distance']]+[('footprint',c.c_double*32)]
class Obstacle(c.Structure):
 _fields_=[(n,c.c_double)for n in ['x','y','vx','vy']]+[('dynamic',c.c_uint32)]
class Query(c.Structure):
 _fields_=[(n,c.c_double)for n in ['x','y','yaw','goal_x','goal_y','goal_yaw','vx','vy','omega']]+[('obstacles',c.c_uint32),('data',c.POINTER(Obstacle))]
class Sample(c.Structure):
 _fields_=[(n,c.c_double)for n in ['x','y','yaw','time','vx','vy','omega']]
class Result(c.Structure):
 _fields_=[('status',c.c_int32),('samples',c.c_uint32),('classes',c.c_uint32),('vx',c.c_double),('vy',c.c_double),('omega',c.c_double),('sequence',c.c_uint64)]
def expected():return {0:1,1:c.sizeof(Config),2:c.sizeof(Query),3:c.sizeof(Result),4:c.sizeof(Sample),5:c.sizeof(Obstacle),6:Config.footprint.offset,7:Query.data.offset,8:Result.sequence.offset,20:0,21:0,22:0}
def numeric_entry(*args,**kwargs):raise AssertionError('SOURCE_LOADER_ONLY_NO_NUMERIC_ADMISSION')
