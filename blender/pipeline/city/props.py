# -*- coding: utf-8 -*-
"""Z16 营造：主径/环径 + 行道树 + 灌木 + 花簇 + 14 石灯笼（全岛生活层）。"""
import math
from math import pi, radians as D, cos, sin
from .. import geo, util, layout

CK = 'Z16_PRP'

ZONES_CIRC = [  # (x, y, r) 建筑禁放区
    (0, 0, 6.0), (0, 12, 12.5),
    (cos(D(-12)) * 23.5, sin(D(-12)) * 23.5, 8.0),
    (cos(D(194)) * 23.5, sin(D(194)) * 23.5, 8.5),
    (cos(D(-97)) * 23.5, sin(D(-97)) * 23.5, 8.5),
    (cos(D(83)) * 24.0, sin(D(83)) * 24.0, 9.0),
    (15.5, 21.5, 8.6), (cos(D(140)) * 17.5, sin(D(140)) * 17.5, 7.5),
    (cos(D(-110)) * 26.5, sin(D(-110)) * 26.5, 5.0),
    (cos(D(-70)) * 21.5, sin(D(-70)) * 21.5, 6.0),
    (cos(D(-117)) * 21.0, sin(D(-117)) * 21.0, 4.5),
    (cos(D(-45)) * 30.0, sin(D(-45)) * 30.0, 7.0),
]

def _near_zone(x, y):
    for (zx, zy, zr) in ZONES_CIRC:
        if (x - zx) ** 2 + (y - zy) ** 2 < zr * zr:
            return True
    return False

def _on_grave(x, y):
    rr = math.hypot(x, y)
    th = math.degrees(math.atan2(y, x))
    return 145 < th < 195 and rr > 23.5

def main_path_pts():
    """山门 → 广场 的弧线主径采样点"""
    pts = []
    for t in range(0, 13):
        u = t / 12
        th = -45 + (45 + 12) * (1 - (1 - u) ** 1.6)   # 从山门弯向广场
        rr = 30 - (30 - 14.5) * u
        pts.append(layout.pos(th, rr))
    pts.append(layout.pos(0, 14.5))
    return pts

def build(M):
    objs = []
    street = M('street')
    # ---- 主径 ----
    pts = main_path_pts()
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]; x1, y1 = pts[i + 1]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        ang = math.atan2(y1 - y0, x1 - x0)
        L = math.hypot(x1 - x0, y1 - y0) + 0.4
        objs.append(geo.box(f'PRP_main{i}', L, 2.2, 0.1, street, ckey=CK,
                            loc=(mx, my, 0.10), rot=(0, 0, ang)))
    # ---- 环径（r 24.3，跳过建筑） ----
    th = -180.0
    while th < 180:
        ang = th + 1.5
        mid = th + 0.75
        if not layout.blocked(mid):
            x0, y0 = layout.pos(th, 24.3)
            x1, y1 = layout.pos(th + 1.5, 24.3)
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            a = math.atan2(y1 - y0, x1 - x0)
            objs.append(geo.box(f'PRP_ring{int(th)}', 1.85, 1.35, 0.09, street, ckey=CK,
                                loc=(mx, my, 0.09), rot=(0, 0, a)))
        th += 1.5
    # ---- 行道树（主径两侧8） ----
    for i in range(1, 9):
        u = i / 9
        idx = min(int(u * (len(pts) - 1)), len(pts) - 2)
        x0, y0 = pts[idx]; x1, y1 = pts[idx + 1]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L
        side = 1 if i % 2 else -1
        tx, ty = mx + nx * 2.6 * side, my + ny * 2.6 * side
        if _near_zone(tx, ty) or _on_grave(tx, ty):
            continue
        objs += geo.tree(f'PRP_street{i}', 'round', M('bark'), M('leaf'), CK, (tx, ty),
                         s=util.R.uniform(0.95, 1.3), crown=1.35)
    # ---- 宿舍环间隙树 ×9 ----
    done = 0
    tries = 0
    while done < 9 and tries < 300:
        tries += 1
        th = util.R.uniform(-180, 180)
        if layout.blocked(th):
            continue
        r = util.R.uniform(24.6, 26.5)
        x, y = layout.pos(th, r)
        if _on_grave(x, y) or _near_zone(x, y):
            continue
        if not layout.blocked(th + 8) and not layout.blocked(th - 8):
            objs += geo.tree(f'PRP_dor{done}', 'round', M('bark'), M('leaf'), CK, (x, y),
                             s=util.R.uniform(0.7, 0.95), crown=1.0)
            done += 1
    # ---- 海心临崖树 ×4（冠偏崖外） ----
    for i, th in enumerate([70, 78, 88, 96]):
        x, y = layout.pos(th, 27.0)
        objs += geo.tree(f'PRP_sea{i}', 'round', M('bark'), M('leaf'), CK, (x, y),
                         s=1.0, crown=1.1)
    # ---- 广场边树 ×2 ----
    for (tx, ty) in [(-12.5, 14.5), (12.5, 17.5)]:
        objs += geo.tree(f'PRP_plaza{tx}', 'round', M('bark'), M('leaf'), CK, (tx, ty), s=0.9, crown=1.1)
    # ---- 灌木 ×40 ----
    done = 0; tries = 0
    while done < 40 and tries < 700:
        tries += 1
        th = util.R.uniform(-180, 180)
        r = util.R.uniform(5.5, 27.0)
        x, y = layout.pos(th, r)
        if math.hypot(x, y) < 5.0 or _near_zone(x, y) or _on_grave(x, y):
            continue
        if 23.2 < math.hypot(x, y) < 25.2 and not layout.blocked(th):
            continue
        if abs(math.hypot(x, y) - 21.5) < 1.8 and not layout.blocked(th):
            continue
        mat = util.R.choice([M('leaf'), M('vine'), M('moss')])
        objs.append(geo.bush(f'PRP_bush{done}', mat, CK, (x, y), r=util.R.uniform(0.35, 0.75)))
        done += 1
    # ---- 花簇 ×60（金/白/蓝，无紫） ----
    mats = [M('flower_gold'), M('flower_white'), M('flower_blue')]
    done = 0; tries = 0
    while done < 60 and tries < 900:
        tries += 1
        th = util.R.uniform(-180, 180)
        r = util.R.uniform(3.0, 26.5)
        x, y = layout.pos(th, r)
        if math.hypot(x, y) < 4.2 or _near_zone(x, y) or _on_grave(x, y):
            continue
        if abs(math.hypot(x, y) - 21.5) < 1.7 and not layout.blocked(th):
            continue
        objs += geo.flower_cluster(f'PRP_fl{done}', util.R.choice(mats), CK, (x, y),
                                   n=util.R.randint(4, 7), r=util.R.uniform(0.3, 0.5))
        done += 1
    # ---- 14 石灯笼 ----
    for i, (th, rr) in enumerate(layout.LANTERNS):
        r = min(rr, 28.2)
        x, y = layout.pos(th, r)
        if _on_grave(x, y) or _near_zone(x, y):
            continue
        objs += geo.lantern(f'PRP_light{i}', M('white_smooth'), M('window'), CK, (x, y), s=1.0)
    return objs
