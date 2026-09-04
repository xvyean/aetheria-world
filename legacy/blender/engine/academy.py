# -*- coding: utf-8 -*-
"""星槎学院 · 建筑群
星陨塔 / 星穗馆 / 四院回廊与院门 / 宿舍环 / 星图广场 /
浮池 / 浮岩孤灯 / 星槎舟与码头 / 悬梯与接引台 / 旗与灯绳 / 植被
"""
import math
from mathutils import Vector
from helpers import (B, MAT, vnoise, fbm, clamp, smoothstep, lerp, srand,
                     TAU, PI, catenary, make_curve)

TOP = 240.0          # 岛顶（与 island.py 一致）
RNG = srand(2026)

MATS_ORDER = None    # 由 build() 指定

HOUSES = {
    'dawn':  dict(color='h_dawn',  glow='glow_h_dawn', banner='banner_dawn',
                  dir=(1, 0),  gate=(72, 0),   rotz=-90 * PI / 180, name='晨辉院'),
    'speak': dict(color='h_speak', glow='glow_h_speak', banner='banner_speak',
                  dir=(0, -1), gate=(0, -46),  rotz=180 * PI / 180, name='星语院'),
    'forge': dict(color='h_forge', glow='glow_h_forge', banner='banner_forge',
                  dir=(-1, 0), gate=(-40, 0),  rotz=90 * PI / 180, name='锤音院'),
    'tide':  dict(color='h_tide',  glow='glow_h_tide',  banner='banner_tide',
                  dir=(0, 1),  gate=(0, 46),   rotz=0.0, name='海心院'),
}


# ================================================================ 星陨塔
def build_tower(M):
    b = B('tower', [M['stone_cream'], M['stone_light'], M['stone_dark'],
                    M['gold'], M['glow_warm'], M['glow_win'], M['crystal_core'], M['crystal'],
                    M['magic_moss'], M['h_dawn'], M['h_speak'], M['h_forge'], M['h_tide'],
                    M['glass_warm'], M['marble']])
    z0 = TOP - 1.5
    SEG = 8
    # 基座
    b.cyl(13.5, 13.5, 4.0, SEG, MAT((0, 0, z0 + 2.0), (0, 0, PI / SEG)), 'stone_dark')
    b.cyl(11.8, 11.8, 5.5, SEG, MAT((0, 0, z0 + 4.8), (0, 0, PI / SEG)), 'stone_light')
    # 台阶（四向）
    for k in range(4):
        ang = k * PI / 2 + PI / 4
        for st in range(3):
            w = 7.0 + st * 2.2
            b.box((w, 2.2, 0.3), MAT((math.cos(ang) * (11.5 + st * 1.1),
                                    math.sin(ang) * (11.5 + st * 1.1), TOP + 0.15 + st * 0.0),
                                   (0, 0, ang + PI / 2)), 'marble')
    # 窗（发光 · 拱窗框）：先置石材框，再把发光芯凸出
    def windows(radius, z, n, w, h, color='glow_win'):
        for i in range(n):
            a = i * TAU / n + PI / SEG
            x, y = math.cos(a) * radius, math.sin(a) * radius
            # 石框横档（上下）
            for sy in (h / 2 + 0.25, -h / 2 - 0.25):
                b.box((w + 1.2, 0.9, 0.4), MAT((x, y, z + sy), (0, 0, a + PI / 2)), 'stone_light')
            # 竖框（左右）
            bx, by = math.cos(a + PI / 2), math.sin(a + PI / 2)
            for s2 in (-1, 1):
                ox, oy = x + bx * s2 * (w / 2 + 0.45), y + by * s2 * (w / 2 + 0.45)
                b.box((0.5, 0.9, h + 0.9), MAT((ox, oy, z), (0, 0, a + PI / 2)), 'stone_light')
            # 发光内芯（凸出框外 0.15）
            b.box((w, 0.95, h), MAT((x, y, z), (0, 0, a + PI / 2)), color)
            # 上拱（半圆发光）
            b.cyl(w * 0.5, w * 0.5, 0.85, 12, MAT((x * 1.0, y * 1.0, z + h / 2 + 0.1),
                                                  (PI / 2, 0, a + PI / 2)), color)
            # 窗台
            b.box((w + 1.2, 1.0, 0.35), MAT((x * 1.02, y * 1.02, z - h / 2 - 0.45),
                                            (0, 0, a + PI / 2)), 'stone_light')
    # 一层鼓身
    b.cyl(9.0, 9.0, 15.0, SEG, MAT((0, 0, z0 + 13.0), (0, 0, PI / SEG)), 'stone_cream')
    windows(9.15, z0 + 13.5, 8, 2.6, 5.0)
    # 四院圆徽（塔基四向）
    for k, hk in enumerate(['h_dawn', 'h_speak', 'h_forge', 'h_tide']):
        a = k * PI / 2
        x, y = math.cos(a) * 10.3, math.sin(a) * 10.3
        b.cyl(1.15, 1.15, 0.5, 24, MAT((x, y, z0 + 8.2), (PI / 2, 0, a + PI)), M[hk])
    # 檐环与过渡
    b.cyl(10.1, 10.1, 1.1, SEG, MAT((0, 0, z0 + 21.0), (0, 0, PI / SEG)), 'gold')
    b.cyl(9.9, 7.8, 2.2, SEG, MAT((0, 0, z0 + 22.6), (0, 0, PI / SEG)), 'stone_light')
    # 二层
    b.cyl(7.8, 7.8, 12.0, SEG, MAT((0, 0, z0 + 29.7), (0, 0, PI / SEG)), 'stone_cream')
    windows(7.9, z0 + 30.0, 8, 2.2, 4.0)
    b.cyl(8.8, 8.8, 1.0, SEG, MAT((0, 0, z0 + 36.2), (0, 0, PI / SEG)), 'gold')
    b.cyl(8.6, 6.4, 2.0, SEG, MAT((0, 0, z0 + 37.7), (0, 0, PI / SEG)), 'stone_light')
    # 三层
    b.cyl(6.4, 6.4, 10.0, SEG, MAT((0, 0, z0 + 43.7), (0, 0, PI / SEG)), 'stone_cream')
    windows(6.5, z0 + 44.0, 8, 1.8, 3.2)
    b.cyl(7.2, 7.2, 0.9, SEG, MAT((0, 0, z0 + 49.2), (0, 0, PI / SEG)), 'gold')
    b.cyl(7.0, 5.2, 1.8, SEG, MAT((0, 0, z0 + 50.6), (0, 0, PI / SEG)), 'stone_light')
    # 尖锥
    b.cyl(5.4, 0.35, 24.0, SEG, MAT((0, 0, z0 + 63.6), (0, 0, PI / SEG)), 'stone_light')
    b.cyl(5.7, 5.7, 0.9, SEG, MAT((0, 0, z0 + 52.6), (0, 0, PI / SEG)), 'gold')
    b.cyl(0.7, 0.7, 2.2, SEG, MAT((0, 0, z0 + 76.4)), 'gold')
    b.cyl(1.15, 0.0, 1.4, 4, MAT((0, 0, z0 + 78.2)), 'gold')
    # 苔环（发光苔藓）
    b.cyl(9.35, 9.35, 0.55, SEG, MAT((0, 0, z0 + 6.2), (0, 0, PI / SEG)), 'magic_moss')
    for i in range(6):
        a = RNG.uniform(0, TAU)
        b.box((1.6, 0.9, 0.9), MAT((math.cos(a) * 9.3, math.sin(a) * 9.3, z0 + 8.6),
                                 (0, 0, a)), 'magic_moss')
    # 裂隙晶（悬浮 · 放大醒目）
    cz = z0 + 86.0
    b.cyl(3.6, 0.08, 9.0, 4, MAT((0, 0, cz + 4.5), (0, 0, PI / 4)), 'crystal_core')
    b.cyl(3.6, 0.08, 9.0, 4, MAT((0, 0, cz - 4.5), (PI, 0, PI / 4)), 'crystal_core')
    b.cyl(2.3, 0.06, 5.6, 4, MAT((0, 0, cz + 2.4), (0, 0.5, PI / 4)), 'crystal')
    for (dx, dy, s, dz) in [(5.0, 0, 1.2, 2.0), (-4.2, 3.0, 0.9, -1.0),
                            (-2.4, -4.4, 0.7, 3.4), (3.0, 4.4, 0.65, 5.2),
                            (-5.4, -2.2, 0.6, 1.2), (4.6, -3.4, 0.5, -2.4)]:
        b.cyl(s * 1.6, 0.05, s * 3.9, 4, MAT((dx, dy, cz + dz), (0.3, RNG.uniform(-0.5, 0.5), 0.4)),
              'crystal' if s < 0.8 else 'crystal_core')
    # 悬浮光环（冰晶环）
    b.torus(5.6, 0.14, 40, 8, MAT((0, 0, cz + 1.0), (0.35, 0.25, 0)), 'crystal')
    b.torus(7.2, 0.10, 44, 8, MAT((0, 0, cz - 2.6), (-0.28, 0.4, 0)), 'crystal')
    return b


# ================================================================ 星穗馆
def build_library(M):
    b = B('library', [M['stone_cream'], M['gold'], M['brass'], M['glow_warm'],
                      M['glow_win'], M['stone_dark'], M['marble'], M['glass_warm']])
    cx, cy = 46.0, -36.0
    # 朝向广场
    ang = math.atan2(0 - cy, 0 - cx)
    rz = ang - 112.5 * PI / 180
    pcx, pcy, rz = cx, cy, rz
    base = B('library_base', [M['stone_cream'], M['gold'], M['brass'], M['glow_warm'],
                              M['glow_win'], M['marble'], M['stone_dark'], M['glass_warm']])
    # 底盘
    base.cyl(15.2, 15.2, 1.4, 8, MAT((pcx, pcy, TOP - 0.8), (0, 0, PI / 8 + rz)), 'stone_dark')
    radii = [14.0, 12.8, 11.6, 10.4, 9.2, 8.0, 6.8]
    z = TOP + 0.7
    z0 = TOP + 0.7
    for i, r in enumerate(radii):
        h = 4.0 if i < 6 else 3.6
        base.cyl(r, r, h, 8, MAT((pcx, pcy, z + h / 2), (0, 0, PI / 8 + rz)), 'stone_cream')
        # 环窗
        n_win = 10
        for k in range(n_win):
            a = k * TAU / n_win + PI / 8 + rz
            x, y = pcx + math.cos(a) * (r + 0.12), pcy + math.sin(a) * (r + 0.12)
            base.box((1.0, 0.5, 2.4), MAT((x, y, z + h * 0.55), (0, 0, a + PI / 2)),
                     'glow_win')
            base.box((1.3, 0.32, 0.35), MAT((x, y, z + h * 0.55 + 1.3), (0, 0, a + PI / 2)), 'gold')
        base.cyl(r + 0.75, r + 0.75, 0.42, 8, MAT((pcx, pcy, z + h + 0.2), (0, 0, PI / 8 + rz)), 'gold')
        z += h + 0.4
    # 金穹（暗金，防过曝）
    base.uvsph(5.4, MAT((pcx, pcy, z + 0.2), (0, 0, rz), (1.25, 1.25, 1.0)), 'brass', u=24, v=12)
    base.cyl(0.5, 0.5, 2.0, 8, MAT((pcx, pcy, z + 5.6)), 'brass')
    base.uvsph(0.8, MAT((pcx, pcy, z + 6.8)), 'glow_warm', u=12, v=8)
    # 楼身金饰带（环层）
    for i, r in enumerate(radii):
        base.cyl(r + 0.2, r + 0.2, 0.25, 8, MAT((pcx, pcy, z0 + 1.0 + i * 4.4), (0, 0, PI / 8 + rz)), 'brass')
    # 入口
    fx, fy = pcx + math.cos(ang) * 15.0, pcy + math.sin(ang) * 15.0
    for st in range(3):
        w = 6.5 - st * 0.0
        base.box((w, 1.2, 0.35), MAT((fx + math.cos(ang) * (1.4 + st * 1.0),
                                    fy + math.sin(ang) * (1.4 + st * 1.0),
                                    TOP + 0.2 + st * 0.35 + (3 - st) * 0.0), (0, 0, ang + PI / 2)),
                 'marble')
    base.box((3.4, 0.5, 4.6), MAT((pcx + math.cos(ang) * 14.62, pcy + math.sin(ang) * 14.62,
                                 TOP + 3.0), (0, 0, ang + PI / 2)), 'stone_dark')
    base.box((4.0, 0.6, 0.7), MAT((pcx + math.cos(ang) * 14.6, pcy + math.sin(ang) * 14.6,
                                 TOP + 5.6), (0, 0, ang + PI / 2)), 'gold')
    return base


# ================================================================ 院门
def build_gate(M, key):
    h = HOUSES[key]
    gx, gy = h['gate']
    rz = h['rotz']
    b = B(f'gate_{key}', [M['stone_light'], M['stone_cream'], M['stone_dark'],
                          M[h['color']], M[h['glow']], M[h['banner']], M['gold'],
                          M['roof_slate']])
    mm = MAT((gx, gy, 0), (0, 0, rz))
    # 台基
    b.box((13, 9.5, 1.6), mm @ MAT((0, 0, TOP - 0.8)), 'stone_dark')
    # 拱门墙（局部 -Y 为朝向广场方向）
    b.arch_wall(11.0, 8.6, 4.0, 2.4, 10, mm @ MAT((0, 0, TOP + 1.2)), 'stone_light')
    # 檐与顶
    b.box((12.4, 5.2, 0.8), mm @ MAT((0, 0, TOP + 10.2)), 'stone_cream')
    b.box((12.4, 5.6, 0.8), mm @ MAT((0, 0, TOP + 10.9)), M[h['color']])
    # 山墙
    b.prism_xz([(-6.2, 0), (6.2, 0), (0, 3.4)], 5.4, mm @ MAT((0, 0, TOP + 11.3)), 'roof_slate')
    b.box((0.5, 5.6, 0.5), mm @ MAT((0, 0, TOP + 14.8)), M[h['color']])
    # 拱楣色带 + 钥匙石
    b.box((4.4, 4.2, 0.5), mm @ MAT((0, 0, TOP + 4.4)), M[h['color']])
    # 角塔 ×2
    for sx in (-1, 1):
        tx = sx * 7.4
        b.cyl(1.5, 1.5, 8.0, 12, mm @ MAT((tx, 0, TOP + 5.4)), 'stone_light')
        b.cyl(1.9, 1.9, 0.7, 12, mm @ MAT((tx, 0, TOP + 9.6)), M[h['color']])
        b.cyl(1.7, 0.0, 3.2, 12, mm @ MAT((tx, 0, TOP + 11.6)), 'roof_slate')
        b.cyl(0.09, 0.09, 2.6, 6, mm @ MAT((tx, 0, TOP + 14.4)), 'gold')
        b.box((1.25, 0.05, 1.9), mm @ MAT((tx, 0.45, TOP + 13.2),), M[h['banner']])
        b.uvsph(0.3, mm @ MAT((tx, 0, TOP + 10.4)), M[h['glow']], u=10, v=8)
    # 门侧灯
    b.uvsph(0.34, mm @ MAT((0, -3.1, TOP + 6.2)), M[h['glow']], u=10, v=8)
    # 门前台阶
    for st in range(3):
        b.box((6.0, 1.0, 0.3), mm @ MAT((0, -3.6 - st * 0.9, TOP + 0.35 + (2 - st) * 0.3)), 'stone_dark')
    # 旗（两侧）
    for sx in (-1, 1):
        b.cyl(0.08, 0.08, 6.4, 6, mm @ MAT((sx * 9.3, -0.6, TOP + 13.0)), 'gold')
        b.box((0.06, 1.3, 4.4), mm @ MAT((sx * 9.3 + 0.7, -0.6, TOP + 12.2),
                                       (0, 0, PI / 2)), M[h['banner']])
    return b


# ================================================================ 回廊
def build_cloister(M, key):
    h = HOUSES[key]
    b = B(f'cloister_{key}', [M['stone_light'], M['stone_cream'], M['paving'],
                              M[h['color']], M[h['glow']], M['gold']])
    gx, gy = h['gate']
    dx, dy = h['dir']
    dist = math.hypot(gx, gy) - 27.0
    if dist < 8:
        dist = 8.0
    n = 8
    bay = dist / n
    at = math.atan2(dy, dx)
    ox, oy = dx * 27.0, dy * 27.0
    mm = MAT((ox, oy, 0), (0, 0, at))
    # 地面板
    b.box((dist + 2.0, 5.4, 0.5), mm @ MAT((dist / 2, 0, TOP + 0.1)), 'paving')
    # 立柱与拱
    for i in range(n + 1):
        x = i * bay
        if i == 0 or i == n:
            b.box((1.7, 1.7, 5.2), mm @ MAT((x, -2.2, TOP + 3.0)), 'stone_cream')
            b.box((1.7, 1.7, 5.2), mm @ MAT((x, 2.2, TOP + 3.0)), 'stone_cream')
        else:
            b.cyl(0.42, 0.48, 4.0, 10, mm @ MAT((x, -2.2, TOP + 2.6)), 'stone_light')
            b.cyl(0.42, 0.48, 4.0, 10, mm @ MAT((x, 2.2, TOP + 2.6)), 'stone_light')
        # 柱础与柱头
        for sy in (-2.2, 2.2):
            b.box((1.0, 1.0, 0.5), mm @ MAT((x, sy, TOP + 0.65)), 'stone_light')
            b.box((0.9, 0.9, 0.4), mm @ MAT((x, sy, TOP + 4.7)), 'stone_light')
    # 拱（分段）
    for i in range(n):
        x = i * bay + bay / 2
        r = bay / 2
        for k in range(8):
            a = k * PI / 8
            seg = MAT((x + math.cos(a) * r * 0.5, 0, TOP + 4.9 + math.sin(a) * r * 0.4),
                    (PI / 2, 0, at), (bay * 0.56, 0.42, 0.55))
            b.box((1, 1, 1), mm @ seg, 'stone_cream')
    # 廊顶与屋脊色带
    b.box((dist + 2.4, 6.0, 0.55), mm @ MAT((dist / 2, 0, TOP + 6.7)), 'stone_light')
    b.box((dist + 2.4, 1.0, 0.5), mm @ MAT((dist / 2, 0, TOP + 7.2)), M[h['color']])
    # 外侧矮栏
    for sx in (-1, 1):
        b.box((dist, 0.4, 0.9), mm @ MAT((dist / 2, sx * 2.9, TOP + 0.95)), 'stone_light')
    # 每跨琉璃灯
    for i in range(n):
        x = i * bay + bay / 2
        b.cyl(0.07, 0.07, 0.9, 6, mm @ MAT((x, 0, TOP + 4.9)), 'gold')
        b.uvsph(0.3, mm @ MAT((x, 0, TOP + 6.1)), M[h['glow']], u=10, v=8)
    return b


# ================================================================ 宿舍环
def build_dorms(M):
    b = B('dorms', [M['stone_cream'], M['roof_slate'], M['glow_warm'],
                    M['h_dawn'], M['h_speak'], M['h_forge'], M['h_tide'],
                    M['wood'], M['glow_lamp'], M['stone_dark']])
    ang_h = {'dawn': 'h_dawn', 'speak': 'h_speak', 'forge': 'h_forge', 'tide': 'h_tide'}
    for i in range(12):
        a = (i * 30 + 15) * PI / 180
        r = 36.0
        x, y = math.cos(a) * r, math.sin(a) * r
        # 归属院色：按方位
        deg = (i * 30 + 15) % 360
        hk = 'dawn' if deg < 45 or deg >= 315 else (
            'tide' if deg < 135 else ('speak' if deg < 225 else 'forge'))
        col = ang_h[hk]
        mm = MAT((x, y, 0), (0, 0, a + PI / 2))   # 面朝环心
        b.box((7.2, 5.2, 5.4), mm @ MAT((0, 0, TOP + 2.2)), 'stone_cream')
        b.box((0.9, 1.0, 4.2), mm @ MAT((0, -2.7, TOP + 3.0)), M[col])      # 门前色带
        b.box((7.8, 5.8, 1.1), mm @ MAT((0, 0, TOP + 5.4)), 'stone_dark')   # 檐板
        b.prism_xz([(-4.1, 0), (4.1, 0), (0, 2.2)], 6.0, mm @ MAT((0, 0, TOP + 5.9)), 'roof_slate')
        b.box((0.4, 6.2, 0.4), mm @ MAT((0, 0, TOP + 8.1)), M[col])        # 脊色
        b.box((0.9, 0.9, 1.8), mm @ MAT((2.2, 0, TOP + 7.6)), 'stone_dark')  # 烟囱
        # 门与窗
        b.box((1.1, 0.25, 2.2), mm @ MAT((0, -2.62, TOP + 1.3)), 'wood')
        for sx in (-1, 1):
            b.box((1.0, 0.3, 1.5), mm @ MAT((sx * 2.3, -2.66, TOP + 3.1)), 'glow_warm')
        b.uvsph(0.24, mm @ MAT((0, -2.7, TOP + 2.9)), 'glow_lamp', u=10, v=8)
    return b


# ================================================================ 星图广场
def build_plaza(M):
    b = B('plaza', [M['paving'], M['stone_dark'], M['gold'], M['glow_warm'],
                    M['marble'], M['stone_light']])
    b.cyl(27.0, 27.0, 0.8, 32, MAT((0, 0, TOP - 0.3)), 'paving')
    b.cyl(27.6, 27.6, 0.5, 32, MAT((0, 0, TOP - 0.5)), 'stone_dark')
    # 外环石台缘
    b.torus(27.9, 0.7, 48, 8, MAT((0, 0, TOP + 0.35)), 'stone_light')
    # 八芒星镶嵌
    pts = []
    for i in range(16):
        a = i * TAU / 16 + PI / 16
        r = 9.5 if i % 2 == 0 else 3.6
        pts.append((math.cos(a) * r, math.sin(a) * r))
    b.prism_xz(pts, 0.3, MAT((0, 0, TOP + 0.12)), 'gold')
    b.cyl(1.6, 1.6, 0.35, 24, MAT((0, 0, TOP + 0.2)), 'glow_warm')
    # 内圈星图环（细金环嵌线）
    b.torus(17.0, 0.12, 48, 6, MAT((0, 0, TOP + 0.55)), 'gold')
    # 四向路 + 石缘
    for key in HOUSES:
        h = HOUSES[key]
        dx, dy = h['dir']
        gx, gy = h['gate']
        d = math.hypot(gx, gy)
        p0 = Vector((dx * 26.0, dy * 26.0, TOP + 0.85 + 0.01))
        p1 = Vector((dx * (d - 5.2), dy * (d - 5.2), TOP + 0.86))
        mid = Vector((dx * (26 + (d - 5.2 - 26) / 2), dy * (26 + (d - 5.2 - 26) / 2),
                      TOP + 0.86))
        b.ribbon([p0, mid, p1], [4.6, 4.6, 4.6], 'paving', smooth=False)
        # 路缘石
        n = Vector((-dy, dx))
        for s in (-1, 1):
            pA = Vector((dx * 26 + n.x * 2.55 * s, dy * 26 + n.y * 2.55 * s, TOP + 0.7))
            pB = Vector((dx * (d - 5.2) + n.x * 2.55 * s, dy * (d - 5.2) + n.y * 2.55 * s, TOP + 0.7))
            b.ribbon([pA, pB], [0.5, 0.5], 'stone_light', smooth=False)
    # 塔下四面立柱（灯柱）
    for k in range(4):
        a = k * PI / 2 + PI / 4
        x, y = math.cos(a) * 30.2, math.sin(a) * 30.2
        b.cyl(0.34, 0.34, 4.6, 8, MAT((x, y, TOP + 2.3)), 'stone_dark')
        b.uvsph(0.4, MAT((x, y, TOP + 5.1)), 'glow_warm', u=12, v=8)
    # 广场环灯（小灯柱 8 座）
    for k in range(8):
        a = k * TAU / 8 + PI / 8
        x, y = math.cos(a) * 24.0, math.sin(a) * 24.0
        b.cyl(0.22, 0.22, 2.6, 8, MAT((x, y, TOP + 1.3)), 'stone_dark')
        b.uvsph(0.3, MAT((x, y, TOP + 3.0)), 'glow_warm', u=10, v=8)
    return b


# ================================================================ 浮池
def build_pool(M):
    b = B('pool', [M['stone_light'], M['stone_cream'], M['water'],
                   M['glow_h_tide'], M['stone_dark'], M['rock'], M['glow_warm']])
    px, py = 0.0, 74.0
    pz = TOP - 0.5          # 池口与岛缘齐平
    tilt = 5 * PI / 180
    # 碗体（浅色石碗，沉入岛缘南侧）
    mm = MAT((px, py, pz), (tilt, 0, 0.0))
    b.uvsph(8.4, mm @ MAT((0, 0, -2.2), scale=(1.5, 1.0, 0.62)), 'stone_light', u=30, v=16)
    # 内壁
    b.cyl(7.6, 7.0, 1.6, 30, mm @ MAT((0, 0, -0.7)), 'stone_cream', caps=False)
    # 承水盘（发光水面）
    b.cyl(6.9, 6.9, 0.3, 30, mm @ MAT((0, 0, -1.5)), 'water')
    b.cyl(6.6, 6.6, 0.18, 30, mm @ MAT((0, 0, -1.1)), 'glow_h_tide')
    # 石缘
    b.torus(7.7, 0.65, 36, 10, mm @ MAT((0, 0, 0.4)), 'stone_cream')
    # 池底倒石笋（伸向下方虚空）
    for (dx, dy, L, r) in [(-2.8, 0.6, 11.0, 1.2), (2.0, -1.4, 8.0, 0.9),
                           (0.2, 2.4, 9.0, 0.8), (-1.0, -2.6, 6.0, 0.6)]:
        b.cyl(r, r * 0.2, L, 8, mm @ MAT((dx, dy, -6.8 - L / 2)), 'rock')
    # 与岛缘连接的桥面 + 石栏（低矮融入岛缘）
    b.box((4.6, 26.0, 1.2), MAT((0, 61.0, TOP - 0.6)), 'stone_light')
    for sx in (-1, 1):
        b.box((0.5, 26.0, 0.8), MAT((sx * 2.2, 61.0, TOP + 0.5)), 'stone_cream')
    # 桥面灯光
    b.uvsph(0.3, MAT((2.0, 66.0, TOP + 1.2)), 'glow_warm', u=10, v=8)
    b.uvsph(0.3, MAT((-2.0, 66.0, TOP + 1.2)), 'glow_warm', u=10, v=8)
    # 池边灯柱
    for (lx, ly) in [(6.2, 3.6), (-6.4, 2.2), (0.5, -6.8)]:
        b.cyl(0.18, 0.18, 2.8, 8, mm @ MAT((lx, ly, 1.6)), 'stone_dark')
        b.uvsph(0.32, mm @ MAT((lx, ly, 3.4)), 'glow_warm', u=10, v=8)
    return b


# ================================================================ 星槎舟与码头
def build_boat(M):
    b = B('boat', [M['wood'], M['wood_dark'], M['sail'], M['rope'], M['gold']])
    bx, by, bz = -68.0, 4.0, 204.0
    mm = MAT((bx, by, bz), (0, 0, 0.5))
    # 船体
    b.uvsph(6.0, mm @ MAT((0, 0, 0), scale=(2.6, 0.78, 0.62)), 'wood', u=28, v=14)
    b.cyl(2.4, 0.0, 3.4, 10, mm @ MAT((13.5, 0, 1.2), (0, PI / 2, 0)), 'wood')      # 船头
    b.cyl(2.0, 0.0, 2.8, 10, mm @ MAT((-13.0, 0, 0.8), (0, -PI / 2, 0)), 'wood')    # 船尾
    b.box((22.0, 3.6, 0.4), mm @ MAT((0, 0, 2.4)), 'wood_dark')
    # 桅与帆
    b.cyl(0.16, 0.12, 11.5, 8, mm @ MAT((-1.0, 0, 8.0)), 'wood_dark')
    b.cyl(0.12, 0.12, 4.6, 8, mm @ MAT((2.6, 0, 9.2), (0, PI / 2, 0)), 'wood_dark')
    b.prism_xz([(-0.1, 0.0), (5.2, 1.4), (5.0, 6.8), (-0.1, 7.4)], 0.12,
               mm @ MAT((0.6, 0, 2.6)), 'sail')
    b.prism_xz([(-0.05, 0.0), (3.0, 0.9), (2.9, 4.4), (-0.05, 4.9)], 0.1,
               mm @ MAT((3.4, -0.9, 5.4), (0, 0, 0.35)), 'sail')
    b.box((1.0, 0.05, 0.7), mm @ MAT((-0.9, 0.0, 13.9)), 'gold')
    # 系泊缆（连码头）
    b.cyl(0.05, 0.05, 18.0, 6, mm @ MAT((12.0, 2.0, 8.0), (0.5, 0.9, 0)), 'rope')
    # 码头
    dock = B('dock', [M['stone_light'], M['stone_dark'], M['glow_lamp']])
    dock.box((9.0, 6.0, 1.4), MAT((-54.0, 6.0, TOP - 2.2)), 'stone_light')
    dock.box((7.0, 4.4, 0.8), MAT((-55.5, 5.5, TOP - 0.6)), 'stone_dark')
    for i in range(3):
        dock.cyl(0.3, 0.3, 4.0, 8, MAT((-56.5 + i * 1.8, 8.2, TOP + 0.6)), 'stone_dark')
    dock.uvsph(0.4, MAT((-56.5, 8.2, TOP + 3.0)), 'glow_lamp', u=12, v=8)
    return b, dock


# ================================================================ 悬梯与接引台
def build_ladder(M):
    b = B('ladder', [M['rope'], M['wood'], M['glow_lamp'], M['rock']])
    lx, ly = -57.0, -19.0
    z_top = TOP - 2.0
    z_len = 62.0
    for sx in (-0.6, 0.6):
        b.cyl(0.06, 0.06, z_len, 6, MAT((lx + sx, ly, z_top - z_len / 2)), 'rope')
    for i in range(22):
        z = z_top - 2.2 - i * 2.6
        if z < z_top - z_len + 1:
            break
        b.box((1.5, 0.12, 0.12), MAT((lx, ly, z)), 'wood')
    # 接引台
    b.ico(3.2, 2, MAT((lx - 1.0, ly - 2.0, z_top - z_len + 4.0),
                    (0.3, 0.2, 0.1), (1, 0.85, 0.7)), 'rock', smooth=False)
    b.cyl(0.12, 0.12, 3.0, 8, MAT((lx - 1.0, ly - 2.0, z_top - z_len + 7.4)), 'wood')
    b.uvsph(0.36, MAT((lx - 1.0, ly - 2.0, z_top - z_len + 9.2)), 'glow_lamp', u=10, v=8)
    return b


# ================================================================ 锻炉（锤音院）
def build_forge(M):
    b = B('forge', [M['stone_dark'], M['roof_slate'], M['glow_fire'], M['iron'],
                    M['copper'], M['stone_light']])
    fx, fy = -36.0, 22.0
    mm = MAT((fx, fy, 0), (0, 0, 0.35))
    b.box((10.5, 7.5, 5.2), mm @ MAT((0, 0, TOP + 1.2)), 'stone_dark')
    b.prism_xz([(-5.8, 0), (5.8, 0), (0, 2.6)], 8.6, mm @ MAT((0, 0, TOP + 3.8)), 'roof_slate')
    b.box((2.2, 1.2, 6.0), mm @ MAT((2.5, 0.5, TOP + 8.2)), 'stone_dark')          # 烟囱
    b.box((2.8, 1.6, 1.0), mm @ MAT((2.5, 0.5, TOP + 11.6)), 'copper')
    b.cyl(1.2, 0.6, 1.6, 10, mm @ MAT((2.5, 0.5, TOP + 12.6)), 'glow_fire')
    # 炉口
    b.box((0.9, 2.6, 2.2), mm @ MAT((0, -3.76, TOP + 1.6)), 'glow_fire')
    b.cyl(0.5, 0.35, 1.2, 8, mm @ MAT((-3.0, -4.4, TOP + 0.9)), 'iron')
    b.box((1.6, 0.9, 0.7), mm @ MAT((-3.0, -4.6, TOP + 0.35)), 'iron')             # 铁砧
    b.uvsph(0.36, mm @ MAT((4.2, -3.6, TOP + 4.6)), 'glow_fire', u=10, v=8)
    return b


# ================================================================ 树木与灌木
def build_flora(M):
    b = B('flora', [M['leaf'], M['leaf_dark'], M['trunk'], M['wood'], M['wheat']])
    # 梧桐（星语院 · 800 岁）
    tx, ty = 14.0, -50.0
    b.cyl(0.95, 0.75, 8.0, 8, MAT((tx, ty, TOP + 4.0)), 'trunk')
    b.cyl(0.5, 0.4, 3.0, 8, MAT((tx + 1.8, ty + 0.6, TOP + 7.4), (0, 0.5, 0)), 'trunk')
    for (dx, dy, dz, r) in [(0, 0, 11.5, 5.2), (3.2, 1.2, 10.4, 3.4),
                            (-3.0, 1.6, 10.0, 3.0), (-1.4, -2.4, 9.6, 2.8),
                            (2.0, -2.0, 9.0, 2.4)]:
        b.uvsph(r, MAT((tx + dx, ty + dy, TOP + dz), (0, 0, 0), (1.35, 1.15, 0.8)),
                'leaf', u=14, v=8)
    # 石松（若干处）
    for (px, py, s) in [(104, -26, 1.0), (112, 30, 0.8), (88, 44, 0.7),
                        (-30, -34, 0.9), (-18, 38, 0.75), (56, 52, 0.8)]:
        b.cyl(0.3 * s, 0.26 * s, 2.4 * s, 6, MAT((px, py, TOP + 1.2 * s)), 'trunk')
        for li, (tr, th) in enumerate([(2.4, 2.4), (1.9, 2.1), (1.4, 1.7)]):
            b.cyl(tr * 0.55 * s, 0.0, th * s, 8,
                  MAT((px, py, TOP + (2.0 + li * 1.6) * s)), 'leaf_dark')
    # 灌木散布
    rng = srand(55)
    count = 0
    while count < 30:
        a = rng.uniform(0, TAU)
        rr = rng.uniform(0.52, 0.93)
        x = math.cos(a) * rr * 78
        y = math.sin(a) * rr * 52
        # 避开建筑与路径扇区
        if math.hypot(x, y) < 31:
            continue
        if abs(math.atan2(y, x) % (PI / 2)) < 0.20 or abs(math.atan2(y, x)) < 0.12:
            continue
        if (x - 14) ** 2 + (y + 50) ** 2 < 81 or (x - 46) ** 2 + (y + 36) ** 2 < 300:
            continue
        s = rng.uniform(0.7, 1.6)
        b.ico(s, 1, MAT((x, y, TOP + s * 0.55), (0, 0, rng.uniform(0, 3)),
                      (1.25, 1.25, 0.72)), 'leaf_dark' if count % 2 else 'leaf', smooth=False)
        count += 1
    # 东端麦田
    for (mx, my, w, d, rot) in [(96, -14, 22, 14, 0.2), (104, 22, 18, 12, -0.3),
                                (86, 40, 14, 10, 0.1)]:
        b.box((w, d, 0.5), MAT((mx, my, TOP + 0.15), (0, 0, rot)), 'wheat')
    return b


# ================================================================ 船头望塔
def build_tip_tower(M):
    b = B('tip_tower', [M['stone_light'], M['roof_slate'], M['glow_lamp'], M['gold']])
    tx, ty = 118.0, 2.0
    b.cyl(2.2, 2.4, 1.0, 12, MAT((tx, ty, TOP + 0.2)), 'stone_light')
    b.cyl(1.3, 1.5, 6.4, 12, MAT((tx, ty, TOP + 4.0)), 'stone_light')
    b.cyl(1.7, 1.7, 0.5, 12, MAT((tx, ty, TOP + 7.4)), 'stone_light')
    b.box((1.9, 1.9, 1.4), MAT((tx, ty, TOP + 8.4)), 'gold')
    b.uvsph(0.45, MAT((tx, ty, TOP + 9.4)), 'glow_lamp', u=12, v=8)
    b.cyl(1.4, 0.0, 1.8, 12, MAT((tx, ty, TOP + 10.4)), 'roof_slate')
    return b


# ================================================================ 灯绳（悬链）
def build_lantern_strings(M):
    lamps = B('lanterns', [M['glow_lamp']])
    ropes = []
    strands = [
        ((0, 0, TOP + 56.0), (72, 0, TOP + 12.0), 5.0),
        ((0, 0, TOP + 56.0), (0, -46, TOP + 12.0), 5.0),
        ((0, 0, TOP + 56.0), (0, 46, TOP + 12.0), 5.0),
        ((0, 0, TOP + 56.0), (-40, 0, TOP + 12.0), 5.0),
        ((0, 0, TOP + 56.0), (46, -36, TOP + 30.0), 6.0),
        ((0, 0, TOP + 30.0), (26, 0, TOP + 7.4), 1.6),
    ]
    for (a, bpt, sag) in strands:
        pts = catenary(a, bpt, sag, 18)
        ropes.append(make_curve(pts, 0.05, M['rope'], 'rope_strand'))
        A, Bv = Vector(a), Vector(bpt)
        for i in range(1, 8):
            t = i / 8.0
            p = lerp(A, Bv, t)
            p.z -= sag * (4 * t * (1 - t))
            lamps.uvsph(0.3, MAT((p.x, p.y, p.z - 0.32)), 'glow_lamp', u=10, v=8)
    return lamps, ropes


# ================================================================ 观星台（东船尖 · 四院星斗赛）
def build_observatory(M):
    b = B('observatory', [M['stone_cream'], M['stone_light'], M['gold'],
                          M['roof_slate'], M['glow_warm'], M['stone_dark']])
    ox, oy = 118.0, -18.0
    mm = MAT((ox, oy, 0), (0, 0, 0.2))
    # 台基
    b.cyl(9.0, 9.6, 2.2, 24, mm @ MAT((0, 0, TOP + 0.6)), 'stone_light')
    b.cyl(7.2, 7.4, 7.0, 24, mm @ MAT((0, 0, TOP + 5.0)), 'stone_cream')
    # 环廊柱
    for k in range(12):
        a = k * TAU / 12
        x, y = math.cos(a) * 8.2, math.sin(a) * 8.2
        b.cyl(0.3, 0.34, 4.6, 8, mm @ MAT((x, y, TOP + 4.0)), 'stone_light')
    b.cyl(8.8, 8.8, 0.55, 24, mm @ MAT((0, 0, TOP + 6.6)), 'stone_dark')
    # 穹顶（旋转式）
    b.uvsph(4.6, mm @ MAT((0, 0, TOP + 9.6), scale=(1.15, 1.15, 0.95)), 'roof_slate', u=24, v=12)
    b.box((4.2, 2.2, 1.6), mm @ MAT((2.0, 0, TOP + 12.6), (0, 0.5, 0)), 'stone_dark')
    # 望远镜管
    b.cyl(0.5, 0.62, 4.6, 12, mm @ MAT((3.4, 0, TOP + 13.6), (0, 1.1, 0)), 'gold')
    # 星命名碑（金）
    b.box((1.4, 1.0, 3.4), mm @ MAT((-6.4, 4.0, TOP + 2.4), (0, 0, 0.4)), 'gold')
    b.uvsph(0.34, mm @ MAT((-6.4, 4.0, TOP + 4.6)), 'glow_warm', u=10, v=8)
    return b


# ================================================================ 组装
def build_all(M):
    objs = []

    def emit(x):
        if isinstance(x, B):
            objs.append(x.to_object())
        elif isinstance(x, (tuple, list)):
            for y in x:
                emit(y)
        else:
            objs.append(x)

    def add(fn):
        emit(fn(M))

    add(build_tower)
    add(build_library)
    for key in HOUSES:
        add(lambda m, k=key: build_gate(m, k))
        add(lambda m, k=key: build_cloister(m, k))
    add(build_dorms)
    add(build_plaza)
    add(build_pool)
    add(build_boat)
    add(build_ladder)
    add(build_forge)
    add(build_flora)
    add(build_tip_tower)
    add(build_observatory)
    add(build_lantern_strings)
    return objs
