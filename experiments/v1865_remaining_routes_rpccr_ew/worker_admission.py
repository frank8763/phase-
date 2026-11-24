"""Pure common-task EW worker authority; no numerical imports or mutations."""
from pathlib import Path

def validate(out,round_root,task,admission,window,freeze_sha256,now,mono,boot):
 out=Path(out);round_root=Path(round_root)
 assert out==round_root/'actual'and Path(task['output'])==out,'EW_WORKER_CURRENT_OUTPUT'
 assert task['task_id']==round_root.name and task['case_id']=='EAST_WEST'and task['common_method']=='RP-CCR'and task['mechanism_variant']=='full','EW_WORKER_ROUTE_AND_METHOD'
 assert admission['scope']=='RPCCR_COMMON_CONDITION_FULL_TASK'and admission['models_authorized']and admission['assignment']==task,'EW_WORKER_CURRENT_AUTHORITY'
 assert admission['source_freeze_sha256']==freeze_sha256,'EW_WORKER_CURRENT_SOURCE'
 assert boot==window['boot_id']and now<window['normal_end_unix']and mono<window['hard_stop_monotonic'],'EW_WORKER_CURRENT_CLOCK'
 return True
