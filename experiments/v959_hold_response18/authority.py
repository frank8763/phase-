"""One nonrenewable component window. No authority after close or source changes."""
import hashlib
import json
import math
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent
OUT=ROOT/'runs/v959_hold_response18'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def authorized(now=None):
    now=time.time()if now is None else now
    assert not(OUT/'COMPLETION.json').exists(),'BATCH_ALREADY_CLOSED'
    auth=json.loads((OUT/'AUTHORIZATION.json').read_text())
    assert auth['models_authorized']is True and auth['scope']=='V959_ORIGINAL18_HOLD_RESPONSE_ONLY'
    assert math.isfinite(auth['deadline_unix'])and abs(auth['deadline_unix']-auth['started_unix']-5400.)<1e-6
    assert auth['started_unix']<=now<auth['deadline_unix']-20,'WINDOW_EXPIRED'
    assert sha(CODE/'SOURCE_FREEZE.json')==auth['source_freeze_sha256']
    assert sha(OUT/'USER_INSTRUCTION.json')==auth['user_instruction_sha256']
    for relative,expected in json.loads((CODE/'SOURCE_FREEZE.json').read_text())['files'].items():
        p=ROOT/relative;assert p.resolve().is_relative_to(ROOT)and p.is_file()and sha(p)==expected,'FROZEN_SOURCE_CHANGED '+relative
    return auth
