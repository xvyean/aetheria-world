# -*- coding: utf-8 -*-
"""Z01 星陨塔：八角三收塔 + 观星环廊 + 开缝铜穹 + 裂隙晶。"""
import math
from math import pi, radians as D, cos, sin
from .. import geo, layout, util

CK = 'Z01_TWR'
FACE_A = [45 + 45 * f for f in range(8)]   # 八角面心方位（deg）

def build(M):
    objs = []
    sand, white = M('plaster'), M('white_smooth')
    slate, cptr, gold = M('slate'), M('cuprite'), M('gold')
    glow, crystal, black = M('window'), M('crystal'), M('blackstone')

    # ---- 台基（两级八角） ----
    objs.append(geo.ngon('TWR_base1', 8, 5.3, 0.7, white, loc=(0, 0, 0.35), ckey=CK, phase=pi / 8))
    objs.append(geo.ngon('TWR_base2', 8, 4.65, 0.7, white, loc=(0, 0, 0.95), ckey=CK, phase=pi / 8))
    # 塔门（正南 +Y = 90°）
    objs += geo.arch_portal('TWR_door', 1.7, 3.4, 0.9, white, CK, loc=(0, 3.9, 1.3),
                            pane=M('darkboard'))
    objs += geo.carve_band('TWR_doorlintel', 2.4, white, CK, loc=(0, 4.15, 4.95), h=0.3)

    # ---- 下段（高12 r4） ----
    objs.append(geo.ngon('TWR_low', 8, 4.0, 12, sand, loc=(0, 0, 1.3 + 6), ckey=CK, phase=pi / 8))
    for i in range(16):   # 束柱（棱线）
        a = pi / 8 + i * pi / 4
        x, y = cos(a) * 3.95, sin(a) * 3.95
        objs.append(geo.box(f'TWR_pil{i}', 0.16, 0.22, 11.8, white, ckey=CK,
                            loc=(x, y, 1.35 + 5.9), rot=(0, 0, a + pi / 2)))
    for f, adeg in enumerate(FACE_A):
        a = D(adeg)
        cx, cy = cos(a) * 3.97, sin(a) * 3.97
        rotz = a - pi / 2
        if abs(adeg - 90) < 3:   # 南面（塔门面）：上半开拱窗+圆窗
            objs += geo.win_arch(f'TWR_lw{f}', 0.95, 2.2, white, glow, CK, loc=(cx, cy, 8.6), rot=(0, 0, rotz), frame=0.12)
            objs += geo.win_round(f'TWR_up{f}', 0.42, gold, glow, CK, loc=(cx, cy, 11.4), rot=(0, 0, rotz))
        else:
            objs += geo.win_arch(f'TWR_lw{f}', 0.95, 2.2, white, glow, CK, loc=(cx, cy, 4.6), rot=(0, 0, rotz), frame=0.12)
            objs += geo.win_round(f'TWR_up{f}', 0.42, gold, glow, CK, loc=(cx, cy, 8.0), rot=(0, 0, rotz))
    objs.append(geo.ngon('TWR_eave1', 8, 4.6, 0.5, white, loc=(0, 0, 13.55), ckey=CK, phase=pi / 8))

    # ---- 中段（高9 r3.1）+ 观星环廊 ----
    objs.append(geo.ngon('TWR_mid', 8, 3.1, 9, sand, loc=(0, 0, 14.05 + 4.5), ckey=CK, phase=pi / 8))
    objs.append(geo.ngon('TWR_walk', 32, 4.0, 0.22, white, loc=(0, 0, 14.05), ckey=CK))
    for i in range(24):
        a = 2 * pi * i / 24
        x, y = cos(a) * 3.95, sin(a) * 3.95
        objs.append(geo.box(f'TWR_wp{i}', 0.09, 0.09, 1.0, white, ckey=CK, loc=(x, y, 14.65)))
    objs.append(geo.ring_tube('TWR_wrail', 3.95, 0.05, white, (0, 0, 15.15), CK, n=32, m=6))
    for f, adeg in enumerate(FACE_A):
        a = D(adeg)
        cx, cy = cos(a) * 3.07, sin(a) * 3.07
        rotz = a - pi / 2
        if abs(adeg - 90) < 3:   # 南面第三层：被砌死的门（塔中塔）
            objs.append(geo.box('TWR_sealframe', 1.35, 0.4, 2.6, M('rock'), ckey=CK, loc=(0, 3.02, 16.1)))
            objs.append(geo.box('TWR_sealplate', 0.95, 0.12, 2.05, black, ckey=CK, loc=(0, 3.12, 16.05)))
            objs.append(geo.carve_band('TWR_sealline', 1.1, M('rock'), CK, loc=(0, 3.16, 17.05), h=0.14, n=6))
            objs += geo.win_arch(f'TWR_mw{f}', 0.9, 2.2, white, glow, CK, loc=(cx, cy, 19.6), rot=(0, 0, rotz), frame=0.12)
        else:
            objs += geo.win_arch(f'TWR_mw{f}', 0.9, 2.2, white, glow, CK, loc=(cx, cy, 17.6), rot=(0, 0, rotz), frame=0.12)

    # ---- 上段（高6.5 r2.3）四面圆窗（金框） ----
    objs.append(geo.ngon('TWR_hi', 8, 2.3, 6.5, sand, loc=(0, 0, 23.6 + 3.25), ckey=CK, phase=pi / 8))
    for f in range(4):
        a = f * pi / 2
        cx, cy = cos(a) * 2.27, sin(a) * 2.27
        objs += geo.win_round(f'TWR_hr{f}', 0.62, gold, glow, CK, loc=(cx, cy, 26.3), rot=(0, 0, a - pi / 2))
    objs.append(geo.ngon('TWR_eave2', 8, 2.78, 0.42, white, loc=(0, 0, 30.0), ckey=CK, phase=pi / 8))

    # ---- 可开观景穹（铜绿 + 8 金肋 + 开缝） ----
    objs.append(geo.dome('TWR_dome', 2.62, 2.9, cptr, (0, 0, 30.2), CK, seg=28, rings=8, gap=(38, 74)))
    for k in range(8):
        az = D(45 * k)
        pts = []
        for i in range(9):
            phi = (pi / 2) * i / 8
            rr = cos(phi) * 2.68
            zz = 30.2 + sin(phi) * 2.9 - 0.05
            pts.append((cos(az) * rr, sin(az) * rr, zz))
        objs.append(geo.tube(f'TWR_rib{k}', pts, 0.05, gold, CK, n=6))
    objs.append(geo.ngon('TWR_scope', 10, 0.14, 1.1, gold, ckey=CK,
                         loc=(0.55, 0.4, 31.6), rot=(D(50), 0, D(-30)), r_top=0.1))
    objs.append(geo.ngon('TWR_pinn', 8, 0.52, 1.0, cptr, loc=(0, 0, 33.2), ckey=CK, phase=pi / 8))
    objs.append(geo.ngon('TWR_pinncap', 8, 0.62, 0.9, cptr, loc=(0, 0, 34.05), ckey=CK, phase=pi / 8, r_top=0.02))

    # ---- 裂隙晶（全场最亮） ----
    objs.append(geo.ngon('TWR_cbase', 8, 0.55, 0.7, black, loc=(0, 0, 34.85), ckey=CK, phase=pi / 8))
    objs += geo.crystal_cluster('TWR_crystal', crystal, CK, (0, 0, 35.3), n=4, h=3.3, r=0.65)
    ring = geo.ring_tube('TWR_goldring', 1.25, 0.045, gold, (0, 0, 36.7), CK, n=24, m=6)
    ring.rotation_euler = (D(22), 0, 0)
    objs.append(ring)
    return objs
