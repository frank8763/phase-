"""Bounded model-free ROS namespace; preserve source/input fingerprints and errors."""
import fcntl
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODE = Path(__file__).parent
OUT = ROOT/'runs/v939_rpccr_rpp_handoff'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert json.loads((ROOT/'runs/v938_rpccr_recovery_segments/QUALIFICATION.json').read_text())['passed']
OUT.mkdir(exist_ok=False)
files = sorted(CODE.glob('*.py'))+[CODE/'PROTOCOL.md']
files += sorted((ROOT/'experiments/v938_rpccr_recovery_segments').glob('*.py'))
files += [ROOT/'runs/v938_rpccr_recovery_segments/CORRIDORS.json',
          ROOT/'experiments/v934_rpccr_certified_recovery/A_motion.yaml',
          ROOT/'runs/v884_feasible_rpp/install/lib/libphase_feasible_rpp.so',
          ROOT/'runs/v936_rpccr_corridor_search/ENTRY_QUALIFICATION.json']
frozen = {str(p.relative_to(ROOT)): sha(p) for p in files}
(OUT/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files=frozen, at=time.time(), models=0, integrations=0), indent=2)+'\n')
guard = (ROOT/'REVIEW_PENDING').read_bytes()
lock = (ROOT/'runs/v648_static_unknown/execution.lock').open('a+')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
sys.path.insert(0, str(ROOT/'experiments/v856_nav2_foundation'))
from ros_environment import command, environment
env = environment()
env['AMENT_PREFIX_PATH'] = str(ROOT/'runs/v884_feasible_rpp/install')+':'+env['AMENT_PREFIX_PATH']
env['ROS_LOG_DIR'] = str(OUT/'ros_logs')
with (OUT/'probe.console').open('w') as console:
    result = subprocess.run(command(['/usr/bin/python3.12', str(CODE/'probe.py')]),
                            cwd=ROOT, env=env, stdout=console, stderr=subprocess.STDOUT, timeout=100.)
verified = all(sha(ROOT/p)==expected for p,expected in frozen.items())
receipt = dict(returncode=result.returncode, unchanged_sources=verified,
               guard_unchanged=(ROOT/'REVIEW_PENDING').read_bytes()==guard,
               models=0, integrations=0, physical_authorized=False)
(OUT/'EXECUTION_RECEIPT.json').write_text(json.dumps(receipt, indent=2)+'\n')
assert result.returncode==0 and verified and receipt['guard_unchanged']
