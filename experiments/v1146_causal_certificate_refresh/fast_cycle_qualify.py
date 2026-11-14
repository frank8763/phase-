"""Actual refusal differential and bounded warm certificate benchmark."""
from qualify import *
from fast_cycle import certify

if __name__=='__main__':
    assert not (O/'FAST_CYCLE_QUALIFICATION.json').exists()
    packet=json.loads((O/'ACTUAL_REFUSAL_PACKET.json').read_text())
    source=json.loads((O/'CAUSAL_SOURCE.json').read_text())
    setup=json.loads((R/'runs/v858_nav2_verified/v1144/observation_main/physics/SETUP.json').read_text())
    old=json.loads((R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/COUPLED_ENTRY.json').read_text())
    rows=json.loads((R/'runs/v1144_saved_entry_relay/software/ROWS.json').read_text())['rows']
    rest=remaining_rows(rows,12355);block=[];left=8
    for t,v,n,m in rest:
        take=min(left,int(n));block.append((t,v,take,m));left-=take
        if not left:break
    schedule=block+[(0.,0.,2200,0)]
    engine=Engine(setup);states,controls=engine.simulate(initial(packet),schedule)
    x=dict(setup=setup,packet=packet,source=source,goal=states[-1,:2].tolist(),safe_terminal_pose=states[-1,:3].tolist())
    red=certify(dict(x,source=old['source']),states,controls,schedule)
    green=certify(x,states,controls,schedule)
    assert not red['passed'] and green['passed']
    wall=[]
    for _ in range(30):
        start=time.perf_counter();proof=certify(x,states,controls,schedule);wall.append(time.perf_counter()-start)
        assert proof['passed'] and proof['states_sha256']==green['states_sha256']
    dump(O/'FAST_CYCLE_QUALIFICATION.json',dict(passed=True,old=red,refreshed=green,phase_LPs=0,warm_calls=30,certificate_wall_median_s=float(np.median(wall)),certificate_wall_max_s=max(wall),benchmark_excludes_estimator_io_and_vehicle=True,not_end_to_end_real_time_proof=True,analytical_cpp_native=engine.native,analytical_python_native=0,models=0,physical_native=0))
