# -*- coding: utf-8 -*-
"""几何组件库：以程序化方式装配「精致的通用构件」。
所有构件 = 基元 + 贝塞尔修改器 + 细部叠加，避免布尔运算（稳健、快速、可批量）。
"""
import bpy, math
from mathutils import Vector, Euler
import random

D = math.radians

# ------------------------------------------------------------------ 基础
def _act(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob

def _finish(ob, name, mat, loc, rot, scale, coll, smooth_faces=False, bevel=0.0):
    ob.name = name
    if mat is not None:
        ob.data.materials.append(mat)
    ob.location = loc
    ob.rotation_euler = Euler([D(a) for a in rot], 'XYZ')
    if scale != (1, 1, 1):
        ob.scale = scale
    if coll is not None:
        for c in ob.users_collection:
            c.objects.unlink(ob)
        coll.objects.link(ob)
    if bevel > 0:
        _act(ob)
        m = ob.modifiers.new('bv', 'BEVEL')
        m.width = bevel; m.segments = 2; m.limit_method = 'ANGLE'
        try:
            bpy.ops.object.modifier_apply(modifier='bv')
        except Exception:
            ob.modifiers.remove(m)
    if smooth_faces:
        _act(ob)
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=D(38))
        except Exception:
            try:
                bpy.ops.object.shade_smooth()
            except Exception:
                for p in ob.data.polygons:
                    p.use_smooth = True
    return ob

def _mesh(name, verts, faces, mat, loc, rot, scale, coll, smooth_faces=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return _finish(ob, name, mat, loc, rot, scale, coll, smooth_faces)

def box(name, sx, sy, sz, loc, mat, rot=(0, 0, 0), coll=None, bevel=0.028, smooth=False):
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object
    ob.scale = (sx, sy, sz)
    return _finish(ob, name, mat, loc, rot, (1, 1, 1), coll, smooth, bevel)

def cyl(name, r1, r2, h, loc, mat, rot=(0, 0, 0), verts=14, coll=None, smooth=True):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=h)
    ob = bpy.context.active_object
    return _finish(ob, name, mat, loc, rot, (1, 1, 1), coll, smooth)

def sphere(name, r, loc, mat, scale=(1, 1, 1), seg=18, ring=12, coll=None, smooth=True):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=ring, radius=r)
    ob = bpy.context.active_object
    return _finish(ob, name, mat, loc, (0, 0, 0), scale, coll, smooth)

def ico(name, r, loc, mat, sub=1, rot=(0, 0, 0), coll=None, scale=(1, 1, 1), smooth=False):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r)
    ob = bpy.context.active_object
    return _finish(ob, name, mat, loc, rot, scale, coll, smooth)

def torus(name, R, r, loc, mat, rot=(0, 0, 0), segs=28, minor=10, coll=None, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r,
                                     major_segments=segs, minor_segments=minor)
    ob = bpy.context.active_object
    return _finish(ob, name, mat, loc, rot, scale, coll, True)

def prism(name, w, d, h, loc, mat, rot=(0, 0, 0), coll=None, ridge=0.0):
    """人字坡顶（三角柱）。w=檐口宽(x)，d=进深(z)，h=屋脊高。ridge: 屋脊偏移(0=居中)。"""
    hw, hd = w / 2, d / 2
    v = [(-hw, -hd, 0), (hw, -hd, 0), (hw, hd, 0), (-hw, hd, 0),
         (ridge - hw * 0.02, 0, -hd), (ridge + hw * 0.02, 0, -hd),
         (ridge - hw * 0.02, 0, hd), (ridge + hw * 0.02, 0, hd)]
    f = [(0, 1, 5, 4), (2, 3, 7, 6), (0, 4, 7, 3), (1, 2, 6, 5),
         (4, 5, 6, 7)]
    return _mesh(name, v, f, mat, loc, rot, (1, 1, 1), coll, False)

def hip(name, w, d, h, loc, mat, rot=(0, 0, 0), coll=None, back=0.55):
    """四坡顶。back: 屋脊长度占比。"""
    hw, hd = w / 2, d / 2
    rl = w * back / 2
    v = [(-hw, -hd, 0), (hw, -hd, 0), (hw, hd, 0), (-hw, hd, 0),
         (-rl, 0, h), (rl, 0, h)]
    f = [(0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4)]
    return _mesh(name, v, f, mat, loc, rot, (1, 1, 1), coll, False)

def pyr(name, w, d, h, loc, mat, rot=(0, 0, 0), coll=None):
    hw, hd = w / 2, d / 2
    v = [(-hw, -hd, 0), (hw, -hd, 0), (hw, hd, 0), (-hw, hd, 0), (0, 0, h)]
    f = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (0, 3, 2, 1)]
    return _mesh(name, v, f, mat, loc, rot, (1, 1, 1), coll, False)

def bipyr(name, r, h, loc, mat, rot=(0, 0, 0), n=6, coll=None):
    """双锥（晶体）。"""
    v = [(0, 0, h / 2), (0, 0, -h / 2)]
    for i in range(n):
        a = i / n * math.tau
        v.append((math.cos(a) * r, math.sin(a) * r, 0))
    f = []
    for i in range(n):
        j = (i + 1) % n
        f.append((0, 2 + i, 2 + j))
        f.append((1, 2 + j, 2 + i))
    return _mesh(name, v, f, mat, loc, rot, (1, 1, 1), coll, True)

def lathe(name, profile, segs, mat, loc, coll=None, noise=0.0, seed=1,
          close_top=False, close_bottom=False, gap=None, y_scale=1.0):
    """旋转成型（原生坐标：X 东 / Y 南 / Z 上）。profile=[(r,z),...]，z=高度。gap=(a0,a1) 开口。"""
    import mathutils.noise as N
    if not gap:
        angs = [i / segs * math.tau for i in range(segs)]
    else:
        a0, a1 = gap
        span = math.tau - (a1 - a0)
        angs = [a0 + (i / segs) * span for i in range(segs + 1)]
    ringv = []
    for (r, z) in profile:
        row = []
        for a in angs:
            rr = r
            if noise > 0 and abs(r) > 0.01:
                rr = r * (1.0 + N.noise(Vector((math.cos(a) * 2.1, math.sin(a) * 2.1, z * 0.7 + seed))) * noise)
            row.append((math.cos(a) * rr, math.sin(a) * rr, z * y_scale))
        ringv.append(row)
    verts = [p for row in ringv for p in row]
    faces = []
    nA = len(angs)
    for i in range(len(profile) - 1):
        for j in range(nA - 1 if gap else nA):
            a = i * nA + j
            b = i * nA + (j + 1) % nA
            c = (i + 1) * nA + (j + 1) % nA
            e = (i + 1) * nA + j
            faces.append((a, b, c, e))
    if close_top:
        cidx = len(verts)
        top = ringv[0]
        verts.append((sum(p[0] for p in top) / len(top), profile[0][1], sum(p[2] for p in top) / len(top)))
        for j in range(nA - 1 if gap else nA):
            b = (j + 1) % nA
            faces.append((cidx, b, j))
    if close_bottom:
        cidx = len(verts)
        bot = ringv[-1]
        verts.append((sum(p[0] for p in bot) / len(bot), profile[-1][1], sum(p[2] for p in bot) / len(bot)))
        base = (len(profile) - 1) * nA
        for j in range(nA - 1 if gap else nA):
            b = (j + 1) % nA
            faces.append((cidx, base + j, base + b))
    return _mesh(name, verts, faces, mat, loc, (0, 0, 0), (1, 1, 1), coll, True)

# ------------------------------------------------------------------ 建筑构件
def cornice(name, w, d, h, loc, mat, rot=(0, 0, 0), coll=None, overhang=0.9):
    return box(name, w + overhang, d + overhang, h, loc, mat, rot, coll, bevel=0.05)

def column(name, r, h, loc, mat, coll=None, verts=12, capital=True, base=True):
    parts = []
    parts.append(cyl(name + '_shaft', r, r * 0.92, h, (loc[0], loc[1], loc[2] + h / 2), mat, verts=verts, coll=coll))
    if base:
        parts.append(cyl(name + '_base', r * 1.35, r * 1.35, h * 0.05, (loc[0], loc[1], loc[2] + h * 0.025), mat, verts=verts, coll=coll))
    if capital:
        parts.append(cyl(name + '_cap', r * 1.32, r * 1.32, h * 0.05, (loc[0], loc[1], loc[2] + h * 0.975), mat, verts=verts, coll=coll))
    return parts

def colonnade(prefix, n, r, h, spacing, loc, mat, rot=0, coll=None, beam=True, beam_h=0.45, beam_d=0.8):
    out = []
    x0 = -(n - 1) * spacing / 2
    for i in range(n):
        x = x0 + i * spacing
        out += column(f"{prefix}_c{i}", r, h, (x, 0, 0), mat, coll=coll)
    if beam:
        out.append(box(f"{prefix}_beam", (n - 1) * spacing + r * 2.6, beam_d, beam_h,
                       (0, 0, h + beam_h / 2), mat, rot=(0, 0, -rot), coll=coll, bevel=0.04))
    # 把整组放到 loc/rot
    g = join(out, prefix + '_grp')
    g.location = loc
    g.rotation_euler = Euler((0, 0, D(rot)), 'XYZ')
    return g

def window(name, w, h, loc, mat_glass, mat_frame, rot=(0, 0, 0), coll=None, frame_w=0.09, arch=False, mullions=1):
    """发光窗：玻璃面板 + 石框 + 竖棂。"""
    parts = []
    t = frame_w
    parts.append(box(name + '_g', w, 0.08, h, (0, 0, 0), mat_glass, coll=coll))
    parts.append(box(name + '_fl', t, 0.16, h + t, (-w / 2, 0, 0), mat_frame, coll=coll))
    parts.append(box(name + '_fr', t, 0.16, h + t, (w / 2, 0, 0), mat_frame, coll=coll))
    parts.append(box(name + '_ft', w + t, 0.16, t, (0, 0, h / 2), mat_frame, coll=coll))
    parts.append(box(name + '_fb', w + t, 0.16, t, (0, 0, -h / 2), mat_frame, coll=coll))
    for i in range(mullions):
        mx = -w / 2 + (i + 1) * w / (mullions + 1)
        parts.append(box(name + f'_m{i}', 0.05, 0.1, h, (mx, 0, 0), mat_frame, coll=coll))
    g = join(parts, name)
    g.location = loc
    g.rotation_euler = Euler([D(a) for a in rot], 'XYZ')
    return g

def arch_top(name, w, h, loc, mat, rot=(0, 0, 0), coll=None, n=7, r=None):
    """半圆拱（楔石式，用 n 块小石拼出拱形）。"""
    r = r or w / 2
    parts = []
    for i in range(n):
        a = math.pi * (i + 0.5) / n
        x = math.cos(a) * r
        z = math.sin(a) * (r * 0.8) + h
        parts.append(box(name + f'_v{i}', r * 2.6 / n, 0.3, 0.34, (x, 0, z), mat,
                         rot=(0, D(90 - math.degrees(a)), 0), coll=coll, bevel=0.02))
    g = join(parts, name)
    g.location = loc
    g.rotation_euler = Euler([D(a) for a in rot], 'XYZ')
    return g

def arch_door(name, w, h, loc, mat_frame, mat_dark, rot=(0, 0, 0), coll=None, lantern=None):
    """拱门：暗门洞 + 拱 + 门框 + 可选两盏门灯。"""
    parts = []
    parts.append(box(name + '_cav', w, 0.12, h, (0, 0, h / 2), mat_dark, coll=coll))
    parts.append(box(name + '_jl', 0.22, 0.3, h, (-w / 2 - 0.11, 0, h / 2), mat_frame, coll=coll))
    parts.append(box(name + '_jr', 0.22, 0.3, h, (w / 2 + 0.11, 0, h / 2), mat_frame, coll=coll))
    parts.append(arch_top(name + '_arch', w + 0.44, h * 0.94, (0, 0, 0), mat_frame, coll=coll))
    g = join(parts, name)
    g.location = loc
    g.rotation_euler = Euler([D(a) for a in rot], 'XYZ')
    return g

def balustrade(name, length, h, loc, mat, coll=None, rot=(0, 0, 0), n=None):
    parts = []
    n = n or max(3, int(length / 0.55))
    for i in range(n):
        x = -length / 2 + i * length / (n - 1)
        parts.append(box(name + f'_p{i}', 0.09, 0.09, h * 0.9, (x, 0, h * 0.45), mat, coll=coll, bevel=0.01))
    parts.append(box(name + '_rail', length + 0.1, 0.14, 0.12, (0, 0, h), mat, coll=coll, bevel=0.02))
    parts.append(box(name + '_sill', length + 0.1, 0.16, 0.1, (0, 0, 0.05), mat, coll=coll, bevel=0.02))
    g = join(parts, name)
    g.location = loc
    g.rotation_euler = Euler([D(a) for a in rot], 'XYZ')
    return g

def stairs(name, w, n, rise, run, loc, mat, coll=None, rot=(0, 0, 0)):
    parts = []
    for i in range(n):
        parts.append(box(name + f'_s{i}', w, run, rise * (i + 1),
                         (0, (i - n / 2) * run, rise * (i + 1) / 2), mat, coll=coll, bevel=0.015))
    g = join(parts, name)
    g.location = loc
    g.rotation_euler = Euler([D(a) for a in rot], 'XYZ')
    return g

def tube(name, pts, r, mat, coll=None, smooth=True, res=6):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = r
    cu.bevel_resolution = 2
    cu.resolution_u = res
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0], p[1], p[2], 1)
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    if mat:
        ob.data.materials.append(mat)
    _act(ob)
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.active_object
    ob.name = name
    if coll is not None:
        for c in ob.users_collection:
            c.objects.unlink(ob)
        coll.objects.link(ob)
    if smooth:
        for p in ob.data.polygons:
            p.use_smooth = True
    return ob

def ribbon(name, pts, width, y, mat, coll=None, closed=False):
    """平地铺路用的扁带（原生坐标：pts=[(x,south)...]，y=高度）。"""
    verts = []
    n = len(pts)
    for i, (x, z) in enumerate(pts):
        if closed:
            nx, nz = pts[(i + 1) % n]
            px, pz = pts[(i - 1) % n]
        else:
            nx, nz = pts[min(i + 1, n - 1)]
            px, pz = pts[max(i - 1, 0)]
        dx, dz = nx - px, nz - pz
        L = math.hypot(dx, dz) or 1
        ox, oz = -dz / L * width / 2, dx / L * width / 2
        verts += [(x + ox, z + oz, y), (x - ox, z - oz, y)]
    faces = []
    m = n if closed else n - 1
    for i in range(m):
        a = i * 2
        b = (i * 2 + 2) % (n * 2)
        c = (i * 2 + 3) % (n * 2)
        e = i * 2 + 1
        faces.append((a, b, c, e))
    return _mesh(name, verts, faces, mat, (0, 0, 0), (0, 0, 0), (1, 1, 1), coll, False)

# ------------------------------------------------------------------ 自然物
def hash01(v, seed):
    import math
    x = math.sin(v[0] * 12.9898 + v[1] * 78.233 + v[2] * 37.719 + seed * 7.13) * 43758.5453
    return x - math.floor(x)

def vcol(ob, amount=0.07, seed=3, key='Col', luminance_only=True):
    me = ob.data
    att = me.color_attributes.get(key)
    if att is None:
        att = me.color_attributes.new(key, 'BYTE_COLOR', 'CORNER')
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            v = me.vertices[vi].co
            if luminance_only:
                h = hash01((v.x, v.y, v.z), seed)
                s = 1.0 + (h - 0.5) * 2 * amount
                att.data[li].color = (min(1, s), min(1, s), min(1, s), 1.0)
            else:
                r = 1.0 + (hash01((v.x, v.y, v.z), seed) - 0.5) * 2 * amount
                g = 1.0 + (hash01((v.x, v.y, v.z), seed + 1) - 0.5) * 2 * amount
                b = 1.0 + (hash01((v.x, v.y, v.z), seed + 2) - 0.5) * 2 * amount
                att.data[li].color = (min(1, r), min(1, g), min(1, b), 1.0)
    return ob

def tree(name, loc, h, crown_r, mat_leaf, mat_trunk, coll=None, seed=1, autumn=False, style='round', bend=0.0):
    rand = random.Random(seed)
    parts = []
    th = h * 0.42
    tilt = (rand.random() - 0.5) * 8 + bend
    parts.append(cyl(name + '_trunk', 0.16 * (h / 5), 0.22 * (h / 5), th, (0, 0, th / 2), mat_trunk,
                     rot=(0, tilt, 0), verts=8, coll=coll))
    cy = th + crown_r * 0.35
    # 树冠整体随 tilt 横向偏移（树干倾斜方向）
    cxo = math.sin(D(tilt)) * th * 0.85
    if style == 'round':
        # 主冠 + 3 个随机偏移的副球（树冠透气、立体）
        parts.append(sphere(name + '_cr1', crown_r * 0.92, (cxo, 0, cy), mat_leaf,
                            scale=(1, 1, 0.88), seg=14, ring=10, coll=coll))
        for k in range(3):
            ka = rand.random() * math.tau
            kr = crown_r * (0.55 + rand.random() * 0.35)
            kx = cxo + math.cos(ka) * crown_r * 0.55
            kz2 = math.sin(ka) * crown_r * 0.55
            ky = cy + (rand.random() * 0.7 - 0.15) * crown_r * 0.6
            parts.append(sphere(f'{name}_cr{k+1}', kr * 0.75, (kx, kz2, ky), mat_leaf,
                                scale=(1, 1, 0.82), seg=12, ring=8, coll=coll))
        if crown_r > 2.6:
            parts.append(sphere(name + '_crtop', crown_r * 0.5, (cxo + crown_r * 0.35, crown_r * 0.2, cy + crown_r * 0.55),
                                mat_leaf, scale=(1, 1, 0.8), seg=12, ring=8, coll=coll))
    else:
        parts.append(cyl(name + '_cr1', crown_r * 0.05, crown_r, crown_r * 1.5, (cxo, 0, cy + crown_r * 0.4),
                         mat_leaf, verts=8, coll=coll))
    g = join(parts, name)
    g.location = loc
    return g

def shrub(name, loc, r, mat, coll=None, seed=1, scale=(1, 1, 1)):
    o = ico(name, r, loc, mat, sub=1, rot=(0, 0, seed * 40), coll=coll, scale=scale, smooth=True)
    return o

def rock(name, loc, r, mat, coll=None, seed=1, scale=(1, 0.7, 1)):
    o = ico(name, r, loc, mat, sub=1, rot=(seed * 37 % 360, seed * 53 % 360, 0), coll=coll, scale=scale, smooth=False)
    return o

def crystal_cluster(name, loc, mat, coll=None, seed=1, n=4, h=3.0, r=0.5):
    parts = []
    rand = random.Random(seed)
    for i in range(n):
        a = i / n * math.tau + rand.random()
        rad = 0.0 if i == 0 else 0.35 + rand.random() * 0.5
        hh = h * (1.0 if i == 0 else 0.5 + rand.random() * 0.4)
        parts.append(bipyr(name + f'_c{i}', r * (0.5 + rand.random() * 0.4), hh,
                           (math.cos(a) * rad, math.sin(a) * rad, hh / 2 - 0.1),
                           mat, rot=(rand.random() * 24 - 12, rand.random() * 24 - 12, 0), n=6, coll=coll))
    g = join(parts, name)
    g.location = loc
    return g

def flagpole(name, loc, mat_pole, mat_flag, coll=None, h=6.2, wave=0.5):
    parts = []
    parts.append(cyl(name + '_pole', 0.05, 0.06, h, (0, 0, h / 2), mat_pole, verts=8, coll=coll))
    parts.append(cyl(name + '_foot', 0.22, 0.26, 0.3, (0, 0, 0.15), mat_pole, verts=10, coll=coll))
    parts.append(sphere(name + '_tip', 0.09, (0, 0, h + 0.06), mat_pole, seg=8, ring=6, coll=coll))
    # 旗面（微波浪）
    n = 8
    verts = []
    for i in range(n + 1):
        x = i / n * 1.9
        z = -wave * math.sin(i / n * math.pi * 1.5) * 0.35
        verts += [(x, 0, h - 0.42 + z * 0.2), (x, 0.02, h - 1.55 + z)]
    faces = []
    for i in range(n):
        a = i * 2
        faces.append((a, a + 2, a + 3, a + 1))
    fl = _mesh(name + '_flag', verts, faces, mat_flag, (0.03, 0, 0), (0, 0, 0), (1, 1, 1), coll, False)
    fl.data.materials.clear()
    fl.data.materials.append(mat_flag)
    g = join(parts + [fl], name)
    g.location = loc
    return g

def lantern(name, loc, mat_stone, mat_glow, coll=None, h=1.5, on=True):
    parts = []
    parts.append(box(name + '_base', 0.4, 0.4, 0.14, (0, 0, 0.07), mat_stone, coll=coll))
    parts.append(cyl(name + '_pole', 0.09, 0.11, h * 0.55, (0, 0, h * 0.275), mat_stone, verts=8, coll=coll))
    parts.append(cyl(name + '_head', 0.17, 0.13, h * 0.3, (0, 0, h * 0.7), mat_stone, verts=6, coll=coll))
    parts.append(torus(name + '_ring', 0.16, 0.024, (0, 0, h * 0.86), mat_stone, rot=(90, 0, 0), segs=18, minor=6, coll=coll))
    parts.append(box(name + '_cap', 0.34, 0.34, 0.1, (0, 0, h), mat_stone, coll=coll, bevel=0.03))
    parts.append(pyr(name + '_tip', 0.3, 0.3, 0.22, (0, 0, h + 0.16), mat_stone, coll=coll))
    if on:
        parts.append(cyl(name + '_glow', 0.11, 0.11, 0.18, (0, 0, h * 0.72), mat_glow, verts=8, coll=coll))
    g = join(parts, name)
    g.location = loc
    return g

# ------------------------------------------------------------------ 工具
def join(objs, name):
    if not objs:
        return None
    if len(objs) == 1:
        objs[0].name = name
        return objs[0]
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = name
    return ob

def ring_band(name, r, h, t, loc, mat, coll=None, segs=48, gap=None, y0=0):
    """环形矮墙（原生坐标：X 东 / Y 南 / Z 上；z0=底高，h=高）。gap=(a0,a1) 弧度开口。"""
    if gap:
        a0, a1 = gap
        span = math.tau - (a1 - a0)
        angs = [a0 + i / segs * span for i in range(segs)]
    else:
        angs = [i / segs * math.tau for i in range(segs)]
    verts = []
    nA = len(angs)
    for a in angs:
        ca, sa = math.cos(a), math.sin(a)
        verts += [(ca * (r - t / 2), sa * (r - t / 2), y0),
                  (ca * (r + t / 2), sa * (r + t / 2), y0),
                  (ca * (r + t / 2), sa * (r + t / 2), y0 + h),
                  (ca * (r - t / 2), sa * (r - t / 2), y0 + h)]
    faces = []
    for i in range(nA):
        j = (i + 1) % nA
        a = i * 4
        b = j * 4
        faces += [(a, b, b + 1, a + 1), (a + 1, b + 1, b + 2, a + 2),
                  (a + 2, b + 2, b + 3, a + 3), (a + 3, b + 3, b, a)]
    return _mesh(name, verts, faces, mat, loc, (0, 0, 0), (1, 1, 1), coll, True)
