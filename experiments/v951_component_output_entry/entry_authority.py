"""Explicit one-time metadata exception, same original absolute deadline."""
import hashlib
import json
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent
OUT=ROOT/'runs/v951_component_output_entry'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def authorized(now=None):
    now=time.time()if now is None else now
    auth=json.loads((OUT/'AUTHORIZATION.json').read_text())
    assert auth['models_authorized']is True and auth['one_output_exception']is True,'NO_ENTRY_EXCEPTION_AUTHORITY'
    assert auth['source_freeze_sha256']==sha(CODE/'SOURCE_FREEZE.json'),'ENTRY_SOURCE_CHANGED'
    assert auth['entry_approval_sha256']==sha(OUT/'USER_ENTRY_APPROVAL.json'),'ENTRY_APPROVAL_CHANGED'
    old=json.loads((ROOT/'runs/v950_steering_response/AUTHORIZATION.original.json').read_text())
    assert auth['started_unix']==old['started_unix']and auth['deadline_unix']==old['deadline_unix'],'ORIGINAL_DEADLINE_CHANGED'
    assert auth['started_unix']<=now<auth['deadline_unix']-20,'ORIGINAL_COMPONENT_DEADLINE_EXPIRED'
    for relative,expected in json.loads((CODE/'SOURCE_FREEZE.json').read_text())['files'].items():
        p=ROOT/relative;assert p.is_file()and sha(p)==expected,'FROZEN_SOURCE_CHANGED '+relative
    return auth
