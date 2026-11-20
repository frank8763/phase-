"""Measured rear-axle travel drives fixed capture arcs; no physical imports."""
import math

def rear(body):return [body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]]

class Capture:
    def __init__(self,task):
        self.task=task;self.phase='REVERSE_ARC';self.cursor=None;self.distance=0.;self.brake_start=None

    def select(self,body,tick):
        p=rear(body)
        if self.cursor is not None and self.phase in ['REVERSE_ARC','FORWARD_ARC']:self.distance+=math.dist(p[:2],self.cursor[:2])
        self.cursor=p
        if self.phase=='REVERSE_ARC' and self.distance>=self.task['reverse_distance']:
            self.phase='BRAKE_REVERSE';self.brake_start=tick
        if self.phase=='BRAKE_REVERSE' and tick-self.brake_start>=200 and max(abs(x) for x in body[3:])<=.003:
            self.phase='FORWARD_ARC';self.distance=0.
        if self.phase=='FORWARD_ARC' and self.distance>=self.task['forward_distance']:self.phase='CAPTURE_COMPLETE'
        if self.phase=='REVERSE_ARC':v=-self.task['speed'];w=v*self.task['reverse_curvature']
        elif self.phase=='FORWARD_ARC':v=self.task['speed'];w=v*self.task['forward_curvature']
        else:v=w=0.
        return v,w,dict(phase=self.phase,actual_rear_travel_m=self.distance,brake_start=self.brake_start)

def errors(body,segment):
    a=rear(body);b=segment['poses'][0]
    return math.dist(a[:2],b[:2]),abs(math.atan2(math.sin(a[2]-b[2]),math.cos(a[2]-b[2])))
