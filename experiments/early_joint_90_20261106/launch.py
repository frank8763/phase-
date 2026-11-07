"""One detached offline campaign launch; refuses all existing claims."""
import json,os,subprocess,sys,time
from pathlib import Path
from evidence_rules import dump,read
repo=Path(__file__).resolve().parents[2];root=repo/'runs/early_joint_90_20261106';claim=root/'LAUNCH_CLAIM.json'
with claim.open('x')as f:json.dump(dict(claimed_unix=time.time(),attempts=1),f)
assert not(root/'ROUND_WINDOW.json').exists()and read(root/'PREPARED.json')['status']=='ONE_CANDIDATE_FROZEN_AND_ZERO_MODEL_QUALIFIED'
with(root/'campaign.console').open('x')as stream:p=subprocess.Popen([sys.executable,'-B',str(Path(__file__).parent/'campaign.py')],cwd=repo,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
dump(root/'LAUNCHED.json',dict(pid=p.pid,absolute_deadline_unix=read(root/'PREPARED.json')['absolute_deadline_unix'],attempts=1));print(json.dumps(read(root/'LAUNCHED.json')))
