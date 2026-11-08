"""One same-source cold-start software retry; only output directory changes, no vehicle/model."""
import json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(C))
sys.argv=[str(C/"planner_qual.py"),"margin01"]
import planner_qual
O=R/'runs/v866_margin_qualification'
old=json.loads((O/'margin01/PLAYBACK_COMPLETION.json').read_text());assert old['closed']and old['model_integrations']==0 and old['ros_returncode']==1
assert json.loads((O/'margin01/ROS_RESULT.json').read_text())['error']=="TimeoutError('MANAGER_STARTUP_TIMEOUT')"
assert time.time()<json.loads((O/'SOFTWARE_WINDOW.json').read_text())['deadline_unix']-80
planner_qual.O=O/'margin02';sys.argv=[str(C/'planner_qual.py'),'margin01'];planner_qual.main()
