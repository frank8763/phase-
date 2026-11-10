"""Atomic profile release into one previously admitted stationary command."""
import copy,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v1013_original_profile_owner',R/'experiments/v1019_terminal_progress_recovery/profile_owner.py')
original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
class Startup(original.Startup):
    def receive(self,packet,now,native_tick,sim_time):
        if packet.get('kind')!='release_profile':return super().receive(packet,now,native_tick,sim_time)
        assert self.phase=='RUNNING'and self.profile is None and self.holding and packet['profile_id']==self.active_profile_id,'HANDOFF_PROFILE_NOT_COMPLETE'
        command=packet.get('resume_command');assert isinstance(command,dict),'HANDOFF_ZERO_PROOF_MISSING'
        assert command['kind']=='command'and command['run_id']==packet['run_id']==self.run_id and command['v']==command['w']==0.,'HANDOFF_COMMAND_NOT_OWN_ZERO'
        assert command['issued_at']==packet['issued_at']and 0<=now-command['issued_at']<=.05,'HANDOFF_ZERO_DELIVERY_OVER_50MS'
        proof=command['tube'];assert proof['v']==proof['w']==0. and proof['passed']is True and 0<=proof['body_age_s']<=.05,'HANDOFF_ZERO_NOT_QUALIFIED'
        assert 0<=native_tick-proof['body_native_tick']<=10,'HANDOFF_ZERO_NOT_CURRENT_NATIVE_STATE'
        # Validate the unchanged production finite-tube/sequence contract on an
        # isolated metadata copy BEFORE switching adapter or dropping ownership.
        shadow=copy.copy(self);shadow.command=None;shadow.events=[];shadow.receipts=[];shadow.execution=[]
        original.base.Startup.receive(shadow,command,now,native_tick,sim_time)
        assert shadow.command==command and shadow.receipts[-1]['decision']=='ACCEPTED','HANDOFF_ZERO_NOT_ACCEPTED'
        # Native integration is single threaded: no Vehicle.step can occur
        # between these operations. Both resulting ingress rows are audited.
        super().receive(packet,now,native_tick,sim_time)
        original.base.Startup.receive(self,command,now,native_tick,sim_time)
        self.vehicle.profile_status['handoff_sequence']=command['sequence']
