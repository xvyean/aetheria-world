# -*- coding: utf-8 -*-
"""Z12 钟楼：三层收分方楼 + 四角尖顶钟冠 + 海锈沉钟 + 更鼓 + 守夜岗。"""
import math
from math import pi, radians as D, cos, sin
from .. import geo, layout

CK = 'Z12_CLK'

def build(M):
    objs = []
    cx, cy = layout.CLK_C
    white, cptr = M('white_smooth'), M('cuprite')
    bell, glow = M('bell'), M('window')
    rotz = D(-110) - pi / 2
    # 基座
    objs.append(geo.box('CLK_base', 5.0, 5.0, 0.6, white, ckey=CK, loc=(cx, cy, 0.3)))
    # 三层收分
    objs.append(geo.box('CLK_t1', 3.6, 3.6, 3.2, white, ckey=CK, loc=(cx, cy, 0.6 + 1.6)))
    objs.append(geo.box('CLK_t2', 3.0, 3.0, 2.6, white, ckey=CK, loc=(cx, cy, 3.8 + 1.3)))
    objs.append(geo.box('CLK_t3', 2.4, 2.4, 2.4, white, ckey=CK, loc=(cx, cy, 6.4 + 1.2)))
    # 四角尖顶钟冠
    for k in range(4):
        a = D(45 + 90 * k)
        x, y = cx + cos(a) * 2.05, cy + sin(a) * 2.05
        objs.append(geo.ngon(f'CLK_spire{k}', 6, 0.4, 2.4, cptr, loc=(x, y, 9.5), ckey=CK, r_top=0.02))
    objs.append(geo.ngon('CLK_crown', 8, 1.5, 1.2, cptr, loc=(cx, cy, 9.0), ckey=CK, r_top=0.35))
    # 四面钟窗 + 沉钟（海锈）
    for f in range(4):
        a = D(90 * f)
        x, y = cx + cos(a) * 1.22, cy + sin(a) * 1.22
        objs += geo.arch_portal(f'CLK_bellwin{f}', 1.3, 1.9, 0.5, white, CK, loc=(x, y, 0.6 + 3.2),
                                rot=(0, 0, D(90 * f) - pi / 2))
        objs.append(geo.ngon(f'CLK_bell{f}', 12, 0.5, 0.75, bell, loc=(x, y, 0.6 + 2.6),
                             ckey=CK, r_top=0.24))
    # 更鼓（西墙）
    objs.append(geo.ngon('CLK_drum', 14, 0.45, 0.35, M('plank_dark'),
                         loc=(cx - 1.55, cy, 0.6 + 4.6), ckey=CK, rot=(pi / 2, 0, 0)))
    objs.append(geo.ring_tube('CLK_drumrim', 0.45, 0.045, M('rope'), (cx - 1.58, cy, 0.6 + 4.6), CK, n=14, m=5, rot=(pi / 2, 0, 0)))
    # 守夜岗（试读生守夜处）
    objs.append(geo.box('CLK_post', 1.8, 1.8, 0.35, M('plank_dark'), ckey=CK, loc=(cx - 3.2, cy + 2.2, 0.28)))
    for (px, py) in [(-4.0, 1.3), (-2.4, 1.3), (-4.0, 3.1), (-2.4, 3.1)]:
        objs.append(geo.box(f'CLK_post{px}{py}', 0.16, 0.16, 2.2, M('plank'), ckey=CK, loc=(cx + px, cy + py, 1.4)))
    objs.append(geo.box('CLK_postroof', 2.4, 2.4, 0.2, M('slate'), ckey=CK, loc=(cx - 3.2, cy + 2.2, 2.6)))
    objs.append(geo.box('CLK_bench', 1.4, 0.4, 0.4, M('plank'), ckey=CK, loc=(cx - 3.2, cy + 2.2, 0.75)))
    objs += geo.lantern('CLK_light', white, glow, CK, (cx - 3.2, cy + 3.3), s=1.1)
    # 木牌"钟别响三下"
    objs.append(geo.box('CLK_sign', 1.3, 0.05, 0.8, M('paper'), ckey=CK, loc=(cx - 4.1, cy + 2.2, 1.5), rot=(0, 0, pi / 2)))
    return objs
