"""Exactly one detached Phase launch; no retry/loop/network."""
import json,subprocess,sys,time
from pathlib import Path
from evidence_rules import dump,read
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/staged_90_then12_20261106';C=Path(__file__).parent
with(ROOT/'LAUNCH_CLAIM.json').open('x')as f:json.dump(dict(claimed_unix=time.time(),attempts=1),f)
assert not(ROOT/'ROUND_WINDOW.json').exists()and read(ROOT/'PREPARED.json')['status']=='FROZEN_AND_ZERO_MODEL_QUALIFIED'
with(ROOT/'campaign.console').open('x')as f:p=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
dump(ROOT/'LAUNCHED.json',dict(pid=p.pid,pilot_deadline_unix=read(ROOT/'PREPARED.json')['stage1_deadline_unix'],attempts=1));print(json.dumps(read(ROOT/'LAUNCHED.json')))
