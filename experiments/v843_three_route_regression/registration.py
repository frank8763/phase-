"""Auditor applicability only; existing scientific worker and assertions remain frozen."""
import ast
from pathlib import Path
from common import R,C,read
ANCHORS={10060002:'runs/v830_ranked_return_development/main_slot01/paired/geometry_memory',10060008:'runs/v828_goal_dynamic_confirmation/main_slot08/paired/geometry_memory',10010002:'runs/v827_goal_route_validation/repeat_slot02/paired/geometry_memory',10010001:'runs/v827_goal_route_validation/main_slot01/paired/geometry_memory',10010003:'runs/v827_goal_route_validation/main_slot03/paired/geometry_memory'}
def transform(script,source):
 original=source;changes=[]
 def replace(before,after):
  nonlocal source
  assert source.count(before)==1,(script,'REGISTERED_PATCH_NOT_UNIQUE',before)
  source=source.replace(before,after);changes.append((before,after))
 if script=='audit_run.py':replace("event=next(e for e in lines(cell/'early_joint_decisions.jsonl')if e['step']==step)","event=next(e for e in cached_early_lines(cell/'early_joint_decisions.jsonl')if e['step']==step)")
 if script=='audit_complete_joint.py':replace("event=next(x for x in lines(cell/'early_joint_decisions.jsonl')if x['step']==step)","event=next(x for x in cached_early_lines(cell/'early_joint_decisions.jsonl')if x['step']==step)")
 if script=='audit_reactive.py':replace("for row in lines(cell/'control_decisions.jsonl'):","for row in __import__('itertools').chain(lines(cell/'control_decisions.jsonl'),({'stage':'BACKUP_APPEND','detail':probe['detail']}for event in lines(cell/'early_joint_decisions.jsonl')for probe in event['probes'])):")
 if script=='audit_field_preflight.py':replace("registered=read(Path(__file__).parent/'TASK_LIST.json');","registered=read(REGISTERED_TASKS_PATH);")
 if script=='audit_early_joint.py':replace("anchors={10060002:'runs/v830_ranked_return_development/main_slot01/paired/geometry_memory',10060008:'runs/v828_goal_dynamic_confirmation/main_slot08/paired/geometry_memory'}","anchors=REGISTERED_PREFIX_ANCHORS")
 restored=source
 for before,after in reversed(changes):restored=restored.replace(after,before)
 assert restored==original,'UNREGISTERED_AUDITOR_SOURCE_CHANGE'
 assert sum(isinstance(n,ast.Assert)for n in ast.walk(ast.parse(source)))==sum(isinstance(n,ast.Assert)for n in ast.walk(ast.parse(original)))
 return source,changes
def prefix_anchor(seed):
 assert seed in ANCHORS,'UNREGISTERED_PREFIX_TASK'
 return R/ANCHORS[seed]
