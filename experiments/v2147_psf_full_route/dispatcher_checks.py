"""Actual single-task dispatcher decisions and path pins, zero processes/models."""
from context import R,C,SOURCE as S,load,put
m=load('new_full_route_dispatcher',C/'dispatcher.py')
assert m.decision(True,True,False)=='RUN'and m.decision(False,True,False)=='WAIT'and m.decision(True,False,False)=='DEADLINE_STOP'and m.decision(True,True,True)=='USER_STOP'
assert m.S==S and m.C==C and m.ready()
put(S/'DISPATCHER_SOFTWARE_PROOF.json',dict(passed=True,finite_order=['PSF'],models=0,physics=0,actual_dispatcher_ready_predecessors=True,actual_decision_cases=4))
print('dispatcher proof pass')
