# -*- coding: utf-8 -*-
"""
星槎学院 · 核心建筑：星陨塔 / 四柱 / 广场 / 四院回廊 / 星穗馆 / 校史馆
"""
import bmesh
import math
import random
from mathutils import Vector, Matrix
from util import *
from parts import *
import layout as LY
import island as IS

HOUSE_ORDER = ('dawn', 'speak', 'forge', 'tide')
HOUSE_YAW = {'dawn': 0.0, 'speak': math.pi / 2, 'forge': -math.pi / 2, 'tide': math.pi}


# ================================================================== 星陨塔
def build_star_tower(M, C):
    T = LY.STAR_TOWER
    r, rt, h, sides = T['r'], T['r_top'], T['h'], T['sides']
    gz = IS.ground_h(0, 0)
    col = C['tower']
    objs = []
    # 台基：三级八角
    for i, (rr, hh) in enumerate(((r + 3.4, 0.45), (r + 2.4, 0.45), (r + 1.4, 0.45))):
        b = prism('StarTower_Plinth_%d' % i, rr, hh, 8, (0, 0, gz + i * 0.45), col, M['stone_white'])
        subdivide(b, 2)
        stone_vcol(b, PAL['stone_white'], seed=i, ground_z=0.0, grime=0.2)
        objs.append(b)
    base_z = gz + 1.35
    # 塔身：分段砌筑，略收分，每段之间有线脚
    segs_z = [(0.0, 9.0), (9.3, 18.0), (18.3, 26.0), (26.3, h)]
    for i, (z0, z1) in enumerate(segs_z):
        t0, t1 = z0 / h, z1 / h
        r0, r1 = r + (rt - r) * t0, r + (rt - r) * t1
        body = lathe('StarTower_Body_%d' % i, [(r0, z0), (r1, z1)], sides, (0, 0, base_z), col, M['stone_white'], smooth=False, phase=math.pi / 8)
        subdivide(body, 14)
        stone_vcol(body, PAL['stone_white'], seed=10 + i, ground_z=0.0, course=0.62, grime=0.35 if i == 0 else 0.0, noise_amt=0.12)
        objs.append(body)
        if i < len(segs_z) - 1:
            # 线脚（string course）+ 金色饰带
            sc = lathe('StarTower_Course_%d' % i, [(r1 + 0.02, z1), (r1 + 0.32, z1 + 0.08), (r1 + 0.32, z1 + 0.22), (r1 + 0.02, z1 + 0.3)], sides, (0, 0, base_z), col, M['stone_cream'], smooth=False, phase=math.pi / 8)
            set_vcol_const(sc, PAL['stone_cream'], jitter=0.06, seed=i)
            objs.append(sc)
            gb = lathe('StarTower_GoldBand_%d' % i, [(r1 + 0.03, z1 - 0.32), (r1 + 0.09, z1 - 0.28), (r1 + 0.09, z1 - 0.06), (r1 + 0.03, z1 - 0.02)], sides, (0, 0, base_z), col, M['gold'], smooth=False, phase=math.pi / 8)
            objs.append(gb)
        # 每段面上的浅浮雕盲拱（凹进去的假窗带，让白墙不空）
        for k in range(sides):
            a = TAU * (k + 0.5) / sides
            t = ((z0 + z1) / 2) / h
            rr = r + (rt - r) * t
            face_r = rr * math.cos(math.pi / sides)
            c_, s_ = math.cos(a), math.sin(a)
            for dz in (-2.6, 2.6):
                pl = box('StarTower_Relief_%d_%d_%d' % (i, k, int(dz > 0)), (0.06, 0.55, 1.3), (c_ * (face_r + 0.03), s_ * (face_r + 0.03), base_z + (z0 + z1) / 2 + dz), col, M['stone_cream'], rot=(0, 0, a))
                set_vcol_const(pl, '#c9bda2', jitter=0.04, seed=k)
                objs.append(pl)
    # 角部扶壁（8 条）
    for k in range(sides):
        a = TAU * k / sides  # 顶点方向（phase=π/8 时顶点在 0, 45°...）
        bt = lathe('StarTower_Buttress_%d' % k, [(0.75, 0), (0.7, 6.0), (0.5, 11.0), (0.3, 16.0), (0.22, 16.6)], 4, (math.cos(a) * (r + 0.35), math.sin(a) * (r + 0.35), base_z), col, M['stone_cream'], smooth=False, phase=a + math.pi / 4)
        subdivide(bt, 4)
        stone_vcol(bt, PAL['stone_cream'], seed=20 + k, grime=0.3)
        objs.append(bt)
        pin = lathe('StarTower_ButtressPin_%d' % k, [(0.3, 0), (0.12, 0.7), (0.0, 1.3)], 4, (math.cos(a) * (r + 0.35), math.sin(a) * (r + 0.35), base_z + 16.6), col, M['gold'], smooth=False, phase=a + math.pi / 4)
        objs.append(pin)
    # 螺旋外梯：绕塔 2.4 圈，从台基到晶室
    objs += build_spiral_stair(M, C, r, rt, h, base_z)
    # 窗：每段两扇尖窗错开
    for i, (z0, z1) in enumerate(segs_z[:-1]):
        for k in range(sides):
            if (k + i) % 2:
                continue
            a = TAU * (k + 0.5) / sides  # 面中心方向
            t = ((z0 + z1) / 2) / h
            rr = r + (rt - r) * t
            face_r = rr * math.cos(math.pi / sides)
            pos = Vector((math.cos(a) * face_r, math.sin(a) * face_r, base_z + (z0 + z1) / 2 + 0.6))
            objs += window('StarTower_Win_%d_%d' % (i, k), pos, a, 0.8, 2.2, col, M, kind='lancet')
    # 塔顶平台 + 八面敞亭
    top_z = base_z + h
    plat = lathe('StarTower_TopPlate', [(rt + 0.9, 0), (rt + 1.1, 0.25), (rt + 1.1, 0.5), (rt + 0.6, 0.5)], sides, (0, 0, top_z), col, M['stone_cream'], smooth=False, phase=math.pi / 8)
    set_vcol_const(plat, PAL['stone_cream'], jitter=0.06, seed=30)
    objs.append(plat)
    objs += parapet_ring('StarTower_TopParapet', (0, 0, top_z + 0.5), rt + 0.6, sides, col, M['stone_white'], h=0.9, t=0.28, phase=math.pi / 8)
    pav_z = top_z + 0.5
    pav_h = 6.2
    for k in range(sides):
        a = TAU * k / sides + math.pi / 8
        objs += column('StarTower_PavCol_%d' % k, (math.cos(a) * (rt - 0.3), math.sin(a) * (rt - 0.3), pav_z), col, M, r=0.3, h=pav_h, mat=M['stone_white'])
        # 柱间尖拱（两根斜杆组成的尖拱）
        a2 = TAU * (k + 1) / sides + math.pi / 8
        p0 = Vector((math.cos(a) * (rt - 0.3), math.sin(a) * (rt - 0.3), pav_z + pav_h - 1.6))
        p1 = Vector((math.cos(a2) * (rt - 0.3), math.sin(a2) * (rt - 0.3), pav_z + pav_h - 1.6))
        am = (a + a2) / 2
        pm = Vector((math.cos(am) * (rt - 0.3) * math.cos(math.pi / sides), math.sin(am) * (rt - 0.3) * math.cos(math.pi / sides), pav_z + pav_h - 0.1))
        objs.append(tube('StarTower_PavArch_%d' % k, [p0, p0.lerp(pm, 0.5) + Vector((0, 0, 0.35)), pm, pm.lerp(p1, 0.5) + Vector((0, 0, 0.35)), p1], 0.1, col, M['gold'], segs=6))
    # 亭顶：八角攒尖 + 金瓦（更陡）
    objs += pyramid_roof('StarTower_PavRoof', rt - 0.1, 5.2, sides, (0, 0, pav_z + pav_h + 0.3), col, M['gold'], overhang=0.7, phase=math.pi / 8, thick=0.16, finial_mat=M['gold'], finial_h=2.2)
    # 屋顶八条脊线（铜）
    for k in range(sides):
        a = TAU * k / sides + math.pi / 8
        p0 = Vector((math.cos(a) * (rt + 0.6), math.sin(a) * (rt + 0.6), pav_z + pav_h + 0.46))
        p1 = Vector((0, 0, pav_z + pav_h + 0.3 + 5.2 + 0.16))
        objs.append(tube('StarTower_RoofRidge_%d' % k, [p0, p1], 0.07, col, M['copper'], segs=5))
    # 亭顶下的环梁
    beam = lathe('StarTower_PavBeam', [(rt + 0.2, 0), (rt + 0.2, 0.32), (rt - 0.6, 0.32), (rt - 0.6, 0)], sides, (0, 0, pav_z + pav_h), col, M['stone_cream'], smooth=False, phase=math.pi / 8, close=False)
    objs.append(beam)
    # 裂隙晶：八面体，不落地，缓缓转
    cz = pav_z + 3.0
    cry = lathe('FX_RiftCrystal', [(0.0, -1.7), (0.6, -0.8), (0.7, 0.0), (0.6, 0.8), (0.0, 1.7)], 8, (0, 0, cz), C['fx'], M['crystal'], smooth=False)
    cry.scale = (1.0, 1.0, 1.3)
    # 晶体下的光环（发光薄环）
    halo = torus('FX_CrystalHalo', 1.6, 0.05, (0, 0, cz - 0.4), C['fx'], M['crystal_root'], segs=32, rsegs=5)
    halo['fx'] = 'halo'
    objs.append(halo)
    cry['fx'] = 'crystal'
    objs.append(cry)
    # 晶体周围的悬浮碎片
    rng = random.Random(9)
    for i in range(7):
        a = TAU * i / 7 + rng.uniform(-0.2, 0.2)
        rr = 1.1 + rng.uniform(0, 0.5)
        sh = lathe('FX_CrystalShard_%d' % i, [(0, -0.22), (0.07, 0), (0, 0.22)], 4, (math.cos(a) * rr, math.sin(a) * rr, cz + rng.uniform(-0.9, 0.9)), C['fx'], M['crystal'], smooth=False)
        sh.rotation_euler = (rng.uniform(0, 1), rng.uniform(0, 1), 0)
        sh['fx'] = 'shard'
        sh['orbit_r'] = rr
        sh['orbit_a0'] = a
        objs.append(sh)
    # 塔身裂缝里的苔藓（发绿光的小块）
    rng = random.Random(31)
    for i in range(26):
        a = rng.uniform(0, TAU)
        z = rng.uniform(2.0, h - 4.0)
        t = z / h
        rr = r + (rt - r) * t
        face_a = (math.floor((a - math.pi / 8) / (TAU / sides)) + 0.5) * (TAU / sides) + math.pi / 8
        face_r = rr * math.cos(math.pi / sides)
        c, s = math.cos(face_a), math.sin(face_a)
        # 沿面切向偏移
        u = rng.uniform(-rr * 0.32, rr * 0.32)
        p = Vector((c * face_r - s * u, s * face_r + c * u, base_z + z))
        mo = box('FX_Moss_%02d' % i, (0.06, rng.uniform(0.12, 0.34), rng.uniform(0.25, 0.9)), p + Vector((c, s, 0)) * 0.02, C['fx'], M['moss'], rot=(0, 0, face_a))
        mo['fx'] = 'moss'
        objs.append(mo)
    # 塔门（南面，朝锤音回廊）
    door_a = -math.pi / 2
    face_r = r * math.cos(math.pi / sides)
    dp = Vector((0, -face_r, base_z))
    objs += door('StarTower_Door', dp, door_a, 1.8, 3.4, col, M, arch=True, frame_mat=M['stone_cream'])
    objs += steps('StarTower_Steps', Vector((0, -(r + 3.4), gz)), -math.pi / 2, 4.0, 3, rise=0.45, tread=1.0, collection=col, mat=M['stone_white'])
    return objs


def subdivide(ob, cuts):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def build_spiral_stair(M, C, r, rt, h, base_z):
    """绕塔的螺旋外梯：踏步 + 外侧矮栏 + 支撑牛腿。每年换一级——第 412 级是新石。"""
    col = C['tower']
    objs = []
    turns = 2.4
    n = 300
    tread_w = 1.15
    verts, faces = [], []
    rail_pts = []
    rng = random.Random(412)
    start_a = -math.pi / 2  # 从南门旁起
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        a0 = start_a + TAU * turns * t0
        a1 = start_a + TAU * turns * t1
        z0 = base_z + 0.3 + (h - 1.2) * t0
        rr0 = r + (rt - r) * (z0 - base_z) / h
        rin = rr0 * 1.0 + 0.02
        rout = rin + tread_w
        # 扇形踏步：四角 + 厚度
        base = len(verts)
        pts = [(math.cos(a0) * rin, math.sin(a0) * rin), (math.cos(a0) * rout, math.sin(a0) * rout),
               (math.cos(a1) * rout, math.sin(a1) * rout), (math.cos(a1) * rin, math.sin(a1) * rin)]
        thick = 0.18
        for (x, y) in pts:
            verts.append((x, y, z0 - thick))
        for (x, y) in pts:
            verts.append((x, y, z0))
        faces += [(base + 4, base + 5, base + 6, base + 7), (base + 3, base + 2, base + 1, base + 0),
                  (base + 0, base + 1, base + 5, base + 4), (base + 1, base + 2, base + 6, base + 5),
                  (base + 2, base + 3, base + 7, base + 6), (base + 3, base + 0, base + 4, base + 7)]
        if i % 3 == 0:
            rail_pts.append(Vector((math.cos(a0) * (rout - 0.08), math.sin(a0) * (rout - 0.08), z0)))
    stair = mesh_from('StarTower_Stair', verts, faces, col, mat=M['stone_grey'])
    base_c = hex2lin(PAL['stone_grey'])[:3]
    new_c = hex2lin(PAL['stone_white'])[:3]
    per = {}
    rng2 = random.Random(8)

    def f(co, n_):
        k = int(round((math.atan2(co.y, co.x) + TAU * 3) / (TAU * turns / n))) % 100000
        key = (k, round(co.z / 0.12))
        if key not in per:
            per[key] = 0.78 + rng2.random() * 0.4
        j = per[key]
        # 磨损：靠内侧更亮更滑
        inner = smoothstep(rout, rin, math.hypot(co.x, co.y))
        c = mix(base_c, new_c, inner * 0.35)
        return (c[0] * j, c[1] * j, c[2] * j)
    set_vcol(stair, f)
    objs.append(stair)
    # 新换的那一级（第 412 级）：亮白
    i = 137
    t0 = i / n
    a0 = start_a + TAU * turns * t0
    z0 = base_z + 0.3 + (h - 1.2) * t0
    rr0 = r + (rt - r) * (z0 - base_z) / h
    new_step = box('StarTower_Stair_NewStep', (tread_w, 0.26, 0.19), (math.cos(a0 + 0.004) * (rr0 + tread_w / 2 + 0.02), math.sin(a0 + 0.004) * (rr0 + tread_w / 2 + 0.02), z0 + 0.005), col, M['stone_white'], rot=(0, 0, a0))
    set_vcol_const(new_step, '#f4f1e8')
    new_step['lore'] = '今年熔心送来的新台阶'
    objs.append(new_step)
    # 外侧矮栏：立柱 + 扶手管
    posts = []
    for j, p in enumerate(rail_pts):
        if j % 2 == 0:
            posts.append(cylinder('StarTower_StairPost_%03d' % j, 0.05, 0.95, p, col, M['iron'], segments=6))
    objs += posts
    hand = tube('StarTower_StairHandrail', [p + Vector((0, 0, 0.95)) for p in rail_pts], 0.045, col, M['wood_dark'], segs=6)
    objs.append(hand)
    # 牛腿（每 12 级一个）
    for i in range(0, n, 12):
        t0 = i / n
        a0 = start_a + TAU * turns * t0
        z0 = base_z + 0.3 + (h - 1.2) * t0
        rr0 = r + (rt - r) * (z0 - base_z) / h
        cb = mesh_from('StarTower_Corbel_%03d' % i,
                       [(0, -0.2, 0), (tread_w * 0.85, -0.2, 0), (0, -0.2, -0.9), (0, 0.2, 0), (tread_w * 0.85, 0.2, 0), (0, 0.2, -0.9)],
                       [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)], col, mat=M['stone_grey'])
        cb.location = (math.cos(a0) * rr0, math.sin(a0) * rr0, z0 - 0.2)
        cb.rotation_euler = (0, 0, a0)
        set_vcol_const(cb, PAL['stone_grey'], jitter=0.1, seed=i)
        objs.append(cb)
    return objs


# ================================================================== 四柱 + 广场
def build_plaza(M, C):
    col = C['plaza']
    gz = IS.ground_h(0, 0)
    objs = []
    # 广场铺装：八角石板放射纹
    verts, faces = [], []
    rings = 9
    segs = 48
    for i in range(rings + 1):
        rr = LY.PLAZA_R * (i / rings) ** 0.9
        for k in range(segs):
            a = TAU * k / segs
            verts.append((math.cos(a) * rr, math.sin(a) * rr, gz + 0.04 + 0.02 * math.sin(a * 8)))
    for i in range(rings):
        for k in range(segs):
            k2 = (k + 1) % segs
            faces.append((i * segs + k, i * segs + k2, (i + 1) * segs + k2, (i + 1) * segs + k))
    plaza = mesh_from('Plaza_Paving', verts, faces, col, mat=M['flagstone'])
    fl = hex2lin(PAL['flagstone'])[:3]
    fl2 = hex2lin(PAL['stone_cream'])[:3]
    fl3 = hex2lin(PAL['stone_grey'])[:3]
    rng = random.Random(3)
    per = {}

    def f(co, n):
        a = math.atan2(co.y, co.x)
        d = math.hypot(co.x, co.y)
        key = (int((a + math.pi) / TAU * segs), int(d / LY.PLAZA_R * rings))
        if key not in per:
            per[key] = rng.uniform(0.85, 1.15)
        c = fl
        # 放射纹：8 条浅色条带（对准 8 个方向）
        band = min(abs(math.atan2(math.sin(a - TAU * k / 8), math.cos(a - TAU * k / 8))) for k in range(8))
        if band < 0.045:
            c = fl2
        # 中心同心环
        if abs(d - LY.PLAZA_R * 0.5) < 0.25 or abs(d - LY.PLAZA_R * 0.92) < 0.3:
            c = fl3
        j = per[key]
        return (c[0] * j, c[1] * j, c[2] * j)
    set_vcol(plaza, f)
    objs.append(plaza)
    # 四柱
    for i, P in enumerate(LY.PILLARS):
        x, y = P['pos']
        h = P['h']
        hk = P['house']
        base = box('Pillar_%s_Base' % hk, (1.5, 1.5, 0.4), (x, y, gz), col, M['stone_grey'], origin='bottom')
        set_vcol_const(base, PAL['stone_grey'], jitter=0.1, seed=i)
        objs.append(base)
        shaft = lathe('Pillar_%s' % hk, [(0.48, 0), (0.44, h * 0.9), (0.42, h)], 12, (x, y, gz + 0.4), col, M['stone_cream'], smooth=True)
        subdivide(shaft, 3)
        stone_vcol(shaft, PAL['stone_cream'], seed=40 + i, grime=0.3, course=0.4)
        objs.append(shaft)
        if P['broken']:
            # 断口：不规则顶面碎块
            rng = random.Random(50 + i)
            for j in range(4):
                a = TAU * j / 4 + rng.uniform(0, 0.8)
                fr = ico('Pillar_%s_Frag_%d' % (hk, j), rng.uniform(0.12, 0.25), (x + math.cos(a) * 0.3, y + math.sin(a) * 0.3, gz + 0.4 + h + rng.uniform(0.0, 0.2)), col, M['stone_cream'], subdiv=0, smooth=False)
                objs.append(fr)
            # 断掉的柱段躺在旁边
            seg_len = 6.0 - h
            if seg_len > 1.0:
                a = math.atan2(y, x) + rng.uniform(-0.4, 0.4)
                fallen = lathe('Pillar_%s_Fallen' % hk, [(0.44, 0), (0.42, seg_len)], 12, (0, 0, 0), col, M['stone_cream'], smooth=True)
                fallen.matrix_world = Matrix.Translation((x + math.cos(a) * 2.2, y + math.sin(a) * 2.2, gz + 0.44)) @ Matrix.Rotation(a + math.pi / 2 + 0.3, 4, 'Z') @ Matrix.Rotation(math.pi / 2, 4, 'X')
                subdivide(fallen, 2)
                stone_vcol(fallen, PAL['stone_cream'], seed=60 + i, grime=0.4)
                objs.append(fallen)
        else:
            cap = lathe('Pillar_%s_Cap' % hk, [(0.42, 0), (0.62, 0.22), (0.66, 0.36)], 12, (x, y, gz + 0.4 + h - 0.02), col, M['stone_cream'], smooth=False)
            objs.append(cap)
        # 柱头刻字位：一块彩色院徽板（本院色金属）
        plaque = box('Pillar_%s_Plaque' % hk, (0.04, 0.42, 0.42), (x, y, gz + 0.4 + 1.5), col, M['tile_' + hk])
        plaque.rotation_euler = (0, 0, math.atan2(-y, -x))
        plaque.location = Vector((x, y, gz + 1.9)) + Vector((math.cos(math.atan2(-y, -x)), math.sin(math.atan2(-y, -x)), 0)) * 0.46
        plaque['lore'] = {'dawn': '启', 'speak': '言', 'forge': '锻', 'tide': '怀'}[hk]
        objs.append(plaque)
    # 广场灯柱
    for j, a in enumerate(LY.PLAZA_LAMPS):
        rr = LY.PLAZA_R - 1.2
        objs += lantern_post('Plaza_Lamp_%d' % j, (math.cos(a) * rr, math.sin(a) * rr, gz + 0.05), col, M, h=2.8, glow_coll=C['fx'])
    # 广场边缘矮墙（在回廊之间的弧段）
    for k in range(4):
        a0 = TAU * k / 4 + 0.22
        a1 = TAU * (k + 1) / 4 - 0.22
        n = 10
        verts, faces = [], []
        for i in range(n + 1):
            a = a0 + (a1 - a0) * i / n
            for rr in (LY.PLAZA_R + 0.2, LY.PLAZA_R + 0.6):
                verts.append((math.cos(a) * rr, math.sin(a) * rr, gz))
                verts.append((math.cos(a) * rr, math.sin(a) * rr, gz + 0.55))
        for i in range(n):
            b = i * 4
            faces += [(b, b + 4, b + 5, b + 1), (b + 2, b + 3, b + 7, b + 6), (b + 1, b + 5, b + 7, b + 3), (b, b + 2, b + 6, b + 4)]
        w = mesh_from('Plaza_Wall_%d' % k, verts, faces, col, mat=M['stone_grey'])
        set_vcol_const(w, PAL['stone_grey'], jitter=0.12, seed=70 + k)
        objs.append(w)
    return objs


# ================================================================== 四院回廊
def build_corridors(M, C):
    """四条柱廊：两排柱子 + 本院色瓦的坡顶 + 地面石板 + 尽头无锁院门。"""
    col = C['corridors']
    objs = []
    for hk in HOUSE_ORDER:
        cd = LY.CORRIDORS[hk]
        dx, dy = cd['dir']
        yaw = math.atan2(dy, dx)
        s0, s1 = cd['start'], cd['end']
        w = cd['width']
        L = s1 - s0
        n_bays = max(3, int(L / 3.0))
        # 地面
        for i in range(n_bays):
            t0 = s0 + L * i / n_bays
            t1 = s0 + L * (i + 1) / n_bays
            cx, cy = dx * (t0 + t1) / 2, dy * (t0 + t1) / 2
            z = IS.ground_h(cx, cy)
            slab = box('Corr_%s_Slab_%02d' % (hk, i), (t1 - t0 - 0.06, w, 0.12), (cx, cy, z + 0.03), col, M['flagstone'], rot=(0, 0, yaw), origin='bottom')
            set_vcol_const(slab, PAL['flagstone'], jitter=0.12, seed=i * 7 + hash(hk) % 100)
            objs.append(slab)
        # 柱子
        ch = 3.1
        col_pts = []
        for i in range(n_bays + 1):
            t = s0 + L * i / n_bays
            for side in (-1, 1):
                px = dx * t + (-dy) * side * (w / 2 - 0.25)
                py = dy * t + dx * side * (w / 2 - 0.25)
                pz = IS.ground_h(px, py) + 0.14
                objs += column('Corr_%s_Col_%02d_%d' % (hk, i, side), (px, py, pz), col, M, r=0.2, h=ch, mat=M['stone_white'])
                col_pts.append(Vector((px, py, pz)))
        # 檐梁
        for side in (-1, 1):
            px0 = dx * s0 + (-dy) * side * (w / 2 - 0.25)
            py0 = dy * s0 + dx * side * (w / 2 - 0.25)
            px1 = dx * s1 + (-dy) * side * (w / 2 - 0.25)
            py1 = dy * s1 + dx * side * (w / 2 - 0.25)
            z = (IS.ground_h(px0, py0) + IS.ground_h(px1, py1)) / 2 + 0.14 + ch + 0.15
            b = box('Corr_%s_Beam_%d' % (hk, side), (L + 0.5, 0.36, 0.3), ((px0 + px1) / 2, (py0 + py1) / 2, z), col, M['wood_dark'], rot=(0, 0, yaw))
            wood_vcol(b, PAL['wood_dark'], seed=side)
            objs.append(b)
        # 屋顶（双坡，本院色瓦）
        zc = IS.ground_h(dx * (s0 + s1) / 2, dy * (s0 + s1) / 2) + 0.14 + ch + 0.45
        rf = gable_roof('Corr_%s_Roof' % hk, L + 0.4, w + 0.3, 1.25, (dx * (s0 + s1) / 2, dy * (s0 + s1) / 2, zc), col, M['tile_' + hk], yaw=yaw, overhang=0.5, thick=0.15, ridge_mat=M['stone_dark'])
        roof_vcol(rf[0], PAL['tile_' + hk], seed=hash(hk) % 50, moss_hex=PAL['grass_c'], moss=0.35)
        objs += rf
        # 椽子
        for i in range(int((L + 0.4) / 0.6)):
            t = s0 - 0.1 + 0.6 * i + 0.3
            px, py = dx * t, dy * t
            zb = IS.ground_h(px, py) + 0.14 + ch + 0.42
            for side in (-1, 1):
                rb = box('Corr_%s_Rafter_%02d_%d' % (hk, i, side), (0.12, w / 2 + 0.45, 0.1), (0, 0, 0), col, M['wood_mid'])
                rb.matrix_world = Matrix.Translation((px, py, zb)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Translation((0, side * (w / 4 + 0.2), 0.62)) @ Matrix.Rotation(-side * math.atan2(1.25, w / 2 + 0.5), 4, 'X')
                objs.append(rb)
        # 尽头：院门（无锁，门开着）—— 两侧门柱 + 过梁 + 本院色垂幅
        gx, gy = dx * (s1 + 0.6), dy * (s1 + 0.6)
        gz = IS.ground_h(gx, gy)
        for side in (-1, 1):
            px = gx + (-dy) * side * (w / 2 + 0.2)
            py = gy + dx * side * (w / 2 + 0.2)
            pier = box_grid('Corr_%s_GatePier_%d' % (hk, side), (0.7, 0.7, 4.2), (px, py, gz), col, M['stone_cream'], cell=0.5)
            stone_vcol(pier, PAL['stone_cream'], seed=80 + side)
            objs.append(pier)
            capb = lathe('Corr_%s_GateCap_%d' % (hk, side), [(0.5, 0), (0.42, 0.5), (0.0, 0.9)], 4, (px, py, gz + 4.2), col, M['tile_' + hk], smooth=False, phase=math.pi / 4 + yaw)
            objs.append(capb)
        lintel = box('Corr_%s_GateLintel' % hk, (0.5, w + 1.1, 0.45), (gx, gy, gz + 4.2), col, M['stone_cream'], rot=(0, 0, yaw))
        objs.append(lintel)
        # 门扇开着（两扇各开 100°）
        for side in (-1, 1):
            hinge = Vector((gx + (-dy) * side * (w / 2 - 0.15), gy + dx * side * (w / 2 - 0.15), gz))
            leaf = box('Corr_%s_GateLeaf_%d' % (hk, side), (0.08, w / 2 - 0.2, 3.6), (0, 0, 0), col, M['wood_dark'])
            open_a = yaw + side * math.radians(100)
            leaf.matrix_world = Matrix.Translation(hinge) @ Matrix.Rotation(open_a, 4, 'Z') @ Matrix.Translation((0, -side * (w / 4 - 0.1), 1.8))
            wood_vcol(leaf, PAL['wood_dark'], seed=90 + side)
            objs.append(leaf)
        # 垂幅（本院色）挂在过梁下
        objs += banner('Corr_%s_Banner' % hk, Vector((gx, gy, gz + 4.1)) - Vector((dx, dy, 0)) * 0.35, yaw + math.pi, 1.1, 2.4, col, M['cloth_' + hk], pole=True, pole_mat=M['wood_dark'], fx_coll=C['fx'])
        # 回廊入口处的挂灯（每两跨一盏）
        for i in range(1, n_bays, 2):
            t = s0 + L * (i + 0.5) / n_bays
            px, py = dx * t, dy * t
            z = IS.ground_h(px, py) + 0.14 + ch + 0.2
            objs += hanging_lamp('Corr_%s_Lamp_%02d' % (hk, i), (px, py, z - 0.55), col, M, glow_coll=C['fx'])
    return objs


# ================================================================== 星穗馆
def build_grain_hall(M, C):
    """七层圆楼，金穹顶，底层嵌岩。每层退台，窗带渐密。"""
    G = LY.GRAIN_HALL
    x, y = G['pos']
    R, floors, fh = G['r'], G['floors'], G['floor_h']
    gz = IS.ground_h(x, y)
    col = C['library']
    objs = []
    # 底层"嵌岩"：一圈粗石基座
    base = lathe('GrainHall_RockBase', [(R + 1.6, -1.5), (R + 1.3, 0.0), (R + 0.9, 1.2)], 22, (x, y, gz), col, M['rock'], smooth=False)
    subdivide(base, 2)
    set_vcol_const(base, PAL['rock_b'], jitter=0.18, seed=5)
    objs.append(base)
    z = gz + 1.2
    for f in range(floors):
        rr = R - f * 0.32
        body = lathe('GrainHall_Floor_%d' % f, [(rr, 0), (rr, fh)], 24, (x, y, z), col, M['stone_cream'], smooth=True)
        subdivide(body, 3)
        stone_vcol(body, PAL['stone_cream'], seed=100 + f, ground_z=0.0, course=0.5, grime=0.3 if f == 0 else 0.0)
        objs.append(body)
        # 楼层线脚 / 檐
        cor = lathe('GrainHall_Cornice_%d' % f, [(rr + 0.02, fh - 0.05), (rr + 0.34, fh + 0.02), (rr + 0.34, fh + 0.16), (rr - 0.32, fh + 0.16)], 24, (x, y, z), col, M['stone_white'], smooth=False, close=False)
        objs.append(cor)
        # 窗：每层数量随层数增加（藏书越往上越多）
        nw = 4 + f * 2
        for k in range(nw):
            a = TAU * k / nw + f * 0.13
            if f == 0 and abs(math.atan2(math.sin(a - math.atan2(-y, -x)), math.cos(a - math.atan2(-y, -x)))) < 0.5:
                continue  # 门的位置
            pos = Vector((x + math.cos(a) * rr, y + math.sin(a) * rr, z + fh * 0.55))
            objs += window('GrainHall_Win_%d_%02d' % (f, k), pos, a, 0.55 if f < 5 else 0.45, 1.3 if f < 5 else 1.0, col, M, kind='lancet' if f % 2 == 0 else 'square', glass='window', sill=(f < 4))
        z += fh + 0.16
    # 金穹顶
    rtop = R - (floors - 1) * 0.32
    dome = lathe('GrainHall_Dome', [(rtop + 0.4, 0), (rtop + 0.45, 0.25), (rtop * 0.98, 0.6), (rtop * 0.86, 1.6), (rtop * 0.62, 2.6), (rtop * 0.3, 3.3), (0.0, 3.55)], 24, (x, y, z), col, M['gold'], smooth=True)
    objs.append(dome)
    # 穹顶肋（8 条铜肋）
    for k in range(8):
        a = TAU * k / 8
        pts = [Vector((x + math.cos(a) * rtop * rf, y + math.sin(a) * rtop * rf, z + zz)) for (rf, zz) in ((0.99, 0.55), (0.87, 1.6), (0.63, 2.6), (0.31, 3.3), (0.02, 3.6))]
        objs.append(tube('GrainHall_Rib_%d' % k, pts, 0.09, col, M['copper'], segs=6))
    # 顶饰：星穗（一束麦穗形的金杆）
    for k in range(5):
        a = TAU * k / 5
        objs.append(cylinder('GrainHall_Spike_%d' % k, 0.05, 1.6, (x + math.cos(a) * 0.22, y + math.sin(a) * 0.22, z + 3.5), col, M['gold'], segments=6, r_top=0.01))
        objs[-1].rotation_euler = (-math.sin(a) * 0.18, math.cos(a) * 0.18, 0)
    objs.append(sphere('GrainHall_Orb', 0.28, (x, y, z + 3.9), col, M['gold'], segs=10, rings=8))
    # 门（朝广场）
    da = math.atan2(-y, -x)
    dp = Vector((x + math.cos(da) * R, y + math.sin(da) * R, gz + 1.2))
    objs += door('GrainHall_Door', dp, da, 1.6, 2.8, col, M, arch=True, frame_mat=M['stone_white'])
    objs += steps('GrainHall_Steps', Vector((x + math.cos(da) * (R + 1.2), y + math.sin(da) * (R + 1.2), gz)), da, 3.0, 4, rise=0.3, tread=0.42, collection=col, mat=M['stone_grey'])
    # 门口两盏灯
    for side in (-1, 1):
        t = Vector((-math.sin(da), math.cos(da), 0))
        objs += lantern_post('GrainHall_Lamp_%d' % side, dp + Vector((math.cos(da), math.sin(da), 0)) * 2.4 + t * side * 1.9 + Vector((0, 0, -1.2)), col, M, h=2.4, glow_coll=C['fx'])
    return objs


# ================================================================== 校史馆
def build_history_hall(M, C):
    H = LY.HISTORY_HALL
    x, y = H['pos']
    sx, sy = H['size']
    yaw = H['yaw']
    gz = IS.ground_h(x, y)
    col = C['misc']
    objs = []
    body = box_grid('HistoryHall_Body', (sx, sy, 3.4), (x, y, gz), col, M['stone_grey'], cell=0.6, rot=(0, 0, yaw))
    stone_vcol(body, PAL['stone_grey'], seed=140, grime=0.3)
    objs.append(body)
    rf = gable_roof('HistoryHall_Roof', sx, sy, 1.7, (x, y, gz + 3.4), col, M['slate'], yaw=yaw, overhang=0.5, ridge_mat=M['stone_dark'])
    roof_vcol(rf[0], PAL['slate'], seed=141, moss_hex=PAL['grass_c'], moss=0.5)
    objs += rf
    # 山墙填充
    for side in (-1, 1):
        tri = mesh_from('HistoryHall_Gable_%d' % side, [(-sy / 2, 0, 0), (sy / 2, 0, 0), (0, 0, 1.7)], [(0, 1, 2)], col, mat=M['stone_grey'])
        tri.matrix_world = Matrix.Translation((x, y, gz + 3.4)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Translation((side * sx / 2, 0, 0)) @ Matrix.Rotation(math.pi / 2 if side > 0 else -math.pi / 2, 4, 'Z')
        objs.append(tri)
    # 门朝广场
    n = Vector((math.cos(yaw), math.sin(yaw), 0))
    tv = Vector((-math.sin(yaw), math.cos(yaw), 0))
    da = yaw + math.pi / 2  # 长边朝广场
    # 计算哪条长边更靠近原点
    p1 = Vector((x, y, 0)) + tv * (sy / 2)
    p2 = Vector((x, y, 0)) - tv * (sy / 2)
    if p2.length < p1.length:
        da = yaw - math.pi / 2
        dpos = p2
    else:
        dpos = p1
    objs += door('HistoryHall_Door', Vector((dpos.x, dpos.y, gz)), da, 1.3, 2.3, col, M, arch=False)
    # "不该来的墙"：西墙上一块块小石牌（214 个名字 → 用 60 块小板示意）
    wall_dir = yaw + math.pi  # 短边朝西侧
    wp = Vector((x, y, 0)) - n * (sx / 2)
    rng = random.Random(214)
    for i in range(60):
        r_ = i // 10
        c_ = i % 10
        pos = wp + tv * ((c_ - 4.5) * 0.42) + Vector((0, 0, gz + 0.7 + r_ * 0.42))
        pl = box('HistoryHall_Name_%02d' % i, (0.04, 0.32, 0.3), pos - n * 0.02, col, M['stone_white'] if i > 2 else M['gold'], rot=(0, 0, yaw))
        objs.append(pl)
    # 窗
    for side in (-1, 1):
        pos = Vector((x, y, gz + 1.9)) + n * (side * sx / 2)
        objs += window('HistoryHall_Win_%d' % side, pos, yaw if side > 0 else yaw + math.pi, 0.7, 1.1, col, M, kind='square')
    objs += chimney('HistoryHall_Chimney', Vector((x, y, gz + 2.0)) + n * (sx * 0.3) + tv * (sy * 0.25), col, M, w=0.7, h=3.4)
    return objs
