from pathlib import Path
import os,json,hashlib,math
from domain import project as initial
from domain_finite import project
O=Path(__file__).resolve().parents[2]/'runs/v2174_shared_virtual_command_domain'
assert os.sched_getaffinity(0)=={0}and not(O/'FINITE_TRACE_SUPPLEMENT.json').exists()
counter=dict(virtual_steer_rad=1.,virtual_wheel_rad_s=1e300,wheel_radius_m=.12,wheelbase_m=1e-308)
bad=initial(counter);assert not math.isfinite(bad['raw_bicycle_yaw_rate_rad_s'])
(O/'INITIAL_DERIVED_TRACE_OVERFLOW_COUNTEREXAMPLE.json').write_text(json.dumps({'initial_prepared_helper_preserved':True,'finite_input':counter,'initial_raw_yaw_rate_finite':False,'no_models_or_issued_commands':True,'initial_helper_sha256':hashlib.sha256((Path(__file__).parent/'domain.py').read_bytes()).hexdigest()},indent=2)+'\n')
try:project(counter)
except ValueError as e:reason=str(e)
else:raise AssertionError('OVERFLOW_TRACE_ACCEPTED')
assert reason.startswith('NONFINITE_DERIVED_TRACE')
p=dict(virtual_steer_rad=.2,virtual_wheel_rad_s=2.,wheel_radius_m=.12,wheelbase_m=.6)
assert project(p)==initial(p)
x={'passed':True,'scope':'DERIVED_TRACE_FINITE_ENVELOPE_ONLY','old_8positive_8negative_3saved_cases_not_rerun':True,
   'new_extreme_counterexample_rejected':reason,'one_ordinary_input_unchanged':True,'original_helper_unchanged':True,
   'production_preparation_helper':'domain_finite.py','new_models_NN_physics_replay_audit_source':0,
   'helper_sha256':hashlib.sha256((Path(__file__).parent/'domain_finite.py').read_bytes()).hexdigest()}
(O/'FINITE_TRACE_SUPPLEMENT.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({'passed':True,'overflow_rejected':True,'ordinary_equivalence':True}))
