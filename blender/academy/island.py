# -*- coding: utf-8 -*-
"""
星槎学院 · 岛体
- 杏仁形轮廓，西侧缺口（"被咬过一口"）
- 岛面自西向东抬高三米，中心广场找平
- 崖壁分层岩 + 倒锥底 + 塔根
- 陪岛石（带轨道参数，写入 glTF extras）
- 环道（东半铺石、西半土路）、双圈栏杆
"""
import math
import random
from mathutils import Vector
from util import *
import layout as LY

A_AXIS, B_AXIS = 250.0, 180.0
BITE_DEPTH, BITE_WIDTH = 38.0, 0.44      # 西门外的天然港湾
RIM_Z_DROP = 13.0                        # 崖壁垂直段
TIP_Z = -115.0                           # 扩展后的倒锥尖
SEGS = 192                               # 大岛增加轮廓分段


def island_radius(theta):
    c, s = math.cos(theta), math.sin(theta)
    r = A_AXIS * B_AXIS / math.sqrt((B_AXIS * c) ** 2 + (A_AXIS * s) ** 2)
    r *= 1.0 + 0.055 * fbm(c * 2.3, s * 2.3, 0.7, oct=3, seed=5.0)
    d = abs(math.atan2(math.sin(theta - math.pi), math.cos(theta - math.pi)))
    if d < BITE_WIDTH:
        k = math.cos(d / BITE_WIDTH * math.pi / 2)
        r -= BITE_DEPTH * k * k
    return r


def raw_h(x, y):
    base = 0.3 + 6.0 * smoothstep(-230.0, 230.0, x)
    base += 0.85 * fbm(x / 34.0, y / 34.0, 0.0, oct=3, seed=11.0)
    d = math.hypot(x, y)
    plaza = 1.75
    k = smoothstep(LY.PLAZA_R + 6.0, LY.PLAZA_R + 2.0, d)
    return base * (1 - k) + plaza * k


_PADS = None


def _pads():
    global _PADS
    if _PADS is None:
        _PADS = []
        for (px, py, pr, pz) in LY.pads():
            if pz is None:
                pz = raw_h(px, py)
            _PADS.append((px, py, pr, pz))
    return _PADS


def ground_h(x, y):
    """岛面高度（米），含建筑找平垫。"""
    h = raw_h(x, y)
    for (px, py, pr, pz) in _pads():
        d = math.hypot(x - px, y - py)
        if d < pr:
            k = smoothstep(pr, pr * 0.62, d)
            h = h * (1 - k) + pz * k
    return h


def road_r(th):
    """环道中心半径：外城与岛沿之间的一圈大道。"""
    R = island_radius(th)
    return R * LY.ROAD_K


def rail_gap(th):
    """栏杆断口：栈桥口与浮池。"""
    if abs(math.atan2(math.sin(th - math.pi), math.cos(th - math.pi))) < 0.15:
        return True
    th_pool = math.atan2(LY.POOL['pos'][1], LY.POOL['pos'][0])
    if abs(math.atan2(math.sin(th - th_pool), math.cos(th - th_pool))) < 0.17:
        return True
    return False


def theta_r(x, y):
    t = math.atan2(y, x)
    return t, island_radius(t)


def build_island(M, C):
    # ------------------------------------------------ 主体：极坐标网格 + 崖壁 + 倒锥
    rings = []
    NR = 42
    # 岛面
    for i in range(NR + 1):
        t = i / NR
        f = t ** 0.85
        ring = []
        for k in range(SEGS):
            th = TAU * k / SEGS
            R = island_radius(th)
            r = R * f
            x, y = math.cos(th) * r, math.sin(th) * r
            z = ground_h(x, y)
            if i == NR:
                z -= 0.15
            ring.append(Vector((x, y, z)))
        rings.append(ring)
    # 崖壁（略外鼓，再内收）
    cliff_profile = [(1.012, -0.6), (1.03, -2.2), (1.02, -4.0), (0.985, -RIM_Z_DROP)]
    for (rf, dz) in cliff_profile:
        ring = []
        for k in range(SEGS):
            th = TAU * k / SEGS
            R = island_radius(th)
            wob = 1.0 + 0.03 * fbm(math.cos(th) * 3.0, math.sin(th) * 3.0, dz * 0.4, oct=3, seed=2.0)
            r = R * rf * wob
            x, y = math.cos(th) * r, math.sin(th) * r
            z = ground_h(x, y) + dz
            ring.append(Vector((x, y, z)))
        rings.append(ring)
    # 倒锥：更多环、竖向棱脊（ridged 沿 θ 高频）、低频鼓包
    NC = 18
    for j in range(1, NC + 1):
        t = j / NC
        ring = []
        for k in range(SEGS):
            th = TAU * k / SEGS
            R = island_radius(th) * 0.985
            shrink = (1 - t) ** 1.15
            low = fbm(math.cos(th) * 2.2, math.sin(th) * 2.2, t * 3.0, oct=4, seed=3.0)
            stri = ridged(math.cos(th) * 7.0, math.sin(th) * 7.0, t * 1.2, oct=3, seed=4.0) - 1.2
            wob = 1.0 + 0.26 * low + 0.14 * stri * (0.4 + 0.6 * t)
            r = max(R * shrink * wob, 0.8 if j < NC else 0.0)
            x, y = math.cos(th) * r, math.sin(th) * r
            z_rim = -RIM_Z_DROP
            z = z_rim + (TIP_Z - z_rim) * (t ** 0.85)
            z += 2.2 * fbm(x / 9.0, y / 9.0, 0.5, oct=2, seed=6.0) * (1 - t)
            z -= 1.6 * max(0.0, stri) * (1 - t) * t  # 棱脊处下垂
            ring.append(Vector((x, y, z)))
        rings.append(ring)
    # 顶点：中心极点单独处理 —— 把第 0 圈合并为一个点：直接用 ring_surface 再 merge
    ob = ring_surface('Island_Body', rings, C['island'], mat=M['rock'], cap_top=False, cap_bottom=True)
    # 合并中心圈的重复点
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    center_verts = [bm.verts[k] for k in range(SEGS)]
    bmesh.ops.pointmerge(bm, verts=center_verts, merge_co=(0, 0, ground_h(0, 0)))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    smooth_by_angle(ob, 38)

    top_z_at_rim = {}

    def col_fn(co, n):
        x, y, z = co.x, co.y, co.z
        gz = ground_h(x, y)
        up = n.z
        rock_a, rock_b, rock_c = hex2lin(PAL['rock_a'])[:3], hex2lin(PAL['rock_b'])[:3], hex2lin(PAL['rock_c'])[:3]
        grass_a, grass_b, grass_c = hex2lin(PAL['grass_a'])[:3], hex2lin(PAL['grass_b'])[:3], hex2lin(PAL['grass_c'])[:3]
        soil = hex2lin(PAL['soil'])[:3]
        dirt = hex2lin(PAL['path_dirt'])[:3]
        # 岩：地层
        band = 0.5 + 0.5 * math.sin(z * 1.1 + 2.0 * fbm(x / 7, y / 7, z / 7, oct=2, seed=9))
        rock = mix(rock_b, rock_c, band)
        rock = mix(rock, rock_a, 0.45)
        rock = tuple(c * (0.9 + 0.2 * fbm(x / 3, y / 3, z / 3, oct=2, seed=12)) for c in rock)
        # 倒锥：竖向棱脊阴影 + 越往下越暗、越蓝（裂隙光影响）
        if z < -RIM_Z_DROP + 0.5:
            thr = math.atan2(y, x)
            st = ridged(math.cos(thr) * 7.0, math.sin(thr) * 7.0, 0.3, oct=2, seed=4.0) - 1.0
            rock = tuple(c * (0.82 + 0.25 * st) for c in rock)
            deep = smoothstep(-RIM_Z_DROP, TIP_Z, z)
            rock = mix(rock, (0.05, 0.12, 0.18), deep * 0.45)
        # 草
        gn = 0.5 + 0.5 * fbm(x / 6.5, y / 6.5, 0.0, oct=3, seed=21)
        grass = mix(grass_c, grass_b, gn)
        grass = mix(grass, grass_a, 0.4)
        # 大块明暗斑（草地不均匀）+ 细碎斑点
        patch = fbm(x / 16.0, y / 16.0, 1.0, oct=2, seed=22)
        grass = tuple(c * (1.0 + 0.16 * patch) for c in grass)
        spk = fbm(x / 1.1, y / 1.1, 2.0, oct=1, seed=23)
        grass = tuple(c * (1.0 + 0.08 * spk) for c in grass)
        # 环道：土路（西半）在岛面上压一道
        th = math.atan2(y, x)
        R = island_radius(th)
        d = math.hypot(x, y)
        rr = road_r(th)
        road = smoothstep(2.2, 1.0, abs(d - rr))
        west = smoothstep(-0.25, 0.25, -math.cos(th))  # 西半
        grass = mix(grass, dirt, road * west * 0.85)
        # 边缘泥土
        edge = smoothstep(0.9, 0.985, d / R)
        grass = mix(grass, soil, edge * 0.6)
        # 上下混合
        k = smoothstep(0.35, 0.8, up) * smoothstep(gz - 1.2, gz - 0.25, z)
        return mix(rock, grass, k)
    set_vcol(ob, col_fn)

    # ------------------------------------------------ 塔根（星陨塔地基穿岛而出）
    root_top, root_bot = TIP_Z + 6.0, TIP_Z - 16.0
    root = lathe('Tower_Root', [(4.6, root_top), (4.2, root_top - 4), (3.4, root_bot + 4), (2.2, root_bot), (0.0, root_bot - 2.5)],
                 8, (0, 0, 0), C['island'], mat=M['basalt'], smooth=False, phase=math.pi / 8)
    set_vcol_const(root, PAL['basalt'], jitter=0.15, seed=3)
    # 悬垂岩柱：从倒锥面上垂下的钟乳状岩体
    rng = random.Random(77)
    for i in range(11):
        a = TAU * i / 11 + rng.uniform(-0.25, 0.25)
        t = rng.uniform(0.25, 0.75)
        R = island_radius(a) * 0.985 * (1 - t) ** 1.15 * 0.96
        z_rim = -RIM_Z_DROP
        z0 = z_rim + (TIP_Z - z_rim) * (t ** 0.85) + 1.5
        L = rng.uniform(7.0, 16.0) * (1.2 - t * 0.6)
        r0 = rng.uniform(1.6, 3.2)
        prof = [(r0 * 1.15, 0.0), (r0, -L * 0.25), (r0 * 0.7, -L * 0.6), (r0 * 0.35, -L * 0.88), (0.0, -L)]
        hc = lathe('Island_HangRock_%02d' % i, prof, 9, (math.cos(a) * R, math.sin(a) * R, z0), C['island'], mat=M['rock'], smooth=True)
        me = hc.data
        sd = rng.uniform(0, 50)
        for v in me.vertices:
            n = Vector((v.co.x, v.co.y, 0.0))
            if n.length > 1e-4:
                n.normalize()
                d = fbm(n.x * 2.0, n.y * 2.0, v.co.z * 0.25, oct=3, seed=sd)
                v.co.x *= 1 + 0.3 * d
                v.co.y *= 1 + 0.3 * d
        me.update()
        smooth_by_angle(hc, 30)
        hc.rotation_euler = (rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), 0)
        hc.rotation_euler = (-math.sin(a) * 0.14, math.cos(a) * 0.14, 0.0)
        set_vcol(hc, lambda co, n_, sd=sd: tuple(c * (0.85 + 0.3 * (0.5 + 0.5 * fbm(co.x / 2, co.y / 2, co.z / 2, oct=2, seed=sd))) for c in mix(hex2lin(PAL['rock_b'])[:3], hex2lin(PAL['rock_a'])[:3], 0.5)))
    # 根部晶簇：大而明显，围着塔根与锥尖
    for i in range(16):
        a = TAU * i / 16 + rng.uniform(-0.2, 0.2)
        if i < 10:
            z = rng.uniform(root_bot + 2.0, root_top + 4.0)
            r0 = 3.0 + 1.6 * (z - root_bot) / (root_top - root_bot)
        else:
            z = rng.uniform(TIP_Z + 3.0, TIP_Z + 12.0)
            t = (z + RIM_Z_DROP) / (TIP_Z + RIM_Z_DROP)
            r0 = island_radius(a) * 0.985 * (1 - t) ** 1.15 * 0.9
        h = rng.uniform(4.5, 11.0)
        w = h * rng.uniform(0.14, 0.2)
        c = lathe('FX_CrystalRoot_%02d' % i, [(0.0, -h * 0.25), (w, 0.0), (w * 0.8, h * 0.6), (0.0, h)], 6,
                  (math.cos(a) * r0, math.sin(a) * r0, z), C['fx'], mat=M['crystal_root'], smooth=False)
        tilt = rng.uniform(0.55, 1.1)
        c.rotation_euler = (-math.sin(a) * tilt, math.cos(a) * tilt, rng.uniform(0, 1))
        c['fx'] = 'crystal_root'
    # 岩下的碎石垂挂
    for i in range(14):
        a = rng.uniform(0, TAU)
        t = rng.uniform(0.15, 0.7)
        R = island_radius(a) * 0.985 * (1 - t) ** 1.25
        z = -RIM_Z_DROP + (TIP_Z + RIM_Z_DROP) * t
        s = ico('Island_Rubble_%02d' % i, rng.uniform(0.8, 2.4), (math.cos(a) * R * 1.02, math.sin(a) * R * 1.02, z - 1.0),
                C['island'], mat=M['rock'], subdiv=1, smooth=False)
        jitter_verts(s, 0.35, rng)
        s.scale = (1.0, rng.uniform(0.7, 1.2), rng.uniform(0.6, 1.0))
        set_vcol_const(s, PAL['rock_b'], jitter=0.2, seed=i)

    # ------------------------------------------------ 陪岛石（绕岛一年一周）
    rng = random.Random(1024)
    for i in range(34):
        a = TAU * i / 34 + rng.uniform(-0.12, 0.12)
        orbit_r = rng.uniform(285.0, 390.0)
        z = rng.uniform(-72.0, 26.0)
        size = rng.choice([0.5, 0.8, 1.2, 1.8, 2.6, 3.6, 4.8]) * rng.uniform(0.8, 1.2)
        s = ico('Companion_Stone_%02d' % i, size, (math.cos(a) * orbit_r, math.sin(a) * orbit_r, z),
                C['stones'], mat=M['rock'], subdiv=2 if size > 1.0 else 1, smooth=False)
        rock_displace(s, rng, size)
        s.rotation_euler = (rng.uniform(0, 3), rng.uniform(0, 3), rng.uniform(0, 3))
        s.scale = (1.0, rng.uniform(0.75, 1.15), rng.uniform(0.6, 1.05))
        set_vcol_const(s, PAL['rock_a'], jitter=0.22, seed=100 + i)
        # 轨道参数 → glTF extras
        s['orbit_r'] = orbit_r
        s['orbit_a0'] = a
        s['orbit_z'] = z
        s['spin'] = rng.uniform(-0.4, 0.4)
        s['bob'] = rng.uniform(0.6, 1.8)
        # 顶上一小撮草（大块石头）
        if size > 2.4:
            g = ico('Companion_Grass_%02d' % i, size * 0.6, (math.cos(a) * orbit_r, math.sin(a) * orbit_r, z + size * 0.62),
                    C['stones'], mat=M['grass'], subdiv=2, smooth=True)
            rock_displace(g, rng, size * 0.6, amt=0.18)
            g.scale = (1.25, 1.1, 0.3)
            set_vcol_const(g, PAL['grass_a'], jitter=0.15, seed=200 + i)
            bpy.context.view_layer.update()          # 让 s.matrix_world 含入上面设置的旋转/缩放
            g.parent = s
            g.matrix_parent_inverse = s.matrix_world.inverted()

    # ------------------------------------------------ 云：岛下与岛侧几团（渲染与网页共用）
    rng = random.Random(4242)
    for i in range(9):
        a = TAU * i / 9 + rng.uniform(-0.3, 0.3)
        d = rng.uniform(310.0, 520.0)
        z = rng.uniform(-150.0, -70.0) if i % 3 else rng.uniform(-45.0, 16.0)
        cx, cy = math.cos(a) * d, math.sin(a) * d
        n_puff = rng.randint(3, 6)
        for j in range(n_puff):
            pr = rng.uniform(5.0, 11.0)
            c = ico('FX_Cloud_%02d_%d' % (i, j), pr, (cx + rng.uniform(-9, 9), cy + rng.uniform(-9, 9), z + rng.uniform(-2, 3)), C['fx'], mat=M['cloud'], subdiv=2, smooth=True)
            c.scale = (1.0, rng.uniform(0.8, 1.3), rng.uniform(0.35, 0.5))
            c['fx'] = 'cloud'
            c['fx_i'] = i
    # ------------------------------------------------ 环道石板（东半）
    build_ring_road_paving(M, C)
    # ------------------------------------------------ 双圈栏杆
    build_railings(M, C)
    return ob


def rock_displace(ob, rng, size, amt=0.32):
    """岩石：低频拉伸 + 中频 fbm + 高频棱角。"""
    me = ob.data
    sd = rng.uniform(0, 100)
    sx, sy, sz = rng.uniform(0.8, 1.3), rng.uniform(0.8, 1.3), rng.uniform(0.6, 1.0)
    for v in me.vertices:
        n = v.co.normalized()
        d = fbm(n.x * 1.6, n.y * 1.6, n.z * 1.6, oct=3, seed=sd)
        r2 = 1.0 + amt * d + 0.12 * (ridged(n.x * 3.0, n.y * 3.0, n.z * 3.0, oct=2, seed=sd + 1) - 1.0)
        v.co = Vector((n.x * sx, n.y * sy, n.z * sz)) * size * r2
    me.update()
    smooth_by_angle(ob, 28)


def jitter_verts(ob, amt, rng):
    me = ob.data
    for v in me.vertices:
        n = v.co.normalized()
        v.co += n * rng.uniform(-amt, amt) * v.co.length
    me.update()


def road_point(th, off=0.0):
    r = road_r(th) + off
    x, y = math.cos(th) * r, math.sin(th) * r
    return Vector((x, y, ground_h(x, y)))


def build_ring_road_paving(M, C):
    """东半环道铺石：一块块梯形石板贴着地面（西半只在顶点色里压出土路）。"""
    rng = random.Random(55)
    verts, faces = [], []
    n = 300
    for i in range(n):
        th0 = -math.pi / 2 + math.pi * i / n
        th1 = -math.pi / 2 + math.pi * (i + 0.86) / n
        for lane in range(2):
            o0 = -1.5 + lane * 1.5 + 0.06
            o1 = o0 + 1.5 - 0.12
            p00, p01 = road_point(th0, o0), road_point(th0, o1)
            p10, p11 = road_point(th1, o0), road_point(th1, o1)
            zlift = 0.06 + rng.uniform(0.0, 0.05)
            base = len(verts)
            for p in (p00, p01, p11, p10):
                verts.append((p.x, p.y, p.z + zlift))
            for p in (p00, p01, p11, p10):
                verts.append((p.x, p.y, p.z + zlift + 0.14))
            faces.append((base + 4, base + 5, base + 6, base + 7))
            faces.append((base + 0, base + 1, base + 5, base + 4))
            faces.append((base + 1, base + 2, base + 6, base + 5))
            faces.append((base + 2, base + 3, base + 7, base + 6))
            faces.append((base + 3, base + 0, base + 4, base + 7))
    ob = mesh_from('Ring_Road_Paving', verts, faces, C['paths'], mat=M['flagstone'])
    rng2 = random.Random(56)
    base = hex2lin(PAL['flagstone'])[:3]
    per_slab = {}

    def f(co, nrm):
        key = (round(co.x / 1.5), round(co.y / 1.5))
        if key not in per_slab:
            per_slab[key] = 0.82 + rng2.random() * 0.36
        j = per_slab[key]
        return (base[0] * j, base[1] * j, base[2] * j * 0.97)
    set_vcol(ob, f)
    return ob


def build_railings(M, C):
    """岛沿两圈栏杆：内圈石柱木栏，外圈（海心院的地界）矮桩铁链。"""
    verts, faces = [], []

    def add_box(p, sx, sy, sz, rot):
        base = len(verts)
        c, s = math.cos(rot), math.sin(rot)
        for dz in (0, sz):
            for (ex, ey) in ((-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy)):
                rx, ry = ex * c - ey * s, ex * s + ey * c
                verts.append((p.x + rx, p.y + ry, p.z + dz))
        faces.extend([(base + 4, base + 5, base + 6, base + 7), (base + 3, base + 2, base + 1, base + 0),
                      (base + 0, base + 1, base + 5, base + 4), (base + 1, base + 2, base + 6, base + 5),
                      (base + 2, base + 3, base + 7, base + 6), (base + 3, base + 0, base + 4, base + 7)])

    def add_bar(p0, p1, r):
        d = p1 - p0
        L = d.length
        if L < 1e-4:
            return
        ang = math.atan2(d.y, d.x)
        pitch = math.atan2(d.z, math.hypot(d.x, d.y))
        base = len(verts)
        c, s = math.cos(ang), math.sin(ang)
        cp, sp = math.cos(pitch), math.sin(pitch)
        for (u, v, w) in ((0, -r, -r), (0, r, -r), (0, r, r), (0, -r, r), (L, -r, -r), (L, r, -r), (L, r, r), (L, -r, r)):
            # pitch about local y then yaw about z
            x1, z1 = u * cp - w * sp, u * sp + w * cp
            verts.append((p0.x + x1 * c - v * s, p0.y + x1 * s + v * c, p0.z + z1))
        faces.extend([(base + 0, base + 1, base + 2, base + 3), (base + 7, base + 6, base + 5, base + 4),
                      (base + 0, base + 4, base + 5, base + 1), (base + 1, base + 5, base + 6, base + 2),
                      (base + 2, base + 6, base + 7, base + 3), (base + 3, base + 7, base + 4, base + 0)])

    # 内圈
    n_in = 260
    pts = []
    for i in range(n_in):
        th = TAU * i / n_in
        R = island_radius(th)
        r = R * 0.955
        x, y = math.cos(th) * r, math.sin(th) * r
        p = Vector((x, y, ground_h(x, y)))
        # 缺口西侧、栈桥处留门
        pts.append((th, p))
    stone_verts_start = 0
    for i, (th, p) in enumerate(pts):
        if rail_gap(th):
            continue
        add_box(p, 0.18, 0.18, 1.05, th)
    ob_posts = mesh_from('Railing_Inner_Posts', verts, faces, C['paths'], mat=M['stone_grey'])
    set_vcol_const(ob_posts, PAL['stone_grey'], jitter=0.12, seed=7)
    verts, faces = [], []
    for i, (th, p) in enumerate(pts):
        th2, p2 = pts[(i + 1) % n_in]
        if rail_gap(th) or rail_gap(th2):
            continue
        for zz in (0.55, 0.95):
            add_bar(p + Vector((0, 0, zz)), p2 + Vector((0, 0, zz)), 0.045)
    ob_rails = mesh_from('Railing_Inner_Rails', verts, faces, C['paths'], mat=M['wood_mid'])
    set_vcol_const(ob_rails, PAL['wood_mid'], jitter=0.1, seed=8)
    # 外圈：三步之外，矮桩铁链
    verts, faces = [], []
    n_out = 300
    pts = []
    for i in range(n_out):
        th = TAU * i / n_out
        R = island_radius(th)
        r = R * 0.992
        x, y = math.cos(th) * r, math.sin(th) * r
        p = Vector((x, y, ground_h(x, y) - 0.15))
        pts.append((th, p))
    for i, (th, p) in enumerate(pts):
        if rail_gap(th):
            continue
        add_box(p, 0.09, 0.09, 0.55, th)
    ob2 = mesh_from('Railing_Outer_Posts', verts, faces, C['paths'], mat=M['iron'])
    verts, faces = [], []
    for i, (th, p) in enumerate(pts):
        th2, p2 = pts[(i + 1) % n_out]
        if rail_gap(th) or rail_gap(th2):
            continue
        # 链条垂弧：三段
        a = p + Vector((0, 0, 0.5))
        b = p2 + Vector((0, 0, 0.5))
        m1 = a.lerp(b, 0.33) - Vector((0, 0, 0.12))
        m2 = a.lerp(b, 0.66) - Vector((0, 0, 0.12))
        add_bar(a, m1, 0.02)
        add_bar(m1, m2, 0.02)
        add_bar(m2, b, 0.02)
    ob3 = mesh_from('Railing_Outer_Chain', verts, faces, C['paths'], mat=M['iron'])
    return ob_posts
