# -*- coding: utf-8 -*-
"""Z06 锤音院（锤与砧）：矮壮石厅 + 阶梯平台屋顶 + 辉纹带 + 锻场烟囱 + 门前铁砧。"""
import math
from math import pi, radians as D, cos, sin
from .. import geo
from .common import place, yard_rot, yard_center
from .. import layout

CK = 'Z06_HAM'

def build(M):
    y = layout.YARDS['hamm']
    cx, cy = yard_center(y['theta'], y['r'])
    rotz = yard_rot(y['theta'])
    objs = []
    rock, slate = M('rock'), M('slate')
    copper, glow = M('glaze_copper'), M('window')
    iron, dark = M('iron'), M('plank_dark')

    # 石厅（厚墙）
    objs.append(geo.box('HAM_hall', 13, 10, 6.5, rock, ckey=CK, loc=(0, 1.0, 0.2 + 3.25)))
    # 阶梯平台屋顶（两级，可上人）
    objs.append(geo.box('HAM_plat1', 13.7, 10.7, 0.5, slate, ckey=CK, loc=(0, 1.0, 6.85)))
    objs.append(geo.box('HAM_plat2', 8.5, 7.5, 0.5, slate, ckey=CK, loc=(0, 1.0, 7.35)))
    objs.append(geo.box('HAM_parapet_f', 13.7, 0.3, 0.9, rock, ckey=CK, loc=(0, -4.45, 7.3)))
    objs.append(geo.box('HAM_parapet_b', 13.7, 0.3, 0.9, rock, ckey=CK, loc=(0, 6.45, 7.3)))
    objs.append(geo.box('HAM_parapet_l', 0.3, 11.0, 0.9, rock, ckey=CK, loc=(-6.85, 1.0, 7.3)))
    objs.append(geo.box('HAM_parapet_r', 0.3, 11.0, 0.9, rock, ckey=CK, loc=(6.85, 1.0, 7.3)))
    # 辉纹带 ×3（铜色方回纹浮雕）
    for i, zz in enumerate([2.2, 3.6, 5.0]):
        objs += geo.carve_band(f'HAM_runi{i}', 8.2, copper, CK, loc=(0, -4.05, 0.2 + zz), h=0.3, n=34, depth=0.05)
    # 门（厚石门）
    objs.append(geo.box('HAM_doorframe', 2.6, 0.5, 3.4, dark, ckey=CK, loc=(0, -4.05, 0.2 + 1.7)))
    objs.append(geo.box('HAM_door', 2.0, 0.2, 3.0, M('iron'), ckey=CK, loc=(0, -4.2, 0.2 + 1.55)))
    # 锻场（东侧连体，单坡）
    objs.append(geo.box('HAM_forge', 9, 6, 4.4, rock, ckey=CK, loc=(10.0, 1.0, 0.2 + 2.2)))
    objs.append(geo.box('HAM_forgeroof', 9.8, 5.4, 0.25, slate, ckey=CK, loc=(10.0, 1.0, 4.85), rot=(0, 0.18, 0)))
    # 大烟囱 + 熏黑
    objs.append(geo.ngon('HAM_chimney', 10, 0.62, 8.0, rock, loc=(10.0, -1.2, 4.4), ckey=CK, r_top=0.5))
    objs.append(geo.ngon('HAM_chimtop', 10, 0.52, 0.5, M('smoke_stain'), loc=(10.0, -1.2, 8.5), ckey=CK, r_top=0.46))
    objs.append(geo.ngon('HAM_chimring', 10, 0.75, 0.3, rock, loc=(10.0, -1.2, 4.3), ckey=CK))
    # 炉窗（发光）
    objs += geo.win_arch('HAM_firewin', 1.6, 1.2, rock, glow, CK, loc=(5.2, 1.0, 2.0), rot=(0, 0, pi / 2), frame=0.14)
    # 门前铁砧
    objs.append(geo.box('HAM_anvil_top', 1.7, 0.55, 0.3, iron, ckey=CK, loc=(0, -5.6, 1.05)))
    objs.append(geo.ngon('HAM_anvil_neck', 8, 0.22, 0.45, iron, ckey=CK, loc=(0, -5.6, 0.7), r_top=0.4))
    objs.append(geo.box('HAM_anvil_base', 1.0, 0.8, 0.4, iron, ckey=CK, loc=(0, -5.6, 0.35)))
    objs += geo.carve_band('HAM_anvil_words', 1.4, M('copper_metal'), CK, loc=(0, -5.6, 1.06), h=0.12, n=9)
    # 材料棚 + 燃料库
    objs.append(geo.box('HAM_shed', 4.2, 3.2, 0.15, M('street'), ckey=CK, loc=(9.5, -4.2, 0.25)))
    for i in range(3):
        objs.append(geo.box(f'HAM_shedpost{i}', 0.18, 0.18, 2.3, dark, ckey=CK, loc=(7.8 + i * 1.7, -5.7, 1.35)))
    objs.append(geo.box('HAM_shedroof', 4.6, 3.6, 0.14, slate, ckey=CK, loc=(9.5, -4.2, 2.6), rot=(0.1, 0, 0)))
    for i in range(4):
        objs.append(geo.box(f'HAM_wood{i}', 1.6, 0.5, 0.4, M('plank'), ckey=CK,
                            loc=(9.2 + (i % 2) * 0.2, -4.2 + (i // 2) * 0.55, 0.5 + (i % 2) * 0.35), rot=(0, 0, 0.3 * i)))
    objs.append(geo.ngon('HAM_fuel', 10, 1.75, 3.0, rock, loc=(-6.2, -5.0, 1.7), ckey=CK))
    objs.append(geo.ngon('HAM_fuelcap', 10, 1.9, 0.7, slate, ckey=CK, loc=(-6.2, -5.0, 3.5), r_top=0.1))
    # 院墙矮
    objs.append(geo.box('HAM_wf', 13.5, 0.4, 1.2, rock, ckey=CK, loc=(0, -7.0, 0.8)))
    objs.append(geo.box('HAM_wb', 13.5, 0.4, 1.2, rock, ckey=CK, loc=(0, 7.6, 0.8)))
    return place(objs, cx, cy, rotz)
