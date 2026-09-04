# -*- coding: utf-8 -*-
"""Z09 星穗馆：圆馆 + 8 壁柱高窗 + 白檐环 + 24 金肋金穹 + 金穗冠塔 + 半掩侧门。"""
import math
from math import pi, radians as D, cos, sin
from .. import geo, layout

CK = 'Z09_LIB'

def build(M):
    objs = []
    cx, cy = layout.LIB_C
    white, dark = M('plaster_w'), M('slate')
    gold, glow = M('gold'), M('window')
    # 台基（两级圆台）
    objs.append(geo.ngon('LIB_base1', 32, 6.4, 0.5, white, loc=(cx, cy, 0.25), ckey=CK))
    objs.append(geo.ngon('LIB_base2', 32, 5.9, 0.5, white, loc=(cx, cy, 0.72), ckey=CK))
    # 鼓座（壁柱8 + 高窗）
    objs.append(geo.ngon('LIB_drum', 32, 5.5, 5.6, white, loc=(cx, cy, 1.0 + 2.8), ckey=CK))
    for i in range(8):
        a = 2 * pi * i / 8 + pi / 8
        x, y = cx + cos(a) * 5.5, cy + sin(a) * 5.5
        objs.append(geo.ngon(f'LIB_pil{i}', 10, 0.32, 5.0, white, loc=(x, y, 1.0 + 2.5), ckey=CK))
    # 柱间高窗（暖光 + 竖棂）
    for i in range(8):
        a = 2 * pi * i / 8
        x, y = cx + cos(a) * 5.35, cy + sin(a) * 5.35
        objs += geo.win_arch(f'LIB_w{i}', 1.0, 2.8, white, glow, CK, loc=(x, y, 1.0 + 3.2), rot=(0, 0, a - pi / 2), frame=0.1, bars=3)
    # 白色檐环
    objs.append(geo.ngon('LIB_eave', 32, 6.1, 1.1, white, loc=(cx, cy, 0.2 + 6.1 + 0.55), ckey=CK))
    # 金穹（24 金肋）
    objs.append(geo.ngon('LIB_dombase', 32, 5.5, 0.3, dark, loc=(cx, cy, 7.6), ckey=CK))
    objs.append(geo.dome('LIB_dome', 5.6, 4.3, dark, (cx, cy, 7.75), CK, seg=32, rings=8))
    for i in range(24):
        a = 2 * pi * i / 24
        pts = []
        for k in range(7):
            phi = (pi / 2) * k / 6
            rr = cos(phi) * 5.68
            zz = 7.75 + sin(phi) * 4.3 - 0.04
            pts.append((cx + cos(a) * rr, cy + sin(a) * rr, zz))
        objs.append(geo.tube(f'LIB_rib{i}', pts, 0.055, gold, CK, n=6))
    # 冠塔 + 金穗
    objs.append(geo.ngon('LIB_crown', 10, 0.75, 1.3, dark, loc=(cx, cy, 12.1), ckey=CK, r_top=0.5))
    objs.append(geo.ngon('LIB_crowncap', 10, 0.55, 1.1, gold, ckey=CK, loc=(cx, cy, 13.3), r_top=0.03))
    objs.append(geo.ngon('LIB_grain', 8, 0.14, 1.5, gold, ckey=CK, loc=(cx, cy, 14.6), r_top=0.02))
    # 馆门（正东）+ 侧门（西北半掩）
    objs += geo.arch_portal('LIB_door', 2.2, 3.6, 0.8, white, CK, loc=(cx + 5.9, cy, 0.6), rot=(0, 0, pi / 2), pane=M('window'))
    objs += geo.arch_portal('LIB_sidedoor', 1.5, 2.8, 0.7, white, CK,
                            loc=(cx + cos(D(215)) * 5.6, cy + sin(D(215)) * 5.6, 0.6),
                            rot=(0, 0, D(215) - pi / 2))
    objs.append(geo.box('LIB_sideleaf', 0.85, 0.08, 2.3, M('plank_dark'), ckey=CK,
                        loc=(cx + cos(D(215)) * 5.15, cy + sin(D(215)) * 5.15, 1.75),
                        rot=(0, 0, D(215) - pi / 2 - 0.4)))
    # 馆边书堆小景
    from .. import util
    objs += geo.books('LIB_books', M('paper'), M('bronze'), CK,
                      (cx - 5.2, cy - 4.2, 1.1), rot=(0, 0, D(215)), n=5, scale=0.15)
    return objs
