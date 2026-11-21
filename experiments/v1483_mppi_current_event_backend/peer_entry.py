"""Executed inside the private ROS namespace; original peer bytecode unchanged."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
R=Path(__file__).resolve().parents[2]

def exact(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def bounded_main():
 out=Path(sys.argv[1]);assert out.is_absolute()and out.is_relative_to(R/'runs')and sorted(os.sched_getaffinity(0))==[3]
 current=json.loads((out/'CURRENT_INPUT.json').read_text());binding=exact('v1483_MPPI_inner_identity',Path(__file__).with_name('controller_identity.py'));controller_sha=binding.verify_current(current);binding.verify_environment(current['controller_binding'],role='MODELED_ROS')
 identity=current['input_sha256'];p=Path(__file__).with_name('modeled_peer.py');proof=dict(inner_pid=os.getpid(),parent_pid=os.getppid(),network_namespace=os.readlink('/proc/self/ns/net'),current_input_sha256=identity,controller_identity_sha256=controller_sha,source_peer_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),active_bounded_peer_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),actual_cpu=[3],models=0,physical_native=0,recorded_monotonic=time.monotonic())
 target=out/'MODELED_PEER_INNER_NAMESPACE.json';assert not target.exists();temporary=target.with_suffix('.pending');temporary.write_text(json.dumps(proof,indent=2)+'\n');temporary.replace(target)
 return exact('v1483_bound_MPPI_modeled_peer',p).main()

def main():
 entry=exact('v1483_inner_bounded_writer',Path(__file__).with_name('entry_boundary.py'))
 return entry.run(bounded_main)
if __name__=='__main__':raise SystemExit(main())
