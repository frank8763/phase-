import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS_RECONNECTION '+name)
sys.meta_path.insert(0,NoModels())
from worker_context import *
import fcntl,signal
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    old=science();now=time.time();configure_owner(O,now+300,dict())
    from reconnect import renew_from_complete_partial
    parent=R/'runs/v858_nav2_verified/v1275/main_slot24';p=read(parent/'ACTUAL_FINAL_PACKET.json');setup=read(parent/'physics/SETUP.json')
    begin=time.monotonic();plan,records=renew_from_complete_partial(setup,p,[-4.,-2.],O)
    dump(O/'TWO_STAGE_SAVED_PLAN.json',plan);dump(O/'TWO_STAGE_FIXED_RECORDS.json',records)
    assert plan['passed'],'NO_TWO_STAGE_SAVED_RECONNECTION'
    print(json.dumps(dict(passed=True,models=0,physical_native=0,wall_s=time.monotonic()-begin,records=records)))
if __name__=='__main__':main()
