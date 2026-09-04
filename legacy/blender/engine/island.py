# -*- coding: utf-8 -*-
"""星槎学院 · 大地与裂隙
地面荒原 / 星辉裂隙裂谷 / 发光晶簇 / 光柱 / 星辉河 / 空岛台地
"""
import math
from mathutils import Vector
from helpers import B, MAT, vnoise, fbm, clamp, smoothstep, lerp, srand, TAU, PI

# ---- 关键高度 ----
ISLAND_TOP = 240.0        # 岛顶面
ISLAND_CLIFF = 68.0       # 崖高
GROUND_Z = 0.0
PLAZA_R = 30.0


# ================================================================ 地面
def ground_h(x, y):
    """地形高度函数（确定性），裂隙裂谷 + 远山"""
    # 远山（南/西/东较远区域）
    d = math.hypot(x, y)
    ridge = max(0.0, fbm(x * 0.004, y * 0.004, 4, 1.0, 31.0)) * 26.0
    hill = smoothstep(620, 1050, d) * ridge
    base = fbm(x * 0.02, y * 0.02, 4, 1.0, 7.0) * 2.6
    # 裂隙裂谷：沿 X 轴的长椭圆凹陷
    # 距裂缝线段的距离（裂缝：x∈[-150,150], y=0）
    dx = clamp(x, -150, 150)
    dy = y
    d_rift = math.hypot(x - dx, y - dy)
    depth = 20.0 * smoothstep(88.0, 18.0, d_rift)
    crack = 7.0 * smoothstep(9.0, 1.5, d_rift)
    return base + hill - depth - crack


def build_ground(M):
    b = B('ground', [M['rock'], M['rock_mid'], M['rock_dark'], M['soil'],
                     M['grass'], M['moss']])
    nx, ny = 220, 110
    sx, sy = 2400.0, 1200.0
    x0, y0 = -sx / 2, -sy / 2
    grid = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            x = x0 + sx * i / nx
            y = y0 + sy * j / ny
            h = ground_h(x, y)
            row.append((x, y, h))
        grid.append(row)
    # 顶点
    vs = [[b.bm.verts.new((x, y, z)) for x, y, z in row] for row in grid]
    # 面 + 材质按高度/属性分
    for j in range(ny):
        for i in range(nx):
            f = b.bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
            cx = (grid[j][i][0] + grid[j + 1][i + 1][0]) / 2
            cy = (grid[j][i][1] + grid[j + 1][i + 1][1]) / 2
            cz = (grid[j][i][2] + grid[j + 1][i + 1][2]) / 2
            d_r = math.hypot(clamp(cx, -150, 150) - cx, cy)
            if d_r < 14:
                mat = 'rock_dark'
            elif d_r < 45:
                mat = 'rock'
            elif cz < -4:
                mat = 'rock_mid'
            elif cz > 6:
                mat = 'moss'
            elif cz < 1.2:
                mat = 'soil'
            else:
                mat = 'grass'
            f.material_index = b.slot[mat]
            f.smooth = False
    return b


# ================================================================ 裂隙晶簇
def build_crystals(M):
    b = B('rift_crystals', [M['crystal'], M['crystal_core']])
    rng = srand(11)
    # 主簇：裂缝线上 46 枚
    for i in range(46):
        x = rng.uniform(-145, 145)
        y = rng.gauss(0, 9.0)
        d_r = abs(y)
        if d_r > 11:
            continue
        r = lerp(0.7, 4.2, 1.0 - clamp(d_r / 11, 0, 1)) * rng.uniform(0.6, 1.35)
        # 中心的大晶更多
        center = 1.0 - clamp(abs(x) / 150, 0, 1)
        r *= 0.8 + 0.7 * center
        h = r * rng.uniform(1.6, 2.8)
        tilt = rng.uniform(-0.22, 0.22)
        face = rng.choice([0, 1])
        mat = 'crystal_core' if r > 3.0 else 'crystal'
        b.cyl(r, r * 0.22, h, 4, MAT((x, y, ground_h(x, y) + h / 2 - 1.2),
                                   (tilt, rng.uniform(-0.3, 0.3), 0)),
              mat, caps=True, smooth=False)
    # 谷壁小晶群
    for i in range(30):
        x = rng.uniform(-170, 170)
        side = rng.choice([-1, 1])
        y = side * rng.uniform(16, 46)
        r = rng.uniform(0.4, 1.4)
        h = r * rng.uniform(1.4, 2.2)
        tilt = rng.uniform(-0.4, 0.4)
        b.cyl(r, r * 0.3, h, 4, MAT((x, y, ground_h(x, y) + h / 2 - 0.8),
                                  (tilt, rng.uniform(-0.4, 0.4), 0)),
              'crystal', caps=True, smooth=False)
    return b


def build_crack_glow(M):
    """裂缝底发光裂纹带 + 宽阔的谷底辉光毯"""
    b = B('rift_crack_glow', [M['rift_crack']])
    seg = 90
    pts = []
    for i in range(seg + 1):
        x = lerp(-150, 150, i / seg)
        y = vnoise(x, 0, 0, 0.02, 41.0) * 3.0
        z = ground_h(x, y) + 1.2
        pts.append(Vector((x, y, z)))
    # 亮裂纹（窄）
    b.ribbon(pts, [4.2 - 3.2 * (i / seg) for i in range(seg + 1)], 'rift_crack', smooth=False)
    # 谷底辉光毯（宽而弱，模拟「整个谷底都在发光」）
    b.ribbon(pts, [26.0 - 16.0 * (i / seg) for i in range(seg + 1)], 'rift_crack', smooth=True)
    return b


# ================================================================ 光柱
def build_pillar(M):
    b = B('light_pillar', [M['pillar'], M['pillar_core']])
    # 下柱：裂隙 → 岛底（托举，顶缘恰好在岛底之下）
    b.cyl(26.0, 17.0, 168.0, 48, MAT((0, 0, -28 + 84)), 'pillar', caps=True, smooth=True)
    b.cyl(10.0, 6.6, 168.0, 32, MAT((0, 0, -28 + 84)), 'pillar_core', caps=True, smooth=True)
    # 上柱：裂隙晶 → 天穹（星辉流，细束）——从塔顶晶簇上方重新升起
    b.cyl(4.0, 2.0, 620.0, 32, MAT((0, 0, 372 + 310)), 'pillar', caps=True, smooth=True)
    b.cyl(1.8, 0.9, 620.0, 24, MAT((0, 0, 372 + 310)), 'pillar_core', caps=True, smooth=True)
    # 柱外螺旋浮晶（星辉流，仅在下柱区域）
    b2 = B('pillar_crystals', [M['crystal']])
    rng = srand(23)
    for k in range(36):
        t = k / 36.0
        ang = t * TAU * 3.0 + 0.5
        rad = 32.0 + 8.0 * math.sin(t * TAU * 2.0)
        z = 25.0 + t * 112.0
        x, y = math.cos(ang) * rad, math.sin(ang) * rad
        r = lerp(0.8, 2.4, t * (1 - t) * 4.0) * rng.uniform(0.7, 1.3)
        b2.cyl(r, r * 0.2, r * 4.6, 4, MAT((x, y, z), (rng.uniform(-0.5, 0.5),
                                                     rng.uniform(-0.5, 0.5), ang)),
               'crystal', caps=True, smooth=False)
    return b, b2


# ================================================================ 星辉河
def build_river(M):
    b = B('river', [M['river']])
    # 自裂隙东口向东南蜿蜒
    path = [(168, 6), (205, 22), (238, 52), (262, 96), (280, 152), (296, 222),
            (312, 300), (330, 390), (346, 480)]
    widths = [7.0, 6.4, 5.8, 5.0, 4.2, 3.4, 2.8, 2.2, 1.6]
    pts = []
    for i, (x, y) in enumerate(path):
        z = ground_h(x, y) + 0.9
        pts.append(Vector((x, y, z)))
    b.ribbon(pts, widths, 'river', smooth=True)
    return b


# ================================================================ 空岛台地
def island_profile(theta):
    """岛体极坐标轮廓：船形超椭圆，西钝东尖（+X 为东）"""
    c, s = math.cos(theta), math.sin(theta)
    a_w, a_e, bb = 54.0, 150.0, 60.0
    a = a_w + (a_e - a_w) * smoothstep(-0.15, 0.55, c)
    r = 1.0 / math.sqrt((c / a) ** 2 + (s / bb) ** 2)
    r *= (1.0 + 0.14 * vnoise(c * 1.9, s * 1.9, 0, 1.0, 5.0))
    r += 16.0 * max(0.0, c) ** 7                      # 东端尖化
    return r


def island_r(theta):
    return island_profile(theta)


def build_island(M):
    """空岛：顶面 + 崖壁 + 底部 + 石笋，单对象"""
    b = B('island', [M['rock'], M['rock_dark'], M['rock_mid'], M['moss'],
                     M['grass'], M['stone_light'], M['soil']])
    N, TOP = 168, ISLAND_TOP
    cliff = ISLAND_CLIFF

    def ring_pts(scale, z_fn, shrink=1.0, jitter=0.0, seed=0.0):
        pts = []
        for i in range(N):
            th = TAU * i / N
            r = island_r(th) * scale * shrink
            nz = 1.0 + jitter * vnoise(math.cos(th) * 4.0, math.sin(th) * 4.0, 0, 1.0, seed)
            x, y = math.cos(th) * r, math.sin(th) * r
            pts.append(Vector((x, y, z_fn(th, r))))
        return pts

    # ---- 顶面（径向渐密网格）----
    t_steps = [0.0, 0.20, 0.40, 0.60, 0.78, 0.90, 1.0]
    top_rings = []
    for t in t_steps:
        def zf(th, r, t=t):
            rr = r / max(island_r(th), 1e-5)
            bump = 1.5 * fbm(math.cos(th) * 2 + 3, math.sin(th) * 2, 3, 1.0, 9.0)
            bump *= smoothstep(0.5, 0.98, rr) * (0.4 + 0.6 * t)
            return TOP + bump + 0.4 * t
        top_rings.append(ring_pts(t if t > 0 else 0.0, zf, jitter=0.0))
    # 中央点
    c_v = [b.bm.verts.new((0, 0, TOP + 0.5))]
    # 顶面网格
    for j in range(len(top_rings) - 1):
        r0, r1 = top_rings[j], top_rings[j + 1]
        v0 = [b.bm.verts.new(p) for p in r0]
        v1 = [b.bm.verts.new(p) for p in r1]
        mat = 'grass' if j >= 1 else 'grass'
        for i in range(N):
            f = b.bm.faces.new((v0[i], v0[(i + 1) % N], v1[(i + 1) % N], v1[i]))
            # 边缘环带状苔缘
            f.material_index = b.slot['moss' if j == len(top_rings) - 2 else mat]
            f.smooth = False
    # 中心扇
    v0 = [b.bm.verts.new(p) for p in top_rings[0]]
    for i in range(N):
        f = b.bm.faces.new((c_v[0], v0[(i + 1) % N], v0[i]))
        f.material_index = b.slot['grass']
        f.smooth = False

    # ---- 崖壁（内收 + 岩层条带 · 噪声风化）----
    z_bands = [TOP - 2.0, TOP - 11.0, TOP - 24.0, TOP - 38.0, TOP - 52.0, TOP - cliff]
    band_mats = ['moss', 'rock_mid', 'rock', 'rock_mid', 'rock_dark', 'rock']
    prev = top_rings[-1]
    prev_v = [b.bm.verts.new(p) for p in prev]
    for bi, z in enumerate(z_bands):
        zn = (TOP - z) / cliff
        scale = 1.0 - 0.13 * (zn ** 1.7)          # 内收
        def zfn(th, r, z=z, zn=zn):
            return z + 2.6 * vnoise(math.cos(th) * 6.0, math.sin(th) * 6.0, 0, 1.0, 17.0 + zn * 3.0)
        ring = ring_pts(1.0, zfn, shrink=scale, seed=zn * 7.0)
        cur_v = [b.bm.verts.new(p) for p in ring]
        for i in range(N):
            f = b.bm.faces.new((prev_v[i], prev_v[(i + 1) % N],
                                cur_v[(i + 1) % N], cur_v[i]))
            f.material_index = b.slot[band_mats[bi]]
            f.smooth = False
        prev_v = cur_v

    # ---- 底部（内收穹 + 岛根石笋位置留孔不处理，贴近即可）----
    bottom_rings = []
    for (s, z) in [(0.9, TOP - cliff - 4.0), (0.62, TOP - cliff - 16.0),
                   (0.34, TOP - cliff - 26.0), (0.12, TOP - cliff - 32.0)]:
        def zfn(th, r, z=z):
            return z + 1.2 * vnoise(math.cos(th) * 5.0, math.sin(th) * 5.0, 0, 1.0, 51.0)
        bottom_rings.append(ring_pts(1.0, zfn, shrink=s, seed=8.0))
    for bi, ring in enumerate(bottom_rings):
        cur_v = [b.bm.verts.new(p) for p in ring]
        for i in range(N):
            f = b.bm.faces.new((prev_v[i], prev_v[(i + 1) % N],
                                cur_v[(i + 1) % N], cur_v[i]))
            f.material_index = b.slot['rock_dark' if bi > 0 else 'rock']
            f.smooth = False
        prev_v = cur_v
    # 底心
    bv = [b.bm.verts.new(p) for p in bottom_rings[-1]]
    center = b.bm.verts.new((0, 0, TOP - cliff - 34.0))
    for i in range(N):
        f = b.bm.faces.new((bv[i], bv[(i + 1) % N], center))
        f.material_index = b.slot['rock_dark']
        f.smooth = False

    # ---- 崖壁风化岩块（打破规则色带）----
    rng = srand(171)
    for k in range(60):
        th = rng.uniform(0, TAU)
        rr = island_r(th) * rng.uniform(0.99, 1.06)
        x, y = math.cos(th) * rr, math.sin(th) * rr
        z = TOP - rng.uniform(8, cliff - 6)
        s = rng.uniform(0.8, 2.6)
        b.ico(s, 1, MAT((x, y, z), (rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), 0),
                        (1.25, 1.0, 0.7)),
              'rock' if rng.random() < 0.6 else 'rock_mid', smooth=False)

    # ---- 岛底石笋（倒长的山根）----
    rng = srand(77)
    for k in range(9):
        th = rng.uniform(0, TAU)
        rr = island_r(th) * rng.uniform(0.22, 0.8)
        x, y = math.cos(th) * rr, math.sin(th) * rr
        L = rng.uniform(45, 130)
        r = rng.uniform(3.0, 8.0)
        z0 = TOP - cliff - 30.0
        b.cyl(r, r * 0.22, L, 8, MAT((x, y, z0 - L / 2),
                                     (rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), 0)),
              'rock_dark', caps=True, smooth=False)
    return b


def build_floating_rocks(M):
    """浮岩群（8 块，其中 2 块有树、1 块孤灯、1 块近岛底覆苔）"""
    b = B('floating_rocks', [M['rock'], M['rock_mid'], M['rock_dark'], M['moss'],
                             M['leaf_dark'], M['trunk'], M['glow_lamp'], M['iron']])
    b2 = B('floating_trees', [M['leaf'], M['leaf_dark'], M['trunk']])
    rng = srand(99)
    spots = [
        (105, -60, 150, 7.0), (120, 40, 120, 5.0), (60, 100, 175, 4.0),
        (-90, 70, 130, 6.0), (-120, -50, 155, 4.5), (0, 130, 205, 3.5),
        (75, -120, 100, 8.0), (-40, -100, 90, 5.5),
        (20, -140, 165, 4.5), (-60, -155, 140, 3.8), (140, -30, 105, 6.2),
        (-140, 30, 170, 5.0), (95, 110, 140, 3.2), (-110, 105, 185, 4.2),
    ]
    for idx, (x, y, z, r) in enumerate(spots):
        seg = 10 if r < 5 else 12
        ax, ay = rng.uniform(0, TAU), rng.uniform(0, TAU)
        mt = MAT((x, y, z), (ax, ay, rng.uniform(-0.3, 0.3)), (1, 0.82, 0.72))
        b.ico(r, 2, mt, 'rock_mid' if idx % 2 else 'rock', smooth=False)
        # 顶部苔面
        b.ico(r * 0.86, 2, MAT((x, y, z + r * 0.38), (ax, ay, 0), (1, 0.9, 0.25)),
              'moss', smooth=False)
        if idx in (1, 4, 7):
            # 石松 2-3 层
            tx, ty = x + r * 0.1, y + r * 0.08
            tz = z + r * 0.72
            b2.cyl(0.35, 0.28, 2.4, 6, MAT((tx, ty, tz + 1.2)), 'trunk')
            for li, (tr, th) in enumerate([(2.6, 2.6), (2.0, 2.2), (1.4, 1.8)]):
                b2.cyl(tr * 0.55, 0.0, th, 8, MAT((tx, ty, tz + 1.6 + li * 1.7)), 'leaf')
        if idx == 6:
            # 孤灯
            b.cyl(0.16, 0.16, 3.2, 6, MAT((x, y, z + r * 0.7 + 1.6)), 'iron')
            b.uvsph(0.5, MAT((x, y, z + r * 0.7 + 3.6)), 'glow_lamp', u=12, v=8)
    # 近岛底“悬着的草”浮岩
    b.ico(4.5, 2, MAT((-30, 24, 178), (0.4, 0.2, 0.2), (1, 0.85, 0.7)), 'rock_dark', smooth=False)
    b.ico(3.6, 2, MAT((-30, 24, 182), (0.4, 0.2, 0.2), (1, 0.9, 0.3)), 'moss', smooth=False)
    return b, b2
