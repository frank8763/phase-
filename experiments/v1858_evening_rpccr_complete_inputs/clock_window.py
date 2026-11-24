"""Conservative finite float deadlines; do not extend any requested duration."""
import math
def earlier_deadline(start,duration):
 assert type(start)in{int,float}and math.isfinite(start)and start>=0
 assert type(duration)in{int,float}and math.isfinite(duration)and 0<duration<=5400
 stop=math.nextafter(start+duration,-math.inf)
 assert math.isfinite(stop)and 0<stop-start<=duration,'CLOCK_RESOLUTION_CANNOT_REPRESENT_BOUNDED_WINDOW'
 return stop
def make_window(now,started,boot):
 assert isinstance(boot,str)and boot
 return dict(started_unix=now,started_monotonic=started,absolute_deadline_unix=earlier_deadline(now,5400),hard_stop_monotonic=earlier_deadline(started,5400),normal_end_unix=earlier_deadline(now,4200),boot_id=boot)
