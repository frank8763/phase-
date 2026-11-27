"""PCBF numerical proposal eligibility; NEVER physical execution authority."""
import math
def admissible(answer):
 return bool(answer.get('passed')and answer.get('original_hard_geometry_passed')and math.isfinite(answer.get('maximum_command_domain_violation',float('inf')))and answer['maximum_command_domain_violation']<=1e-7)
