"""Exact model calls counted outside original numerical bodies; no retries."""
import os,time
class ModelWork:
 def __init__(self,limits,deadline):
  self.limits=limits;self.deadline=deadline;self.cpp=0;self.python=0;self.cpp_calls=0;self.python_calls=0
  self.cpp_constructions=0;self.python_constructions=0;self.inflight=None;self.poisoned=False
 def before(self,kind,count):
  assert not self.poisoned and self.inflight is None
  assert sorted(os.sched_getaffinity(0))==[2]and time.time()<self.deadline
  assert type(count)is int and count>0 and getattr(self,kind)+count<=self.limits[kind+'_native_cap']
  self.inflight=dict(kind=kind,requested=count)
 def done(self,kind,count):
  assert self.inflight==dict(kind=kind,requested=count)
  setattr(self,kind,getattr(self,kind)+count);setattr(self,kind+'_calls',getattr(self,kind+'_calls')+1);self.inflight=None
 def bind(self,q):
  tracker=self;engine=q.accelerator.Engine;predictor=q.model.Predictor
  class CountedEngine(engine):
   def __init__(self,*a,**k):
    super().__init__(*a,**k);tracker.cpp_constructions+=1
   def simulate(self,origin,rows):
    n=sum(int(r[2])for r in rows);tracker.before('cpp',n);prior=self.native
    try:
     result=super().simulate(origin,rows);assert self.native-prior==n;tracker.done('cpp',n);return result
    except BaseException:tracker.poisoned=True;raise
  class CountedPredictor(predictor):
   def __init__(self,*a,**k):
    super().__init__(*a,**k);tracker.python_constructions+=1
   def step(self,*a,**k):
    tracker.before('python',1)
    try:value=super().step(*a,**k);tracker.done('python',1);return value
    except BaseException:tracker.poisoned=True;raise
  q.accelerator.Engine=CountedEngine;q.model.Predictor=CountedPredictor
 def snapshot(self):
  return dict(cpp_native=None if self.inflight and self.inflight['kind']=='cpp'else self.cpp,
    python_native=None if self.inflight and self.inflight['kind']=='python'else self.python,
    cpp_completed_native=self.cpp,python_completed_native=self.python,inflight=self.inflight,
    cpp_calls=self.cpp_calls,python_calls=self.python_calls,
    cpp_constructor_returns=self.cpp_constructions,python_constructor_returns=self.python_constructions,
    internal_Allocator_constructions=None,poisoned=self.poisoned)
