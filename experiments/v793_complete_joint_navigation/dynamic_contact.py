"""Extend the frozen evaluator only for one explicitly declared mocap obstacle."""
from pathlib import Path
import xml.etree.ElementTree as ET
from contact_contract import GeometryCatalog as StaticCatalog,ContactRecorder

class GeometryCatalog(StaticCatalog):
    def __init__(self,m,mj,xml):
        gid=mj.mj_name2id(m,mj.mjtObj.mjOBJ_GEOM,'real_circle_obs_10')
        bid=mj.mj_name2id(m,mj.mjtObj.mjOBJ_BODY,'phase_dynamic_actor')
        declaration=ET.parse(xml).getroot().find("worldbody/body[@name='phase_dynamic_actor']/geom[@name='real_circle_obs_10']")
        assert declaration is not None and int(m.geom_bodyid[gid])==bid and int(m.body_mocapid[bid])>=0
        saved=(int(m.geom_contype[gid]),int(m.geom_conaffinity[gid]));m.geom_contype[gid]=0;m.geom_conaffinity[gid]=0
        try:super().__init__(m,mj,xml)
        finally:m.geom_contype[gid],m.geom_conaffinity[gid]=saved
        assert bid not in self.robot_bodies
        self.entries[gid].update(category='obstacle',contype=saved[0],conaffinity=saved[1],
            classification_basis={'reason':'verified declared mocap actor, outside robot subtree','xml':str(xml),
                                  'xml_attachment':'worldbody/phase_dynamic_actor/geom','body_id':bid,'mocap_id':int(m.body_mocapid[bid])})
