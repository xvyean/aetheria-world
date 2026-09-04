# -*- coding: utf-8 -*-
"""星槎空岛 · 总装 master（原生坐标系：X 东 / Y 南 / Z 上；岛顶面 z=0）。
严格按 bible/03-空岛建筑志 施工。方位角 a：pos_xy = (r*cos a, r*sin a)；东 0 / 南 90 / 西 180 / 北 -90。
"""
import bpy, math, random
from math import radians as D
from mathutils import Euler
from lib import geo
from lib.mats import M

RIM = 29.2
random.seed(412)

def dirp(a, r):
    return (math.cos(D(a)) * r, math.sin(D(a)) * r)

def place(ob, P, rotz=0.0):
    if len(P) == 2:
        P = (P[0], P[1], 0.0)
    ob.location = P
    r = ob.rotation_euler
    ob.rotation_euler = Euler((r.x, r.y, r.z + D(rotz)), 'XYZ')
    return ob

def pr(rotz=0.0):
    return (0, 0, rotz)

# ================================================================ 岛体
def build_island(coll):
    objs = []
    # —— 顶面（草地台地） ——
    prof = [(0.6, 0.05), (7, 0.02), (14, -0.05), (21, -0.14), (26.5, -0.3),
            (28.6, -0.5), (29.4, -0.9)]
    top = geo.lathe('ISC_top', prof, 96, M('grass'), (0, 0, 0), coll,
                    noise=0.022, seed=7, close_top=True)
    geo.vcol(top, 0.09, seed=11)
    objs.append(top)
    # —— 岩体（裙摆到船底） ——
    prof2 = [(29.4, -0.9), (29.1, -1.7), (28.4, -3.2), (26.6, -5.8), (24.2, -8.8),
             (21.0, -12.2), (17.2, -15.8), (13.6, -19.4), (11.2, -22.8),
             (10.0, -25.2), (9.8, -26.2)]
    rock = geo.lathe('ISC_rock', prof2, 96, M('basalt'), (0, 0, 0), coll,
                     noise=0.045, seed=21, close_bottom=True)
    geo.vcol(rock, 0.10, seed=22)
    objs.append(rock)
    # —— 船底晶簇（裂隙之光的地基）：中央大簇 + 环圈小簇 ——
    objs.append(geo.crystal_cluster('ISC_under_crystal', (0, 0, -25.6), M('crystal'), coll, seed=3, n=6, h=5.6, r=0.8))
    for i in range(6):
        a = 60 * i + random.uniform(-14, 14)
        p = (math.cos(D(a)) * 7.2, math.sin(D(a)) * 7.2, -24.0 + random.uniform(-1.2, 0.6))
        objs.append(place(geo.crystal_cluster(f'ISC_ring_c{i}', (0, 0, 0), M('crystal'), coll, seed=40 + i, n=3, h=2.6, r=0.5),
                          p, random.uniform(0, 360)))
        objs.append(place(geo.sphere(f'ISC_ring_glow{i}', 0.55, (p[0], p[1], p[2] + 0.4), M('lantern'), seg=10, ring=8, coll=coll), p, 0))
    # 岛底"晶脉"环带（两条发光带，随岩体起伏）
    for i, (rz, rj) in enumerate([(11.5, 6.8), (14.2, 3.4)]):
        ring = []
        for k in range(24):
            a = k / 24 * math.tau
            rr = rz + math.sin(a * 5 + i * 2) * 0.55
            ring.append((math.cos(a) * rr, math.sin(a) * rr, rz + 0.4))
        objs.append(geo.tube(f'ISC_vein{i}', ring, 0.14, M('crystal'), coll, res=4))
    # —— 垂蔓（多条不同深度，拉出岩面） ——
    for i in range(16):
        a = random.uniform(0, 360)
        r0 = random.uniform(24.5, 28)
        out = random.uniform(1.4, 2.6)
        deep = random.uniform(3.5, 9.5)
        p0 = (math.cos(D(a)) * (r0 + 0.4), math.sin(D(a)) * (r0 + 0.4), -random.uniform(1.0, 2.4))
        p1 = (math.cos(D(a)) * (r0 + out * 0.5), math.sin(D(a)) * (r0 + out * 0.5), -deep * 0.55)
        p2 = (math.cos(D(a)) * (r0 + out * 0.72), math.sin(D(a)) * (r0 + out * 0.72), -deep)
        objs.append(geo.tube(f'ISC_vine{i}', [p0, p1, p2], 0.07, M('foliage'), coll, res=4))
        objs.append(geo.ico(f'ISC_vineleaf{i}', 0.22, (math.cos(D(a)) * (r0 + out * 0.7), math.sin(D(a)) * (r0 + out * 0.7), -deep * 0.9),
                            M('foliage_light'), sub=1, coll=coll, scale=(1, 1, 0.6)))
    # —— 岛缘护墙（两段弧形：E 段与 W/N 大段；南 + 东南开敞：海心院/浮池地盘；山门口开缺） ——
    def wall_seg(name, a0, a1):
        n = max(8, int((a1 - a0) / 4))
        angs = [D(a0 + (a1 - a0) * i / n) for i in range(n + 1)]
        verts = []
        for a in angs:
            ca, sa = math.cos(a), math.sin(a)
            for (rr, h) in [(28.35, 0.0), (28.85, 0.0), (28.85, 0.95), (28.35, 0.95)]:
                verts.append((ca * rr, sa * rr, h))
        faces = []
        for i in range(n):
            b = (i + 1) * 4
            a4 = i * 4
            faces += [(a4, b, b + 1, a4 + 1), (a4 + 1, b + 1, b + 2, a4 + 2),
                      (a4 + 2, b + 2, b + 3, a4 + 3), (a4 + 3, b + 3, b, a4)]
        return geo._mesh(name, verts, faces, M('basalt'), (0, 0, 0), (0, 0, 0), (1, 1, 1), coll, True)
    objs.append(wall_seg('ISC_wallE', -24, 26))
    objs.append(wall_seg('ISC_wallN', 155, 308))
    # —— 环径（岛缘内侧环路） ——
    ring_pts = [dirp(a, 24.6) for a in range(0, 360, 9)]
    objs.append(geo.ribbon('ISC_ring_path', ring_pts, 1.4, 0.10, M('cobble'), coll, closed=True))
    return objs

# ================================================================ 星陨塔
def build_tower(coll):
    objs = []
    # 台基两级
    objs.append(geo.cyl('TWR_plinth1', 6.1, 6.4, 1.15, (0, 0, 0.575), M('limestone'), verts=8, coll=coll))
    objs.append(geo.cyl('TWR_plinth2', 5.2, 5.5, 1.05, (0, 0, 1.7), M('sandstone'), verts=8, coll=coll))
    # 下段
    objs.append(geo.cyl('TWR_low', 4.95, 4.62, 11.2, (0, 0, 2.23 + 5.6), M('sandstone'), verts=8, coll=coll))
    objs.append(geo.cyl('TWR_low_cor', 5.45, 5.45, 0.5, (0, 0, 13.75), M('limestone'), verts=8, coll=coll))
    # 下段窗（南面留门位）
    apot = 4.5 * math.cos(D(22.5))
    for i in range(8):
        a = 45 * i
        if abs(((a - 90) + 540) % 360 - 180) < 1.0:  # 南面（门朝向 +Y）
            continue
        p0 = dirp(a, apot)
        objs.append(place(geo.window(f'TWR_w{i}', 1.15, 2.7, (0, 0, 0), M('glass_warm'), M('limestone'),
                                     coll=coll), (p0[0], p0[1], 4.6 + 1.4), a - 90))
        objs.append(place(geo.cyl(f'TWR_o{i}', 0.5, 0.5, 0.12, (0, 0, 0), M('glass_warm'),
                                  rot=(90, 0, 0), verts=12, coll=coll), (p0[0], p0[1], 9.6), a))
    # 中段 + 环廊
    objs.append(geo.cyl('TWR_mid', 4.05, 3.8, 9.0, (0, 0, 14.25 + 4.5), M('sandstone'), verts=8, coll=coll))
    objs.append(geo.cyl('TWR_balc', 4.75, 4.65, 0.32, (0, 0, 14.45), M('limestone'), verts=8, coll=coll))
    objs.append(geo.ring_band('TWR_balc_rail', 4.35, 0.85, 0.12, (0, 0, 0), M('cobble'), coll,
                              segs=32, y0=14.61))
    apot2 = 3.6 * math.cos(D(22.5))
    for i in range(8):
        a = 45 * i
        p0 = dirp(a, apot2)
        objs.append(place(geo.window(f'TWR_wm{i}', 1.05, 2.2, (0, 0, 0), M('glass_warm'), M('limestone'),
                                     coll=coll), (p0[0], p0[1], 19.35), a - 90))
    objs.append(geo.cyl('TWR_mid_cor', 4.42, 4.42, 0.45, (0, 0, 23.5), M('limestone'), verts=8, coll=coll))
    # 上段 + 金边圆窗
    objs.append(geo.cyl('TWR_up', 3.35, 3.15, 6.2, (0, 0, 23.95 + 3.1), M('sandstone'), verts=8, coll=coll))
    apot3 = 2.95 * math.cos(D(22.5))
    for i in [0, 1, 2, 3]:
        a = 45 * i + 22.5
        p0 = dirp(a, apot3 * 1.02)
        objs.append(place(geo.torus(f'TWR_ru{i}', 0.62, 0.07, (0, 0, 0), M('gold'),
                                    coll=coll, segs=20, minor=8), (p0[0], p0[1], 27.6), 0))
        objs.append(place(geo.cyl(f'TWR_rg{i}', 0.55, 0.55, 0.3, (0, 0, 0), M('glass_warm'),
                                  rot=(90, 0, 0), verts=14, coll=coll), (p0[0], p0[1], 27.6), a))
    objs.append(geo.cyl('TWR_up_cor', 3.35, 3.35, 0.4, (0, 0, 30.5), M('limestone'), verts=8, coll=coll))
    # 观景穹顶（带开缝）+ 金肋
    objs.append(geo.cyl('TWR_dome_base', 2.95, 2.95, 0.5, (0, 0, 30.9), M('limestone'), verts=8, coll=coll))
    objs.append(geo.lathe('TWR_dome', [(2.9, 0), (2.86, 0.8), (2.7, 1.6), (2.35, 2.3), (1.6, 2.85), (0.5, 3.1)],
                          24, M('copperverde'), (0, 0, 31.4), coll, gap=(D(-100), D(-40))))
    for i in range(8):
        a = 22.5 + 45 * i
        if -100 < a < -40 or 260 < a < 320:
            continue
        pts = []
        for t in range(6):
            u = t / 5
            r = 2.9 * (1 - u * u * 0.97)
            hh = 3.1 * u * 1.02
            pts.append((math.cos(D(a)) * r, math.sin(D(a)) * r, 31.4 + hh))
        objs.append(geo.tube(f'TWR_rib{i}', pts, 0.05, M('gold'), coll, res=3))
    # 顶塔 + 裂隙晶 + 金环
    objs.append(geo.cyl('TWR_crown', 0.62, 0.72, 0.9, (0, 0, 34.4), M('limestone'), verts=8, coll=coll))
    objs.append(geo.torus('TWR_crown_ring', 0.6, 0.06, (0, 0, 34.9), M('gold'), coll=coll, segs=20, minor=8))
    objs.append(geo.crystal_cluster('TWR_crystal', (0, 0, 35.7), M('crystal'), coll, seed=9, n=5, h=4.2, r=0.72))
    objs.append(place(geo.torus('TWR_halo2', 3.0, 0.05, (0, 0, 0), M('gold'), coll=coll,
                                segs=36, minor=6), (0, 0, 38.6), 0))
    objs[-1].rotation_euler = Euler((D(-14), 0, D(24)), 'XYZ')
    halo = place(geo.torus('TWR_halo', 2.25, 0.045, (0, 0, 0), M('gold'), coll=coll,
                           segs=32, minor=6), (0, 0, 37.4), 0)
    halo.rotation_euler = Euler((D(20), 0, 0), 'XYZ')
    objs.append(halo)
    # 塔门（南向 +Y）+ 门灯
    objs.append(place(geo.arch_door('TWR_door', 2.3, 3.2, (0, 0, 0), M('limestone'), M('dark_stone'),
                                    coll=coll), (0, 4.35, 2.05), 180))
    for sx in (-1, 1):
        objs.append(place(geo.lantern(f'TWR_dl{sx}', (0, 0, 0), M('limestone'), M('lantern'),
                                      coll=coll, h=1.7), (sx * 1.9, 4.9, 0), 0))
    return objs

# ================================================================ 中央广场
def build_plaza(coll):
    objs = []
    PC = (0, 10.2)
    objs.append(place(geo.cyl('PLZ_base', 9.6, 9.9, 0.14, (0, 0, 0.07), M('plaza_mid'), verts=40, coll=coll), PC, 0))
    objs.append(place(geo.cyl('PLZ_core', 4.6, 4.8, 0.2, (0, 0, 0.17), M('plaza_dark'), verts=32, coll=coll), PC, 0))
    for i, mm in enumerate(['tile_dawn', 'tile_speak', 'tile_forge', 'tile_tide']):
        a0 = 45 + 90 * i
        n = 7
        verts = [(0, 0, 0.30)]
        for k in range(n + 1):
            a = D(a0 + 90 * k / n)
            verts.append((math.cos(a) * 2.6, math.sin(a) * 2.6, 0.30))
        faces = [(0, k + 1, k + 2) for k in range(n)]
        objs.append(place(geo._mesh(f'PLZ_pie{i}', verts, faces, M(mm), (0, 0, 0), (0, 0, 0), (1, 1, 1), coll, False), PC, 0))
    # 分选礼台（中心偏南）
    T = (PC[0], PC[1] + 1.8)
    objs.append(place(geo.cyl('PLZ_alt1', 3.9, 4.1, 0.26, (0, 0, 0.13), M('limestone'), verts=28, coll=coll), T, 0))
    objs.append(place(geo.cyl('PLZ_alt2', 3.3, 3.5, 0.3, (0, 0, 0.41), M('sandstone'), verts=28, coll=coll), T, 0))
    objs.append(place(geo.cyl('PLZ_alt3', 2.0, 2.15, 0.34, (0, 0, 0.20), M('limestone'), verts=24, coll=coll), T, 0))
    objs.append(place(geo.lantern('PLZ_lamp', (0, 0, 0), M('limestone'), M('lantern'), coll=coll, h=2.9),
                      (T[0], T[1], 0.56), 0))
    # 12 座旁听石座
    for i in range(12):
        a = i * 30 + 15
        p = (T[0] + math.cos(D(a)) * 4.5, T[1] + math.sin(D(a)) * 4.5)
        objs.append(place(geo.box(f'PLZ_seat{i}', 0.7, 0.45, 0.42, (0, 0, 0.1), M('limestone'), coll=coll, bevel=0.03),
                          (p[0], p[1], 0), a + 90))
    # 四面旗
    for i, (a, mm) in enumerate([(45, 'cloth_dawn'), (135, 'cloth_tide'), (225, 'cloth_speak'), (315, 'cloth_forge')]):
        p = (PC[0] + math.cos(D(a)) * 6.2, PC[1] + math.sin(D(a)) * 6.2)
        objs.append(place(geo.flagpole(f'PLZ_flag{i}', (0, 0, 0), M('iron'), M(mm), coll=coll, h=6.2),
                          (p[0], p[1], 0), a + 90))
    # 主径：山门 → 广场；四院径
    pts = [(21.4, -16.7), (17.5, -11.5), (12.5, -5.5), (6.5, 1.5), (1.5, 6.5), (0.0, 10.2)]
    objs.append(geo.ribbon('PLZ_main_path', pts, 2.6, 0.115, M('cobble'), coll))
    for a, rr in [(8, 15.8), (182, 15.8), (-98, 15.8), (112, 17.2)]:
        e = dirp(a, rr)
        objs.append(geo.ribbon(f'PLZ_path_{abs(a)}',
                               [(PC[0] + math.cos(D(a)) * 8.2, PC[1] + math.sin(D(a)) * 8.2),
                                (e[0] * 0.94, e[1] * 0.94)], 1.7, 0.105, M('cobble'), coll))
    return objs

# ================================================================ 四院回廊
def build_cloister(coll, a, tile, name):
    objs = []
    R0, R1 = 5.6, 15.6
    mid = (R0 + R1) / 2
    rotz = a + 90
    L = R1 - R0
    offs = (math.cos(D(a + 90)), math.sin(D(a + 90)))
    # 坡道（向外下倾 4°）
    floor = geo.box(f'{name}_floor', 2.6, L + 0.6, 0.22, (0, 0, 0), M('cobble'), coll=coll, bevel=0.02)
    fl = place(floor, (dirp(a, mid)[0], dirp(a, mid)[1], 0.42), rotz)
    fl.rotation_euler = Euler((D(-4), 0, D(rotz)), 'XYZ')
    objs.append(fl)
    roof_ = geo.box(f'{name}_roof', 3.4, L + 1.2, 0.16, (0, 0, 0), M(tile), coll=coll, bevel=0.03)
    rf = place(roof_, (dirp(a, mid)[0], dirp(a, mid)[1], 3.48), rotz)
    rf.rotation_euler = Euler((D(-4.2), 0, D(rotz)), 'XYZ')
    objs.append(rf)
    for i, rr in enumerate([7.2, 10.2, 13.2, 15.2]):
        px, py = dirp(a, rr)
        cx, cy = px + offs[0] * 1.05, py + offs[1] * 1.05
        objs += geo.column(f'{name}_col{i}', 0.17, 3.0, (cx, cy, 0.44), M('limestone'), coll=coll, verts=10)
        ix, iy = px - offs[0] * 1.05, py - offs[1] * 1.05
        objs.append(place(geo.box(f'{name}_wall{i}', 0.22, 3.4 + 0.2, 1.05, (0, 0, 0), M('sandstone'),
                                  coll=coll, bevel=0.02), (ix, iy, 0.99), rotz))
    # 院门（无锁，双扇微开）
    gx, gy = dirp(a, R1 + 0.35)
    objs.append(place(geo.box(f'{name}_post', 3.4, 0.4, 2.9, (0, 0, 0), M('limestone'), coll=coll, bevel=0.04),
                      (gx, gy, 1.45), rotz))
    for s in (-1, 1):
        d = geo.box(f'{name}_door{s}', 1.05, 0.09, 2.3, (0, 0, 0), M('wood_dark'), coll=coll, bevel=0.015)
        d.rotation_euler = Euler((0, 0, D(s * -38)), 'XYZ')
        objs.append(place(d, (gx + offs[0] * 0.52 * s * 0.0, gy, 0.08), rotz))
        objs[-1].location = (gx + math.cos(D(rotz + 90)) * 0.5 * s, gy + math.sin(D(rotz + 90)) * 0.5 * s, 0.08)
        objs[-1].rotation_euler = Euler((0, 0, D(rotz) + D(s * -34)), 'XYZ')
    objs.append(place(geo.box(f'{name}_lin', 3.5, 0.5, 0.35, (0, 0, 0), M('limestone'), coll=coll, bevel=0.03),
                      (gx, gy, 2.95), rotz))
    return objs

# ================================================================ 四院
def build_dawn(coll):
    objs = []
    A = 8.0
    C = dirp(A, 20.2)
    rotz = 90 + A
    uv = (math.cos(D(rotz + 90)), math.sin(D(rotz + 90)))   # 沿立面方向
    rv = (math.cos(D(rotz)), math.sin(D(rotz)))             # 朝岛心方向
    objs.append(place(geo.box('DAW_sty', 15.6, 10.6, 0.5, (0, 0, 0.25), M('limestone'), coll=coll, bevel=0.05), C, rotz))
    objs.append(place(geo.box('DAW_hall', 14, 9, 5.0, (0, 0, 0.5 + 2.5), M('sandstone'), coll=coll, bevel=0.06), C, rotz))
    front = geo.colonnade('DAW_cols', 6, 0.4, 4.4, 2.15, (0, 0, 0), M('limestone'), coll=coll, beam=True, beam_h=0.5, beam_d=0.9)
    fl = place(front, (C[0] + rv[0] * 4.55, C[1] + rv[1] * 4.55, 0.5), rotz)
    objs.append(fl)
    objs.append(place(geo.prism('DAW_roof', 10.4, 15.8, 2.6, (0, 0, 6.0), M('tile_deep'), rot=(0, 0, 90), coll=coll), C, rotz))
    objs.append(place(geo.prism('DAW_ped', 2.2, 14.2, 2.0, (0, 0, 0), M('limestone'), rot=(0, 0, 90), coll=coll),
                      (C[0] + rv[0] * 4.9, C[1] + rv[1] * 4.9, 5.3), rotz))
    # 钟楼（北侧 = 立面方向 -1）
    tp = (C[0] + uv[0] * -6.2, C[1] + uv[1] * -6.2)
    objs.append(place(geo.box('DAW_tw', 3.1, 3.1, 8.2, (0, 0, 0.5 + 4.1), M('sandstone'), coll=coll, bevel=0.06), tp, rotz))
    objs.append(place(geo.window('DAW_tw_w', 1.3, 1.9, (0, 0, 0), M('glass_warm'), M('limestone'), coll=coll),
                      (tp[0], tp[1], 7.6), rotz + 90))
    objs.append(place(geo.pyr('DAW_tw_top', 3.9, 3.9, 2.4, (0, 0, 9.0), M('gold'), coll=coll), tp, rotz))
    objs.append(place(geo.cyl('DAW_sun', 0.42, 0.42, 0.12, (0, 0, 0), M('gold'), rot=(90, 0, 0), verts=14, coll=coll),
                      (tp[0], tp[1], 11.6), rotz + 90))
    for s in (-1, 1):
        objs.append(place(geo.box(f'DAW_wing{s}', 1.15, 0.06, 0.28, (0, 0, 0), M('gold'), coll=coll),
                          (tp[0] + math.cos(D(rotz + 90)) * 0.62 * s, tp[1] + math.sin(D(rotz + 90)) * 0.62 * s, 11.55),
                          rotz + 90 + s * 38))
    # 侧翼讲堂（立面 -1 方向更远）
    wp = (C[0] + uv[0] * -9.4, C[1] + uv[1] * -9.4)
    objs.append(place(geo.box('DAW_wing_hall', 11.5, 4.6, 3.4, (0, 0, 0.5 + 1.7), M('sandstone'), coll=coll, bevel=0.05), wp, rotz))
    objs.append(place(geo.prism('DAW_wing_roof', 5.4, 12.4, 1.5, (0, 0, 4.3), M('tile_deep'), rot=(0, 0, 90), coll=coll), wp, rotz))
    for i in range(4):
        x = -4.2 + i * 2.8
        lx = wp[0] + uv[0] * x + rv[0] * 2.35
        ly = wp[1] + uv[1] * x + rv[1] * 2.35
        objs.append(place(geo.window(f'DAW_ww{i}', 0.9, 1.7, (0, 0, 0), M('glass_warm'), M('limestone'), coll=coll),
                          (lx, ly, 2.7), rotz + 90))
    # 前院：金叶梧桐 ×4
    for i, (dx, dz, s) in enumerate([(-4.6, 6.6, 101), (4.6, 6.6, 102), (-4.6, 9.2, 103), (4.6, 9.2, 104)]):
        p = (C[0] + uv[0] * dx + rv[0] * dz, C[1] + uv[1] * dx + rv[1] * dz)
        objs.append(geo.tree(f'DAW_tree{i}', (p[0], p[1], 0.15), 5.2 + 0.5 * (i % 3), 2.1,
                             M('foliage_autumn'), M('trunk'), coll, seed=s))
    objs.append(place(geo.lantern('DAW_lp', (0, 0, 0), M('limestone'), M('lantern'), coll=coll, h=1.8),
                      (C[0] + uv[0] * 1.8, C[1] + uv[1] * 1.8, 0.5), 0))
    return objs

def build_speak(coll):
    objs = []
    A = 182.0
    C = dirp(A, 20.8)
    rotz = 90 + A
    uv = (math.cos(D(A + 90)), math.sin(D(A + 90)))   # 侧向
    rv = (-math.cos(D(A)), -math.sin(D(A)))            # 朝岛心
    # 院墙（三面）
    objs.append(place(geo.box('SPK_wall_f', 15.8, 0.4, 2.0, (0, 0, 1.0), M('limestone'), coll=coll, bevel=0.04),
                      (C[0] + rv[0] * 4.9, C[1] + rv[1] * 4.9, 0), rotz))
    for s in (-1, 1):
        objs.append(place(geo.box(f'SPK_wall_s{s}', 0.4, 9.6, 2.0, (0, 0, 1.0), M('limestone'), coll=coll, bevel=0.04),
                          (C[0] + uv[0] * 7.9, C[1] + uv[1] * 7.9, 0), rotz))
    # 主体书楼 + 陡尖顶
    objs.append(place(geo.box('SPK_hall', 16, 8, 5.4, (0, 0, 0.3 + 2.7), M('sandstone'), coll=coll, bevel=0.06), C, rotz))
    objs.append(place(geo.prism('SPK_roof', 5.6, 18.4, 6.2, (0, 0, 6.2), M('tile_speak'), rot=(0, 0, 90), coll=coll), C, rotz))
    # 中脊小尖塔 ×5
    for i, x in enumerate([-6.5, -3.2, 0, 3.2, 6.5]):
        p = (C[0] + uv[0] * x, C[1] + uv[1] * x)
        objs.append(place(geo.cyl(f'SPK_spire{i}', 0.3, 0.36, 2.2, (0, 0, 12.0), M('limestone'), verts=8, coll=coll),
                          (p[0], p[1], 0), 0))
        objs.append(place(geo.pyr(f'SPK_spireT{i}', 0.75, 0.75, 1.7, (0, 0, 14.1), M('tile_speak'), coll=coll),
                          (p[0], p[1], 0), 0))
    # 观星台（后园，可开穹顶）
    tp = (C[0] + uv[0] * -7.2, C[1] + uv[1] * -7.2)
    objs.append(place(geo.cyl('SPK_obs', 2.0, 2.2, 3.6, (0, 0, 1.8), M('sandstone'), verts=14, coll=coll), tp, 0))
    objs.append(geo.lathe('SPK_obs_dome', [(1.9, 0), (1.85, 0.55), (1.7, 1.05), (1.2, 1.5), (0.38, 1.75)],
                          20, M('slate'), (tp[0], tp[1], 3.6), coll, gap=(D(120), D(210))))
    objs.append(place(geo.cyl('SPK_tel', 0.16, 0.22, 1.7, (0, 0, 0), M('iron'), verts=10, coll=coll),
                      (tp[0] + rv[0] * -0.4, tp[1] + rv[1] * -0.4, 5.0), 0))
    # 高窗排 ×5
    for i, x in enumerate([-6.2, -3.1, 0, 3.1, 6.2]):
        lx = C[0] + uv[0] * x + rv[0] * 4.15
        ly = C[1] + uv[1] * x + rv[1] * 4.15
        objs.append(place(geo.window(f'SPK_w{i}', 0.8, 2.4, (0, 0, 0), M('glass_warm'), M('limestone'), coll=coll, mullions=2),
                          (lx, ly, 3.4), rotz + 90))
    # 院门（门朝北：局部 -Y 一侧开门洞于院墙）
    g = (C[0] + rv[0] * 4.95, C[1] + rv[1] * 4.95)
    objs.append(place(geo.arch_door('SPK_gate', 1.6, 2.6, (0, 0, 0), M('limestone'), M('wood_dark'), coll=coll),
                      (g[0], g[1], 1.3), rotz))
    # 八百岁梧桐 + 2 棵
    tp2 = (C[0] + uv[0] * 5.8 + rv[0] * -6.6, C[1] + uv[1] * 5.8 + rv[1] * -6.6)
    objs.append(geo.tree('SPK_grand', (tp2[0], tp2[1], 0.15), 9.2, 4.6, M('foliage'), M('trunk'), coll, seed=77, bend=-10))
    for i, (dx, dz, s) in enumerate([(4.8, -5.4, 78), (-6.4, -3.8, 79)]):
        p = (C[0] + uv[0] * dx + rv[0] * dz, C[1] + uv[1] * dx + rv[1] * dz)
        objs.append(geo.tree(f'SPK_tree{i}', (p[0], p[1], 0.15), 5.8, 2.4, M('foliage_light'), M('trunk'), coll, seed=s))
    return objs

def build_forge(coll):
    objs = []
    A = -98.0
    C = dirp(A, 20.4)
    rotz = 90 + A
    uv = (math.cos(D(A + 90)), math.sin(D(A + 90)))   # 侧向
    rv = (-math.cos(D(A)), -math.sin(D(A)))            # 朝岛心
    objs.append(place(geo.box('FRG_hall', 13, 10, 6.0, (0, 0, 0.3 + 3.0), M('mountain_rock'), coll=coll, bevel=0.07), C, rotz))
    # 阶梯平台屋顶（两级）
    objs.append(place(geo.box('FRG_p1', 13.8, 5.6, 0.55, (0, 0, 6.6), M('slate'), coll=coll, bevel=0.04),
                      (C[0] + rv[0] * -1.9, C[1] + rv[1] * -1.9, 0), rotz))
    objs.append(place(geo.box('FRG_p2', 13.8, 3.2, 0.5, (0, 0, 7.15), M('slate'), coll=coll, bevel=0.04),
                      (C[0] + rv[0] * 0.4, C[1] + rv[1] * 0.4, 0), rotz))
    objs.append(place(geo.box('FRG_par', 13.8, 0.25, 0.6, (0, 0, 7.5), M('mountain_rock'), coll=coll),
                      (C[0] + rv[0] * -4.05, C[1] + rv[1] * -4.05, 0), rotz))
    # 辉纹饰带（正面 3 段）
    for i, x in enumerate([-4.2, 0, 4.2]):
        lx = C[0] + uv[0] * x + rv[0] * 5.15
        ly = C[1] + uv[1] * x + rv[1] * 5.15
        objs.append(place(geo.box(f'FRG_rune{i}', 0.85, 0.1, 2.6, (0, 0, 0), M('bronze'), coll=coll, bevel=0.02),
                          (lx, ly, 2.7), rotz + 90))
    # 锻场（东侧连体）+ 大烟囱
    dx = C[0] + uv[0] * 9.9
    dy = C[1] + uv[1] * 9.9
    objs.append(place(geo.box('FRG_forge', 6.6, 9, 4.4, (0, 0, 0.3 + 2.2), M('mountain_rock'), coll=coll, bevel=0.06),
                      (dx, dy), rotz))
    r_ = place(geo.box('FRG_forge_roof', 7.2, 9.6, 0.4, (0, 0, 0), M('slate'), coll=coll, bevel=0.02), (dx, dy, 4.75), rotz)
    r_.rotation_euler = Euler((0, D(7), 0), 'XYZ')
    objs.append(r_)
    ch = (dx + uv[0] * 2.2, dy + uv[1] * 2.2)
    objs.append(place(geo.cyl('FRG_chimney', 0.62, 0.5, 7.6, (0, 0, 3.8), M('mountain_rock'), verts=10, coll=coll), ch, 0))
    objs.append(place(geo.cyl('FRG_chim_top', 0.82, 0.82, 0.35, (0, 0, 7.7), M('dark_stone'), verts=10, coll=coll), ch, 0))
    objs.append(place(geo.cyl('FRG_ember', 0.4, 0.3, 0.3, (0, 0, 7.95), M('lantern'), verts=8, coll=coll), ch, 0))
    # 门前铁砧 + 木料堆 + 燃料仓
    anv = (C[0] + rv[0] * 7.8, C[1] + rv[1] * 7.8)
    objs.append(place(geo.box('FRG_anvil_top', 1.7, 0.62, 0.5, (0, 0, 0.85), M('iron'), coll=coll, bevel=0.05), anv, rotz + 90))
    objs.append(place(geo.box('FRG_anvil_body', 0.55, 0.5, 0.62, (0, 0, 0.31), M('basalt'), coll=coll, bevel=0.03), anv, 0))
    sil = (C[0] + uv[0] * -8.4, C[1] + uv[1] * -8.4)
    objs.append(place(geo.cyl('FRG_silo', 1.75, 1.85, 2.9, (0, 0, 1.45), M('mountain_rock'), verts=12, coll=coll), sil, 0))
    objs.append(place(geo.cyl('FRG_silo_cap', 1.85, 0.3, 1.0, (0, 0, 3.5), M('slate'), verts=12, coll=coll), sil, 0))
    for i, (dx2, dz2) in enumerate([(2.0, 5.8), (3.0, 5.8), (2.5, 6.7)]):
        p = (C[0] + uv[0] * dx2 + rv[0] * dz2, C[1] + uv[1] * dx2 + rv[1] * dz2)
        objs.append(place(geo.box(f'FRG_log{i}', 1.9, 0.5, 0.5, (0, 0, 0.25), M('wood_dark'), coll=coll, bevel=0.04),
                          (p[0], p[1], 0), rotz + 90))
    return objs

def build_tide(coll):
    objs = []
    A = 112.0
    C = dirp(A, 21.0)
    rotz = 90 + A
    uv = (math.cos(D(A + 90)), math.sin(D(A + 90)))   # 侧向
    rv = (-math.cos(D(A)), -math.sin(D(A)))            # 朝岛心
    objs.append(place(geo.box('TID_hall', 13, 7.6, 4.4, (0, 0, 0.3 + 2.2), M('sandstone'), coll=coll, bevel=0.06), C, rotz))
    objs.append(place(geo.prism('TID_roof', 7.4, 13.6, 1.9, (0, 0, 4.75), M('tile_tide'), rot=(0, 0, 90), coll=coll), C, rotz))
    for i, x in enumerate([-5.4, -1.8, 1.8, 5.4]):
        lx = C[0] + uv[0] * x + rv[0] * 4.0
        ly = C[1] + uv[1] * x + rv[1] * 4.0
        objs.append(place(geo.box(f'TID_col{i}', 0.26, 0.26, 3.9, (0, 0, 0), M('wood'), coll=coll, bevel=0.02),
                          (lx, ly, 2.9), rotz + 90))
    objs.append(place(geo.box('TID_beam', 14.6, 0.3, 0.34, (0, 0, 0), M('wood'), coll=coll, bevel=0.02),
                      (C[0] + rv[0] * 4.05, C[1] + rv[1] * 4.05, 4.85), rotz + 90))
    objs.append(place(geo.box('TID_trim', 14.8, 0.12, 0.22, (0, 0, 0), M('tile_tide'), coll=coll, bevel=0.02),
                      (C[0] + rv[0] * 4.2, C[1] + rv[1] * 4.2, 4.42), rotz + 90))
    # 望楼（西端 + 鲸尾）
    wtp = (C[0] + uv[0] * -7.9, C[1] + uv[1] * -7.9)
    objs.append(place(geo.box('TID_watch', 2.7, 2.7, 6.4, (0, 0, 0.3 + 3.2), M('sandstone'), coll=coll, bevel=0.05), wtp, rotz))
    objs.append(place(geo.box('TID_watch_top', 3.3, 3.3, 1.5, (0, 0, 6.8 + 0.75), M('wood'), coll=coll, bevel=0.04), wtp, rotz))
    for i in range(4):
        a = 45 + 90 * i
        p0 = (wtp[0] + math.cos(D(a)) * 1.62, wtp[1] + math.sin(D(a)) * 1.62)
        objs.append(place(geo.window(f'TID_ww{i}', 0.8, 1.1, (0, 0, 0), M('glass_warm'), M('wood'), coll=coll),
                          (p0[0], p0[1], 8.5), a - 90))
    objs.append(place(geo.box('TID_tail1', 0.14, 1.9, 0.05, (0, 0, 0), M('wood_dark'), coll=coll, bevel=0.01),
                      (wtp[0], wtp[1], 9.6), rotz + 65))
    objs.append(place(geo.box('TID_tail2', 0.14, 1.9, 0.05, (0, 0, 0), M('wood_dark'), coll=coll, bevel=0.01),
                      (wtp[0], wtp[1], 9.6), rotz + 115))
    # 架空平台 + 桩柱
    deckp = (C[0] + rv[0] * 5.9, C[1] + rv[1] * 5.9)
    deckp = (C[0] + rv[0] * 5.2, C[1] + rv[1] * 5.2)
    objs.append(place(geo.box('TID_deck', 9.6, 2.6, 0.3, (0, 0, 0.30), M('wood'), coll=coll, bevel=0.02), deckp, rotz))
    for i, x in enumerate([-4.4, 0, 4.4]):
        pp = (deckp[0] + uv[0] * x + rv[0] * 1.0, deckp[1] + uv[1] * x + rv[1] * 1.0)
        objs.append(place(geo.box(f'TID_pile{i}', 0.3, 0.3, 2.3, (0, 0, -1.15), M('wood_dark'), coll=coll, bevel=0.02),
                          (pp[0], pp[1], 0.35), 0))
    # 船坞 + 系船柱
    dockp = (C[0] + rv[0] * 8.2, C[1] + rv[1] * 8.2)
    objs.append(place(geo.box('TID_dock', 3.4, 2.2, 0.34, (0, 0, -0.28), M('wood'), coll=coll, bevel=0.02), dockp, rotz))
    for i in range(3):
        pp = (dockp[0] + uv[0] * (-1.1 + i * 1.1), dockp[1] + uv[1] * (-1.1 + i * 1.1))
        objs.append(place(geo.cyl(f'TID_bollard{i}', 0.14, 0.18, 1.05, (0, 0, 0.52), M('wood_dark'), verts=10, coll=coll), pp, 0))
        objs.append(place(geo.torus(f'TID_knot{i}', 0.2, 0.05, (0, 0, 1.02), M('rope'), coll=coll, segs=14, minor=6), pp, 0))
    # 蓝窗 ×3 + 门 + 蓝灯笼
    for i, x in enumerate([-3.4, 0, 3.4]):
        lx = C[0] + uv[0] * x + rv[0] * 3.95
        ly = C[1] + uv[1] * x + rv[1] * 3.95
        objs.append(place(geo.window(f'TID_w{i}', 1.0, 1.5, (0, 0, 0), M('glass_warm'), M('wood'), coll=coll),
                          (lx, ly, 2.7), rotz + 90))
    objs.append(place(geo.arch_door('TID_door', 1.5, 2.4, (0, 0, 0), M('wood'), M('dark_stone'), coll=coll),
                      (C[0] + rv[0] * 4.1, C[1] + rv[1] * 4.1, 1.5), rotz + 180))
    objs.append(place(geo.lantern('TID_lp', (0, 0, 0), M('wood'), M('glass_cool'), coll=coll, h=1.7),
                      (C[0] + uv[0] * -3.2 + rv[0] * 5.6, C[1] + uv[1] * -3.2 + rv[1] * 5.6, 0.1), 0))
    return objs

# ================================================================ 星穗馆
def build_library(coll):
    objs = []
    A = 215.0
    C = dirp(A, 15.2)
    rotz = 90 + A
    rv = (-math.cos(D(A)), -math.sin(D(A)))      # 朝岛心
    objs.append(place(geo.cyl('LIB_base1', 6.9, 7.1, 0.42, (0, 0, 0.21), M('limestone'), verts=28, coll=coll), C, 0))
    objs.append(place(geo.cyl('LIB_base2', 6.2, 6.4, 0.42, (0, 0, 0.63), M('sandstone'), verts=28, coll=coll), C, 0))
    objs.append(place(geo.cyl('LIB_drum', 5.6, 5.7, 4.4, (0, 0, 0.84 + 2.2), M('sandstone'), verts=28, coll=coll), C, 0))
    for i in range(8):
        a = 45 * i
        p0 = dirp(a, 5.7)
        objs.append(place(geo.box(f'LIB_pil{i}', 0.5, 0.34, 4.2, (0, 0, 0.84 + 2.3), M('limestone'), coll=coll, bevel=0.03),
                          (C[0] + p0[0], C[1] + p0[1], 0), a + 90))
        pa = 22.5 + 45 * i
        p1 = dirp(pa, 5.72)
        objs.append(place(geo.window(f'LIB_w{i}', 0.95, 2.6, (0, 0, 0), M('glass_warm'), M('limestone'), coll=coll, mullions=2),
                          (C[0] + p1[0], C[1] + p1[1], 0.84 + 2.4), pa - 90))
    objs.append(place(geo.cyl('LIB_ent', 6.5, 6.6, 0.8, (0, 0, 5.35), M('limestone'), verts=28, coll=coll), C, 0))
    objs.append(place(geo.sphere('LIB_dome', 5.9, (C[0], C[1], 6.35), M('slate'), scale=(1, 1, 0.62), seg=24, ring=14, coll=coll), C, 0))
    for i in range(16):
        a = 22.5 * i
        pts = []
        for t in range(9):
            u = D(t / 8 * 90)
            pts.append((C[0] + math.cos(u) * 5.9 * math.cos(D(a)),
                        C[1] + math.cos(u) * 5.9 * math.sin(D(a)),
                        6.35 + math.sin(u) * 5.9 * 0.62))
        objs.append(geo.tube(f'LIB_rib{i}', pts, 0.055, M('gold'), coll, res=3))
    objs.append(place(geo.cyl('LIB_crown', 0.5, 0.62, 1.0, (0, 0, 10.15), M('limestone'), verts=12, coll=coll), C, 0))
    objs.append(place(geo.bipyr('LIB_grain', 0.4, 2.0, (C[0], C[1], 11.6), M('gold'), n=8, coll=coll), C, 0))
    g = (C[0] + rv[0] * 6.0, C[1] + rv[1] * 6.0)
    objs.append(place(geo.arch_door('LIB_door', 2.1, 3.2, (0, 0, 0), M('limestone'), M('wood_dark'), coll=coll),
                      (g[0], g[1], 2.45), rotz + 180))
    # 侧门（西北侧半掩）
    a2 = A - 55
    g2 = (dirp(a2, 15.2)[0] + math.cos(D(a2)) * 5.9, dirp(a2, 15.2)[1] + math.sin(D(a2)) * 5.9)
    objs.append(place(geo.box('LIB_side_door', 1.3, 0.1, 2.4, (0, 0, 0), M('wood_dark'), coll=coll, bevel=0.01),
                      (g2[0], g2[1], 2.05), a2 - 90))
    # 馆前石灯对
    for s in (-1, 1):
        pp = (C[0] + math.cos(D(rotz + 90)) * 2.6 * s + rv[0] * 4.4,
              C[1] + math.sin(D(rotz + 90)) * 2.6 * s + rv[1] * 4.4)
        objs.append(place(geo.lantern(f'LIB_lp{s}', (0, 0, 0), M('limestone'), M('lantern'), coll=coll, h=1.6),
                          (pp[0], pp[1], 0.85), 0))
    return objs

# ================================================================ 宿舍环
def build_dorms(coll):
    objs = []
    RR = 22.0
    def sector(a):
        if -45 <= a < 45:
            return 'tile_dawn'
        if 45 <= a < 135:
            return 'tile_tide'
        if 135 <= a < 225 or a < -135:
            return 'tile_speak'
        return 'tile_forge'
    for i in range(22):
        a = -10 + i * 16.36
        if i == 9:
            # 第 22 栋「缺席」：旧地基 + 残石（谜二）
            p = dirp(a - 8.2, RR)
            objs.append(place(geo.cyl(f'DRM_gap{i}', 2.9, 3.0, 0.1, (0, 0, 0.05), M('plaza_dark'), verts=20, coll=coll), p, 0))
            objs.append(place(geo.box(f'DRM_gapstone{i}', 0.5, 0.35, 0.22, (0, 0, 0.1), M('cobble'), coll=coll, bevel=0.02),
                              (p[0] + 1.5, p[1] - 1.3, 0), 20))
            continue
        p = dirp(a, RR)
        rotz = a + 90
        mat = M(sector(a))
        uv = (math.cos(D(a + 90)), math.sin(D(a + 90)))   # 侧向
        rv = (-math.cos(D(a)), -math.sin(D(a)))           # 朝岛心
        objs.append(place(geo.box(f'DRM_h{i}', 5.9, 4.2, 2.5, (0, 0, 1.25), M('sandstone'), coll=coll, bevel=0.05), p, rotz))
        objs.append(place(geo.prism(f'DRM_r{i}', 4.9, 6.8, 1.6, (0, 0, 2.42), mat, rot=(0, 0, 90), coll=coll), p, rotz))
        dr = (p[0] + rv[0] * 2.16, p[1] + rv[1] * 2.16)
        objs.append(place(geo.box(f'DRM_d{i}', 0.85, 0.1, 1.9, (0, 0, 0), M('wood_dark'), coll=coll, bevel=0.012),
                          (dr[0], dr[1], 0.95), rotz))
        objs.append(place(geo.box(f'DRM_dl{i}', 1.15, 0.16, 0.14, (0, 0, 0), M('limestone'), coll=coll),
                          (dr[0], dr[1], 1.95), rotz))
        for s in (-1, 1):
            wpos = (p[0] + uv[0] * 1.7 * s + rv[0] * 2.16, p[1] + uv[1] * 1.7 * s + rv[1] * 2.16)
            objs.append(place(geo.window(f'DRM_w{i}_{s}', 0.6, 0.85, (0, 0, 0), M('glass_warm'), M('limestone'), coll=coll),
                              (wpos[0], wpos[1], 1.7), rotz))
        chp = (p[0] - rv[0] * 0.8, p[1] - rv[1] * 0.8)
        objs.append(place(geo.box(f'DRM_ch{i}', 0.42, 0.42, 1.2, (0, 0, 0), M('mountain_rock'), coll=coll, bevel=0.02),
                          (chp[0], chp[1], 3.6), 0))
        objs.append(place(geo.box(f'DRM_st{i}', 1.6, 0.6, 0.22, (0, 0, 0.11), M('cobble'), coll=coll, bevel=0.02),
                          (p[0] + rv[0] * 2.75, p[1] + rv[1] * 2.75, 0), rotz))
        objs.append(place(geo.lantern(f'DRM_lp{i}', (0, 0, 0), M('limestone'), M('lantern'), coll=coll, h=1.5),
                          (p[0] + uv[0] * 2.7 - rv[0] * 1.2, p[1] + uv[1] * 2.7 - rv[1] * 1.2, 0), 0))
        lp = (p[0] + uv[0] * 3.1 - rv[0] * 1.2, p[1] + uv[1] * 3.1 - rv[1] * 1.2)
        objs.append(place(geo.box(f'DRM_wood{i}', 1.5, 0.5, 0.45, (0, 0, 0.22), M('wood_dark'), coll=coll, bevel=0.04), lp, rotz + 90))
    return objs

# ================================================================ 山门
def build_gate(coll):
    objs = []
    A = -38.0
    P = dirp(A, 27.4)
    rotz = A - 90
    rv = (math.cos(D(A)), math.sin(D(A)))         # 朝外
    uv = (math.cos(D(A + 90)), math.sin(D(A + 90)))      # 侧向
    # 台阶（向外 7 级）
    gpl = (P[0] - rv[0] * 1.7, P[1] - rv[1] * 1.7)
    objs.append(place(geo.cyl('GATE_plateau', 4.6, 4.9, 0.3, (0, 0, -0.18), M('cobble'), verts=22, coll=coll), gpl, 0))
    objs.append(place(geo.stairs('GATE_steps', 3.6, 5, 0.24, 0.46, (0, 0, 0), M('cobble'), coll=coll),
                      (P[0] + rv[0] * 1.0, P[1] + rv[1] * 1.0, -1.12), rotz + 180))
    # 双柱 + 弧形楣 + 星徽
    for s in (-1, 1):
        pp = (P[0] + uv[0] * 1.75 * s, P[1] + uv[1] * 1.75 * s)
        objs.append(place(geo.box(f'GATE_pil{s}', 0.75, 0.9, 4.3, (0, 0, 0), M('sandstone'), coll=coll, bevel=0.06), pp, rotz))
        objs.append(place(geo.box(f'GATE_pilcap{s}', 1.0, 1.15, 0.4, (0, 0, 4.5), M('limestone'), coll=coll, bevel=0.04), pp, rotz))
    objs.append(place(geo.arch_top('GATE_arch', 4.3, 3.9, (0, 0, 0), M('limestone'), coll=coll, n=9),
                      (P[0], P[1], 4.9), rotz))
    objs.append(place(geo.cyl('GATE_star', 0.5, 0.5, 0.16, (0, 0, 0), M('limestone'), rot=(90, 0, 0), verts=8, coll=coll),
                      (P[0], P[1], 6.3), rotz + 90))
    # 双守门像（剪影式：矮人锻像 / 精灵弓手）
    for s, kind in [(-1, 'dwarf'), (1, 'elf')]:
        pp = (P[0] + uv[0] * 3.6 * s, P[1] + uv[1] * 3.6 * s)
        objs.append(place(geo.box(f'GATE_ped{s}', 1.1, 1.1, 0.7, (0, 0, 0.35), M('basalt'), coll=coll, bevel=0.03), pp, rotz))
        if kind == 'dwarf':
            objs.append(place(geo.box('GATE_dw_body', 1.05, 0.7, 1.5, (0, 0, 1.45), M('sandstone'), coll=coll, bevel=0.09), pp, rotz))
            objs.append(place(geo.sphere('GATE_dw_head', 0.34, (pp[0], pp[1], 2.55), M('sandstone'), seg=12, ring=8, coll=coll), pp, 0))
            objs.append(place(geo.pyr('GATE_dw_helm', 0.55, 0.55, 0.5, (0, 0, 3.0), M('mountain_rock'), coll=coll), pp, 0))
            objs.append(place(geo.cyl('GATE_dw_hammer', 0.09, 0.09, 1.6, (0, 0, 0), M('wood_dark'), verts=8, coll=coll),
                              (pp[0] + uv[0] * 0.75, pp[1] + uv[1] * 0.75, 2.1), rotz + 90))
            objs.append(place(geo.box('GATE_dw_hhead', 0.42, 0.3, 0.34, (0, 0, 0), M('iron'), coll=coll, bevel=0.04),
                              (pp[0] + uv[0] * 0.75, pp[1] + uv[1] * 0.75, 2.95), rotz + 90))
        else:
            objs.append(place(geo.cyl('GATE_el_body', 0.3, 0.45, 2.1, (0, 0, 1.75), M('limestone'), verts=10, coll=coll), pp, 0))
            objs.append(place(geo.sphere('GATE_el_head', 0.28, (pp[0], pp[1], 3.0), M('limestone'), seg=12, ring=8, coll=coll), pp, 0))
            bowpts = []
            for t in range(7):
                u = D(-70 + 140 * t / 6)
                bx = pp[0] + uv[0] * (math.cos(u) * 0.8 + 0.55)
                by = pp[1] + uv[1] * (math.cos(u) * 0.8 + 0.55)
                bz = 1.75 + math.sin(u) * 0.9
                bowpts.append((bx, by, bz))
            objs.append(geo.tube('GATE_el_bow', bowpts, 0.035, M('wood'), coll, res=3))
    # 白板墙（石板 + 石框）
    ww = (P[0] + uv[0] * 5.4, P[1] + uv[1] * 5.4)
    gf = []
    gf.append(geo.box('GATE_board', 4.8, 0.2, 1.9, (0, 0, 0), M('dark_stone'), coll=coll, bevel=0.02))
    for off, siz in [((0, 0, 2.35), (5.4, 0.3, 0.32)), ((0, 0, 0.8), (5.4, 0.3, 0.32)),
                     ((-2.6, 0, 1.6), (0.32, 0.3, 1.86)), ((2.6, 0, 1.6), (0.32, 0.3, 1.86))]:
        gf.append(geo.box('GATE_board_f', siz[0], siz[1], siz[2], (off[0], 0, off[2]), M('sandstone'), coll=coll, bevel=0.03))
    gfr = geo.join(gf, 'GATE_board_grp')
    objs.append(place(gfr, (ww[0], ww[1], 0.42), rotz))
    # 吊篮泊位
    lift = (P[0] + uv[0] * -4.8, P[1] + uv[1] * -4.8)
    for s in (-1, 1):
        lp = (lift[0] + uv[0] * 1.35 * s, lift[1] + uv[1] * 1.35 * s)
        objs.append(place(geo.box(f'GATE_lift_post{s}', 0.32, 0.32, 6.2, (0, 0, 0), M('wood_dark'), coll=coll, bevel=0.03), lp, 0))
    objs.append(place(geo.box('GATE_lift_beam', 3.6, 0.4, 0.35, (0, 0, 6.15), M('wood'), coll=coll, bevel=0.03), lift, rotz))
    objs.append(place(geo.torus('GATE_pulley', 0.28, 0.08, (0, 0, 0), M('iron'), rot=(90, 0, 0), coll=coll, segs=16, minor=6),
                      (lift[0], lift[1], 5.8), 0))
    objs.append(geo.lathe('GATE_basket', [(0.9, 0), (1.0, 0.2), (1.05, 0.5), (1.05, 0.7), (0.95, 0.85)],
                          14, M('wood_dark'), (lift[0], lift[1], 3.5), coll, close_bottom=True))
    objs.append(place(geo.torus('GATE_basket_rim', 1.02, 0.06, (0, 0, 0), M('rope'), coll=coll, segs=18, minor=6),
                      (lift[0], lift[1], 4.35), 0))
    for s in (-1, 1):
        rp = [(lift[0] + uv[0] * 1.35 * s, lift[1] + uv[1] * 1.35 * s, 6.0),
              (lift[0] + uv[0] * 0.95 * s, lift[1] + uv[1] * 0.95 * s, 4.4),
              (lift[0] + uv[0] * 0.8 * s, lift[1] + uv[1] * 0.8 * s, 3.6)]
        objs.append(geo.tube(f'GATE_rope{s}', rp, 0.035, M('rope'), coll, res=3))
    return objs

# ================================================================ 钟楼
def build_belltower(coll):
    objs = []
    A = -64.0
    P = dirp(A, 25.0)
    rotz = A + 90
    objs.append(place(geo.box('BLT_base', 4.6, 4.6, 3.0, (0, 0, 1.5), M('mountain_rock'), coll=coll, bevel=0.07), P, rotz))
    objs.append(place(geo.box('BLT_mid', 3.7, 3.7, 2.7, (0, 0, 4.35), M('sandstone'), coll=coll, bevel=0.06), P, rotz))
    objs.append(place(geo.box('BLT_belfry', 3.1, 3.1, 2.5, (0, 0, 7.05), M('sandstone'), coll=coll, bevel=0.05), P, rotz))
    for i in range(4):
        a = 90 * i + 45
        p0 = dirp(a, 1.62)
        objs.append(place(geo.box(f'BLT_arch{i}', 1.1, 0.1, 1.5, (0, 0, 0), M('dark_stone'), coll=coll),
                          (P[0] + p0[0], P[1] + p0[1], 7.5), a))
        objs.append(place(geo.arch_top(f'BLT_archt{i}', 1.2, 6.8, (0, 0, 0), M('limestone'), coll=coll, n=5),
                          (P[0] + p0[0], P[1] + p0[1], 0.55), a))
    objs.append(place(geo.cyl('BLT_bell', 0.5, 0.26, 0.7, (0, 0, 0), M('iron'), verts=12, coll=coll),
                      (P[0], P[1], 8.3), 180))
    objs.append(place(geo.sphere('BLT_bell_knob', 0.17, (P[0], P[1], 8.95), M('iron'), seg=10, ring=8, coll=coll), P, 0))
    objs.append(place(geo.pyr('BLT_top', 4.3, 4.3, 1.5, (0, 0, 9.1), M('copperverde'), coll=coll), P, rotz))
    for s in (-1, 1):
        for t in (-1, 1):
            cp = (P[0] + math.cos(D(rotz + 90)) * 1.75 * s + math.cos(D(rotz)) * 1.75 * t,
                  P[1] + math.sin(D(rotz + 90)) * 1.75 * s + math.sin(D(rotz)) * 1.75 * t)
            objs.append(place(geo.pyr(f'BLT_c{s}{t}', 1.0, 1.0, 0.95, (0, 0, 9.35), M('copperverde'), coll=coll), cp, 0))
    objs.append(place(geo.cyl('BLT_spire', 0.055, 0.18, 1.6, (0, 0, 10.3), M('gold'), verts=8, coll=coll), P, 0))
    dr = (P[0] + math.cos(D(A - 90)) * 1.95, P[1] + math.sin(D(A - 90)) * 1.95)
    objs.append(place(geo.cyl('BLT_drum', 0.45, 0.45, 0.18, (0, 0, 0), M('wood'), rot=(90, 0, 0), verts=14, coll=coll),
                      (dr[0], dr[1], 2.3), 0))
    objs.append(place(geo.cyl('BLT_glow', 0.7, 0.7, 0.5, (0, 0, 0), M('glass_warm'), verts=12, coll=coll),
                      (P[0], P[1], 7.4), 0))
    return objs

# ================================================================ 浮池
def build_pool(coll):
    objs = []
    A = 40.0
    P = dirp(A, 25.2)
    prof = [(4.8, -1.35), (6.0, -0.95), (6.75, -0.42), (6.95, 0.2), (6.95, 0.58),
            (6.8, 0.86), (6.4, 0.94), (5.9, 0.94), (5.85, 0.4), (5.7, -0.25),
            (5.15, -0.95), (4.6, -1.3)]
    objs.append(geo.lathe('POOL_bowl', prof, 40, M('sandstone'), (P[0], P[1], 0.35), coll, noise=0.008, seed=5))
    objs.append(place(geo.cyl('POOL_water', 5.82, 5.82, 0.08, (0, 0, 0), M('water'), verts=32, coll=coll),
                      (P[0], P[1], 0.35 + 0.87), 0))
    for i in range(14):
        a = i * 360 / 14 + 6
        if math.cos(D(a - A)) < -0.15:
            pp = (P[0] + math.cos(D(a)) * 7.7, P[1] + math.sin(D(a)) * 7.7)
            objs.append(place(geo.box(f'POOL_seat{i}', 0.62, 0.4, 0.4, (0, 0, 0.1), M('limestone'), coll=coll, bevel=0.03),
                              (pp[0], pp[1], 0.2), a + 90))
    sup = (P[0] + math.cos(D(A + 180)) * 5.0, P[1] + math.sin(D(A + 180)) * 5.0)
    objs.append(place(geo.box('POOL_support', 4.2, 5.5, 1.5, (0, 0, -0.4), M('basalt'), coll=coll, bevel=0.1), sup, A + 90))
    objs.append(place(geo.box('POOL_support2', 2.6, 4.0, 1.2, (0, 0, -1.1), M('basalt'), coll=coll, bevel=0.1),
                      (sup[0] + math.cos(D(A)) * 1.8, sup[1] + math.sin(D(A)) * 1.8, 0), A + 90))
    objs.append(place(geo.box('POOL_table', 1.4, 0.8, 0.5, (0, 0, 0.25), M('cobble'), coll=coll, bevel=0.03),
                      (P[0] + math.cos(D(A + 180)) * 8.8, P[1] + math.sin(D(A + 180)) * 8.8, 0), A + 90))
    return objs

# ================================================================ 植被 / 灯具 / 浮岩
def build_props(coll):
    objs = []
    for i, (a, s) in enumerate([(-149, 31), (-128, 32), (-108, 33), (-88, 34),
                                (155, 35), (172, 36), (196, 37), (-166, 38)]):
        pp = dirp(a, 17.2 + (i % 2) * 1.5)
        objs.append(geo.tree(f'PRP_road{i}', (pp[0], pp[1], 0.12), 5.2, 1.9, M('foliage'), M('trunk'), coll, seed=s))
    for i in range(9):
        a = 15 + i * 40
        p = dirp(a, 19.7)
        objs.append(geo.tree(f'PRP_dorm{i}', (p[0], p[1], 0.1), 3.6, 1.5, M('foliage_light'), M('trunk'), coll, seed=40 + i))
    for i, a in enumerate([132, 141, 96, 105]):
        p = dirp(a, 23.8)
        objs.append(geo.tree(f'PRP_cliff{i}', (p[0], p[1], 0.1), 4.4, 1.8, M('foliage'), M('trunk'), coll, seed=50 + i, bend=10))
    for i, a in enumerate([250, 285, 300]):
        p = dirp(a, 17.5 + i)
        objs.append(geo.tree(f'PRP_misc{i}', (p[0], p[1], 0.1), 4.8, 1.8, M('foliage'), M('trunk'), coll, seed=60 + i))
    def near_building(a, r):
        for ca in (8, 182, -98, 112, 215):
            da = abs(((a - ca + 180) % 360) - 180)
            if 16 <= r <= 25 and da < 22:
                return True
        return False
    for i in range(42):
        a = random.uniform(0, 360)
        r = random.uniform(15.5, 28.0)
        if near_building(a, r):
            continue
        p = dirp(a, r)
        objs.append(geo.shrub(f'PRP_shrub{i}', (p[0], p[1], 0.18), random.uniform(0.5, 1.0),
                              M('foliage_light'), coll, seed=i, scale=(1, 1, 0.75)))
    lamp_spots = [dirp(-149, 14.2), dirp(-111, 11.8), dirp(-73, 10.2), dirp(-38, 20.6),
                  dirp(0, 12.6), dirp(8, 14.8), dirp(50, 18.0), dirp(90, 16.6),
                  dirp(122, 16.4), dirp(155, 18.2), dirp(188, 16.6), dirp(218, 11.4),
                  dirp(252, 12.0), dirp(298, 15.4)]
    for i, p in enumerate(lamp_spots):
        objs.append(place(geo.lantern(f'PRP_lamp{i}', (0, 0, 0), M('limestone'), M('lantern'), coll=coll, h=1.6),
                          (p[0], p[1], 0.06), 0))
    for i in range(56):
        zone = random.choice(['gold', 'white', 'blue'] * 3 + ['purple'])
        a = random.uniform(0, 360)
        r = random.uniform(15, 28)
        near_tide = abs(((a - 112 + 180) % 360) - 180) < 14
        if zone == 'purple' and not near_tide:
            continue
        if near_tide and zone != 'purple':
            continue
        if near_building(a, r):
            continue
        p = dirp(a, r)
        mm = {'gold': 'flower_gold', 'white': 'flower_white', 'blue': 'flower_blue', 'purple': 'flower_purple'}[zone]
        objs.append(place(geo.ico(f'PRP_flower{i}', 0.13, (0, 0, 0), M(mm), sub=1, coll=coll, scale=(1, 1, 0.8)),
                          (p[0], p[1], 0.12), 0))
    for i in range(12):
        a = random.uniform(0, 360)
        r = random.uniform(32.5, 43)
        y = random.uniform(-2.5, -8.5)
        p = dirp(a, r)
        objs.append(place(geo.rock(f'PRP_float{i}', (0, 0, 0), random.uniform(0.8, 2.1), M('basalt'), coll, seed=90 + i,
                                   scale=(1, 1, random.uniform(0.55, 0.8))),
                          (p[0], p[1], y), random.uniform(0, 360)))
    # 名士墓（西缘小簇）
    for i in range(7):
        a = 198 + i * 5.5
        p = dirp(a, 25.5)
        objs.append(place(geo.box(f'PRP_grave{i}', 0.55, 0.22, 0.8, (0, 0, 0), M('limestone'), coll=coll, bevel=0.02),
                          (p[0], p[1], 0.35), a + 90 + random.uniform(-6, 6)))
        objs.append(geo.shrub(f'PRP_gravesh{i}', (p[0] + 0.5, p[1], 0.1), 0.3, M('foliage'), coll, seed=200 + i))

    # —— 生活痕迹（散点小物，弱化摆件感） ——
    def spot(zone_a, rr, dist_r=0):
        a = zone_a + random.uniform(-12, 12) * 0.9
        p = dirp(a, rr + random.uniform(-dist_r, dist_r))
        return p
    for i in range(8):
        p = spot(random.choice([8, 182, -98, 112]), 17.6, 1.4)
        objs.append(place(geo.box(f'PRP_crate{i}', 0.55, 0.45, 0.42, (0, 0, 0.21), M('wood_dark'), coll=coll, bevel=0.02),
                          (p[0], p[1], 0.1), random.uniform(0, 90)))
    for i in range(5):
        p = spot(215, 17.0, 2.0)
        objs.append(place(geo.cyl(f'PRP_jar{i}', 0.26, 0.3, 0.5, (0, 0, 0.25), M('plaza_mid'), verts=12, coll=coll),
                          (p[0], p[1], 0.1), 0))
    for i in range(4):
        p = spot(30, 20.5, 1.2)
        objs.append(place(geo.cyl(f'PRP_wash{i}', 0.34, 0.3, 0.36, (0, 0, 0.18), M('water'), verts=14, coll=coll),
                          (p[0], p[1], 0.1), 0))
    for i in range(3):
        p = spot(150, 18.0, 1.5)
        for s in (-1, 1):
            objs.append(place(geo.cyl(f'PRP_clothe{i}{s}', 0.035, 0.035, 1.7, (0, 0, 0.85), M('wood'), verts=6, coll=coll),
                              (p[0] + s * 0.65, p[1], 0.1), 0))
        objs.append(place(geo.box(f'PRP_line{i}', 1.5, 0.04, 0.04, (0, 0, 1.72), M('rope'), coll=coll),
                          (p[0], p[1], 0), 0))
        for k in range(3):
            objs.append(place(geo.box(f'PRP_cloth{i}{k}', 0.3, 0.05, 0.42, (0, 0, 0), M('cloth_white' if k % 2 else 'cloth_tide'), coll=coll),
                              (p[0] - 0.4 + k * 0.4, p[1], 1.5), 0))
    for i in range(6):
        p = spot(random.choice([-38, 160, 220]), 16.8, 1.6)
        objs.append(place(geo.box(f'PRP_bench{i}', 1.7, 0.42, 0.13, (0, 0, 0.42), M('wood'), coll=coll, bevel=0.03),
                          (p[0], p[1], 0), random.uniform(0, 360)))
        objs.append(place(geo.box(f'PRP_benchleg{i}', 0.3, 0.34, 0.4, (0, 0, 0.2), M('wood_dark'), coll=coll),
                          (p[0], p[1], 0), random.uniform(0, 360)))
    return objs


# ================================================================ 总装
ZONES = [
    ('island', build_island, 'ISC'),
    ('tower', build_tower, 'TWR'),
    ('plaza', build_plaza, 'PLZ'),
    ('cloister_dawn', lambda c: build_cloister(c, 8, 'tile_dawn', 'CLD'), 'CLD'),
    ('cloister_speak', lambda c: build_cloister(c, 182, 'tile_speak', 'CLS'), 'CLS'),
    ('cloister_forge', lambda c: build_cloister(c, -98, 'tile_forge', 'CLF'), 'CLF'),
    ('cloister_tide', lambda c: build_cloister(c, 112, 'tile_tide', 'CLT'), 'CLT'),
    ('college_dawn', build_dawn, 'DAW'),
    ('college_speak', build_speak, 'SPK'),
    ('college_forge', build_forge, 'FRG'),
    ('college_tide', build_tide, 'TID'),
    ('library', build_library, 'LIB'),
    ('dorms', build_dorms, 'DRM'),
    ('gate', build_gate, 'GATE'),
    ('belltower', build_belltower, 'BLT'),
    ('pool', build_pool, 'POOL'),
    ('props', build_props, 'PRP'),
]

def assemble():
    """构建全部，返回 {zone: joined_object}。前提：场景已重置（read_factory_settings 由调用方执行）。"""
    scn = bpy.context.scene
    coll = bpy.data.collections.new('ACADEMY')
    scn.collection.children.link(coll)
    out = {}
    for zname, fn, prefix in ZONES:
        objs = fn(coll)
        j = geo.join(objs, f'AC_{zname}')
        if j is not None:
            out[zname] = j
    return out
