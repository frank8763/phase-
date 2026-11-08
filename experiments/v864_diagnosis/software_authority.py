"""Playback authorizes genuine ROS computation, explicitly forbids vehicle models."""
import json,time
from pathlib import Path
C=Path(__file__).resolve().parent
def authorized(task,receipt,now,freeze_sha):
 assert receipt['software_playback_only']is True and receipt['models_authorized']is False
 assert receipt['source_freeze_sha256']==freeze_sha and receipt['run_id']==task['run_id']
 assert task['scope']=='RECORDED_STATE_SENSOR_PLAYBACK_NO_VEHICLE'and receipt['started_unix']<=now<receipt['deadline_unix']
 return receipt['deadline_unix']
