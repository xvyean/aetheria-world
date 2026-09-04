# -*- coding: utf-8 -*-
"""
星槎学院 · 生活区：星潮厅 / 灶房 / 梯田 / 羊圈 / 马圈 / 宿舍 / 烬园 / 熄灯钟楼 / 植被 / 人物点缀
"""
import bmesh
import math
import random
from mathutils import Vector, Matrix
from util import *
from parts import *
from buildings_core import subdivide
from buildings_houses import build_figure, build_goat
import layout as LY
import island as IS


# ================================================================== 星潮厅 + 灶房
def build_tide_hall(M, C):
    H = LY.TIDE_HALL
    x, y = H['pos']
    L, W, h, yaw = H['L'], H['W'], H['h'], H['yaw']
    gz = IS.ground_h(x, y)
    col = C['hall']
    objs = []
    n = Vector((math.cos(yaw), math.sin(yaw), 0))
    t = Vector((-math.sin(yaw), math.cos(yaw), 0))
    # 墙体：石砌
    body = box_grid('TideHall_Body', (L, W, h), (x, y, gz), col, M['stone_cream'], cell=0.7, rot=(0, 0, yaw))
    stone_vcol(body, PAL['stone_cream'], seed=900, course=0.55, grime=0.32)
    objs.append(body)
    # 扶壁（每侧 5 个）
    for i in range(5):
        u = (i - 2) * (L / 5.2)
        for side in (-1, 1):
            p = Vector((x, y, gz)) + n * u + t * (side * (W / 2 + 0.3))
            bt = lathe('TideHall_Buttress_%d_%d' % (i, side), [(0.45, 0), (0.42, h * 0.6), (0.25, h - 0.6)], 4, p, col, M['stone_grey'], smooth=False, phase=yaw + math.pi / 4)
            set_vcol_const(bt, PAL['stone_grey'], jitter=0.08, seed=901 + i)
            objs.append(bt)
    # 木拱顶：一段圆弧拱形屋面（沿长轴），瓦深灰
    verts, faces = [], []
    segs_a, segs_l = 14, 10
    rise = 2.6
    hw = W / 2 + 0.55
    for i in range(segs_l + 1):
        u = -L / 2 - 0.5 + (L + 1.0) * i / segs_l
        for j in range(segs_a + 1):
            a = math.pi * j / segs_a
            px = math.cos(a) * hw
            pz = math.sin(a) * rise
            p = Vector((x, y, gz + h)) + n * u + t * px + Vector((0, 0, pz))
            verts.append(p)
    for i in range(segs_l):
        for j in range(segs_a):
            a = i * (segs_a + 1) + j
            faces.append((a, a + 1, a + segs_a + 2, a + segs_a + 1))
    roof = mesh_from('TideHall_Roof', verts, faces, col, mat=M['slate'], smooth=True)
    roof_vcol(roof, PAL['slate'], seed=902, streak=0.14, moss_hex=PAL['grass_c'], moss=0.3)
    objs.append(roof)
    # 拱顶内侧木肋（露在两端山墙外的部分 → 用木拱端头）
    for end in (-1, 1):
        u = end * (L / 2 + 0.45)
        pts = []
        for j in range(segs_a + 1):
            a = math.pi * j / segs_a
            pts.append(Vector((x, y, gz + h)) + n * u + t * (math.cos(a) * (hw - 0.1)) + Vector((0, 0, math.sin(a) * (rise - 0.1))))
        rib = tube('TideHall_EndRib_%d' % end, pts, 0.14, col, M['wood_dark'], segs=6)
        objs.append(rib)
        # 山墙填充：半圆板
        gv = [Vector((x, y, gz + h)) + n * (u - end * 0.15) + t * (math.cos(math.pi * j / segs_a) * (hw - 0.15)) + Vector((0, 0, math.sin(math.pi * j / segs_a) * (rise - 0.15))) for j in range(segs_a + 1)]
        gv.append(Vector((x, y, gz + h)) + n * (u - end * 0.15))
        gf = [(j, j + 1, segs_a + 1) for j in range(segs_a)]
        gab = mesh_from('TideHall_Gable_%d' % end, [tuple(v) for v in gv], gf, col, mat=M['wood_mid'])
        wood_vcol(gab, PAL['wood_mid'], seed=903)
        objs.append(gab)
        # 山墙圆窗
        gp = Vector((x, y, gz + h + rise * 0.45)) + n * (u - end * 0.1)
        objs += window('TideHall_Rose_%d' % end, gp, yaw if end > 0 else yaw + math.pi, 1.6, 1.6, col, M, kind='round', frame_mat=M['wood_dark'])
    # 高窗：两侧各 7 扇
    for i in range(7):
        u = (i - 3) * (L / 7.2)
        for side in (-1, 1):
            p = Vector((x, y, gz + h * 0.62)) + n * u + t * (side * W / 2)
            objs += window('TideHall_Win_%d_%d' % (i, side), p, yaw + side * math.pi / 2, 0.9, 2.0, col, M, kind='lancet')
    # 大门：朝广场那一端（-n 方向更靠近原点）
    end_dir = -1 if (Vector((x, y, 0)) - n * L / 2).length < (Vector((x, y, 0)) + n * L / 2).length else 1
    dp = Vector((x, y, gz)) + n * (end_dir * L / 2)
    da = yaw if end_dir > 0 else yaw + math.pi
    objs += door('TideHall_Door', dp, da, 2.4, 3.4, col, M, arch=True, frame_mat=M['stone_white'])
    objs += steps('TideHall_Steps', dp + Vector((math.cos(da), math.sin(da), 0)) * 0.7, da, 4.0, 2, rise=0.22, tread=0.45, collection=col, mat=M['stone_grey'])
    # 门口两盏灯
    for side in (-1, 1):
        objs += lantern_post('TideHall_Lamp_%d' % side, dp + Vector((math.cos(da), math.sin(da), 0)) * 2.0 + t * side * 2.4, col, M, h=2.6, glow_coll=C['fx'])
    # 烟囱（灶房那侧）
    objs += chimney('TideHall_Chimney', Vector((x, y, gz + h - 0.5)) + n * (-end_dir * L * 0.32) + t * (W * 0.28), col, M, w=0.8, h=3.6)
    # ---------------- 灶房：矮屋、一根烟囱冒烟、门口一排水缸
    K = LY.KITCHEN
    kx, ky = K['pos']
    ks = K['size']
    kh = K['h']
    kgz = IS.ground_h(kx, ky)
    kb = box_grid('Kitchen_Body', (ks[0], ks[1], kh), (kx, ky, kgz), col, M['stone_grey'], cell=0.6, rot=(0, 0, yaw))
    stone_vcol(kb, PAL['stone_grey'], seed=910, grime=0.4)
    objs.append(kb)
    rf = gable_roof('Kitchen_Roof', ks[0], ks[1], 1.5, (kx, ky, kgz + kh), col, M['tile_forge'], yaw=yaw, overhang=0.55, ridge_mat=M['stone_dark'])
    roof_vcol(rf[0], '#9a6a4a', seed=911, moss_hex=PAL['grass_c'], moss=0.45)
    objs += rf
    for side in (-1, 1):
        tri = mesh_from('Kitchen_Gable_%d' % side, [(-ks[1] / 2, 0, 0), (ks[1] / 2, 0, 0), (0, 0, 1.5)], [(0, 1, 2)], col, mat=M['stone_grey'])
        tri.matrix_world = Matrix.Translation((kx, ky, kgz + kh)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Translation((side * ks[0] / 2, 0, 0)) @ Matrix.Rotation(math.pi / 2 if side > 0 else -math.pi / 2, 4, 'Z')
        objs.append(tri)
    objs += chimney('Kitchen_Chimney', Vector((kx, ky, kgz + kh - 0.4)) + n * (ks[0] * 0.25), col, M, w=0.9, h=3.0, smoke=True, smoke_coll=C['fx'])
    # 门（朝星潮厅）
    kd_dir = (Vector((x, y, 0)) - Vector((kx, ky, 0)))
    kd_yaw = math.atan2(kd_dir.y, kd_dir.x)
    # 选最接近的墙面法线
    cands = [(yaw, n * (ks[0] / 2)), (yaw + math.pi, -n * (ks[0] / 2)), (yaw + math.pi / 2, t * (ks[1] / 2)), (yaw - math.pi / 2, -t * (ks[1] / 2))]
    best = min(cands, key=lambda c: abs(math.atan2(math.sin(c[0] - kd_yaw), math.cos(c[0] - kd_yaw))))
    objs += door('Kitchen_Door', Vector((kx, ky, kgz)) + best[1], best[0], 1.2, 2.2, col, M, arch=False)
    # 水缸 + 柴堆
    rng = random.Random(912)
    for i in range(4):
        p = Vector((kx, ky, kgz)) + best[1] * 1.0 + Vector((math.cos(best[0] + math.pi / 2), math.sin(best[0] + math.pi / 2), 0)) * (i * 0.75 - 1.1) + Vector((math.cos(best[0]), math.sin(best[0]), 0)) * 1.0
        objs.append(lathe('Kitchen_Jar_%d' % i, [(0.22, 0), (0.32, 0.25), (0.3, 0.55), (0.2, 0.7)], 10, p, col, M['wood_dark'], smooth=True))
    wood_p = Vector((kx, ky, kgz)) - t * (ks[1] / 2 + 0.6) + n * 0.5
    for i in range(12):
        lg = cylinder('Kitchen_Log_%02d' % i, 0.09, 0.8, (0, 0, 0), col, M['wood_light'], segments=6)
        lg.matrix_world = Matrix.Translation(wood_p + Vector((0, 0, 0.1 + (i // 4) * 0.19)) + n * ((i % 4) * 0.2 - 0.3)) @ Matrix.Rotation(yaw + math.pi / 2, 4, 'Z') @ Matrix.Rotation(math.pi / 2, 4, 'X')
        objs.append(lg)
    # 灶房总管佩格（半身人，小个子，围裙色）
    objs += build_figure('Kitchen_Peg', tuple(Vector((kx, ky, kgz)) + best[1] * 1.0 + Vector((math.cos(best[0]), math.sin(best[0]), 0)) * 2.2), 1.05, M, col, cloak='#c9b68a', yaw=best[0] + math.pi)
    # ---------------- 梯田：东南坡三层
    T = LY.TERRACES
    for li, rr in enumerate(T['radii']):
        n_seg = 10
        verts, faces = [], []
        wall_h = 0.55
        for i in range(n_seg + 1):
            a = T['theta0'] + (T['theta1'] - T['theta0']) * i / n_seg
            R = IS.island_radius(a)
            r_in, r_out = rr - 0.9, rr + 0.9
            if r_out > R * 0.95:
                r_out = R * 0.95
            for r_ in (r_in, r_out):
                px, py = math.cos(a) * r_, math.sin(a) * r_
                pz = IS.ground_h(px, py)
                verts.append((px, py, pz + 0.15 + li * 0.05))
        for i in range(n_seg):
            b = i * 2
            faces.append((b, b + 2, b + 3, b + 1))
        bed = mesh_from('Terrace_Bed_%d' % li, verts, faces, col, mat=M['soil'])
        set_vcol_const(bed, PAL['soil'], jitter=0.15, seed=920 + li)
        objs.append(bed)
        # 挡土墙（外沿）
        verts, faces = [], []
        for i in range(n_seg + 1):
            a = T['theta0'] + (T['theta1'] - T['theta0']) * i / n_seg
            r_ = rr + 0.9
            px, py = math.cos(a) * r_, math.sin(a) * r_
            pz = IS.ground_h(px, py)
            verts.append((px, py, pz - 0.2))
            verts.append((px, py, pz + 0.25 + li * 0.05))
            verts.append((math.cos(a) * (r_ + 0.25), math.sin(a) * (r_ + 0.25), pz + 0.25 + li * 0.05))
            verts.append((math.cos(a) * (r_ + 0.25), math.sin(a) * (r_ + 0.25), pz - 0.2))
        for i in range(n_seg):
            b = i * 4
            faces += [(b, b + 1, b + 5, b + 4), (b + 1, b + 2, b + 6, b + 5), (b + 2, b + 3, b + 7, b + 6)]
        wall = mesh_from('Terrace_Wall_%d' % li, verts, faces, col, mat=M['stone_grey'])
        set_vcol_const(wall, PAL['stone_grey'], jitter=0.14, seed=930 + li)
        objs.append(wall)
        # 作物：一排排小绿团
        rng = random.Random(940 + li)
        vv, ff = [], []
        for i in range(24):
            a = T['theta0'] + (T['theta1'] - T['theta0']) * (i + 0.5) / 24
            for row in (-0.45, 0.35):
                r_ = rr + row
                px, py = math.cos(a) * r_, math.sin(a) * r_
                pz = IS.ground_h(px, py) + 0.15 + li * 0.05
                s = rng.uniform(0.16, 0.26)
                b = len(vv)
                # 小四棱锥
                vv += [(px - s, py - s, pz), (px + s, py - s, pz), (px + s, py + s, pz), (px - s, py + s, pz), (px, py, pz + s * 1.8)]
                ff += [(b, b + 1, b + 4), (b + 1, b + 2, b + 4), (b + 2, b + 3, b + 4), (b + 3, b, b + 4)]
        crop = mesh_from('Terrace_Crops_%d' % li, vv, ff, col, mat=M['leaf'])
        la, lb = hex2lin(PAL['leaf_b'])[:3], hex2lin('#4f8a3a')[:3]
        set_vcol(crop, lambda co, nrm: mix(la, lb, 0.5 + 0.5 * math.sin(co.x * 3 + co.y * 2)))
        objs.append(crop)
    # ---------------- 羊圈：矮木栅 + 一头羊（"一百四十八"）
    G = LY.GOAT_PEN
    gx, gy = G['pos']
    gs = G['size']
    gyaw = G['yaw']
    ggz = IS.ground_h(gx, gy)
    gn = Vector((math.cos(gyaw), math.sin(gyaw), 0))
    gt = Vector((-math.sin(gyaw), math.cos(gyaw), 0))
    corners = [Vector((gx, gy, 0)) + gn * (sx * gs[0] / 2) + gt * (sy * gs[1] / 2) for (sx, sy) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        Ln = (b - a).length
        cnt = max(2, int(Ln / 0.9))
        for j in range(cnt + 1):
            p = a.lerp(b, j / cnt)
            pz = IS.ground_h(p.x, p.y)
            objs.append(cylinder('GoatPen_Post_%d_%d' % (i, j), 0.06, 0.9, (p.x, p.y, pz), col, M['wood_dark'], segments=6))
        for zz in (0.35, 0.75):
            pa, pb = Vector((a.x, a.y, IS.ground_h(a.x, a.y) + zz)), Vector((b.x, b.y, IS.ground_h(b.x, b.y) + zz))
            objs.append(tube('GoatPen_Rail_%d_%d' % (i, int(zz * 10)), [pa, pb], 0.04, col, M['wood_mid'], segs=5))
    objs += build_goat('Goat_148', (gx + 0.3, gy - 0.2, ggz), M, col, yaw=gyaw + 0.8)
    objs[-1]['lore'] = '一百四十八'
    # 小棚
    shed = box('GoatPen_Shed', (1.6, 1.2, 1.0), tuple(Vector((gx, gy, ggz)) - gn * (gs[0] / 2 - 0.9) - gt * (gs[1] / 2 - 0.7)), col, M['wood_dark'], rot=(0, 0, gyaw), origin='bottom')
    objs.append(shed)
    objs += gable_roof('GoatPen_ShedRoof', 1.6, 1.2, 0.5, shed.location + Vector((0, 0, 1.0)), col, M['wood_mid'], yaw=gyaw, overhang=0.2, thick=0.08)
    # ---------------- 马圈：六匹很胖的马
    P = LY.PADDOCK
    px_, py_ = math.cos(P['theta']) * P['r'], math.sin(P['theta']) * P['r']
    pyaw = P['theta'] + math.pi / 2
    pn = Vector((math.cos(pyaw), math.sin(pyaw), 0))
    pt = Vector((-math.sin(pyaw), math.cos(pyaw), 0))
    ps = P['size']
    corners = [Vector((px_, py_, 0)) + pn * (sx * ps[0] / 2) + pt * (sy * ps[1] / 2) for (sx, sy) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        Ln = (b - a).length
        cnt = max(2, int(Ln / 1.1))
        for j in range(cnt + 1):
            p = a.lerp(b, j / cnt)
            pz = IS.ground_h(p.x, p.y)
            objs.append(cylinder('Paddock_Post_%d_%d' % (i, j), 0.07, 1.2, (p.x, p.y, pz), col, M['wood_dark'], segments=6))
        for zz in (0.5, 1.0):
            pa, pb = Vector((a.x, a.y, IS.ground_h(a.x, a.y) + zz)), Vector((b.x, b.y, IS.ground_h(b.x, b.y) + zz))
            objs.append(tube('Paddock_Rail_%d_%d' % (i, int(zz * 10)), [pa, pb], 0.045, col, M['wood_mid'], segs=5))
    rng = random.Random(950)
    hm = principled('Horse', '#5a3d2b', rough=0.85)
    hm2 = principled('Horse_Dun', '#8a6a48', rough=0.85)
    for i in range(6):
        hp = Vector((px_, py_, 0)) + pn * rng.uniform(-ps[0] / 2 + 1.0, ps[0] / 2 - 1.0) + pt * rng.uniform(-ps[1] / 2 + 0.8, ps[1] / 2 - 0.8)
        hz = IS.ground_h(hp.x, hp.y)
        hyaw = rng.uniform(0, TAU)
        m = hm if i % 2 else hm2
        parts_ = []
        parts_.append(sphere('Horse_%d_Body' % i, 0.62, (0, 0, 1.15), col, m, segs=10, rings=8, scale=(1.5, 1.15, 1.0)))  # 很胖
        parts_.append(sphere('Horse_%d_Head' % i, 0.26, (1.05, 0, 1.7), col, m, segs=8, rings=6, scale=(1.6, 0.8, 0.9)))
        parts_.append(tube('Horse_%d_Neck' % i, [Vector((0.7, 0, 1.35)), Vector((0.95, 0, 1.7))], 0.24, col, m, segs=6))
        for j, (dx, dy) in enumerate(((-0.55, -0.35), (-0.55, 0.35), (0.55, -0.35), (0.55, 0.35))):
            parts_.append(cylinder('Horse_%d_Leg_%d' % (i, j), 0.1, 0.95, (dx, dy, 0.0), col, m, segments=6))
        parts_.append(tube('Horse_%d_Tail' % i, [Vector((-0.9, 0, 1.3)), Vector((-1.15, 0, 0.9)), Vector((-1.2, 0.05, 0.5))], 0.07, col, M['wood_dark'], segs=5))
        for o in parts_:
            o.matrix_world = Matrix.Translation((hp.x, hp.y, hz)) @ Matrix.Rotation(hyaw, 4, 'Z') @ o.matrix_world
        objs += parts_
    # 马槽
    tr = box('Paddock_Trough', (2.0, 0.6, 0.5), tuple(Vector((px_, py_, IS.ground_h(px_, py_))) + pt * (ps[1] / 2 - 0.6)), col, M['wood_dark'], rot=(0, 0, pyaw), origin='bottom')
    objs.append(tr)
    return objs


# ================================================================== 宿舍
def build_dorms(M, C):
    col = C['dorms']
    objs = []
    rng = random.Random(1000)
    all_dorms = [(a, s, 'NE') for (a, s) in LY.DORMS_NE] + [(a, s, 'SW') for (a, s) in LY.DORMS_SW]
    sx, sy = LY.DORM_SIZE
    for i, (adeg, side, grp) in enumerate(all_dorms):
        a = math.radians(adeg)
        rr = IS.road_r(a) + (LY.DORM_OUT_OFF + sy / 2 if side > 0 else -(LY.DORM_IN_OFF + sy / 2))
        x, y = math.cos(a) * rr, math.sin(a) * rr
        gz = IS.ground_h(x, y)
        yaw = a + math.pi / 2  # 长边沿环道切向
        h = 2.9 + 2.6  # 两层
        # 找平：用一个小台基
        pad = box('Dorm_%02d_Pad' % i, (sx + 0.8, sy + 0.8, 0.35), (x, y, gz - 0.25), col, M['stone_grey'], rot=(0, 0, yaw), origin='bottom')
        set_vcol_const(pad, PAL['stone_grey'], jitter=0.1, seed=i)
        objs.append(pad)
        # 一层石、二层木骨（半木结构）
        z0 = gz + 0.1
        lower = box_grid('Dorm_%02d_Lower' % i, (sx, sy, 2.9), (x, y, z0), col, M['stone_cream'], cell=0.6, rot=(0, 0, yaw))
        stone_vcol(lower, PAL['stone_cream'], seed=1010 + i, grime=0.35, tint=rng.choice(['#e7dfcc', '#d8d3c6', '#e3d9c0']))
        objs.append(lower)
        upper = box_grid('Dorm_%02d_Upper' % i, (sx + 0.3, sy + 0.3, 2.6), (x, y, z0 + 2.9), col, M['plaster'], cell=0.6, rot=(0, 0, yaw))
        set_vcol_const(upper, rng.choice(['#e6dcc4', '#dfd3b8', '#e8e0cc', '#d9cdb0']), jitter=0.05, seed=i)
        objs.append(upper)
        # 木骨架：转角柱 + 横梁 + 斜撑
        n = Vector((math.cos(yaw), math.sin(yaw), 0))
        t = Vector((-math.sin(yaw), math.cos(yaw), 0))
        for (u, v) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            p = Vector((x, y, z0 + 2.9)) + n * (u * (sx + 0.3) / 2) + t * (v * (sy + 0.3) / 2)
            objs.append(box('Dorm_%02d_Post_%d%d' % (i, u > 0, v > 0), (0.16, 0.16, 2.6), p, col, M['wood_dark'], rot=(0, 0, yaw), origin='bottom'))
        for v in (-1, 1):
            for zz in (0.0, 2.5):
                p = Vector((x, y, z0 + 2.9 + zz)) + t * (v * (sy + 0.3) / 2)
                objs.append(box('Dorm_%02d_Beam_%d_%d' % (i, v > 0, int(zz)), (sx + 0.3, 0.14, 0.14), p + Vector((0, 0, 0.07)), col, M['wood_dark'], rot=(0, 0, yaw)))
            # 斜撑
            for u in (-1, 1):
                br = box('Dorm_%02d_Brace_%d_%d' % (i, u > 0, v > 0), (1.3, 0.1, 0.1), (0, 0, 0), col, M['wood_dark'])
                br.matrix_world = Matrix.Translation(Vector((x, y, z0 + 2.9 + 0.6)) + n * (u * (sx / 2 - 0.6)) + t * (v * (sy + 0.3) / 2 + v * 0.02)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(u * 0.75, 4, 'Y')
                objs.append(br)
        # 屋顶：双坡，瓦色随年份组（NE 暖灰 / SW 蓝灰），带烟囱
        roof_mat = M['roof_terra'] if grp == 'NE' else M['roof_blue']
        roof_hex = rng.choice(['#a8603f', '#9c5a3c', '#b06a45']) if grp == 'NE' else rng.choice(['#4f5f74', '#55667c', '#46566a'])
        rf = gable_roof('Dorm_%02d_Roof' % i, sx + 0.3, sy + 0.3, 1.9, (x, y, z0 + 5.5), col, roof_mat, yaw=yaw, overhang=0.5, ridge_mat=M['stone_dark'])
        roof_vcol(rf[0], roof_hex, seed=1020 + i, moss_hex=PAL['grass_c'], moss=0.4)
        objs += rf
        for u in (-1, 1):
            tri = mesh_from('Dorm_%02d_Gable_%d' % (i, u > 0), [(-(sy + 0.3) / 2, 0, 0), ((sy + 0.3) / 2, 0, 0), (0, 0, 1.9)], [(0, 1, 2)], col, mat=M['plaster'], recalc=False)
            set_vcol_const(tri, '#e6dcc4')
            tri.matrix_world = Matrix.Translation((x, y, z0 + 5.5)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Translation((u * (sx + 0.3) / 2, 0, 0)) @ Matrix.Rotation(math.pi / 2 if u > 0 else -math.pi / 2, 4, 'Z')
            objs.append(tri)
        objs += chimney('Dorm_%02d_Chimney' % i, Vector((x, y, z0 + 5.0)) + n * (sx * 0.28) + t * (sy * 0.15), col, M, w=0.55, h=2.6, smoke=(i % 4 == 0), smoke_coll=C['fx'])
        # 门朝环道
        door_side = -side  # 朝环道
        dp = Vector((x, y, z0)) + t * (door_side * sy / 2)
        dyaw = yaw + (math.pi / 2 if door_side > 0 else -math.pi / 2)
        objs += door('Dorm_%02d_Door' % i, dp, dyaw, 1.0, 2.1, col, M, arch=False, frame_mat=M['wood_dark'])
        # 窗：一层两扇、二层三扇，朝环道；背面二层两扇
        for k in range(2):
            p = dp + n * ((k - 0.5) * (sx * 0.55)) + Vector((0, 0, 1.6))
            objs += window('Dorm_%02d_W1_%d' % (i, k), p, dyaw, 0.7, 0.9, col, M, kind='square', frame_mat=M['wood_dark'])
        for k in range(3):
            p = Vector((x, y, z0 + 2.9 + 1.4)) + t * (door_side * (sy + 0.3) / 2) + n * ((k - 1) * (sx * 0.32))
            objs += window('Dorm_%02d_W2_%d' % (i, k), p, dyaw, 0.65, 0.9, col, M, kind='square', frame_mat=M['wood_dark'], sill=False)
        for k in range(2):
            p = Vector((x, y, z0 + 2.9 + 1.4)) - t * (door_side * (sy + 0.3) / 2) + n * ((k - 0.5) * (sx * 0.5))
            objs += window('Dorm_%02d_W3_%d' % (i, k), p, dyaw + math.pi, 0.65, 0.9, col, M, kind='square', frame_mat=M['wood_dark'], sill=False)
        # 门口一盏挂灯、一条晾衣绳（偶尔）
        objs += hanging_lamp('Dorm_%02d_Lamp' % i, dp + Vector((math.cos(dyaw), math.sin(dyaw), 0)) * 0.35 + n * 0.9 + Vector((0, 0, 2.5)), col, M, glow_coll=C['fx'], r=0.13)
        if i % 3 == 1:
            hk = ['dawn', 'speak', 'forge', 'tide'][i % 4]
            objs += banner('Dorm_%02d_Cloth' % i, dp + Vector((math.cos(dyaw), math.sin(dyaw), 0)) * 0.6 + n * (-1.2) + Vector((0, 0, 2.3)), dyaw, 0.6, 0.9, col, M['cloth_' + hk], pole=True, pole_mat=M['wood_dark'], fx_coll=C['fx'])
    return objs


# ================================================================== 烬园 + 熄灯钟楼
def build_ember_garden(M, C):
    E = LY.EMBER_GARDEN
    x, y = E['pos']
    r = E['r']
    gz = IS.ground_h(x, y)
    col = C['garden']
    objs = []
    # 矮墙：圆环，留一个口朝广场
    gap_a = math.atan2(-y, -x)
    n = 36
    verts, faces = [], []
    for i in range(n + 1):
        a = gap_a + 0.35 + (TAU - 0.7) * i / n
        for rr in (r, r + 0.4):
            px, py = x + math.cos(a) * rr, y + math.sin(a) * rr
            pz = IS.ground_h(px, py)
            verts.append((px, py, pz - 0.1))
            verts.append((px, py, pz + 0.9))
    for i in range(n):
        b = i * 4
        faces += [(b, b + 4, b + 5, b + 1), (b + 2, b + 3, b + 7, b + 6), (b + 1, b + 5, b + 7, b + 3)]
    wall = mesh_from('EmberGarden_Wall', verts, faces, col, mat=M['stone_grey'])
    set_vcol_const(wall, PAL['stone_grey'], jitter=0.14, seed=1100)
    objs.append(wall)
    # 墙帽
    cap_pts = []
    for i in range(n + 1):
        a = gap_a + 0.35 + (TAU - 0.7) * i / n
        px, py = x + math.cos(a) * (r + 0.2), y + math.sin(a) * (r + 0.2)
        cap_pts.append(Vector((px, py, IS.ground_h(px, py) + 0.95)))
    objs.append(tube('EmberGarden_WallCap', cap_pts, 0.26, col, M['stone_grey'], segs=6))
    # 地面：灰白细砂圆
    ground = lathe('EmberGarden_Ground', [(0.0, 0.06), (r - 0.1, 0.05)], 28, (x, y, gz), col, M['ash'], smooth=True)
    objs.append(ground)
    # 不开花的树：4 棵深色瘦树
    rng = random.Random(1101)
    for k in range(4):
        a = TAU * k / 4 + 0.6
        rr = r * 0.6
        tx, ty = x + math.cos(a) * rr, y + math.sin(a) * rr
        tz = IS.ground_h(tx, ty)
        th = rng.uniform(5.0, 7.0)
        trunk = lathe('EmberTree_%d_Trunk' % k, [(0.22, 0), (0.16, th * 0.6), (0.08, th)], 8, (tx, ty, tz), col, M['bark'], smooth=True)
        set_vcol_const(trunk, '#3a2f28', jitter=0.1, seed=k)
        objs.append(trunk)
        for j in range(5):
            a2 = rng.uniform(0, TAU)
            z0 = th * rng.uniform(0.45, 0.9)
            L = rng.uniform(1.2, 2.4)
            p0 = Vector((tx, ty, tz + z0))
            p1 = p0 + Vector((math.cos(a2) * L, math.sin(a2) * L, L * rng.uniform(0.4, 0.9)))
            objs.append(tube('EmberTree_%d_Br_%d' % (k, j), [p0, p1], 0.06, col, M['bark'], segs=5))
        # 稀疏暗叶
        crown = ico('EmberTree_%d_Crown' % k, 1.5, (tx, ty, tz + th * 0.95), col, M['cypress'], subdiv=1)
        crown.scale = (1.0, 1.0, 1.4)
        me = crown.data
        for v in me.vertices:
            v.co *= 1 + 0.3 * fbm(v.co.x, v.co.y, v.co.z, oct=2, seed=k)
        me.update()
        set_vcol_const(crown, '#2d3d2c', jitter=0.15, seed=10 + k)
        objs.append(crown)
    # 石凳（烬人坐的地方）+ 坐着的烬人（灰斗篷）
    for k in range(6):
        a = TAU * k / 6 + 0.2
        if abs(math.atan2(math.sin(a - gap_a), math.cos(a - gap_a))) < 0.5:
            continue
        rr = r * 0.78
        bx, by = x + math.cos(a) * rr, y + math.sin(a) * rr
        bz = IS.ground_h(bx, by)
        bench = box('EmberGarden_Bench_%d' % k, (1.5, 0.45, 0.42), (bx, by, bz), col, M['stone_grey'], rot=(0, 0, a + math.pi / 2), origin='bottom')
        objs.append(bench)
        if k % 2 == 0:
            f = build_figure('EmberGarden_Ashen_%d' % k, (bx + math.cos(a + math.pi) * 0.25, by + math.sin(a + math.pi) * 0.25, bz + 0.42), 1.15, M, col, cloak='#8e8a86', yaw=a + math.pi, skin='#b9b2a8')
            objs += f
    # ---------------- 熄灯钟楼：细高石塔 + 钟 + 鼓皮
    B = LY.BELL_TOWER
    bx, by = B['pos']
    bw, bh = B['w'], B['h']
    bgz = IS.ground_h(bx, by)
    body = prism('BellTower_Body', bw / 2 * math.sqrt(2), bh, 4, (bx, by, bgz), col, M['stone_grey'], taper=0.82, phase=math.pi / 4)
    subdivide(body, 6)
    stone_vcol(body, PAL['stone_grey'], seed=1120, course=0.5, grime=0.3, tint='#8f8c86')
    objs.append(body)
    # 钟室：四根柱 + 攒尖顶
    top = bgz + bh
    plat = box('BellTower_Plate', (bw * 1.1, bw * 1.1, 0.25), (bx, by, top), col, M['stone_cream'], origin='bottom')
    objs.append(plat)
    for (u, v) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        objs += column('BellTower_Col_%d%d' % (u > 0, v > 0), (bx + u * bw * 0.42, by + v * bw * 0.42, top + 0.25), col, M, r=0.11, h=2.2, mat=M['stone_cream'], base=False)
    objs += pyramid_roof('BellTower_Roof', bw * 0.62, 1.9, 4, (bx, by, top + 2.5), col, M['slate'], overhang=0.4, phase=math.pi / 4, thick=0.1, finial_mat=M['iron'], finial_h=0.7)
    roof_vcol(objs[-2], PAL['slate'], seed=1121)
    # 钟
    bell = lathe('BellTower_Bell', [(0.0, 0), (0.42, 0.0), (0.4, 0.15), (0.3, 0.6), (0.24, 1.0), (0.1, 1.15), (0.0, 1.2)], 14, (bx, by, top + 0.25 + 0.6), col, M['bell'], smooth=True)
    bell['fx'] = 'bell'
    objs.append(bell)
    objs.append(sphere('BellTower_Clapper', 0.08, (bx, by, top + 0.25 + 0.65), col, M['iron'], segs=8, rings=6))
    objs.append(cylinder('BellTower_Yoke', 0.05, bw * 0.84, (bx - bw * 0.42, by, top + 0.25 + 1.85), col, M['wood_dark'], segments=6))
    objs[-1].rotation_euler = (0, math.pi / 2, 0)
    # 血誓部族的鼓皮：挂在钟室一侧的一块圆皮
    drum = lathe('BellTower_Drumskin', [(0.0, 0), (0.55, 0), (0.55, 0.04), (0.0, 0.04)], 16, (0, 0, 0), col, M['wood_light'], smooth=False)
    drum.matrix_world = Matrix.Translation((bx + bw * 0.5, by, top + 0.25 + 1.2)) @ Matrix.Rotation(math.pi / 2, 4, 'Y')
    set_vcol_const(drum, '#c9a880')
    drum['lore'] = '血誓部族的鼓皮'
    objs.append(drum)
    # 小门
    objs += door('BellTower_Door', (bx + bw / 2, by, bgz), 0.0, 0.9, 1.9, col, M, arch=True, frame_mat=M['stone_cream'])
    # 门楣刻字位（一块铜牌）
    objs.append(box('BellTower_Inscription', (0.04, 1.1, 0.28), (bx + bw / 2 + 0.03, by, bgz + 2.35), col, M['copper']))
    objs[-1]['lore'] = '学府教人点灯，先得教人记得关灯。'
    return objs


# ================================================================== 植被
def build_vegetation(M, C):
    """
    岛上树木：环道内外散布。避开建筑（用 layout 中的占位半径）。
    树型：柏（瘦锥）、阔叶（叶团）。
    """
    col = C['veg']
    objs = []
    rng = random.Random(2000)
    blockers = [
        (0, 0, LY.PLAZA_R + 3.5),
        (LY.DAWN_TOWER['pos'][0], LY.DAWN_TOWER['pos'][1], 6.5),
        (LY.SPEAK_TOWER['pos'][0], LY.SPEAK_TOWER['pos'][1], 6.0),
        (LY.SYCAMORE['pos'][0], LY.SYCAMORE['pos'][1], 7.0),
        (LY.FORGE_TOWER['pos'][0], LY.FORGE_TOWER['pos'][1], 8.0),
        (LY.OLD_STEPS['pos'][0], LY.OLD_STEPS['pos'][1], 4.0),
        (LY.TIDE_TOWER['pos'][0], LY.TIDE_TOWER['pos'][1], 8.5),
        (LY.POOL['pos'][0], LY.POOL['pos'][1], 7.5),
        (LY.CLOUD_NET['pos'][0], LY.CLOUD_NET['pos'][1], 4.5),
        (LY.GRAIN_HALL['pos'][0], LY.GRAIN_HALL['pos'][1], 8.5),
        (LY.HISTORY_HALL['pos'][0], LY.HISTORY_HALL['pos'][1], 5.0),
        (LY.TIDE_HALL['pos'][0], LY.TIDE_HALL['pos'][1], 12.0),
        (LY.KITCHEN['pos'][0], LY.KITCHEN['pos'][1], 5.0),
        (LY.GOAT_PEN['pos'][0], LY.GOAT_PEN['pos'][1], 4.0),
        (LY.EMBER_GARDEN['pos'][0], LY.EMBER_GARDEN['pos'][1], 7.0),
        (LY.BELL_TOWER['pos'][0], LY.BELL_TOWER['pos'][1], 3.0),
        (math.cos(LY.PADDOCK['theta']) * LY.PADDOCK['r'], math.sin(LY.PADDOCK['theta']) * LY.PADDOCK['r'], 5.0),
    ]
    for (adeg, side) in LY.DORMS_NE + LY.DORMS_SW:
        a = math.radians(adeg)
        rr = IS.road_r(a) + (LY.DORM_OUT_OFF + LY.DORM_SIZE[1] / 2 if side > 0 else -(LY.DORM_IN_OFF + LY.DORM_SIZE[1] / 2))
        blockers.append((math.cos(a) * rr, math.sin(a) * rr, 4.4))
    # 回廊
    for hk, cd in LY.CORRIDORS.items():
        dx, dy = cd['dir']
        for s in range(int(cd['start']), int(cd['end']) + 3, 3):
            blockers.append((dx * s, dy * s, 3.2))
    # 梯田
    for rr in LY.TERRACES['radii']:
        for i in range(6):
            a = LY.TERRACES['theta0'] + (LY.TERRACES['theta1'] - LY.TERRACES['theta0']) * i / 5
            blockers.append((math.cos(a) * rr, math.sin(a) * rr, 2.0))

    def free(px, py, rad):
        th = math.atan2(py, px)
        R = IS.island_radius(th)
        d = math.hypot(px, py)
        if d > R * 0.93:
            return False
        rr = IS.road_r(th)
        if abs(d - rr) < 2.0 + rad:
            return False
        for (bx, by, br) in blockers:
            if math.hypot(px - bx, py - by) < br + rad:
                return False
        return True
    placed = []
    tries = 0
    while len(placed) < 95 and tries < 6000:
        tries += 1
        a = rng.uniform(0, TAU)
        R = IS.island_radius(a)
        d = R * math.sqrt(rng.uniform(0.15, 0.9))
        px, py = math.cos(a) * d, math.sin(a) * d
        if not free(px, py, 1.6):
            continue
        if any(math.hypot(px - qx, py - qy) < 2.6 for (qx, qy, _) in placed):
            continue
        kind = 'cypress' if rng.random() < 0.45 else 'broad'
        placed.append((px, py, kind))
    for i, (px, py, kind) in enumerate(placed):
        pz = IS.ground_h(px, py)
        s = rng.uniform(0.8, 1.3)
        if kind == 'cypress':
            objs += tree_cypress('Tree_Cyp_%02d' % i, (px, py, pz), s, M, col, rng)
        else:
            objs += tree_broad('Tree_Broad_%02d' % i, (px, py, pz), s, M, col, rng)
    # 灌木：环道边、建筑脚下
    n_bush = 0
    tries = 0
    while n_bush < 70 and tries < 4000:
        tries += 1
        a = rng.uniform(0, TAU)
        R = IS.island_radius(a)
        d = R * math.sqrt(rng.uniform(0.2, 0.9))
        px, py = math.cos(a) * d, math.sin(a) * d
        if not free(px, py, 0.4):
            continue
        pz = IS.ground_h(px, py)
        b = ico('Bush_%02d' % n_bush, rng.uniform(0.45, 0.9), (px, py, pz + 0.2), col, M['leaf'], subdiv=1)
        b.scale = (1.0, rng.uniform(0.8, 1.2), rng.uniform(0.55, 0.8))
        set_vcol_const(b, rng.choice([PAL['leaf_a'], PAL['leaf_b'], '#5a7f36']), jitter=0.12, seed=n_bush)
        objs.append(b)
        n_bush += 1
    return objs


def tree_cypress(name, loc, s, M, col, rng):
    x, y, z = loc
    h = 6.5 * s
    objs = [cylinder(name + '_Trunk', 0.16 * s, 1.2 * s, (x, y, z - 0.1), col, M['bark'], segments=7, r_top=0.12 * s)]
    set_vcol_const(objs[0], PAL['bark'], jitter=0.12, seed=hash(name) & 0xff)
    prof = [(0.0, 0.0), (0.9 * s, 0.4 * s), (1.0 * s, 1.6 * s), (0.75 * s, 3.4 * s), (0.42 * s, 5.0 * s), (0.15 * s, 6.0 * s), (0.0, h)]
    crown = lathe(name + '_Crown', prof, 9, (x, y, z + 0.9 * s), col, M['cypress'], smooth=True)
    me = crown.data
    for v in me.vertices:
        d = fbm(v.co.x / s, v.co.y / s, v.co.z / s, oct=2, seed=hash(name) % 100)
        v.co.x *= 1 + 0.18 * d
        v.co.y *= 1 + 0.18 * d
    me.update()
    ca, cb = hex2lin(PAL['cypress'])[:3], hex2lin('#3d6b3a')[:3]
    set_vcol(crown, lambda co, n: mix(ca, cb, smoothstep(-0.2, 0.8, n.z) * 0.7 + 0.15 * fbm(co.x, co.y, co.z, oct=2, seed=3)))
    crown['fx'] = 'foliage'
    objs.append(crown)
    return objs


def tree_broad(name, loc, s, M, col, rng):
    x, y, z = loc
    th = 2.4 * s
    trunk = lathe(name + '_Trunk', [(0.3 * s, 0), (0.22 * s, th * 0.6), (0.16 * s, th)], 8, (x, y, z - 0.1), col, M['bark'], smooth=True)
    set_vcol_const(trunk, PAL['bark'], jitter=0.12, seed=hash(name) & 0xff)
    objs = [trunk]
    for k in range(3):
        a = TAU * k / 3 + rng.uniform(-0.4, 0.4)
        p0 = Vector((x, y, z + th * 0.8))
        p1 = p0 + Vector((math.cos(a) * 1.2 * s, math.sin(a) * 1.2 * s, 1.0 * s))
        objs.append(tube(name + '_Br_%d' % k, [p0, p1], 0.09 * s, col, M['bark'], segs=5))
    la, lb, lc = hex2lin(PAL['leaf_a'])[:3], hex2lin(PAL['leaf_b'])[:3], hex2lin(PAL['grass_c'])[:3]
    for k in range(4):
        a = TAU * k / 4 + rng.uniform(-0.5, 0.5)
        rr = rng.uniform(0.3, 0.9) * s
        c = Vector((x + math.cos(a) * rr, y + math.sin(a) * rr, z + th + 1.3 * s + rng.uniform(-0.3, 0.5) * s))
        r_ = rng.uniform(1.2, 1.8) * s
        b = ico(name + '_Leaf_%d' % k, r_, c, col, M['leaf'], subdiv=2)
        b.scale = (1.0, rng.uniform(0.85, 1.1), rng.uniform(0.7, 0.9))
        me = b.data
        for v in me.vertices:
            v.co *= 1 + 0.2 * fbm(v.co.x / r_, v.co.y / r_, v.co.z / r_, oct=2, seed=k + (hash(name) % 50))
        me.update()
        set_vcol(b, lambda co, n: mix(mix(lc, la, smoothstep(-0.4, 0.9, n.z)), lb, 0.4 * smoothstep(0.2, 1.0, n.z) * (0.5 + 0.5 * fbm(co.x, co.y, co.z, oct=2, seed=5))))
        b['fx'] = 'foliage'
        objs.append(b)
    return objs


# ================================================================== 人物点缀
def build_people(M, C):
    col = C['people']
    objs = []
    rng = random.Random(3000)
    cloaks = {'dawn': PAL['cloth_dawn'], 'speak': PAL['cloth_speak'], 'forge': PAL['cloth_forge'], 'tide': PAL['cloth_tide']}
    spots = [
        # 广场上
        ((4.0, -9.5), 'dawn'), ((5.2, -8.6), 'speak'), ((-9.0, 3.0), 'tide'), ((9.5, 3.5), 'forge'), ((-3.0, 10.5), 'speak'),
        # 回廊里
        ((20.0, 1.2), 'dawn'), ((-1.0, 16.0), 'speak'), ((1.2, -15.0), 'forge'), ((-16.5, -0.9), 'tide'),
        # 旧阶堆上吃饭的
        ((7.6, -23.9), 'forge'), ((6.2, -22.8), 'dawn'),
        # 星潮厅门口
        ((10.0, -8.6), 'tide'), ((11.0, -7.4), 'speak'),
        # 环道上走的
        ((28.0, 18.0), 'dawn'), ((-20.0, -26.0), 'forge'), ((-30.0, 14.0), 'tide'), ((22.0, 25.0), 'speak'),
    ]
    for i, ((px, py), hk) in enumerate(spots):
        pz = IS.ground_h(px, py)
        if math.hypot(px, py) <= LY.PLAZA_R:
            pz += 0.06
        h = rng.uniform(1.55, 1.8)
        if hk == 'forge' and i % 3 == 0:
            h = 1.35  # 矮人
        objs += build_figure('Student_%02d' % i, (px, py, pz), h, M, col, cloak=cloaks[hk], yaw=rng.uniform(0, TAU))
    # 乌尔莎·黑牙：高大，在锤音塔炉口边
    fx, fy = LY.FORGE_TOWER['pos']
    objs += build_figure('Ursa_Blackfang', (fx + 2.6, fy + 5.6, IS.ground_h(fx + 2.6, fy + 5.6)), 2.1, M, col, cloak=PAL['cloth_dawn'], yaw=math.radians(-120), skin='#6f7d5a')
    # 布兰·哑锤：矮，炉口另一边
    objs += build_figure('Bran_MuteHammer', (fx - 2.4, fy + 5.4, IS.ground_h(fx - 2.4, fy + 5.4)), 1.3, M, col, cloak=PAL['cloth_forge'], yaw=math.radians(-60))
    # 守岛的圣骑士（没带剑，带了面镜子）：浮池边
    px, py = LY.POOL['pos'][0] + 6.5, LY.POOL['pos'][1] + 2.0
    objs += build_figure('Paladin', (px, py, IS.ground_h(px, py)), 1.85, M, col, cloak='#e0d6b8', yaw=math.atan2(LY.POOL['pos'][1] - py, LY.POOL['pos'][0] - px))
    mirror = box('Paladin_Mirror', (0.05, 0.4, 0.55), (px + 0.35, py, IS.ground_h(px, py) + 1.0), col, M['crystal'])
    objs.append(mirror)
    # 校长凯兰·星羽：星穗馆门口
    gx, gy = LY.GRAIN_HALL['pos']
    da = math.atan2(-gy, -gx)
    px, py = gx + math.cos(da) * (LY.GRAIN_HALL['r'] + 3.0), gy + math.sin(da) * (LY.GRAIN_HALL['r'] + 3.0)
    objs += build_figure('Headmaster_Kaelan', (px, py, IS.ground_h(px, py)), 1.78, M, col, cloak='#2e2a3a', yaw=da + math.pi)
    return objs
