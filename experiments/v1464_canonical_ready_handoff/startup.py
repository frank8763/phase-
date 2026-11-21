"""Canonical t0 readiness and fail-fast cooperative process control only."""
import hashlib
import json
from pathlib import Path
import time

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())

def emit_ready(vehicle,canonical,output,*,run_id,source_identity,atomic):
 out=Path(output);assert vehicle.count==canonical.native.applied==vehicle.audit.native_count==0 and float(vehicle.d.time)==0. and not vehicle.rows and not vehicle.commands
 packet=read(out/'INITIAL_PACKET.json');assert packet['native_tick']==0 and packet['sim_time']==0. and packet['body']==list(vehicle.body())
 assert packet['controller_memory']['last_ctrl']==vehicle.adapter.last.tolist()and packet['controller_memory']['integral']==float(vehicle.adapter.integral)
 assert (out/'native.sock').is_socket()and (out/'INITIAL_FULL_STATE.npz').is_file()
 setup=read(out/'physics/SETUP.json');assert setup['model_sha256']==sha(out/'physics/scene_model.mjb')
 value=dict(run_id=run_id,source_identity=source_identity,native_tick=0,sim_time=0.,canonical_factory_returned=True,initial_packet_sha256=sha(out/'INITIAL_PACKET.json'),initial_fullstate_sha256=sha(out/'INITIAL_FULL_STATE.npz'),model_sha256=setup['model_sha256'],source_counts=dict(actual_native=0,private_native=0),ready_monotonic=time.monotonic(),ready_unix=time.time(),software_fixture=False)
 atomic(out/'CANONICAL_T0_READY.json',value);return value

def verify_ready(output,*,run_id,source_identity,allow_software=False):
 out=Path(output);value=read(out/'CANONICAL_T0_READY.json')
 assert value['software_fixture']is False or allow_software,'SOFTWARE_READY_CANNOT_AUTHORIZE_ACTUAL_ROS'
 assert value['run_id']==run_id and value['source_identity']==source_identity and value['canonical_factory_returned']is True
 assert value['native_tick']==0 and value['sim_time']==0. and value['source_counts']==dict(actual_native=0,private_native=0)
 assert value['initial_packet_sha256']==sha(out/'INITIAL_PACKET.json')and value['initial_fullstate_sha256']==sha(out/'INITIAL_FULL_STATE.npz')
 setup=read(out/'physics/SETUP.json');assert value['model_sha256']==setup['model_sha256']==sha(out/'physics/scene_model.mjb')
 packet=read(out/'INITIAL_PACKET.json');assert packet['native_tick']==0 and packet['sim_time']==0.
 assert (out/'native.sock').is_socket(),'CURRENT_NATIVE_SOCKET_NOT_READY'
 return value

def wait_ready(output,task,source_identity,job,window,*,maximum_s,check):
 out=Path(output);start=(time.time(),time.monotonic());assert maximum_s==180
 while True:
  check();assert max(time.time()-start[0],time.monotonic()-start[1])<maximum_s,'CANONICAL_INITIALIZER_READY_CAP'
  assert job.poll()is None,'NATIVE_CLOSED_BEFORE_CANONICAL_READY'
  if(out/'CANONICAL_T0_READY.json').exists():return verify_ready(out,run_id=task['run_id'],source_identity=source_identity)
  time.sleep(.05)

def unexpected_ROS_failure(output,run_id):
 out=Path(output);path=out/'ROS_RESULT.json'
 if not path.exists():return None
 value=read(path)
 if not value.get('closed'):return None
 requested=out/'PEER_STOP_REQUEST.json'
 cooperative=requested.exists()and read(requested).get('run_id')==run_id and value.get('functional_stop')=='COOPERATIVE_PEER_CLOSED'and value.get('controller_server_exited')is True and not value.get('error')and not value.get('evidence_write_errors')
 if cooperative or(value.get('passed')is True and value.get('controller_server_exited')is True and not value.get('error')and not value.get('evidence_write_errors')):return None
 return dict(first_saved_ROS_error=value.get('error')or value.get('functional_stop')or'ROS_FAILED_WITHOUT_REASON',ROS_result_sha256=sha(path),closed=value['closed'],cooperative_request_valid=cooperative,controller_server_exited=value.get('controller_server_exited'))

def request_native_stop(output,*,run_id,source_identity,error,atomic):
 out=Path(output);value=dict(run_id=run_id,source_identity=source_identity,reason=error,requested_unix=time.time(),requested_monotonic=time.monotonic(),no_new_action_authorized=True)
 atomic(out/'NATIVE_STOP_REQUEST.json',value);return value

def check_native_stop(output,*,run_id,source_identity):
 path=Path(output)/'NATIVE_STOP_REQUEST.json'
 if not path.exists():return
 value=read(path);assert value['run_id']==run_id and value['source_identity']==source_identity and value['no_new_action_authorized']is True,'FOREIGN_NATIVE_STOP_REQUEST'
 raise RuntimeError('SUPERVISOR_REQUESTED_NATIVE_SAVE_AND_CLOSE:'+str(value['reason']))

def wait_native_close(job,window,*,maximum_s,check):
 assert maximum_s==200;start=(time.time(),time.monotonic())
 while job.poll()is None:
  check();assert max(time.time()-start[0],time.monotonic()-start[1])<maximum_s,'NATIVE_COOPERATIVE_CLOSE_CAP'
  time.sleep(.05)
 return job.returncode


def initializer_deadlines(window,phase_end,*,cap_s):
 assert cap_s==180
 now=time.time();mono=time.monotonic()
 assert window['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 end=dict(absolute_deadline_unix=min(window['absolute_deadline_unix']-5,phase_end['absolute_deadline_unix'],now+cap_s),hard_stop_monotonic=min(window['hard_stop_monotonic']-5,phase_end['hard_stop_monotonic'],mono+cap_s))
 assert min(end['absolute_deadline_unix']-now,end['hard_stop_monotonic']-mono)>0,'CANONICAL_INITIALIZER_NO_REMAINING_WINDOW'
 return end
