# -*- coding: utf-8 -*-
"""Z14 白石浴场：圆屋 + 穹顶烟洞 + 余热烟囱 + 晾衣绳（灰白长袍的传说）。"""
import math
from math import pi, radians as D, cos, sin
from .. import geo, layout

CK = 'Z14_BATH'

def build(M):
    objs = []
    cx, cy = layout.BATH_C
    white, glow = M('plaster_w'), M('window')
    # 圆屋
    objs.append(geo.ngon('BATH_wall', 24, 2.6, 3.2, white, loc=(cx, cy, 1.6), ckey=CK))
    objs.append(geo.dome('BATH_dome', 2.7, 1.5, white, (cx, cy, 3.2), CK, seg=24, rings=6, gap=(55, 80)))
    # 烟洞（蒸汽出口）
    objs.append(geo.ring_tube('BATH_hole', 0.45, 0.08, M('slate'), (cx, cy, 4.65), CK, n=14, m=5))
    # 余热矮烟囱（连锤音炉子）
    objs.append(geo.ngon('BATH_chim', 10, 0.3, 3.4, M('rock'), loc=(cx + 2.6, cy + 1.6, 1.7), ckey=CK, r_top=0.24))
    # 门
    objs += geo.arch_portal('BATH_door', 1.3, 2.4, 0.6, white, CK, loc=(cx, cy - 2.6, 0.0), rot=(0, 0, pi))
    # 门口灯
    objs += geo.lantern('BATH_lamp', white, glow, CK, (cx - 2.6, cy - 1.4), s=0.9)
    # 晾衣绳 ×2 + 布片（含那件灰白长袍的传说位）
    for i in range(2):
        y0 = cy - 3.6 - i * 0.7
        objs.append(geo.rope(f'BATH_line{i}', M('rope'), CK, (cx - 2.8, y0, 2.0), (cx + 2.8, y0, 2.0), sag=0.35, r=0.02))
    cloths = [(0.9, M('cloth')), (2.0, M('cloth_grey')), (-1.4, M('cloth_white') if False else M('cloth'))]
    # 灰白布片：挂中间（那件 402 年后没人的长袍）
    objs.append(geo.banner('BATH_robe', 0.7, 1.9, M('cloth_white'), CK, loc=(cx + 0.2, cy - 3.9, 1.15), wave=0.02))
    for i, (dx, m) in enumerate(cloths):
        objs.append(geo.banner(f'BATH_cloth{i}', 0.55, 0.75, m, CK, loc=(cx + dx, cy - 4.55, 1.62), wave=0.03))
    # 地面水渍
    objs.append(geo.ngon('BATH_wet', 16, 1.3, 0.02, M('water'), loc=(cx, cy, 0.03), ckey=CK, r_top=0.5))
    return objs
