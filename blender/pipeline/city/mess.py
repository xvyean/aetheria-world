# -*- coding: utf-8 -*-
"""Z13 长桌堂：东西山墙开敞的食堂 + 8 米长桌 + 欠账榜 + 暖灯。"""
import math
from math import pi, radians as D, cos, sin
from .. import geo, layout

CK = 'Z13_MES'
ROT = D(-70) - pi / 2

def W(lx, ly, lz=0.0):
    c, s = cos(ROT), sin(ROT)
    ox, oy = layout.MESS_C
    return (ox + lx * c - ly * s, oy + lx * s + ly * c, lz)

def build(M):
    objs = []
    wood, dark, glow = M('plank'), M('plank_dark'), M('window')
    # 柱廊开敞长屋（西山墙开门）
    for i in range(4):
        x = -5.4 + i * 3.6
        objs.append(geo.box(f'MES_p{i}', 0.3, 0.3, 3.0, wood, ckey=CK, loc=W(x, -2.2, 1.6)))
        objs.append(geo.box(f'MES_pb{i}', 0.3, 0.3, 3.0, wood, ckey=CK, loc=W(x, 2.2, 1.6)))
    objs.append(geo.box('MES_beamf', 12.6, 0.28, 0.28, wood, ckey=CK, loc=W(0, -2.2, 3.2)))
    objs.append(geo.box('MES_beamb', 12.6, 0.28, 0.28, wood, ckey=CK, loc=W(0, 2.2, 3.2)))
    objs += geo.gable_roof('MES_roof', 13.0, 5.6, 1.5, M('slate'), CK, loc=W(0, 0, 3.4))
    # 山墙（东西两端，0.8 留门）
    objs.append(geo.box('MES_gw_w', 0.3, 4.6, 3.2, wood, ckey=CK, loc=W(-6.35, 0, 1.7)))
    objs.append(geo.box('MES_gw_e', 0.3, 4.6, 3.2, wood, ckey=CK, loc=W(6.35, 0, 1.7)))
    # 8 米长桌 + 两列长凳
    objs.append(geo.box('MES_table', 8.0, 1.1, 0.12, dark, ckey=CK, loc=W(0, 0, 0.92)))
    for s in (1, -1):
        for i in range(3):
            x = -2.9 + i * 2.9
            objs.append(geo.box(f'MES_leg{i}{s}', 0.16, 0.16, 0.85, dark, ckey=CK, loc=W(x, s * 0.35, 0.45)))
        objs.append(geo.box(f'MES_bench{s}', 8.6, 0.42, 0.1, wood, ckey=CK, loc=W(0, s * 1.15, 0.62)))
        objs.append(geo.box(f'MES_benchleg{s}', 0.16, 0.4, 0.55, dark, ckey=CK, loc=W(0, s * 1.15, 0.30)))
    # 欠账榜（北墙黑石板）
    objs.append(geo.box('MES_board', 3.2, 0.1, 1.4, M('darkboard'), ckey=CK, loc=W(-1.6, 2.0, 2.0), rot=(0, 0, 0)))
    objs.append(geo.box('MES_boardframe', 3.6, 0.12, 0.14, dark, ckey=CK, loc=W(-1.6, 2.0, 2.75), rot=(0, 0, 0)))
    objs.append(geo.box('MES_boardframe2', 3.6, 0.12, 0.14, dark, ckey=CK, loc=W(-1.6, 2.0, 1.27), rot=(0, 0, 0)))
    # 灶台与暖灯
    objs.append(geo.box('MES_stove', 2.2, 1.2, 1.0, M('rock'), ckey=CK, loc=W(4.6, 1.5, 0.55)))
    objs.append(geo.box('MES_stoveglow', 1.2, 0.1, 0.5, glow, ckey=CK, loc=W(4.6, 0.9, 0.75)))
    for i in range(2):
        objs.append(geo.box(f'MES_lamp{i}', 0.1, 0.1, 2.6, dark, ckey=CK, loc=W(-2.0 + i * 4.0, -1.8, 1.5)))
        objs.append(geo.ngon(f'MES_lampg{i}', 6, 0.16, 0.24, M('lamp'), ckey=CK, loc=W(-2.0 + i * 4.0, -1.8, 3.0), r_top=0.12))
    # 碗碟小景
    for i in range(4):
        objs.append(geo.ngon(f'MES_bowl{i}', 10, 0.12, 0.08, M('plaster_w'),
                             loc=W(-2.4 + i * 1.5, 0.1, 1.02), ckey=CK, r_top=0.08))
    return objs
