"""Exact prospective namespace and original task binding transformation."""
from pathlib import Path
import ast
VERSIONS={'RPP':'v2046_rpp_remaining_three','MPPI':'v2047_mppi_remaining_ten'}
PARENTS={'RPP':'v2038_rpp09_reserved_census','MPPI':'v2042_mppi_core_preload_exact_proof'}
IDS={'RPP':[f'common_{i:02d}__RPP'for i in range(10,13)],'MPPI':[f'common_{i:02d}__MPPI'for i in range(3,13)]}
def transform(text,name,method):
 old=PARENTS[method];new=VERSIONS[method];text=text.replace(old,new)
 if name=='reserved_census.py':return None
 for k in ['SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','POST_SOURCE_STORAGE_BARRIER.json']:text=text.replace("O/'"+k+"'","SOURCE/'"+k+"'")
 # Source authority is shared; each case output remains independently selected.
 for n in ['v2037_parallel_reserved_source','v2042_mppi_core_preload_exact_proof']:text=text.replace("SOURCE=R/'runs/"+n+"'","SOURCE=R/'runs/v2045_remaining_parallel_source'")
 if 'from context import 'in text:text=text.replace('from context import ','from context import SOURCE,',1)if 'from context import SOURCE,'not in text else text
 declare="R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;SOURCE=R/'runs/v2045_remaining_parallel_source';RID=os.environ.get('PHASE_COMMON_ASSIGNMENT',"+repr(IDS[method][0])+");assert RID in "+repr(IDS[method])+";O=SOURCE/'rounds'/RID"
 if name=='context.py':
  a=text.index('R=Path(');b=text.index('\ndef read(',a);text=text[:a]+declare+";OLD=R/'experiments/v1281_partial_reconnection_fixed24'"+text[b:]
  prior='common_09'if method=='RPP'else'common_02';text=text.replace("task['common_task_id']=='"+prior+"'","task['task_id']==RID and task['common_task_id']==RID.split('__')[0]")
 elif name=='run_phase.py':
  a=text.index('R=Path(');b=text.index('\ndef read(',a);text=text[:a]+declare+text[b:]
 elif name=='pilot_entry.py':
  a=text.index('R=Path(');b=text.index('assert (O/',a);text=text[:a]+declare+'\n'+text[b:]
 elif name=='owner.py':
  prior='common_09'if method=='RPP'else'common_02';text=text.replace("x['task']['task_id']=='"+prior+"'","x['task']['task_id']==task['common_task_id']")
  text=text.replace('reserve=global_admission(require_launch=True)',"reserve=global_admission(require_launch=True)\n from queue_storage import admit\n admit(O)")
  text=text.replace("read(O/'DIRECT_CORE_RNG_RUNTIME_PROBE_RESULT.json')['passed']","read(SOURCE/'MPPI_RUNTIME_INTERFACE_PROOF.json')['passed']")
 elif name=='parallel_events.py':
  prior='common_09'if method=='RPP'else'common_02';allowed=[x.split('__')[0]for x in IDS[method]];text=text.replace("task['common_task_id']=='"+prior+"'","task['common_task_id'] in "+repr(allowed)+" and task['task_id']==O.name")
 ast.parse(text);return text
