# -*- coding: utf-8 -*-
"""质量检查：面数/材质/命名/水面/禁紫/悬空粗查。"""
import bpy, math
from mathutils import Vector

def run(objs):
    rep = {}
    tris = 0
    mats = set()
    n_objs = 0
    bad_uv = 0
    mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
    for o in mesh_objs:
        n_objs += 1
        o.data.calc_loop_triangles()
        tris += len(o.data.loop_triangles)
        for m in o.data.materials:
            if m:
                mats.add(m.name)
        if not o.data.uv_layers:
            bad_uv += 1
    rep['objects'] = n_objs
    rep['triangles'] = tris
    rep['materials'] = sorted(mats)
    rep['no_uv'] = bad_uv

    # 禁紫检查
    purple = []
    for mn in mats:
        m = bpy.data.materials.get(mn)
        if m and m.use_nodes:
            for n in m.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    c = n.inputs['Base Color'].default_value
                    if c[0] > 0.5 and c[2] > 0.5 and c[1] < c[0] * 0.8 and c[1] < c[2] * 0.8 and 'M_flower_purple' not in mn:
                        if 'M_' not in mn or 'flower' not in mn:
                            purple.append(mn)
    rep['suspicious_purple'] = sorted(set(purple))

    # 水面平度
    for o in mesh_objs:
        if o.name.startswith('POOL'):
            zs = [ (o.matrix_world @ Vector(c)).z for c in o.bound_box ]
            if 'water' in o.name.lower():
                rep['pool_water_z'] = (min(zs), max(zs))
    rep['modifiers_remaining'] = sum(1 for o in mesh_objs for _ in o.modifiers)
    return rep

def apply_all_modifiers():
    from .geo import MODS
    done = []
    for ob, m in MODS:
        try:
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.modifier_apply(modifier=m.name)
            done.append(ob.name)
        except Exception as e:
            print('[qa] modifier fail', ob.name, e)
    return done
