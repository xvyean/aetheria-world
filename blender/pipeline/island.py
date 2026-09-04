# -*- coding: utf-8 -*-
"""岛体：顶面台地（含船首岬）、四带岩层、船底穹面、晶簇、垂蔓、浮岩、护墙。"""
import math
from math import sin, cos, pi, radians as D
from . import geo, util, layout, mats as _mats
from .util import R

CK = 'Z00_ISL'

def rim_radius(theta):
    """岛缘半径（含船首岬与海心内收）"""
    base = layout.RIM + 1.4 * sin(D(theta) * 3.1 + 0.7) + 0.9 * sin(D(theta) * 7.3 + 2.1)
    base += 3.4 * math.exp(-(((theta + 45) ** 2) / (2 * 15 ** 2)))       # 船首岬（东北）
    base -= 1.6 * math.exp(-(((theta - 83) ** 2) / (2 * 22 ** 2)))       # 海心院外缘内收（南墙即缘）
    return base

def _jitter(x, y, z, amp, seed):
    n = (sin(x * 1.31 + seed) * sin(y * 1.77 + seed * 2.1) * 0.5 +
         sin(x * 3.7 + y * 2.9 + seed * 3.3) * 0.35 +
         sin(x * 7.1 - y * 5.3 + seed * 5.1) * 0.15)
    return z + n * amp

# ---------------------------------------------------------------- 顶面草地
def build_top(mat):
    seg, rings = 96, 6
    prof = [(0.0, 0.26), (0.28, 0.20), (0.52, 0.11), (0.76, -0.02), (0.92, -0.28), (1.0, -0.72)]
    vs, fs = [], []
    vs.append((0, 0, 0.26))
    for ri, (t, zz) in enumerate(prof[1:], start=1):
        r0 = rim_radius(0)
        for j in range(seg):
            th = 2 * pi * j / seg
            rr = rim_radius(math.degrees(th)) * t
            x, y = cos(th) * rr, sin(th) * rr
            z = _jitter(x, y, zz, 0.10, 1.7 + ri)
            vs.append((x, y, z))
    for j in range(seg):
        fs.append((0, 1 + j, 1 + (j + 1) % seg))
    for ri in range(1, len(prof)):
        a0 = 1 + (ri - 1) * seg
        a1 = 1 + ri * seg
        for j in range(seg):
            j2 = (j + 1) % seg
            fs.append((a0 + j, a0 + j2, a1 + j2, a1 + j))
    ob = geo._mesh('ISL_top', vs, fs, mat, CK, uv='cyl', uvscale=0.22, smooth=True)
    for p in ob.data.polygons:
        pass
    return ob

# ---------------------------------------------------------------- 岩体（四带）
def build_rock(mat_main, mat_deep):
    seg = 96
    prof = [  # (径向比例, z)
        (1.000, -0.72), (0.988, -1.7), (0.965, -3.2), (0.905, -5.8), (0.825, -8.8),
        (0.715, -12.2), (0.585, -15.8), (0.465, -19.4), (0.365, -22.8), (0.300, -25.2),
        (0.286, -26.0), (0.205, -26.35), (0.105, -26.52), (0.0, -26.6),
    ]
    vs, fs, matidx = [], [], []
    rings = []
    for ri, (t, zz) in enumerate(prof):
        ring = []
        for j in range(seg):
            th = 2 * pi * j / seg
            rr = rim_radius(math.degrees(th)) * t
            x, y = cos(th) * rr, sin(th) * rr
            amp = 0.35 if ri < 8 else 0.12
            z = _jitter(x, y, zz, amp, 9.1 + ri * 1.3)
            ring.append(len(vs))
            vs.append((x, y, z))
        rings.append(ring)
    for ri in range(len(prof) - 1):
        for j in range(seg):
            j2 = (j + 1) % seg
            fs.append((rings[ri][j], rings[ri][j2], rings[ri + 1][j2], rings[ri + 1][j]))
            matidx.append(0 if (prof[ri][1] > -19.0 and prof[ri + 1][1] > -21.0) else 1)
    # 底尖
    vs.append((0, 0, -26.6))
    tip = len(vs) - 1
    for j in range(seg):
        j2 = (j + 1) % seg
        fs.append((rings[-1][j], rings[-1][j2], tip))
        matidx.append(1)
    ob = geo._mesh('ISL_rock', vs, fs, None, CK, uv='cyl', uvscale=0.16, smooth=True)
    ob.data.materials.append(mat_main)
    ob.data.materials.append(mat_deep)
    for p, mi in zip(ob.data.polygons, matidx):
        p.material_index = mi
    return ob

# ---------------------------------------------------------------- 底部与点缀
def build_under(mat_crystal, mat_rock, mat_vine):
    objs = geo.crystal_cluster('ISL_under_core', mat_crystal, CK, (0, 0, -26.0), n=7, h=5.2, r=0.9)
    for i in range(6):
        a = 60 * i + R.uniform(-16, 16)
        p = layout.pos(a, 7.4)
        z = -23.6 + R.uniform(-1.0, 0.5)
        objs += geo.crystal(f'ISL_rc{i}', mat_crystal, CK, (p[0], p[1], z),
                            h=R.uniform(1.2, 2.4), r=R.uniform(0.2, 0.42),
                            rot=(R.uniform(-0.4, 0.4), R.uniform(-0.4, 0.4), R.uniform(0, 3)))
    objs.append(geo.ring_tube('ISL_under_ring', 0.62, 0.06, mat_rock, (0, 0, -25.7), CK, n=14, m=6))
    # 垂蔓
    for i in range(14):
        a = R.uniform(-180, 180)
        if 65 < a < 115:   # 海心侧少垂蔓（临海院墙）
            continue
        p = layout.pos(a, rim_radius(a) * 0.985)
        x0, y0 = p
        z0 = -0.8 + R.uniform(-0.3, 0.2)
        L = R.uniform(4.5, 9.5)
        x1 = x0 * R.uniform(0.90, 0.97)
        y1 = y0 * R.uniform(0.90, 0.97)
        pts = [(x0, y0, z0), (x0 * 0.99, y0 * 0.99, z0 - L * 0.35),
               (x1, y1, z0 - L * 0.72), (x1 * 0.995, y1 * 0.995, z0 - L)]
        objs.append(geo.tube(f'ISL_vine{i}', pts, R.uniform(0.05, 0.085), mat_vine, CK))
        if i % 3 == 0:
            objs.append(geo.sphere(f'ISL_vknot{i}', 0.22, mat_vine, (x1, y1, z0 - L), CK, seg=8, rings=5))
    # 浮岩
    for i in range(12):
        a = R.uniform(-180, 180)
        rr = R.uniform(2.5, 9.0)
        p = layout.pos(a, rim_radius(a) + rr)
        z = R.uniform(-11.0, -2.0)
        s = R.uniform(0.7, 1.7)
        ob = geo.sphere(f'ISL_float{i}', s, mat_rock, (p[0], p[1], z), CK, seg=10, rings=6,
                        scale=(R.uniform(0.8, 1.2), R.uniform(0.7, 1.1), R.uniform(0.55, 0.9)),
                        rot=(R.uniform(0, 3), R.uniform(0, 3), R.uniform(0, 3)))
        if i % 3 == 0:
            geo.sphere(f'ISL_floatm{i}', s * 0.55, _mats.M('moss'), (p[0], p[1], z + s * 0.45), CK,
                       seg=8, rings=5, scale=(1, 1, 0.4))
    return objs

# ---------------------------------------------------------------- 护墙（北东西三面 + 垛口）
def build_wall(mat):
    objs = []
    def blocked(th):
        for a, b in [(-58, -30), (64, 118), (150, 200)]:  # 山门 / 海心(南墙即缘) / 墓园缓坡
            if a <= th <= b:
                return True
        return False
    th = -178.0
    step = 3.2
    while th < 178:
        if not blocked(th):
            r = rim_radius(th) - 1.0
            p = layout.pos(th, r)
            ang = th + 90
            z = 0.0
            objs.append(geo.box(f'ISL_wall{int(th)}', 0.5, 2.5, 0.9, mat, ckey=CK,
                                loc=(p[0], p[1], z + 0.45), rot=(0, 0, D(ang))))
            if int(th / step) % 2 == 0:
                objs.append(geo.box(f'ISL_wallc{int(th)}', 0.7, 0.5, 1.15, mat, ckey=CK,
                                    loc=(p[0], p[1], z + 0.55), rot=(0, 0, D(ang))))
        th += step
    return objs

def build_all(M):
    objs = []
    objs.append(build_top(M('grass')))
    objs.append(build_rock(M('rock'), M('rock2')))
    objs += build_under(M('crystal'), M('rock'), M('vine'))
    objs += build_wall(M('stonewall'))
    return objs
