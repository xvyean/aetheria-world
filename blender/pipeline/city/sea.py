# -*- coding: utf-8 -*-
"""Z07 海心院（罗盘与鲸尾）：船楼低剖面 + 白木构架 + 望楼鲸尾 + 船坞缆绳 + 北境花圃。"""
import math
from math import pi, radians as D, cos, sin
from .. import geo
from .common import place, yard_rot, yard_center
from .. import layout

CK = 'Z07_SEA'

def build(M):
    y = layout.YARDS['sea']
    cx, cy = yard_center(y['theta'], y['r'])
    rotz = yard_rot(y['theta'])
    objs = []
    white = M('plaster')
    blue, glow = M('glaze_blue'), M('window')
    beam = M('plank_dark')

    # 架空底层（桩柱 + 码头台阶）
    objs.append(geo.box('SEA_floor', 14, 8, 0.3, beam, ckey=CK, loc=(0, 1.4, 1.35)))
    for i in range(5):
        for j in range(3):
            objs.append(geo.ngon(f'SEA_pile{i}{j}', 8, 0.16, 1.3, beam,
                                 loc=(-5.6 + i * 2.8, -1.4 + j * 2.9, 0.75), ckey=CK))
    objs.append(geo.stair('SEA_jettystep', 4, 3.0, 0.3, 0.45, beam, ckey=CK, loc=(-1.5, -4.6, 0.0)))
    # 船楼主体
    objs.append(geo.box('SEA_hull', 14, 8, 4.6, white, ckey=CK, loc=(0, 1.4, 1.5 + 2.6)))
    # 白木构架（外露柱梁描白）
    for i in range(5):
        x = -6 + i * 3
        objs.append(geo.box(f'SEA_frame{i}', 0.22, 0.22, 4.2, white, ckey=CK, loc=(x, -2.7, 3.9)))
    objs.append(geo.box('SEA_beamf', 14.2, 0.3, 0.3, white, ckey=CK, loc=(0, -2.7, 6.05)))
    # 蓝瓦双坡 + 蓝漆饰条
    objs += geo.gable_roof('SEA_roof', 15.4, 9.6, 2.4, blue, CK, loc=(0, 1.4, 6.5), over=0.6)
    objs.append(geo.box('SEA_strip', 14.0, 0.16, 0.16, M('glaze_blue'), ckey=CK, loc=(0, -2.72, 4.6)))
    objs.append(geo.box('SEA_strip2', 14.0, 0.16, 0.16, M('glaze_blue'), ckey=CK, loc=(0, -2.72, 3.4)))
    # 暖窗
    objs += geo.win_arch('SEA_win1', 1.1, 1.5, white, glow, CK, loc=(-3.2, -2.62, 4.2), frame=0.12)
    objs += geo.win_arch('SEA_win2', 1.1, 1.5, white, glow, CK, loc=(3.2, -2.62, 4.2), frame=0.12)
    # 望楼（西端两层）
    objs.append(geo.box('SEA_watch1', 3.2, 3.2, 3.4, beam, ckey=CK, loc=(-8.4, 0.0, 1.5 + 1.7)))
    objs.append(geo.box('SEA_watch2', 3.4, 3.4, 2.8, white, ckey=CK, loc=(-8.4, 0.0, 6.4)))
    for s in (1, -1):
        objs += geo.win_arch(f'SEA_wwin{s}', 0.9, 1.4, white, glow, CK, loc=(-8.4, 0.0 + s * 1.72, 6.6), rot=(0, 0, s * pi / 2), frame=0.1)
    objs += geo.gable_roof('SEA_watchroof', 3.8, 3.8, 1.2, blue, CK, loc=(-8.4, 0.0, 7.9))
    # 鲸尾（镇院：刻着日期的鲸须）
    pts = [(0, 0), (0.7, 0.5), (0.55, 1.5), (0.1, 2.1), (-0.35, 1.6), (-0.5, 0.7), (-0.15, 0.1)]
    objs.append(geo.poly_prism('SEA_whale', [(x, z) for (x, z) in pts], 0.1, M('plank'),
                               loc=(-8.4, 0.0, 8.9), rot=(0, 0, pi / 2), ckey=CK))
    # 船坞（岛缘悬挑 + 缆绳 + 系船柱）
    objs.append(geo.box('SEA_dock', 5.2, 3.4, 0.25, beam, ckey=CK, loc=(3.5, 9.8, 0.7), rot=(0, 0, 0.06)))
    objs.append(geo.rope('SEA_rope1', M('rope'), CK, (2.2, 8.3, 0.85), (2.6, 11.2, -4.0), sag=0.5, r=0.045))
    objs.append(geo.rope('SEA_rope2', M('rope'), CK, (5.0, 9.0, 0.85), (5.6, 11.0, -4.0), sag=0.5, r=0.045))
    for i in range(3):
        px = 2.4 + i * 1.3
        objs.append(geo.ngon(f'SEA_bollard{i}', 10, 0.16, 1.25, beam, loc=(px, 8.5, 1.35), ckey=CK, r_top=0.2))
        objs.append(geo.ring_tube(f'SEA_knot{i}', 0.2, 0.045, M('rope'), (px, 8.5, 1.28), CK, n=10, m=5))
    # 北境花圃（全院唯一紫）
    objs.append(geo.ngon('SEA_garden', 12, 1.5, 0.22, M('dirt'), loc=(5.6, -5.6, 0.2), ckey=CK))
    objs += geo.flower_cluster('SEA_purple', M('flower_purple'), CK, (5.6, -5.6), n=9, r=1.15)
    objs += geo.flower_cluster('SEA_purple2', M('flower_purple'), CK, (4.6, -4.8), n=5, r=0.7)
    objs += geo.flower_cluster('SEA_gold', M('flower_gold'), CK, (6.6, -4.9), n=4, r=0.6)
    # 潮汐钟（面海铜锣）
    objs.append(geo.ngon('SEA_gongpost', 10, 0.12, 2.2, beam, loc=(6.4, 3.4, 1.1), ckey=CK))
    objs.append(geo.ngon('SEA_gong', 14, 0.55, 0.12, M('copper_metal'), loc=(6.4, 3.5, 2.0), ckey=CK, rot=(pi / 2, 0, 0)))
    return place(objs, cx, cy, rotz)
