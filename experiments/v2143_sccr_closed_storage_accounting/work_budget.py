"""Prospective optimizer stages: synchronize before exact completion counts."""
import copy
import os
import time

class WorkBudget:
 def __init__(self,*,receipt,absolute_deadline_unix,hard_stop_monotonic):
  assert sorted(os.sched_getaffinity(0))==[6]and os.environ.get('CUDA_VISIBLE_DEVICES')==''
  assert time.time()<absolute_deadline_unix<=time.time()+601 and time.monotonic()<hard_stop_monotonic
  self.receipt=receipt;self.end=absolute_deadline_unix;self.mono=hard_stop_monotonic;self.pending=None
  self.counts=dict(constructor_attempts=0,constructor_returns=0,optimizer_call_attempts=0,optimizer_calls=0,iterations_completed=0,projection_candidate_updates=0,elite_cost_evaluations=0,shifted_candidate_scores=0,initial_guess_scores=0,mathematical_candidate_evaluations=None,inflight_unknown=False,models=0,response_model_native=0,physical_native=0,Allocator_recomputations=0,replay_native=0)
  self.expected_caps=dict(optimizer_calls=1,CEM_iterations=12,projection_iterations_per_CEM=13,batch=110,elite_cost_batch=80,upsampling=30,timepoints=100,constructor_random_trajectory_vectors=3410,constructor_additional_scalar_normal_draws=16555)
 def check(self):
  assert time.time()<self.end and time.monotonic()<self.mono,'PRIEST_OPTIMIZER_ROOT_OR_SCOPE_EXPIRED'
 def save(self,**extra):self.receipt(dict(counts=copy.deepcopy(self.counts),expected_caps=copy.deepcopy(self.expected_caps),pending_stage=self.pending,**extra))
 def begin(self,stage):
  self.check();assert self.pending is None and stage in {'CONSTRUCTOR','WARM_GUESS','INITIAL_GUESS','CEM'}
  if stage=='CEM':assert self.counts['optimizer_call_attempts']==0;self.counts['optimizer_call_attempts']+=1
  if stage=='CONSTRUCTOR':assert self.counts['constructor_attempts']==0;self.counts['constructor_attempts']+=1
  self.pending=stage;self.started=time.monotonic();self.counts['inflight_unknown']=True;self.save(phase='DISPATCH_STARTED')
 def complete(self,stage):
  assert self.pending==stage
  if stage=='CONSTRUCTOR':self.counts['constructor_returns']+=1
  if stage=='INITIAL_GUESS':self.counts['initial_guess_scores']=3300
  if stage=='CEM':
   self.counts.update(optimizer_calls=1,iterations_completed=12,projection_candidate_updates=12*13*110,elite_cost_evaluations=12*80,shifted_candidate_scores=12*3300)
  elapsed=time.monotonic()-self.started;self.pending=None;self.counts['inflight_unknown']=False;self.save(phase='SYNCHRONIZED_RETURN',completed_stage=stage,wall_s=elapsed);self.check()
 def failure(self,error):
  # Do not infer how much work an interrupted compiled call completed.
  self.counts['inflight_unknown']=self.pending is not None;self.save(phase='CLOSED_ERROR',first_error=repr(error),partial_compiled_work_known=False)
