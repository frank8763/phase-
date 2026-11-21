# V1426 模型peer完整退出证据

V1425内层namespace/current input握手与真实RPP callback已通过，但close_event在STOP后立即TERM外层bwrap，未保存PEER_RESULT/controller_exited；该证据缺口单独保留，不把wrapper退出当全子进程已核。旧V1424失败与V1425窄资格不重跑。

新EventPeer只改进程关闭：发原STOP后最多8s等原PEER_RESULT.closed/controller_exited及监督进程退出，超时有限TERM/KILL并准确拒绝完整退出资格。初始namespace wrapper与原RPP字节不改，修订5，0模型/积分/物理/实际replay。一次新run_phase CPU2/单锁、CPU3实际ROS callback+完整关闭，60s总cap；保存所有原source/回复/握手/close，首错后闭资格不重启。实际route/完整集成审核/90min预算/supervisor依然未准入。
