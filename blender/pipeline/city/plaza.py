# -*- coding: utf-8 -*-
"""Z02 中央广场：四色扇形地面 + 分选礼台 + 石灯 + 12 石座 + 四色旗。"""
import math
from math import pi, radians as D, cos, sin
from .. import geo, layout

CK = 'Z02_PLZ'

def _ring(name, r0, r1, z, mat, ckey, seg=48):
    vs, fs = [], []
    for i in range(seg):
        a = 2 * pi * i / seg
        vs.append((cos(a) * r0, sin(a) * r0, z))
    for i in range(seg):
        a = 2 * pi * i / seg
        vs.append((cos(a) * r1, sin(a) * r1, z))
    for i in range(seg):
        j = (i + 1) % seg
        fs.append((i, j, seg + j, seg + i))
    return geo._mesh(name, vs, fs, mat, ckey, uv='cyl', uvscale=0.5)

def _wedge(name, a0, a1, r, z, mat, ckey, seg=12):
    vs = [(0, 0, z)]
    for i in range(seg + 1):
        a = D(a0 + (a1 - a0) * i / seg)
        vs.append((cos(a) * r, sin(a) * r, z))
    fs = []
    for i in range(seg):
        fs.append((0, 1 + i, 1 + i + 1))
    return geo._mesh(name, vs, fs, mat, ckey, uv='cyl', uvscale=0.6)

def build(M):
    objs = []
    cx, cy = layout.PLAZA_C
    R = layout.PLAZA_R
    street, slate, white = M('street'), M('slate'), M('white_smooth')
    glow, lamp = M('window'), M('lamp')

    # 广场地面（台地顶面 z≈0.16）
    z0 = 0.16
    objs.append(_ring('PLZ_outer', R * 0.62, R + 0.35, z0, slate, CK))
    objs.append(_ring('PLZ_mid', 3.6, R * 0.62, z0 + 0.015, street, CK))
    for k, (a0, mat) in enumerate([(0, M('glaze_gold')), (90, M('glaze_blue')),
                                   (180, M('glaze_green')), (270, M('glaze_copper'))]):
        objs.append(_wedge(f'PLZ_sector{k}', a0, a0 + 90, 3.6, z0 + 0.03, mat, CK))
    objs.append(geo.ngon('PLZ_core', 24, 1.0, 0.06, white, loc=(cx, cy, z0 + 0.035), ckey=CK, r_top=1.0))

    # 分选礼台
    ax, ay = layout.ALTAR
    objs.append(geo.ngon('PLZ_altar1', 20, 3.2, 0.28, white, loc=(ax, ay, z0 + 0.14), ckey=CK))
    objs.append(geo.ngon('PLZ_altar2', 20, 2.5, 0.24, white, loc=(ax, ay, z0 + 0.4), ckey=CK))
    # 石灯（八角攒尖）
    objs += geo.lantern('PLZ_lamp', white, glow, CK, (ax, ay), s=2.1)
    # 12 石座（旁听席）
    for i in range(12):
        a = D(30 * i + 8)
        x, y = ax + cos(a) * 4.9, ay + sin(a) * 4.9
        objs.append(geo.ngon(f'PLZ_seat{i}', 10, 0.42, 0.55, white, loc=(x, y, z0 + 0.28), ckey=CK, r_top=0.3))
    # 四色旗
    mats = [M('flag_gold'), M('flag_blue'), M('flag_green'), M('flag_copper')]
    for i in range(4):
        a = D(45 + 90 * i)
        x, y = cx + cos(a) * 7.6, cy + sin(a) * 7.6
        objs += geo.flagpole(f'PLZ_flag{i}', white, mats[i], CK, (x, y), h=6.0)
    # 甬道口（北向塔门）
    objs.append(geo.box('PLZ_alley', 4.0, 6.5, 0.12, street, ckey=CK, loc=(cx, cy - R - 3.0, z0)))
    return objs
