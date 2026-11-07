"""Add only two mechanical assembly exclusions; preserve actual MJB physical arrays."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
PAIRS=[('mkmini_base','left_front_wheel'),('mkmini_base','right_front_wheel')]
ALLOW_ARRAY_SHAPE={'exclude_signature'}

def metadata_field(key):return key.startswith('name_')or key in {'names','names_map'}

def make_xml(original,target,asset_directory):
    tree=ET.parse(original);root=tree.getroot();assert root.find('contact') is None,'UNEXPECTED_EXISTING_CONTACT_SECTION'
    root.find('compiler').set('meshdir',str(asset_directory))
    contact=ET.SubElement(root,'contact')
    for a,b in PAIRS:ET.SubElement(contact,'exclude',body1=a,body2=b)
    tree.write(target,encoding='unicode');return target

def transplant(actual,recompiled):
    records=[];changed=[];struct=[]
    for key in dir(actual):
        if key.startswith('_'):continue
        value=getattr(actual,key)
        if not isinstance(value,np.ndarray):continue
        if metadata_field(key):continue
        other=getattr(recompiled,key)
        if value.shape!=other.shape:
            assert key in ALLOW_ARRAY_SHAPE,'UNEXPECTED_STRUCTURAL_ARRAY_SHAPE:'+key
            struct.append(dict(name=key,old=list(value.shape),new=list(other.shape)));continue
        if key in ALLOW_ARRAY_SHAPE:continue
        if not np.array_equal(value,other):
            assert other.flags.writeable,'NONWRITABLE_ACTUAL_PARAMETER:'+key
            other[:]=value;changed.append(key)
        assert np.array_equal(value,other),'ACTUAL_MODEL_ARRAY_NOT_PRESERVED:'+key
        records.append(dict(name=key,shape=list(value.shape),dtype=str(value.dtype),sha256=hashlib.sha256(value.tobytes()).hexdigest()))
    # Preserve every numerical solver/integrator option, including integer flags.
    options=[]
    for key in dir(actual.opt):
        if key.startswith('_'):continue
        v=getattr(actual.opt,key)
        if isinstance(v,np.ndarray):getattr(recompiled.opt,key)[:]=v;assert np.array_equal(v,getattr(recompiled.opt,key));options.append(key)
        elif isinstance(v,(int,float,np.integer,np.floating)):
            setattr(recompiled.opt,key,v);assert getattr(recompiled.opt,key)==v;options.append(key)
    assert recompiled.nexclude==actual.nexclude+2 and actual.nexclude==0
    for key in ['nq','nv','nu','nbody','njnt','ngeom','npair','nmesh','nactuator','nsensor']:
        if hasattr(actual,key):assert getattr(actual,key)==getattr(recompiled,key),'MODEL_DIMENSION_CHANGED:'+key
    assert not np.any(recompiled.geom_contype!=actual.geom_contype) and not np.any(recompiled.geom_conaffinity!=actual.geom_conaffinity)
    from model_contract import verify_model_interface
    interface=verify_model_interface(actual,recompiled)
    return dict(interface=interface,preserved_array_count=len(records),preserved_arrays=records,xml_actual_parameter_transplants=changed,permitted_structural_shape_changes=struct,preserved_option_fields=options)

def verify_excludes(model,mj):
    pairs=[]
    for a,b in PAIRS:
        i=mj.mj_name2id(model,mj.mjtObj.mjOBJ_BODY,a);j=mj.mj_name2id(model,mj.mjtObj.mjOBJ_BODY,b);assert min(i,j)>0
        pairs.append((min(i,j)<<16)+max(i,j))
    assert sorted(model.exclude_signature.tolist())==sorted(pairs),'EXACT_ASSEMBLY_PAIRS_NOT_PRESERVED'
    return pairs
