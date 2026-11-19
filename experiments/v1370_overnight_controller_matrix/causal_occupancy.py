"""Current-horizon or nested all-future disk under the declared periodic class."""
import importlib.util
import math
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('phase_original_periodic_ball',R/'experiments/v1357_expiry_evidence_relay/causal_occupancy.py')
base=importlib.util.module_from_spec(s);s.loader.exec_module(base)


class CausalBall(base.CausalBall):
    def __init__(self,known,horizon_s=1.5,model='PERIODIC',forecast_kind='HORIZON'):
        super().__init__(known,horizon_s,model=model)
        assert model=='PERIODIC' and forecast_kind in ['HORIZON','NESTED_SWEEP']
        self.forecast_kind=forecast_kind;self.invariant_disk=None;self.sweep_events=[]

    def occupied_ball(self,sim_time):
        if self.forecast_kind=='HORIZON':return super().occupied_ball(sim_time)
        if self.center is None:return None
        assert sim_time>=self.last-1e-8
        # Any two true actor centers are at most2*.25m apart. This disk from
        # a real return is valid for ALL times under the declared fixed-anchor
        # class, even if subsequent observations are lost.
        candidate=(self.center.copy(),.24+.10+.50)
        period=math.tau/.32
        if self.periodic is not None and self.periodic.last is not None:
            support=base.swept.swept_bounds([p.v for p in self.periodic.polytopes],0.,period)
            lower=-support[[8,12]];upper=support[[0,4]]
            assert (lower<=upper).all() and np.isfinite(support).all()
            center=(lower+upper)/2;radius=float(np.linalg.norm((upper-lower)/2))+.10
            if radius<candidate[1]:candidate=(center,radius)
        previous=self.invariant_disk
        install=previous is None or np.linalg.norm(candidate[0]-previous[0])+candidate[1]<=previous[1]-1e-10
        if install:
            self.invariant_disk=(candidate[0].copy(),candidate[1])
            self.sweep_events.append(dict(native_tick=self.last_tick,sim_time=sim_time,center=candidate[0].tolist(),
                radius_m=candidate[1],previous_center=None if previous is None else previous[0].tolist(),
                previous_radius_m=None if previous is None else previous[1],valid_for_all_future_under_declared_class=True))
        center,radius=self.invariant_disk
        if not self.forecasts or self.forecasts[-1]['native_tick']!=self.last_tick:
            self.forecasts.append(dict(native_tick=self.last_tick,sim_time=sim_time,model=self.model,
                center=center.tolist(),radius_m=radius,horizon_s=1.5,last_observed_time=self.last,
                method='NESTED_ALL_PERIOD_SWEPT_DISK',forecast_kind=self.forecast_kind,
                invariant_for_all_future_under_declared_class=True,coefficient_sweep_period_s=period,
                periodic_source_tick=self.periodic.source_tick))
        return center.copy(),radius

    def snapshot(self):
        value=super().snapshot();value.update(forecast_kind=self.forecast_kind,nested_sweep_events=self.sweep_events)
        return value
