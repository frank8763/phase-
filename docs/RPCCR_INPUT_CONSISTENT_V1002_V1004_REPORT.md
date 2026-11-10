# 原因果输入一致恢复与条件动态实验

状态：NOT_PASSED。停止原因：{'error': "AssertionError('FIRST_DEVELOPMENT_FUNCTION_OR_SAFETY_EVIDENCE_FAILURE')", 'traceback': 'Traceback (most recent call last):\n  File "/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1004_planned_input_navigation/campaign.py", line 62, in main\n    assert task[\'stage\']==\'confirmation\'and row[\'evidence_passed\'],\'FIRST_DEVELOPMENT_FUNCTION_OR_SAFETY_EVIDENCE_FAILURE\'\nAssertionError: FIRST_DEVELOPMENT_FUNCTION_OR_SAFETY_EVIDENCE_FAILURE\n'}

两个原保存恢复状态实际通过，均执行2204新增原生步和完整2秒停车尾。进展分别0.571996510、0.517086897米；最大位置误差0.002478015、0.001282189米，最大航向误差0.001781884、0.000279778弧度；最低实际净空0.273036567米、坏接触0，各自完整状态/控制重放误差0。

前向预测器只由两项旧响应标定，另外两项留出检验通过，不读取未来实测状态；不是全局误差界。整路恢复期间先取消普通Nav2动作，再由唯一控制者执行原因果计划输入，完整停车后交回原目标。此Nav2经验条件合同不是旧328步控制器的保证。

完整整路/重复结果：

- main_we：FAIL；导航原生=0，重放=0

固定24：已执行0，成功0，未执行24；固定重复执行0。未执行全24不报告全分母成功率。旧V828的8执行/6成功不混入。

精确已知分账：`{"component_models": 2, "historical_native": 13897, "component_new_native": 4408, "component_own_replay_native": 18305, "navigation_models": 1, "navigation_native": 0, "navigation_own_replay_native": 0, "private_mujoco_native": 0, "passed_true_t0_initializations": 3}`。未知项：`[]`。未知不填0。

前置窗口18:44:53.884–20:14:53.884保持；条件夜间模型总截止2026-11-11 08:00+08，未延长旧批。首开发功能或安全/源码/证据异常停止所有依赖，不自动修补重跑。软件交接演练为非物理peer，不能冒称新Nav2到达。

当前仅有限单actor声明课程；不宣称任意遮挡、多actor、地图泛化、实时、递归安全或RAS全面优势。训练、SAC、实体机0，Stage隔离。必要证据远端全来源及解压SHA核验后按清单清理；失败保留原始缓存。
