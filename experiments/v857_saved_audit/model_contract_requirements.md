# 后续模型资格必须补的前置接口门（设计，未运行新模型）

V857的数组保持检查复制了name_actuatoradr，但没有复制names_map（后者因新exclude从214变218）。多数数值数组相同不等于对象名称查找和结构元数据一致；当前ACTUATOR_LIMITS_REQUIRED发生在修正模型首积分前，不能解释成真实转向/轮速执行不合格。

未来构建器应把名称/地址/哈希等结构元数据与物理参数分开：让编译器按同一套名字生成完整结构，不直接移植部分name_*。逐个独立核验原/新body、joint、geom、actuator名称与ID映射，特别是四驱动器唯一名称、transmission joint ID、ctrl limited/范围、forcerange、gain/bias、armature/damping、时间步/solver；控制映射Adapter必须在任何重放或分支积分前成功构造，并与原实际SETUP指明的ID一致。

必要证据不能只是一份布尔JSON：保存原/新name→ID→joint/ctrlrange表并由另一只读实现比对；加入一个伪造name_actuatoradr或错actuator ID的负例，确认门能失败。然后才是碰撞清单/原控制重放/修正模型同控制对照/闭环响应。这里不修改旧冻结模型源，不加载或积分新模型，不授权第二接口接续。

依据：[MuJoCo3.9.0 engine_name.c](https://raw.githubusercontent.com/google-deepmind/mujoco/3.9.0/src/engine/engine_name.c)：名称查询同时依赖名称缓冲区、类型对应地址数组及names_map；不是只看控制范围数组。
