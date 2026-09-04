# -*- coding: utf-8 -*-
"""几何组件库：手动网格 + 自动 UV 构建建筑构件。无布尔；倒角用 modifier 末尾统一 apply。"""
import bpy, math
from math import sin, cos, pi
from mathutils import Vector, Euler
from . import util
from . import mats as _mats

MODS = []

# ---------------------------------------------------------------- 底层
def _uvs(me, mode='box', scale=0.45):
    """盒式投影 UV：按"世界米制"比例，保证同一贴图在所有表面上密度一致。
    scale：1 米织物重复 1 次单位（即贴图 repeat 密度 = scale）。"""
    uv = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i])) if mode == 'box' else None
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            if mode == 'cyl':
                if abs(n[2]) > 0.7:
                    u, w = v.x, v.y
                else:
                    u = math.atan2(v.y, v.x) / (2 * pi)
                    w = v.z
                uvd = (u * scale, w * scale)
            else:
                if ax == 0: u, w = v.y, v.z
                elif ax == 1: u, w = v.x, v.z
                else: u, w = v.x, v.y
                uvd = (u * scale, w * scale)
            uv.data[li].uv = uvd

def _mesh(name, verts, faces, mat, ckey=None, uv='box', uvscale=0.5, smooth=False, bevel=0.0):
    me = bpy.data.meshes.new(name)
    me.from_pydata([Vector(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate()
    me.update()
    _uvs(me, uv, uvscale)
    ob = bpy.data.objects.new(name, me)
    if ckey:
        util.coll(ckey).objects.link(ob)
    if mat:
        me.materials.append(mat)
    if smooth:
        util.shade(ob, True, 40)
    if bevel > 0:
        m = ob.modifiers.new('bv', 'BEVEL')
        m.width = bevel
        m.segments = 1
        m.limit_method = 'ANGLE'
        m.angle_limit = math.radians(50)
        MODS.append((ob, m))
    return ob

def box(tag, sx, sy, sz, mat, loc=(0, 0, 0), rot=(0, 0, 0), ckey=None, bevel=0.0, uvscale=0.45):
    x, y, z = sx / 2, sy / 2, sz / 2
    vs = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
          (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    fs = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    ob = _mesh(tag, vs, fs, mat, ckey, bevel=bevel, uvscale=uvscale)
    ob.location = loc
    ob.rotation_euler = Euler(rot, 'XYZ')
    if ckey:
        ob.name = f'{ckey}_{tag}'
    return ob

def ngon(tag, n, r, h, mat, loc=(0, 0, 0), rot=(0, 0, 0), ckey=None, r_top=None,
         cap=True, smooth=True, uvscale=0.5, phase=0.0, bevel=0.0):
    r0, r1 = r, r_top if r_top is not None else r
    vs, fs = [], []
    for i in range(n):
        a = 2 * pi * i / n + phase
        vs.append((cos(a) * r0, sin(a) * r0, -h / 2))
    for i in range(n):
        a = 2 * pi * i / n + phase
        vs.append((cos(a) * r1, sin(a) * r1, h / 2))
    for i in range(n):
        j = (i + 1) % n
        fs.append((i, j, n + j, n + i))
    if cap:
        fs.append(tuple(range(n - 1, -1, -1)))
        fs.append(tuple(range(n, 2 * n)))
    ob = _mesh(tag, vs, fs, mat, ckey, uv='cyl', uvscale=uvscale, smooth=smooth, bevel=bevel)
    ob.location = loc
    ob.rotation_euler = Euler(rot, 'XYZ')
    if ckey:
        ob.name = f'{ckey}_{tag}'
    return ob

def sphere(tag, r, mat, loc, ckey=None, seg=14, rings=8, scale=(1, 1, 1), rot=(0, 0, 0), uvscale=0.5):
    vs, fs = [], []
    for i in range(rings + 1):
        phi = pi * i / rings
        for j in range(seg):
            th = 2 * pi * j / seg
            vs.append((sin(phi) * cos(th) * r, sin(phi) * sin(th) * r, cos(phi) * r))
    for i in range(rings):
        for j in range(seg):
            a = i * seg + j
            b = i * seg + (j + 1) % seg
            c = (i + 1) * seg + (j + 1) % seg
            d = (i + 1) * seg + j
            fs.append((a, b, c, d))
    ob = _mesh(tag, vs, fs, mat, ckey, uv='cyl', uvscale=uvscale, smooth=True)
    ob.location = loc
    ob.rotation_euler = Euler(rot, 'XYZ')
    ob.scale = scale
    if ckey:
        ob.name = f'{ckey}_{tag}'
    return ob

def dome(tag, r, h, mat, loc, ckey=None, seg=24, rings=7, gap=None, uvscale=0.5):
    vs, fs = [], []
    for i in range(rings + 1):
        phi = (pi / 2) * i / rings
        rr = cos(phi) * r
        z = sin(phi) * h
        for j in range(seg + 1):
            th = 2 * pi * j / seg
            vs.append((cos(th) * rr, sin(th) * rr, z))
    for i in range(rings):
        for j in range(seg):
            a = i * (seg + 1) + j
            b = i * (seg + 1) + j + 1
            c = (i + 1) * (seg + 1) + j + 1
            d = (i + 1) * (seg + 1) + j
            if gap:
                ag = 360 * j / seg
                a0, a1 = gap
                if a0 <= ag <= a1 or (a0 - 360) <= ag <= (a1 - 360):
                    continue
            fs.append((a, b, c, d))
    ob = _mesh(tag, vs, fs, mat, ckey, uv='cyl', uvscale=uvscale, smooth=True)
    ob.location = loc
    if ckey:
        ob.name = f'{ckey}_{tag}'
    return ob

def tube(tag, pts, r, mat, ckey=None, n=8, uvscale=0.5):
    pts = [Vector(p) for p in pts]
    vs, fs = [], []
    up = Vector((0, 0, 1))
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        side = t.cross(up)
        if side.length < 1e-4:
            side = Vector((1, 0, 0))
        side.normalize()
        up2 = side.cross(t).normalized()
        for j in range(n):
            a = 2 * pi * j / n
            vs.append(tuple(p + side * cos(a) * r + up2 * sin(a) * r))
    rings = len(pts)
    for i in range(rings - 1):
        for j in range(n):
            a = i * n + j
            b = i * n + (j + 1) % n
            c = (i + 1) * n + (j + 1) % n
            d = (i + 1) * n + j
            fs.append((a, b, c, d))
    ob = _mesh(tag, vs, fs, mat, ckey, uv='cyl', uvscale=uvscale, smooth=True)
    if ckey:
        ob.name = f'{ckey}_{tag}'
    return ob

def ring_tube(tag, R, r, mat, loc, ckey=None, n=24, m=8, rot=(0, 0, 0)):
    loc = _L3(loc)
    vs, fs = [], []
    for i in range(n):
        a = 2 * pi * i / n
        for j in range(m):
            b = 2 * pi * j / m
            vs.append((cos(a) * (R + r * cos(b)), sin(a) * (R + r * cos(b)), r * sin(b)))
    for i in range(n):
        for j in range(m):
            a = i * m + j
            b = i * m + (j + 1) % m
            c = ((i + 1) % n) * m + (j + 1) % m
            d = ((i + 1) % n) * m + j
            fs.append((a, b, c, d))
    ob = _mesh(tag, vs, fs, mat, ckey, uv='cyl', uvscale=0.8, smooth=True)
    ob.location = loc
    ob.rotation_euler = Euler(rot, 'XYZ')
    if ckey:
        ob.name = f'{ckey}_{tag}'
    return ob

def poly_prism(tag, pts2d, thick, mat, loc=(0, 0, 0), rot=(0, 0, 0), ckey=None, bevel=0.0, uvscale=0.5):
    n = len(pts2d)
    vs = [(x, y, -thick / 2) for x, y in pts2d] + [(x, y, thick / 2) for x, y in pts2d]
    fs = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        fs.append((i, j, n + j, n + i))
    ob = _mesh(tag, vs, fs, mat, ckey, bevel=bevel, uvscale=uvscale)
    ob.location = loc
    ob.rotation_euler = Euler(rot, 'XYZ')
    if ckey:
        ob.name = f'{ckey}_{tag}'
    return ob

# ---------------------------------------------------------------- 构件
def gable_roof(tag, L, W, rise, mat, ckey, loc=(0, 0, 0), rot=(0, 0, 0), t=0.28, over=0.55, ridge=True):
    objs = []
    half = W / 2 + over
    ang = math.atan2(rise, half)
    sl = math.sqrt(half ** 2 + rise ** 2) + t * 0.4
    for s in (1, -1):
        o = box(f'{tag}_slope{s}', L + over * 2, sl, t, mat, ckey=ckey, bevel=0.03)
        o.location = (loc[0], loc[1] + s * half / 2, loc[2] + rise / 2)
        o.rotation_euler = Euler((rot[0], rot[1] + s * (-ang), rot[2]), 'XYZ')
        objs.append(o)
    if ridge:
        objs.append(box(f'{tag}_ridge', L + over * 2, 0.35, 0.3, mat, ckey=ckey,
                        loc=(loc[0], loc[1], loc[2] + rise + 0.05)))
    return objs

def gable_end(tag, W, rise, mat, ckey, loc, rot=(0, 0, 0), t=0.22):
    pts = [(-W / 2, 0), (W / 2, 0), (0, rise)]
    return [poly_prism(tag, pts, t, mat, loc=loc, rot=rot, ckey=ckey)]

def stair(tag, steps, w, rise, run, mat, ckey, loc=(0, 0, 0), rot=(0, 0, 0)):
    vs, fs = [], []
    for i in range(steps):
        x0 = i * run
        vs += [(x0, -w / 2, 0), (x0 + run, -w / 2, 0), (x0 + run, -w / 2, (i + 1) * rise), (x0, -w / 2, (i + 1) * rise),
               (x0, w / 2, 0), (x0 + run, w / 2, 0), (x0 + run, w / 2, (i + 1) * rise), (x0, w / 2, (i + 1) * rise)]
    for i in range(steps):
        b = i * 8
        fs += [(b, b + 1, b + 2, b + 3), (b + 7, b + 6, b + 5, b + 4),
               (b, b + 4, b + 5, b + 1), (b + 1, b + 5, b + 6, b + 2), (b + 2, b + 6, b + 7, b + 3)]
    ob = _mesh(tag, vs, fs, mat, ckey)
    ob.location = loc
    ob.rotation_euler = Euler(rot, 'XYZ')
    return ob

def colonnade(tag, n_posts, w, h, post_r, mat_post, mat_top, ckey, loc=(0, 0, 0), rot=(0, 0, 0)):
    objs = []
    gap = w / max(n_posts - 1, 1)
    for i in range(n_posts):
        x = -w / 2 + i * gap
        objs.append(ngon(f'{tag}_p{i}', 12, post_r, h, mat_post,
                         loc=(loc[0] + x, loc[1], loc[2] + h / 2), ckey=ckey, uvscale=0.8))
        objs.append(box(f'{tag}_b{i}', post_r * 2.6, post_r * 2.6, 0.16, mat_post,
                        loc=(loc[0] + x, loc[1], loc[2] + 0.08), ckey=ckey))
    objs.append(box(f'{tag}_arch', w + post_r * 2, post_r * 3.2, 0.4, mat_top, ckey=ckey,
                    loc=(loc[0], loc[1], loc[2] + h + 0.2)))
    for o in objs:
        o.rotation_euler = Euler((o.rotation_euler.x + rot[0], o.rotation_euler.y + rot[1],
                                  o.rotation_euler.z + rot[2]), 'XYZ')
    return objs

def rail(tag, length, h, mat, ckey, loc=(0, 0, 0), rot=(0, 0, 0), posts=None):
    objs = [box(f'{tag}_top', length, 0.12, 0.1, mat, ckey=ckey, loc=(loc[0], loc[1], loc[2] + h)),
            box(f'{tag}_mid', length, 0.08, 0.08, mat, ckey=ckey, loc=(loc[0], loc[1], loc[2] + h * 0.55))]
    n = posts or max(2, int(length / 1.4))
    for i in range(n + 1):
        x = -length / 2 + length * i / n
        objs.append(box(f'{tag}_p{i}', 0.09, 0.09, h, mat, ckey=ckey, loc=(loc[0] + x, loc[1], loc[2] + h / 2)))
    for o in objs:
        o.rotation_euler = Euler((o.rotation_euler.x + rot[0], o.rotation_euler.y + rot[1],
                                  o.rotation_euler.z + rot[2]), 'XYZ')
    return objs

def arch_portal(tag, w, h, thick, mat, ckey, loc=(0, 0, 0), rot=(0, 0, 0), nv=9, pane=None):
    """拱门：双柱 + 楔石拱 + 拱肩补墙。"""
    objs = []
    pw = max(0.28, w * 0.14)
    pier_h = h - w / 2
    for s in (1, -1):
        objs.append(box(f'{tag}_pier{s}', pw, thick, pier_h, mat, ckey=ckey))
        objs[-1].location = (s * (w / 2 + pw / 2), 0, pier_h / 2)
    r0 = w / 2
    for i in range(nv):
        a = pi * (i + 0.5) / nv
        vx, vz = cos(a) * r0, sin(a) * r0
        seg = w / nv
        o = box(f'{tag}_vous{i}', seg * 1.35, thick, seg * 0.9, mat, ckey=ckey)
        o.location = (vx, 0, pier_h + vz)
        o.rotation_euler = Euler((0, a, 0), 'XYZ')
        objs.append(o)
    objs.append(box(f'{tag}_lintel', w + pw * 2.6, thick, 0.36, mat, ckey=ckey,
                    loc=(0, 0, pier_h + w / 2 + 0.18)))
    for s in (1, -1):
        o = box(f'{tag}_spandrel{s}', w * 0.36, thick, w * 0.30, mat, ckey=ckey)
        o.location = (s * (w * 0.35), 0, pier_h + w * 0.36)
        objs.append(o)
    if pane:
        objs.append(box(f'{tag}_pane', w * 0.94, thick * 0.4, h * 0.06, pane, ckey=ckey,
                        loc=(0, 0, h * 0.35 + w * 0.1)))
    for o in objs:
        o.location = (o.location.x + loc[0], o.location.y + loc[1], o.location.z + loc[2])
        o.rotation_euler = Euler((rot[0], rot[1], rot[2] + o.rotation_euler.z), 'XYZ')
    return objs

def win_arch(tag, w, h, mat_wall, mat_glow, ckey, loc=(0, 0, 0), rot=(0, 0, 0), bars=2, frame=0.1):
    objs = [box(f'{tag}_glow', w, 0.1, h, mat_glow, ckey=ckey)]
    for i in range(bars):
        x = -w / 2 + w * (i + 1) / (bars + 1)
        objs.append(box(f'{tag}_bar{i}', 0.05, 0.14, h, mat_wall, ckey=ckey, loc=(x, 0, 0)))
    objs.append(box(f'{tag}_top', w + frame * 2, 0.16, frame, mat_wall, ckey=ckey, loc=(0, 0, h / 2 + frame / 2)))
    objs.append(box(f'{tag}_bot', w + frame * 2, 0.16, frame, mat_wall, ckey=ckey, loc=(0, 0, -h / 2 - frame / 2)))
    for s in (1, -1):
        objs.append(box(f'{tag}_side{s}', frame, 0.16, h, mat_wall, ckey=ckey, loc=(s * (w / 2 + frame / 2), 0, 0)))
    for o in objs:
        o.location = (o.location.x + loc[0], o.location.y + loc[1], o.location.z + loc[2])
        o.rotation_euler = Euler((rot[0], rot[1], rot[2] + o.rotation_euler.z), 'XYZ')
    return objs

def win_round(tag, r, mat_rim, mat_glow, ckey, loc=(0, 0, 0), rot=(0, 0, 0)):
    o1 = ngon(f'{tag}_g', 16, r, 0.08, mat_glow, loc=loc, rot=rot, ckey=ckey, phase=pi / 16)
    o2 = ring_tube(f'{tag}_rim', r, 0.055, mat_rim, loc=loc, ckey=ckey, n=20, m=6)
    o2.rotation_euler = Euler((rot[0], rot[1], rot[2]), 'XYZ')
    return [o1, o2]

def carve_band(tag, L, mat, ckey, loc=(0, 0, 0), rot=(0, 0, 0), h=0.22, depth=0.035, n=None):
    """浮雕条（假刻字：一列高矮不齐小块）。"""
    rnd = util.R
    objs = [box(f'{tag}_base', L, 0.08, h, mat, ckey=ckey, loc=loc)]
    n = n or max(2, int(L / 0.14))
    for i in range(n):
        w = 0.055 + rnd.random() * 0.05
        hh = h * (0.35 + rnd.random() * 0.5)
        x = -L / 2 + L * (i + 0.5) / n
        objs.append(box(f'{tag}_g{i}', w, depth, hh, mat, ckey=ckey,
                        loc=(loc[0] + x, loc[1], loc[2] + h * 0.1 + rnd.random() * 0.1)))
    for o in objs:
        o.rotation_euler = Euler((rot[0], rot[1], rot[2] + o.rotation_euler.z), 'XYZ')
    return objs

def banner(tag, w, h, mat, ckey, loc=(0, 0, 0), rot=(0, 0, 0), phase=0.6, wave=0.09):
    nx, nz = 10, 5
    vs, fs = [], []
    for iz in range(nz + 1):
        for ix in range(nx + 1):
            x = -w / 2 + w * ix / nx
            z = -h / 2 + h * iz / nz
            y = -sin(x / w * pi * 2.2 + phase) * wave * (0.4 + 0.6 * ix / nx)
            vs.append((x, y, z))
    for iz in range(nz):
        for ix in range(nx):
            a = iz * (nx + 1) + ix
            fs.append((a, a + 1, a + nx + 2, a + nx + 1))
    ob = _mesh(tag, vs, fs, mat, ckey, uvscale=0.3)
    ob.location = loc
    ob.rotation_euler = Euler(rot, 'XYZ')
    return ob

def books(tag, mat1, mat2, ckey, loc, rot=(0, 0, 0), n=4, scale=0.12):
    loc = _L3(loc)
    rnd = util.R
    objs = []
    x = 0
    for i in range(n):
        b = box(f'{tag}_{i}', scale * (0.7 + rnd.random() * 0.5), scale * (0.85 + rnd.random() * 0.4),
                scale * (0.35 + rnd.random() * 0.3), mat1 if i % 2 else mat2, ckey=ckey)
        b.location = (loc[0] + x, loc[1], loc[2] + scale * 0.18)
        b.rotation_euler = Euler((rot[0] + rnd.random() * 0.16, rot[1], rot[2] + rnd.random() * 0.12), 'XYZ')
        x += scale * 1.05
        objs.append(b)
    return objs

def _L3(loc):
    return (loc[0], loc[1], loc[2] if len(loc) > 2 else 0.0)

def lantern(tag, mat_stone, mat_glow, ckey, loc, s=1.0):
    loc = _L3(loc)
    return [box(f'{tag}_foot', 0.5 * s, 0.5 * s, 0.22 * s, mat_stone, ckey=ckey, loc=(loc[0], loc[1], loc[2] + 0.11 * s)),
            ngon(f'{tag}_body', 6, 0.2 * s, 0.5 * s, mat_stone, loc=(loc[0], loc[1], loc[2] + 0.55 * s), ckey=ckey, phase=pi / 6),
            ngon(f'{tag}_cap', 6, 0.3 * s, 0.22 * s, mat_stone, loc=(loc[0], loc[1], loc[2] + 0.9 * s), ckey=ckey, r_top=0.02, phase=pi / 6),
            ngon(f'{tag}_gem', 6, 0.13 * s, 0.3 * s, mat_glow, loc=(loc[0], loc[1], loc[2] + 0.56 * s), ckey=ckey, r_top=0.11 * s, phase=pi / 6)]

def tree(tag, kind, mat_trunk, mat_leaf, ckey, loc, s=1.0, crown=None):
    loc = _L3(loc)
    rnd = util.R
    objs = []
    if kind == 'pine':
        objs.append(ngon(f'{tag}_t', 8, 0.14 * s, 1.6 * s, mat_trunk, loc=(loc[0], loc[1], loc[2] + 0.8 * s),
                         ckey=ckey, r_top=0.08 * s))
        for i, (rr, hh, zz) in enumerate([(1.15, 1.5, 1.1), (0.9, 1.3, 1.9), (0.55, 1.1, 2.6)]):
            objs.append(ngon(f'{tag}_c{i}', 9, rr * s, hh * s, mat_leaf,
                             loc=(loc[0], loc[1], loc[2] + zz * s), ckey=ckey, r_top=0.02 * s))
        return objs
    th = (1.6 if kind == 'big' else 1.1) * s
    objs.append(ngon(f'{tag}_t', 9, 0.16 * s * (2 if kind == 'big' else 1), th, mat_trunk,
                     loc=(loc[0], loc[1], loc[2] + th / 2), ckey=ckey, r_top=0.1 * s))
    nb = 4 if kind == 'big' else 2
    for i in range(nb):
        a = rnd.uniform(0, 2 * pi)
        L = (0.9 if kind == 'big' else 0.7) * s
        p0 = (loc[0], loc[1], loc[2] + th * 0.85)
        p1 = (loc[0] + cos(a) * L, loc[1] + sin(a) * L, loc[2] + th + L * rnd.uniform(0.2, 0.6))
        objs.append(tube(f'{tag}_b{i}', [p0, p1], 0.05 * s, mat_trunk, ckey))
    cr = crown or ((2.2 if kind == 'big' else 1.0) * s)
    nc = 6 if kind == 'big' else 4
    for i in range(nc):
        a = rnd.uniform(0, 2 * pi)
        d = rnd.uniform(0, cr * 0.8)
        rr = cr * rnd.uniform(0.45, 0.75)
        objs.append(sphere(f'{tag}_s{i}', rr, mat_leaf,
                           (loc[0] + cos(a) * d, loc[1] + sin(a) * d, loc[2] + th + cr * rnd.uniform(0.15, 0.9)),
                           ckey, seg=10, rings=6, scale=(1, 1, 0.82)))
    return objs

def bush(tag, mat, ckey, loc, r=0.5):
    loc = _L3(loc)
    o = sphere(tag, r, mat, loc, ckey, seg=10, rings=6, scale=(1, 1, 0.62))
    o.rotation_euler = Euler((0, 0, util.R.uniform(0, 3)), 'XYZ')
    return o

def flower_cluster(tag, mat, ckey, loc, n=6, r=0.32):
    loc = _L3(loc)
    rnd = util.R
    objs = [sphere(f'{tag}_g', r * 0.75, _mats.M('leaf'), (loc[0], loc[1], loc[2] + 0.06), ckey, seg=8, rings=4, scale=(1, 1, 0.5))]
    for i in range(n):
        a = rnd.uniform(0, 2 * pi)
        d = rnd.uniform(0, r)
        objs.append(sphere(f'{tag}_{i}', rnd.uniform(0.045, 0.085), mat,
                           (loc[0] + cos(a) * d, loc[1] + sin(a) * d, loc[2] + 0.16 + rnd.uniform(0, 0.08)),
                           ckey, seg=6, rings=4))
    return objs

def crystal(tag, mat, ckey, loc, h=1.0, r=0.16, rot=None, n=4):
    vs = [(0, 0, h * 0.62), (0, 0, -h * 0.38)]
    for i in range(n):
        a = 2 * pi * i / n
        vs.append((cos(a) * r, sin(a) * r, 0))
    fs = []
    for i in range(n):
        j = (i + 1) % n
        fs.append((0, j + 2, i + 2))
        fs.append((1, i + 2, j + 2))
    ob = _mesh(f'{tag}_c', vs, fs, mat, ckey, uvscale=0.6, smooth=False)
    ob.location = loc
    if rot:
        ob.rotation_euler = Euler(rot, 'XYZ')
    return [ob]

def crystal_cluster(tag, mat, ckey, loc, n=6, h=3.0, r=0.5):
    rnd = util.R
    objs = []
    for i in range(n):
        main = i == 0
        a = rnd.uniform(0, 2 * pi)
        d = rnd.uniform(0, r)
        hh = h * (1.0 if main else rnd.uniform(0.35, 0.7))
        rr = r * (0.5 if main else rnd.uniform(0.22, 0.4))
        x, y = cos(a) * d, sin(a) * d
        objs += crystal(f'{tag}{i}', mat, ckey, (loc[0] + x, loc[1] + y, loc[2]),
                        h=hh, r=rr, rot=(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(0, 3)), n=4)
    return objs

def tombstone(tag, mat, ckey, loc, rot=(0, 0, 0), w=0.55, h=0.9, t=0.14, s=1.0):
    pts = [(-w / 2, 0), (w / 2, 0), (w / 2, h * 0.62)]
    for i in range(5):
        a = pi * i / 4
        pts.append((cos(a) * w / 2, h * 0.62 + sin(a) * w / 2))
    pts.append((-w / 2, h * 0.62))
    return poly_prism(tag, [(x * s, y * s) for x, y in pts], t * s, mat, loc=loc, rot=rot, ckey=ckey, bevel=0.02)

def statue(tag, kind, mat, ckey, loc, rot=(0, 0, 0), h=2.2):
    objs = [box(f'{tag}_base', 0.9 * h / 2.2, 0.9 * h / 2.2, 0.24 * h / 2.2, mat, ckey=ckey, loc=(0, 0, 0.12 * h / 2.2))]
    k = h / 2.2
    if kind == 'dwarf':
        objs.append(box(f'{tag}_legs', 0.62 * k, 0.4 * k, 0.55 * k, mat, ckey=ckey, loc=(0, 0, 0.5 * k)))
        objs.append(box(f'{tag}_torso', 0.78 * k, 0.5 * k, 0.85 * k, mat, ckey=ckey, loc=(0, 0, 1.15 * k)))
        objs.append(sphere(f'{tag}_head', 0.22 * k, mat, (0, 0, 1.82 * k), ckey, seg=10, rings=6))
        objs.append(box(f'{tag}_arm', 0.62 * k, 0.2 * k, 0.2 * k, mat, ckey=ckey, loc=(0.45 * k, 0.05 * k, 1.28 * k), rot=(0, 0.15, 0.35)))
        objs.append(box(f'{tag}_hh', 0.5 * k, 0.14 * k, 0.14 * k, mat, ckey=ckey, loc=(0.72 * k, 0.12 * k, 1.52 * k), rot=(0, -0.5, 0.35)))
        objs.append(box(f'{tag}_hw', 0.3 * k, 0.3 * k, 0.2 * k, mat, ckey=ckey, loc=(0.88 * k, 0.16 * k, 1.62 * k), rot=(0, -0.5, 0.35)))
    else:
        objs.append(box(f'{tag}_legs', 0.34 * k, 0.34 * k, 0.85 * k, mat, ckey=ckey, loc=(0, 0, 0.62 * k)))
        objs.append(box(f'{tag}_torso', 0.5 * k, 0.34 * k, 0.8 * k, mat, ckey=ckey, loc=(0, 0, 1.5 * k)))
        objs.append(sphere(f'{tag}_head', 0.2 * k, mat, (0, 0, 2.05 * k), ckey, seg=10, rings=6))
        objs.append(box(f'{tag}_arm', 0.55 * k, 0.14 * k, 0.16 * k, mat, ckey=ckey, loc=(0.34 * k, 0.04 * k, 1.7 * k), rot=(0, 0.1, 0.9)))
        arc = []
        for i in range(7):
            a = -1.4 + i * 0.45
            arc.append((0.5 * k + cos(a) * 0.42 * k, 0.1 * k, 1.5 * k + sin(a) * 0.42 * k))
        objs.append(tube(f'{tag}_bow', arc, 0.035 * k, mat, ckey))
    for o in objs:
        o.location = (o.location.x + loc[0], o.location.y + loc[1], o.location.z + loc[2])
        o.rotation_euler = Euler((rot[0], rot[1], rot[2] + o.rotation_euler.z), 'XYZ')
    return objs

def basket(tag, mat_wood, mat_rope, ckey, loc, r=0.8, h=0.62):
    prof = [(0.55, 0), (0.85, 0.18), (1.0, 0.45), (0.92, 0.85), (0.83, 1.0)]
    n = 16
    vs, fs, rings = [], [], []
    for (pr, zz) in prof:
        ring = []
        for i in range(n):
            a = 2 * pi * i / n
            ring.append(len(vs))
            vs.append((cos(a) * pr * r, sin(a) * pr * r, zz * h))
        rings.append(ring)
    for k in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            fs.append((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]))
    ob = _mesh(tag, vs, fs, mat_wood, ckey, uv='cyl', uvscale=0.8, smooth=True)
    ob.location = loc
    rim = ring_tube(tag + '_rim', r * 0.86, 0.05, mat_rope, (loc[0], loc[1], loc[2] + h), ckey, n=20, m=6)
    arms = [tube(tag + '_a1', [(loc[0], loc[1], loc[2] + h), (loc[0] + 0.3, loc[1], loc[2] + h + 0.5),
                               (loc[0], loc[1], loc[2] + h + 0.62)], 0.035, mat_rope, ckey),
            tube(tag + '_a2', [(loc[0], loc[1], loc[2] + h), (loc[0] - 0.3, loc[1], loc[2] + h + 0.5),
                               (loc[0], loc[1], loc[2] + h + 0.62)], 0.035, mat_rope, ckey)]
    return [ob, rim] + arms

def rope(tag, mat, ckey, p0, p1, sag=0.0, r=0.03):
    p0, p1 = Vector(p0), Vector(p1)
    pts = []
    for i in range(9):
        t = i / 8
        p = p0.lerp(p1, t)
        p.z -= sin(t * pi) * sag
        pts.append(tuple(p))
    return tube(tag, pts, r, mat, ckey)

def flagpole(tag, mat_pole, mat_flag, ckey, loc, h=6.0):
    loc = _L3(loc)
    objs = [ngon(f'{tag}_pole', 8, 0.045, h, mat_pole, loc=(loc[0], loc[1], loc[2] + h / 2), ckey=ckey, uvscale=0.8),
            ngon(f'{tag}_base', 8, 0.3, 0.24, mat_pole, loc=(loc[0], loc[1], loc[2] + 0.12), ckey=ckey),
            banner(f'{tag}_b', 1.7, 1.15, mat_flag, ckey, loc=(loc[0] + 0.88, loc[1], loc[2] + h - 0.75), rot=(0, 0, pi / 2))]
    return objs
