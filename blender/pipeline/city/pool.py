# -*- coding: utf-8 -*-
"""Z08 浮池：悬出岛缘的石盆 + 永远满平的镜面水 + 14 石座 + 名字环带 + 石隼。"""
import math
from math import pi, radians as D, cos, sin
from .. import geo, util, layout

CK = 'Z08_POOL'

def build(M):
    objs = []
    px, py = layout.POOL_C
    R = layout.POOL_R
    white, water = M('white_smooth'), M('water')
    z_top = 0.30   # 盆沿
    # 石托内凹盆（lathe：外壁 + 内壁）
    prof = [  # (r, z) 外缘 → 沿 → 内
        (R, 0.0), (R + 0.15, 0.15), (R + 0.1, z_top), (R - 0.35, z_top + 0.18),
        (R - 1.1, z_top - 0.5), (R - 2.6, z_top - 1.0), (R - 4.2, z_top - 1.35), (R - 5.6, z_top - 1.55),
    ]
    seg = 48
    vs, fs = [], []
    rings = []
    for (rr, zz) in prof:
        ring = []
        for i in range(seg):
            a = 2 * pi * i / seg
            ring.append(len(vs))
            vs.append((px + cos(a) * rr, py + sin(a) * rr, zz))
        rings.append(ring)
    for k in range(len(rings) - 1):
        for i in range(seg):
            j = (i + 1) % seg
            fs.append((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]))
    ob = geo._mesh('POOL_basin', vs, fs, white, CK, uv='cyl', uvscale=0.35, smooth=True)
    objs.append(ob)
    # 水面（精确水平，z = 沿下 0.1）
    z_water = z_top - 0.10
    objs.append(geo.ngon('POOL_water', 40, R - 1.15, 0.04, water, loc=(px, py, z_water), ckey=CK, r_top=R - 1.15))
    # 名字环带（浮雕）
    objs.append(geo.carve_band('POOL_names', 5.5, M('plaster'), CK,
                               loc=(px + R - 0.2, py, z_top + 0.1), n=38, h=0.16))
    objs.append(geo.carve_band('POOL_names2', 5.5, M('plaster'), CK,
                               loc=(px - R + 0.2, py, z_top + 0.1), rot=(0, 0, pi), n=38, h=0.16))
    objs.append(geo.carve_band('POOL_names3', 5.5, M('plaster'), CK,
                               loc=(px, py + R - 0.2, z_top + 0.1), rot=(0, 0, pi / 2), n=38, h=0.16))
    objs.append(geo.carve_band('POOL_names4', 5.5, M('plaster'), CK,
                               loc=(px, py - R + 0.2, z_top + 0.1), rot=(0, 0, -pi / 2), n=38, h=0.16))
    # 14 石座
    for i in range(14):
        a = D(360 * i / 14 + 6)
        x, y = px + cos(a) * (R + 1.7), py + sin(a) * (R + 1.7)
        objs.append(geo.ngon(f'POOL_seat{i}', 8, 0.4, 0.62, white, loc=(x, y, 0.33), ckey=CK, r_top=0.34))
    # 悬挑石隼（2 块，底下）
    for i in range(2):
        a = D(30 + 120 * i)
        objs.append(geo.box(f'POOL_corbel{i}', 0.9, 1.6, 0.5, M('rock'), ckey=CK,
                            loc=(px + cos(a) * R * 0.8, py + sin(a) * R * 0.8, -0.5),
                            rot=(0, 0, a)))
    # 池边值日小灯
    objs += geo.lantern('POOL_lamp', white, M('window'), CK, (px - R - 2.6, py - R - 0.6), s=0.9)
    return objs
