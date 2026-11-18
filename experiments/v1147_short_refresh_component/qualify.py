"""Actual entry imports and old-refusal/new-refresh differential; zero vehicles."""
from common_short import *
import copy
import numpy as np
sys.path.insert(0,str(C));import worker,audit
from worker import historical_mode
sys.path.insert(0,str(R/'experiments/v1146_causal_certificate_refresh'))
from refresh import try_commit,digest

def main():
 assert '--isolated'in sys.argv or sha(R/'REVIEW_PENDING')==GUARD_SHA
 task=json.loads((C/'TASK.json').read_text());assert not Path(task['output']).exists()
 j=json.loads((worker.PARENT/'MODE_JOURNAL.json').read_text())
 for i in range(32515):historical_mode(i,j)
 qualified=json.loads((R/'runs/v1146_causal_certificate_refresh/QUALIFICATION.json').read_text());p=json.loads((R/'runs/v1146_causal_certificate_refresh/ACTUAL_REFUSAL_PACKET.json').read_text())
 current=qualified['refreshed'];old=qualified['old'];previous={'original':'complete stop'};candidate=dict(packet_sha256=digest(p),nested_domain=True,duals_verified=True,source_native_tick=32515,source_age_s=0.)
 _,green=try_commit(previous,p,lambda _:candidate,lambda a,b:current,lambda:0.,1.);_,red=try_commit(previous,p,lambda _:candidate,lambda a,b:old,lambda:0.,1.);assert green['committed']and not red['committed']
 source=json.loads((R/'runs/v1146_causal_certificate_refresh/CAUSAL_SOURCE.json').read_text());oldx=json.loads((R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/COUPLED_ENTRY.json').read_text());sys.path.insert(0,str(R/'runs/v1111_solver_dependencies/site'));from scipy.spatial import ConvexHull
 nested=max(float((np.asarray(new)@ConvexHull(np.asarray(prior)).equations[:,:3].T+ConvexHull(np.asarray(prior)).equations[:,3]).max())for new,prior in zip(source['periodic']['vertices'],oldx['source']['periodic']['vertices']));assert nested<=2e-8
 factory=load('qualified_short_actual_factory',R/'experiments/v1114_coupled_steering_mode/physical.py');assert callable(factory.create)and callable(factory.replay)
 result=dict(passed=True,actual_worker_and_audit_imported=True,canonical_history_schedule_checked=32515,old_red_new_green_at_actual_seam=True,nested_directional_hull_residual=nested,physical_factory_imported_without_constructing=True,models=0,physical_native=0,analytical_native=0,isolated='--isolated'in sys.argv)
 dump(O/('ISOLATED_QUALIFICATION.json'if '--isolated'in sys.argv else'QUALIFICATION.json'),result);print(encode(result))

if __name__=='__main__':main()
