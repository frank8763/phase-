"""A missing observed-ray key must fail the complete new auditor, no physics."""
import copy,gzip,hashlib,importlib.util,json,subprocess
from pathlib import Path
repo=Path(__file__).resolve().parents[2];src=repo/'experiments/v699_dynamic_packet_audit';root=repo/'runs/v699_dynamic_packet_audit'
pair=repo/'runs/v697_rpccr_dynamic_initialization/v698_slot13/paired';fixture=root/'negative_fixtures/missing_ray_key';cell=fixture/'geometry_memory';cell.mkdir(parents=True)
for name in ['STATIC_PROTOCOL.json','DYNAMIC_PROTOCOL.json','INITIAL_UNSEEN.json']:(fixture/name).symlink_to(pair/name)
for path in (pair/'geometry_memory').iterdir():
    if path.is_file() and path.name!='sensor_packets.jsonl.gz':(cell/path.name).symlink_to(path)
with gzip.open(pair/'geometry_memory/sensor_packets.jsonl.gz','rt') as stream:packets=[json.loads(line) for line in stream]
del packets[0]['rays'];(cell/'sensor_packets.jsonl.gz').write_bytes(gzip.compress(('\n'.join(json.dumps(x) for x in packets)+'\n').encode(),mtime=0))
spec=importlib.util.spec_from_file_location('v699_zero_guard_namespace',repo/'tools/isolate.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
output=root/'negative_missing_key';command=module.command(src/'zero_runner.py',writable=True)+['audit_discovery.py',str(fixture),'--output-dir',str(output)]
completed=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=45)
(root/'negative_missing_key.console').write_bytes(completed.stdout)
checks={'audit_process_rejected':completed.returncode!=0,'no_pass_or_audit_file_written':not (output/'DISCOVERY_CHAIN_AUDIT_V699.json').exists(),'missing_rays_key_reported':"KeyError: 'rays'" in completed.stdout.decode(),'original_packet_key_still_present':True}
with gzip.open(pair/'geometry_memory/sensor_packets.jsonl.gz','rt') as stream:checks['original_packet_key_still_present']='rays' in json.loads(next(stream))
result={'status':'MISSING_KEY_REJECTION_VERIFIED' if all(checks.values()) else 'FAIL','checks':checks,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'auditor_exit':completed.returncode,'simulation_steps':0,'new_navigation_trials':0,'review_guard_retained':(repo/'REVIEW_PENDING').exists()}
(root/'MISSING_KEY_NEGATIVE_TEST.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert all(checks.values())
