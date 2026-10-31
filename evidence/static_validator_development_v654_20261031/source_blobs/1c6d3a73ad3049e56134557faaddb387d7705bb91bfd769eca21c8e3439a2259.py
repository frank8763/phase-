"""Zero-simulation regression: a path rewrite cannot hide physical differences."""
import copy
import json
from pathlib import Path
from contact_fingerprint import normalize, compare_contacts

repo = Path(__file__).resolve().parents[2]
base = repo/'runs/v651_static_progress/dev29_seed93000074_legacy_two/paired'
repeat = repo/'runs/v653_static_log_recovery/repeat_93000074_legacy_two/paired'
proof = compare_contacts(base, repeat)
assert proof['passed'] and not proof['raw_content_hashes_identical']
assert proof['contact_records'] == [91819,91819]
assert proof['raw_json_different_rows'] == 66940
row = {'classification_basis':{'geom1':{'xml':str(base/'assets/isolated_indoor.xml')}},
       'contact_distance':-.001, 'position':[1.,2.,3.], 'physics_step':1,
       'contact_type':'ground_support'}
a = normalize(row, base, proof['xml_bytes_sha256'][0])
changed = copy.deepcopy(row); changed['contact_distance'] = -.002
assert a != normalize(changed, base, proof['xml_bytes_sha256'][0])
changed = copy.deepcopy(row); changed['position'][0] += 1e-12
assert a != normalize(changed, base, proof['xml_bytes_sha256'][0])
changed = copy.deepcopy(row); changed['contact_type'] = 'robot_obstacle'
assert a != normalize(changed, base, proof['xml_bytes_sha256'][0])
assert a != normalize(row, base, 'different_xml_bytes')
changed = copy.deepcopy(row); changed['classification_basis']['geom1']['xml'] = '/tmp/other.xml'
try:
    normalize(changed, base, proof['xml_bytes_sha256'][0])
except AssertionError:
    pass
else:
    raise AssertionError('Unexpected provenance was accepted')
output = repo/'runs/v654_static_overnight'
output.mkdir(exist_ok=True)
(output/'CONTACT_PATH_DIAGNOSIS.json').write_text(json.dumps(proof,indent=2)+'\n')
result = {'passed':True, 'simulation_steps':0,
          'physical_distance_change_rejected':True, 'position_change_1e12_rejected':True,
          'classification_change_rejected':True, 'different_xml_hash_rejected':True,
          'unexpected_provenance_path_rejected':True}
(output/'ZERO_STEP_CONTACT_REGRESSION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
