"""New explicit component-only authority; no inherited or renewable deadline."""
import hashlib
import json
import math
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; CODE=Path(__file__).parent
OUT=ROOT/'runs/v950_steering_response'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def authorized(now=None):
    now=time.time()if now is None else now
    auth=json.loads((OUT/'AUTHORIZATION.json').read_text())
    assert auth['models_authorized']is True and auth['scope']=='18_FIXED_RESPONSES_THEN_ONE_HANDOFF_ONLY','WRONG_COMPONENT_AUTHORITY'
    assert auth['source_freeze_sha256']==sha(CODE/'SOURCE_FREEZE.json'),'SOURCE_AUTHORITY_CHANGED'
    assert auth['user_approval_sha256']==sha(OUT/'USER_WINDOW_APPROVAL.json'),'USER_APPROVAL_CHANGED'
    start=auth['started_unix'];end=auth['deadline_unix']
    assert math.isfinite(start)and math.isfinite(end)and abs(end-start-5400.)<1e-6,'WINDOW_RESET_OR_WRONG_DURATION'
    assert start<=now<end-20,'COMPONENT_WINDOW_EXPIRED'
    for rel,expected in json.loads((CODE/'SOURCE_FREEZE.json').read_text())['files'].items():
        path=ROOT/rel
        assert path.resolve().is_relative_to(ROOT)and path.is_file()and sha(path)==expected,'FROZEN_SOURCE_CHANGED '+rel
    return auth
