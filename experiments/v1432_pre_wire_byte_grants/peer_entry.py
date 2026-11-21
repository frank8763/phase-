"""Executed inside the private ROS namespace; original peer bytecode unchanged."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
R=Path(__file__).resolve().parents[2]

def main():
 out=Path(sys.argv[1]);assert out.is_absolute()and out.is_relative_to(R/'runs')and sorted(os.sched_getaffinity(0))==[3]
 current=json.loads((out/'CURRENT_INPUT.json').read_text());value=dict(current);identity=value.pop('input_sha256');assert hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==identity
 p=Path(__file__).with_name('modeled_peer.py');original=R/'experiments/v1398_current_event_witness/modeled_peer.py';proof=dict(inner_pid=os.getpid(),parent_pid=os.getppid(),network_namespace=os.readlink('/proc/self/ns/net'),current_input_sha256=identity,source_peer_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),active_bounded_peer_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),actual_cpu=[3],models=0,physical_native=0,recorded_monotonic=time.monotonic())
 target=out/'MODELED_PEER_INNER_NAMESPACE.json';assert not target.exists();temporary=target.with_suffix('.pending');temporary.write_text(json.dumps(proof,indent=2)+'\n');temporary.replace(target)
 spec=importlib.util.spec_from_file_location('v1425_original_frozen_modeled_peer',p);source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source);entry_path=Path(__file__).with_name('entry_boundary.py');spec=importlib.util.spec_from_file_location('v1432_inner_output_boundary',entry_path);entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry);return entry.run(source.main)
if __name__=='__main__':raise SystemExit(main())
