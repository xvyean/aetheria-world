# -*- coding: utf-8 -*-
"""Z10 宿舍环：21 栋四色小屋（±4°朝向差）+ 旧地基空位（15栋/22栋）+ 木板药房。"""
import math
from math import pi, radians as D, cos, sin
from .. import geo, util, layout
from .common import place

CK = 'Z10_DOR'

def seg_color(theta):
    """按 θ 归属四院段色"""
    for (a0, a1, key) in [(-34, 4, 'glaze_gold'), (183, 207, 'glaze_green'),
                          (-106, -88, 'glaze_copper'), (72, 96, 'glaze_blue')]:
        if a0 <= theta <= a1:
            return key
    # 其余按就近原则（环带色）
    return ['glaze_gold', 'glaze_green', 'glaze_copper', 'glaze_blue'][
        int((theta + 180) // 90) % 4]

def free_arcs():
    """未被建筑占据的 θ 区间（度）"""
    blocked = sorted(layout.DORM_BLOCKED)
    arcs, cur = [], -180.0
    for (a, b) in blocked:
        if cur < a:
            arcs.append((cur, a))
        cur = max(cur, b)
    if cur < 180:
        arcs.append((cur, 180))
    return arcs

def house(M, tag, theta, r, roof_key, ckey):
    mat_wall = M('plaster')
    glow = M('window')
    objs = []
    # 基座
    objs.append(geo.box(f'{tag}_base', 6.2, 4.2, 0.5, M('stone_smooth'), ckey=ckey, loc=(0, 0, 0.25)))
    # 屋身
    objs.append(geo.box(f'{tag}_wall', 6.2, 4.2, 2.9, mat_wall, ckey=ckey, loc=(0, 0, 0.5 + 1.45)))
    # 坡顶（院色）+ 檐口
    objs += geo.gable_roof(f'{tag}_roof', 6.9, 5.0, 1.5, M(roof_key), ckey, loc=(0, 0, 3.4), over=0.45)
    # 门（朝院心 = 局部 -Y）+ 台阶
    objs.append(geo.box(f'{tag}_door', 0.95, 0.1, 2.0, M('plank_dark'), ckey=ckey, loc=(0, -2.12, 1.5)))
    objs.append(geo.box(f'{tag}_step1', 1.4, 0.5, 0.16, M('white_smooth'), ckey=ckey, loc=(0, -2.5, 0.58)))
    objs.append(geo.box(f'{tag}_step2', 1.4, 0.5, 0.16, M('white_smooth'), ckey=ckey, loc=(0, -2.95, 0.42)))
    # 窗前（2）+ 侧窗（1）
    for s in (1, -1):
        objs += geo.win_arch(f'{tag}_win{s}', 0.85, 1.1, mat_wall, glow, CK, loc=(s * 1.7, -2.13, 1.9), frame=0.09, bars=1)
    objs += geo.win_arch(f'{tag}_winside', 0.8, 0.9, mat_wall, glow, CK, loc=(3.13, -0.6, 1.9), rot=(0, 0, pi / 2), frame=0.09, bars=1)
    # 烟囱（随房屋）
    objs.append(geo.box(f'{tag}_chim', 0.5, 0.5, 1.3, M('stone_smooth'), ckey=ckey,
                        loc=(2.2 * (1 if util.R.random() > 0.5 else -1), 1.3, 3.9)))
    # 门前小灯笼
    objs.append(geo.box(f'{tag}_lamppost', 0.06, 0.06, 1.5, M('wood_dark'), ckey=ckey, loc=(1.35, -2.3, 1.35)))
    objs.append(geo.ngon(f'{tag}_lamp', 6, 0.13, 0.22, M('lamp'), ckey=ckey, loc=(1.35, -2.3, 2.15), r_top=0.1))
    # 柴堆
    objs.append(geo.box(f'{tag}_wood', 0.9, 0.4, 0.35, M('plank'), ckey=ckey,
                        loc=(-2.4, 2.2, 0.72), rot=(0, 0, util.R.uniform(-0.2, 0.2))))
    # 朝向 ±4° 差
    rotz = D(theta) - pi / 2 + util.R.uniform(-D(4), D(4))
    ox, oy = layout.pos(theta, r)
    return place(objs, ox, oy, rotz)

def build(M):
    objs = []
    arcs = free_arcs()
    total = sum(b - a for a, b in arcs)
    # 21 栋按弧长均布
    targets = [-(total / 2) + total * (i + 0.5) / layout.DORM_N for i in range(layout.DORM_N)]
    # 找每个目标的 θ
    pos_list = []
    for t in targets:
        acc = -total / 2
        for a, b in arcs:
            if acc + (b - a) >= t:
                pos_list.append(a + (t - acc))
                break
            acc += (b - a)
    for i, theta in enumerate(pos_list):
        # 避开空位（113°±2.5）
        if abs(theta - layout.DORM_VOID_THETA) < 2.6:
            continue
        jitter = theta + 2.2 * math.sin(i * 2.7)  # 栋距手风琴感
        objs += house(M, f'DOR_{i:02d}', jitter, layout.DORM_R + util.R.uniform(-0.3, 0.3),
                      seg_color(jitter), CK)
    # ---- 空位（第 15 号位 = 旧图纸 22 栋）----
    tv = layout.DORM_VOID_THETA
    vx, vy = layout.pos(tv, layout.DORM_R)
    objs.append(geo.ngon('DOR_void', 24, 2.7, 0.1, M('foundation'), loc=(vx, vy, 0.10), ckey=CK))
    for k in range(14):
        a = D(360 * k / 14 + 4)
        objs.append(geo.box(f'DOR_oldbase{k}', 0.5, 0.3, 0.28, M('grave'), ckey=CK,
                            loc=(vx + cos(a) * 2.6, vy + sin(a) * 2.6, 0.24), rot=(0, 0, a)))
    # 木板药房（占的不是 15 的位置，是 15 的名字）
    off = 3.1
    phx, phy = vx + cos(D(tv + 22)) * off, vy + sin(D(tv + 22)) * off
    ph_rot = D(tv) - pi / 2
    objs.append(geo.box('DOR_clinic', 3.4, 2.6, 2.3, M('plank'), ckey=CK, loc=(phx, phy, 1.35), rot=(0, 0, ph_rot)))
    objs += geo.gable_roof('DOR_clinicroof', 4.0, 3.2, 0.9, M('slate'), CK, loc=(phx, phy, 2.55), rot=(0, 0, ph_rot))
    objs.append(geo.box('DOR_clinicdoor', 0.8, 0.08, 1.8, M('wood_dark'), ckey=CK,
                        loc=(phx - 1.28 * sin(D(tv)), phy + 1.28 * cos(D(tv)), 1.25), rot=(0, 0, ph_rot - pi / 2)))
    # 门牌"15 栋"
    objs.append(geo.box('DOR_plaque', 0.5, 0.05, 0.35, M('paper'), ckey=CK,
                        loc=(phx - 1.32 * sin(D(tv)) + 0.4 * cos(D(tv)),
                             phy + 1.32 * cos(D(tv)) + 0.4 * sin(D(tv)), 2.05), rot=(0, 0, ph_rot - pi / 2)))
    # 药圃（草药）
    objs += geo.flower_cluster('DOR_herb1', M('flower_white'), CK, (phx + 1.9, phy - 0.9), n=5, r=0.6)
    objs += geo.flower_cluster('DOR_herb2', M('flower_gold'), CK, (phx - 1.8, phy + 0.8), n=4, r=0.5)
    return objs
