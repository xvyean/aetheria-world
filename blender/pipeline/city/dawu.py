# -*- coding: utf-8 -*-
"""Z04 晨辉院（翼日）：对称礼堂 + 柱廊山花 + 金顶钟楼 + 侧翼讲堂 + 金叶梧桐。"""
import math
from math import pi, radians as D, cos, sin
from .. import geo
from .common import place, yard_rot, yard_center
from .. import layout

CK = 'Z04_DAW'

def build(M):
    y = layout.YARDS['dawu']
    cx, cy = yard_center(y['theta'], y['r'])
    rotz = yard_rot(y['theta'])
    objs = []
    sand, white = M('plaster'), M('white_smooth')
    slate, gold, glow = M('slate'), M('gold'), M('window')

    # 石坪
    objs.append(geo.box('DAW_yard', 17, 15, 0.12, M('street'), ckey=CK, loc=(0, 2, 0.10)))
    # 礼堂（对称：柱廊6 + 山花 + 台阶5）
    objs.append(geo.box('DAW_hall', 14, 9, 6.5, sand, ckey=CK, loc=(0, 2.8, 0.22 + 3.25)))
    for i in range(6):
        x = -6 + i * 2.4
        objs.append(geo.ngon(f'DAW_col{i}', 14, 0.27, 5.0, white, loc=(x, -2.6, 0.22 + 2.5), ckey=CK))
        objs.append(geo.box(f'DAW_colb{i}', 0.7, 0.7, 0.3, white, ckey=CK, loc=(x, -2.6, 0.35)))
    objs.append(geo.box('DAW_arch', 15.4, 0.8, 0.5, white, ckey=CK, loc=(0, -2.6, 5.6)))
    objs.append(geo.box('DAW_goldline', 15.2, 0.2, 0.1, M('glaze_gold'), ckey=CK, loc=(0, -2.6, 5.9)))
    objs.append(geo.poly_prism('DAW_pediment', [(-8.0, 0), (8.0, 0), (0, 2.2)], 0.5, white,
                               loc=(0, -2.6, 5.85), rot=(0, pi / 2, 0), ckey=CK))
    objs.append(geo.stair('DAW_steps', 5, 7.2, 0.18, 0.42, white, ckey=CK, loc=(-3.6, -4.3, 0.22), rot=(0, 0, pi / 2)))
    # 门（暖光大拱窗）
    objs += geo.arch_portal('DAW_door', 2.2, 4.0, 0.7, white, CK, loc=(0, -1.9, 0.22), pane=M('window'))
    # 屋顶
    objs += geo.gable_roof('DAW_roof', 15.6, 10.9, 2.7, slate, CK, loc=(0, 2.8, 7.0))
    # 侧翼讲堂
    objs.append(geo.box('DAW_wing', 5, 12, 4.2, sand, ckey=CK, loc=(-7.6, 3.2, 0.22 + 2.1)))
    objs += geo.gable_roof('DAW_wingroof', 12.6, 5.9, 1.6, slate, CK, loc=(-7.6, 3.2, 4.7), rot=(0, 0, pi / 2))
    # 钟楼（方塔 + 金攒尖 + 翼日）
    objs.append(geo.box('DAW_bellt', 3, 3, 11.5, white, ckey=CK, loc=(-4.5, -6.5, 0.22 + 5.75)))
    objs.append(geo.ngon('DAW_bellroof', 4, 2.35, 2.6, gold, ckey=CK, loc=(-4.5, -6.5, 12.3), r_top=0.05, phase=pi / 4))
    objs.append(geo.ngon('DAW_bellwin', 4, 0.95, 1.7, glow, ckey=CK, loc=(-4.5, -5.05, 8.4), r_top=0.8, phase=pi / 4))
    objs.append(geo.ngon('DAW_sun', 12, 0.55, 0.12, gold, ckey=CK, loc=(-4.5, -6.5, 15.15), rot=(0, pi / 2, 0)))
    for s in (1, -1):
        objs.append(geo.poly_prism(f'DAW_wingpl{s}', [(0, 0), (1.0, 0.28), (0.9, 0.62), (0.15, 0.4)],
                                   0.08, gold, loc=(-4.5 + s * 0.75, -6.5, 14.7),
                                   rot=(0, 0, s * pi / 2), ckey=CK))
    # 树（金叶梧桐 ×4）
    for (tx, ty) in [(-5.5, -8.2), (5.5, -8.2), (-6.8, -3.6), (6.8, -3.6)]:
        objs += geo.tree(f'DAW_t{tx}{ty}', 'round', M('bark'), M('leaf_gold'), CK, (tx, ty), s=1.25, crown=1.6)
    # 前院旗杆
    objs += geo.flagpole('DAW_flag', white, M('flag_gold'), CK, (0, -8.6), h=5.4)
    # 院墙
    for seg in [(-6, -9.2), (6, -9.2), (-9.2, -6.5), (9.2, -6.5)]:
        objs.append(geo.box(f'DAW_wall{seg}', 0.35, 4.6, 1.5, white, ckey=CK, loc=(seg[0], seg[1], 0.9)))
    return place(objs, cx, cy, rotz)
