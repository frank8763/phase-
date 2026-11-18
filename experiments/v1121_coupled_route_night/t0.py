"""Same route-aware canonical t0, with new frozen worker/task authority."""
import sys,runpy
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C));import worker
if __name__=='__main__':runpy.run_path(str(C.parents[0]/'v1089_route_scene_contract/t0.py'),run_name='__main__')
