"""Safe functional failures advance the frozen matrix; evidence faults stop it."""
FUNCTIONAL={
 'component_functional','component_goal','reverse_progress','independent_whole_goal',
 'independent_forward_progress','dynamic_actual_actor_return','dynamic_after_detection_travel_ge1m'}

def classify(row):
    native=row.get('native') or {};ros=row.get('ros') or {};audit=row.get('audit') or {}
    if not native.get('closed') or not ros.get('closed') or not audit.get('checks'):return 'EVIDENCE_OR_OPERATION_STOP'
    if native.get('error') or ros.get('error') or not native.get('source_unchanged'):return 'CONTROL_SOURCE_OR_OPERATION_STOP'
    if not ros.get('public_static_map_receipt',{}).get('passed'):return 'EVIDENCE_OR_OPERATION_STOP'
    if native.get('new_actual_native') is None or native.get('own_replay_native') is None:return 'UNKNOWN_PHYSICAL_COUNT_STOP'
    if not all(value for name,value in audit['checks'].items() if name not in FUNCTIONAL):return 'SAFETY_CONTROL_OR_EVIDENCE_STOP'
    if native['passed'] and ros['passed'] and audit['passed']:return 'PASSED'
    return 'FUNCTIONAL_FAILURE_SAFE_COMPLETE'

def eligible(task,completed):return all(completed.get(name)=='PASSED' for name in task['depends_on'])
