"""Owner-side current request binding and immutable witness commit.

The future native integration supplies the registered generator/auditor and
physical guards. This module never constructs a model or advances a vehicle.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from session import Session,digest
from method_dispatch import choose

R=Path(__file__).resolve().parents[2]


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


origin=exact('v1404_current_owner_binding',R/'experiments/v1398_current_event_witness/origin_binding.py')


def measured_identity(vehicle):
    state={key:getattr(vehicle.d,key).tolist()for key in ('qpos','qvel','ctrl','mocap_pos','mocap_quat')};state['time']=float(vehicle.d.time)
    return hashlib.sha256(json.dumps(state,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


class OwnerRequest:
    def __init__(self,notice,*,output,vehicle,mode_memory,gear,run_id,last_event_index,now):
        output=Path(output).resolve();assert output.is_relative_to(R/'runs')
        self.output=output
        assert notice['kind']=='BRIDGE_CERTIFICATE_REQUEST_FILE'and notice['run_id']==run_id
        assert type(notice['event_index'])is int and notice['event_index']==last_event_index+1, 'NATIVE_EVENT_SEQUENCE'
        path=R/notice['path'];expected=output/'cusp_requests'/('event%04d.json'%notice['event_index'])
        assert path==expected and path.resolve()==expected and not path.is_symlink(), 'NATIVE_CUSP_FILE_ESCAPE'
        assert path.stat().st_size<=4*1024**2 and hashlib.sha256(path.read_bytes()).hexdigest()==notice['file_sha256'], 'NATIVE_CUSP_FILE_CHANGED'
        packet=json.loads(path.read_text());request=packet['request'];self.session=Session(packet)
        assert request['run_id']==run_id and request['event_index']==notice['event_index']and request['request_sha256']==notice['request_sha256']
        self.current=origin.bind(vehicle,request,mode_memory,packet['causal_snapshot'],gear=gear,now=now)
        self.method=choose(request)
        self.start_native=vehicle.count;self.start_full_state_sha256=measured_identity(vehicle)
        self.controller_memory=copy.deepcopy(self.current['origin']['controller_memory']);self.mode_history=copy.deepcopy(self.current['mode_history'])
        self.gear_memory=copy.deepcopy(self.current['gear_memory']);self.committed=False;self.closed=False

    def commit(self,*,vehicle,mode_memory,gear,generation,audit,evidence_files,manifest_path):
        assert not self.committed and not self.closed and vehicle.count==self.start_native
        assert measured_identity(vehicle)==self.start_full_state_sha256, 'PHYSICAL_STATE_ADVANCED_DURING_MODEL_CERTIFICATE'
        assert vehicle.adapter.last.tolist()==self.controller_memory['last_ctrl']and float(vehicle.adapter.integral)==self.controller_memory['integral'], 'ALLOCATOR_CHANGED_DURING_MODEL_CERTIFICATE'
        assert mode_memory.snapshot(vehicle.count)==self.mode_history
        assert dict(gear=gear.gear,brake_start=gear.brake_start,last_tick=gear.last_tick)==self.gear_memory
        assert generation['passed']is True and generation['closed']is True and not generation['analytical_inflight_unknown']
        assert audit['passed']is True and audit['closed']is True and not audit['audit_inflight_unknown']
        assert generation['input_sha256']==self.current['input_sha256']
        assert generation['qualified_method']==self.method['method'], 'GENERATED_WITNESS_DOES_NOT_COVER_DISPATCHED_METHOD'
        assert generation['complete_braking_branches']==generation['nominal_native']and audit['braking_origins']==generation['nominal_native']
        assert audit['model_error']<=1e-8 and generation['checks']['complete200_zero_tail']and audit['checks']['complete200_zero_tail']
        manifest_path=Path(manifest_path)
        assert manifest_path.parent==self.output/'bridge_events'/('event%04d'%self.session.event_index)and manifest_path.name=='CERTIFICATE.json', 'NATIVE_CERTIFICATE_OUTPUT_ESCAPE'
        files=[]
        for path in evidence_files:
            path=Path(path);assert path.is_absolute()and path.is_relative_to(Path(manifest_path).parent)and not path.is_symlink()
            files.append(dict(path=str(path.relative_to(R)),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        assert files
        value=dict(request_sha256=self.session.request_sha256,input_sha256=self.current['input_sha256'],start_native=self.start_native,
                   start_full_state_sha256=self.start_full_state_sha256,method=self.method,files=files,
                   generation=copy.deepcopy(generation),independent_model_audit=copy.deepcopy(audit),physical_admission=False)
        identity=digest(value);path=Path(manifest_path);assert path.is_absolute()and not path.exists()
        temporary=path.with_suffix(path.suffix+'.pending');temporary.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n');temporary.replace(path)
        self.committed=True;self.certificate_sha256=identity
        return dict(kind='BRIDGE_CERTIFICATE_READY',run_id=self.session.run_id,event_index=self.session.event_index,
                    request_sha256=self.session.request_sha256,input_sha256=self.current['input_sha256'],certificate_sha256=identity,
                    model_generation_passed=True,independent_model_audit_passed=True)

    def reject(self,reason):
        self.closed=True
        return dict(kind='BRIDGE_FAILED',run_id=self.session.run_id,event_index=self.session.event_index,
                    request_sha256=self.session.request_sha256,reason=str(reason),physical_admission=False)
