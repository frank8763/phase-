import importlib.util,inspect,json,sys
from pathlib import Path
import rclpy
from nav2_msgs.action import NavigateToPose,FollowPath
c=Path(sys.argv[1]);sys.path.insert(0,str(c))
s=importlib.util.spec_from_file_location('qualification_ros_worker',c/'ros_worker.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
assert Path(inspect.getsourcefile(m.authorized)).resolve()==c/'authority.py'
assert (c/'ros_bridge.py').is_file()
print(json.dumps(dict(passed=True,models_initialized=0,nodes_created=0,real_nav2_servers_started=False,actual_installed_ros_imports=True,authority_source=str(c/'authority.py'))))
