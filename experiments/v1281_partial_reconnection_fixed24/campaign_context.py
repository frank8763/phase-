"""Operational aliases only; scientific imports retain their private binding."""
from worker_context import *
old=science();q=old.q;np=q.np;previous=old.previous;packet=old.packet;pin=old.pin;GUARD=old.GUARD
import chain as bridge
RESOURCE=old.RESOURCE
# Use same complete V1217 source closure; all local operations also frozen.
def source_ok():
    return all(sha(R/n)==h for n,h in read(C/'SOURCE_FREEZE.json')['files'].items())
