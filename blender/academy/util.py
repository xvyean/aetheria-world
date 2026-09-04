# -*- coding: utf-8 -*-
"""
星槎学院 · Blender 程序化建模工具库
--------------------------------
所有几何都以 bmesh / 顶点数组直接构造，避免布尔与交互式算子；
材质统一走 principled()，顶点色走 set_vcol()，导出时 glTF 只带被材质引用的颜色属性。
单位：米。Z 向上（导出时转 Y-up）。
"""
import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix, noise

TAU = math.pi * 2.0

# ------------------------------------------------------------------ 颜色
def hex2lin(h):
    """'#rrggbb' → 线性 RGBA (Blender 内部空间)。"""
    h = h.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (srgb2lin(r), srgb2lin(g), srgb2lin(b), 1.0)


def srgb2lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def mix(a, b, t):
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(min(len(a), len(b))))


def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def smoothstep(e0, e1, x):
    t = clamp((x - e0) / (e1 - e0))
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ 调色板（sRGB）
PAL = {
    'stone_white': '#ddd6c4',
    'stone_cream': '#cfc2a6',
    'stone_grey': '#8f8a7e',
    'stone_dark': '#4e4b47',
    'basalt': '#3a3733',
    'rock_a': '#7a7168',   # 岩体主色
    'rock_b': '#5c544d',   # 岩体暗层
    'rock_c': '#8e8479',   # 岩体亮层
    'soil': '#6b563f',
    'grass_a': '#5a8a38',
    'grass_b': '#86a843',
    'grass_c': '#365f27',
    'path_dirt': '#8b7355',
    'flagstone': '#b3ab98',
    'wood_dark': '#4a3626',
    'wood_mid': '#7a5a3a',
    'wood_light': '#a8845a',
    'gold': '#e2b654',
    'copper': '#b8683f',
    'patina': '#5f9c8a',
    'iron': '#2e2b2b',
    'slate': '#4b5563',
    'tile_dawn': '#e2b654',
    'tile_speak': '#3e8f56',
    'tile_forge': '#c47a4a',
    'tile_tide': '#4a9dc9',
    'cloth_dawn': '#e8b45b',
    'cloth_speak': '#2f8a4a',
    'cloth_forge': '#c97a4a',
    'cloth_tide': '#4a9dc9',
    'leaf_a': '#3f7a3a',
    'leaf_b': '#6f9c3e',
    'leaf_sycamore_a': '#6f9440',
    'leaf_sycamore_b': '#a9b24e',
    'cypress': '#243b2a',
    'bark': '#5a4635',
    'bark_syc': '#b8ad98',
    'water': '#3a9dc0',
    'crystal': '#bfefff',
    'fire': '#ff9a3a',
    'lamp': '#ffd28a',
    'moss': '#7dff9a',
    'ash': '#8e8a86',
    'goat': '#d8d2c4',
}

# ------------------------------------------------------------------ 场景
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    return sc


_COLL = {}


def coll(name):
    """按名取/建集合（挂在场景根集合下）。"""
    if name in _COLL:
        return _COLL[name]
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    _COLL[name] = c
    return c


# ------------------------------------------------------------------ 材质
_MAT = {}


def principled(name, color, rough=0.6, metal=0.0, emit=None, emit_strength=0.0,
               alpha=1.0, vcol=False, specular=0.5, sheen=0.0):
    """
    带缓存的 Principled BSDF 材质。
    vcol=True 时把 Color Attribute 节点接进 Base Color（glTF 才会导出顶点色）。
    """
    if name in _MAT:
        return _MAT[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    col = hex2lin(color) if isinstance(color, str) else color
    bsdf.inputs['Base Color'].default_value = col
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = specular
    if sheen and 'Sheen Weight' in bsdf.inputs:
        bsdf.inputs['Sheen Weight'].default_value = sheen
    if emit:
        ec = hex2lin(emit) if isinstance(emit, str) else emit
        bsdf.inputs['Emission Color'].default_value = ec
        bsdf.inputs['Emission Strength'].default_value = emit_strength
    if alpha < 1.0:
        bsdf.inputs['Alpha'].default_value = alpha
        m.blend_method = 'BLEND'
        m.use_backface_culling = False
    if vcol:
        ca = nt.nodes.new('ShaderNodeVertexColor')
        ca.layer_name = 'Col'
        ca.location = (-400, 300)
        nt.links.new(ca.outputs['Color'], bsdf.inputs['Base Color'])
    m.diffuse_color = col  # workbench 预览色
    m.roughness = rough
    m.metallic = metal
    _MAT[name] = m
    return m


def mat_lib():
    """一次性建好全部标准材质，返回 dict。"""
    P = PAL
    M = {}
    M['stone_white'] = principled('Stone_White', P['stone_white'], rough=0.72, vcol=True)
    M['stone_cream'] = principled('Stone_Cream', P['stone_cream'], rough=0.75, vcol=True)
    M['stone_grey'] = principled('Stone_Grey', P['stone_grey'], rough=0.8, vcol=True)
    M['stone_dark'] = principled('Stone_Dark', P['stone_dark'], rough=0.85, vcol=True)
    M['basalt'] = principled('Basalt', P['basalt'], rough=0.9, vcol=True)
    M['rock'] = principled('Island_Rock', P['rock_a'], rough=0.95, vcol=True)
    M['grass'] = principled('Island_Grass', P['grass_a'], rough=0.9, vcol=True)
    M['soil'] = principled('Soil', P['soil'], rough=1.0, vcol=True)
    M['flagstone'] = principled('Flagstone', P['flagstone'], rough=0.8, vcol=True)
    M['wood_dark'] = principled('Wood_Dark', P['wood_dark'], rough=0.7, vcol=True)
    M['wood_mid'] = principled('Wood_Mid', P['wood_mid'], rough=0.65, vcol=True)
    M['wood_light'] = principled('Wood_Light', P['wood_light'], rough=0.6, vcol=True)
    M['gold'] = principled('Gold', P['gold'], rough=0.32, metal=1.0)
    M['copper'] = principled('Copper', P['copper'], rough=0.4, metal=1.0)
    M['patina'] = principled('Copper_Patina', P['patina'], rough=0.55, metal=0.6)
    M['iron'] = principled('Iron', P['iron'], rough=0.5, metal=0.9)
    M['slate'] = principled('Slate', P['slate'], rough=0.6, vcol=True)
    for h in ('dawn', 'speak', 'forge', 'tide'):
        M['tile_' + h] = principled('Tile_' + h.capitalize(), P['tile_' + h], rough=0.45, metal=0.15, vcol=True)
        M['cloth_' + h] = principled('Cloth_' + h.capitalize(), P['cloth_' + h], rough=0.9, sheen=0.4)
    M['leaf'] = principled('Leaf', P['leaf_a'], rough=0.8, vcol=True)
    M['leaf_syc'] = principled('Leaf_Sycamore', P['leaf_sycamore_a'], rough=0.8, vcol=True)
    M['cypress'] = principled('Cypress', P['cypress'], rough=0.9, vcol=True)
    M['bark'] = principled('Bark', P['bark'], rough=0.95, vcol=True)
    M['bark_syc'] = principled('Bark_Sycamore', P['bark_syc'], rough=0.9, vcol=True)
    M['water'] = principled('FX_Water', P['water'], rough=0.05, metal=0.1, alpha=0.82,
                            emit='#1a4a66', emit_strength=0.6)
    M['waterfall'] = principled('FX_Waterfall', '#9fd8ee', rough=0.2, alpha=0.45,
                                emit='#9fd8ee', emit_strength=0.3)
    M['crystal'] = principled('FX_Crystal', P['crystal'], rough=0.1, emit='#54d4f4', emit_strength=6.0)
    M['crystal_root'] = principled('FX_CrystalRoot', '#8fe8ff', rough=0.2, emit='#3ab8e8', emit_strength=3.0)
    M['fire'] = principled('FX_Fire', P['fire'], rough=0.5, emit='#ff7a1a', emit_strength=12.0)
    M['lamp'] = principled('FX_Lamp', P['lamp'], rough=0.3, emit='#ffc36a', emit_strength=8.0)
    M['window'] = principled('FX_Window', '#f2d9a0', rough=0.25, emit='#ffc36a', emit_strength=1.6)
    M['window_frame'] = principled('Window_Frame', '#6b6357', rough=0.8)
    M['plaster'] = principled('Plaster', '#e6dcc4', rough=0.9, vcol=True)
    M['roof_terra'] = principled('Roof_Terracotta', '#a8603f', rough=0.7, vcol=True)
    M['roof_blue'] = principled('Roof_BlueSlate', '#4f5f74', rough=0.65, vcol=True)
    M['cloud'] = principled('FX_Cloud', '#f6f3ec', rough=1.0, alpha=0.55, emit='#fff6e8', emit_strength=0.35)
    M['moss'] = principled('FX_Moss', P['moss'], rough=0.8, emit='#5cf08a', emit_strength=2.5)
    M['beam'] = principled('FX_LightColumn', '#bfefff', rough=0.3, alpha=0.18, emit='#7fdcff', emit_strength=2.0)
    M['ash'] = principled('Ash', P['ash'], rough=1.0)
    M['goat'] = principled('Goat', P['goat'], rough=0.9)
    M['glass_dark'] = principled('Glass_Dark', '#1c2530', rough=0.15, metal=0.2)
    M['net'] = principled('Net', '#d8d2c0', rough=0.9, alpha=0.55)
    M['rope'] = principled('Rope', '#b09a70', rough=0.95)
    M['paper'] = principled('Paper', '#efe6d0', rough=0.95)
    M['feather'] = principled('Feather', '#141018', rough=0.6)
    M['bell'] = principled('Bell_Bronze', '#8a6a3a', rough=0.35, metal=1.0)
    return M


# ------------------------------------------------------------------ 网格构造
def recalc_normals(me):
    """统一外向法线（对闭合体可靠；对开放面片给出一致朝向）。"""
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.update()


def mesh_from(name, verts, faces, collection, edges=(), mat=None, smooth=False, recalc=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], list(edges), [tuple(f) for f in faces])
    me.update()
    if recalc and len(faces) > 1:
        recalc_normals(me)
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    if mat is not None:
        me.materials.append(mat)
    if smooth:
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    return ob


def bm_to_obj(name, bm, collection, mat=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.update()
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    if mat is not None:
        me.materials.append(mat)
    return ob


def smooth_by_angle(ob, angle_deg=32.0):
    """全部面平滑 + 按二面角标记锐边（4.1+ 直接尊重 sharp_edge）。"""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    thr = math.radians(angle_deg)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2:
            a = e.calc_face_angle(0.0)
            e.smooth = a < thr
        else:
            e.smooth = False
    bm.to_mesh(me)
    bm.free()
    me.update()


def set_vcol(ob, func):
    """
    以顶点位置计算顶点色。func(v_co: Vector, v_normal: Vector) -> (r,g,b) 线性。
    使用 POINT 域 FLOAT_COLOR，名为 'Col'。
    """
    me = ob.data
    attr = me.color_attributes.get('Col')
    if attr is None:
        attr = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    me.color_attributes.active_color = attr
    vals = []
    for v in me.vertices:
        r, g, b = func(v.co, v.normal)[:3]
        vals.extend((r, g, b, 1.0))
    attr.data.foreach_set('color', vals)
    me.update()


def set_vcol_const(ob, hexcol, jitter=0.0, seed=0):
    base = hex2lin(hexcol)[:3]
    rng = random.Random(seed)

    def f(co, n):
        if jitter <= 0:
            return base
        j = 1.0 + rng.uniform(-jitter, jitter)
        return (base[0] * j, base[1] * j, base[2] * j)
    set_vcol(ob, f)


def apply_transform(ob, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    ob.location = loc
    ob.rotation_euler = rot
    ob.scale = scale
    return ob


def transform_verts(ob, mat):
    ob.data.transform(mat)
    ob.data.update()


def add_bevel(ob, width=0.05, segments=2, angle=40.0):
    m = ob.modifiers.new('Bevel', 'BEVEL')
    m.width = width
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)
    m.harden_normals = False
    return m


def add_displace(ob, strength=0.5, size=3.0, depth=3, seed=1, mid=0.5):
    tex = bpy.data.textures.new('disp_%s' % ob.name, 'CLOUDS')
    tex.noise_scale = size
    tex.noise_depth = depth
    tex.noise_basis = 'ORIGINAL_PERLIN'
    m = ob.modifiers.new('Displace', 'DISPLACE')
    m.texture = tex
    m.strength = strength
    m.mid_level = mid
    m.texture_coords = 'GLOBAL'
    return m


def apply_modifiers(ob):
    """在无 UI 上下文下应用全部修改器。"""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    bpy.data.meshes.remove(old)
    return ob


# ------------------------------------------------------------------ 基本体
def box(name, size, loc, collection, mat=None, rot=(0, 0, 0), origin='center'):
    sx, sy, sz = size
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    off = Vector((0, 0, 0.5)) if origin == 'bottom' else Vector((0, 0, 0))
    for v in bm.verts:
        v.co = Vector(((v.co.x) * sx, (v.co.y) * sy, (v.co.z + off.z) * sz))
    ob = bm_to_obj(name, bm, collection, mat)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def prism(name, radius, height, sides, loc, collection, mat=None, taper=1.0,
          rot=(0, 0, 0), phase=None, cap=True, smooth=False):
    """正多边形棱柱（底面在 z=0），taper=顶/底半径比。"""
    if phase is None:
        phase = math.pi / sides  # 使一条边朝向 +x（八角塔常规）
    verts, faces = [], []
    for k, (r, z) in enumerate(((radius, 0.0), (radius * taper, height))):
        for i in range(sides):
            a = TAU * i / sides + phase
            verts.append((math.cos(a) * r, math.sin(a) * r, z))
    for i in range(sides):
        j = (i + 1) % sides
        faces.append((i, j, sides + j, sides + i))
    if cap:
        faces.append(tuple(range(sides - 1, -1, -1)))
        faces.append(tuple(range(sides, 2 * sides)))
    ob = mesh_from(name, verts, faces, collection, mat=mat, smooth=smooth)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def lathe(name, profile, segments, loc, collection, mat=None, rot=(0, 0, 0),
          smooth=True, phase=0.0, close=True):
    """
    旋转体。profile: [(r, z), ...] 自下而上；r=0 的点作为极点。
    """
    verts, faces = [], []
    ring_idx = []
    for (r, z) in profile:
        if r <= 1e-6:
            verts.append((0.0, 0.0, z))
            ring_idx.append(('pole', len(verts) - 1))
        else:
            base = len(verts)
            for i in range(segments):
                a = TAU * i / segments + phase
                verts.append((math.cos(a) * r, math.sin(a) * r, z))
            ring_idx.append(('ring', base))
    for a, b in zip(ring_idx[:-1], ring_idx[1:]):
        if a[0] == 'ring' and b[0] == 'ring':
            for i in range(segments):
                j = (i + 1) % segments
                faces.append((a[1] + i, a[1] + j, b[1] + j, b[1] + i))
        elif a[0] == 'pole' and b[0] == 'ring':
            for i in range(segments):
                j = (i + 1) % segments
                faces.append((a[1], b[1] + j, b[1] + i))
        elif a[0] == 'ring' and b[0] == 'pole':
            for i in range(segments):
                j = (i + 1) % segments
                faces.append((a[1] + i, a[1] + j, b[1]))
    if close:
        first, last = ring_idx[0], ring_idx[-1]
        if first[0] == 'ring':
            faces.append(tuple(first[1] + i for i in range(segments - 1, -1, -1)))
        if last[0] == 'ring':
            faces.append(tuple(last[1] + i for i in range(segments)))
    ob = mesh_from(name, verts, faces, collection, mat=mat, smooth=smooth)
    ob.location = loc
    ob.rotation_euler = rot
    if smooth:
        smooth_by_angle(ob, 40)
    return ob


def cylinder(name, r, h, loc, collection, mat=None, segments=16, r_top=None, rot=(0, 0, 0), smooth=True):
    rt = r if r_top is None else r_top
    return lathe(name, [(r, 0.0), (rt, h)], segments, loc, collection, mat, rot=rot, smooth=smooth)


def cone(name, r, h, loc, collection, mat=None, segments=16, rot=(0, 0, 0), smooth=True, r_top=0.0):
    return lathe(name, [(r, 0.0), (r_top, h)], segments, loc, collection, mat, rot=rot, smooth=smooth)


def sphere(name, r, loc, collection, mat=None, segs=16, rings=10, scale=(1, 1, 1), smooth=True, hemi=False):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    if hemi:
        geom = [v for v in bm.verts if v.co.z < -1e-4]
        bmesh.ops.delete(bm, geom=geom, context='VERTS')
    for v in bm.verts:
        v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
    if smooth:
        for f in bm.faces:
            f.smooth = True
    ob = bm_to_obj(name, bm, collection, mat)
    ob.location = loc
    return ob


def ico(name, r, loc, collection, mat=None, subdiv=1, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    if smooth:
        for f in bm.faces:
            f.smooth = True
    ob = bm_to_obj(name, bm, collection, mat)
    ob.location = loc
    return ob


def torus(name, R, r, loc, collection, mat=None, segs=32, rsegs=10, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=False, radius=r, segments=rsegs)
    # 把圆放到 XZ 平面并平移到 R
    for v in bm.verts:
        v.co = Vector((R + v.co.x, 0.0, v.co.y))
    geom = bm.verts[:] + bm.edges[:]
    bmesh.ops.spin(bm, geom=geom, cent=(0, 0, 0), axis=(0, 0, 1), angle=TAU, steps=segs, use_merge=True)
    for f in bm.faces:
        f.smooth = True
    ob = bm_to_obj(name, bm, collection, mat)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def tube(name, pts, r, collection, mat=None, segs=8, closed=False, cap=True):
    """沿折线放样圆管。pts: [Vector,...]"""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    if n < 2:
        return None
    verts, faces = [], []
    up = Vector((0, 0, 1))
    frames = []
    for i in range(n):
        if closed:
            t = (pts[(i + 1) % n] - pts[i - 1]).normalized()
        elif i == 0:
            t = (pts[1] - pts[0]).normalized()
        elif i == n - 1:
            t = (pts[-1] - pts[-2]).normalized()
        else:
            t = (pts[i + 1] - pts[i - 1]).normalized()
        ref = up if abs(t.dot(up)) < 0.95 else Vector((1, 0, 0))
        b = t.cross(ref).normalized()
        nrm = b.cross(t).normalized()
        frames.append((b, nrm))
    for i, p in enumerate(pts):
        b, nrm = frames[i]
        for k in range(segs):
            a = TAU * k / segs
            verts.append(p + b * (math.cos(a) * r) + nrm * (math.sin(a) * r))
    m = n if closed else n - 1
    for i in range(m):
        i2 = (i + 1) % n
        for k in range(segs):
            k2 = (k + 1) % segs
            faces.append((i * segs + k, i * segs + k2, i2 * segs + k2, i2 * segs + k))
    if cap and not closed:
        faces.append(tuple(range(segs - 1, -1, -1)))
        faces.append(tuple((n - 1) * segs + k for k in range(segs)))
    ob = mesh_from(name, verts, faces, collection, mat=mat, smooth=True)
    smooth_by_angle(ob, 50)
    return ob


def ring_surface(name, rings, collection, mat=None, cap_top=True, cap_bottom=False, smooth=True):
    """
    由多圈顶点（每圈同样数量、按序）缝成曲面；rings: [[Vector,...], ...]
    """
    segs = len(rings[0])
    verts, faces = [], []
    for ring in rings:
        verts.extend(ring)
    for i in range(len(rings) - 1):
        a, b = i * segs, (i + 1) * segs
        for k in range(segs):
            k2 = (k + 1) % segs
            faces.append((a + k, a + k2, b + k2, b + k))
    if cap_top:
        faces.append(tuple(range(segs - 1, -1, -1)))
    if cap_bottom:
        base = (len(rings) - 1) * segs
        faces.append(tuple(base + k for k in range(segs)))
    ob = mesh_from(name, verts, faces, collection, mat=mat, smooth=smooth)
    return ob


# ------------------------------------------------------------------ 噪声
def n3(x, y, z, seed=0.0):
    """Perlin, -1..1"""
    return noise.noise(Vector((x + seed * 17.3, y - seed * 9.1, z + seed * 3.7)))


def fbm(x, y, z, oct=4, lac=2.0, gain=0.5, seed=0.0):
    a, f, s, norm = 1.0, 1.0, 0.0, 0.0
    for _ in range(oct):
        s += a * n3(x * f, y * f, z * f, seed)
        norm += a
        a *= gain
        f *= lac
    return s / norm


def ridged(x, y, z, oct=4, seed=0.0):
    a, f, s = 1.0, 1.0, 0.0
    for _ in range(oct):
        s += a * (1.0 - abs(n3(x * f, y * f, z * f, seed)))
        a *= 0.5
        f *= 2.0
    return s


# ------------------------------------------------------------------ 合并 / 导出辅助
def join_objects(objs, name):
    """把一组对象合并成一个（保留各自材质槽）。"""
    objs = [o for o in objs if o is not None and o.type == 'MESH']
    if not objs:
        return None
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    return ob


def empty(name, loc, collection, size=1.0):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = 'PLAIN_AXES'
    e.empty_display_size = size
    e.location = loc
    collection.objects.link(e)
    return e


def stats():
    v = f = 0
    for o in bpy.data.objects:
        if o.type == 'MESH':
            v += len(o.data.vertices)
            f += len(o.data.polygons)
    return v, f
