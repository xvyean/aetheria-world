# -*- coding: utf-8 -*-
"""
星槎学院 · 总平面
坐标：x 东、y 北、z 上，单位米。岛 90 × 68。
所有位置都已经做过相互避让校验（环道 0.80R、内栏杆 0.955R、广场 r13）。
"""
import math

TAU = math.pi * 2

PLAZA_R = 13.0
ROAD_K = 0.80        # 环道半径 = ROAD_K * R(θ)
RAIL_IN_K = 0.955
RAIL_OUT_K = 0.992

# 星陨塔
STAR_TOWER = dict(pos=(0.0, 0.0), r=4.6, r_top=3.6, h=36.0, sides=8)

# 四柱（升岛时四学徒抱住的柱）：启 言 锻 怀
PILLARS = [
    dict(pos=(7.07, 7.07), h=6.0, broken=False, house='dawn'),    # 启 · 完整
    dict(pos=(-7.07, 7.07), h=3.6, broken=True, house='speak'),   # 言
    dict(pos=(-7.07, -7.07), h=2.3, broken=True, house='forge'),  # 锻
    dict(pos=(7.07, -7.07), h=4.5, broken=True, house='tide'),    # 怀
]

# 四院塔
DAWN_TOWER = dict(pos=(31.0, 0.0), r=3.0, h=22.0)
SPEAK_TOWER = dict(pos=(-2.0, 22.0), r=3.2, h=12.0, sides=6)
SYCAMORE = dict(pos=(-7.5, 24.5), trunk_r=1.25, h=19.0, crown_r=8.2)
FORGE_TOWER = dict(pos=(0.0, -21.0), w=8.0, h=9.0)
OLD_STEPS = dict(pos=(7.0, -23.5), r=2.2)
TIDE_TOWER = dict(pos=(-28.0, 0.0), L=10.0, W=5.2, h=14.0)
PIER = dict(x0=-33.0, x1=-57.0, y=0.0, w=3.2)
FERRY = dict(pos=(-59.5, 4.0, -1.4), size=6.0)
POOL = dict(pos=(-32.5, -12.5), r=4.4, r_center=math.hypot(32.5, 12.5))
CLOUD_NET = dict(pos=(-30.5, -5.5), yaw=math.radians(180))

# 星穗馆 / 校史馆
GRAIN_HALL = dict(pos=(-21.0, 13.5), r=5.8, floors=7, floor_h=2.45)
HISTORY_HALL = dict(pos=(-11.5, 8.5), size=(6.0, 5.0), yaw=math.radians(35))

# 四院回廊：起点半径、终点 x/y、朝向
CORRIDORS = {
    'dawn': dict(dir=(1, 0), start=PLAZA_R, end=27.6, width=4.0),
    'speak': dict(dir=(0, 1), start=PLAZA_R, end=18.4, width=3.6),
    'forge': dict(dir=(0, -1), start=PLAZA_R, end=16.6, width=4.4),
    'tide': dict(dir=(-1, 0), start=PLAZA_R, end=19.0, width=3.6),
}

# 星潮厅 / 灶房 / 梯田 / 羊圈 / 马圈
TIDE_HALL = dict(pos=(17.5, -14.0), L=18.0, W=7.0, h=5.0, yaw=math.radians(50))
KITCHEN = dict(pos=(22.0, -17.8), size=(5.0, 4.0), h=3.0, yaw=math.radians(50))
TERRACES = dict(theta0=math.radians(-33), theta1=math.radians(-17), radii=(35.3, 37.1, 38.9))
GOAT_PEN = dict(pos=(22.2, -24.7), size=(4.0, 3.0), yaw=math.radians(-48))
PADDOCK = dict(theta=math.radians(22), r=37.0, size=(5.5, 4.2))

# 烬园 / 熄灯钟楼
EMBER_GARDEN = dict(pos=(-12.0, -15.0), r=5.5)
BELL_TOWER = dict(pos=(-8.5, -12.5), w=1.7, h=11.0)

# 宿舍：(θ°, side)  side=+1 环道外侧, -1 内侧
DORMS_NE = [(18, -1), (31, -1), (44, -1), (57, -1), (70, -1),
            (32, 1), (44, 1), (56, 1), (68, 1), (80, 1), (92, 1), (104, 1), (116, 1), (128, 1)]
DORMS_SW = [(-142, -1), (-130, -1), (-112, -1),
            (-146, 1), (-134, 1), (-122, 1), (-110, 1), (-98, 1)]
DORM_SIZE = (5.4, 4.4)
DORM_IN_OFF = 3.4
DORM_OUT_OFF = 3.3

# 广场灯柱：八角顶点（避开四条回廊）
PLAZA_LAMPS = [math.radians(a) for a in (22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5)]

# 找平垫（x, y, 半径, 高度 None=取中心地面）
def pads():
    P = []
    P.append((TIDE_HALL['pos'][0], TIDE_HALL['pos'][1], 11.5, None))
    P.append((KITCHEN['pos'][0], KITCHEN['pos'][1], 4.2, None))
    P.append((FORGE_TOWER['pos'][0], FORGE_TOWER['pos'][1], 6.5, None))
    P.append((GRAIN_HALL['pos'][0], GRAIN_HALL['pos'][1], 7.5, None))
    P.append((SPEAK_TOWER['pos'][0], SPEAK_TOWER['pos'][1], 5.0, None))
    P.append((DAWN_TOWER['pos'][0], DAWN_TOWER['pos'][1], 5.0, None))
    P.append((TIDE_TOWER['pos'][0], TIDE_TOWER['pos'][1], 7.0, None))
    P.append((POOL['pos'][0], POOL['pos'][1], 6.8, None))
    P.append((EMBER_GARDEN['pos'][0], EMBER_GARDEN['pos'][1], 6.5, None))
    P.append((HISTORY_HALL['pos'][0], HISTORY_HALL['pos'][1], 4.5, None))
    P.append((GOAT_PEN['pos'][0], GOAT_PEN['pos'][1], 3.2, None))
    return P
