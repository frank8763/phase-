"""Frozen branch dependency and failure accounting; data only."""
PHYSICAL_EXCLUSIONS={'component_functional','independent_whole_goal','independent_forward_progress','dynamic_actual_actor_return','dynamic_after_detection_travel_ge1m'}


def classify(row):
    native=row.get('native') or {};ros=row.get('ros') or {};audit=row.get('audit') or {}
    if 'NATIVE_SAFETY_ANOMALY' in native.get('error',''):
        return 'SAFETY_CONTROL_OR_EVIDENCE_STOP'
    if not native.get('closed') or not ros or not audit.get('checks'):
        return 'EVIDENCE_OR_OPERATION_STOP'
    if native.get('error') or ros.get('error') or not native.get('source_unchanged'):
        return 'CONTROL_SOURCE_OR_OPERATION_STOP'
    if not ros.get('public_static_map_receipt',{}).get('passed'):
        return 'EVIDENCE_OR_OPERATION_STOP'
    if not all(v for k,v in audit['checks'].items() if k not in PHYSICAL_EXCLUSIONS):
        return 'SAFETY_CONTROL_OR_EVIDENCE_STOP'
    if native.get('passed') and ros.get('passed') and audit.get('passed'):
        return 'PASSED'
    return 'FUNCTIONAL_FAILURE_SAFE_COMPLETE'


def eligible(task,completed):
    assert task['stage']=='dynamic'
    return task['role']!='repeat' or completed.get((task['branch'],'dynamic','main'))=='PASSED'
