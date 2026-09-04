# -*- coding: utf-8 -*-
"""
星槎学院城·外城扩建区

中央保留旧学宫，本模块在其外建造城墙、林荫大道和七个可辨识的功能区。
建筑使用参数化体块和顶点色，导出时仍可按材质合并以控制 draw call。
"""
import math
import random
from mathutils import Vector

from util import *
from parts import *
import layout as LY
import island as IS


def _segment(name, p0, p1, width, height, col, mat, lift=0.0):
    """在两点之间放置一个沿地表的长方体。"""
    a, b = Vector(p0), Vector(p1)
    d = b - a
    mid = (a + b) * 0.5
    z = (IS.ground_h(a.x, a.y) + IS.ground_h(b.x, b.y)) * 0.5 + lift
    ob = box(name, (math.hypot(d.x, d.y), width, height), (mid.x, mid.y, z), col, mat,
             rot=(0, 0, math.atan2(d.y, d.x)), origin='bottom')
    return ob


def _road(name, p0, p1, width, C, M):
    ob = _segment(name, p0, p1, width, 0.16, C['city_paths'], M['flagstone'], lift=0.04)
    set_vcol_const(ob, PAL['flagstone'], jitter=0.12, seed=hash(name) & 0xffff)
    return ob


def _block(name, pos, size, floors, yaw, roof_key, C, M, banner_key=None, tower=False):
    """外城通用学舍：石基、浅色墙、大屋顶、成排灯窗和扶壁。"""
    x, y = pos
    L, W = size
    gz = IS.ground_h(x, y)
    h = floors * 3.25
    col = C['districts']
    objs = []

    pad = box(name + '_Foundation', (L + 1.8, W + 1.8, 0.55), (x, y, gz - 0.18), col,
              M['stone_grey'], rot=(0, 0, yaw), origin='bottom')
    set_vcol_const(pad, PAL['stone_grey'], jitter=0.10, seed=hash(name) & 0xffff)
    objs.append(pad)
    body = box_grid(name + '_Body', (L, W, h), (x, y, gz + 0.32), col, M['stone_cream'],
                    cell=1.15, rot=(0, 0, yaw))
    stone_vcol(body, PAL['stone_cream'], seed=hash(name) & 0xffff, course=0.7, grime=0.24)
    objs.append(body)

    n = Vector((math.cos(yaw), math.sin(yaw), 0))
    t = Vector((-math.sin(yaw), math.cos(yaw), 0))
    # 长立面的成排灯窗。网格小而可在导出时合并。
    bays = max(3, int(L // 3.2))
    for side in (-1, 1):
        for floor in range(floors):
            for k in range(bays):
                u = (-0.5 + (k + 0.5) / bays) * (L - 2.0)
                p = Vector((x, y, gz + 0.32 + floor * 3.25 + 1.75)) + n * u + t * side * (W / 2 + 0.035)
                win = box('%s_Window_%d_%d_%d' % (name, side, floor, k), (0.82, 0.10, 1.25), p,
                          C['city_fx'], M['window'], rot=(0, 0, yaw))
                win['fx'] = 'window'
                objs.append(win)
    # 扶壁让长楼不像现代盒子。
    for side in (-1, 1):
        for u in (-L / 2 + 0.6, 0.0, L / 2 - 0.6):
            p = Vector((x, y, gz + 0.32)) + n * u + t * side * (W / 2 + 0.35)
            objs.append(box(name + '_Buttress', (0.75, 0.75, h * 0.78), p, col, M['stone_grey'],
                            rot=(0, 0, yaw), origin='bottom'))

    roof_mat = M[roof_key]
    roof_hex = PAL['slate'] if roof_key == 'slate' else (
        '#a8603f' if roof_key == 'roof_terra' else '#4f5f74')
    roof = gable_roof(name + '_Roof', L + 0.8, W + 0.8, min(4.8, W * 0.38),
                      (x, y, gz + 0.32 + h), col, roof_mat, yaw=yaw, overhang=0.65,
                      ridge_mat=M['stone_dark'])
    if roof:
        roof_vcol(roof[0], roof_hex, seed=(hash(name) + 7) & 0xffff)
        objs += roof

    # 中央正门和院旗。
    door_pos = Vector((x, y, gz + 0.32)) - t * (W / 2 + 0.03)
    objs += door(name + '_Door', door_pos, yaw - math.pi / 2, 1.8 if L > 18 else 1.3, 2.7,
                 col, M, arch=True, frame_mat=M['stone_white'])
    if banner_key:
        for u in (-L * 0.22, L * 0.22):
            bp = Vector((x, y, gz + h * 0.68)) + n * u - t * (W / 2 + 0.10)
            objs += banner(name + '_Banner', bp, yaw - math.pi / 2, 1.2, 2.8, col,
                           M['cloth_' + banner_key], pole=True, pole_mat=M['iron'], fx_coll=C['city_fx'])

    if tower:
        for u in (-L / 2, L / 2):
            p = Vector((x, y, gz + 0.15)) + n * u
            tw = prism(name + '_Turret', 2.7, h + 3.0, 8, p, col, M['stone_grey'], taper=0.88)
            stone_vcol(tw, PAL['stone_grey'], seed=(hash(name) + int(u * 10)) & 0xffff)
            objs.append(tw)
            objs += pyramid_roof(name + '_TurretRoof', 2.75, 4.8, 8,
                                 (p.x, p.y, gz + h + 3.15), col, roof_mat,
                                 overhang=0.4, finial_mat=M['gold'], finial_h=1.1)
    return objs


def _gatehouse(name, pos, yaw, house_key, C, M):
    x, y = pos
    gz = IS.ground_h(x, y)
    n = Vector((math.cos(yaw), math.sin(yaw), 0))
    t = Vector((-math.sin(yaw), math.cos(yaw), 0))
    col = C['city_wall']
    objs = []
    for side in (-1, 1):
        p = Vector((x, y, gz)) + t * side * 6.4
        tw = prism(name + '_Tower_%d' % side, 4.1, 14.0, 8, p, col, M['stone_grey'], taper=0.88)
        stone_vcol(tw, PAL['stone_grey'], seed=hash(name + str(side)) & 0xffff)
        objs.append(tw)
        objs += pyramid_roof(name + '_Roof_%d' % side, 4.3, 6.0, 8, (p.x, p.y, gz + 14.2),
                             col, M['tile_' + house_key], overhang=0.5,
                             finial_mat=M['gold'], finial_h=1.2)
    # 门洞保留为空，只用上方连桥压住轮廓。
    bridge = box(name + '_Bridge', (3.8, 8.0, 4.0),
                 Vector((x, y, gz + 9.0)), col, M['stone_cream'], rot=(0, 0, yaw), origin='bottom')
    set_vcol_const(bridge, PAL['stone_cream'], jitter=0.08, seed=hash(name) & 0xffff)
    objs.append(bridge)
    objs += flag(name + '_Flag', (x, y, gz + 13.0), 7.5, 2.1, col,
                  M['cloth_' + house_key], M['iron'], fx_coll=C['city_fx'])
    return objs


def build_city_walls(M, C):
    """椿圆外墙、四座城门与内外两道交通骨架。"""
    objs = []
    A, B, H = LY.CITY_WALL['a'], LY.CITY_WALL['b'], LY.CITY_WALL['h']
    nseg = 96
    gate_angles = (0.0, math.pi / 2, math.pi, math.pi * 1.5)
    for i in range(nseg):
        a0 = TAU * i / nseg
        a1 = TAU * (i + 1) / nseg
        amid = (a0 + a1) * 0.5
        if any(abs(math.atan2(math.sin(amid - ga), math.cos(amid - ga))) < 0.045 for ga in gate_angles):
            continue
        p0 = (math.cos(a0) * A, math.sin(a0) * B, 0)
        p1 = (math.cos(a1) * A, math.sin(a1) * B, 0)
        wall = _segment('CityWall_%03d' % i, p0, p1, 2.8, H, C['city_wall'], M['stone_grey'])
        set_vcol_const(wall, PAL['stone_grey'], jitter=0.13, seed=4100 + i)
        objs.append(wall)
        if i % 6 == 0:
            x, y = p0[0], p0[1]
            gz = IS.ground_h(x, y)
            tower = prism('CityWall_Watch_%02d' % i, 3.4, 11.5, 8, (x, y, gz),
                          C['city_wall'], M['stone_dark'], taper=0.9)
            set_vcol_const(tower, PAL['stone_dark'], jitter=0.12, seed=4200 + i)
            objs.append(tower)
            objs += pyramid_roof('CityWall_WatchRoof_%02d' % i, 3.5, 4.2, 8,
                                 (x, y, gz + 11.7), C['city_wall'], M['slate'],
                                 overhang=0.4, finial_mat=M['iron'], finial_h=0.7)

    objs += _gatehouse('EastGate', (A, 0), 0.0, 'dawn', C, M)
    objs += _gatehouse('NorthGate', (0, B), math.pi / 2, 'speak', C, M)
    objs += _gatehouse('WestGate', (-A, 0), math.pi, 'tide', C, M)
    objs += _gatehouse('SouthGate', (0, -B), -math.pi / 2, 'forge', C, M)

    # 四条 12 米宽大道从古学宫通向城门。
    objs += [_road('GrandRoad_E', (34, 0, 0), (A + 8, 0, 0), 12, C, M),
             _road('GrandRoad_W', (-34, 0, 0), (-A - 8, 0, 0), 12, C, M),
             _road('GrandRoad_N', (0, 30, 0), (0, B + 8, 0), 12, C, M),
             _road('GrandRoad_S', (0, -30, 0), (0, -B - 8, 0), 12, C, M)]
    # 内环学舍大道。
    nroad = 64
    for i in range(nroad):
        a0 = TAU * i / nroad
        a1 = TAU * (i + 0.90) / nroad
        objs.append(_road('InnerBoulevard_%02d' % i,
                          (math.cos(a0) * 142, math.sin(a0) * 101, 0),
                          (math.cos(a1) * 142, math.sin(a1) * 101, 0), 7.5, C, M))
    return objs


def build_scholar_quarter(M, C):
    """北部星语学宫：双庭院讲学楼、大档案馆与观星圆顶。"""
    objs = []
    x, y = LY.DISTRICTS['scholar']['pos']
    objs += _block('Scholar_GrandArchive', (x, y + 3), (34, 14), 4, 0, 'roof_blue', C, M, 'speak', True)
    objs += _block('Scholar_WestLecture', (x - 28, y - 8), (24, 11), 3, math.radians(12), 'roof_blue', C, M, 'speak')
    objs += _block('Scholar_EastLecture', (x + 28, y - 8), (24, 11), 3, math.radians(-12), 'roof_blue', C, M, 'speak')
    gz = IS.ground_h(x, y + 15)
    drum = prism('Scholar_Observatory', 7.2, 18, 12, (x, y + 15, gz), C['districts'], M['stone_white'], taper=0.86)
    set_vcol_const(drum, PAL['stone_white'], jitter=0.08, seed=4401)
    objs.append(drum)
    dome = sphere('Scholar_Dome', 6.4, (x, y + 15, gz + 18), C['districts'], M['patina'],
                  segs=24, rings=12, scale=(1, 1, 0.55), hemi=True)
    objs.append(dome)
    arm = torus('Scholar_Armillary', 3.4, 0.18, (x, y + 15, gz + 23), C['city_fx'], M['gold'], segs=28, rsegs=7)
    arm['fx'] = 'armillary'
    objs.append(arm)
    return objs


def build_dawn_quarter(M, C):
    """东部晨辉演武院：大礼堂、骑术场、决斗台和两翼兵舍。"""
    objs = []
    x, y = LY.DISTRICTS['dawn']['pos']
    objs += _block('Dawn_GreatHall', (x + 18, y), (36, 15), 4, math.pi / 2, 'roof_terra', C, M, 'dawn', True)
    objs += _block('Dawn_NorthWing', (x - 10, y + 25), (27, 10), 3, 0, 'roof_terra', C, M, 'dawn')
    objs += _block('Dawn_SouthWing', (x - 10, y - 25), (27, 10), 3, 0, 'roof_terra', C, M, 'dawn')
    # 长方形演武场与观礼阶。
    gz = IS.ground_h(x - 14, y)
    yard = box('Dawn_TrainingYard', (35, 27, 0.24), (x - 14, y, gz + 0.02), C['city_paths'],
               M['ash'], origin='bottom')
    objs.append(yard)
    for side in (-1, 1):
        for i in range(5):
            objs.append(box('Dawn_Stand_%d_%d' % (side, i), (19, 1.1, 0.45),
                            (x - 14, y + side * (14 + i * 1.1), gz + i * 0.45), C['districts'],
                            M['stone_grey'], origin='bottom'))
    for i in range(6):
        a = TAU * i / 6
        px, py = x - 14 + math.cos(a) * 8, y + math.sin(a) * 8
        objs += lantern_post('Dawn_YardLamp_%d' % i, (px, py, IS.ground_h(px, py)), C['districts'], M, h=4.0, glow_coll=C['city_fx'])
    return objs


def build_forge_quarter(M, C):
    """南部锤音工造院：中央铸堂、六座作坊、仓库和烟囱群。"""
    objs = []
    x, y = LY.DISTRICTS['forge']['pos']
    objs += _block('Forge_Foundry', (x, y), (38, 17), 3, 0, 'slate', C, M, 'forge', True)
    for row in (-1, 1):
        for k in range(3):
            px = x - 28 + k * 28
            py = y + row * 24
            objs += _block('Forge_Workshop_%d_%d' % (row, k), (px, py), (19, 10), 2, 0,
                           'slate', C, M, 'forge')
    for k, (ox, oy, h) in enumerate(((-13, 2, 18), (0, 3, 23), (13, 2, 16), (32, -20, 14))):
        px, py = x + ox, y + oy
        gz = IS.ground_h(px, py)
        ch = cylinder('Forge_Chimney_%d' % k, 1.35, h, (px, py, gz + 8), C['districts'], M['basalt'],
                      segments=12, r_top=0.95)
        set_vcol_const(ch, PAL['basalt'], jitter=0.12, seed=4500 + k)
        objs.append(ch)
    return objs


def build_tide_quarter(M, C):
    """西部海心港区：水院、航海楼、船坞和向城外延伸的云海栈道。"""
    objs = []
    x, y = LY.DISTRICTS['tide']['pos']
    objs += _block('Tide_NavigationHall', (x + 16, y), (34, 14), 4, math.pi / 2,
                   'roof_blue', C, M, 'tide', True)
    objs += _block('Tide_Boathouse_N', (x - 18, y + 25), (27, 11), 2, 0, 'roof_blue', C, M, 'tide')
    objs += _block('Tide_Boathouse_S', (x - 18, y - 25), (27, 11), 2, 0, 'roof_blue', C, M, 'tide')
    # 十字水院和多级码头。
    gz = IS.ground_h(x - 10, y)
    water = box('Tide_WaterCourt', (31, 22, 0.35), (x - 10, y, gz + 0.05), C['city_fx'], M['water'], origin='bottom')
    water['fx'] = 'water'
    objs.append(water)
    for j, yy in enumerate((-15, -7.5, 0, 7.5, 15)):
        objs.append(_segment('Tide_Pier_%d' % j, (x - 27, y + yy, 0), (x - 61, y + yy, 0),
                             2.2, 0.55, C['districts'], M['wood_mid'], lift=0.10))
    return objs


def build_residential_quarters(M, C):
    """东北七年舍街与西北百工/疗愈区，共同形成真正的学院街区。"""
    objs = []
    rng = random.Random(4600)
    rx, ry = LY.DISTRICTS['residence']['pos']
    # 四行宿舍，留下两条横巷与一条主街。
    for row in range(4):
        for col_i in range(4):
            px = rx - 34 + col_i * 22.5
            py = ry - 27 + row * 18.0
            roof = 'roof_terra' if (row + col_i) % 2 == 0 else 'roof_blue'
            objs += _block('Residence_%d_%d' % (row, col_i), (px, py), (16, 8),
                           2 + ((row + col_i) % 3 == 0), 0, roof, C, M,
                           ('dawn', 'speak', 'forge', 'tide')[(row + col_i) % 4])
    sx, sy = LY.DISTRICTS['service']['pos']
    objs += _block('Service_Infirmary', (sx - 18, sy + 10), (32, 14), 3, math.radians(-8),
                   'roof_blue', C, M, 'tide', True)
    objs += _block('Service_Refectories', (sx + 20, sy + 12), (31, 15), 3, math.radians(8),
                   'roof_terra', C, M, 'dawn')
    objs += _block('Service_GuildHall', (sx, sy - 22), (36, 13), 3, 0,
                   'slate', C, M, 'forge', True)
    # 中央市集广场：几排有色棚子。
    for i in range(12):
        px = sx - 24 + (i % 6) * 9.5
        py = sy - 5 + (i // 6) * 8
        gz = IS.ground_h(px, py)
        stall = box('Service_Stall_%02d' % i, (6.5, 4.2, 2.5), (px, py, gz), C['districts'],
                    M['wood_mid'], origin='bottom')
        set_vcol_const(stall, PAL['wood_mid'], jitter=0.12, seed=4700 + i)
        objs.append(stall)
        color_key = ('dawn', 'speak', 'forge', 'tide')[i % 4]
        objs.append(box('Service_Awning_%02d' % i, (7.0, 4.8, 0.20), (px, py, gz + 2.6),
                        C['districts'], M['cloth_' + color_key], origin='bottom'))
    return objs


def build_garden_quarter(M, C):
    """西南星植苑：围墙植物园、玻璃温室、药草花坛和林荫书亭。"""
    objs = []
    x, y = LY.DISTRICTS['garden']['pos']
    # 植物园低墙
    corners = [(x - 42, y - 31, 0), (x + 42, y - 31, 0), (x + 42, y + 31, 0), (x - 42, y + 31, 0)]
    for i in range(4):
        objs.append(_segment('Garden_Wall_%d' % i, corners[i], corners[(i + 1) % 4], 1.0, 2.1,
                             C['districts'], M['stone_grey']))
    # 两座金属骨架温室。
    for k, ox in enumerate((-19, 19)):
        px, py = x + ox, y + 7
        gz = IS.ground_h(px, py)
        body = box('Garden_Glasshouse_%d' % k, (29, 13, 5.5), (px, py, gz), C['districts'],
                   M['glass_dark'], origin='bottom')
        objs.append(body)
        objs += gable_roof('Garden_GlassRoof_%d' % k, 29.5, 13.5, 5.2, (px, py, gz + 5.5),
                           C['districts'], M['patina'], overhang=0.2, ridge_mat=M['gold'])
        for i in range(8):
            u = -12 + i * 3.4
            objs.append(box('Garden_Frame_%d_%d' % (k, i), (0.16, 13.2, 5.5),
                            (px + u, py, gz), C['districts'], M['patina'], origin='bottom'))
    # 药草圃和庭中树。
    rng = random.Random(4800)
    for i in range(28):
        a = TAU * i / 28
        rr = 19 + (i % 4) * 4
        px, py = x + math.cos(a) * rr, y - 15 + math.sin(a) * rr * 0.45
        gz = IS.ground_h(px, py)
        bed = cylinder('Garden_HerbBed_%02d' % i, 1.5, 0.45, (px, py, gz), C['districts'],
                       M['soil'], segments=10)
        set_vcol_const(bed, PAL['soil'], jitter=0.10, seed=4800 + i)
        objs.append(bed)
        bush = ico('Garden_Herb_%02d' % i, rng.uniform(0.7, 1.2), (px, py, gz + 0.55),
                   C['city_veg'], M['leaf'], subdiv=1)
        bush.scale = (1, 1, rng.uniform(0.45, 0.8))
        set_vcol_const(bush, rng.choice([PAL['leaf_a'], PAL['leaf_b'], '#7f9f48']), jitter=0.12, seed=i)
        bush['fx'] = 'foliage'
        objs.append(bush)
    return objs


def build_city_vegetation(M, C):
    """街道树与外墙林带：在城市尺度上提供对照，也分隔七个校区。"""
    objs = []
    rng = random.Random(4900)
    # 四条大道两侧的白杨式行道树。
    pts = []
    for d in range(48, 208, 12):
        for side in (-1, 1):
            pts += [(d, side * 9), (-d, side * 9), (side * 9, d * 0.70), (side * 9, -d * 0.70)]
    # 外墙内侧的林带。
    for i in range(90):
        a = TAU * i / 90 + rng.uniform(-0.02, 0.02)
        rr = rng.uniform(0.82, 0.90)
        pts.append((math.cos(a) * LY.CITY_WALL['a'] * rr, math.sin(a) * LY.CITY_WALL['b'] * rr))
    for i, (x, y) in enumerate(pts):
        gz = IS.ground_h(x, y)
        h = rng.uniform(5.5, 9.5)
        trunk = cylinder('CityTree_Trunk_%03d' % i, 0.22, 1.5, (x, y, gz), C['city_veg'],
                         M['bark'], segments=7, r_top=0.15)
        set_vcol_const(trunk, PAL['bark'], jitter=0.10, seed=4900 + i)
        objs.append(trunk)
        crown = cone('CityTree_Crown_%03d' % i, rng.uniform(1.3, 2.0), h,
                     (x, y, gz + 1.0), C['city_veg'], M['cypress'], segments=9, r_top=0.10)
        set_vcol_const(crown, PAL['cypress'], jitter=0.16, seed=5000 + i)
        crown['fx'] = 'foliage'
        objs.append(crown)
    return objs


def build_all(M, C):
    objs = []
    objs += build_city_walls(M, C)
    objs += build_scholar_quarter(M, C)
    objs += build_dawn_quarter(M, C)
    objs += build_forge_quarter(M, C)
    objs += build_tide_quarter(M, C)
    objs += build_residential_quarters(M, C)
    objs += build_garden_quarter(M, C)
    objs += build_city_vegetation(M, C)
    return objs
