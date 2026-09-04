# -*- coding: utf-8 -*-
"""Z05 星语院（梧桐叶与星图）：月白墙 + 陡峭深绿尖顶 + 三细塔 + 观星台 + 八百年梧桐。"""
import math
from math import pi, radians as D, cos, sin
from .. import geo, util
from .common import place, yard_rot, yard_center
from .. import layout

CK = 'Z05_LIN'

def build(M):
    y = layout.YARDS['lingu']
    cx, cy = yard_center(y['theta'], y['r'])
    rotz = yard_rot(y['theta'])
    objs = []
    moon = M('plaster_w')
    green, glow = M('glaze_green'), M('window')

    # 书楼
    objs.append(geo.box('LIN_hall', 16, 8, 9, moon, ckey=CK, loc=(0, 2.2, 0.2 + 4.5)))
    # 高窄拱窗（北墙与南墙成排，暖光）
    for fx in range(5):
        x = -5.6 + fx * 2.8
        objs += geo.win_arch(f'LIN_wf{fx}', 0.8, 2.4, moon, glow, CK, loc=(x, -2.2, 0.2 + 5.4), rot=(0, 0, 0), frame=0.1)
        objs += geo.win_arch(f'LIN_wb{fx}', 0.8, 2.4, moon, glow, CK, loc=(x, 6.6, 0.2 + 5.4), rot=(0, 0, pi), frame=0.1)
    # 爬藤（窗间）
    for fx in range(4):
        x = -4.2 + fx * 2.8
        objs.append(geo.box(f'LIN_vine{fx}', 0.7, 0.1, 3.6, M('vine'), ckey=CK, loc=(x, -2.16, 0.2 + 5.0)))
    # 陡峭深绿尖顶（55°）+ 脊饰小尖塔5
    objs += geo.gable_roof('LIN_roof', 17.6, 9.9, 5.2, green, CK, loc=(0, 2.2, 9.4), over=0.7)
    for i in range(5):
        x = -6.4 + i * 3.2
        objs.append(geo.ngon(f'LIN_pin{i}', 6, 0.3, 1.4, green, ckey=CK, loc=(x, 2.2, 14.9), r_top=0.02))
    # 观星台（后院穹顶，"给天看的"）
    objs.append(geo.ngon('LIN_obsbase', 20, 3.1, 1.0, moon, loc=(0, 7.0, 0.2 + 0.5), ckey=CK))
    objs.append(geo.dome('LIN_obs', 2.7, 2.2, moon, (0, 7.0, 1.7), CK, seg=22, rings=6, gap=(120, 175)))
    objs.append(geo.tube('LIN_telescope', [(0.15, 6.6, 3.2), (0.9, 6.0, 4.6)], 0.12, M('bronze'), CK, n=8))
    # 三细塔（北侧）
    for i, (tx, th) in enumerate([(-5.5, 7.0), (0.0, 9.0), (5.5, 8.0)]):
        objs.append(geo.ngon(f'LIN_slim{i}', 8, 0.42, th, moon, loc=(tx, 6.6, 0.2 + th / 2), ckey=CK, r_top=0.3))
        objs.append(geo.ngon(f'LIN_slimcap{i}', 8, 0.5, 1.6, green, ckey=CK, loc=(tx, 6.6, 0.2 + th + 0.8), r_top=0.02))
    # 八百年梧桐
    objs += geo.tree('LIN_bigtree', 'big', M('bark'), M('leaf'), CK, (6.2, 4.5), s=1.6, crown=3.4)
    objs.append(geo.box('LIN_scar', 0.5, 0.3, 0.9, M('rock'), ckey=CK, loc=(6.2, 4.5, 2.4), rot=(0, 0, 0.4)))
    # 禁语圈（白圈）
    for r in (1.3, 1.7):
        objs.append(geo.ring_tube(f'LIN_circle{r}', r, 0.035, moon, (2.0, -4.8), CK, n=24, m=5))
    # 院墙（1.8 月白，开口朝院门）
    objs.append(geo.box('LIN_wl', 0.4, 17.0, 1.8, moon, ckey=CK, loc=(-9.2, 1.0, 1.1)))
    objs.append(geo.box('LIN_wr', 0.4, 17.0, 1.8, moon, ckey=CK, loc=(9.2, 1.0, 1.1)))
    objs.append(geo.box('LIN_wb', 18.6, 0.4, 1.8, moon, ckey=CK, loc=(0, 9.8, 1.1)))
    objs.append(geo.box('LIN_vwall1', 6.2, 0.35, 1.8, moon, ckey=CK, loc=(-5.9, -4.9, 1.1)))
    objs.append(geo.box('LIN_vwall2', 6.2, 0.35, 1.8, moon, ckey=CK, loc=(5.9, -4.9, 1.1)))
    objs.append(geo.box('LIN_vgate', 0.3, 0.3, 2.6, M('wood_dark'), ckey=CK, loc=(-3.1, -4.9, 1.5)))
    objs.append(geo.box('LIN_vgate2', 0.3, 0.3, 2.6, M('wood_dark'), ckey=CK, loc=(3.1, -4.9, 1.5)))
    # 门前藤蔓
    for i in range(6):
        objs.append(geo.bush(f'LIN_bush{i}', M('vine'), CK, (-8.4 + i * 3.3, -4.6 + util.R.uniform(-0.2, 0.2)), r=0.45))
    return place(objs, cx, cy, rotz)
