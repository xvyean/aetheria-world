# -*- coding: utf-8 -*-
"""
星槎学院 · 四院塔
- 晨辉塔（东）：细高白塔 + 八柱金瓦火廊 + 铜盆火
- 星语塔 + 千岁梧桐（北）：六角矮塔贴树而建 + 观星台铜浑仪
- 锤音塔（南）：方石矮塔 + 炉口 + 砧形铜台烟囱 + 誓铁墙 + 旧阶堆
- 海心塔（西）：船形塔 + 长明灯 + 栈桥 + 渡船 + 浮池 + 云网 + 细瀑
"""
import bmesh
import math
import random
from mathutils import Vector, Matrix
from util import *
from parts import *
from buildings_core import subdivide
import layout as LY
import island as IS


# ================================================================== 晨辉塔
def build_dawn_tower(M, C):
    T = LY.DAWN_TOWER
    x, y = T['pos']
    r, h = T['r'], T['h']
    gz = IS.ground_h(x, y)
    col = C['dawn']
    objs = []
    # 基座：方形两级
    for i, (s, hh) in enumerate(((r * 2 + 3.0, 0.5), (r * 2 + 1.6, 0.5))):
        b = box_grid('DawnTower_Plinth_%d' % i, (s, s, hh), (x, y, gz + i * 0.5), col, M['stone_white'], cell=0.8)
        stone_vcol(b, PAL['stone_white'], seed=200 + i, grime=0.25)
        objs.append(b)
    z0 = gz + 1.0
    # 塔身：圆柱收分，三段，中间有金色环带
    segs = [(0.0, 8.0, 1.0), (8.3, 15.0, 0.93), (15.3, h, 0.86)]
    for i, (a, b, rf) in enumerate(segs):
        body = lathe('DawnTower_Body_%d' % i, [(r * (rf + 0.03), a), (r * rf, b)], 20, (x, y, z0), col, M['stone_white'], smooth=True)
        subdivide(body, 10)
        stone_vcol(body, PAL['stone_white'], seed=210 + i, course=0.58, grime=0.3 if i == 0 else 0.0, tint='#f6efdc')
        objs.append(body)
        band = lathe('DawnTower_Band_%d' % i, [(r * rf + 0.02, b), (r * rf + 0.22, b + 0.06), (r * rf + 0.22, b + 0.24), (r * rf + 0.02, b + 0.3)], 20, (x, y, z0), col, M['gold'], smooth=False)
        objs.append(band)
        # 窗：朝东为主（走廊永远朝东），每段东面一扇大窗、其他方向小窗
        za = z0 + (a + b) / 2
        for k in range(4):
            ang = TAU * k / 4
            rr = r * rf
            pos = Vector((x + math.cos(ang) * rr, y + math.sin(ang) * rr, za))
            if k == 0:
                objs += window('DawnTower_Win_%d_E' % i, pos, ang, 1.1, 2.6, col, M, kind='lancet')
            else:
                objs += window('DawnTower_Win_%d_%d' % (i, k), pos, ang, 0.55, 1.4, col, M, kind='lancet', sill=False)
    # 东侧外挑的"晨廊"：一道悬挑的小阳台，正对日出
    bal_z = z0 + 11.5
    bal = box('DawnTower_Balcony', (2.2, 3.2, 0.3), (x + r * 0.93 + 0.9, y, bal_z), col, M['stone_cream'])
    objs.append(bal)
    for i in range(3):
        cb = mesh_from('DawnTower_BalCorbel_%d' % i, [(0, -0.15, 0), (1.5, -0.15, 0), (0, -0.15, -1.2), (0, 0.15, 0), (1.5, 0.15, 0), (0, 0.15, -1.2)],
                       [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)], col, mat=M['stone_cream'])
        cb.location = (x + r * 0.93, y - 1.1 + i * 1.1, bal_z - 0.15)
        objs.append(cb)
    for i in range(7):
        objs.append(cylinder('DawnTower_BalBaluster_%d' % i, 0.06, 0.8, (x + r * 0.93 + 1.85, y - 1.45 + i * 0.48, bal_z + 0.15), col, M['stone_cream'], segments=6))
    objs.append(box('DawnTower_BalRail', (0.12, 3.2, 0.1), (x + r * 0.93 + 1.85, y, bal_z + 1.0), col, M['stone_cream']))
    # 塔顶：平台 + 八柱火廊
    top_z = z0 + h
    rt = r * 0.86
    plat = lathe('DawnTower_TopPlate', [(rt + 1.2, 0), (rt + 1.35, 0.3), (rt + 1.35, 0.55), (rt + 0.9, 0.55)], 20, (x, y, top_z), col, M['stone_cream'], smooth=False)
    objs.append(plat)
    objs += crenellation('DawnTower_Merlons', (x, y, top_z + 0.55), rt + 1.1, 16, col, M['stone_white'], h=0.5, t=0.28, n_per_side=1)
    pz = top_z + 0.55
    ph = 4.2
    for k in range(8):
        a = TAU * k / 8 + math.pi / 8
        objs += column('DawnTower_FireCol_%d' % k, (x + math.cos(a) * (rt - 0.1), y + math.sin(a) * (rt - 0.1), pz), col, M, r=0.24, h=ph, mat=M['stone_white'])
    # 金瓦顶（八角攒尖，略陡）+ 尖顶金球
    objs += pyramid_roof('DawnTower_Roof', rt + 0.1, 4.6, 8, (x, y, pz + ph + 0.3), col, M['tile_dawn'], overhang=0.7, phase=math.pi / 8, thick=0.16, finial_mat=M['gold'], finial_h=1.6)
    roof_vcol(objs[-2], PAL['tile_dawn'], seed=220, streak=0.08)
    ring = lathe('DawnTower_RoofBeam', [(rt + 0.2, 0), (rt + 0.2, 0.3), (rt - 0.5, 0.3), (rt - 0.5, 0)], 8, (x, y, pz + ph), col, M['wood_dark'], smooth=False, phase=math.pi / 8, close=False)
    objs.append(ring)
    # 铜盆 + 火
    basin = lathe('DawnTower_Basin', [(0.0, 0.0), (0.5, 0.0), (0.42, 0.8), (1.05, 1.15), (1.15, 1.3), (1.0, 1.32), (0.85, 1.1), (0.0, 0.95)], 16, (x, y, pz + 0.02), col, M['copper'], smooth=True)
    objs.append(basin)
    fire = lathe('FX_DawnFire', [(0.0, 0.0), (0.72, 0.15), (0.6, 0.6), (0.3, 1.2), (0.12, 1.7), (0.0, 2.1)], 10, (x, y, pz + 1.1), C['fx'], M['fire'], smooth=True)
    fire['fx'] = 'fire'
    objs.append(fire)
    glow = sphere('FX_DawnFireGlow', 0.45, (x, y, pz + 1.6), C['fx'], M['fire'], segs=8, rings=6)
    glow['fx'] = 'fire'
    objs.append(glow)
    # 门（朝西，接回廊）
    dp = Vector((x - r * 1.03, y, z0))
    objs += door('DawnTower_Door', dp, math.pi, 1.6, 3.0, col, M, arch=True, frame_mat=M['stone_cream'])
    objs += steps('DawnTower_Steps', Vector((x - (r + 1.5), y, gz)), math.pi, 3.0, 3, rise=0.33, tread=0.5, collection=col, mat=M['stone_white'])
    # 金色院旗
    objs += banner('DawnTower_Banner', Vector((x, y - r * 0.9 - 0.05, z0 + 7.6)), -math.pi / 2, 1.3, 3.2, col, M['cloth_dawn'], pole=True, pole_mat=M['wood_dark'], fx_coll=C['fx'])
    return objs


# ================================================================== 星语塔 + 千岁梧桐
def build_speak_tower(M, C):
    T = LY.SPEAK_TOWER
    S = LY.SYCAMORE
    x, y = T['pos']
    r, h, sides = T['r'], T['h'], T['sides']
    gz = IS.ground_h(x, y)
    col = C['speak']
    objs = []
    # 六角矮塔，塔身一半"贴"着树干（树在西侧）
    body = prism('SpeakTower_Body', r, h, sides, (x, y, gz), col, M['stone_cream'], taper=0.92, phase=0.0)
    subdivide(body, 6)
    stone_vcol(body, PAL['stone_cream'], seed=300, tint='#e8e6d0', grime=0.35, course=0.5)
    objs.append(body)
    # 爬藤（绿色顶点色带）：单独一层薄壳
    ivy = prism('SpeakTower_Ivy', r + 0.06, h * 0.75, sides, (x, y, gz), col, M['leaf'], taper=0.93, phase=0.0, cap=False)
    subdivide(ivy, 8)
    rng = random.Random(301)
    la, lb = hex2lin(PAL['leaf_a'])[:3], hex2lin(PAL['leaf_b'])[:3]

    def ivy_col(co, n):
        k = 0.5 + 0.5 * fbm(co.x / 0.8, co.y / 0.8, co.z / 0.8, oct=2, seed=17)
        return mix(la, lb, k)
    set_vcol(ivy, ivy_col)
    # 用顶点位移把藤壳打成不连续的"补丁"：把不该有藤的顶点缩回墙内
    me = ivy.data
    for v in me.vertices:
        m = fbm(v.co.x / 1.6 + x / 3, v.co.y / 1.6, v.co.z / 1.6, oct=3, seed=19)
        toward_tree = -v.co.x / (r + 0.06)  # 西侧（靠树）更多
        thresh = 0.05 - 0.3 * toward_tree + 0.35 * (v.co.z / h)
        if m < thresh:
            v.co *= 0.96
    me.update()
    objs.append(ivy)
    # 观星台：塔顶平台 + 六角矮栏 + 铜浑仪
    top = gz + h
    plat = prism('SpeakTower_TopPlate', r * 0.92 + 0.6, 0.4, sides, (x, y, top), col, M['stone_white'], phase=0.0)
    objs.append(plat)
    objs += parapet_ring('SpeakTower_Parapet', (x, y, top + 0.4), r * 0.92 + 0.6, sides, col, M['stone_cream'], h=0.9, t=0.25, phase=0.0)
    # 浑仪：三个正交铜环 + 轴，环上嵌月石（月影林地每年一枚，八百年一圈）
    az = top + 0.4 + 1.5
    R_arm = 1.15
    ring1 = torus('SpeakTower_Armillary_A', R_arm, 0.05, (x, y, az), col, M['patina'], segs=32, rsegs=6)
    ring2 = torus('SpeakTower_Armillary_B', R_arm * 0.85, 0.05, (x, y, az), col, M['patina'], segs=32, rsegs=6, rot=(math.pi / 2, 0, 0))
    ring3 = torus('SpeakTower_Armillary_C', R_arm * 0.72, 0.05, (x, y, az), col, M['copper'], segs=32, rsegs=6, rot=(math.pi / 2, 0, math.pi / 2))
    ring4 = torus('SpeakTower_Armillary_D', R_arm * 1.0, 0.04, (x, y, az), col, M['patina'], segs=32, rsegs=6, rot=(math.radians(23.5), 0, 0))
    objs += [ring1, ring2, ring3, ring4]
    ring1['fx'] = 'armillary'
    axis = cylinder('SpeakTower_ArmAxis', 0.06, R_arm * 2.5, (x, y, az - R_arm * 1.25), col, M['copper'], segments=8)
    axis.rotation_euler = (math.radians(23.5), 0, 0)
    axis.location = (x, y - math.sin(math.radians(23.5)) * 0, az)
    axis.matrix_world = Matrix.Translation((x, y, az)) @ Matrix.Rotation(math.radians(23.5), 4, 'X') @ Matrix.Translation((0, 0, -R_arm * 1.25))
    objs.append(axis)
    stand = lathe('SpeakTower_ArmStand', [(0.6, 0), (0.5, 0.15), (0.12, 0.3), (0.1, 1.5 - R_arm * 0.0)], 8, (x, y, top + 0.4), col, M['stone_dark'], smooth=False)
    objs.append(stand)
    # 月石：环上 24 颗小白珠
    for k in range(24):
        a = TAU * k / 24
        ms = ico('SpeakTower_Moonstone_%02d' % k, 0.055, (x + math.cos(a) * R_arm, y + math.sin(a) * R_arm, az), col, M['crystal'], subdiv=0)
        objs.append(ms)
    # 窗（尖窗，本院绿玻璃不用——玻璃还是暖光）
    for i, zz in enumerate((3.2, 7.4)):
        for k in range(sides):
            if k in (2, 3):
                continue  # 靠树面不开窗
            a = TAU * (k + 0.5) / sides
            rr = (r - (r - r * 0.92) * zz / h) * math.cos(math.pi / sides)
            pos = Vector((x + math.cos(a) * rr, y + math.sin(a) * rr, gz + zz))
            objs += window('SpeakTower_Win_%d_%d' % (i, k), pos, a, 0.6, 1.5, col, M, kind='lancet')
    # 门（朝南 → 回廊）
    face_r = r * math.cos(math.pi / sides)
    dp = Vector((x, y - face_r, gz))
    objs += door('SpeakTower_Door', dp, -math.pi / 2, 1.5, 2.8, col, M, arch=True, frame_mat=M['stone_white'])
    # 绿旗
    objs += banner('SpeakTower_Banner', Vector((x + face_r + 0.05, y, gz + h - 1.0)), 0.0, 1.2, 3.0, col, M['cloth_speak'], pole=True, pole_mat=M['wood_dark'], fx_coll=C['fx'])
    # ---------------- 千岁梧桐
    objs += build_sycamore(M, C, S['pos'][0], S['pos'][1], S['trunk_r'], S['h'], S['crown_r'])
    # 树下：石凳一圈（"树下不许喊"）
    for k in range(6):
        a = TAU * k / 6 + 0.3
        if abs(a - 0.0) < 0.6 or abs(a - TAU) < 0.6:
            continue
        rr = S['trunk_r'] + 2.6
        bx, by = S['pos'][0] + math.cos(a) * rr, S['pos'][1] + math.sin(a) * rr
        if math.hypot(bx - x, by - y) < r + 1.0:
            continue
        bench = box('Sycamore_Bench_%d' % k, (1.6, 0.45, 0.45), (bx, by, IS.ground_h(bx, by)), col, M['stone_grey'], rot=(0, 0, a + math.pi / 2), origin='bottom')
        objs.append(bench)
    return objs


def build_sycamore(M, C, x, y, trunk_r, h, crown_r):
    """千岁梧桐：树干（多段、有分枝）、主枝、叶团（多个椭球拼成大冠）、落叶。"""
    col = C['speak']
    gz = IS.ground_h(x, y)
    objs = []
    rng = random.Random(800)
    # 主干：带扭曲的放样
    prof = []
    n = 14
    trunk_h = h * 0.55
    for i in range(n + 1):
        t = i / n
        rr = trunk_r * (1.0 - 0.45 * t) * (1.0 + 0.08 * math.sin(t * 9.0))
        if i == 0:
            rr = trunk_r * 1.35  # 根部外扩
        prof.append((rr, t * trunk_h))
    trunk = lathe('Sycamore_Trunk', prof, 14, (x, y, gz - 0.3), col, M['bark_syc'], smooth=True)
    subdivide(trunk, 1)
    me = trunk.data
    for v in me.vertices:
        d = fbm(v.co.x / 0.6, v.co.y / 0.6, v.co.z / 0.9, oct=3, seed=23)
        v.co.x *= 1 + 0.12 * d
        v.co.y *= 1 + 0.12 * d
        # 轻微弯曲
        v.co.x += 0.35 * (v.co.z / trunk_h) ** 2
    me.update()
    smooth_by_angle(trunk, 45)
    ba, bb = hex2lin(PAL['bark_syc'])[:3], hex2lin('#7d7566')[:3]

    def bark_col(co, nrm):
        k = 0.5 + 0.5 * fbm(co.x / 0.5, co.y / 0.5, co.z / 0.5, oct=3, seed=29)
        # 梧桐斑驳：高频块状
        patch = smoothstep(0.45, 0.55, 0.5 + 0.5 * fbm(co.x / 0.35, co.y / 0.35, co.z / 0.6, oct=2, seed=31))
        c = mix(bb, ba, patch)
        return tuple(ci * (0.9 + 0.2 * k) for ci in c)
    set_vcol(trunk, bark_col)
    objs.append(trunk)
    # 根部隆起
    for k in range(7):
        a = TAU * k / 7 + rng.uniform(-0.2, 0.2)
        L = rng.uniform(1.6, 2.8)
        rt = tube('Sycamore_Root_%d' % k, [Vector((x + math.cos(a) * trunk_r * 0.8, y + math.sin(a) * trunk_r * 0.8, gz + 0.6)),
                                            Vector((x + math.cos(a) * (trunk_r + L * 0.5), y + math.sin(a) * (trunk_r + L * 0.5), gz + 0.1)),
                                            Vector((x + math.cos(a) * (trunk_r + L), y + math.sin(a) * (trunk_r + L), gz - 0.25))], 0.28, col, M['bark_syc'], segs=7)
        set_vcol(rt, bark_col)
        objs.append(rt)
    # 主枝：从 0.5h 到 0.85h 之间伸出 7 条，末端再分二叉
    top = gz - 0.3 + trunk_h
    branch_ends = []
    for k in range(7):
        a = TAU * k / 7 + rng.uniform(-0.25, 0.25)
        z0 = gz + trunk_h * rng.uniform(0.55, 0.95)
        L = crown_r * rng.uniform(0.55, 0.85)
        rise = rng.uniform(0.35, 0.6)
        p0 = Vector((x + 0.35 * ((z0 - gz) / trunk_h) ** 2, y, z0))
        p1 = p0 + Vector((math.cos(a) * L * 0.5, math.sin(a) * L * 0.5, L * rise * 0.5))
        p2 = p0 + Vector((math.cos(a) * L, math.sin(a) * L, L * rise))
        br = tube('Sycamore_Branch_%d' % k, [p0, p1, p2], 0.34, col, M['bark_syc'], segs=7)
        set_vcol(br, bark_col)
        objs.append(br)
        branch_ends.append(p2)
        # 二叉
        for j in range(2):
            a2 = a + (j - 0.5) * rng.uniform(0.6, 1.1)
            L2 = L * rng.uniform(0.35, 0.55)
            p3 = p2 + Vector((math.cos(a2) * L2, math.sin(a2) * L2, L2 * rng.uniform(0.3, 0.7)))
            br2 = tube('Sycamore_Twig_%d_%d' % (k, j), [p2, p3], 0.16, col, M['bark_syc'], segs=6)
            set_vcol(br2, bark_col)
            objs.append(br2)
            branch_ends.append(p3)
    # 树冠：多个椭球叶团
    la, lb = hex2lin(PAL['leaf_sycamore_a'])[:3], hex2lin(PAL['leaf_sycamore_b'])[:3]
    lc = hex2lin(PAL['leaf_a'])[:3]
    crown_c = Vector((x + 0.4, y, gz + trunk_h + crown_r * 0.3))
    blobs = [(crown_c, crown_r * 0.62, (1.0, 0.95, 0.55))]
    for p in branch_ends:
        blobs.append((p + Vector((0, 0, 0.4)), crown_r * rng.uniform(0.2, 0.3), (1.0, rng.uniform(0.85, 1.1), rng.uniform(0.55, 0.75))))
    for k in range(26):
        a = rng.uniform(0, TAU)
        rr = crown_r * rng.uniform(0.25, 0.95)
        zz = rng.uniform(-3.0, 4.0) * (1.0 - rr / crown_r * 0.5)
        blobs.append((crown_c + Vector((math.cos(a) * rr, math.sin(a) * rr, zz)), crown_r * rng.uniform(0.18, 0.32), (1.0, rng.uniform(0.85, 1.15), rng.uniform(0.5, 0.7))))
    for i, (c, rr, sc) in enumerate(blobs):
        b = ico('Sycamore_Leaves_%02d' % i, rr, c, col, M['leaf_syc'], subdiv=2, smooth=True)
        b.scale = sc
        me = b.data
        for v in me.vertices:
            n = v.co.normalized()
            d = fbm(n.x * 2.2, n.y * 2.2, n.z * 2.2, oct=3, seed=40 + i)
            d2 = ridged(n.x * 4.0, n.y * 4.0, n.z * 4.0, oct=2, seed=41 + i) - 1.0
            v.co *= 1 + 0.3 * d + 0.1 * d2
        me.update()
        smooth_by_angle(b, 40)
        top_z = c.z + rr * sc[2]

        def leaf_col(co, nrm, c=c, rr=rr, top_z=top_z):
            up = smoothstep(-0.5, 0.8, nrm.z)
            k = 0.5 + 0.5 * fbm(co.x / 2.0 + c.x, co.y / 2.0 + c.y, co.z / 2.0, oct=2, seed=45)
            base = mix(lc, la, up * 0.85)
            base = mix(base, lb, k * 0.35 * up)
            return tuple(b * 0.92 for b in base)
        set_vcol(b, leaf_col)
        b['fx'] = 'foliage'
        objs.append(b)
    # 落叶：树下地面撒一圈
    verts, faces = [], []
    for i in range(160):
        a = rng.uniform(0, TAU)
        rr = rng.uniform(1.5, crown_r * 1.2)
        px, py = x + math.cos(a) * rr, y + math.sin(a) * rr
        if math.hypot(px - LY.SPEAK_TOWER['pos'][0], py - LY.SPEAK_TOWER['pos'][1]) < LY.SPEAK_TOWER['r'] + 0.3:
            continue
        pz = IS.ground_h(px, py) + 0.03
        s = rng.uniform(0.18, 0.3)
        ang = rng.uniform(0, TAU)
        base = len(verts)
        for (u, v) in ((-1, -0.6), (1, -0.6), (1.1, 0.5), (0, 1), (-1.1, 0.5)):
            rx, ry = u * s, v * s
            verts.append((px + rx * math.cos(ang) - ry * math.sin(ang), py + rx * math.sin(ang) + ry * math.cos(ang), pz))
        faces.append((base, base + 1, base + 2, base + 3, base + 4))
    leaves = mesh_from('Sycamore_FallenLeaves', verts, faces, col, mat=M['leaf_syc'])
    lf = hex2lin(PAL['leaf_sycamore_b'])[:3]
    lg = hex2lin('#a5763a')[:3]
    rng2 = random.Random(9)
    per = {}

    def fl(co, n):
        key = (round(co.x, 1), round(co.y, 1))
        if key not in per:
            per[key] = rng2.random()
        return mix(lf, lg, per[key])
    set_vcol(leaves, fl)
    objs.append(leaves)
    return objs


# ================================================================== 锤音塔
def build_forge_tower(M, C):
    T = LY.FORGE_TOWER
    x, y = T['pos']
    w, h = T['w'], T['h']
    gz = IS.ground_h(x, y)
    col = C['forge']
    objs = []
    # 方石塔身：略收分（用 prism 4 边，phase=π/4 使边平行坐标轴）
    body = prism('ForgeTower_Body', w / 2 * math.sqrt(2), h, 4, (x, y, gz), col, M['stone_dark'], taper=0.9, phase=math.pi / 4)
    subdivide(body, 7)
    stone_vcol(body, PAL['stone_dark'], seed=400, course=0.7, grime=0.25, noise_amt=0.16, tint='#5a4e46')
    objs.append(body)
    # 角部铁箍
    for zz in (2.6, 5.6):
        for k in range(4):
            a = TAU * k / 4 + math.pi / 4
            rr = (w / 2 * math.sqrt(2)) * (1 - 0.1 * zz / h)
            band = box('ForgeTower_Band_%d_%d' % (int(zz), k), (0.5, 0.5, 0.35), (x + math.cos(a) * rr, y + math.sin(a) * rr, gz + zz), col, M['iron'], rot=(0, 0, a))
            objs.append(band)
    # 炉口（北面，朝广场）：一个比门宽的拱形洞 + 炉膛发光
    fw, fh = 3.2, 2.8
    fy = y + (w / 2) * 1.0
    # 洞口框：厚重石框
    frame_l = box_grid('ForgeTower_HearthJambL', (0.8, 0.9, fh + 0.4), (x - fw / 2 - 0.4, fy - 0.1, gz), col, M['basalt'], cell=0.5)
    frame_r = box_grid('ForgeTower_HearthJambR', (0.8, 0.9, fh + 0.4), (x + fw / 2 + 0.4, fy - 0.1, gz), col, M['basalt'], cell=0.5)
    lintel = box('ForgeTower_HearthLintel', (fw + 1.6, 0.9, 0.7), (x, fy - 0.1, gz + fh + 0.4 + 0.35), col, M['basalt'])
    for o in (frame_l, frame_r, lintel):
        set_vcol_const(o, PAL['basalt'], jitter=0.14, seed=401)
    objs += [frame_l, frame_r, lintel]
    arch = torus('ForgeTower_HearthArch', fw / 2 + 0.25, 0.3, (x, fy - 0.1, gz + fh + 0.1), col, M['basalt'], segs=20, rsegs=6, rot=(math.pi / 2, 0, 0))
    objs.append(arch)
    # 炉膛：内凹的发光腔
    cav = box('ForgeTower_HearthCavity', (fw - 0.2, 2.6, fh - 0.2), (x, fy - 1.3, gz + 0.1), col, M['basalt'], origin='bottom')
    objs.append(cav)
    coals = box('FX_ForgeCoals', (fw - 0.6, 2.2, 0.5), (x, fy - 1.3, gz + 0.15), C['fx'], M['fire'], origin='bottom')
    coals['fx'] = 'fire'
    objs.append(coals)
    fire = lathe('FX_ForgeFire', [(0.0, 0.0), (1.1, 0.2), (0.85, 0.9), (0.4, 1.6), (0.0, 2.1)], 10, (x, fy - 1.3, gz + 0.5), C['fx'], M['fire'], smooth=True)
    fire['fx'] = 'fire'
    objs.append(fire)
    # 砧形铜台 + 烟囱
    top = gz + h
    plat = box('ForgeTower_TopPlate', (w * 0.92, w * 0.92, 0.4), (x, y, top), col, M['stone_grey'], origin='bottom')
    objs.append(plat)
    # 砧：一个横放的砧体（用 lathe 造角，再用 box 造体）
    anvil_body = box('ForgeTower_AnvilBody', (4.6, 2.0, 1.2), (x, y, top + 0.4 + 0.6), col, M['copper'])
    anvil_horn = lathe('ForgeTower_AnvilHorn', [(0.9, 0), (0.5, 1.6), (0.0, 2.4)], 10, (0, 0, 0), col, M['copper'], smooth=True)
    anvil_horn.matrix_world = Matrix.Translation((x + 2.3, y, top + 0.4 + 0.8)) @ Matrix.Rotation(-math.pi / 2, 4, 'Y')
    anvil_foot = box('ForgeTower_AnvilFoot', (3.0, 1.6, 0.5), (x - 0.4, y, top + 0.4 + 0.25), col, M['patina'])
    objs += [anvil_body, anvil_horn, anvil_foot]
    chim = cylinder('ForgeTower_Chimney', 0.7, 4.2, (x - 1.0, y, top + 1.6), col, M['basalt'], segments=12, r_top=0.6)
    set_vcol_const(chim, PAL['basalt'], jitter=0.12, seed=402)
    objs.append(chim)
    objs.append(lathe('ForgeTower_ChimneyCap', [(0.9, 0), (0.95, 0.15), (0.5, 0.5)], 12, (x - 1.0, y, top + 5.8), col, M['iron'], smooth=False))
    # 烟：五团
    rng = random.Random(403)
    for i in range(6):
        rr = 0.55 + i * 0.28
        s = ico('FX_ForgeSmoke_%d' % i, rr, (x - 1.0 + rng.uniform(-0.4, 0.4) * i + i * 0.35, y + rng.uniform(-0.3, 0.3) * i, top + 6.6 + i * 1.15), C['fx'], M['smoke'], subdiv=1)
        s['fx'] = 'smoke'
        s['fx_i'] = i
        objs.append(s)
    # 誓铁墙：外墙（东、西两面）挂满巴掌大的铁片
    rng = random.Random(404)
    for face, (nx, ny) in (('E', (1, 0)), ('W', (-1, 0))):
        for i in range(90):
            zz = rng.uniform(0.8, h - 1.2)
            u = rng.uniform(-w / 2 + 0.5, w / 2 - 0.5)
            rr = (w / 2) * (1 - 0.1 * zz / h)
            px, py = x + nx * (rr + 0.06), y + u
            pl = box('ForgeTower_OathIron_%s_%02d' % (face, i), (0.05, rng.uniform(0.14, 0.22), rng.uniform(0.16, 0.26)), (px, py, gz + zz), col, M['iron'] if rng.random() > 0.15 else M['copper'])
            pl.rotation_euler = (rng.uniform(-0.15, 0.15), 0, rng.uniform(-0.1, 0.1))
            objs.append(pl)
        # 挂钩横杆
        for j in range(4):
            zz = 1.6 + j * 1.8
            rr = (w / 2) * (1 - 0.1 * zz / h)
            objs.append(box('ForgeTower_Rail_%s_%d' % (face, j), (0.05, w - 0.8, 0.05), (x + nx * (rr + 0.02), y, gz + zz), col, M['iron']))
    # 窗（南面两扇小方窗；东西各一）
    for (ang, zz) in ((-math.pi / 2, 3.5), (-math.pi / 2, 6.5), (0, 5.0), (math.pi, 5.0)):
        rr = (w / 2) * (1 - 0.1 * zz / h)
        pos = Vector((x + math.cos(ang) * rr, y + math.sin(ang) * rr, gz + zz))
        objs += window('ForgeTower_Win_%d_%d' % (int(math.degrees(ang)), int(zz)), pos, ang, 0.7, 0.9, col, M, kind='square')
    # 铜旗
    objs += banner('ForgeTower_Banner', Vector((x - w / 2 - 0.05, y - 1.0, gz + h - 0.6)), math.pi, 1.2, 3.0, col, M['cloth_forge'], pole=True, pole_mat=M['wood_dark'], fx_coll=C['fx'])
    # ---------------- 旧阶堆：八百块换下来的台阶堆成小山
    O = LY.OLD_STEPS
    ox, oy = O['pos']
    ogz = IS.ground_h(ox, oy)
    rng = random.Random(405)
    n = 0
    verts, faces = [], []
    layers = 9
    for L in range(layers):
        rr = O['r'] * (1 - L / layers) + 0.5
        cnt = max(3, int(rr * 5))
        for i in range(cnt):
            a = TAU * i / cnt + L * 0.3 + rng.uniform(-0.2, 0.2)
            d = rng.uniform(0, rr)
            px, py = ox + math.cos(a) * d, oy + math.sin(a) * d
            pz = ogz + L * 0.24 + rng.uniform(0, 0.05)
            ang = rng.uniform(0, TAU)
            sx, sy, sz = 1.05 + rng.uniform(-0.1, 0.1), 0.32, 0.2
            base = len(verts)
            c, s = math.cos(ang), math.sin(ang)
            for dz in (0, sz):
                for (ex, ey) in ((-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2)):
                    verts.append((px + ex * c - ey * s, py + ex * s + ey * c, pz + dz))
            faces += [(base + 4, base + 5, base + 6, base + 7), (base + 3, base + 2, base + 1, base + 0),
                      (base + 0, base + 1, base + 5, base + 4), (base + 1, base + 2, base + 6, base + 5),
                      (base + 2, base + 3, base + 7, base + 6), (base + 3, base + 0, base + 4, base + 7)]
            n += 1
    pile = mesh_from('OldSteps_Pile', verts, faces, col, mat=M['stone_grey'])
    sg = hex2lin(PAL['stone_grey'])[:3]
    per = {}
    rng2 = random.Random(406)

    def f(co, nrm):
        key = (round(co.x * 2), round(co.y * 2), round(co.z * 4))
        if key not in per:
            per[key] = 0.7 + rng2.random() * 0.5
        j = per[key]
        return (sg[0] * j, sg[1] * j, sg[2] * j)
    set_vcol(pile, f)
    pile['lore'] = '旧阶堆：八百年换下来的台阶'
    objs.append(pile)
    return objs


# ================================================================== 海心塔 · 栈桥 · 渡船 · 浮池 · 云网
def build_tide_tower(M, C):
    T = LY.TIDE_TOWER
    x, y = T['pos']
    L, W, h = T['L'], T['W'], T['h']
    gz = IS.ground_h(x, y)
    col = C['tide']
    objs = []
    # 船形平面：由一圈顶点（船头朝西）放样，墙微微外鼓
    def hull_ring(z, bulge):
        pts = []
        n = 28
        for i in range(n):
            t = i / n
            a = TAU * t
            # 船形：椭圆 + 西端收尖
            u = math.cos(a)
            v = math.sin(a)
            px = u * L / 2
            py = v * W / 2 * (1 - 0.45 * max(0.0, -u) ** 2)  # 西侧（-x）收尖
            if u < 0:
                px = u * L / 2 * 1.08
            pts.append(Vector((x + px * bulge, y + py * bulge, z)))
        return pts
    rings = [hull_ring(gz, 1.0), hull_ring(gz + h * 0.35, 1.06), hull_ring(gz + h * 0.7, 1.05), hull_ring(gz + h, 0.98)]
    body = ring_surface('TideTower_Body', rings, col, mat=M['stone_white'], cap_top=True, cap_bottom=True)
    subdivide(body, 7)
    smooth_by_angle(body, 30)
    stone_vcol(body, PAL['stone_white'], seed=500, tint='#dfe3e2', course=0.6, grime=0.35)
    objs.append(body)
    # 船舷线：两道深色水平带（像船的水线）
    for zz, tk in ((h * 0.28, 0.25), (h * 0.62, 0.18)):
        r1 = hull_ring(gz + zz, 1.065)
        r2 = hull_ring(gz + zz + tk, 1.065)
        band = ring_surface('TideTower_Strake_%d' % int(zz), [r1, r2], col, mat=M['slate'], cap_top=False, cap_bottom=False)
        set_vcol_const(band, PAL['slate'], jitter=0.08, seed=501)
        objs.append(band)
    # 塔顶：平台 + 灯室（八角玻璃）+ 长明灯
    top = gz + h
    plat = ring_surface('TideTower_TopPlate', [hull_ring(top, 1.06), hull_ring(top + 0.4, 1.06)], col, mat=M['stone_cream'], cap_top=True, cap_bottom=False)
    objs.append(plat)
    # 矮栏
    rail_pts = hull_ring(top + 0.4, 1.0)
    for i, p in enumerate(rail_pts):
        if i % 2 == 0:
            objs.append(cylinder('TideTower_Baluster_%02d' % i, 0.06, 0.85, p, col, M['stone_cream'], segments=6))
    objs.append(tube('TideTower_Handrail', [p + Vector((0, 0, 0.85)) for p in rail_pts], 0.06, col, M['wood_dark'], segs=6, closed=True))
    # 灯室
    lz = top + 0.4
    lamp_r = 1.6
    lamp_h = 3.0
    objs.append(lathe('TideTower_LampBase', [(lamp_r + 0.3, 0), (lamp_r + 0.3, 0.3), (lamp_r, 0.3)], 8, (x - 1.0, y, lz), col, M['stone_cream'], smooth=False, phase=math.pi / 8))
    for k in range(8):
        a = TAU * k / 8 + math.pi / 8
        objs.append(cylinder('TideTower_LampMullion_%d' % k, 0.09, lamp_h, (x - 1.0 + math.cos(a) * lamp_r, y + math.sin(a) * lamp_r, lz + 0.3), col, M['iron'], segments=6))
    glass = prism('TideTower_LampGlass', lamp_r - 0.02, lamp_h, 8, (x - 1.0, y, lz + 0.3), col, M['window'], phase=math.pi / 8)
    glass['fx'] = 'lamp'
    objs.append(glass)
    flame = lathe('FX_TideLamp', [(0.0, 0), (0.6, 0.1), (0.5, 0.9), (0.2, 1.6), (0.0, 2.0)], 10, (x - 1.0, y, lz + 0.6), C['fx'], M['lamp'], smooth=True)
    flame['fx'] = 'lamp_main'
    objs.append(flame)
    objs += pyramid_roof('TideTower_LampRoof', lamp_r + 0.1, 1.6, 8, (x - 1.0, y, lz + 0.3 + lamp_h), col, M['tile_tide'], overhang=0.4, phase=math.pi / 8, thick=0.12, finial_mat=M['copper'], finial_h=0.9)
    roof_vcol(objs[-2], PAL['tile_tide'], seed=502)
    # 窗：舷窗（圆）两排
    for i, zz in enumerate((3.4, 7.2, 10.6)):
        for k in range(10):
            a = TAU * k / 10 + i * 0.31
            u, v = math.cos(a), math.sin(a)
            px = u * L / 2 * (1.08 if u < 0 else 1.0)
            py = v * W / 2 * (1 - 0.45 * max(0.0, -u) ** 2)
            bulge = 1.06 if zz < h * 0.7 else 1.02
            pos = Vector((x + px * bulge, y + py * bulge, gz + zz))
            nrm = math.atan2(py * (L / W) ** 2 * 0 + py, px * (W / L) ** 2 * 0 + px)
            nrm = math.atan2(py / (W / 2) ** 2, px / (L / 2) ** 2)
            if abs(math.atan2(math.sin(nrm), math.cos(nrm))) < 0.5 and i == 0:
                continue  # 东侧门
            objs += window('TideTower_Port_%d_%02d' % (i, k), pos, nrm, 0.75, 0.75, col, M, kind='round', frame_mat=M['copper'])
    # 门（东，接回廊）
    dp = Vector((x + L / 2 * 1.0, y, gz))
    objs += door('TideTower_Door', dp, 0.0, 1.5, 2.8, col, M, arch=True, frame_mat=M['stone_cream'])
    # 蓝旗
    objs += banner('TideTower_Banner', Vector((x, y + W / 2 * 1.05 + 0.05, gz + h - 1.6)), math.pi / 2, 1.2, 3.0, col, M['cloth_tide'], pole=True, pole_mat=M['wood_dark'], fx_coll=C['fx'])
    # 西侧门（通栈桥）
    dpw = Vector((x - L / 2 * 1.08, y, gz))
    objs += door('TideTower_DoorW', dpw, math.pi, 1.4, 2.6, col, M, arch=True, frame_mat=M['stone_cream'])
    # ---------------- 栈桥
    objs += build_pier(M, C)
    # ---------------- 浮池 + 云网 + 细瀑
    objs += build_pool(M, C)
    return objs


def build_pier(M, C):
    P = LY.PIER
    col = C['tide']
    objs = []
    x0, x1, y, w = P['x0'], P['x1'], P['y'], P['w']
    z = IS.ground_h(x0, y) + 0.2
    n = int((x0 - x1) / 0.55)
    rng = random.Random(600)
    verts, faces = [], []
    for i in range(n):
        px0 = x0 - i * 0.55
        px1 = px0 - 0.5
        zz = z + rng.uniform(-0.015, 0.015) - (i / n) ** 2 * 0.35  # 末端略下垂
        base = len(verts)
        for (xx, yy) in ((px0, y - w / 2), (px1, y - w / 2), (px1, y + w / 2), (px0, y + w / 2)):
            verts.append((xx, yy, zz - 0.08))
        for (xx, yy) in ((px0, y - w / 2), (px1, y - w / 2), (px1, y + w / 2), (px0, y + w / 2)):
            verts.append((xx, yy, zz))
        faces += [(base + 4, base + 5, base + 6, base + 7), (base + 3, base + 2, base + 1, base + 0),
                  (base + 0, base + 1, base + 5, base + 4), (base + 1, base + 2, base + 6, base + 5),
                  (base + 2, base + 3, base + 7, base + 6), (base + 3, base + 0, base + 4, base + 7)]
    deck = mesh_from('Pier_Deck', verts, faces, col, mat=M['wood_mid'])
    wm = hex2lin(PAL['wood_mid'])[:3]
    per = {}
    rng2 = random.Random(601)

    def f(co, nrm):
        key = round(co.x / 0.55)
        if key not in per:
            per[key] = 0.75 + rng2.random() * 0.5
        j = per[key]
        # 越往外越灰白（盐渍）
        salt = smoothstep(x0, x1, co.x) * 0.35
        c = mix(wm, hex2lin('#b9b2a2')[:3], salt)
        return (c[0] * j, c[1] * j, c[2] * j)
    set_vcol(deck, f)
    objs.append(deck)
    # 纵梁
    for side in (-1, 1):
        objs.append(box('Pier_Stringer_%d' % side, (x0 - x1 + 0.5, 0.2, 0.3), ((x0 + x1) / 2, y + side * (w / 2 - 0.2), z - 0.25), col, M['wood_dark']))
    # 斜撑：从岛崖伸出的木斜撑（前 1/3 段），之后悬空
    for i in range(4):
        px = x0 - 1.5 - i * 2.4
        for side in (-1, 1):
            p0 = Vector((x0 + 0.6, y + side * (w / 2 - 0.3), z - 3.5 - i * 0.8))
            p1 = Vector((px, y + side * (w / 2 - 0.3), z - 0.4))
            objs.append(tube('Pier_Brace_%d_%d' % (i, side), [p0, p1], 0.12, col, M['wood_dark'], segs=6))
    # 栏杆（两侧）+ 铜钉
    for side in (-1, 1):
        pts = []
        for i in range(0, n, 4):
            px = x0 - i * 0.55
            zz = z - (i / n) ** 2 * 0.35
            p = Vector((px, y + side * (w / 2 - 0.12), zz))
            pts.append(p + Vector((0, 0, 1.0)))
            objs.append(cylinder('Pier_Post_%d_%02d' % (side, i), 0.07, 1.0, p, col, M['wood_dark'], segments=6))
        objs.append(tube('Pier_Rail_%d' % side, pts, 0.05, col, M['wood_dark'], segs=6))
    # 末端：系缆桩 + 灯柱 + 栈桥尽头的两根黑羽毛
    end = Vector((x1 + 0.4, y, z - 0.35))
    for side in (-1, 1):
        objs.append(cylinder('Pier_Bollard_%d' % side, 0.16, 0.7, end + Vector((0.6, side * (w / 2 - 0.4), 0)), col, M['wood_dark'], segments=8, r_top=0.14))
    objs += lantern_post('Pier_EndLamp', end + Vector((0.3, w / 2 - 0.25, 0)), col, M, h=2.2, glow_coll=C['fx'])
    for i in range(2):
        fe = mesh_from('Pier_Feather_%d' % i, [(-0.02, 0, 0), (0.02, 0, 0), (0.05, 0.28, 0.06), (0.0, 0.42, 0.1), (-0.05, 0.28, 0.06)], [(0, 1, 2, 3, 4)], col, mat=M['feather'])
        fe.location = end + Vector((0.2 + i * 0.25, -0.35 + i * 0.12, 0.02))
        fe.rotation_euler = (0.15, 0, 0.6 + i * 0.5)
        fe['lore'] = '暮影领的羽毛，今年两根'
        objs.append(fe)
    # 渡船 "第二块石头"
    objs += build_ferry(M, C)
    return objs


def build_ferry(M, C):
    F = LY.FERRY
    fx, fy, fz = F['pos']
    s = F['size']
    col = C['tide']
    objs = []
    # 平底方筏：厚板 + 四周挡板 + 桅杆 + 灯
    hull = box_grid('Ferry_Hull', (s, s * 0.75, 0.5), (fx, fy, fz), col, M['wood_mid'], cell=0.6)
    wood_vcol(hull, PAL['wood_mid'], seed=700)
    objs.append(hull)
    for side, axis in ((-1, 'x'), (1, 'x'), (-1, 'y'), (1, 'y')):
        if axis == 'x':
            objs.append(box('Ferry_Gunwale_x%d' % side, (0.15, s * 0.75, 0.6), (fx + side * (s / 2 - 0.08), fy, fz + 0.5), col, M['wood_dark'], origin='bottom'))
        else:
            objs.append(box('Ferry_Gunwale_y%d' % side, (s, 0.15, 0.6), (fx, fy + side * (s * 0.75 / 2 - 0.08), fz + 0.5), col, M['wood_dark'], origin='bottom'))
    mast = cylinder('Ferry_Mast', 0.12, 5.5, (fx, fy, fz + 0.5), col, M['wood_dark'], segments=8, r_top=0.08)
    objs.append(mast)
    objs += hanging_lamp('Ferry_Lamp', (fx + 0.4, fy, fz + 5.2), col, M, glow_coll=C['fx'], r=0.2)
    arm = box('Ferry_LampArm', (0.8, 0.06, 0.06), (fx + 0.4, fy, fz + 5.75), col, M['wood_dark'])
    objs.append(arm)
    # 底下的浮岩（渡船其实是踩着一块石头在光里漂）
    stone = ico('Ferry_Stone', s * 0.42, (fx, fy, fz - 1.2), col, M['rock'], subdiv=1, smooth=False)
    stone.scale = (1.0, 0.8, 0.55)
    set_vcol_const(stone, PAL['rock_a'], jitter=0.2, seed=701)
    objs.append(stone)
    # 船上：一袋袋面粉 + 一头驴（简化体块）+ 灰叔（半身人，小个子）
    rng = random.Random(702)
    for i in range(5):
        sack = ico('Ferry_Sack_%d' % i, 0.42, (fx - 1.4 + (i % 3) * 0.75, fy + 0.9 - (i // 3) * 0.7, fz + 0.9), col, M['paper'], subdiv=1)
        sack.scale = (1.0, 0.8, 0.75)
        objs.append(sack)
    objs += build_figure('Ferry_GreyUncle', (fx + 1.6, fy - 0.2, fz + 0.5), 1.05, M, col, cloak='#8e8a86', yaw=math.pi)
    objs += build_donkey('Ferry_Donkey', (fx + 0.2, fy - 1.3, fz + 0.5), M, col, yaw=0.3)
    for o in objs:
        if o is not None:
            o['fx'] = 'ferry'
    return objs


def build_pool(M, C):
    P = LY.POOL
    x, y = P['pos']
    r = P['r']
    gz = IS.ground_h(x, y)
    col = C['tide']
    objs = []
    # 池沿：矮石环
    rim = lathe('Pool_Rim', [(r + 0.6, 0), (r + 0.6, 0.45), (r - 0.05, 0.45), (r - 0.05, 0.1)], 28, (x, y, gz), col, M['stone_grey'], smooth=True, close=False)
    smooth_by_angle(rim, 30)
    set_vcol_const(rim, PAL['stone_grey'], jitter=0.1, seed=650)
    objs.append(rim)
    # 水面：高出池沿一掌（0.15），中央微微隆起
    water = lathe('FX_PoolWater', [(0.0, 0.62), (r * 0.5, 0.6), (r * 0.9, 0.58), (r + 0.05, 0.52), (r + 0.1, 0.45)], 28, (x, y, gz), C['fx'], M['water'], smooth=True)
    water['fx'] = 'water'
    objs.append(water)
    # 溢流细瀑：从岛沿外侧落下、半空散开
    th = math.atan2(y, x)
    R = IS.island_radius(th)
    ex, ey = math.cos(th) * (R + 0.4), math.sin(th) * (R + 0.4)
    ez = IS.ground_h(math.cos(th) * (R - 0.5), math.sin(th) * (R - 0.5))
    # 溢流槽：从池沿到岛沿的石槽
    d = math.hypot(ex - x, ey - y)
    ch = box('Pool_Spillway', (d - r - 0.2, 0.7, 0.25), ((x + ex) / 2 + math.cos(th) * r / 2, (y + ey) / 2 + math.sin(th) * r / 2, gz + 0.35), col, M['stone_grey'], rot=(0, 0, th))
    ch.location = (x + math.cos(th) * (r + (d - r) / 2), y + math.sin(th) * (r + (d - r) / 2), gz + 0.3)
    objs.append(ch)
    wf_pts = [Vector((x + math.cos(th) * (r + 0.3), y + math.sin(th) * (r + 0.3), gz + 0.55)),
              Vector((ex, ey, ez - 0.2)),
              Vector((ex + math.cos(th) * 0.8, ey + math.sin(th) * 0.8, ez - 3.0)),
              Vector((ex + math.cos(th) * 1.6, ey + math.sin(th) * 1.6, ez - 7.5)),
              Vector((ex + math.cos(th) * 2.6, ey + math.sin(th) * 2.6, ez - 13.0))]
    wf = tube('FX_Waterfall', wf_pts, 0.28, C['fx'], M['waterfall'], segs=8)
    # 尾端变粗、变淡（散开）
    me = wf.data
    n_ring = 8
    for i, v in enumerate(me.vertices):
        k = i // n_ring
        t = k / (len(wf_pts) - 1)
        c = Vector(wf_pts[k])
        v.co = c + (v.co - c) * (1 + 3.5 * t ** 2)
    me.update()
    wf['fx'] = 'waterfall'
    objs.append(wf)
    # 水雾团
    for i in range(3):
        m = ico('FX_Mist_%d' % i, 1.0 + i * 0.5, wf_pts[-1] + Vector((math.cos(th) * i * 0.8, math.sin(th) * i * 0.8, -i * 1.2)), C['fx'], M['smoke'], subdiv=1)
        m['fx'] = 'mist'
        m['fx_i'] = i
        objs.append(m)
    # 云网：西侧岛沿三根杆子撑起的一张网 + 竹槽引水到池
    N = LY.CLOUD_NET
    nx, ny = N['pos']
    ngz = IS.ground_h(nx, ny)
    poles = []
    for i, (dx, dy) in enumerate(((0, -3.2), (0, 0), (0, 3.2))):
        px, py = nx + dx, ny + dy
        pz = IS.ground_h(px, py)
        ph = 5.2 + (1 if i == 1 else 0)
        objs.append(cylinder('CloudNet_Pole_%d' % i, 0.09, ph, (px, py, pz), col, M['wood_dark'], segments=6, r_top=0.06))
        poles.append(Vector((px, py, pz + ph)))
    # 网：四边形网格，中间下垂
    verts, faces = [], []
    rows, cols_ = 5, 10
    for i in range(rows + 1):
        v = i / rows
        for j in range(cols_ + 1):
            u = j / cols_
            top = poles[0].lerp(poles[2], u)
            top.z = poles[0].z + (poles[1].z - poles[0].z) * math.sin(u * math.pi)
            sag = 0.8 * math.sin(u * math.pi) * (1 - v) * v * 4
            p = Vector((top.x, top.y, top.z - v * 3.6 - sag))
            p.x -= (1 - v) * 0.5  # 网面向西倾
            verts.append(p)
    for i in range(rows):
        for j in range(cols_):
            a = i * (cols_ + 1) + j
            faces.append((a, a + 1, a + cols_ + 2, a + cols_ + 1))
    net = mesh_from('CloudNet_Net', verts, faces, col, mat=M['net'], smooth=True)
    net['fx'] = 'net'
    objs.append(net)
    # 竹槽：从网底到池沿
    g0 = Vector((nx + 0.3, ny, ngz + 1.6))
    g1 = Vector((x + math.cos(math.atan2(ny - y, nx - x)) * (r + 0.4), y + math.sin(math.atan2(ny - y, nx - x)) * (r + 0.4), gz + 0.75))
    gutter = tube('CloudNet_Gutter', [g0, g0.lerp(g1, 0.5) + Vector((0, 0, -0.1)), g1], 0.12, col, M['wood_light'], segs=6)
    objs.append(gutter)
    for i, t in enumerate((0.25, 0.6)):
        p = g0.lerp(g1, t)
        pz = IS.ground_h(p.x, p.y)
        objs.append(cylinder('CloudNet_GutterPost_%d' % i, 0.05, p.z - pz - 0.12, (p.x, p.y, pz), col, M['wood_dark'], segments=6))
    # 池边练水形的学生（两个）
    objs += build_figure('Pool_Student_A', (x + r + 1.0, y + 1.2, gz), 1.6, M, col, cloak=PAL['cloth_tide'], yaw=math.atan2(-1.2, -r - 1.0))
    objs += build_figure('Pool_Student_B', (x - 0.8, y + r + 1.1, gz), 1.5, M, col, cloak=PAL['cloth_tide'], yaw=-math.pi / 2)
    # 池上悬着的水球（练水形的成果）
    for i in range(3):
        a = TAU * i / 3
        wb = sphere('FX_WaterOrb_%d' % i, 0.22 + i * 0.06, (x + math.cos(a) * r * 0.45, y + math.sin(a) * r * 0.45, gz + 1.4 + i * 0.4), C['fx'], M['water'], segs=10, rings=8)
        wb['fx'] = 'orb'
        wb['fx_i'] = i
        objs.append(wb)
    return objs


# ================================================================== 人物 / 动物（低模）
def build_figure(name, loc, h, M, col, cloak='#8e8a86', yaw=0.0, skin='#d9b48c'):
    """低模人物：斗篷体 + 头 + 兜帽，高度 h。"""
    x, y, z = loc
    objs = []
    cm = principled('Cloak_' + cloak.strip('#'), cloak, rough=0.9, sheen=0.3)
    body = lathe(name + '_Body', [(h * 0.2, 0), (h * 0.19, h * 0.15), (h * 0.14, h * 0.55), (h * 0.11, h * 0.75), (0.0, h * 0.8)], 10, (x, y, z), col, cm, smooth=True)
    objs.append(body)
    sm = principled('Skin_' + skin.strip('#'), skin, rough=0.7)
    head = sphere(name + '_Head', h * 0.085, (x, y, z + h * 0.86), col, sm, segs=10, rings=8)
    objs.append(head)
    hood = lathe(name + '_Hood', [(h * 0.11, 0), (h * 0.105, h * 0.09), (h * 0.06, h * 0.15), (0.0, h * 0.165)], 10, (x, y, z + h * 0.8), col, cm, smooth=True)
    objs.append(hood)
    for o in objs:
        o.rotation_euler = (0, 0, yaw)
    return objs


def build_donkey(name, loc, M, col, yaw=0.0):
    x, y, z = loc
    dm = principled('Donkey', '#7a6a5c', rough=0.9)
    objs = []
    body = sphere(name + '_Body', 0.55, (0, 0, 1.0), col, dm, segs=10, rings=8, scale=(1.6, 1.0, 0.95))
    head = sphere(name + '_Head', 0.28, (0.95, 0, 1.35), col, dm, segs=8, rings=6, scale=(1.5, 0.9, 0.9))
    neck = tube(name + '_Neck', [Vector((0.6, 0, 1.2)), Vector((0.85, 0, 1.4))], 0.2, col, dm, segs=6)
    objs += [body, head, neck]
    for i, (dx, dy) in enumerate(((-0.5, -0.3), (-0.5, 0.3), (0.5, -0.3), (0.5, 0.3))):
        objs.append(cylinder(name + '_Leg_%d' % i, 0.09, 0.85, (dx, dy, 0.0), col, dm, segments=6))
    for side in (-1, 1):
        ear = lathe(name + '_Ear_%d' % side, [(0.07, 0), (0.05, 0.25), (0.0, 0.32)], 6, (1.05, side * 0.18, 1.6), col, dm, smooth=False)
        ear.rotation_euler = (side * -0.4, 0.3, 0)
        objs.append(ear)
    for o in objs:
        o.matrix_world = Matrix.Translation((x, y, z)) @ Matrix.Rotation(yaw, 4, 'Z') @ o.matrix_world
    return objs


def build_goat(name, loc, M, col, yaw=0.0):
    x, y, z = loc
    objs = []
    body = sphere(name + '_Body', 0.34, (0, 0, 0.62), col, M['goat'], segs=10, rings=8, scale=(1.5, 0.9, 0.9))
    head = sphere(name + '_Head', 0.17, (0.6, 0, 0.85), col, M['goat'], segs=8, rings=6, scale=(1.4, 0.8, 0.85))
    objs += [body, head]
    for i, (dx, dy) in enumerate(((-0.3, -0.2), (-0.3, 0.2), (0.3, -0.2), (0.3, 0.2))):
        objs.append(cylinder(name + '_Leg_%d' % i, 0.05, 0.5, (dx, dy, 0.0), col, M['goat'], segments=6))
    for side in (-1, 1):
        horn = lathe(name + '_Horn_%d' % side, [(0.04, 0), (0.025, 0.2), (0.0, 0.3)], 6, (0.62, side * 0.1, 1.0), col, M['stone_dark'], smooth=False)
        horn.rotation_euler = (side * 0.3, -0.7, 0)
        objs.append(horn)
    for o in objs:
        o.matrix_world = Matrix.Translation((x, y, z)) @ Matrix.Rotation(yaw, 4, 'Z') @ o.matrix_world
    return objs
