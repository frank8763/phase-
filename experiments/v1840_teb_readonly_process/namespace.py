"""Original native view, three exact private aliases, no child file writer."""
from context import R,O,load,read,sha
PYTHON='/home/linghu/miniconda3/envs/mk_mujoco/bin/python'
ENV='/home/linghu/miniconda3/envs/mk_mujoco'
def command(argv,output):
 n=load('v1739_original_native_namespace',R/'experiments/v1728_teb_final_link_build/namespace.py')
 p=R/'runs/v1728_teb_final_link_build'
 args=n.command(output,p/'view',R/'runs/v1706_noetic_payload_intake/sysroot/opt/ros/noetic',argv)
 # The only process that writes files is the metered parent. The native child
 # receives stdin and returns a bounded pipe; both normally writable binds RO.
 args=['--ro-bind'if x=='--bind'else x for x in args]
 i=args.index('--remount-ro');args[i:i]=['--ro-bind',ENV,ENV,'--ro-bind',str(output/'build/empty_cwd'),str(output/'build/empty_cwd')]
 i=args.index('--chdir');args[i+1]=str(output/'build/empty_cwd')
 for row in read(O/'EXACT_NATIVE_ALIASES.json')['aliases']:
  assert sha(R/row['source'])==row['sha256']and sha(row['target'])==row['original_target_sha256']
  i=args.index('--remount-ro');args[i:i]=['--ro-bind',str(R/row['source']),row['target']]
 for k in range(len(args)-2):
  if args[k:k+2]==['--setenv','LD_LIBRARY_PATH']:args[k+2]='/opt/ros/noetic/lib:/usr/lib/x86_64-linux-gnu:'+str(p/'build/devel/lib')
  if args[k:k+2]==['--setenv','HOME']:args[k+2]=str(output/'build/home')
 i=args.index('--remount-ro');args[i:i]=['--setenv','MUJOCO_GL','osmesa','--setenv','PYOPENGL_PLATFORM','osmesa','--setenv','LIBGL_ALWAYS_SOFTWARE','1','--setenv','NUMEXPR_NUM_THREADS','1']
 return args
