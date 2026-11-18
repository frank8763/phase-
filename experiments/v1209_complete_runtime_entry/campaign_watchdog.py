"""Unchanged parent entry, with the separately qualified new namespace."""
from worker_context import *
entry=load('v1209_original_campaign_watchdog',R/'experiments/v1204_goal_audit_worker/campaign_watchdog.py')
if __name__=='__main__':
    result=entry.main()
    sys.exit(0 if result is None else result)
