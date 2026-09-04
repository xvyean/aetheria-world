# -*- coding: utf-8 -*-
"""世界场景（环境镜头）：裂隙光柱 + 海面 + 灰港灯火 + 远山剪影。"""
import math
from math import pi, radians as D, cos, sin
from . import geo, layout, util

CK = 'Z99_WLD'

def build(M):
    objs = []
    sea = geo.ngon('WLD_sea', 48, 420, 0.5, M('water_sea'), loc=(0, 0, layout.SEA_Z), ckey=CK)
    objs.append(sea)
    # 裂隙光柱（自岛底到海）
    n = 40
    pts = []
    for i in range(n):
        t = i / (n - 1)
        z = layout.COLUMN_TOP_Z - (layout.COLUMN_TOP_Z - layout.SEA_Z) * t
        pts.append((0, 0, z))
    col = geo.tube('WLD_column', pts, layout.COLUMN_R, M('crystal'), CK, n=12)
    objs.append(col)
    # 海面光晕（柱脚）
    objs.append(geo.ngon('WLD_glow', 32, 26, 0.2, M('crystal'), loc=(0, 0, layout.SEA_Z + 0.4), ckey=CK, r_top=14))
    # 灰港城灯火（西岸，远处小发光点群）
    for i in range(26):
        a = util.R.uniform(0, 2 * pi)
        rr = util.R.uniform(120, 240)
        x, y = cos(a) * rr, sin(a) * rr
        z = layout.SEA_Z + util.R.uniform(0.5, 4)
        s = util.R.uniform(0.3, 0.9)
        objs.append(geo.ngon(f'WLD_gl{i}', 8, s, s, M('lamp'), loc=(x, y, z), ckey=CK, r_top=s * 0.5))
    # 远山剪影（两圈低多边形环）
    for ring_i, (rr0, hh, cc) in enumerate([(430, 22, 44), (540, 36, 34)]):
        for i in range(cc):
            a = 2 * pi * i / cc + ring_i * 0.13
            x, y = cos(a) * rr0, sin(a) * rr0
            h = hh * (0.7 + 0.5 * math.sin(i * 2.7 + ring_i))
            objs.append(geo.ngon(f'WLD_mtn{ring_i}_{i}', 7, 26 + 14 * math.sin(i * 1.7), h,
                                 M('rock2'), loc=(x, y, layout.SEA_Z + h / 2 + 1), ckey=CK,
                                 r_top=3, smooth=False))
    # 碎浪群岛：远处小岛群（气氛）
    for k in range(7):
        a = D(35 * k - 40)
        rr = 150 + 30 * math.sin(k * 2.3)
        x, y = cos(D(35 * k - 40)) * rr, sin(D(35 * k - 40)) * rr
        s0 = 6 + 4 * (k % 3)
        h0 = 5 + (k * 7) % 9
        objs.append(geo.ngon(f'WLD_isle{k}', 9, s0, h0, M('rock2'),
                             loc=(x, y, layout.SEA_Z + h0 / 2), ckey=CK, r_top=1.2, smooth=False))
    return objs
