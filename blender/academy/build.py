# -*- coding: utf-8 -*-
"""
星槎学院 · 总装 / 导出 / 渲染
用法：
  blender -b --python build.py -- [--out DIR] [--render] [--quality low|high] [--blend]
"""
import sys
import os
import time
import math
import random

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy
from mathutils import Vector, Matrix

from util import *
import layout as LY
import island as IS
import buildings_core as BC
import buildings_houses as BH
import buildings_life as BL
import districts as DT
import castle as CA
import wilds as WD
import atmosphere as AT


def parse_args():
    argv = sys.argv
    args = argv[argv.index('--') + 1:] if '--' in argv else []
    opt = {'out': os.path.join(HERE, '..', '..', 'models'), 'render': False, 'quality': 'low', 'blend': False, 'only': None}
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--out':
            opt['out'] = args[i + 1]; i += 1
        elif a == '--render':
            opt['render'] = True
        elif a == '--quality':
            opt['quality'] = args[i + 1]; i += 1
        elif a == '--blend':
            opt['blend'] = True
        elif a == '--only':
            opt['only'] = args[i + 1]; i += 1
        elif a == '--no-export':
            opt['no_export'] = True
        i += 1
    return opt


def make_collections():
    names = ['island', 'stones', 'paths', 'plaza', 'tower', 'corridors', 'dawn', 'speak', 'forge', 'tide',
             'library', 'hall', 'dorms', 'garden', 'misc', 'veg', 'people', 'fx',
             'city_wall', 'city_paths', 'districts', 'city_veg', 'city_fx']
    return {n: coll('C_' + n) for n in names}


def log(msg, t0):
    print('[%6.1fs] %s' % (time.time() - t0, msg))
    sys.stdout.flush()


def build_all(opt):
    t0 = time.time()
    reset_scene()
    C = make_collections()
    M = mat_lib()
    M['smoke'] = principled('FX_Smoke', '#c9c4bc', rough=1.0, alpha=0.35)
    log('materials ready', t0)

    only = opt['only']
    stages = [
        ('island', lambda: IS.build_island(M, C)),
        ('plaza', lambda: BC.build_plaza(M, C)),
        ('star_tower', lambda: BC.build_star_tower(M, C)),
        ('corridors', lambda: BC.build_corridors(M, C)),
        ('grain_hall', lambda: BC.build_grain_hall(M, C)),
        ('history_hall', lambda: BC.build_history_hall(M, C)),
        ('castle', lambda: CA.build_castle(M, C)),
        ('dawn', lambda: BH.build_dawn_tower(M, C)),
        ('speak', lambda: BH.build_speak_tower(M, C)),
        ('forge', lambda: BH.build_forge_tower(M, C)),
        ('tide', lambda: BH.build_tide_tower(M, C)),
        ('tide_hall', lambda: BL.build_tide_hall(M, C)),
        ('dorms', lambda: BL.build_dorms(M, C)),
        ('ember', lambda: BL.build_ember_garden(M, C)),
        ('academy_city', lambda: DT.build_all(M, C)),
        ('wilds', lambda: WD.build_all(M, C)),
        ('veg', lambda: BL.build_vegetation(M, C)),
        ('people', lambda: BL.build_people(M, C)),
    ]
    for name, fn in stages:
        if only and name not in only.split(','):
            continue
        fn()
        v, f = stats()
        log('%-12s  verts=%d faces=%d' % (name, v, f), t0)
    # 光柱（塔根下）
    beam = lathe('FX_LightColumn', [(3.0, IS.TIP_Z - 60), (5.5, IS.TIP_Z - 10), (6.5, IS.TIP_Z + 8)], 24, (0, 0, 0), C['fx'], M['beam'], smooth=True)
    beam['fx'] = 'beam'
    # 锚点：相机兴趣点、栈桥、渡船轨道端点
    empty('ANCHOR_Plaza', (0, 0, IS.ground_h(0, 0)), C['misc'])
    empty('ANCHOR_CrystalTop', (0, 0, IS.ground_h(0, 0) + 1.35 + LY.STAR_TOWER['h'] + 3.4), C['misc'])
    empty('ANCHOR_PierEnd', (LY.PIER['x1'], LY.PIER['y'], IS.ground_h(LY.PIER['x0'], 0) - 0.2), C['misc'])
    empty('ANCHOR_FerryTop', LY.FERRY['pos'], C['misc'])
    empty('ANCHOR_FerryBottom', (LY.FERRY['pos'][0], LY.FERRY['pos'][1], LY.FERRY['pos'][2] - 300.0), C['misc'])
    return M, C


INDIVIDUAL_FX = {'crystal', 'shard', 'halo', 'fire', 'lamp_main', 'water', 'waterfall', 'mist', 'smoke', 'cloud',
                 'banner', 'flag', 'bell', 'armillary', 'orb', 'beam', 'net'}


def merge_for_export(C):
    """
    按 (集合, 材质, fx类型) 合并对象，减少 draw call：
    - INDIVIDUAL_FX / lore / orbit 对象保留独立（运行时需要单独动画或拾取）
    - window / lamp / foliage / moss 等 fx 按类型合并成一个网格（整体做呼吸/摆动即可）
    """
    for cname, c in C.items():
        groups = {}
        for ob in list(c.objects):
            if ob.type != 'MESH':
                continue
            fx = ob.get('fx')
            if fx in INDIVIDUAL_FX or 'lore' in ob.keys() or 'orbit_r' in ob.keys() or ob.parent is not None or len(ob.children) > 0:
                continue
            if len(ob.data.materials) != 1:
                continue
            key = (ob.data.materials[0].name, fx or '')
            groups.setdefault(key, []).append(ob)
        for (mname, fx), obs in groups.items():
            if len(obs) < 2:
                continue
            for ob in obs:
                if ob.modifiers:
                    apply_modifiers(ob)
                if ob.data.color_attributes.get('Col') is None:
                    base = ob.data.materials[0].diffuse_color
                    attr = ob.data.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
                    vals = []
                    for _ in ob.data.vertices:
                        vals.extend((base[0], base[1], base[2], 1.0))
                    attr.data.foreach_set('color', vals)
            bpy.ops.object.select_all(action='DESELECT')
            for ob in obs:
                ob.select_set(True)
            bpy.context.view_layer.objects.active = obs[0]
            bpy.ops.object.join()
            j = bpy.context.view_layer.objects.active
            j.name = ('FXM_%s_%s_%s' % (fx, cname, mname)) if fx else ('M_%s_%s' % (cname, mname))
            j.data.name = j.name
            if fx:
                j['fx'] = fx
                j['merged'] = True


def export_glb(path):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format='GLB',
        export_apply=True,
        export_yup=True,
        export_extras=True,
        export_lights=False,
        export_cameras=False,
        export_materials='EXPORT',
        export_image_format='NONE',
        export_texcoords=False,
        export_normals=True,
        export_vertex_color='MATERIAL',
        export_attributes=False,
        use_selection=False,
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,
        export_draco_position_quantization=14,
        export_draco_normal_quantization=10,
        export_draco_color_quantization=10,
    )


def render_views(out_dir, quality):
    sc = bpy.context.scene
    gz = IS.ground_h(0, 0)
    top = gz + 1.35 + LY.STAR_TOWER['h']
    views = [
        ('hero_sw', (-660, -540, 320), (10, 10, gz + 6), 46),
        ('hero_ne', (640, 520, 300), (0, 0, gz + 6), 46),
        ('pier_west', (-500, 120, 110), (-140, 0, gz + 12), 36),
        ('plaza_low', (-46, -40, gz + 5.0), (0.0, 0.0, gz + 30), 46),
        ('castle', (150, -150, gz + 95), (4, 56, gz + 18), 40),
        ('forge_side', (190, -210, gz + 70), (18, -94, gz + 8), 36),
        ('sycamore', (70, 130, gz + 34), (-5, 35, gz + 10), 36),
        ('underside', (380, -520, -90), (0, 0, -55), 40),
        ('top_down', (0.1, -0.1, 1300), (0, 0, gz), 44),
    ]
    if quality == 'low':
        views = views[:4] + views[6:7]
    only = os.environ.get('ACADEMY_VIEWS')
    if only:
        keep = only.split(',')
        views = [v for v in views if v[0] in keep]
    cam_data = bpy.data.cameras.new('Cam')
    cam_data.clip_start = 0.5
    cam_data.clip_end = 40000.0
    cam = bpy.data.objects.new('Cam', cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    for name, loc, tgt, fov in views:
        cam.location = loc
        d = Vector(tgt) - Vector(loc)
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        cam_data.angle = math.radians(fov)
        sc.render.filepath = os.path.join(out_dir, 'render_%s.png' % name)
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print('rendered %s in %.1fs' % (name, time.time() - t))
        sys.stdout.flush()


def export_hotspots(path):
    """建筑热点（网页拾取/标签用）：名称、位置（Z-up 米）、标签高度、志书键。"""
    import json
    gz = IS.ground_h(0, 0)
    H = []

    def add(key, name, x, y, z, r, cam=None):
        H.append(dict(key=key, name=name, pos=[round(x, 2), round(y, 2), round(z, 2)], r=r, cam=cam))
    add('star_tower', '星陨塔', 0, 0, gz + 1.35 + LY.STAR_TOWER['h'] + 4.0, 6.0, [28, -34, gz + 30])
    add('crystal', '裂隙晶', 0, 0, gz + 1.35 + LY.STAR_TOWER['h'] + 0.5 + 3.0, 2.5, [9, -11, gz + 1.35 + LY.STAR_TOWER['h'] + 4])
    add('pillars', '四柱', 0, 0, gz + 5.0, 3.0, [14, -18, gz + 8])
    dx, dy = LY.DAWN_TOWER['pos']
    add('dawn', '晨辉塔', dx, dy, IS.ground_h(dx, dy) + LY.DAWN_TOWER['h'] + 9.0, 5.0, [dx + 18, dy - 22, gz + 26])
    sx, sy = LY.SPEAK_TOWER['pos']
    add('speak', '星语塔 · 观星台', sx, sy, IS.ground_h(sx, sy) + LY.SPEAK_TOWER['h'] + 5.0, 4.0, [sx + 16, sy - 14, gz + 18])
    tx, ty = LY.SYCAMORE['pos']
    add('sycamore', '千岁梧桐', tx, ty, IS.ground_h(tx, ty) + 20.0, 6.0, [tx - 18, ty + 14, gz + 20])
    fx, fy = LY.FORGE_TOWER['pos']
    add('forge', '锤音塔', fx, fy, IS.ground_h(fx, fy) + LY.FORGE_TOWER['h'] + 8.0, 5.0, [fx + 16, fy - 16, gz + 14])
    ox, oy = LY.OLD_STEPS['pos']
    add('old_steps', '旧阶堆', ox, oy, IS.ground_h(ox, oy) + 3.5, 2.5, [ox + 8, oy - 8, gz + 6])
    hx, hy = LY.TIDE_TOWER['pos']
    add('tide', '海心塔', hx, hy, IS.ground_h(hx, hy) + LY.TIDE_TOWER['h'] + 7.0, 5.0, [hx - 6, hy - 24, gz + 18])
    add('pier', '槎埠 · 栈桥', LY.PIER['x1'] + 4, 0, IS.ground_h(LY.PIER['x0'], 0) + 2.5, 3.0, [LY.PIER['x1'] + 2, -16, gz + 6])
    add('ferry', '渡船「第二块石头」', LY.FERRY['pos'][0], LY.FERRY['pos'][1], LY.FERRY['pos'][2] + 7.0, 4.0, [LY.FERRY['pos'][0] - 4, LY.FERRY['pos'][1] - 14, LY.FERRY['pos'][2] + 6])
    px, py = LY.POOL['pos']
    add('pool', '浮池 · 云网', px, py, IS.ground_h(px, py) + 4.0, 4.0, [px + 10, py - 10, gz + 8])
    gx, gy = LY.GRAIN_HALL['pos']
    add('grain_hall', '星穗馆', gx, gy, IS.ground_h(gx, gy) + 1.2 + 7 * 2.61 + 5.0, 5.0, [gx + 14, gy - 16, gz + 22])
    hx2, hy2 = LY.HISTORY_HALL['pos']
    add('history_hall', '校史馆 · 不该来的墙', hx2, hy2, IS.ground_h(hx2, hy2) + 6.0, 3.0, [hx2 + 6, hy2 - 9, gz + 7])
    tx2, ty2 = LY.TIDE_HALL['pos']
    add('tide_hall', '星潮厅', tx2, ty2, IS.ground_h(tx2, ty2) + LY.TIDE_HALL['h'] + 4.5, 6.0, [tx2 + 10, ty2 - 20, gz + 14])
    kx, ky = LY.KITCHEN['pos']
    add('kitchen', '灶房 · 梯田 · 羊圈', kx, ky, IS.ground_h(kx, ky) + 5.0, 3.5, [kx + 14, ky - 10, gz + 10])
    ex, ey = LY.EMBER_GARDEN['pos']
    add('ember', '烬园', ex, ey, IS.ground_h(ex, ey) + 6.0, 4.0, [ex - 6, ey - 14, gz + 10])
    bx, by = LY.BELL_TOWER['pos']
    add('bell', '熄灯钟楼', bx, by, IS.ground_h(bx, by) + LY.BELL_TOWER['h'] + 4.0, 2.5, [bx + 8, by - 10, gz + 12])
    a = math.radians(LY.DORMS_NE[2][0])
    rr = IS.road_r(a) - (LY.DORM_IN_OFF + LY.DORM_SIZE[1] / 2)
    add('dorms', '宿舍（按年份分）', math.cos(a) * rr, math.sin(a) * rr, IS.ground_h(math.cos(a) * rr, math.sin(a) * rr) + 8.0, 6.0, [math.cos(a) * rr + 12, math.sin(a) * rr - 14, gz + 12])
    pa = LY.PADDOCK['theta']
    add('paddock', '马圈（六匹很胖的马）', math.cos(pa) * LY.PADDOCK['r'], math.sin(pa) * LY.PADDOCK['r'], IS.ground_h(math.cos(pa) * LY.PADDOCK['r'], math.sin(pa) * LY.PADDOCK['r']) + 3.5, 3.0, None)
    add('root', '塔根 · 裂隙光柱', 0, 0, IS.TIP_Z - 6.0, 6.0, [40, -60, IS.TIP_Z - 30])
    add('corridors', '四院回廊', 20.0, 0.0, gz + 6.0, 3.0, None)
    # 外城扩建区
    add('city_wall', '星槎外城墙', 0, LY.CITY_WALL['b'],
        IS.ground_h(0, LY.CITY_WALL['b']) + 13.0, 12.0,
        [0, LY.CITY_WALL['b'] + 95, gz + 62])
    for key, title, camoff in (
        ('scholar_quarter', '星语学宫', (72, 70, 52)),
        ('dawn_quarter', '晨辉演武院', (76, -62, 48)),
        ('forge_quarter', '锤音工造院', (72, -72, 45)),
        ('tide_quarter', '海心港区', (-82, -72, 44)),
        ('residence_quarter', '七年舍街', (72, 66, 45)),
        ('service_quarter', '百工与疗愈区', (-75, 68, 44)),
        ('garden_quarter', '星植苑', (-72, -70, 40)),
    ):
        source_key = key.replace('_quarter', '')
        dx, dy = LY.DISTRICTS[source_key]['pos']
        add(key, title, dx, dy, IS.ground_h(dx, dy) + 17.0, 15.0,
            [dx + camoff[0], dy + camoff[1], gz + camoff[2]])
    add('castle', '旧学宫主堡', 4, 56, gz + 30.0, 16.0, [80, -46, gz + 44])
    add('lake', '西南湖', IS.LAKE['cx'], IS.LAKE['cy'], IS.LAKE_Z + 2.0, 22.0,
        [IS.LAKE['cx'] + 70, IS.LAKE['cy'] - 70, gz + 34])
    add('mountain', '东脊雪山', IS.MOUNTAIN['cx'], IS.MOUNTAIN['cy'], gz + 42.0, 26.0,
        [IS.MOUNTAIN['cx'] - 90, IS.MOUNTAIN['cy'] - 130, gz + 80])
    add('forest', '外环密林', 0, -272, gz + 8.0, 24.0, [0, -350, gz + 70])
    meta = dict(island=dict(a=IS.A_AXIS, b=IS.B_AXIS, ground=gz, tip=IS.TIP_Z), hotspots=H)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)


def main():
    opt = parse_args()
    out = os.path.abspath(opt['out'])
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    M, C = build_all(opt)
    v, f = stats()
    print('TOTAL before merge: objects=%d verts=%d faces=%d' % (len(bpy.data.objects), v, f))
    if opt['blend']:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, 'xingcha_academy.blend'))
        log('blend saved', t0)
    # 合并网格统一前置：导出与渲染共用，避免上万独立对象拖垮 Cycles 同步
    merge_for_export(C)
    v, f = stats()
    print('TOTAL after merge: objects=%d verts=%d faces=%d' % (len(bpy.data.objects), v, f))
    if not opt.get('no_export'):
        export_hotspots(os.path.join(out, 'xingcha_academy.hotspots.json'))
        glb = os.path.join(out, 'xingcha_academy.glb')
        export_glb(glb)
        log('glb exported: %s (%.1f MB)' % (glb, os.path.getsize(glb) / 1e6), t0)
    if opt['render']:
        AT.setup_render(opt['quality'])
        render_views(out, opt['quality'])
        log('renders done', t0)


if __name__ == '__main__':
    main()
