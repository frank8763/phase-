"""Count distinct actually available first commands, no new prediction."""
import hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2];source=repo/'runs/v735_scan_differential_navigation/main01/paired/geometry_memory/control_decisions.jsonl';rows=[json.loads(s)for s in source.read_text().splitlines()];details=[]
assert (repo/'REVIEW_PENDING').exists()
for step in [140,144,148]:
 record=next(x for x in rows if x['step']==step and x['stage']=='NOMINAL'and x['candidate_role']=='BACKUP_RETURN');safe=sorted([x for x in record['candidates']if x['reason']is None],key=lambda c:c['score'],reverse=True);unique=[];seen=set()
 for x in safe:
  key=tuple(x['first_command'])
  if key not in seen:seen.add(key);unique.append(x['first_command'])
 details.append(dict(step=step,safe_target_count=len(safe),distinct_safe_first_commands=len(unique),tested_append_inputs=1,unexamined_distinct_first_commands=len(unique)-1,commands=unique,not_assumed_jointly_feasible=True))
out=dict(status='RETURN_INPUT_CLASSES_EXACTLY_DEDUPLICATED',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),details=details,new_integrations=0)
(repo/'runs/v736_scan_pilot_postmortem/DISTINCT_RETURN_INPUTS.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='details'}))
