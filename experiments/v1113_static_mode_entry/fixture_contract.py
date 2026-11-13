"""Scenario and compiled static identity contract, before any physical import."""
import math,re
def validate_task(task,fixture):
 s=fixture['setup'];p=fixture['packet']
 assert task['dynamic']is False and s['dynamic']is False and s['actor']is None,'STATIC_TASK_FIXTURE_SCOPE'
 assert task['case_id']==s['case']['id']=='NORTH_SOUTH'and task['seed']==s['seed']==10010002,'STATIC_CASE_SEED_BINDING'
 assert task['phase']==3.673083947600074,'STATIC_REGISTERED_PHASE'
 assert p['native_tick']==0 and p['sim_time']==0. and not p['dynamic_discovered'],'STATIC_T0_ONLY'
 assert p['body']==[-1.600000023841858,4.,-1.5707963267948963,0.,0.],'STATIC_CANONICAL_BODY'
 assert p['steering']['position']==p['steering']['velocity']==[0.,0.],'STATIC_INITIAL_ENCODERS'
 assert p['controller_memory']==dict(last_ctrl=[0.,0.,0.,0.],integral=0.),'STATIC_INITIAL_MEMORY'
 assert abs(s['dt']-.01)<1e-12 and s['stage_isolated']is True,'STATIC_PLANT_CONTRACT'
 assert re.fullmatch('[0-9a-f]{64}',s['model_sha256']),'STATIC_MJB_DIGEST'
 return True
def validate_actual(task,fixture,setup,model_sha):
 validate_task(task,fixture)
 assert model_sha==setup['model_sha256']==fixture['setup']['model_sha256'],'CANONICAL_STATIC_MODEL_CHANGED'
 assert setup==fixture['setup'],'STATIC_FULL_SETUP_CHANGED'
 return True
