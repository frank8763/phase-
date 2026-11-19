"""Public motion-class conditioning; no anchor, phase, axis or actor truth input.

The speed-only predecessor remains unchanged in V1354. This version explicitly
conditions on bounded .25m sinusoidal excursion (and .32rad/s for PERIODIC).
It is a new prior, never a decision-equivalent speed-only repair.
"""
import importlib.util
import math
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parents[2]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,R/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


legacy=load('phase_speed_only_ball','experiments/v1354_fast_stamped_pipeline/causal_occupancy.py')
periodic=load('phase_public_periodic','experiments/v1037_periodic_norm_source/periodic_norm.py')
swept=load('phase_periodic_swept','experiments/v1020_terminal_two_route_development/periodic_support.py')
NORMALS=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)]


class CausalBall(legacy.CausalBall):
    def __init__(self,known,horizon_s=1.5,model='EXCURSION'):
        super().__init__(known,horizon_s)
        assert model in ['EXCURSION','PERIODIC']
        self.model=model;self.periodic=periodic.PeriodicSupport() if model=='PERIODIC' else None
        self.forecasts=[]

    def update(self,*,native_tick,sim_time,center_body,ranges):
        seen=super().update(native_tick=native_tick,sim_time=sim_time,center_body=center_body,ranges=ranges)
        if seen and self.periodic is not None:
            # The inherited .24m observation-to-center bound is unchanged.
            supports=NORMALS@self.center+.24
            self.periodic.update(sim_time,native_tick,supports.tolist())
        return seen

    def occupied_ball(self,sim_time):
        ball=super().occupied_ball(sim_time)
        if ball is None:return None
        center,speed_radius=ball
        # Public .25 Euclidean excursion around a fixed unknown anchor implies
        # distance between any two centers <=.50. Intersect two displacement
        # upper bounds, keeping the original observation and actor radii.
        radius=.24+.10+min(.08*(max(0.,sim_time-self.last)+self.horizon),.50)
        method='AMPLITUDE_BOUNDED_DISPLACEMENT'
        if self.periodic is not None and self.periodic.last is not None:
            bounds=swept.swept_bounds([p.v for p in self.periodic.polytopes],sim_time,sim_time+self.horizon)
            lower=-bounds[[8,12]];upper=bounds[[0,4]]
            assert np.isfinite(bounds).all() and (lower<=upper).all(),'PERIODIC_SUPPORT_INCONSISTENT'
            point=(lower+upper)/2;rho=float(np.linalg.norm((upper-lower)/2))+.10
            # Each candidate disk independently encloses the declared actor
            # throughout the horizon. Choosing the smaller is conservative.
            if rho<radius:center=point;radius=rho;method='PERIODIC_SWEPT_RECTANGLE_ENCLOSING_DISK'
        if not self.forecasts or self.forecasts[-1]['native_tick']!=self.last_tick:
            self.forecasts.append(dict(native_tick=self.last_tick,sim_time=sim_time,model=self.model,
                center=center.tolist(),radius_m=radius,old_speed_only_radius_m=speed_radius,
                last_observed_time=self.last,method=method,horizon_s=self.horizon,
                periodic_source_tick=None if self.periodic is None else self.periodic.source_tick))
        return center.copy(),radius

    def snapshot(self):
        return dict(model=self.model,last_observed_time=self.last,
             periodic=None if self.periodic is None else self.periodic.snapshot(),
             class_assumptions=dict(amplitude_m=.25,maximum_center_displacement_m=.50,
                 omega_rad_s=.32 if self.periodic is not None else None,norm_speed_m_s=.08),
             online_actor_truth=False)
