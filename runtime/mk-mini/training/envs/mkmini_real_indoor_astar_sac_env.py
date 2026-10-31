from pathlib import Path
import mujoco

from training.envs.mkmini_indoor_room_astar_sac_env import MkMiniIndoorRoomAStarSACEnv


class MkMiniRealIndoorAStarSACEnv(MkMiniIndoorRoomAStarSACEnv):
    def __init__(self):
        super().__init__()

        self.real_robot_xml = Path(
            "training/assets/mkmini_real/mkmini_mobile_manipulator_v1.xml"
        )
        self.real_indoor_xml = Path(
            "training/assets/mkmini_real/mkmini_mobile_manipulator_indoor_v1.xml"
        )

        self._make_real_indoor_xml()

        self.model = mujoco.MjModel.from_xml_path(str(self.real_indoor_xml))
        self.data = mujoco.MjData(self.model)

        self._sync_mujoco()

    def _make_real_indoor_xml(self):
        text = self.real_robot_xml.read_text()

        obstacle_xml = """
        <!-- indoor room obstacles -->
        """

        for i, (cx, cy, hx, hy) in enumerate(self.rect_obstacles):
            obstacle_xml += f'''
        <geom name="real_rect_obs_{i}"
              type="box"
              pos="{float(cx)} {float(cy)} 0.25"
              size="{float(hx)} {float(hy)} 0.25"
              rgba="0.35 0.25 0.15 1"/>
            '''

        for i, (x, y, r) in enumerate(self.circle_obstacles):
            obstacle_xml += f'''
        <geom name="real_circle_obs_{i}"
              type="cylinder"
              pos="{float(x)} {float(y)} 0.25"
              size="{float(r)} 0.25"
              rgba="0.75 0.05 0.05 1"/>
            '''

        text = text.replace("</worldbody>", obstacle_xml + "\n    </worldbody>")
        self.real_indoor_xml.write_text(text)

    def _sync_mujoco(self):
        self.data.qpos[0] = float(self.robot_xy[0])
        self.data.qpos[1] = float(self.robot_xy[1])
        self.data.qpos[2] = 0.24

        import math
        cy = math.cos(self.robot_yaw * 0.5)
        sy = math.sin(self.robot_yaw * 0.5)

        self.data.qpos[3] = cy
        self.data.qpos[4] = 0.0
        self.data.qpos[5] = 0.0
        self.data.qpos[6] = sy

        if self.model.nu >= 7:
            self.data.ctrl[:7] = 0.0

        mujoco.mj_forward(self.model, self.data)
