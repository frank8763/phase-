"""Continuous branch-owned Python/CPP response; no construction on import.

Definitions are explicitly supplied from the frozen V1530 namespace. Every
numerical entry requires a real Guard and its recorded once admission.
"""
import copy
import importlib.util
import math
from pathlib import Path

R = Path(__file__).resolve().parents[2]
GEAR = 'experiments/v1396_rpp_rpc_retirement/gear_handoff.py'
FEEDBACK = 'experiments/v1409_scalar_steering_feedback/feedback.py'
MODEL = 'experiments/v1159_bounded_steering_load/model.py'
ENGINE = 'experiments/v1159_bounded_steering_load/engine.py'


def exact(name, relative, guard):
    guard.check()
    import hashlib
    path = R / relative
    assert hashlib.sha256(path.read_bytes()).hexdigest() == guard.source[relative]
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def new_gear(memory, guard):
    source = exact('v1550_canonical_gear',GEAR,guard)
    assert set(memory) == {'gear','last_tick','brake_start'}
    assert type(memory['gear']) is int and memory['gear'] in (-1,0,1)
    gate = source.GearHandoff()
    for key,value in memory.items():
        setattr(gate,key,value)
    return gate


def raw_body(raw):
    target,speed,parked = raw
    assert type(parked) is int and parked in (0,1)
    assert math.isfinite(target) and abs(target) <= .42722137342572125
    assert speed in (0.,-.03,.08,.12) and (not parked or speed == 0.)
    return float(speed), 0. if parked or speed == 0. else speed*math.tan(target)/.6


class PythonTrajectory:
    stage = 'PYTHON_GENERATION'

    def __init__(self,defs,setup,origin,gear_memory,method,guard):
        guard.check()
        assert Path(defs['model'].Predictor.__init__.__code__.co_filename).resolve() == R/MODEL
        assert method['response_method_sha256'] == guard.input_sha
        method = method['base_method']
        assert origin['steering_load_episode'] is False
        assert gear_memory['last_tick'] == method['fixed_origin_native']-1
        self.guard = guard
        self.base_native = self.native = method['fixed_origin_native']
        self.base_time = method['fixed_origin_sim_time']
        self.gear = new_gear(copy.deepcopy(gear_memory),guard)
        self.feedback = exact('v1550_current_scalar_feedback',FEEDBACK,guard)
        guard.begin(self.stage,'Predictor')
        self.p = defs['model'].Predictor(setup,copy.deepcopy(origin))
        guard.completed(self.stage,'Predictor')
        self.bind_encoder()

    def bind_encoder(self):
        # Closures copied by deepcopy still point at the parent predictor.
        # Bind explicitly to this branch; never reuse the parent's getter.
        p = self.p
        self.p.adapter.encoders = lambda:self.feedback.current(p)

    def fork(self):
        self.guard.begin(self.stage,'copy')
        child = object.__new__(type(self))
        child.__dict__ = self.__dict__.copy()
        child.p = copy.deepcopy(self.p)
        child.gear = copy.deepcopy(self.gear)
        child.bind_encoder()
        self.guard.completed(self.stage,'copy')
        return child

    def snapshot(self):
        p = self.p
        assert p.high_speed_episode is False
        return dict(state=p.state.copy(),memory=[*p.adapter.last,float(p.adapter.integral)],
                    modes=[int(p.coupled_episode),int(getattr(p.adapter,'_steering_motion_active',False)),int(p.steering_load_episode)],
                    parked_target=getattr(p.adapter,'parked_target',None),
                    encoders=list(self.feedback.current(p)),
                    gear=[self.gear.gear,self.gear.last_tick,-1 if self.gear.brake_start is None else self.gear.brake_start],
                    native=self.native,sim_time=self.base_time+.01*(self.native-self.base_native))

    def advance(self,raw):
        self.guard.check()
        before = self.snapshot()
        requested = raw_body(raw)
        gate = copy.deepcopy(self.gear)
        state = before['state']
        v,w,proof = gate.select(*requested,native_tick=self.native,
                               body=[*state[:4],state[5]],last_ctrl=before['memory'][:4],encoders=before['encoders'])
        self.p.adapter.parked_target = raw[0] if raw[2] else None
        self.gear = gate
        self.guard.begin(self.stage,'native')
        state,control = self.p.step(v,w,False)
        self.guard.completed(self.stage,'native')
        self.native += 1
        after = self.snapshot()
        return dict(before=before,after=after,raw=tuple(raw),requested=requested,
                    applied=(v,w),gear_proof=proof,ctrl=control.copy())


class CPPTrajectory:
    stage = 'CPP_AUDIT'

    def __init__(self,defs,engine,origin,gear_memory,method,guard):
        guard.check()
        assert Path(defs['engine'].Engine.simulate.__code__.co_filename).resolve() == R/ENGINE
        assert method['response_method_sha256'] == guard.input_sha
        method = method['base_method']
        assert gear_memory['last_tick'] == method['fixed_origin_native']-1
        self.guard = guard
        self.engine = engine
        self.origin = copy.deepcopy(origin)
        self.base_native = self.native = method['fixed_origin_native']
        self.base_time = method['fixed_origin_sim_time']
        self.steps = 0
        self.front_origin = [*origin['front_position'],*origin['front_velocity']]
        self.gear = new_gear(copy.deepcopy(gear_memory),guard)
        self.feedback = exact('v1550_CPP_scalar_feedback',FEEDBACK,guard)
        self.parked_target = None

    @classmethod
    def create(cls,defs,setup,coefficients,origin,gear_memory,method,guard):
        guard.check()
        assert Path(defs['engine'].Engine.__init__.__code__.co_filename).resolve() == R/ENGINE
        guard.begin(cls.stage,'Engine')
        engine = defs['engine'].Engine(setup,coefficients)
        guard.completed(cls.stage,'Engine')
        return cls(defs,engine,origin,gear_memory,method,guard)

    def fork(self):
        self.guard.begin(self.stage,'copy')
        child = object.__new__(type(self))
        child.__dict__ = self.__dict__.copy()
        child.origin = copy.deepcopy(self.origin)
        child.gear = copy.deepcopy(self.gear)
        # Only the immutable Engine/FFI wrapper is shared, called serially.
        # Each call's input comes from this branch's own previous outputs.
        self.guard.completed(self.stage,'copy')
        return child

    def snapshot(self):
        o = self.origin
        return dict(state=copy.deepcopy(o['state']),memory=[*o['last_ctrl'],o['integral']],
                    modes=[int(o['coupled_episode']),int(o['steering_motion_active']),int(o['steering_load_episode'])],
                    parked_target=self.parked_target,
                    encoders=self.front_origin.copy() if self.steps==0 else self.feedback.from_state(o['state']),
                    gear=[self.gear.gear,self.gear.last_tick,-1 if self.gear.brake_start is None else self.gear.brake_start],
                    native=self.native,sim_time=self.base_time+.01*(self.native-self.base_native))

    def advance(self,raw):
        self.guard.check()
        before = self.snapshot()
        requested = raw_body(raw)
        gate = copy.deepcopy(self.gear)
        state = before['state']
        v,w,proof = gate.select(*requested,native_tick=self.native,
                               body=[*state[:4],state[5]],last_ctrl=before['memory'][:4],encoders=before['encoders'])
        parked = raw[2]
        # Python's parked branch sees the raw target; a gear hold in driving
        # mode sees v=w=0, not the raw steering target or old control array.
        target = raw[0] if parked else math.atan(.6*w/v) if v else 0.
        row = (float(target),float(v),1,parked)
        self.guard.begin(self.stage,'native')
        states,controls,memory = self.engine.simulate(self.origin,[row])
        self.guard.completed(self.stage,'native')
        coupled = bool(self.origin['coupled_episode'])
        active = bool(self.origin['steering_motion_active'])
        loaded = bool(self.origin['steering_load_episode'])
        if not parked:
            active = False
        if abs(v)>=.005:
            coupled = False
        if parked or v<=-.005:
            loaded = False
        elif v>=.005:
            loaded = True
        if parked:
            coupled=active=True
        self.origin.update(state=states[-1].copy(),last_ctrl=memory[-1,:4].copy(),integral=float(memory[-1,4]),
                           coupled_episode=coupled,steering_motion_active=active,steering_load_episode=loaded)
        self.gear = gate
        self.parked_target = raw[0] if parked else None
        self.steps += 1
        self.native += 1
        after = self.snapshot()
        return dict(before=before,after=after,raw=tuple(raw),requested=requested,
                    applied=(v,w),gear_proof=proof,ctrl=controls[-1].copy())
