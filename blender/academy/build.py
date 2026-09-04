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
             'library', 'hall', 'dorms', 'garden', 'misc', 'veg', 'people', 'fx']
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
        ('dawn', lambda: BH.build_dawn_tower(M, C)),
        ('speak', lambda: BH.build_speak_tower(M, C)),
        ('forge', lambda: BH.build_forge_tower(M, C)),
        ('tide', lambda: BH.build_tide_tower(M, C)),
        ('tide_hall', lambda: BL.build_tide_hall(M, C)),
        ('dorms', lambda: BL.build_dorms(M, C)),
        ('ember', lambda: BL.build_ember_garden(M, C)),
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


def setup_render(quality):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    Q = {'preview': (16, 960, 540), 'low': (24, 1280, 720), 'high': (48, 1440, 810)}[quality]
    sc.cycles.samples = Q[0]
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    sc.cycles.max_bounces = 4
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.use_auto_tile = True
    sc.cycles.tile_size = 512          # 分块渲染，2 GB 内存的沙盒也能跑高分辨率
    sc.render.resolution_x = Q[1]
    sc.render.resolution_y = Q[2]
    sc.render.film_transparent = True          # 背景由合成器用 Env 通道贴回（这样雾不会吃掉天空渐变）
    vts = [i.identifier for i in sc.view_settings.bl_rna.properties['view_transform'].enum_items]
    sc.view_settings.view_transform = 'AgX' if 'AgX' in vts else 'Filmic'
    looks = [i.identifier for i in sc.view_settings.bl_rna.properties['look'].enum_items]
    for lk in ('AgX - Punchy', 'Punchy', 'AgX - Medium High Contrast', 'Medium High Contrast'):
        if lk in looks:
            sc.view_settings.look = lk
            break
    sc.view_settings.exposure = 0.25
    sc.view_settings.gamma = 1.0
    # 世界：手绘感天空渐变（顶部钴蓝 → 地平线暖米色 → 底部深灰蓝）
    w = bpy.data.worlds.new('W')
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mapr = nt.nodes.new('ShaderNodeMapRange')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    nt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    nt.links.new(sep.outputs['Z'], mapr.inputs['Value'])
    mapr.inputs['From Min'].default_value = -1.0
    mapr.inputs['From Max'].default_value = 1.0
    nt.links.new(mapr.outputs['Result'], ramp.inputs['Fac'])
    cr = ramp.color_ramp
    cr.interpolation = 'EASE'
    cr.elements[0].position = 0.0
    cr.elements[0].color = (0.30, 0.33, 0.42, 1)      # 正下方（几乎被云海盖住）
    cr.elements[1].position = 1.0
    cr.elements[1].color = (0.010, 0.060, 0.30, 1)    # 天顶：深钴蓝
    e = cr.elements.new(0.455); e.color = (0.46, 0.48, 0.56, 1)   # 地平线下：云海上方的薄霭
    e = cr.elements.new(0.488); e.color = (0.72, 0.62, 0.52, 1)
    e = cr.elements.new(0.503); e.color = (0.95, 0.66, 0.36, 1)   # 地平线：暖光带
    e = cr.elements.new(0.516); e.color = (0.40, 0.52, 0.72, 1)   # 转入蓝
    e = cr.elements.new(0.540); e.color = (0.12, 0.28, 0.62, 1)
    e = cr.elements.new(0.620); e.color = (0.04, 0.14, 0.46, 1)
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 1.0
    # 太阳：午后偏西南，暖色，强对比
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 100))
    sun = bpy.context.object
    sun.data.energy = 5.5
    sun.data.angle = math.radians(2.0)
    sun.data.color = (1.0, 0.92, 0.80)
    sun.rotation_euler = (math.radians(52), 0, math.radians(215))
    # 补光：冷色天光（从东北低角度）
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 100))
    fill = bpy.context.object
    fill.data.energy = 0.9
    fill.data.angle = math.radians(20.0)
    fill.data.color = (0.65, 0.78, 1.0)
    fill.rotation_euler = (math.radians(70), 0, math.radians(40))
    fill.data.use_shadow = False
    # 裂隙光：从底下打上来的蓝色区域光
    bpy.ops.object.light_add(type='AREA', location=(0, 0, IS.TIP_Z - 20))
    rift = bpy.context.object
    rift.data.energy = 60000
    rift.data.color = (0.45, 0.85, 1.0)
    rift.data.size = 30
    rift.rotation_euler = (math.pi, 0, 0)
    # 塔顶晶体点光
    bpy.ops.object.light_add(type='POINT', location=(0, 0, IS.ground_h(0, 0) + 1.35 + LY.STAR_TOWER['h'] + 3.4))
    cry = bpy.context.object
    cry.data.energy = 6000
    cry.data.color = (0.6, 0.9, 1.0)
    cry.data.shadow_soft_size = 1.5
    build_cloud_sea()
    setup_mist_compositor(sc, w)


def build_cloud_sea(z0=-170.0, r_in=40.0, r_out=16000.0, n_ang=192, n_rad=96):
    """渲染专用：岛下方的云海（极坐标网格，近密远疏），网页端由 shader 天空里的云海代替。"""
    from mathutils import noise
    verts, faces, cols = [], [], []
    k = (r_out / r_in) ** (1.0 / (n_rad - 1))
    peak = Vector((1.0, 1.0, 1.0)); valley = Vector((0.42, 0.50, 0.72))
    for j in range(n_rad):
        r = r_in * (k ** j)
        for i in range(n_ang):
            a = TAU * i / n_ang
            x, y = math.cos(a) * r, math.sin(a) * r
            p = Vector((x * 0.0016, y * 0.0016, 0.0))
            h = (noise.noise(p) * 40.0 + noise.noise(p * 2.7 + Vector((5.1, 3.3, 0))) * 18.0
                 + noise.noise(p * 7.5 + Vector((1.7, 9.2, 0))) * 8.0 + noise.noise(p * 19.0) * 3.0)
            h -= 45.0 * math.exp(-(r / 150.0) ** 2)          # 岛正下方压成浅盆，让光柱有落处
            verts.append((x, y, z0 + h))
            t = max(0.0, min(1.0, (h + 20.0) / 50.0))
            c = valley.lerp(peak, t)
            cols.append((c.x, c.y, c.z, 1.0))
    for j in range(n_rad - 1):
        for i in range(n_ang):
            a0 = j * n_ang + i; a1 = j * n_ang + (i + 1) % n_ang
            faces.append((a0, a1, a1 + n_ang, a0 + n_ang))
    # 中心盖一个扇形，免得正下方漏空
    c_idx = len(verts); verts.append((0.0, 0.0, z0 - 45.0)); cols.append((valley.x, valley.y, valley.z, 1.0))
    for i in range(n_ang):
        faces.append((c_idx, (i + 1) % n_ang, i))
    me = bpy.data.meshes.new('CloudSea')
    me.from_pydata(verts, [], faces)
    me.update()
    for pg in me.polygons:
        pg.use_smooth = True
    ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    for i, c in enumerate(cols):
        ca.data[i].color = c
    ob = bpy.data.objects.new('CloudSea', me)
    env_coll = bpy.data.collections.new('render_env')
    bpy.context.scene.collection.children.link(env_coll)
    env_coll.objects.link(ob)
    mat = bpy.data.materials.new('CloudSea')
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
    nt.links.new(vc.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 1.0
    if 'Subsurface Weight' in bsdf.inputs:
        bsdf.inputs['Subsurface Weight'].default_value = 0.25
        bsdf.inputs['Subsurface Radius'].default_value = (10.0, 10.0, 12.0)
    ob.data.materials.append(mat)
    ob.visible_glossy = False
    return ob


def setup_mist_compositor(sc, world):
    """大气透视：Mist 通道把主图层混向"该像素方向的天空色"（由只含世界的 Sky 图层提供），再叠在天空上。"""
    vl = sc.view_layers[0]
    vl.name = 'Main'
    vl.use_pass_mist = True
    sky = sc.view_layers.new('Sky')
    sky.use_pass_environment = True
    sky.use_pass_combined = False
    sky.use_pass_z = False
    sky.use_pass_mist = False
    sky.samples = 4
    for lc in sky.layer_collection.children:
        lc.exclude = True
    world.mist_settings.start = 120.0
    world.mist_settings.depth = 2400.0
    world.mist_settings.falloff = 'LINEAR'
    sc.use_nodes = True
    nt = sc.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    rl = nt.nodes.new('CompositorNodeRLayers'); rl.layer = 'Main'
    rs = nt.nodes.new('CompositorNodeRLayers'); rs.layer = 'Sky'
    scale = nt.nodes.new('CompositorNodeMath'); scale.operation = 'MULTIPLY'; scale.inputs[1].default_value = 0.88
    fog = nt.nodes.new('CompositorNodeMixRGB'); fog.blend_type = 'MIX'
    seta = nt.nodes.new('CompositorNodeSetAlpha')
    over = nt.nodes.new('CompositorNodeAlphaOver'); over.use_premultiply = True
    comp = nt.nodes.new('CompositorNodeComposite')
    nt.links.new(rl.outputs['Mist'], scale.inputs[0])
    nt.links.new(scale.outputs[0], fog.inputs[0])
    nt.links.new(rl.outputs['Image'], fog.inputs[1])
    nt.links.new(rs.outputs['Env'], fog.inputs[2])
    nt.links.new(fog.outputs[0], seta.inputs['Image'])
    nt.links.new(rl.outputs['Alpha'], seta.inputs['Alpha'])
    nt.links.new(rs.outputs['Env'], over.inputs[1])
    nt.links.new(seta.outputs[0], over.inputs[2])
    nt.links.new(over.outputs[0], comp.inputs['Image'])


def render_views(out_dir, quality):
    sc = bpy.context.scene
    gz = IS.ground_h(0, 0)
    top = gz + 1.35 + LY.STAR_TOWER['h']
    views = [
        ('hero_sw', (-176, -142, 34), (0, 0, gz + 3), 42),
        ('hero_ne', (160, 130, 34), (0, 0, gz + 3), 42),
        ('pier_west', (-110, 30, 14), (-28, 0, gz + 9), 36),
        ('plaza_low', (-15.5, -13.5, gz + 1.8), (2.0, 3.0, gz + 24), 48),
        ('forge_side', (26, -52, gz + 8), (0, -20, gz + 5), 36),
        ('sycamore', (20, 55, gz + 12), (-5, 22, gz + 9), 36),
        ('underside', (85, -125, -70), (0, 0, -14), 36),
        ('top_down', (0.1, -0.1, 210), (0, 0, gz), 40),
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
    if not opt.get('no_export'):
        merge_for_export(C)
        v, f = stats()
        print('TOTAL after merge: objects=%d verts=%d faces=%d' % (len(bpy.data.objects), v, f))
        export_hotspots(os.path.join(out, 'xingcha_academy.hotspots.json'))
        glb = os.path.join(out, 'xingcha_academy.glb')
        export_glb(glb)
        log('glb exported: %s (%.1f MB)' % (glb, os.path.getsize(glb) / 1e6), t0)
    if opt['render']:
        setup_render(opt['quality'])
        render_views(out, opt['quality'])
        log('renders done', t0)


if __name__ == '__main__':
    main()
