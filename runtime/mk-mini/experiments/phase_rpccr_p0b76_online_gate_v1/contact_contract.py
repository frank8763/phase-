"""B71 evaluation-only contact contract. Never calls any simulation/control API.

Input model/data are read only. Output streams and counters belong to this
observer, never to an environment. Geometric truth must not feed a planner.
"""
from __future__ import annotations

from collections import Counter
import gzip
import hashlib
import json
import re
import xml.etree.ElementTree as ET


class ClassificationError(RuntimeError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


class GeometryCatalog:
    def __init__(self, model, mj, isolated_xml):
        self.model, self.mj = model, mj
        world = ET.parse(isolated_xml).getroot().find('worldbody')
        xml_root = world.find("body[@name='mkmini_base']")
        root = mj.mj_name2id(model, mj.mjtObj.mjOBJ_BODY, 'mkmini_base')
        if xml_root is None or xml_root.find('freejoint') is None or root < 1:
            raise ClassificationError('XML/model robot root or freejoint missing')
        if int(model.body_parentid[root]) != 0:
            raise ClassificationError('Robot root is not a direct world child')
        joints = range(int(model.body_jntadr[root]), int(model.body_jntadr[root]+model.body_jntnum[root]))
        if not any(int(model.jnt_type[j]) == int(mj.mjtJoint.mjJNT_FREE) for j in joints):
            raise ClassificationError('Robot root has no actual free joint')
        self.robot_bodies = set()
        for body in range(1, model.nbody):
            parent = body
            while parent and parent != root:
                parent = int(model.body_parentid[parent])
            if parent == root:
                self.robot_bodies.add(body)
        self.root_body_id = root
        # These are direct world geoms in the exact, hash-checked generated XML.
        # The generator in MkMiniRealIndoorAStarSACEnv._make_real_indoor_xml
        # creates precisely the rect/box and circle/cylinder families below.
        declarations = {}
        for tag in world.findall('geom'):
            name = tag.get('name')
            gid = mj.mj_name2id(model, mj.mjtObj.mjOBJ_GEOM, name) if name else -1
            if gid < 0:
                raise ClassificationError('Declared world geom absent in compiled model: '+str(name))
            if int(model.geom_bodyid[gid]) != 0:
                raise ClassificationError('Declared world geom attached to non-world body')
            kind = int(model.geom_type[gid])
            basis = {'xml': str(isolated_xml), 'xml_attachment': 'worldbody/direct_geom',
                     'declared_type': tag.get('type'), 'actual_body_id': 0}
            if name == 'floor' and tag.get('type') == 'plane' and kind == int(mj.mjtGeom.mjGEOM_PLANE):
                if any(abs(float(v)) > 1e-12 for v in model.geom_pos[gid]) or any(
                        abs(float(a)-b) > 1e-12 for a,b in zip(model.geom_quat[gid], (1,0,0,0))):
                    raise ClassificationError('Declared support plane is not horizontal at z=0')
                declarations[gid] = ('support', dict(basis, reason='verified horizontal world support plane'))
            elif (re.fullmatch(r'real_rect_obs_\d+', name or '') and tag.get('type') == 'box'
                  and kind == int(mj.mjtGeom.mjGEOM_BOX)) or (
                  re.fullmatch(r'real_circle_obs_\d+', name or '') and tag.get('type') == 'cylinder'
                  and kind == int(mj.mjtGeom.mjGEOM_CYLINDER)):
                declarations[gid] = ('obstacle', dict(basis,
                    reason='environment generator declaration + compiled world attachment/type',
                    construction='training/envs/mkmini_real_indoor_astar_sac_env.py::_make_real_indoor_xml',
                    activation='Phase19::_phase19_activate_geom (evaluation-only, hidden included)'))
        self.entries = []
        for gid in range(model.ngeom):
            body = int(model.geom_bodyid[gid])
            if body in self.robot_bodies:
                category, basis = 'robot', {'reason': 'geom_bodyid in verified free-root body subtree',
                                           'root_body_id': root, 'body_id': body}
            else:
                category, basis = declarations.get(gid, ('unknown', {'reason': 'no verified subtree or world declaration'}))
            self.entries.append({'geom_id': gid,
                'geom_name': mj.mj_id2name(model, mj.mjtObj.mjOBJ_GEOM, gid),
                'body_id': body, 'body_name': mj.mj_id2name(model, mj.mjtObj.mjOBJ_BODY, body),
                'geom_type': int(model.geom_type[gid]), 'category': category,
                'contype': int(model.geom_contype[gid]), 'conaffinity': int(model.geom_conaffinity[gid]),
                'classification_basis': basis})
        unknown_active = [e for e in self.entries if e['category'] == 'unknown' and (e['contype'] or e['conaffinity'])]
        if unknown_active:
            raise ClassificationError('Unclassified collision-enabled geoms: '+canonical(unknown_active))
        if not any(e['category'] == 'robot' and (e['contype'] or e['conaffinity']) for e in self.entries):
            raise ClassificationError('No collision-enabled robot geometry')

    def classify(self, contact, physics_step, public_step, sim_time):
        a, b = int(contact.geom1), int(contact.geom2)
        if min(a,b) < 0 or max(a,b) >= len(self.entries):
            raise ClassificationError('Unsupported contact geom IDs')
        ea, eb = self.entries[a], self.entries[b]
        pair = {ea['category'], eb['category']}
        distance = float(contact.dist)
        penetration = distance < 0.0
        if pair == {'robot', 'obstacle'}:
            kind = 'robot_obstacle_penetration' if penetration else 'robot_obstacle_contact'
        elif ea['category'] == eb['category'] == 'robot':
            kind = 'robot_self_contact'
        elif pair == {'robot', 'support'}:
            kind = 'ground_support'
        else:
            kind = 'unknown_contact'
        return {'physics_step': physics_step, 'public_step': public_step, 'sim_time': sim_time,
                'geom1_id': a, 'geom2_id': b, 'body1_id': ea['body_id'], 'body2_id': eb['body_id'],
                'geom1_name': ea['geom_name'], 'geom2_name': eb['geom_name'],
                'contact_distance': distance, 'negative_distance_penetration': penetration,
                'contact_type': kind, 'position': [float(x) for x in contact.pos],
                'classification_basis': {'geom1': ea['classification_basis'], 'geom2': eb['classification_basis']}}

    def audit(self):
        return {'root_body_id': self.root_body_id, 'robot_body_ids': sorted(self.robot_bodies),
                'category_counts': dict(Counter(e['category'] for e in self.entries)), 'geoms': self.entries}


class ContactRecorder:
    def __init__(self, catalog, output_dir):
        self.catalog = catalog
        self.events = gzip.open(output_dir/'contacts.jsonl.gz', 'xt', encoding='utf-8', compresslevel=5)
        self.steps = gzip.open(output_dir/'physics_steps.jsonl.gz', 'xt', encoding='utf-8', compresslevel=5)
        self.counts, self.negative_counts = Counter(), Counter()
        self.physics_steps = self.contact_records = self.obstacle_steps = self.penetration_steps = 0
        self.minimum_obstacle_distance = None
        self.first_anomaly = None
        self.pairs = set()
        self.contact_hasher = hashlib.sha256()

    def record(self, data, physics_step, public_step):
        self.physics_steps += 1
        if physics_step != self.physics_steps:
            raise RuntimeError('Physical step coverage gap')
        local = Counter()
        unknown = False
        for contact in data.contact:
            row = self.catalog.classify(contact, physics_step, public_step, float(data.time))
            encoded = canonical(row)+'\n'
            self.events.write(encoded)
            self.contact_hasher.update(encoded.encode())
            self.contact_records += 1
            kind = row['contact_type']
            local[kind] += 1
            self.counts[kind] += 1
            if row['negative_distance_penetration']:
                self.negative_counts[kind] += 1
            if kind.startswith('robot_obstacle_'):
                distance = row['contact_distance']
                self.minimum_obstacle_distance = distance if self.minimum_obstacle_distance is None else min(distance, self.minimum_obstacle_distance)
                self.pairs.add(tuple(sorted((row['geom1_id'], row['geom2_id']))))
            if kind.startswith('robot_obstacle_') or kind == 'unknown_contact':
                if self.first_anomaly is None:
                    self.first_anomaly = row
            unknown |= kind == 'unknown_contact'
        self.obstacle_steps += int(any(k.startswith('robot_obstacle_') for k in local))
        self.penetration_steps += int(bool(local['robot_obstacle_penetration']))
        self.steps.write(canonical({'physics_step': physics_step, 'public_step': public_step,
            'sim_time': float(data.time), 'ncon': int(data.ncon), 'counts': dict(local)})+'\n')
        if unknown:
            self.events.flush(); self.steps.flush()
            raise ClassificationError('Unknown contact recorded; stopping affected replay')

    def summary(self):
        return {'physics_steps': self.physics_steps, 'all_contact_records': self.contact_records,
                'contact_type_counts': dict(self.counts), 'negative_distance_counts_all_types': dict(self.negative_counts),
                'robot_obstacle_contact_records': self.counts['robot_obstacle_contact']+self.counts['robot_obstacle_penetration'],
                'robot_obstacle_penetration_records': self.counts['robot_obstacle_penetration'],
                'robot_obstacle_contact_steps': self.obstacle_steps,
                'robot_obstacle_penetration_steps': self.penetration_steps,
                'maximum_obstacle_penetration_depth_m': max(0.0, -(self.minimum_obstacle_distance or 0.0)),
                'minimum_obstacle_distance_m': self.minimum_obstacle_distance,
                'first_anomaly': self.first_anomaly, 'unknown_contact_records': self.counts['unknown_contact'],
                'robot_obstacle_geom_pairs': sorted(self.pairs), 'contact_log_content_sha256': self.contact_hasher.hexdigest()}

    def close(self):
        self.events.close(); self.steps.close()
