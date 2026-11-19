"""Original terminal failure via the actual unchanged V1364 shared object."""
import os
from common import *


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));O.mkdir(exist_ok=True)
    target=O/'ORIGINAL_REPRODUCTION.json';assert not target.exists()
    lib=R/'runs/v1364_space_time_vehicle/libinterval_kinodynamic.so'
    result=call(lib,'plan_interval_kinodynamic')
    assert result['code']==1 and result['path'] is None and result['stats'][0]<=22000
    result.update(reproduced=True,library_sha256=sha(lib),models=0,physical_native=0)
    dump(target,result);print(json.dumps(result))


if __name__=='__main__':main()
