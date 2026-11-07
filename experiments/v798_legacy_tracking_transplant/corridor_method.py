"""Proposal-only path tracking for finite full-safe compound schedules."""
import numpy as np
from serial_predictor import project_to_segment_path


def metrics(initial_pose, trajectory, path):
    start,_,_=project_to_segment_path(np.asarray(initial_pose).reshape(1,3),path)
    arc,contour,heading=project_to_segment_path(trajectory,path)
    error=abs((trajectory[:,2]-heading+np.pi)%(2*np.pi)-np.pi)
    return dict(arc_progress_m=float(arc[-1]-start[0]),end_arc_m=float(arc[-1]),
                start_arc_m=float(start[0]),terminal_contour_m=float(contour[-1]),
                terminal_heading_rad=float(error[-1]),maximum_contour_m=float(contour.max()))


def score(detail,clearance,self_margin,speed,angular):
    penalty=(100.*max(0.,.155-clearance)+100.*max(0.,.002-self_margin)
             +10.*max(0.,speed-.025)+10.*max(0.,angular-.025))
    return float(8.*detail['arc_progress_m']-5.*detail['terminal_contour_m']
                 -detail['terminal_heading_rad']+.15*min(clearance,.30)-penalty)
