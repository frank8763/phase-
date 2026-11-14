"""Fixed unseen suffix from saved actual state; no future observation synthesis."""
from qualify import *


def main():
    assert not (O/'REMAINING_COMPONENT.json').exists()
    assert json.loads((O/'QUALIFICATION.json').read_text())['passed']
    started=time.monotonic();signal.alarm(120)
    root=R/'runs/v858_nav2_verified/v1144/observation_main'
    setup=json.loads((root/'physics/SETUP.json').read_text())
    packet=json.loads((O/'ACTUAL_REFUSAL_PACKET.json').read_text())
    source=json.loads((O/'CAUSAL_SOURCE.json').read_text());tab=np.load(O/'INTERSECTED_TABLE.npz')
    original=json.loads((R/'runs/v1144_saved_entry_relay/software/ROWS.json').read_text())['rows']
    rows=remaining_rows(original,12355)
    reference=np.load(R/'runs/v1144_saved_entry_relay/software/SOURCE.npz')['states'][-1,:3]
    x=dict(setup=setup,packet=packet,source=source,goal=reference[:2].tolist(),safe_terminal_pose=reference.tolist())
    geometry=Geometry(x,{k:tab[k] for k in ['bounds','centers']})
    engine=Engine(setup);states,controls=engine.simulate(initial(packet),rows)
    ps,pu,memory,episodes,active=python_replay(setup,initial(packet),rows)
    difference=max(float(abs(ps-states).max()),float(abs(pu-controls).max()))
    assert difference<=1e-8
    proof,_=geometry.final(x,states,controls,rows)
    from recovery_source import forecast_packet
    backups=[]
    # Matches the fixed worker schedule: 8 while moving, full final stop as one block.
    offset=0;cut=12500-12355;total=sum(r[2] for r in rows)
    while offset<total:
        rest=remaining_rows(rows,offset);first=rest[0]
        take=int(first[2]) if first[3] or offset>=cut else min(8,int(first[2]))
        for end in sorted(set([offset,offset+take])):
            origin=dict(state=ps[end],last_ctrl=memory[end,:4],integral=float(memory[end,4]),coupled_episode=bool(episodes[end]),steering_motion_active=bool(active[end]))
            bs,bu=engine.simulate(origin,[(0.,0.,2200,0)])
            forecast=forecast_packet(packet,ps[end],memory[end],end)
            forecast.update(body_lateral=float(ps[end,4]),coupled_episode=bool(episodes[end]),steering_motion_active=bool(active[end]))
            bp,_=geometry.final(dict(x,packet=forecast,goal=bs[-1,:2].tolist(),safe_terminal_pose=bs[-1,:3].tolist()),bs,bu,[(0.,0.,2200,0)])
            backups.append(dict(native=end,passed=bp['passed'],minimum_raw_m=bp['minimum_raw_m'],terminal_cycle_m=bp['terminal_full_cycle_raw_m'],failed_checks=[k for k,v in bp['checks'].items() if not v]))
        offset+=take
    result=dict(passed=bool(proof['passed'] and all(b['passed'] for b in backups)),scope='unexecuted fixed observation suffix; not original goal arrival',source_sensor_native=source['source_native_tick'],future_measurements_used=0,remaining_native=total,proof=proof,backups=backups,terminal_position_error_m=float(np.linalg.norm(states[-1,:2]-reference[:2])),python_cpp_error=difference,analytical_cpp_native=engine.native,analytical_python_native=total,models=0,physical_native=0,old_failure_unchanged=True,wall_s=time.monotonic()-started)
    dump(O/'REMAINING_COMPONENT.json',result);np.savez_compressed(O/'REMAINING_PREDICTION.npz',states=ps,controls=pu,memory=memory,episodes=episodes,active=active)
    signal.alarm(0);print(encode(result))


if __name__=='__main__':main()
