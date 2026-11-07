"""Register fixed development and fresh confirmation before scene navigation."""
import hashlib,json,math,random
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OUT=R/'runs/v858_nav2_verified';W=R/'experiments/v855_renewal_worker'
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 assert not(C/'TASK_LIST.json').exists(),'TASK_POOL_ALREADY_LOCKED'
 # Produce known-static-only occupancy map and config using the fixed V856 derivation.
 import prepare_tasks;prepare_tasks.prepare()
 cases=json.loads((W/'SCENE_CASES.json').read_text());phases=[.6573753567727383,3.673083947600074,.9511239917756753];tasks=[]
 def add(ident,stage,i,seed,phase):
  case=cases[i];task=dict(id=ident,stage=stage,case_id=case['id'],seed=seed,phase=phase,goal_xy=case['goal_xy'],goal_yaw=case['yaw'],dynamic=stage!='static_main',wall_limit_s=180,output=str(OUT/ident),nav2_params=str(C/'physical_nav2_params.yaml'),root_deadline_unix=1794052800.,algorithm='GENUINE_NAV2_SMAC_MPPI_NOMINAL_BASELINE_NO_RPCCR_328_CERTIFICATE');tasks.append(task);dump(OUT/(ident+'.task.json'),task)
 for stage in ['static_main','dynamic_main','dynamic_repeat']:
  for i in range(3):add(f'{stage}_{i+1:02d}',stage,i,10010001+i,phases[i])
 rng=random.Random(202611075858)
 for slot in range(1,25):
  i=(slot-1)//8;theta=rng.random()*2*math.pi
  # Sine derivative sign is locked balanced by reflection, no outcome screening.
  desired_positive=(slot-1)%2==0
  if (math.cos(theta)>0)!=desired_positive:theta=(math.pi-theta)%(2*math.pi)
  add(f'confirmation_{slot:02d}','confirmation',i,10080000+slot,theta);tasks[-1]['slot']=slot;tasks[-1]['initial_axis_direction']='POSITIVE'if math.cos(theta)>0 else'NEGATIVE';dump(OUT/(tasks[-1]['id']+'.task.json'),tasks[-1])
 for slot in [1,9,17]:
  base=next(t for t in tasks if t.get('slot')==slot);t=dict(base,id=f'confirmation_repeat_{slot:02d}',stage='confirmation_repeat',output=str(OUT/f'confirmation_repeat_{slot:02d}'));tasks.append(t);dump(OUT/(t['id']+'.task.json'),t)
 dump(C/'TASK_LIST.json',tasks);dump(C/'CONFIRMATION_REGISTRATION.json',dict(registered_before_scene_navigation=True,pool='10080001-10080024',phase_rng='Python MT19937 seed202611075858, uniform phase then predeclared direction reflection',new_vs_old_100600_pool=True,full_denominator=24,per_route=8,direction_each=12,strict_chain_minimum=23,per_route_minimum=7,per_direction_minimum=11,fixed_full_repeats=[1,9,17],first_safety_or_evidence_failure_stops=True,second_functional_failure_stops=True,no_replacement=True,per_navigation_wall_limit_s=180,latest_root_deadline_unix=1794052800.,confirmation_start_requires_remaining_s=5700,development_must_pass_first=True,scope='Finite declared single-actor Nav2 baseline acceptance only, not RP-CCR or algorithm superiority'))
 print('REGISTERED_TASKS',len(tasks))
if __name__=='__main__':main()
