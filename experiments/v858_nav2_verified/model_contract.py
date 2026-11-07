"""Semantic model-object contract independent of raw name-buffer addresses."""
import numpy as np

def verify_table(rows,expected_ids):
    assert len(rows)==4 and len({r['new_id']for r in rows})==4,'DRIVER_IDS_NOT_UNIQUE'
    for r,want in zip(rows,expected_ids):
        assert r['new_id']==r['old_id']==want and want>=0,'DRIVER_NAME_ID_MISMATCH'
        assert r['new_limited']and r['old_limited'],'DRIVER_LIMIT_FLAG_CHANGED'
        for key in ['joint_id','trntype','range','force_range','gain','bias']:
            assert r['new_'+key]==r['old_'+key],'DRIVER_CONTRACT_CHANGED:'+key
    return True

def verify_model_interface(old,new):
    import mujoco as mj
    names=['left_front_steer_act','right_front_steer_act','left_rear_wheel_act','right_rear_wheel_act'];rows=[];expected=[]
    for name in names:
        i=mj.mj_name2id(old,mj.mjtObj.mjOBJ_ACTUATOR,name);j=mj.mj_name2id(new,mj.mjtObj.mjOBJ_ACTUATOR,name);assert i>=0 and j>=0,'DRIVER_LOOKUP_FAILED:'+name
        row=dict(name=name,old_id=int(i),new_id=int(j));expected.append(int(i))
        for label,m,idx in [('old',old,i),('new',new,j)]:
            row[label+'_limited']=bool(m.actuator_ctrllimited[idx]);row[label+'_joint_id']=m.actuator_trnid[idx].tolist();row[label+'_trntype']=int(m.actuator_trntype[idx]);row[label+'_range']=m.actuator_ctrlrange[idx].tolist();row[label+'_force_range']=m.actuator_forcerange[idx].tolist();row[label+'_gain']=m.actuator_gainprm[idx].tolist();row[label+'_bias']=m.actuator_biasprm[idx].tolist()
        rows.append(row)
    verify_table(rows,expected);identity=[]
    for kind,count in [(mj.mjtObj.mjOBJ_BODY,old.nbody),(mj.mjtObj.mjOBJ_JOINT,old.njnt),(mj.mjtObj.mjOBJ_GEOM,old.ngeom)]:
        for i in range(count):
            a=mj.mj_id2name(old,kind,i);b=mj.mj_id2name(new,kind,i);assert a==b,'OBJECT_NAME_OR_ID_CHANGED'
            if a:assert mj.mj_name2id(new,kind,a)==i,'BIDIRECTIONAL_OBJECT_LOOKUP_FAILED'
        identity.append(dict(kind=int(kind),objects=count,all_names_and_ids_equal=True))
    return dict(passed=True,drivers=rows,object_identity=identity,compiler_metadata_retained=True)
