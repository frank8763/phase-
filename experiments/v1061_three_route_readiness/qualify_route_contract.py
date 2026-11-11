"""Original NS goal through the real producer with a SYNTHETIC actor source.

This tests route arguments, complete input/control/goal handling and runtime;
no assertion about the original NS actual sensor evidence or dynamic passage.
"""
import copy,json,sys,time,subprocess,itertools,math,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import O,dump
from fresh import actions_from_requests
import numpy as np

def main():
 meta=json.loads((O/'NORTH_SOUTH_T0_METADATA.json').read_text());static=json.loads((O/'NORTH_SOUTH_STATIC_SOURCE.json').read_text());assert static['passed'];packet=copy.deepcopy(meta['packet']);now=time.monotonic();packet.update(sent_at=now,body_measured_at=now,dynamic_discovered=True);packet['steering']['measured_at']=now
 # Controlled software fixture only. Anchor/frequency/amplitude coefficients
 # are chosen here, not observed from an evaluator or from the actual NS actor.
 vertices=[]
 for theta in np.arange(8)*math.pi/8:
  center=4*math.cos(theta)+4*math.sin(theta);vertices.append([[center+dc,a,b]for dc,a,b in itertools.product([-.001,.001],repeat=3)])
 source=dict(source_native_tick=0,source_age_s=0.,decision_at=now,periodic=dict(omega=.32,amplitude=.25,source_tick=0,last=0.,vertices=vertices));actions=actions_from_requests(static['plan']['planned_body_requests']);folder=O/'ns_synthetic_contract_fixed_clock';folder.mkdir(exist_ok=False);payload=dict(setup=meta['setup'],packet=packet,source=source,goal=meta['goal'],actions=actions,elapsed=0);dump(folder/'INPUT.json',payload);dump(folder/'FIXTURE_SCOPE.json',dict(synthetic_actor_anchor=[4,4],coefficient_box_halfwidth=.001,not_original_NS_actor=True,no_actual_sensor_or_truth_used=True,original_NS_start_goal_requests_unchanged=True,actual_dynamic_route_qualified=False,models=0,integrations=0));started=time.monotonic()
 with(folder/'console').open('x')as log:p=subprocess.run([sys.executable,'-B',str(C/'source_job.py'),str(folder)],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=18)
 wall=time.monotonic()-started;result=json.loads((folder/'RESULT.json').read_text());math_passed=p.returncode==0 and result['passed'];passed=math_passed and wall<=8.;summary=dict(passed=passed,source_math_passed=math_passed,software_contract_only=True,actual_NS_dynamic_profile_qualified=False,original_start_goal_and_inputs=True,native_requests=len(static['plan']['planned_body_requests']),producer_job_exit=p.returncode,total_producer_wall_s=wall,within_original8s_hold_budget=wall<=8.,error=result.get('error'),models=0,integrations=0)
 if math_passed:summary.update(goal_upper_m=result['terminal_goal_upper_m'],complete_goal_control_checks=result['complete_profile_checks'],wait_equivalence_proof=result['wait_equivalence_proof'])
 dump(O/'NS_SOFTWARE_CONTRACT_QUALIFICATION.json',summary);print(json.dumps(summary))
if __name__=='__main__':main()
