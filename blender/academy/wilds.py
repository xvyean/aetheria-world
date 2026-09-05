# -*- coding: utf-8 -*-
"""
星槎学院 · 外环荒野
------------------
扩岛后在城墙与岛沿之间的外环地带铺设：
- 大片密林（柏/阔叶混交，噪声聚簇，沉基防浮空）
- 东脊山脚的散置巨石
职责：只往 C['city_veg'] _collection_ 里加自然物，不碰内城。
"""
import math
import random
from mathutils import Vector

from util import *
from parts import *
import island as IS
import layout as LY
from buildings_life import tree_cypress, tree_broad


def _in_lake(x, y, z):
    return z < IS.LAKE_Z + 0.5


def build_forest(M, C):
    col = C['city_veg']
    rng = random.Random(777)
    placed = 0
    tries = 2400
    for i in range(tries):
        th = rng.uniform(0, TAU)
        R = IS.island_radius(th)
        d = rng.uniform(220.0, R * 0.97)
        x, y = math.cos(th) * d, math.sin(th) * d
        z = IS.ground_h(x, y)
        if _in_lake(x, y, z):
            continue
        if z > 34.0:                      # 雪线以上不长树
            continue
        rr = IS.road_r(th)
        if abs(d - rr) < 3.2:             # 让开环道
            continue
        cl = 0.5 + 0.5 * fbm(x / 42.0, y / 42.0, 0.0, oct=2, seed=51)
        if rng.random() > 0.38 + 0.55 * cl:   # 聚簇：噪声高处更密
            continue
        s = rng.uniform(1.1, 2.0) * (0.9 + 0.4 * cl)   # 更大，形成"密林"体量
        loc = (x, y, z - 0.45)            # 沉基，杜绝浮空/穿模
        if rng.random() < 0.75:
            tree_cypress('Wild_Pine_%04d' % i, loc, s, M, col, rng)
        else:
            tree_broad('Wild_Oak_%04d' % i, loc, s, M, col, rng)
        placed += 1
    return placed


def build_rocks(M, C):
    rng = random.Random(888)
    for i in range(16):
        th = rng.uniform(-0.7, 0.7)       # 东山扇区
        d = rng.uniform(246.0, 320.0)
        x, y = math.cos(th) * d, math.sin(th) * d
        z = IS.ground_h(x, y)
        s = rng.uniform(2.0, 6.5)
        r = ico('Wild_Rock_%02d' % i, s, (x, y, z + s * 0.25), C['city_veg'], M['rock'], subdiv=2, smooth=False)
        IS.rock_displace(r, rng, s)
        set_vcol_const(r, PAL['rock_b'], jitter=0.2, seed=400 + i)
    # 湖岸几块立石
    for i in range(6):
        a = TAU * i / 6 + rng.uniform(-0.4, 0.4)
        rr = rng.uniform(60.0, 70.0)
        x = IS.LAKE['cx'] + math.cos(a) * rr
        y = IS.LAKE['cy'] + math.sin(a) * rr * (IS.LAKE['sy'] / IS.LAKE['sx'])
        s = rng.uniform(1.2, 3.0)
        r = ico('Lake_Stone_%02d' % i, s, (x, y, IS.LAKE_Z + 0.3), C['city_veg'], M['rock'], subdiv=1, smooth=False)
        IS.jitter_verts(r, 0.3, rng)
        set_vcol_const(r, PAL['rock_a'], jitter=0.2, seed=500 + i)


def build_all(M, C):
    n = build_forest(M, C)
    build_rocks(M, C)
    return n
