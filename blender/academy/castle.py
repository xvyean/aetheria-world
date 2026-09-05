# -*- coding: utf-8 -*-
"""
星槎学院 · 旧学宫主堡
--------------------
岛心北侧的城堡主体：大礼堂 + 群塔 + 雉堞城墙，构成"霍格沃茨式"天际线。
与中央星陨塔（学术纪念碑）分工：星陨塔是"校"，主堡是"城"。
全部构件复用 parts 库，保证与内城同一精度语言。
"""
import math
import random
from mathutils import Vector

from util import *
from parts import *
import island as IS
import layout as LY

KX, KY = 4.0, 56.0          # 主堡中心


def _gz(x, y):
    return IS.ground_h(x, y)


def build_castle(M, C):
    col = C['tower']
    rng = random.Random(31)
    gz = _gz(KX, KY)
    objs = []

    # 台基：把主堡整体抬高一阶，显得踞于岩台
    terrace = box_grid('Castle_Terrace', (46, 34, 3.6), (KX, KY, gz - 0.8), col, M['stone_grey'], cell=1.2)
    stone_vcol(terrace, PAL['stone_grey'], seed=11, course=0.6, grime=0.3)
    objs.append(terrace)
    base_z = gz + 2.6

    # ---- 大礼堂 ----
    gh = (KX, KY - 4.0)
    L, W, H = 28.0, 14.0, 13.0
    hall = box_grid('Castle_Hall', (L, W, H), (gh[0], gh[1], base_z), col, M['stone_cream'], cell=0.9)
    stone_vcol(hall, PAL['stone_cream'], seed=21, course=0.65, grime=0.26)
    objs.append(hall)
    # 陡屋顶
    roof = gable_roof('Castle_HallRoof', L + 1.0, W + 1.0, 6.5, (gh[0], gh[1], base_z + H),
                      col, M['slate'], yaw=0.0, overhang=0.8, ridge_mat=M['stone_dark'])
    roof_vcol(roof[0], '#4b5563', seed=22, moss_hex=PAL['moss'], moss=0.12)
    objs += roof
    # 扶壁
    for u in (-L / 2 + 2, -L / 6, L / 6, L / 2 - 2):
        for side in (-1, 1):
            p = Vector((gh[0] + u, gh[1] + side * (W / 2 + 0.3), base_z))
            objs.append(box('Castle_Butt_%d_%d' % (u, side), (0.8, 0.8, H * 0.85), p, col, M['stone_grey'], origin='bottom'))
    # 高侧窗（哥特尖窗，发光）
    for side in (-1, 1):
        for k in range(5):
            u = (-0.5 + (k + 0.5) / 5) * (L - 4)
            p = Vector((gh[0] + u, gh[1] + side * (W / 2 + 0.05), base_z + 6.2))
            objs += window('Castle_HallWin_%d_%d' % (side, k), p, math.pi / 2 * side + (math.pi if side < 0 else 0),
                           1.4, 3.4, C['fx'], M, kind='lancet')
    # 山墙玫瑰窗
    objs += window('Castle_Rose', Vector((gh[0] + L / 2 + 0.05, gh[1], base_z + 8.4)), 0.0, 3.2, 3.2, C['fx'], M, kind='round')

    # ---- 群塔（高低错落）----
    towers = [
        (KX - 17, KY + 9, 4.2, 30, 'tile_dawn'),
        (KX + 17, KY + 9, 4.0, 26, 'tile_tide'),
        (KX - 17, KY - 13, 3.6, 22, 'tile_speak'),
        (KX + 17, KY - 13, 3.6, 24, 'tile_forge'),
        (KX + 9, KY + 13, 4.8, 46, 'slate'),      # 主塔（最高）
        (KX - 6, KY + 15, 3.0, 36, 'slate'),      # 细尖塔
    ]
    for i, (tx, ty, tr, th_, roofk) in enumerate(towers):
        tz = _gz(tx, ty)
        tw = prism('Castle_Tower_%d' % i, tr, th_, 8, (tx, ty, tz - 0.5), col, M['stone_white'], taper=0.82)
        stone_vcol(tw, PAL['stone_white'], seed=30 + i, course=0.6, grime=0.24)
        objs.append(tw)
        rmat = M[roofk] if roofk in M else M['slate']
        objs += pyramid_roof('Castle_TowerRoof_%d' % i, tr + 0.5, tr * 2.2, 8, (tx, ty, tz - 0.5 + th_),
                             col, rmat, overhang=0.5, finial_mat=M['gold'], finial_h=1.4)
        # 塔身窄窗
        for k in range(3):
            a = rng.uniform(0, TAU)
            p = Vector((tx + math.cos(a) * (tr * 0.9), ty + math.sin(a) * (tr * 0.9), tz + 4 + k * (th_ / 4)))
            objs += window('Castle_TWin_%d_%d' % (i, k), p, a, 0.9, 2.0, C['fx'], M, kind='lancet')

    # ---- 雉堞城墙（连接四角塔）----
    corners = [(KX - 16, KY + 8), (KX + 16, KY + 8), (KX + 16, KY - 12), (KX - 16, KY - 12)]
    for i in range(4):
        a = Vector((corners[i][0], corners[i][1], 0))
        b = Vector((corners[(i + 1) % 4][0], corners[(i + 1) % 4][1], 0))
        mid = (a + b) * 0.5
        d = b - a
        length = d.length
        yaw = math.atan2(d.y, d.x)
        wz = _gz(mid.x, mid.y)
        wall = box_grid('Castle_Wall_%d' % i, (length, 1.2, 6.0), (mid.x, mid.y, wz - 0.3), col, M['stone_grey'], cell=0.8, rot=(0, 0, yaw))
        stone_vcol(wall, PAL['stone_grey'], seed=40 + i, course=0.55, grime=0.3)
        objs.append(wall)
        # 墙顶走道 + 雉堞
        objs.append(box('Castle_WallWalk_%d' % i, (length, 1.8, 0.3), (mid.x, mid.y, wz + 5.7), col, M['stone_grey'], rot=(0, 0, yaw)))
        n_mer = max(3, int(length / 2.2))
        for k in range(n_mer):
            u = (-0.5 + (k + 0.5) / n_mer) * length
            p = mid + Vector((math.cos(yaw) * u, math.sin(yaw) * u, 6.0))
            objs.append(box('Castle_Mer_%d_%d' % (i, k), (0.7, 1.3, 0.7), p, col, M['stone_grey'], rot=(0, 0, yaw), origin='bottom'))

    # 主堡旗
    for (fx_, fy_), hk in zip([corners[0], corners[1]], ['dawn', 'tide']):
        objs += flag('Castle_Flag_%s' % hk, (fx_, fy_, _gz(fx_, fy_) + 20), 5.0, 2.4,
                     C['fx'], M['cloth_' + hk], M['iron'], fx_coll=C['fx'])
    return objs
