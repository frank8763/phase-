"""Reuse the built material view; isolate native solver libraries from the engine."""
from context import R,C,O,load
PYTHON='/home/linghu/miniconda3/envs/mk_mujoco/bin/python'
ENV='/home/linghu/miniconda3/envs/mk_mujoco'
def command(argv):
 n=load('v1732_unchanged_build_namespace',R/'experiments/v1728_teb_final_link_build/namespace.py')
 p=R/'runs/v1728_teb_final_link_build';args=n.command(O,p/'view',R/'runs/v1706_noetic_payload_intake/sysroot/opt/ros/noetic',argv)
 # Add binds before the final remounts and command.
 i=args.index('--remount-ro');args[i:i]=['--ro-bind',ENV,ENV,'--ro-bind',str(O/'build/empty_cwd'),str(O/'build/empty_cwd')]
 i=args.index('--chdir');args[i+1]=str(O/'build/empty_cwd')
 for k in range(len(args)-2):
  if args[k:k+2]==['--setenv','LD_LIBRARY_PATH']:args[k+2]='/opt/ros/noetic/lib:/usr/lib/x86_64-linux-gnu:'+str(p/'build/devel/lib')
  if args[k:k+2]==['--setenv','HOME']:args[k+2]=str(O/'build/home')
 i=args.index('--remount-ro');args[i:i]=['--setenv','MUJOCO_GL','osmesa','--setenv','PYOPENGL_PLATFORM','osmesa','--setenv','LIBGL_ALWAYS_SOFTWARE','1','--setenv','NUMEXPR_NUM_THREADS','1']
 return args
