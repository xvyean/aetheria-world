# -*- coding: utf-8 -*-
"""Z03 四院回廊：四条坡道柱廊（4°）+ 半墙滚书 + 无锁半开院门 + 开院人之柱。"""
import math
from math import pi, radians as D, cos, sin
from .. import geo, layout, util

CK = 'Z03_CLO'
ARMS = [  # (方位角度, 院色瓦材质key, 院名)
    (0,   'glaze_gold',   'dawu'),
    (180, 'glaze_green',  'lingu'),
    (-90, 'glaze_copper', 'hamm'),
    (90,  'glaze_blue',   'sea'),
]

def _ramp(name, L, W, drop, mat, ckey, loc, rotz):
    """坡道板：局部 +X 为径向，外端下沉 drop。"""
    vs = [(0, -W / 2, 0), (L, -W / 2, -drop), (L, W / 2, -drop), (0, W / 2, 0),
          (0, -W / 2, 0.18), (L, -W / 2, -drop + 0.18), (L, W / 2, -drop + 0.18), (0, W / 2, 0.18)]
    fs = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    ob = geo._mesh(name, [tuple(v) for v in vs], fs, mat, ckey, uvscale=0.5)
    ob.location = loc
    ob.rotation_euler = (0, 0, rotz)
    return ob

def build(M):
    objs = []
    white, dark = M('white_smooth'), M('wood_dark')
    post = M('column')
    glow = M('window')

    r0, r1 = 5.4, 17.6          # 塔基沿 → 院门
    L = r1 - r0
    drop = L * math.tan(D(4))   # 4° 坡
    for (adeg, glaze_key, yard) in ARMS:
        rotz = D(adeg)
        dx, dy = cos(rotz), sin(rotz)
        # 面外法向（径向），内法向
        # 地板
        objs.append(_ramp(f'CLO_{yard}_floor', L, 2.6, drop, M('street'), CK,
                          (dx * r0, dy * r0, 0.14), rotz))
        # 内侧半墙（高1.1，可倚）
        ix, iy = -dy, dx   # 内法向 = 径向旋转-90
        objs.append(geo.box(f'CLO_{yard}_wall', L, 0.26, 1.1, white, ckey=CK,
                            loc=(dx * (r0 + L / 2) + ix * 1.0, dy * (r0 + L / 2) + iy * 1.0, 0.14 + 0.55),
                            rot=(0, 0, rotz)))
        # 外侧柱列（每2米）
        for i in range(7):
            t = 0.06 + i * 0.155
            rr = r0 + L * t
            z = 0.14 - drop * t
            objs.append(geo.ngon(f'CLO_{yard}_p{i}', 10, 0.19, 2.55, post,
                                 loc=(dx * rr + ix * 1.12, dy * rr + iy * 1.12, z + 1.28), ckey=CK, uvscale=0.8))
        # 廊顶（院色琉璃，随坡）
        roof = _ramp(f'CLO_{yard}_roof', L + 0.6, 3.0, drop, M(glaze_key), CK,
                     (dx * (r0 - 0.3), dy * (r0 - 0.3), 0.14 + 2.95), rotz)
        objs.append(roof)
        objs.append(geo.box(f'CLO_{yard}_fascia', L + 0.7, 0.1, 0.34, white, ckey=CK,
                            loc=(dx * (r0 + L / 2 + 0.3) + ix * 1.5, dy * (r0 + L / 2 + 0.3) + iy * 1.5, 0.14 + 2.85 - drop / 2),
                            rot=(0, 0, rotz)))
        # 院门（无锁，半开 22°）
        gx, gy = dx * r1, dy * r1
        objs.append(geo.box(f'CLO_{yard}_jambA', 0.3, 0.5, 2.9, dark, ckey=CK,
                            loc=(gx + ix * 1.15, gy + iy * 1.15, 0.14 - drop + 1.45), rot=(0, 0, rotz)))
        objs.append(geo.box(f'CLO_{yard}_jambB', 0.3, 0.5, 2.9, dark, ckey=CK,
                            loc=(gx - ix * 1.15, gy - iy * 1.15, 0.14 - drop + 1.45), rot=(0, 0, rotz)))
        objs.append(geo.box(f'CLO_{yard}_lintel', 2.9, 0.5, 0.35, dark, ckey=CK,
                            loc=(gx, gy, 0.14 - drop + 3.0), rot=(0, 0, rotz)))
        for s in (1, -1):
            door = geo.box(f'CLO_{yard}_door{s}', 0.95, 0.09, 2.5, M('plank'), ckey=CK)
            a_open = rotz + s * D(-58)   # 门扇沿铰链外开
            door.location = (gx + ix * s * 1.05, gy + iy * s * 1.05, 0.14 - drop + 1.25)
            door.rotation_euler = (0, 0, a_open)
            objs.append(door)
        objs += geo.carve_band(f'CLO_{yard}_words', 2.1, dark, CK,
                               loc=(gx, gy, 0.14 - drop + 3.22), rot=(0, 0, rotz), h=0.2, n=10)
        # 开院人之柱（黑石，掌印）
        objs.append(geo.box(f'CLO_{yard}_pillar', 0.56, 0.56, 3.5, M('blackstone'), ckey=CK,
                            loc=(gx + ix * 3.2, gy + iy * 3.2, 0.14 - drop + 1.75), rot=(0, 0, rotz), bevel=0.03))
        for k in range(3):
            objs.append(geo.box(f'CLO_{yard}_palm{k}', 0.16, 0.05, 0.2, M('rock'), ckey=CK,
                                loc=(gx + ix * 3.2 + dx * 0.29 + ix * (0.02 * k),
                                     gy + iy * 3.2 + dy * 0.29 + iy * (0.02 * k),
                                     0.14 - drop + 1.55 + 0.22 * k), rot=(0, 0, rotz)))
        # 半墙上滚落的书
        for b_i in range(3):
            t = 0.25 + 0.3 * b_i + util.R.uniform(-0.05, 0.05)
            rr = r0 + L * t
            z = 0.14 - drop * t
            objs += geo.books(f'CLO_{yard}_book{b_i}', M('paper'), M('bronze'), CK,
                              (dx * rr + ix * 1.08, dy * rr + iy * 1.08, z + 1.12),
                              rot=(0, 0, rotz + util.R.uniform(0, 3)), n=2 + b_i, scale=0.13)
        # 门内暖光
        objs.append(geo.box(f'CLO_{yard}_gateglow', 1.4, 0.08, 2.2, glow, ckey=CK,
                            loc=(dx * (r1 + 0.7), dy * (r1 + 0.7), 0.14 - drop + 1.2), rot=(0, 0, rotz)))
    return objs
