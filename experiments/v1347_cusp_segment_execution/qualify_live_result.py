"""Newest-occupancy and unchangedstate admission negatives, no physical models."""
import json
from pathlib import Path
from observed_route import revalidate
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1347_cusp_segment_execution'
def main():
 request=json.loads((C/'SAVED_REAL_REQUEST.json').read_text());result=json.loads((O/'software/actual_planner/result01.json').read_text());path=result['path'];ball=(request['ball'][:2],request['ball'][2]);ok,proof=revalidate(request['known'],path,request['body'],ball,request['guard']);assert ok
 moved=request['body'][:];moved[0]+=.1;assert not revalidate(request['known'],path,moved,ball,request['guard'])[0]
 enlarged=(ball[0],ball[1]+2.);assert not revalidate(request['known'],path,request['body'],enlarged,request['guard'])[0]
 assert not revalidate(request['known'],None,request['body'],ball,request['guard'])[0]
 malformed=path[:];malformed[0]=[float('nan'),0,0,1];assert not revalidate(request['known'],malformed,request['body'],ball,request['guard'])[0]
 summary=dict(passed=True,matching_current_state_and_ball_accepted=True,moved_state_negative_rejected=True,new_occupied_region_negative_rejected=True,no_path_and_nonfinite_negative_rejected=True,validation=proof,models=0,physical_native=0)
 (O/'LIVE_RESULT_QUALIFICATION.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
