# -*- coding: utf-8 -*-
"""
星槎学院 · 可复用建筑构件
- box_grid：细分盒体（顶点色需要密度）
- stone_vcol：石墙顶点色（砌缝层理 + 近地脏污 + 噪声）
- window / door / gable_roof / hip_roof / chimney / column / lantern / banner
"""
import bmesh
import math
import random
from mathutils import Vector, Matrix
from util import *


# ------------------------------------------------------------------ 细分盒体
def box_grid(name, size, loc, collection, mat=None, cell=0.7, rot=(0, 0, 0), origin='bottom'):
    sx, sy, sz = size
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sy, (v.co.z + (0.5 if origin == 'bottom' else 0.0)) * sz))
    cuts = max(1, int(round(max(sx, sy, sz) / cell)))
    if cuts > 1:
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    ob = bm_to_obj(name, bm, collection, mat)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


# ------------------------------------------------------------------ 顶点色配方
def stone_vcol(ob, base_hex, seed=0, ground_z=0.0, course=0.55, grime=0.28, noise_amt=0.10, tint=None):
    """
    石墙：横向砌缝（course 高度带）、近地面变脏、低频噪声。
    ground_z：对象局部坐标中的地面高度（用于脏污渐变）。
    """
    base = hex2lin(base_hex)[:3]
    if tint:
        base = mix(base, hex2lin(tint)[:3], 0.35)
    mw = ob.matrix_world

    def f(co, n):
        w = mw @ co
        row = math.floor(co.z / course)
        band = (co.z / course) % 1.0
        k = 1.0 - 0.14 * smoothstep(0.88, 0.97, band)  # 横缝
        # 竖缝（错缝砌法）：沿墙面切向的坐标
        u = (w.x * 0.7 + w.y * 0.7 + (row % 2) * 0.5 * course * 1.8)
        vb = (u / (course * 1.8)) % 1.0
        k *= 1.0 - 0.08 * smoothstep(0.92, 0.98, vb)
        # 每块石头略有色差
        blk = fbm(math.floor(u / (course * 1.8)) * 1.7, row * 2.3, 0.0, oct=1, seed=seed + 3)
        k *= 1.0 + 0.07 * blk
        k *= 1.0 + noise_amt * fbm(w.x / 2.2, w.y / 2.2, w.z / 2.2, oct=3, seed=seed)
        g = smoothstep(1.6, 0.0, co.z - ground_z)
        k *= 1.0 - grime * g
        # 顶部略亮（受光/风化）
        k *= 1.0 + 0.05 * smoothstep(0.0, 8.0, co.z - ground_z)
        return (base[0] * k, base[1] * k, base[2] * k)
    set_vcol(ob, f)


def roof_vcol(ob, base_hex, seed=0, streak=0.12, moss_hex=None, moss=0.0):
    base = hex2lin(base_hex)[:3]
    mossc = hex2lin(moss_hex)[:3] if moss_hex else None
    mw = ob.matrix_world

    def f(co, n):
        w = mw @ co
        k = 1.0 + streak * fbm(w.x / 1.1, w.y / 1.1, w.z / 1.1, oct=2, seed=seed)
        k *= 1.0 + 0.06 * math.sin(w.x * 6.0) * math.sin(w.y * 6.0)
        c = (base[0] * k, base[1] * k, base[2] * k)
        if mossc and moss > 0:
            m = smoothstep(0.35, 0.75, 0.5 + 0.5 * fbm(w.x / 1.6, w.y / 1.6, 0.3, oct=2, seed=seed + 7)) * moss
            m *= smoothstep(0.3, -0.6, n.z)  # 北坡/低处更多苔藓 → 用法线 z 近似
            c = mix(c, mossc, m * 0.7)
        return c
    set_vcol(ob, f)


def wood_vcol(ob, base_hex, seed=0, grain=0.14):
    base = hex2lin(base_hex)[:3]
    mw = ob.matrix_world

    def f(co, n):
        w = mw @ co
        k = 1.0 + grain * fbm(w.x / 0.7, w.y / 4.0, w.z / 4.0, oct=2, seed=seed)
        return (base[0] * k, base[1] * k, base[2] * k)
    set_vcol(ob, f)


# ------------------------------------------------------------------ 门窗
def window(name, pos, yaw, w, h, collection, M, kind='lancet', glass='window', sill=True, depth=0.22, frame_mat=None):
    """
    嵌入式窗：pos 为窗中心（外墙面上），yaw 为外法线方向角。
    由内凹框 + 发光玻璃组成。kind: lancet(尖) / round(圆) / square。
    """
    fm = frame_mat or M['window_frame']
    objs = []
    c, s = math.cos(yaw), math.sin(yaw)
    n = Vector((c, s, 0))
    t = Vector((-s, c, 0))
    p = Vector(pos)
    if kind == 'round':
        fr = torus(name + '_frame', w * 0.55, 0.06, p, collection, fm, segs=16, rsegs=6)
        fr.matrix_world = Matrix.Translation(p - n * depth * 0.15) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(math.pi / 2, 4, 'Y')
        g = lathe(name + '_glass', [(w * 0.5, 0), (w * 0.5, 0.05)], 16, p, collection, M[glass], smooth=False)
        g.matrix_world = Matrix.Translation(p - n * (depth * 0.3)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(math.pi / 2, 4, 'Y')
        g['fx'] = 'window'
        objs += [fr, g]
        return objs
    # 方/尖窗：框为薄壳盒，玻璃为立板
    hh = h
    # 框：四根细边条（不再是整块深色盒子）
    fw = 0.07
    for (off, size) in (((-w / 2 - fw / 2, 0), (fw, hh + fw * 2)), ((w / 2 + fw / 2, 0), (fw, hh + fw * 2)),
                        ((0, -hh / 2 - fw / 2), (w, fw)), ((0, hh / 2 + fw / 2), (w, fw))):
        objs.append(box(name + '_f%d' % len(objs), (depth * 0.5, size[0], size[1]), p + t * off[0] + Vector((0, 0, off[1])) - n * (depth * 0.2), collection, fm, rot=(0, 0, yaw)))
    glass_ob = box(name + '_glass', (0.04, w, hh), p - n * (depth * 0.35), collection, M[glass], rot=(0, 0, yaw))
    glass_ob['fx'] = 'window'
    objs.append(glass_ob)
    # 十字窗棂
    objs.append(box(name + '_mv', (0.05, 0.05, hh), p - n * (depth * 0.3), collection, fm, rot=(0, 0, yaw)))
    objs.append(box(name + '_mh', (0.05, w, 0.05), p - n * (depth * 0.3) + Vector((0, 0, hh * 0.1)), collection, fm, rot=(0, 0, yaw)))
    if kind == 'lancet':
        # 尖拱头：三角楔
        verts = [(-depth * 0.5, -w / 2 - 0.08, hh / 2), (-depth * 0.5, w / 2 + 0.08, hh / 2), (-depth * 0.5, 0, hh / 2 + w * 0.55),
                 (depth * 0.5, -w / 2 - 0.08, hh / 2), (depth * 0.5, w / 2 + 0.08, hh / 2), (depth * 0.5, 0, hh / 2 + w * 0.55)]
        faces = [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
        gl2 = mesh_from(name + '_glass2', [(0, -w / 2, hh / 2 - 0.01), (0, w / 2, hh / 2 - 0.01), (0, 0, hh / 2 + w * 0.5)], [(0, 1, 2)], collection, mat=M[glass], recalc=False)
        gl2.location = p - n * (depth * 0.35)
        gl2.rotation_euler = (0, 0, yaw)
        gl2['fx'] = 'window'
        # 尖拱边条
        for side in (-1, 1):
            L = math.hypot(w / 2, w * 0.5)
            ang = math.atan2(w * 0.5, w / 2)
            bar = box(name + '_arch%d' % side, (depth * 0.5, fw, L + fw), Vector((0, 0, 0)), collection, fm)
            bar.matrix_world = Matrix.Translation(p - n * (depth * 0.2) + t * (side * w / 4) + Vector((0, 0, hh / 2 + w * 0.25))) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(side * (math.pi / 2 - ang), 4, 'X')
            objs.append(bar)
    if sill:
        sl = box(name + '_sill', (0.28, w + 0.3, 0.1), p + n * 0.06 + Vector((0, 0, -hh / 2 - 0.05)), collection, M['stone_grey'], rot=(0, 0, yaw))
        objs.append(sl)
    return objs


def door(name, pos, yaw, w, h, collection, M, open_angle=0.0, arch=True, frame_mat=None, leaf_mat=None):
    """门：门框 + 门扇（可开）。pos 为门槛中心（地面）。"""
    fm = frame_mat or M['stone_grey']
    lm = leaf_mat or M['wood_dark']
    c, s = math.cos(yaw), math.sin(yaw)
    n = Vector((c, s, 0))
    t = Vector((-s, c, 0))
    p = Vector(pos)
    objs = []
    # 门框：两侧立柱 + 过梁
    for side in (-1, 1):
        objs.append(box(name + '_jamb%d' % side, (0.32, 0.22, h + 0.1), p + t * (side * (w / 2 + 0.11)) + Vector((0, 0, (h + 0.1) / 2)), collection, fm, rot=(0, 0, yaw)))
    objs.append(box(name + '_lintel', (0.34, w + 0.5, 0.26), p + Vector((0, 0, h + 0.13)), collection, fm, rot=(0, 0, yaw)))
    if arch:
        # 半圆拱楣：用 lathe 的半环
        arc = torus(name + '_archring', w / 2 + 0.2, 0.13, p + Vector((0, 0, h + 0.2)), collection, fm, segs=16, rsegs=6, rot=(math.pi / 2, 0, yaw))
        objs.append(arc)
    # 门扇（绕铰链旋转）
    hinge = p + t * (-w / 2) - n * 0.08
    leaf = box(name + '_leaf', (0.06, w, h), Vector((0, w / 2, h / 2)), collection, lm)
    leaf.matrix_world = Matrix.Translation(hinge) @ Matrix.Rotation(yaw + open_angle, 4, 'Z') @ Matrix.Translation(Vector((0, w / 2, h / 2)))
    objs.append(leaf)
    # 门口踏步
    objs.append(box(name + '_step', (0.6, w + 0.6, 0.16), p + n * 0.3 + Vector((0, 0, -0.02)), collection, M['stone_grey'], rot=(0, 0, yaw), origin='bottom'))
    return objs


# ------------------------------------------------------------------ 屋顶
def gable_roof(name, L, W, pitch_h, loc, collection, mat, yaw=0.0, overhang=0.45, thick=0.16, ridge_mat=None):
    """
    双坡顶：长轴沿 X（局部），loc 为檐口高度处的屋顶中心。
    返回 [屋面, 山墙填充(两端三角)]。
    """
    hw = W / 2 + overhang
    hl = L / 2 + overhang
    verts = [(-hl, -hw, 0), (hl, -hw, 0), (hl, 0, pitch_h), (-hl, 0, pitch_h), (-hl, hw, 0), (hl, hw, 0),
             (-hl, -hw, thick), (hl, -hw, thick), (hl, 0, pitch_h + thick), (-hl, 0, pitch_h + thick), (-hl, hw, thick), (hl, hw, thick)]
    faces = [(0, 1, 2, 3), (3, 2, 5, 4),          # 下面
             (9, 8, 7, 6), (10, 11, 8, 9),        # 上面
             (0, 6, 7, 1), (1, 7, 8, 2), (2, 8, 11, 5), (5, 11, 10, 4),  # 檐口/脊侧
             (4, 10, 6, 0), (3, 9, 6, 0)]
    # 修正端面：用两侧端面（左右山墙侧的厚度面）
    faces = [(0, 1, 2, 3), (3, 2, 5, 4), (9, 8, 7, 6), (10, 11, 8, 9),
             (0, 6, 7, 1), (5, 11, 10, 4),
             (1, 7, 8, 2), (2, 8, 11, 5), (0, 3, 9, 6), (3, 4, 10, 9)]
    ob = mesh_from(name, verts, faces, collection, mat=mat)
    ob.location = loc
    ob.rotation_euler = (0, 0, yaw)
    objs = [ob]
    # 细分以获得顶点色变化
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=3, use_grid_fill=True)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    if ridge_mat is not None:
        r = box(name + '_ridge', (L + overhang * 2 + 0.1, 0.26, 0.18), Vector(loc), collection, ridge_mat, rot=(0, 0, yaw))
        r.location = Vector(loc) + Vector((0, 0, pitch_h + thick + 0.02))
        objs.append(r)
    return objs


def hip_roof(name, L, W, pitch_h, loc, collection, mat, yaw=0.0, overhang=0.4, thick=0.14):
    hw = W / 2 + overhang
    hl = L / 2 + overhang
    rl = max(0.2, (L - W) / 2)
    verts = [(-hl, -hw, 0), (hl, -hw, 0), (hl, hw, 0), (-hl, hw, 0), (-rl, 0, pitch_h), (rl, 0, pitch_h),
             (-hl, -hw, thick), (hl, -hw, thick), (hl, hw, thick), (-hl, hw, thick), (-rl, 0, pitch_h + thick), (rl, 0, pitch_h + thick)]
    faces = [(0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4),
             (10, 11, 7, 6), (11, 8, 7), (11, 10, 9, 8), (10, 6, 9),
             (0, 6, 7, 1), (1, 7, 8, 2), (2, 8, 9, 3), (3, 9, 6, 0)]
    ob = mesh_from(name, verts, faces, collection, mat=mat)
    ob.location = loc
    ob.rotation_euler = (0, 0, yaw)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=2, use_grid_fill=True)
    bm.to_mesh(ob.data)
    bm.free()
    return [ob]


def pyramid_roof(name, r, h, sides, loc, collection, mat, overhang=0.35, phase=None, thick=0.14, finial_mat=None, finial_h=0.9):
    """多边形攒尖顶（塔顶用）。loc 为檐口中心。"""
    if phase is None:
        phase = math.pi / sides
    ob = lathe(name, [(r + overhang, 0.0), (r + overhang + 0.05, thick), (0.0, h + thick)], sides, loc, collection, mat, smooth=False, phase=phase)
    objs = [ob]
    if finial_mat is not None:
        f = lathe(name + '_finial', [(0.0, 0.0), (0.16, 0.05), (0.06, finial_h * 0.55), (0.14, finial_h * 0.7), (0.0, finial_h)], 8,
                  Vector(loc) + Vector((0, 0, h + thick - 0.05)), collection, finial_mat)
        objs.append(f)
    return objs


def chimney(name, loc, collection, M, w=0.9, h=3.2, cap=True, smoke=False, smoke_coll=None, mat=None):
    objs = [box_grid(name, (w, w, h), loc, collection, mat or M['stone_dark'], cell=0.45)]
    if cap:
        objs.append(box(name + '_cap', (w + 0.3, w + 0.3, 0.16), Vector(loc) + Vector((0, 0, h)), collection, M['stone_grey'], origin='bottom'))
        for dx, dy in ((-w * 0.25, -w * 0.25), (w * 0.25, w * 0.25)):
            objs.append(box(name + '_pot', (w * 0.34, w * 0.34, 0.5), Vector(loc) + Vector((dx, dy, h + 0.16)), collection, M['stone_dark'], origin='bottom'))
    if smoke:
        rng = random.Random(hash(name) & 0xffff)
        for i in range(5):
            r = 0.35 + i * 0.22
            s = ico(name + '_smoke%d' % i, r, Vector(loc) + Vector((rng.uniform(-0.3, 0.3) * i, rng.uniform(-0.3, 0.3) * i, h + 0.9 + i * 0.95)),
                    smoke_coll or collection, M['smoke'], subdiv=1)
            s['fx'] = 'smoke'
            s['fx_i'] = i
            objs.append(s)
    return objs


# ------------------------------------------------------------------ 柱子 / 灯 / 旗
def column(name, loc, collection, M, r=0.24, h=3.0, mat=None, base=True, cap=True, segs=12, fluted=False):
    m = mat or M['stone_white']
    objs = []
    prof = [(r * 1.05, 0.0), (r * 1.02, h * 0.15), (r * 0.92, h * 0.85), (r * 0.9, h)]
    objs.append(lathe(name, prof, segs, loc, collection, m, smooth=True))
    if base:
        objs.append(box(name + '_base', (r * 2.6, r * 2.6, 0.22), Vector(loc) - Vector((0, 0, 0.04)), collection, m, origin='bottom'))
    if cap:
        objs.append(lathe(name + '_cap', [(r * 0.9, 0.0), (r * 1.35, 0.22), (r * 1.4, 0.32)], segs, Vector(loc) + Vector((0, 0, h - 0.05)), collection, m, smooth=False))
    return objs


def lantern_post(name, loc, collection, M, h=2.7, glow_coll=None):
    objs = [cylinder(name + '_post', 0.07, h, loc, collection, M['iron'], segments=8, r_top=0.055)]
    head = box(name + '_head', (0.34, 0.34, 0.42), Vector(loc) + Vector((0, 0, h + 0.05)), collection, M['iron'], origin='bottom')
    objs.append(head)
    core = box(name + '_glow', (0.26, 0.26, 0.3), Vector(loc) + Vector((0, 0, h + 0.1)), glow_coll or collection, M['lamp'], origin='bottom')
    core['fx'] = 'lamp'
    objs.append(core)
    objs.append(lathe(name + '_cap', [(0.28, 0.0), (0.05, 0.22), (0.0, 0.3)], 4, Vector(loc) + Vector((0, 0, h + 0.47)), collection, M['iron'], smooth=False, phase=math.pi / 4))
    return objs


def hanging_lamp(name, loc, collection, M, glow_coll=None, r=0.16):
    objs = [lathe(name, [(0.0, 0.0), (r, 0.05), (r * 0.9, r * 1.6), (r * 0.5, r * 2.0), (0.0, r * 2.1)], 8, loc, collection, M['iron'], smooth=False)]
    g = sphere(name + '_glow', r * 0.62, Vector(loc) + Vector((0, 0, r * 0.95)), glow_coll or collection, M['lamp'], segs=8, rings=6)
    g['fx'] = 'lamp'
    objs.append(g)
    return objs


def banner(name, loc, yaw, w, h, collection, mat, pole=True, pole_mat=None, pole_h=None, fx_coll=None):
    """垂幅：顶部挂杆，布面向下略鼓。loc 为挂点。"""
    objs = []
    c, s = math.cos(yaw), math.sin(yaw)
    n = Vector((c, s, 0))
    t = Vector((-s, c, 0))
    rows, cols = 6, 3
    verts, faces = [], []
    rng = random.Random(hash(name) & 0xffff)
    for i in range(rows + 1):
        v = i / rows
        for j in range(cols + 1):
            u = j / cols
            bulge = 0.12 * math.sin(v * math.pi) * (1 + 0.4 * math.sin(u * math.pi * 2))
            pt = Vector(loc) + t * ((u - 0.5) * w) + n * (bulge) + Vector((0, 0, -v * h))
            if i == rows:  # 燕尾
                pt += Vector((0, 0, -0.28 * abs(u - 0.5) * 2))
            verts.append(pt)
    for i in range(rows):
        for j in range(cols):
            a = i * (cols + 1) + j
            faces.append((a, a + 1, a + cols + 2, a + cols + 1))
    cloth = mesh_from(name, verts, faces, fx_coll or collection, mat=mat, smooth=True)
    cloth['fx'] = 'banner'
    objs.append(cloth)
    if pole:
        pm = pole_mat
        objs.append(cylinder(name + '_rod', 0.04, w + 0.3, Vector(loc) - t * (w / 2 + 0.15), collection, pm, segments=6))
        objs[-1].rotation_euler = (0, math.pi / 2, yaw + math.pi / 2)
    return objs


def flag(name, loc, h, w, collection, cloth_mat, pole_mat, fx_coll=None):
    """旗杆 + 三角旗（飘向 +x 局部）。"""
    objs = [cylinder(name + '_pole', 0.06, h, loc, collection, pole_mat, segments=8, r_top=0.04)]
    objs.append(sphere(name + '_knob', 0.11, Vector(loc) + Vector((0, 0, h + 0.05)), collection, pole_mat, segs=8, rings=6))
    verts, faces = [], []
    cols, rows = 6, 2
    for i in range(rows + 1):
        for j in range(cols + 1):
            u, v = j / cols, i / rows
            taper = 1 - 0.85 * u
            verts.append(Vector(loc) + Vector((u * w, 0.06 * math.sin(u * 6.0), h - 0.15 - v * 0.7 * taper - (1 - taper) * 0.35 * 0)))
    for i in range(rows):
        for j in range(cols):
            a = i * (cols + 1) + j
            faces.append((a, a + 1, a + cols + 2, a + cols + 1))
    cl = mesh_from(name + '_cloth', verts, faces, fx_coll or collection, mat=cloth_mat, smooth=True)
    cl['fx'] = 'flag'
    objs.append(cl)
    return objs


# ------------------------------------------------------------------ 楼梯 / 台阶
def steps(name, loc, yaw, w, n, rise=0.18, tread=0.32, collection=None, mat=None):
    """直跑台阶：从 loc（底部前缘中心）向 -局部x（进入建筑方向）上升。"""
    objs = []
    for i in range(n):
        b = box(name + '_%02d' % i, (tread * (n - i) + 0.0, w, rise), Vector((0, 0, 0)), collection, mat, origin='bottom')
        b.matrix_world = Matrix.Translation(loc) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Translation(Vector((-(tread * (n - i)) / 2, 0, i * rise)))
        objs.append(b)
    return objs


def arcade(name, p0, p1, collection, M, n=None, r=0.22, h=3.0, spacing=3.0, mat=None):
    """一排柱子（从 p0 到 p1）。"""
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    if n is None:
        n = max(2, int(L / spacing) + 1)
    objs = []
    for i in range(n):
        t = i / (n - 1)
        objs += column('%s_%02d' % (name, i), p0.lerp(p1, t), collection, M, r=r, h=h, mat=mat)
    return objs


def crenellation(name, loc, r, sides, collection, mat, h=0.6, w=0.5, t=0.3, phase=None, n_per_side=3):
    """塔顶垛口环。"""
    if phase is None:
        phase = math.pi / sides
    objs = []
    verts, faces = [], []
    for i in range(sides):
        a0 = TAU * i / sides + phase
        a1 = TAU * (i + 1) / sides + phase
        p0 = Vector((math.cos(a0) * r, math.sin(a0) * r, 0))
        p1 = Vector((math.cos(a1) * r, math.sin(a1) * r, 0))
        for k in range(n_per_side):
            u0 = (k + 0.15) / n_per_side
            u1 = (k + 0.65) / n_per_side
            a = p0.lerp(p1, u0)
            b = p0.lerp(p1, u1)
            d = (b - a)
            nrm = Vector((-d.y, d.x, 0)).normalized() * t * -1
            base = len(verts)
            for zz in (0, h):
                verts += [a + Vector((0, 0, zz)), b + Vector((0, 0, zz)), b + nrm + Vector((0, 0, zz)), a + nrm + Vector((0, 0, zz))]
            faces += [(base + 4, base + 5, base + 6, base + 7), (base + 3, base + 2, base + 1, base + 0),
                      (base + 0, base + 1, base + 5, base + 4), (base + 1, base + 2, base + 6, base + 5),
                      (base + 2, base + 3, base + 7, base + 6), (base + 3, base + 0, base + 4, base + 7)]
    ob = mesh_from(name, verts, faces, collection, mat=mat)
    ob.location = loc
    return [ob]


def parapet_ring(name, loc, r, sides, collection, mat, h=0.9, t=0.3, phase=None):
    if phase is None:
        phase = math.pi / sides
    outer = lathe(name, [(r, 0), (r, h), (r - t, h), (r - t, 0)], sides, loc, collection, mat, smooth=False, phase=phase, close=False)
    return [outer]
