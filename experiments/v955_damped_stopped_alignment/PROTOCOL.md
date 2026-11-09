# V955 component candidate preparation

Old V950/V951/V953 remain failed and closed. User now explicitly requests
continuing and completing the original18 responses. This is one new candidate,
not a restart or repair of a frozen old batch. No navigation/new24/handoff model.

Moving conversion uses the V949 kinematic Ackermann mapping without the V856
extra measured-yaw steering P loop, retaining original longitudinal PI, actuator
bounds and per-second slew. This follows the interface separation described by
[ROS2 steering controllers](https://control.ros.org/jazzy/doc/ros2_controllers/steering_controllers_library/doc/userdoc.html):
inverse kinematics maps body twist to steering position and traction velocity;
path tracking is separate. This candidate is our implementation, not an executed
official ROS2 controller or a literature guarantee.

Stop: hold steering and brake traction to zero until measured body speed/yaw
<=.005 for10ticks, then latch ALIGNING until actual encoders are neutral/stable.
Steering target moves continuously toward zero at .60rad/s, below original1.25.
During alignment only, existing independently driven rear joints provide
zero-mean counter-yaw correction: diff=clip(-4*w*.54/(2*.12),+/-.40)rad/s,
left/right=-diff/+diff. No requested body retreat. This relies on the current
model's independent rear drives; real hardware is not yet connected/qualified.
Alignment body speed/yaw must remain <=.03, else fault and close; final encoders
<=.01rad and <=.03rad/s. Original measured response/safety gates are not reduced.

These fixed gains/rate are preregistered engineering hypotheses, not fitted
physical guarantees. No parameter search or new physics before freezing. Zero-
model checks use real old failure inputs, exact moving-map differential, latched
stop fixtures, counter-yaw sign/bounds, encoder failure and full evaluation seams.
All18 original tasks, timings, vehicle, course, seed, actor, sensor/noise and all
physical gates unchanged. New physical window at most90min, first failure stop.
