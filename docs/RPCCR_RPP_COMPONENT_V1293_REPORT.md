# V1293：新90分钟RPP组件入口失败与V1294零模型修复准备

## 授权与窗口

用户明确选择“启动新的90分钟RPP组件验证（推荐）”。V1293新根2026-11-18T12:48:27.548849+08:00，硬截止14:18:27.548849+08:00，配对monotonic同为5400秒。旧V1290–V1292失败和截止保持。任务固定为原槽1场景/seed10060001/phase1.5107128341898335，从(-4,-2)前进到组件目标(-2.8,-2)，完整200原生停尾，主全门通过才重复；不是原8m整路或固定24比较。

## 实际结果

V1293一次启动driver149075，先真实隔离OSMesa/llvmpipe上下文和当前Adapter零模型入口全部通过。物理进程进入原车辆工厂，产生真实reset模型及零积分启动来源；之后输出路径被冻结的旧写入守卫拒绝，最终COMPLETION于12:48:35.066279闭为OPERATION_STOP_NO_RETRY。没有到达控制器接管或RPP导航阶段。

- bootstrap reset模型构造至少1次，内部MjModel构造总数未知；规范Vehicle对象未完整返回，不能把本轮说成“0模型”。
- 保存的INITIALIZATION_PROVENANCE：reset_calls1、bootstrap_integrations0、initial_time0、旧detour0，确认0启动积分。
- 新导航积分0、自身重放0、训练0；主任务和重复的导航均未执行（NA）。
- 错误日志：`PermissionError: Write outside isolated experiment: .../runs/v1293_rpp_component90/main/APPLIED_JOURNAL.json.tmp`。该finally写入拒绝掩盖了其前的原异常；那个原异常没有保存，准确记为未知。
- 全部子进程已终止，REVIEW_PENDING原字节恢复，执行锁空闲，无后台车辆运行。

这次失败是新运行封装的记录路径与原车辆工厂不一致，不是RPP实际跟踪失败，更不能用于算法比较成功率。原V1281成功不变。

## 原因

冻结的`experiments/v858_nav2_verified/vehicle.py`在初始化context返回后将`context['B'].OUT`设为`runs/v858_nav2_verified`。旧`pilot.py.write_guard`只允许在这个OUT内写入。V1293把原始输出放在`runs/v1293_rpp_component90/main`，与这个工厂合同冲突。零模型模块导入和渲染上下文检查没有覆盖工厂返回后的写入根切换，因此先前软件资格不足以发现它。

## V1294已完成的零模型准备

仅将后续主/重复的原始输出放到`runs/v858_nav2_verified/v1294/`，元数据仍在`runs/v1294_rpp_output_scope/`。两处计入同2GiB预算。旧守卫不禁用、不放宽；控制器、车辆、传感、1.2m路径、停尾、任务顺序、物理安全与重放门不改。另将原异常先打印到捕获日志，避免finally记录失败再次掩盖原因；这只改记录，不改控制。

执行`experiments/v1294_rpp_output_scope/qualify_output.py`，使用原冻结pilot.py中实际write_guard函数，完成6项真实atomic写入/回读及5项越界拒绝：原错误输出根、目录穿越、外部mkdir、外部rename、符号链接写逃逸。11/11通过、0模型/0积分。首个测试在清理测试符号链接时被原守卫拒绝，原失败console保留；修正为父进程不跟随链接清理测试夹具后通过，没有修改旧守卫。所有临时占位文件已经按清单移除，不能误作真实模型/轨迹证据。

新模块真实绑定再次验证当前`V1114 coupled_control.Adapter`及新审批元数据根；MuJoCo/vehicle/torch导入被显式阻止，0模型。6985个冻结源/依赖SHA复核通过。V1294物理启动默认拒绝，必须具备明确ENTRY_CONTINUATION_APPROVAL；没有执行新的初始化或导航。

## 下一步条件

已向用户提交唯一一次“输出入口接续”确认。只有明确批准，且V1293原14:18:27截止余时足够，才沿原双时钟接原两个未执行任务，初始化另记，不新开90分钟；再异常即停。未批准、原截止届满或余时不足均不启动模型。准备完成不等于组件或整路通过。

证据：`runs/v1293_rpp_component90/ENTRY_FAILURE_DIAGNOSIS.json`、原COMPLETION/native.console/INITIALIZATION_PROVENANCE；`runs/v1294_rpp_output_scope/OUTPUT_SCOPE_QUALIFICATION.json`、ENTRY_BINDING_QUALIFICATION、READY_FOR_ENTRY_REVIEW。
