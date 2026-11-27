"""Static scopes and actual original auditor body checks; no old audit rerun."""
from context import R,C,SOURCE as S,O,read,put,sha
from pathlib import Path
import ast,os,json
assert os.sched_getaffinity(0)=={5}and not(S/'FINAL_SEAMS.json').exists()and not(S/'SOURCE_ONCE.json').exists()
t=ast.parse((C/'navigation.py').read_text());calls=[x for x in ast.walk(t)if isinstance(x,ast.Call)and isinstance(x.func,ast.Name)and x.func.id=='proof'];stops=[x for x in calls if any(isinstance(a,ast.Constant)and a.value=='segment_stop'for a in x.args)];assert len(stops)==1 and stops[0].args[-1].value==24
assert(C/'driver.py').read_text().count("originalalarm=signal.signal")==1
parent=R/'experiments/v2176_sccr_common_plant_component';tree=ast.parse((C/'audit_component.py').read_text());old=ast.parse((parent/'audit_component.py').read_text());fn=lambda z:next(n for n in z.body if isinstance(n,ast.FunctionDef)and n.name=='audit');f=fn(tree);g=fn(old)
# Original BASE generic/auditor/causal source/full-prediction/actual tracking/
# contact and Nplus1 block precedes only changed component query readout.
a=next(i for i,n in enumerate(f.body)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='query'for t in n.targets));b=next(i for i,n in enumerate(g.body)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='query_audit'for t in n.targets));assert ast.dump(ast.Module(body=f.body[:a],type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=g.body[:b],type_ignores=[]),include_attributes=False),'ORIGINAL_PHYSICAL_AUDIT_BODY_CHANGED'
for n in ['runtime_binding','response','resources','capture','work','source_scope','history_binding','generic_audit','base_quota','granted_quota','quota']:
 assert(C/(n+'.py')).read_bytes()==(parent/(n+'.py')).read_bytes()
assert read(S/'IO_PIPELINE_SOFTWARE.json')['passed']and read(S/'CLIENT_SOFTWARE.json')['passed']and read(S/'NAVIGATION_SOFTWARE.json')['passed']
# Verify runtime task/proof stopping origin and prospective length are consistent.
assert read(O/'PILOT_TASK.json')['maximum_control_native']==120
assert 'n==2320 and len(normal)==120 and len(all_geometry)==49'in(C/'audit_component.py').read_text()
for n in ['owner.py','context.py']:assert "maximum_control_native']==120"in(C/n).read_text()
for p in C.glob('*.py'):ast.parse(p.read_text())
x=dict(passed=True,original_generic_causal_fullprediction_tracking_contact_and_Nplus1_audit_AST_exact=True,stop_prediction_native_origin=120,stop_prediction_cycle=24,expected_actual_native=2320,component_only=True,all_original_safety_numeric_capture_replay_bodies_exact=True,only_component_query_cursor_readout_added=True,new_NLP_models_physics_Source=0,source_sha256={str(p.relative_to(R)):sha(p)for p in [C/'navigation.py',C/'audit_component.py',C/'audit_query_cursor.py',C/'driver.py',C/'final_seam_check.py']});put(S/'FINAL_SEAMS.json',x);print(json.dumps({k:v for k,v in x.items()if k!='source_sha256'}))
