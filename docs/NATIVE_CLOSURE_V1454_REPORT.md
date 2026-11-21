# V1454 原始零尾、实际控制重算及完整重放

一次有限资格实际通过并关闭：规范工厂完整返回1，内部构造次数未知；原始本地零请求200步、实际控制compute200、独立actual-source Allocator重算200、ownreplay200。控制memory与control误差0，完整qpos/qvel/ctrl/mocap重放最大误差0，接触不一致0。N=200/N+1=201状态与初始状态加原实际trace逐项位相同，全部200原始owner行receipt完整。最低实际footprint clearance0.314989181941m，自体余量0.009944851725m，无不良接触。

原V1451保存失败保留，不重跑。新版本只把两个确切gzip输出改为底层仍受WriteProxy逐字节收费的二进制fileobj文本适配，raw descriptor仍禁止；先保存Nplus1状态，再保存接触，关闭不重复尝试失败capture。实际全流程无首错/次错，源未变，Mesa native cache不存在，原REVIEW SHA恢复、锁空闲。

准确来源例外：原协议“无scan”表述过宽。未变的canonical factory通过V945 physical.create_vehicle执行两次真实t0 reference/candidate扫描，保存在SENSORS；并非0总扫描。没有导航wire、合成扫描或200零尾过程中新扫描。完整保存这两行及其来源，不把它们删除或称作未执行。

此资格只验证原t0本地零控制收尾、保存、原实际状态Allocator与自身重放路径。它未验证非零、跨模式event/current reserve、完整生产route生命周期或独立整路repeat。原WE整路0，完整route准入仍不存在。

父账actual116280/ownreplay105105，vehicle_task_starts12是任务启动尝试，科学修订5。新资格actual200/replay200/Allocator200另栏保持，与旧失败和组件分母分开。
