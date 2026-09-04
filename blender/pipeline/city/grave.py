# -*- coding: utf-8 -*-
"""Z15 名士墓：西缘 27 碑（9 朝岛心/18 朝海）+ 3 块新擦 + 无名碑 + 柏 + 灯。"""
import math
from math import pi, radians as D, cos, sin
from .. import geo, util, layout

CK = 'Z15_GRA'

def build(M):
    objs = []
    a0, a1 = layout.GRAVE_ARC
    R = layout.GRAVE_R
    # 27 碑（含 3 新擦、1 无名）
    cleaned = {4, 15, 22}
    blank = 9
    for i in range(27):
        th = a0 + (a1 - a0) * (i + 0.5) / 27 + util.R.uniform(-0.5, 0.5)
        r = R + util.R.uniform(-0.8, 0.8)
        x, y = layout.pos(th, r)
        # 朝向：9 座朝岛心，18 座朝海
        face_in = i % 3 == 0
        rotz = D(th) + (pi / 2 if not face_in else -pi / 2)
        mat = M('plaster_w') if i in cleaned else M('grave')
        s = util.R.uniform(0.8, 1.1)
        ob = geo.tombstone(f'GRA_{i:02d}', mat, CK, (x, y, 0.1), rot=(pi / 2, 0, rotz), s=s)
        objs.append(ob)
        if i in cleaned:   # 新净（微反光高亮）
            objs.append(geo.box(f'GRA_shine{i}', 0.4 * s, 0.03, 0.5 * s, M('plaster_w'), ckey=CK,
                                loc=(x + cos(D(th)) * 0.09, y + sin(D(th)) * 0.09, 0.85 + 0.25 * s), rot=(0, 0, rotz + pi / 2)))
        if i % 5 == 0:     # 苔痕
            objs.append(geo.bush(f'GRA_moss{i}', M('moss'), CK, (x + cos(D(th + 90)) * 0.45, y + sin(D(th + 90)) * 0.45, 0.1), r=0.3))
        if i == blank:     # 无名碑（白花）
            objs.append(geo.flower_cluster('GRA_flower', M('flower_white'), CK, (x, y, 0.3), n=6, r=0.4))
            objs.append(geo.box('GRA_blackstone', 0.5, 0.3, 0.35, M('blackstone'), ckey=CK,
                                loc=(x + 0.5, y + 0.4, 0.28), rot=(0, 0, rotz)))
    # 柏树 ×3
    for i, (th, rr) in enumerate([(152, 27.5), (168, 27.8), (188, 27.2)]):
        x, y = layout.pos(th, rr)
        objs += geo.tree(f'GRA_cyp{i}', 'pine', M('bark'), M('pine'), CK, (x, y), s=1.5)
    # 石灯 ×2
    for th in [159, 180]:
        x, y = layout.pos(th, R + 1.8)
        objs += geo.lantern(f'GRA_lamp{th}', M('white_smooth'), M('window'), CK, (x, y), s=0.95)
    return objs
