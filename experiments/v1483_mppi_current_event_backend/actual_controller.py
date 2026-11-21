"""Actual ROS controller factory, exact same identity as the modeled peer.

No standalone CLI or permission. The not-yet-qualified integrated route must
supply a current task-bound authority and the original bounded writer proxy.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1483_actual_MPPI_identity',C/'controller_identity.py');identity=importlib.util.module_from_spec(s);s.loader.exec_module(identity)
def start(task,*,output,log):
 output=Path(output);assert output.is_absolute()and output.is_relative_to(R/'runs')
 binding=task['controller_binding'];identity.verify_environment(binding,role='ACTUAL_ROS')
 assert task['seed']==10060001 and task['case_id']=='WEST_EAST'and task['controller_plugin']=='Deadband'and task['controller_kind']=='mppi'
 assert task['nav2_params']==str(identity.PARAMS)
 authority=json.loads((output/'ACTUAL_MPPI_PROCESS_AUTHORITY.json').read_text());parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text())
 assert authority['scope']=='ACTUAL_MPPI_CONTROLLER_CURRENT_ROUTE'and authority['models_authorized']is True
 assert authority['round_id']==parent['active_round']and parent['models_now_authorized']and parent['scientific_revisions']==6
 assert authority['run_id']==task['run_id']and authority['controller_identity_sha256']==binding['controller_identity_sha256']
 assert authority['task_sha256']==identity.digest(task)and authority['boot_id']==parent['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert time.time()<authority['absolute_deadline_unix']<=1795395600 and time.monotonic()<authority['hard_stop_monotonic']<=parent['hard_stop_monotonic']
 assert authority['source_hashes']and all(identity.sha(R/name)==digest for name,digest in authority['source_hashes'].items())
 assert os.environ['PHASE_BOUNDED_WRITER_ROLE']=='ACTUAL_ROS'and os.environ['PHASE_BOUNDED_SOURCE_ID']==authority['outer_source_identity']
 assert Path(log.__class__.write.__code__.co_filename).resolve()==C/'bounded_io.py','ACTUAL_MPPI_LOG_REQUIRES_DECLARED_BYTE_BOUNDARY'
 assert log.path==output/'controller.console'and log.boundary.output==output
 server=subprocess.Popen(['/opt/ros/jazzy/lib/nav2_controller/controller_server','--ros-args','--disable-external-lib-logs','--disable-rosout-logs','--params-file',str(identity.PARAMS)],stdout=log,stderr=subprocess.STDOUT)
 return server,identity.process_identity(server.pid)

def configured_identity(record,task):
 return identity.verify_loaded(record,role='ACTUAL_ROS',value=task['controller_binding'])
