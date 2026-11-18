"""Unchanged parent entry, with the separately qualified new namespace."""
from worker_context import *
entry=load('v1218_original_native_audit_cli',R/'experiments/v1204_goal_audit_worker/native_audit_cli.py')
if __name__=='__main__':
    result=entry.main()
    sys.exit(0 if result is None else result)
