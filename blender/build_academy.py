# -*- coding: utf-8 -*-
"""
星槎学院 · 船岛
一条没接住星的船，八百年里长成了学府。
运行： blender --background --factory-startup --python blender/build_academy.py
"""
import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
random.seed(412)
_seq = 0


def uid(prefix):
    global _seq
    _seq += 1
    return "%s_%03d" % (prefix, _seq)


# ---------------------------------------------------------------------------
# scene
# ---------------------------------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.context.preferences.edit.undo_steps = 0
    except Exception:
        pass
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0


def set_active(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def apply_scale(obj):
    set_active(obj)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


def shade(obj, angle=45):
    set_active(obj)
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))
    except Exception:
        bpy.ops.object.shade_smooth()


def bevel(obj, width=0.07, segments=2, angle=40):
    m = obj.modifiers.new("Bev", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    m.affect = "EDGES"
    return m


def parent_keep(child, parent):
    mw = child.matrix_world.copy()
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()
    child.matrix_world = mw


def join(name, objs, mat=None):
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    if len(objs) == 1:
        objs[0].name = name
        return objs[0]
    set_active(objs[0])
    for o in objs:
        o.select_set(True)
    bpy.ops.object.join()
    objs[0].name = name
    if mat:
        objs[0].data.materials.clear()
        objs[0].data.materials.append(mat)
    return objs[0]


# ---------------------------------------------------------------------------
# materials (Blender 4.x Principled)
# ---------------------------------------------------------------------------
def _set(bsdf, names, value):
    for n in names:
        if n in bsdf.inputs:
            sock = bsdf.inputs[n]
            try:
                sock.default_value = value
                return True
            except Exception:
                try:
                    if hasattr(value, "__len__") and len(sock.default_value) == 4 and len(value) == 3:
                        sock.default_value = (*value, 1.0)
                        return True
                except Exception:
                    pass
    return False


def make_mat(name, color, roughness=0.65, metallic=0.0, emission=None, e_strength=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    col = (float(color[0]), float(color[1]), float(color[2]), 1.0)
    _set(bsdf, ["Base Color"], col)
    _set(bsdf, ["Roughness"], float(roughness))
    _set(bsdf, ["Metallic", "Metalness"], float(metallic))
    _set(bsdf, ["Alpha"], float(alpha))
    m.diffuse_color = col
    if emission is not None:
        ecol = (float(emission[0]), float(emission[1]), float(emission[2]), 1.0)
        _set(bsdf, ["Emission Color", "Emission"], ecol)
        _set(bsdf, ["Emission Strength"], float(e_strength))
        # workbench / viewport
        m.diffuse_color = (min(1, color[0] + 0.15), min(1, color[1] + 0.1), min(1, color[2]), 1.0)
    if alpha < 0.999:
        try:
            m.blend_method = "BLEND"
        except Exception:
            pass
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
    return m


class M:
    pass


def build_materials():
    M.limestone = make_mat("Limestone", (0.78, 0.72, 0.62), 0.78, 0.0)
    M.limestone_warm = make_mat("LimestoneWarm", (0.82, 0.74, 0.58), 0.72, 0.0)
    M.stone_grey = make_mat("StoneGrey", (0.52, 0.50, 0.47), 0.85, 0.0)
    M.stone_dark = make_mat("StoneDark", (0.28, 0.26, 0.24), 0.88, 0.0)
    M.rock = make_mat("Rock", (0.34, 0.31, 0.28), 0.95, 0.0)
    M.rock_deep = make_mat("RockDeep", (0.22, 0.20, 0.19), 1.0, 0.0)
    M.grass = make_mat("Grass", (0.27, 0.38, 0.20), 0.92, 0.0)
    M.moss = make_mat("Moss", (0.22, 0.34, 0.18), 1.0, 0.0)
    M.wood = make_mat("Wood", (0.38, 0.24, 0.13), 0.82, 0.02)
    M.wood_dark = make_mat("WoodDark", (0.22, 0.14, 0.08), 0.86, 0.0)
    M.copper = make_mat("Copper", (0.72, 0.38, 0.16), 0.32, 0.85)
    M.copper_old = make_mat("CopperOld", (0.55, 0.32, 0.16), 0.45, 0.7)
    M.patina = make_mat("Patina", (0.22, 0.46, 0.36), 0.48, 0.55)
    M.gold = make_mat("Gold", (0.83, 0.62, 0.22), 0.28, 0.9)
    M.gold_dim = make_mat("GoldDim", (0.62, 0.46, 0.18), 0.4, 0.75)
    M.iron = make_mat("Iron", (0.18, 0.18, 0.2), 0.42, 0.78)
    M.tile_teal = make_mat("TileTeal", (0.22, 0.42, 0.46), 0.55, 0.15)
    M.tile_blue = make_mat("TileBlue", (0.18, 0.34, 0.48), 0.5, 0.1)
    M.roof_dawn = make_mat("RoofDawn", (0.78, 0.52, 0.18), 0.38, 0.55)
    M.roof_speak = make_mat("RoofSpeak", (0.18, 0.42, 0.30), 0.42, 0.5)
    M.roof_forge = make_mat("RoofForge", (0.48, 0.22, 0.12), 0.5, 0.45)
    M.roof_tide = make_mat("RoofTide", (0.20, 0.40, 0.52), 0.48, 0.25)
    M.pave = make_mat("Pave", (0.58, 0.54, 0.46), 0.9, 0.0)
    M.pave_dark = make_mat("PaveDark", (0.42, 0.39, 0.34), 0.92, 0.0)
    M.water = make_mat("PoolWater", (0.12, 0.38, 0.48), 0.08, 0.15,
                       emission=(0.10, 0.42, 0.55), e_strength=0.45, alpha=0.78)
    M.crystal = make_mat("Crystal", (0.55, 0.90, 1.0), 0.12, 0.05,
                         emission=(0.35, 0.85, 1.0), e_strength=6.5)
    M.win_warm = make_mat("WinWarm", (1.0, 0.78, 0.42), 0.25, 0.0,
                          emission=(1.0, 0.72, 0.35), e_strength=4.2)
    M.win_green = make_mat("WinGreen", (0.45, 0.85, 0.55), 0.25, 0.0,
                           emission=(0.3, 0.8, 0.45), e_strength=3.4)
    M.win_ember = make_mat("WinEmber", (1.0, 0.45, 0.15), 0.3, 0.0,
                           emission=(1.0, 0.35, 0.08), e_strength=5.0)
    M.win_blue = make_mat("WinBlue", (0.4, 0.75, 1.0), 0.22, 0.0,
                          emission=(0.25, 0.65, 1.0), e_strength=3.8)
    M.win_cyan = make_mat("WinCyan", (0.6, 0.92, 1.0), 0.18, 0.0,
                          emission=(0.4, 0.9, 1.0), e_strength=5.5)
    M.banner_d = make_mat("BanDawn", (0.85, 0.62, 0.22), 0.7, 0.05,
                          emission=(0.7, 0.45, 0.1), e_strength=0.35)
    M.banner_s = make_mat("BanSpeak", (0.18, 0.48, 0.32), 0.7, 0.0,
                          emission=(0.1, 0.4, 0.22), e_strength=0.3)
    M.banner_f = make_mat("BanForge", (0.62, 0.28, 0.14), 0.7, 0.05,
                          emission=(0.5, 0.15, 0.05), e_strength=0.3)
    M.banner_t = make_mat("BanTide", (0.18, 0.42, 0.58), 0.7, 0.0,
                          emission=(0.1, 0.3, 0.5), e_strength=0.3)
    M.leaf = make_mat("Leaf", (0.18, 0.42, 0.16), 0.85, 0.0)
    M.leaf_old = make_mat("LeafOld", (0.32, 0.40, 0.14), 0.88, 0.0)
    M.chain = make_mat("ChainLight", (0.45, 0.85, 1.0), 0.2, 0.15,
                       emission=(0.3, 0.8, 1.0), e_strength=2.8)
    M.ember = make_mat("Ember", (1.0, 0.35, 0.08), 0.4, 0.0,
                       emission=(1.0, 0.25, 0.05), e_strength=8.0)
    M.soil = make_mat("Soil", (0.28, 0.22, 0.14), 1.0, 0.0)


# ---------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------
def cube(name, size, loc, rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    apply_scale(obj)
    if mat:
        obj.data.materials.append(mat)
    return obj


def cyl(name, radius, depth, loc, rot=(0, 0, 0), verts=12, mat=None):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot
    )
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    return obj


def cone(name, radius1, depth, loc, rot=(0, 0, 0), verts=8, mat=None, radius2=0.0):
    bpy.ops.mesh.primitive_cone_add(
        vertices=verts, radius1=radius1, radius2=radius2, depth=depth,
        location=loc, rotation=rot
    )
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    return obj


def ico(name, radius, loc, subdiv=1, mat=None):
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=subdiv, radius=radius, location=loc
    )
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    return obj


def uvsp(name, radius, loc, segs=12, rings=8, mat=None):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segs, ring_count=rings, radius=radius, location=loc
    )
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    return obj


def mesh_obj(name, verts, faces, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    obj = bpy.data.objects.new(name, me)
    obj.location = loc
    obj.rotation_euler = rot
    bpy.context.collection.objects.link(obj)
    if mat:
        obj.data.materials.append(mat)
    return obj


def empty(name, loc=(0, 0, 0)):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 1.2
    obj.location = loc
    bpy.context.collection.objects.link(obj)
    return obj


def gable_roof(name, length, width, height, loc, rot=(0, 0, 0), mat=None):
    l, w, h = length * 0.5, width * 0.5, height
    verts = [
        (-l, -w, 0), (l, -w, 0), (l, w, 0), (-l, w, 0),
        (-l, 0, h), (l, 0, h),
    ]
    faces = [(0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5), (0, 3, 2, 1)]
    return mesh_obj(name, verts, faces, loc, rot, mat)


def hip_roof(name, length, width, height, loc, rot=(0, 0, 0), mat=None, ridge=0.35):
    l, w, h = length * 0.5, width * 0.5, height
    rl = max(0.15, l * ridge)
    verts = [
        (-l, -w, 0), (l, -w, 0), (l, w, 0), (-l, w, 0),
        (-rl, 0, h), (rl, 0, h),
    ]
    faces = [(0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4), (0, 3, 2, 1)]
    return mesh_obj(name, verts, faces, loc, rot, mat)


def displace(obj, amount, scale, seed, z_only=False, z_mul=1.0):
    me = obj.data
    for v in me.vertices:
        x, y, z = v.co
        n = math.sin((x + seed) * 12.9898 * scale + (y - seed) * 78.233 * scale) * 43758.5453
        n = n - math.floor(n)
        n2 = math.sin((y + seed) * 39.17 * scale + (z + seed) * 11.3 * scale) * 23381.13
        n2 = n2 - math.floor(n2)
        dx = (n - 0.5) * amount
        dy = (n2 - 0.5) * amount
        dz = (n + n2 - 1.0) * amount * 0.45 * z_mul
        if z_only:
            v.co.z += dz
        else:
            v.co.x += dx
            v.co.y += dy
            v.co.z += dz
    me.update()


# ---------------------------------------------------------------------------
# island / hull — wreck that grew a campus
# ---------------------------------------------------------------------------
def make_island(root):
    click = empty("Click_Island", (0, 0, 0))
    parent_keep(click, root)

    # rock mass around the old hull
    rock = ico("IslandRock", 1.0, (0.0, 0.0, -9.0), subdiv=4, mat=M.rock)
    rock.scale = (46.0, 22.5, 13.5)
    apply_scale(rock)
    # shape into a ship-ish island
    for v in rock.data.vertices:
        x, y, z = v.co
        t = (x + 48.0) / 100.0
        t = min(1.0, max(0.0, t))
        if x > 18:
            k = (x - 18.0) / 42.0
            v.co.y *= max(0.12, 1.0 - 0.88 * k * k)
            v.co.z *= 1.0 - 0.25 * k
        if x < -32:
            k = (-32.0 - x) / 22.0
            v.co.y *= max(0.42, 1.0 - 0.5 * k)
        # flatten anything above deck
        if v.co.z > 0.05:
            v.co.z = 0.05 + (v.co.z - 0.05) * 0.04
        # deepen keel line
        if abs(y) < 4.0 and z < -4:
            v.co.z -= 3.2 * (1.0 - abs(y) / 4.0)
    displace(rock, 1.55, 0.09, 7.3, z_only=False, z_mul=1.55)
    for v in rock.data.vertices:
        if v.co.z > 0.15:
            v.co.z = 0.12
    rock.data.update()
    shade(rock, 55)
    parent_keep(rock, click)

    # darker underside cap
    belly = ico("IslandBelly", 1.0, (2.0, 0.0, -16.5), subdiv=2, mat=M.rock_deep)
    belly.scale = (28.0, 10.5, 9.0)
    apply_scale(belly)
    displace(belly, 1.4, 0.09, 2.2)
    shade(belly, 60)
    parent_keep(belly, click)

    # wooden keel (original ship still visible)
    keel = cube("Keel", (78.0, 1.15, 2.4), (2.0, 0.0, -18.5), mat=M.wood_dark)
    bevel(keel, 0.12, 1)
    parent_keep(keel, click)
    keel2 = cube("KeelFin", (36.0, 0.45, 6.5), (6.0, 0.0, -21.5), mat=M.wood_dark)
    parent_keep(keel2, click)

    # ribs under hull
    ribs = []
    for i, x in enumerate(range(-36, 40, 7)):
        t = (x + 36) / 76.0
        beam = 18.0 - abs(t - 0.5) * 10.0
        if x > 22:
            beam *= max(0.25, 1.0 - (x - 22) / 28.0)
        r = cyl(uid("Rib"), 0.22, beam * 2.15, (x, 0.0, -11.5),
                rot=(math.pi / 2, 0, 0), verts=8, mat=M.wood)
        r.scale = (1.0, 1.0, 1.0)
        # squash into an arch by scaling z and rotating slightly
        r.rotation_euler = (math.pi / 2.15, 0.0, 0.0)
        r.scale = (1.4, 1.0, 1.0)
        apply_scale(r)
        ribs.append(r)
        parent_keep(r, click)

    # prow — original wooden beak
    prow_click = empty("Click_Prow", (48.0, 0.0, 1.0))
    parent_keep(prow_click, root)
    prow = cone("Prow", 3.6, 16.0, (52.0, 0.0, -2.5),
                rot=(0, math.pi / 2.15, 0), verts=7, mat=M.wood)
    shade(prow, 40)
    parent_keep(prow, prow_click)
    prow_tip = cone("ProwTip", 1.4, 8.0, (61.5, 0.0, -1.2),
                    rot=(0, math.pi / 2.05, 0), verts=6, mat=M.wood_dark)
    parent_keep(prow_tip, prow_click)
    # figurehead-ish crystal shard lodged in the prow
    shard = ico("ProwShard", 1.15, (58.5, 0.0, 2.2), subdiv=1, mat=M.crystal)
    shard.scale = (0.5, 0.5, 1.8)
    apply_scale(shard)
    shard.rotation_euler = (0.4, 0.7, 0.2)
    parent_keep(shard, prow_click)
    rail = cube("ProwRail", (10.0, 0.22, 0.35), (46.0, 3.4, 1.6), mat=M.wood)
    parent_keep(rail, prow_click)
    rail2 = cube("ProwRail2", (10.0, 0.22, 0.35), (46.0, -3.4, 1.6), mat=M.wood)
    parent_keep(rail2, prow_click)

    # deck paving — elongated
    deck = cyl("Deck", 1.0, 0.55, (0.0, 0.0, 0.28), verts=24, mat=M.pave)
    deck.scale = (48.0, 21.5, 1.0)
    apply_scale(deck)
    for v in deck.data.vertices:
        if v.co.x > 20:
            k = (v.co.x - 20.0) / 36.0
            v.co.y *= max(0.18, 1.0 - 0.82 * k)
        if v.co.x < -34:
            k = (-34.0 - v.co.x) / 18.0
            v.co.y *= max(0.55, 1.0 - 0.4 * k)
    deck.data.update()
    parent_keep(deck, click)

    grass = cyl("Grass", 1.0, 0.22, (0.0, 0.0, 0.58), verts=24, mat=M.grass)
    grass.scale = (45.5, 20.0, 1.0)
    apply_scale(grass)
    for v in grass.data.vertices:
        if v.co.x > 18:
            k = (v.co.x - 18.0) / 36.0
            v.co.y *= max(0.16, 1.0 - 0.84 * k)
        if v.co.x < -32:
            k = (-32.0 - v.co.x) / 18.0
            v.co.y *= max(0.5, 1.0 - 0.45 * k)
    grass.data.update()
    parent_keep(grass, click)

    # worn stone ring around courtyard (cut a visual plaza)
    plaza = cyl("Plaza", 11.5, 0.18, (0.0, 0.0, 0.68), verts=16, mat=M.pave_dark)
    parent_keep(plaza, click)

    # waterline boulders — break the clay-hull silhouette
    for i in range(14):
        t = i / 13.0
        x = -40.0 + t * 86.0
        side = 1 if i % 2 == 0 else -1
        beam = 18.0 - abs(t - 0.5) * 8.0
        if t > 0.78:
            beam *= max(0.2, 1.0 - (t - 0.78) / 0.22)
        y = side * (beam + 1.4 + (i % 3) * 0.6)
        z = -3.5 - (i * 0.47) % 5.0
        rk = ico(uid("WaterRock"), 1.5 + (i % 4) * 0.35, (x, y, z), subdiv=1, mat=M.rock_deep if i % 3 else M.rock)
        rk.scale = (1.3, 0.85, 1.1)
        apply_scale(rk)
        rk.rotation_euler = (0.4 * i, 0.7 * i, 0.2 * i)
        parent_keep(rk, click)

    # wooden gunwale around midships
    for i in range(16):
        t = i / 15.0
        x = -34.0 + t * 72.0
        beam = 19.5 - abs(t - 0.48) * 6.0
        if t > 0.8:
            beam *= max(0.25, 1.0 - (t - 0.8) / 0.2)
        for side in (1, -1):
            g = cube(uid("Gunwale"), (4.6, 0.22, 0.38), (x, side * beam, 1.15), mat=M.wood_dark)
            parent_keep(g, click)

    # hanging rocks
    for i in range(7):
        a = i / 7.0 * math.pi * 2 + 0.4
        rr = 22.0 + (i % 3) * 6.0
        x = math.cos(a) * rr * 1.35
        y = math.sin(a) * rr * 0.55
        z = -10.0 - (i * 1.7) % 9.0
        rk = ico(uid("HangRock"), 1.3 + (i % 3) * 0.5, (x, y, z), subdiv=1, mat=M.rock)
        rk.scale = (1.0 + 0.4 * (i % 2), 0.7, 1.3)
        apply_scale(rk)
        rk.rotation_euler = (0.3 * i, 0.5 * i, 0.2 * i)
        parent_keep(rk, click)

    # mooring chains of leftover light, dropping toward the rift
    for i, x in enumerate((-22.0, -8.0, 6.0, 20.0)):
        ch = cyl(uid("Chain"), 0.09, 28.0 + (i % 2) * 6, (x, (i - 1.5) * 2.2, -28.0),
                 verts=6, mat=M.chain)
        parent_keep(ch, click)

    return click


# ---------------------------------------------------------------------------
# small vocabulary: windows, banners, lanterns, trees, stairs
# ---------------------------------------------------------------------------
def add_windows(parent, origin, count, span, up, size, mat, axis="x"):
    """Row of emissive window boxes with dark frames."""
    ox, oy, oz = origin
    sx, sy, sz = size
    objs = []
    for i in range(count):
        t = 0 if count == 1 else i / (count - 1) - 0.5
        if axis == "x":
            loc = (ox + t * span, oy, oz + up)
            rot = (0, 0, 0)
            fr = (sx + 0.22, sy + 0.1, sz + 0.28)
        else:
            loc = (ox, oy + t * span, oz + up)
            rot = (0, 0, math.pi / 2)
            fr = (sx + 0.1, sy + 0.22, sz + 0.28)
        frame = cube(uid("WinF"), fr, loc, rot, M.wood_dark)
        parent_keep(frame, parent)
        w = cube(uid("Win"), (sx, sy, sz), loc, rot, mat)
        objs.append(w)
        parent_keep(w, parent)
    return objs


def add_banner(parent, loc, rot, mat, size=(0.15, 1.3, 2.4)):
    pole = cyl(uid("Pole"), 0.07, size[2] + 1.4, (loc[0], loc[1], loc[2] + 0.4), verts=6, mat=M.iron)
    parent_keep(pole, parent)
    cloth = cube(uid("Banner"), size, (loc[0] + 0.7, loc[1], loc[2] + size[2] * 0.15), rot, mat)
    parent_keep(cloth, parent)
    return pole


def add_lantern(parent, loc, mat=None):
    mat = mat or M.win_warm
    pole = cyl(uid("LPole"), 0.06, 2.6, (loc[0], loc[1], loc[2] + 1.3), verts=6, mat=M.iron)
    parent_keep(pole, parent)
    lamp = uvsp(uid("Lamp"), 0.22, (loc[0], loc[1], loc[2] + 2.55), segs=8, rings=6, mat=mat)
    parent_keep(lamp, parent)
    cap = cone(uid("LCap"), 0.28, 0.22, (loc[0], loc[1], loc[2] + 2.78), verts=6, mat=M.copper)
    parent_keep(cap, parent)


def add_tree(parent, loc, scale=1.0, old=False):
    trunk = cyl(uid("Trunk"), 0.22 * scale, 2.2 * scale,
                (loc[0], loc[1], loc[2] + 1.1 * scale), verts=7, mat=M.wood)
    parent_keep(trunk, parent)
    leafmat = M.leaf_old if old else M.leaf
    c1 = ico(uid("Canopy"), 1.35 * scale, (loc[0], loc[1], loc[2] + 2.7 * scale), subdiv=1, mat=leafmat)
    c1.scale = (1.15, 1.05, 0.85)
    apply_scale(c1)
    parent_keep(c1, parent)
    c2 = ico(uid("Canopy2"), 0.95 * scale, (loc[0] + 0.6 * scale, loc[1] - 0.3 * scale, loc[2] + 3.1 * scale),
             subdiv=1, mat=leafmat)
    parent_keep(c2, parent)


def add_buttress(parent, loc, depth, height, rot_z, mat):
    # simple flying-ish buttress: leaning box
    b = cube(uid("Butt"), (0.7, 0.9, height), loc, (0, 0, rot_z), mat)
    b.rotation_euler = (0.0, 0.18, rot_z)
    parent_keep(b, parent)
    cap = cube(uid("ButtCap"), (1.1, 1.1, 0.35),
               (loc[0], loc[1], loc[2] + height * 0.48), (0, 0, rot_z), mat)
    parent_keep(cap, parent)


# ---------------------------------------------------------------------------
# 账桅 — mast wrapped in eight centuries of stone
# ---------------------------------------------------------------------------
def make_tower(root):
    click = empty("Click_Tower", (0.0, 0.0, 0.0))
    parent_keep(click, root)

    # stepped octagonal shaft
    base = cyl("TowerBase", 6.4, 3.2, (0, 0, 1.9), verts=8, mat=M.limestone)
    bevel(base, 0.12, 2)
    parent_keep(base, click)

    shaft = cyl("TowerShaft", 4.6, 18.0, (0, 0, 12.4), verts=8, mat=M.limestone_warm)
    bevel(shaft, 0.1, 2)
    parent_keep(shaft, click)

    mid = cyl("TowerMid", 3.6, 8.5, (0, 0, 25.4), verts=8, mat=M.limestone)
    bevel(mid, 0.08, 2)
    parent_keep(mid, click)

    top = cyl("TowerTop", 2.6, 6.0, (0, 0, 32.4), verts=8, mat=M.limestone_warm)
    parent_keep(top, click)

    # wooden mast still poking through
    mast = cyl("MastWood", 0.55, 9.5, (0, 0, 39.0), verts=8, mat=M.wood_dark)
    parent_keep(mast, click)

    # copper ledger plates — overlapping scales
    plates = []
    rows, cols = 9, 8
    for r in range(rows):
        z = 5.0 + r * 2.05
        rad = 4.75 - r * 0.18
        for c in range(cols):
            a = c / cols * math.pi * 2 + (r % 2) * 0.2
            x = math.cos(a) * rad
            y = math.sin(a) * rad
            pl = cube(uid("Plate"), (1.35, 0.07, 1.7), (x, y, z),
                      (0, 0, a + math.pi / 2), M.copper if (r + c) % 3 else M.copper_old)
            plates.append(pl)
            parent_keep(pl, click)

    # balconies
    for z, rad in ((10.5, 5.3), (21.5, 4.2), (29.8, 3.3)):
        ring = cyl(uid("Balc"), rad, 0.28, (0, 0, z), verts=8, mat=M.stone_grey)
        parent_keep(ring, click)
        rail = cyl(uid("Rail"), rad + 0.15, 0.08, (0, 0, z + 1.05), verts=8, mat=M.iron)
        parent_keep(rail, click)
        for k in range(8):
            a = k / 8 * math.pi * 2
            p = cyl(uid("BalcPost"), 0.07, 1.05,
                    (math.cos(a) * rad, math.sin(a) * rad, z + 0.55), verts=6, mat=M.iron)
            parent_keep(p, click)

    # buttresses
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        x, y = math.cos(a) * 7.2, math.sin(a) * 7.2
        add_buttress(click, (x, y, 5.5), 2.0, 11.0, a, M.limestone)

    # windows
    for z in (8.0, 14.0, 19.5, 26.5):
        for k in range(4):
            a = k * math.pi / 2
            x, y = math.cos(a) * 4.55, math.sin(a) * 4.55
            w = cube(uid("TWin"), (0.7, 0.18, 1.6), (x, y, z), (0, 0, a), M.win_cyan)
            parent_keep(w, click)

    # crystal — the sorting shard
    cry = ico("SortingCrystal", 2.05, (0, 0, 45.2), subdiv=1, mat=M.crystal)
    cry.scale = (0.85, 0.85, 1.65)
    apply_scale(cry)
    parent_keep(cry, click)
    # small orbiting chips
    for i in range(3):
        a = i / 3 * math.pi * 2
        ch = ico(uid("Chip"), 0.35, (math.cos(a) * 2.4, math.sin(a) * 2.4, 45.0 + i * 0.4),
                 subdiv=1, mat=M.crystal)
        parent_keep(ch, click)

    crown = cone("TowerCrown", 3.1, 2.4, (0, 0, 36.4), verts=8, mat=M.gold_dim)
    parent_keep(crown, click)

    # door + stair
    door = cube("TowerDoor", (1.8, 0.25, 3.4), (0, -6.5, 2.4), mat=M.wood_dark)
    parent_keep(door, click)
    arch = cube("TowerArch", (2.4, 0.4, 0.4), (0, -6.5, 4.2), mat=M.gold_dim)
    parent_keep(arch, click)
    for i in range(6):
        st = cube(uid("TowStep"), (3.4 - i * 0.15, 1.15, 0.28),
                  (0, -7.4 - i * 0.55, 0.55 + i * 0.28), mat=M.pave)
        parent_keep(st, click)
    # cornice rings
    for z, rad in ((20.6, 4.9), (29.0, 3.9), (35.4, 2.9)):
        cor = cyl(uid("Cornice"), rad, 0.32, (0, 0, z), verts=8, mat=M.gold_dim)
        parent_keep(cor, click)

    return click


# ---------------------------------------------------------------------------
# 余年盘 courtyard
# ---------------------------------------------------------------------------
def make_yard(root):
    click = empty("Click_Yard", (0.0, 0.0, 0.7))
    parent_keep(click, root)
    dais = cyl("YearDais", 3.4, 0.45, (0, 0, 0.85), verts=16, mat=M.copper_old)
    parent_keep(dais, click)
    disc = cyl("YearDisc", 2.6, 0.18, (0, 0, 1.15), verts=24, mat=M.copper)
    parent_keep(disc, click)
    # ticks
    for i in range(12):
        a = i / 12 * math.pi * 2
        t = cube(uid("Tick"), (0.12, 0.45, 0.12),
                 (math.cos(a) * 2.15, math.sin(a) * 2.15, 1.28),
                 (0, 0, a), M.gold)
        parent_keep(t, click)
    pin = cyl("YearPin", 0.08, 1.1, (0, 0, 1.7), verts=6, mat=M.iron)
    parent_keep(pin, click)
    needle = cube("YearNeedle", (1.7, 0.08, 0.08), (0.55, 0, 2.15), mat=M.gold)
    parent_keep(needle, click)
    return click


# ---------------------------------------------------------------------------
# 晨辉院 — spend it. Bow, open, gold, east-facing colonnade.
# ---------------------------------------------------------------------------
def make_dawn(root):
    click = empty("Click_Dawn", (28.0, 0.0, 0.0))
    parent_keep(click, root)
    ox, oy = 28.0, 0.0

    podium = cube("DawnPodium", (16.0, 14.0, 1.2), (ox, oy, 1.1), mat=M.limestone_warm)
    bevel(podium, 0.1, 2)
    parent_keep(podium, click)

    hall = cube("DawnHall", (11.5, 9.5, 6.4), (ox + 0.5, oy, 4.9), mat=M.limestone_warm)
    bevel(hall, 0.12, 2)
    parent_keep(hall, click)

    roof = hip_roof("DawnRoof", 13.2, 11.0, 4.2, (ox + 0.5, oy, 8.15), mat=M.roof_dawn, ridge=0.4)
    bevel(roof, 0.05, 1)
    parent_keep(roof, click)

    # east colonnade (toward prow / morning)
    for i in range(5):
        y = -4.8 + i * 2.4
        col = cyl(uid("DawnCol"), 0.38, 5.2, (ox + 8.4, y, 4.2), verts=8, mat=M.limestone)
        parent_keep(col, click)
        cap = cube(uid("DawnCap"), (1.0, 1.0, 0.28), (ox + 8.4, y, 6.9), mat=M.gold_dim)
        parent_keep(cap, click)
    entabl = cube("DawnEnt", (1.4, 12.0, 0.5), (ox + 8.4, 0, 7.25), mat=M.limestone_warm)
    parent_keep(entabl, click)

    # wing roofs like two gold pinions
    for side in (1, -1):
        wing = cube(uid("DawnWing"), (6.5, 4.2, 4.0), (ox - 2.0, oy + side * 7.2, 3.6), mat=M.limestone)
        bevel(wing, 0.08, 1)
        parent_keep(wing, click)
        wr = gable_roof(uid("DawnWingRoof"), 7.4, 5.0, 2.6,
                        (ox - 2.0, oy + side * 7.2, 5.65),
                        rot=(0, 0, math.pi / 2), mat=M.gold)
        parent_keep(wr, click)

    # spire
    sp = cyl("DawnSpire", 0.9, 5.5, (ox - 3.2, oy, 10.4), verts=8, mat=M.limestone_warm)
    parent_keep(sp, click)
    spc = cone("DawnSpireCap", 1.4, 3.2, (ox - 3.2, oy, 14.6), verts=8, mat=M.gold)
    parent_keep(spc, click)
    gem = ico("DawnGem", 0.45, (ox - 3.2, oy, 16.5), subdiv=1, mat=M.win_warm)
    parent_keep(gem, click)

    add_windows(click, (ox + 0.5, oy + 4.85, 0), 4, 8.0, 5.2, (1.1, 0.16, 1.7), M.win_warm, axis="x")
    add_windows(click, (ox + 0.5, oy - 4.85, 0), 4, 8.0, 5.2, (1.1, 0.16, 1.7), M.win_warm, axis="x")
    add_windows(click, (ox + 6.3, oy, 0), 3, 6.0, 5.0, (0.16, 1.0, 1.8), M.win_warm, axis="y")

    add_banner(click, (ox + 7.5, oy + 6.4, 2.2), (0, 0, 0), M.banner_d)
    add_lantern(click, (ox + 8.0, oy + 5.5, 1.6), M.win_warm)
    add_lantern(click, (ox + 8.0, oy - 5.5, 1.6), M.win_warm)

    # terrace sundial
    sun = cyl("Sundial", 1.1, 0.2, (ox + 10.5, oy, 1.85), verts=12, mat=M.gold_dim)
    parent_keep(sun, click)
    gnom = cube("Gnomon", (0.08, 0.08, 1.1), (ox + 10.5, oy, 2.5), (0.5, 0, 0), M.gold)
    parent_keep(gnom, click)
    return click


# ---------------------------------------------------------------------------
# 星语院 — write it. Port. Green copper, scriptorium, tree through the roof.
# ---------------------------------------------------------------------------
def make_speak(root):
    click = empty("Click_Speak", (4.0, 18.5, 0.0))
    parent_keep(click, root)
    ox, oy = 4.0, 18.5

    podium = cube("SpeakPodium", (12.5, 11.0, 1.1), (ox, oy, 1.05), mat=M.stone_grey)
    bevel(podium, 0.1, 2)
    parent_keep(podium, click)

    hall = cube("SpeakHall", (10.0, 8.2, 7.8), (ox, oy, 5.5), mat=M.stone_grey)
    bevel(hall, 0.1, 2)
    parent_keep(hall, click)

    roof = gable_roof("SpeakRoof", 11.6, 9.4, 5.0, (ox, oy, 9.45), rot=(0, 0, 0), mat=M.roof_speak)
    parent_keep(roof, click)

    # hole in roof + tree (the 800-year 梧桐)
    # we cut a visual well with a darker ring and put the tree through
    well = cyl("SpeakWell", 1.6, 0.5, (ox - 1.2, oy, 11.6), verts=10, mat=M.moss)
    parent_keep(well, click)
    add_tree(click, (ox - 1.2, oy, 0.9), scale=1.55, old=True)
    # extra high canopy to pierce the roof
    hi = ico("SpeakTreeHigh", 2.4, (ox - 1.2, oy, 14.2), subdiv=1, mat=M.leaf_old)
    hi.scale = (1.35, 1.2, 0.95)
    apply_scale(hi)
    parent_keep(hi, click)
    hi2 = ico("SpeakTreeHigh2", 1.6, (ox - 0.2, oy + 1.1, 16.0), subdiv=1, mat=M.leaf)
    parent_keep(hi2, click)

    # script tower
    st = cyl("SpeakTower", 2.1, 14.0, (ox + 5.4, oy - 4.6, 8.0), verts=8, mat=M.stone_grey)
    bevel(st, 0.08, 2)
    parent_keep(st, click)
    strf = cone("SpeakTowerRoof", 2.8, 4.6, (ox + 5.4, oy - 4.6, 17.2), verts=8, mat=M.patina)
    parent_keep(strf, click)
    fin = ico("SpeakFinial", 0.4, (ox + 5.4, oy - 4.6, 19.8), subdiv=1, mat=M.win_green)
    parent_keep(fin, click)

    # flying buttresses toward island
    for i, yoff in enumerate((-3.5, 0.0, 3.5)):
        add_buttress(click, (ox - 6.4, oy + yoff, 3.5), 2.2, 8.5, math.pi, M.stone_grey)

    # tall narrow windows (scriptorium)
    add_windows(click, (ox, oy + 4.2, 0), 5, 8.0, 5.4, (0.55, 0.14, 2.4), M.win_green, axis="x")
    add_windows(click, (ox, oy - 4.2, 0), 5, 8.0, 5.4, (0.55, 0.14, 2.4), M.win_green, axis="x")
    for z in (5.5, 9.5, 13.0):
        w = cube(uid("STWin"), (0.45, 0.14, 1.5), (ox + 5.4, oy - 4.6 + 2.15, z), mat=M.win_green)
        parent_keep(w, click)

    # stacked stone tablets outside
    for i in range(5):
        tab = cube(uid("Tablet"), (1.6, 0.18, 1.1),
                   (ox - 5.5, oy + 4.0 + i * 0.12, 1.9 + i * 0.22),
                   (0, 0, 0.15 * i), M.stone_grey)
        parent_keep(tab, click)

    add_banner(click, (ox - 5.0, oy + 5.6, 1.8), (0, 0, 0.4), M.banner_s)
    add_lantern(click, (ox + 6.2, oy + 4.0, 1.5), M.win_green)
    add_lantern(click, (ox - 5.6, oy - 4.4, 1.5), M.win_green)
    return click


# ---------------------------------------------------------------------------
# 锤音院 — lock it in metal. Starboard. Low, chimneys, ember.
# ---------------------------------------------------------------------------
def make_forge(root):
    click = empty("Click_Forge", (3.0, -18.0, 0.0))
    parent_keep(click, root)
    ox, oy = 3.0, -18.0

    podium = cube("ForgePodium", (15.0, 12.5, 1.4), (ox, oy, 1.15), mat=M.stone_dark)
    bevel(podium, 0.1, 1)
    parent_keep(podium, click)

    hall = cube("ForgeHall", (12.5, 9.0, 5.2), (ox, oy, 4.2), mat=M.stone_dark)
    bevel(hall, 0.1, 1)
    parent_keep(hall, click)

    roof = cube("ForgeRoof", (13.6, 10.0, 1.1), (ox, oy, 7.0), mat=M.roof_forge)
    parent_keep(roof, click)
    # shallow hip
    hip = hip_roof("ForgeHip", 13.8, 10.2, 2.2, (ox, oy, 7.55), mat=M.copper_old, ridge=0.55)
    parent_keep(hip, click)

    # iron bands
    for z in (3.2, 5.6):
        band = cube(uid("Band"), (12.8, 9.3, 0.22), (ox, oy, z), mat=M.iron)
        parent_keep(band, click)

    # chimneys
    chimneys = [(-4.2, -2.4, 1.1), (1.5, -3.2, 1.3), (4.6, 1.8, 0.9)]
    for i, (dx, dy, sc) in enumerate(chimneys):
        ch = cyl(uid("Chim"), 0.7 * sc, 6.5 * sc, (ox + dx, oy + dy, 10.2), verts=8, mat=M.stone_dark)
        parent_keep(ch, click)
        lip = cyl(uid("ChimLip"), 0.9 * sc, 0.35, (ox + dx, oy + dy, 10.2 + 3.3 * sc), verts=8, mat=M.iron)
        parent_keep(lip, click)
        glow = uvsp(uid("ChimGlow"), 0.35 * sc, (ox + dx, oy + dy, 10.2 + 3.6 * sc),
                    segs=8, rings=6, mat=M.ember)
        parent_keep(glow, click)

    # anvil court
    block = cube("AnvilBlock", (2.4, 1.6, 0.9), (ox + 8.4, oy, 1.95), mat=M.iron)
    parent_keep(block, click)
    horn = cube("AnvilHorn", (2.8, 0.7, 0.45), (ox + 8.4, oy, 2.55), mat=M.iron)
    parent_keep(horn, click)
    spark = uvsp("ForgeSpark", 0.28, (ox + 8.4, oy, 3.1), segs=8, rings=6, mat=M.ember)
    parent_keep(spark, click)

    # side workshop
    shop = cube("ForgeShop", (6.0, 5.5, 3.6), (ox - 7.5, oy + 4.4, 3.2), mat=M.stone_dark)
    parent_keep(shop, click)
    shopr = gable_roof("ForgeShopRoof", 6.8, 6.2, 2.0, (ox - 7.5, oy + 4.4, 5.05),
                       rot=(0, 0, math.pi / 2), mat=M.copper_old)
    parent_keep(shopr, click)

    add_windows(click, (ox, oy + 4.6, 0), 4, 9.0, 4.4, (1.0, 0.16, 1.1), M.win_ember, axis="x")
    add_windows(click, (ox, oy - 4.6, 0), 4, 9.0, 4.4, (1.0, 0.16, 1.1), M.win_ember, axis="x")

    add_banner(click, (ox + 7.0, oy - 5.6, 1.9), (0, 0, -0.3), M.banner_f)
    add_lantern(click, (ox + 8.0, oy + 5.0, 1.6), M.win_ember)
    add_lantern(click, (ox - 6.5, oy - 5.2, 1.6), M.win_ember)

    # stacked ingots
    for i in range(4):
        ing = cube(uid("Ingot"), (1.3, 0.5, 0.28),
                   (ox + 6.5 + (i % 2) * 0.2, oy + 3.4, 1.85 + i * 0.3),
                   (0, 0, 0.2 * i), M.copper)
        parent_keep(ing, click)
    return click


# ---------------------------------------------------------------------------
# 海心院 — give it back. Stern. Terraces down into the floating pool.
# ---------------------------------------------------------------------------
def make_tide(root):
    click = empty("Click_Tide", (-30.0, 0.0, 0.0))
    parent_keep(click, root)
    ox, oy = -30.0, 0.0

    # cascading terraces
    for i, (sx, sy, z, drop) in enumerate([
        (14.0, 16.0, 1.0, 1.1),
        (12.0, 13.5, 0.4, 0.9),
        (10.0, 11.0, -0.3, 0.8),
    ]):
        t = cube(uid("Terrace"), (sx, sy, drop), (ox - i * 3.2, oy, z), mat=M.limestone)
        bevel(t, 0.1, 1)
        parent_keep(t, click)
        # teal tile edge
        edge = cube(uid("TileEdge"), (sx + 0.2, 0.4, 0.18), (ox - i * 3.2, oy + sy * 0.48, z + drop * 0.45),
                    mat=M.tile_teal)
        parent_keep(edge, click)
        edge2 = cube(uid("TileEdge2"), (sx + 0.2, 0.4, 0.18), (ox - i * 3.2, oy - sy * 0.48, z + drop * 0.45),
                     mat=M.tile_teal)
        parent_keep(edge2, click)

    hall = cube("TideHall", (9.5, 10.5, 5.4), (ox + 1.5, oy, 4.4), mat=M.limestone)
    bevel(hall, 0.1, 2)
    parent_keep(hall, click)

    # barrel-vault roof (hull memory)
    vault = cyl("TideVault", 5.4, 10.0, (ox + 1.5, oy, 7.6),
                rot=(0, math.pi / 2, 0), verts=12, mat=M.tile_blue)
    # cut conceptually by scaling z
    vault.scale = (1.0, 1.05, 0.55)
    apply_scale(vault)
    parent_keep(vault, click)

    # cascading leftover-seawater down the terraces
    for i in range(5):
        cascade = cube(uid("Cascade"), (1.1, 2.4 - i * 0.15, 0.18),
                       (ox - 4.5 - i * 2.4, 0.0, 1.35 - i * 0.28), mat=M.water)
        parent_keep(cascade, click)

    # two stair-down arms toward pool
    for side in (1, -1):
        stair = cube(uid("TideStair"), (8.5, 2.4, 0.45),
                     (ox - 8.0, oy + side * 5.5, 0.55), (0, 0.18, 0), M.pave)
        parent_keep(stair, click)
        rail = cube(uid("TideRail"), (8.5, 0.12, 0.7),
                    (ox - 8.0, oy + side * 6.6, 1.0), (0, 0.18, 0), M.iron)
        parent_keep(rail, click)

    add_windows(click, (ox + 1.5, oy + 5.35, 0), 4, 7.0, 4.6, (1.1, 0.14, 1.6), M.win_blue, axis="x")
    add_windows(click, (ox + 1.5, oy - 5.35, 0), 4, 7.0, 4.6, (1.1, 0.14, 1.6), M.win_blue, axis="x")

    # stern lanterns like ship lamps
    add_lantern(click, (ox - 4.5, oy + 7.2, 1.4), M.win_blue)
    add_lantern(click, (ox - 4.5, oy - 7.2, 1.4), M.win_blue)
    add_banner(click, (ox + 5.5, oy + 6.4, 2.0), (0, 0, 0.2), M.banner_t)

    # rib posts recalling the hull
    for i in range(4):
        y = -4.5 + i * 3.0
        post = cyl(uid("TideRib"), 0.22, 4.8, (ox + 6.4, y, 3.6), verts=6, mat=M.wood)
        parent_keep(post, click)
    return click


def make_pool(root):
    click = empty("Click_Pool", (-44.0, 0.0, 0.2))
    parent_keep(click, root)
    # the floating dry-dock: a stone ring that holds seawater from the night the star fell
    ring = cyl("PoolRing", 7.4, 1.1, (-44.0, 0.0, 0.4), verts=16, mat=M.stone_grey)
    parent_keep(ring, click)
    inner = cyl("PoolInner", 6.2, 0.7, (-44.0, 0.0, 0.55), verts=16, mat=M.tile_teal)
    parent_keep(inner, click)
    water = cyl("PoolWater", 5.9, 0.35, (-44.0, 0.0, 0.85), verts=20, mat=M.water)
    parent_keep(water, click)
    # four mooring bitts
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        x = -44.0 + math.cos(a) * 7.0
        y = math.sin(a) * 7.0
        bitt = cyl(uid("Bitt"), 0.28, 1.4, (x, y, 1.4), verts=8, mat=M.iron)
        parent_keep(bitt, click)
    # a single unlit lamp waiting to be sunk (海心 ritual)
    lamp = cyl("UnlitLamp", 0.35, 0.8, (-44.0, 0.0, 1.15), verts=8, mat=M.copper_old)
    parent_keep(lamp, click)
    return click


# ---------------------------------------------------------------------------
# 退字阁 — library of rejected drafts
# ---------------------------------------------------------------------------
def make_library(root):
    click = empty("Click_Library", (-12.0, 14.0, 0.0))
    parent_keep(click, root)
    ox, oy = -12.0, 14.0

    base = cyl("LibBase", 5.6, 1.4, (ox, oy, 1.2), verts=8, mat=M.limestone)
    bevel(base, 0.1, 2)
    parent_keep(base, click)
    drum = cyl("LibDrum", 4.8, 7.2, (ox, oy, 5.5), verts=8, mat=M.limestone_warm)
    bevel(drum, 0.1, 2)
    parent_keep(drum, click)
    # dome
    dome = uvsp("LibDome", 4.9, (ox, oy, 9.0), segs=16, rings=8, mat=M.gold_dim)
    # flatten bottom half by scaling and moving
    dome.scale = (1.0, 1.0, 0.72)
    apply_scale(dome)
    parent_keep(dome, click)
    lantern = cyl("LibLantern", 0.7, 1.6, (ox, oy, 13.0), verts=8, mat=M.limestone)
    parent_keep(lantern, click)
    cap = cone("LibCap", 1.1, 1.8, (ox, oy, 14.4), verts=8, mat=M.gold)
    parent_keep(cap, click)
    star = ico("LibStar", 0.4, (ox, oy, 15.5), subdiv=1, mat=M.crystal)
    parent_keep(star, click)

    for k in range(8):
        a = k / 8 * math.pi * 2 + math.pi / 8
        w = cube(uid("LibWin"), (0.9, 0.16, 2.2),
                 (ox + math.cos(a) * 4.75, oy + math.sin(a) * 4.75, 5.6),
                 (0, 0, a), M.win_warm)
        parent_keep(w, click)

    # steps
    for i in range(4):
        st = cube(uid("LibStep"), (3.4 - i * 0.3, 1.6, 0.28),
                  (ox, oy - 6.2 - i * 0.35, 0.7 + i * 0.28), mat=M.pave)
        parent_keep(st, click)
    add_lantern(click, (ox + 3.4, oy - 6.5, 1.2), M.win_warm)
    add_lantern(click, (ox - 3.4, oy - 6.5, 1.2), M.win_warm)
    return click


# ---------------------------------------------------------------------------
# dorms — bed is house-color, not fate
# ---------------------------------------------------------------------------
def make_dorms(root):
    click = empty("Click_Dorms", (0.0, 0.0, 0.0))
    parent_keep(click, root)
    roofs = [M.roof_dawn, M.roof_speak, M.roof_forge, M.roof_tide]
    wins = [M.win_warm, M.win_green, M.win_ember, M.win_blue]
    # along port and starboard gunwales, skipping house footprints
    spots = []
    for x in (-18, -10, 12, 18):
        spots.append((x, 12.5, 0))
        spots.append((x, -12.5, 0))
    spots += [(22.0, 9.5, 0), (22.0, -9.5, 0), (-22.0, 9.0, 0), (-22.0, -9.0, 0)]
    for i, (x, y, _) in enumerate(spots):
        body = cube(uid("Dorm"), (3.4, 2.8, 2.6), (x, y, 2.0), mat=M.limestone)
        bevel(body, 0.06, 1)
        parent_keep(body, click)
        rf = gable_roof(uid("DormRoof"), 3.9, 3.3, 1.6, (x, y, 3.35),
                        rot=(0, 0, math.pi / 2 if abs(y) > 8 else 0), mat=roofs[i % 4])
        parent_keep(rf, click)
        w = cube(uid("DormWin"), (0.7, 0.12, 0.9), (x, y + (0.95 if y > 0 else -0.95) * 1.5, 2.15),
                 mat=wins[i % 4])
        parent_keep(w, click)
    return click


def make_cloisters(root):
    """Stone walks from mast to four houses."""
    click = empty("Click_Cloister", (0, 0, 0))
    parent_keep(click, root)
    paths = [
        ((6.5, 0.0, 1.05), (20.5, 0.0, 1.05), (14.0, 2.6, 0.35), 0.0),          # to dawn
        ((0.0, 6.5, 1.05), (2.5, 13.5, 1.05), (2.6, 8.0, 0.35), math.pi / 2),  # speak
        ((0.0, -6.5, 1.05), (2.0, -13.2, 1.05), (2.6, 8.0, 0.35), math.pi / 2),  # forge
        ((-6.5, 0.0, 1.05), (-20.0, 0.0, 1.05), (14.0, 2.6, 0.35), 0.0),       # tide
    ]
    # simpler: just boxes along axes
    specs = [
        ((13.5, 0.0, 1.05), (15.0, 2.5, 0.32), 0.0),
        ((2.0, 11.0, 1.05), (2.5, 10.0, 0.32), 0.0),
        ((2.0, -11.0, 1.05), (2.5, 10.0, 0.32), 0.0),
        ((-14.0, 0.0, 1.05), (16.0, 2.5, 0.32), 0.0),
    ]
    for i, (loc, size, rot) in enumerate(specs):
        p = cube(uid("Path"), size, loc, (0, 0, rot), M.pave)
        parent_keep(p, click)
        # low wall
        if size[0] > size[1]:
            w1 = cube(uid("PathW"), (size[0], 0.16, 0.7), (loc[0], loc[1] + size[1] * 0.45, loc[2] + 0.4), mat=M.limestone)
            w2 = cube(uid("PathW"), (size[0], 0.16, 0.7), (loc[0], loc[1] - size[1] * 0.45, loc[2] + 0.4), mat=M.limestone)
        else:
            w1 = cube(uid("PathW"), (0.16, size[1], 0.7), (loc[0] + size[0] * 0.45, loc[1], loc[2] + 0.4), mat=M.limestone)
            w2 = cube(uid("PathW"), (0.16, size[1], 0.7), (loc[0] - size[0] * 0.45, loc[1], loc[2] + 0.4), mat=M.limestone)
        parent_keep(w1, click)
        parent_keep(w2, click)
    return click


def scatter_props(root):
    # trees on leftover grass
    spots = [
        (16.5, 8.5, 0.7, 0.85), (14.0, -10.0, 0.7, 1.0),
        (-8.0, 8.5, 0.7, 0.9), (-16.0, -8.0, 0.7, 0.75),
        (8.5, 8.0, 0.7, 0.7), (-6.0, -9.5, 0.7, 0.8),
    ]
    for x, y, z, sc in spots:
        add_tree(root, (x, y, z), scale=sc, old=(sc > 0.9))
    # lanterns along cloisters
    for loc in [(10, 1.6, 0.7), (10, -1.6, 0.7), (-10, 1.6, 0.7), (-10, -1.6, 0.7),
                (1.8, 8.0, 0.7), (-1.8, 8.0, 0.7), (1.8, -8.0, 0.7), (-1.8, -8.0, 0.7),
                (36.0, 3.2, 0.7), (36.0, -3.2, 0.7)]:
        add_lantern(root, loc, M.win_cyan if abs(loc[0]) < 4 else M.win_warm)
    # floating rocks further out
    for i in range(5):
        a = i / 5 * math.pi * 2 + 0.7
        x = math.cos(a) * (58 + i * 2)
        y = math.sin(a) * (28 + i)
        z = -6 - (i * 3) % 11
        rk = ico(uid("Floater"), 1.6 + i * 0.25, (x * 0.7, y * 0.55, z), subdiv=1, mat=M.rock)
        rk.rotation_euler = (0.4 * i, 0.7 * i, 0.2)
        parent_keep(rk, root)


# ---------------------------------------------------------------------------
# export / render
# ---------------------------------------------------------------------------
def setup_view_camera():
    cam_data = bpy.data.cameras.new("HeroCam")
    cam = bpy.data.objects.new("HeroCam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = (78.0, -64.0, 34.0)
    # look at tower mid
    direction = Vector((2.0, 0.0, 14.0)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam_data.lens = 32
    cam_data.clip_end = 800
    bpy.context.scene.camera = cam

    # lights for optional render
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 6.0
    sun.angle = 0.012
    sun_obj = bpy.data.objects.new("Sun", sun)
    sun_obj.rotation_euler = (math.radians(48), math.radians(12), math.radians(35))
    bpy.context.collection.objects.link(sun_obj)

    fill = bpy.data.lights.new("Fill", "AREA")
    fill.energy = 1400
    fill.size = 18
    fill_obj = bpy.data.objects.new("Fill", fill)
    fill_obj.location = (-40, 30, 28)
    fill_obj.rotation_euler = (math.radians(60), 0, math.radians(-40))
    bpy.context.collection.objects.link(fill_obj)

    rim = bpy.data.lights.new("Rim", "AREA")
    rim.energy = 900
    rim.size = 12
    rim.color = (0.45, 0.75, 1.0)
    rim_obj = bpy.data.objects.new("Rim", rim)
    rim_obj.location = (10, 40, 20)
    bpy.context.collection.objects.link(rim_obj)

    world = bpy.data.worlds.new("Sky")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.22, 0.28, 0.38, 1.0)
    bg.inputs[1].default_value = 0.6


def export_glb(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        export_apply=True,
        export_lights=False,
        export_cameras=False,
        export_extras=True,
        export_yup=True,
        export_texcoords=True,
        export_normals=True,
        export_materials="EXPORT",
        use_selection=False,
    )
    print("GLB ->", path, "size", path.stat().st_size if path.exists() else 0)


def try_render(path):
    scene = bpy.context.scene
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    # workbench is the only realistic option on 2GB RAM, no display
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light = "STUDIO"
    sh.color_type = "MATERIAL"
    sh.show_specular_highlight = True
    sh.show_cavity = True
    sh.cavity_type = "BOTH"
    try:
        bpy.ops.render.render(write_still=True)
        print("PNG ->", path)
        return True
    except Exception as e:
        print("render failed:", e)
        return False


def stats():
    verts = sum(len(m.vertices) for m in bpy.data.meshes)
    faces = sum(len(m.polygons) for m in bpy.data.meshes)
    print("objects", len(bpy.data.objects), "meshes", len(bpy.data.meshes),
          "verts", verts, "faces", faces, "mats", len(bpy.data.materials))


def main():
    reset_scene()
    build_materials()
    root = empty("Academy", (0, 0, 0))
    make_island(root)
    make_tower(root)
    make_yard(root)
    make_dawn(root)
    make_speak(root)
    make_forge(root)
    make_tide(root)
    make_pool(root)
    make_library(root)
    make_dorms(root)
    make_cloisters(root)
    scatter_props(root)
    setup_view_camera()
    stats()

    blend_path = ROOT / "blender" / "academy.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print("BLEND ->", blend_path)

    export_glb(ROOT / "models" / "academy.glb")
    try_render(ROOT / "img" / "academy-hero.png")
    print("DONE")


if __name__ == "__main__":
    main()
