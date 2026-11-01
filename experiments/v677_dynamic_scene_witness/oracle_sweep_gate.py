"""Explicitly privileged full-sweep occupancy, constant at every future time."""
from types import MethodType

def install_swept_gate(field):
    def trajectory_values(self,poses,dt):return self.pose_values(poses)
    field.trajectory_values=MethodType(trajectory_values,field)
    field.information_role='ORACLE_FULL_SWEEP_SCENE_WITNESS'
