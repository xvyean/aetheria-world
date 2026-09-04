# -*- coding: utf-8 -*-
"""全岛布局常量表 —— 《建筑志 v2》与几何代码的唯一对接点。
坐标系：X 东，Y 南，Z 上。θ：东 0°，南 90°，西 180°，北 −90°。
pos(theta_deg, r) -> (x, y)
"""
import math
from math import radians as D

def pos(theta, r):
    return (math.cos(D(theta)) * r, math.sin(D(theta)) * r)

RIM = 29.6            # 岛缘基准半径
TOP_Z = 0.0           # 岛顶参考面
ISLAND_DEPTH = 26.0   # 岛底深度（船底中心）

# ---- 核心 ----
TOWER_C = (0, 0)
PLAZA_C = (0, 12)     # 广场圆心（塔正南）
PLAZA_R = 11
ALTAR = (0, 14.5)     # 分选礼台

CLO_LEN = 12.0        # 回廊长（自塔基外沿）
CLO_W = 2.6
CLO_H = 3.2

# ---- 四院（θ, 半径, 旋转偏置°） ----
YARDS = {
    'dawu': dict(theta=-12,  r=23.5, rot=8,   name='晨辉院'),
    'lingu':dict(theta=194,  r=23.5, rot=-6,  name='星语院'),
    'hamm': dict(theta=-97,  r=23.5, rot=4,   name='锤音院'),
    'sea':  dict(theta=83,   r=24.0, rot=-5,  name='海心院'),
}
# 院门（回廊端头）：沿轴向外，位于 r ≈ 塔基沿 + CLO_LEN
DOORS = {'dawu': pos(0, 18.0), 'lingu': pos(180, 18.0),
         'hamm': pos(-90, 18.0), 'sea': pos(90, 18.0)}

# ---- 特殊点 ----
GATE = dict(theta=-45, r=29.5)           # 山门（船首岬）
GATE_POS = pos(GATE['theta'], GATE['r'])
BASKET = pos(-38, 26.5)                  # 吊篮泊位（门楼南侧——θ 更大 = 更南）
BOARD_WALL = pos(-52, 27.2)              # 白板墙（门楼北侧）
POOL_C = pos(55, 25.0)                   # 浮池（东南，悬出岛缘）
POOL_R = 6.5
LIB_C = pos(140, 17.5)                   # 星穗馆（西南）
CLK_C = pos(-110, 26.5)                  # 钟楼（西北）
MESS_C = pos(-70, 21.5)                  # 长桌堂
BATH_C = pos(-117, 21.0)                 # 白石浴场
GRAVE_ARC = (150, 190)                   # 名士墓弧段（θ 范围）
GRAVE_R = 26.0

# ---- 宿舍环 ----
DORM_R = 21.5
DORM_BLOCKED = [                         # 被建筑占据的 θ 区间（度）
    (-34, 4),    # 晨辉院
    (183, 207),  # 星语院
    (-106, -88), # 锤音院
    (72, 96),    # 海心院
    (-56, -34),  # 山门/吊篮
    (-116, -104),# 钟楼
    (48, 66),    # 浮池
    (130, 152),  # 星穗馆
    (-80, -64),  # 长桌堂
    (-126, -112),# 白石浴场
    (152, 196),  # 名士墓
]
DORM_VOID_THETA = 113.0                  # 第 15 号位（= 旧图纸第 22 栋）
DORM_N = 21

# ---- 植被与灯 ----
TREES_STREET = [-24, -18, -12, -6, 2, 8, 14, 20]     # 主径两侧（θ）
LANTERNS = [(-44, 28.6), (-22, 29.0), (0, 29.2), (20, 28.6), (44, 27.6),
            (66, 26.6), (92, 25.8), (112, 24.6), (168, 24.2), (188, 23.6),
            (208, 25.2), (228, 26.6), (246, 27.2), (264, 27.6)]

# ---- 世界场景 ----
COLUMN_TOP_Z = -ISLAND_DEPTH - 2
SEA_Z = -130.0
COLUMN_R = 3.2

def blocked(theta):
    for a, b in DORM_BLOCKED:
        lo, hi = (a, b) if a < b else (b, a)
        if lo <= theta <= hi:
            return True
    return False
