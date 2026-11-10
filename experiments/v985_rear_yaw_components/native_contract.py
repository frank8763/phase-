"""Canonical saved-state origin for ARM only; original command/native guards."""
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v979_original_native_contract',R/'experiments/v968_rpp_closed_loop_night/native_contract.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

class Startup(base.Startup):
    def __init__(self,run_id):
        super().__init__(run_id)
        from authority import read
        self.task=next(t for t in read(Path(__file__).parent/'TASKS.json')if t['run_id']==run_id)
    def receive(self,packet,now,native_tick,sim_time):
        origin=self.task.get('origin_native_tick',0)
        if origin and packet.get('kind')=='arm':
            assert native_tick==origin and abs(sim_time-self.task['origin_sim_time'])<=1e-9,'COMPONENT_ADVANCED_BEFORE_ARM'
            assert packet['native_tick']==origin and abs(packet['sim_time']-sim_time)<=1e-9,'ARM_NOT_FOR_RESTORED_COMPONENT'
            original=dict(packet)
            super().receive(dict(packet,native_tick=0,sim_time=0.),now,0,0.)
            self.events.append(dict(event='COMPONENT_ORIGIN_ARM_VALIDATED',global_native_tick=origin,global_sim_time=sim_time,
                                    logical_startup_origin_only=True,actual_arm_packet=original))
        else:super().receive(packet,now,native_tick,sim_time)
