# -*- coding: utf-8 -*-
"""Z11 山门（船首岬）：石阶 + 双柱弧形楣星徽 + 金翼日 + 守门石像 + 白板墙 + 吊篮泊位。"""
import math
from math import pi, radians as D, cos, sin
from .. import geo, layout
from .common import place

CK = 'Z11_GAT'
THETA = -45.0

def build(M):
    objs = []
    white, black = M('white_smooth'), M('blackstone')
    gold, wood = M('gold'), M('plank_dark')
    r_rim = 32.6  # 船首岬半径
    gx, gy = layout.pos(THETA, 29.0)
    rotz = D(THETA) - pi / 2      # -Y = 朝岛心，+Y = 朝海
    def P(y, x=0.0, z=0.0):
        # 局部 (x, y, z) → 世界（y 沿径向向外）
        c, s = cos(rotz), sin(rotz)
        return (gx + x * c - y * s, gy + x * s + y * c, z)

    # 石阶（7 级向外下）
    objs.append(geo.stair('GAT_steps', 7, 3.2, 0.2, 0.5, white, ckey=CK, loc=P(2.2, 0, 0.9 - 3.4 * 0), rot=(0, 0, rotz + pi)))
    objs[-1].location = P(2.2, 0, 0.55)
    # 垂带石
    for s in (1, -1):
        objs.append(geo.box(f'GAT_cheek{s}', 0.4, 4.4, 1.2, white, ckey=CK, loc=P(2.6, s * 1.95, 0.45), rot=(0, 0.62, rotz)))
    # 双石柱
    for s in (1, -1):
        objs.append(geo.ngon(f'GAT_post{s}', 12, 0.34, 4.4, white, loc=P(3.6, s * 2.1, 2.4), ckey=CK, uvscale=0.8))
        objs.append(geo.box(f'GAT_postbase{s}', 0.95, 0.95, 0.5, white, ckey=CK, loc=P(3.6, s * 2.1, 0.35)))
    # 弧形楣（三段弯梁，沿 x 拱起）+ 星徽
    for k, (xo, zc, tilt) in enumerate([(-1.5, 5.05, D(-24)), (0.0, 5.4, 0.0), (1.5, 5.05, D(24))]):
        objs.append(geo.box(f'GAT_arc{k}', 1.75, 0.8, 0.7, white, ckey=CK,
                            loc=P(3.6, xo, zc), rot=(0, tilt, rotz)))
    # 星徽（八芒：双正方形）
    objs.append(geo.ngon('GAT_starA', 4, 1.05, 0.14, white, loc=P(3.6, 0, 6.2), ckey=CK, rot=(pi / 2, 0, 0), phase=pi / 4))
    objs.append(geo.ngon('GAT_starB', 4, 1.05, 0.14, white, loc=P(3.6, 0, 6.2), ckey=CK, rot=(pi / 2, 0, pi / 4), phase=pi / 4))
    # 金翼日
    objs.append(geo.ngon('GAT_sun', 12, 0.5, 0.16, gold, loc=P(3.6, 0, 7.0), ckey=CK, rot=(pi / 2, 0, 0)))
    for s in (1, -1):
        objs.append(geo.poly_prism(f'GAT_wings{s}', [(0, 0), (1.1, 0.3), (1.0, 0.7), (0.2, 0.45)], 0.09,
                                   gold, loc=P(3.6, 0, 6.75), rot=(0, 0, s * pi / 2), ckey=CK))
    # 守门石像（矮人左、精灵右——剪影式）
    objs += geo.statue('GAT_dwarf', 'dwarf', M('grave'), CK, P(4.0, -2.9, 0), rot=(0, 0, rotz), h=2.3)
    objs += geo.statue('GAT_elf', 'elf', M('grave'), CK, P(4.0, 2.9, 0), rot=(0, 0, rotz), h=2.3)

    # 白板墙（门楼北侧 θ≈-56）
    bx, by = layout.pos(-56, 27.6)
    b_rot = D(-56) - pi / 2 + pi
    objs.append(geo.box('GAT_boardframe', 5.6, 0.3, 2.6, white, ckey=CK, loc=(bx, by, 1.4), rot=(0, 0, b_rot)))
    objs.append(geo.box('GAT_board', 5.0, 0.12, 2.0, M('darkboard'), ckey=CK,
                        loc=(bx + 0.16 * cos(b_rot), by + 0.16 * sin(b_rot), 1.35), rot=(0, 0, b_rot)))
    objs.append(geo.box('GAT_boardstep', 1.6, 0.6, 0.3, white, ckey=CK, loc=(bx, by, 0.25), rot=(0, 0, b_rot)))

    # 吊篮泊位（门楼南侧 θ≈-38）
    hx, hy = layout.pos(-38, 28.2)
    h_rot = D(-38) - pi / 2 + pi
    for s in (1, -1):
        px = hx + s * 1.7 * cos(h_rot), hy + s * 1.7 * sin(h_rot)
        objs.append(geo.box(f'GAT_liftpost{s}', 0.4, 0.4, 5.8, wood, ckey=CK, loc=(px[0], px[1], 2.9), rot=(0, 0, h_rot)))
    objs.append(geo.box('GAT_liftbeam', 4.4, 0.35, 0.35, wood, ckey=CK, loc=(hx, hy, 5.9), rot=(0, 0, h_rot)))
    objs.append(geo.ring_tube('GAT_pulley', 0.32, 0.06, M('iron'), (hx, hy, 5.65), CK, n=12, m=5, rot=(pi / 2, 0, 0)))
    # 吊篮（悬于崖下）
    objs += geo.basket('GAT_basket', M('plank'), M('rope'), CK, (hx, hy, -1.6), r=0.95, h=0.75)
    objs.append(geo.rope('GAT_hangA', M('rope'), CK, (hx - 0.8, hy, 5.9), (hx, hy, -1.0), sag=0.3, r=0.035))
    objs.append(geo.rope('GAT_hangB', M('rope'), CK, (hx + 0.8, hy, 5.9), (hx, hy, -1.0), sag=0.3, r=0.035))
    objs.append(geo.rope('GAT_haul', M('rope'), CK, (hx, hy - 2.0 * cos(h_rot) * 0, hy), (hx, hy, 5.9), sag=0.8, r=0.03))
    objs[-1].location = (hx, hy, 0.4)
    # 缆绳垂向崖下（双股，12）
    objs.append(geo.rope('GAT_droplineA', M('rope'), CK, (hx - 0.35, hy, 5.9), (hx - 0.5, hy, -12), sag=0.4, r=0.028))
    objs.append(geo.rope('GAT_droplineB', M('rope'), CK, (hx + 0.35, hy, 5.9), (hx + 0.5, hy, -12), sag=0.4, r=0.028))
    # 限载牌（813 斤）
    objs.append(geo.box('GAT_813', 0.7, 0.05, 0.5, M('paper'), ckey=CK, loc=(hx - 1.2 * sin(h_rot), hy + 1.2 * cos(h_rot), 3.2), rot=(0, 0, h_rot)))
    return objs
