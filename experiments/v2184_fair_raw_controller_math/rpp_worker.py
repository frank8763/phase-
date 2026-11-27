"""One admitted upstream RPP raw math call; readonly repo/runs and pipe output."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from context import numerical_admission,R,read,sha

def main():
    a,w,source=numerical_admission()  # Before ctypes/CDLL/controller.
    import ctypes,hashlib,importlib.util,json,math,os,stat,traceback
    calls={};returns={};h=None;lib=None;loaded=0;newmaps={};categories={};error=None;answer={}
    def invoke(name,*args):
        calls[name]=calls.get(name,0)+1;value=getattr(lib,name)(*args);returns[name]=returns.get(name,0)+1;return value
    def maps():
        values={}
        for line in Path('/proc/self/maps').read_text().splitlines():
            cols=line.split(None,5)
            if len(cols)!=6 or not cols[5].startswith('/')or cols[5].endswith(' (deleted)'):continue
            p=Path(cols[5])
            if not p.is_file():continue
            st=p.stat();row=values.setdefault(str(p),dict(sha256=None if str(p).startswith('/dev/shm/')else sha(p),permissions=[],bytes=st.st_size,uid=st.st_uid,regular=stat.S_ISREG(st.st_mode),symlink=p.is_symlink()))
            row['permissions'].append(cols[1])
        return values
    dependency='runs/v1978_rpp_first_common_round/NATIVE_DEPENDENCIES.json'
    assert source[dependency]==sha(R/dependency)
    pins=dict(read(R/dependency)['namespace_ELF_files_SHA256']);binary=R/'runs/v2182_fairness_mechanism_diagnosis/libphase_rpp_raw_core_abi2.so'
    assert source[str(binary.relative_to(R))]==sha(binary);pins[str(binary)]=sha(binary)
    scope_path=R/'experiments/v1963_rpp_nonexecuting_shm_scope/mapping_scope.py';assert source[str(scope_path.relative_to(R))]==sha(scope_path)
    spec=importlib.util.spec_from_file_location('v2184_exact_readonly_mapping_scope',scope_path);scope=importlib.util.module_from_spec(spec);spec.loader.exec_module(scope)
    before=maps()
    def verify_maps():
        nonlocal newmaps,categories
        after=maps();new={n:r for n,r in after.items()if n not in before}
        newmaps=new  # Preserve actual mappings even if the first validation fails.
        for name,row in new.items():
            with Path(name).open('rb')as f:magic=f.read(4)
            categories[name]=scope.classify(name,row,magic,pins,os.getuid())
        newmaps=new
    try:
        z=json.loads(sys.stdin.buffer.read(128*1024+1));assert set(z)=={'request','map','path','common_input_sha256'}
        request=z['request'];m=z['map'];path=z['path']
        from fixture import build,digest
        common,_=build(source)
        assert z['common_input_sha256']==digest(common)and request['body']==common['body']and request['scan']==common['scan']
        assert path==[p[:3]for p in common['local_rear_path']]and m['rear_pose_speed']==common['rear_body']
        assert m['source_request_sha256']==digest(request)and m['source_receipt_packet_sha256']==common['source_packet_sha256']
        assert request['physical_authority']is False and request['native_tick']==0 and m['native_tick']==0
        assert m['width']==m['height']==120 and m['resolution']==.05 and len(m['cells'])==14400
        assert all(type(c)is int and 0<=c<=255 for c in m['cells'])and 2<=len(path)<=10000
        assert all(len(p)==3 and all(math.isfinite(v)for v in p)for p in path)
        assert 'mujoco'not in sys.modules
        lib=ctypes.CDLL(str(binary));loaded=1
        dp=ctypes.POINTER(ctypes.c_double);vp=ctypes.c_void_p;integer=ctypes.c_int
        signatures={'abi_version':([],integer),'request_dimension':([],integer),'create':([],vp),
                    'solve':([vp,ctypes.c_longlong,dp,dp,integer,ctypes.POINTER(ctypes.c_ubyte),integer,integer,ctypes.c_double,ctypes.c_double,ctypes.c_double,dp,integer,dp],integer),
                    'call_count':([vp],ctypes.c_ulonglong),'poisoned':([vp],integer),
                    'error':([ctypes.POINTER(ctypes.c_char),integer],integer),'destroy':([vp],None)}
        for name,(args,restype)in signatures.items():getattr(lib,'phase_rpp_'+name).argtypes=args;getattr(lib,'phase_rpp_'+name).restype=restype
        verify_maps();assert invoke('phase_rpp_abi_version')==2 and invoke('phase_rpp_request_dimension')==5
        h=invoke('phase_rpp_create');verify_maps()
        if not h:
            text=ctypes.create_string_buffer(2048);invoke('phase_rpp_error',text,2048)
            answer['constructor_error']=text.value.decode(errors='replace')
            raise AssertionError('RAW_RPP_CONTROLLER_CONSTRUCTOR_REFUSED')
        d=ctypes.c_double;pose=(d*5)(*m['rear_pose_speed']);pp=(d*(len(path)*3))(*[v for p in path for v in p]);foot=m['footprint_xy'];fp=(d*(len(foot)*2))(*[v for p in foot for v in p]);grid=(ctypes.c_ubyte*14400)(*m['cells']);output=(d*2)(float('nan'),float('nan'))
        code=invoke('phase_rpp_solve',h,0,pose,pp,len(path),grid,120,120,.05,*m['origin'],fp,len(foot),output)
        text=ctypes.create_string_buffer(2048);invoke('phase_rpp_error',text,2048);count=int(invoke('phase_rpp_call_count',h));poison=int(invoke('phase_rpp_poisoned',h));verify_maps()
        answer=dict(native_query_returned=True,returncode=code,raw_twist=[v if math.isfinite(v)else None for v in output],raw_double_bytes_hex=bytes(output).hex(),native_error=text.value.decode(errors='replace'),reported_solver_calls=count,reported_poisoned=poison,common_input_sha256=z['common_input_sha256'],native_ROS_clock_is_math_TF_only_not_reticked_physical_packet=True)
    except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        if h:
            try:invoke('phase_rpp_destroy',h)
            except BaseException as e:
                if error is None:error=dict(error=repr(e),stage='native_destroy')
                else:answer['secondary_destroy_error']=repr(e)
        # Every ELF SHA is checked above against the immutable source pins.
        # Store the actual path set and non-ELF identities without redundantly
        # copying the same147SHA strings into the pipe and final result.
        elf_paths=[];nonelf={}
        for name,row in newmaps.items():
            if categories.get(name)=='exact_SHA_ELF':elf_paths.append(name)
            else:nonelf[name]=row
        mapping_raw=json.dumps(newmaps,sort_keys=True,separators=(',',':')).encode()
        result=dict(closed=True,method='RPP_RAW_ABI2',answer=answer,first_error=error,explicit_DLL_loads=loaded,FFI_call_attempts=calls,FFI_call_returns=returns,constructor_handle_returned=bool(h),actual_new_ELF_paths=sorted(elf_paths),actual_nonELF_middleware_mappings=nonelf,full_mapping_record_SHA256=hashlib.sha256(mapping_raw).hexdigest(),all_internal_native_work_unknown=True,original_plant_factory_calls=0,original_physics_steps=0,physical_authority=False)
        print('V2184_RPP_RESULT '+json.dumps(result,allow_nan=False),flush=True)
    return 0 if error is None else 1
if __name__=='__main__':raise SystemExit(main())
