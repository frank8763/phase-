"""SOFTWARE counter concurrency worker; original bounded counter only."""
import importlib.util
from pathlib import Path
import sys

R=Path(__file__).resolve().parents[2]

def main():
    folder=Path(sys.argv[1]);identity=sys.argv[2];mode=sys.argv[3]
    spec=importlib.util.spec_from_file_location('original_bounded_counter',R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    writer=m.WriterBudget(folder,role='ACTUAL_ROS',maximum_bytes=24*1024**2,source_identity=identity)
    print('READY',flush=True)
    assert sys.stdin.readline().strip()=='GO'
    if mode=='RED':
        original=Path.replace
        def replace(source,target,*args,**kwargs):
            if source==writer.path.with_suffix('.json.pending'):
                print('PENDING',flush=True)
                assert sys.stdin.readline().strip()=='RENAME'
            return original(source,target,*args,**kwargs)
        Path.replace=replace
    print('ATTEMPT',flush=True)
    writer.reserve(folder/'SOFTWARE_REGISTERED_NOT_WRITTEN.json',64)
    print('DONE',flush=True)

if __name__=='__main__':main()
