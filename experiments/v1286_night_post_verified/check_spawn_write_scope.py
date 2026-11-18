"""Exercise real IPC under the evidence write guard, without science imports."""
from pathlib import Path
import concurrent.futures,importlib.util,json,multiprocessing,sys,time
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
def main(path):
    sys.path.insert(0,str(path.parent));import night_math
    sys.addaudithook(night_math.write_scope)
    job=dict(slot=17,cpu=2,label='serial_17',deadline=time.monotonic()+60)
    with concurrent.futures.ProcessPoolExecutor(max_workers=1,mp_context=multiprocessing.get_context('spawn'))as p:
        answer=p.submit(night_math.metadata_boundary_job,job).result(timeout=20)
    print(json.dumps(answer))
if __name__=='__main__':main(Path(sys.argv[1]))
