# -*- coding: utf-8 -*-
"""星槎学院 · 主装配
Blender 4.2 · 程序化生成整座空岛学府
用法：
  blender -b --python models/build_academy.py -- --look night --cam hero --res 1280x720 --samples 32
"""
import bpy
import math
import sys
import os
import time
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import clean_scene, M, hexcol, TAU
from materials import make_all, set_glow, LOOK_GLOW, GLOW_KEYS
from island import (build_ground, build_crystals, build_crack_glow, build_pillar,
                    build_river, build_island, build_floating_rocks, ISLAND_TOP)
from academy import build_all

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDER_DIR = os.path.join(ROOT, 'renders')
WEB_DIR = os.path.join(ROOT, 'web')


def parse_args():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    d = {'look': 'night', 'cam': 'hero', 'res': (1280, 720), 'samples': 32,
         'quick': False, 'render': True, 'save_blend': None, 'glb': None}
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--look':
            d['look'] = args[i + 1]; i += 2
        elif a == '--cam':
            d['cam'] = args[i + 1]; i += 2
        elif a == '--res':
            w, h = args[i + 1].split('x'); d['res'] = (int(w), int(h)); i += 2
        elif a == '--samples':
            d['samples'] = int(args[i + 1]); i += 2
        elif a == '--quick':
            d['quick'] = True; i += 1
        elif a == '--no-render':
            d['render'] = False; i += 1
        elif a == '--blend':
            d['save_blend'] = args[i + 1]; i += 2
        elif a == '--glb':
            d['glb'] = args[i + 1]; i += 2
        else:
            i += 1
    return d


# ================================================================ 天幕
def build_skydome(M, look):
    """带渐变与星辰的穹顶（自发光，不受光）"""
    import bmesh
    name = 'skydome'
    # 移除旧穹顶
    for o in list(bpy.data.objects):
        if o.name.startswith(name):
            bpy.data.objects.remove(o, do_unlink=True)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=1800.0)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    # 渐变天幕（垂直 ColorRamp，自发光）
    mat = bpy.data.materials.new('sky_' + look)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    emi = nt.nodes.new('ShaderNodeEmission')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mr = nt.nodes.new('ShaderNodeMapRange')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    nt.links.new(tc.outputs['Object'], sep.inputs['Vector'])
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    mr.inputs['From Min'].default_value = -300.0
    mr.inputs['From Max'].default_value = 700.0
    nt.links.new(mr.outputs['Result'], ramp.inputs['Fac'])
    cr = ramp.color_ramp
    if look == 'night':
        cr.elements[0].position = 0.0
        cr.elements[0].color = hexcol('#05070e')
        cr.elements[1].position = 0.82
        cr.elements[1].color = hexcol('#13233a')
        e = cr.elements.new(1.0)
        e.color = hexcol('#25405c')
    else:
        # 自上而下：深蓝 → 蓝紫 → 地平线铜橙（暖光带在低位）
        cr.elements[0].position = 0.0
        cr.elements[0].color = hexcol('#182448')   # 高空深蓝
        cr.elements[1].position = 0.45
        cr.elements[1].color = hexcol('#2c3a64')   # 过渡蓝
        e = cr.elements.new(0.72)
        e.color = hexcol('#67507a')                # 地平线灰紫
        e2 = cr.elements.new(0.88)
        e2.color = hexcol('#b06a52')               # 低空铜橙
        e3 = cr.elements.new(1.0)
        e3.color = hexcol('#f0a05a')               # 最低处落日金
    emi.inputs['Strength'].default_value = 1.0
    nt.links.new(ramp.outputs['Color'], emi.inputs['Color'])
    nt.links.new(emi.outputs['Emission'], out.inputs['Surface'])
    mesh.materials.append(mat)
    # 星点：几何点云（小面片，弱发光，大小分级）
    star_mat = M['star']
    sbm = bmesh.new()
    rng = __import__('random').Random(31)
    for _ in range(300):
        v = Vector((rng.gauss(0, 1), rng.gauss(0, 1), abs(rng.gauss(0, 1)) * 1.4)).normalized()
        if v.z < 0.05:
            v.z = abs(v.z) + 0.05
            v.normalize()
        p = v * 1680.0
        s = rng.uniform(0.8, 2.6)
        vs = []
        for dx, dy in [(-s, -s), (s, -s), (s, s), (-s, s)]:
            u = v.cross(Vector((0, 0, 1)))
            if u.length < 1e-4:
                u = Vector((1, 0, 0))
            u.normalize()
            w = v.cross(u)
            vs.append(sbm.verts.new(p + u * dx + w * dy))
        sbm.faces.new(vs)
    # 少量亮星（大而稀）
    for _ in range(36):
        v = Vector((rng.gauss(0, 0.8), rng.gauss(0, 0.8), abs(rng.gauss(0, 1.2)))).normalized()
        if v.z < 0.1:
            v.z = abs(v.z) + 0.1
            v.normalize()
        p = v * 1700.0
        s = rng.uniform(2.6, 4.2)
        vs = []
        for dx, dy in [(-s, -s), (s, -s), (s, s), (-s, s)]:
            u = v.cross(Vector((0, 0, 1)))
            if u.length < 1e-4:
                u = Vector((1, 0, 0))
            u.normalize()
            w = v.cross(u)
            vs.append(sbm.verts.new(p + u * dx + w * dy))
        sbm.faces.new(vs)
    smesh = bpy.data.meshes.new('stars')
    sbm.to_mesh(smesh)
    sbm.free()
    smesh.materials.append(star_mat)
    stars = bpy.data.objects.new('stars', smesh)
    bpy.context.scene.collection.objects.link(stars)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


# ================================================================ 灯光
def build_lights(M, look):
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT':
            bpy.data.objects.remove(o, do_unlink=True)
    lights = []
    if look == 'night':
        sun = bpy.data.lights.new('moon', 'SUN')
        sun.energy = 1.35
        sun.color = hexcol('#7d9ad4')[:3]
        sun.angle = 0.3
        so = bpy.data.objects.new('moon', sun)
        so.rotation_euler = (math.radians(44), 0, math.radians(-125))
        lights.append(so)
        # 裂隙辉光（地面主照明，柱外侧）
        for (pos, e, col, size) in [
            ((120, 85, 26), 8.0e5, '#4fc0ff', 16.0),
            ((-125, -75, 40), 6.0e5, '#5f80ff', 16.0),
            ((0, -190, 55), 2.6e5, '#4fc0ff', 14.0),
            ((30, 190, 60), 2.2e5, '#4fc0ff', 14.0),
        ]:
            pl = bpy.data.lights.new('riftlight', 'POINT')
            pl.energy = e
            pl.color = hexcol(col)[:3]
            pl.shadow_soft_size = size
            po = bpy.data.objects.new('riftlight', pl)
            po.location = pos
            lights.append(po)
        # 裂隙晶（塔顶暖光，位于晶簇之上）
        pl = bpy.data.lights.new('crystal', 'POINT')
        pl.energy = 2.4e5
        pl.color = hexcol('#ffd9a0')[:3]
        pl.shadow_soft_size = 4.0
        po = bpy.data.objects.new('crystal_light', pl)
        po.location = (0, 0, ISLAND_TOP + 92)
        lights.append(po)
        # 学院暖光照明（大范围暖色，营造灯火感）——压低防过曝
        ar = bpy.data.lights.new('warm', 'AREA')
        ar.energy = 1.5e5
        ar.size = 90.0
        ar.color = hexcol('#ffc688')[:3]
        ao = bpy.data.objects.new('warmfill', ar)
        ao.location = (10, -14, ISLAND_TOP + 68)
        ao.rotation_euler = (math.radians(10), 0, math.radians(25))
        lights.append(ao)
        # 学院冷调补光（轮廓）
        ar = bpy.data.lights.new('fill', 'AREA')
        ar.energy = 3.0e5
        ar.size = 150.0
        ar.color = hexcol('#8fa0c8')[:3]
        ao = bpy.data.objects.new('fill', ar)
        ao.location = (30, -40, ISLAND_TOP + 140)
        ao.rotation_euler = (math.radians(16), math.radians(-12), math.radians(18))
        lights.append(ao)
        # 四院各一盏小暖灯（让四院更立体）
        for (px, py) in [(72, 0), (0, -46), (-40, 0), (0, 46)]:
            pl = bpy.data.lights.new('houselo', 'POINT')
            pl.energy = 2600.0
            pl.color = hexcol('#ffcf92')[:3]
            pl.shadow_soft_size = 2.0
            po = bpy.data.objects.new('houselo', pl)
            po.location = (px, py, ISLAND_TOP + 12)
            lights.append(po)
        # 锻炉
        pl = bpy.data.lights.new('forge', 'POINT')
        pl.energy = 900.0
        pl.color = hexcol('#ff7a2e')[:3]
        pl.shadow_soft_size = 1.5
        po = bpy.data.objects.new('forge_light', pl)
        po.location = (-36, 17, ISLAND_TOP + 3)
        lights.append(po)
    else:  # dusk
        sun = bpy.data.lights.new('sun', 'SUN')
        sun.energy = 4.6
        sun.color = hexcol('#ffb46a')[:3]
        sun.angle = 0.05
        so = bpy.data.objects.new('sun', sun)
        so.rotation_euler = (math.radians(66), 0, math.radians(-102))
        lights.append(so)
        # 地面暖色斜阳（照亮南侧岛缘与地面）
        ar = bpy.data.lights.new('warmg', 'AREA')
        ar.energy = 2.2e5
        ar.size = 110.0
        ar.color = hexcol('#ffc070')[:3]
        ao = bpy.data.objects.new('warmg', ar)
        ao.location = (250, 380, 90)
        ao.rotation_euler = (math.radians(64), 0, math.radians(-55))
        lights.append(ao)
        # 冷色补光（天空反光）
        ar = bpy.data.lights.new('fill', 'AREA')
        ar.energy = 1.4e5
        ar.size = 180.0
        ar.color = hexcol('#8098c8')[:3]
        ao = bpy.data.objects.new('fill', ar)
        ao.location = (0, -60, ISLAND_TOP + 150)
        ao.rotation_euler = (math.radians(12), 0, math.radians(10))
        lights.append(ao)
        # 裂隙辉光（地面 + 岛底）
        pl = bpy.data.lights.new('rift', 'POINT')
        pl.energy = 3.0e5
        pl.color = hexcol('#4fc0ff')[:3]
        pl.shadow_soft_size = 14.0
        po = bpy.data.objects.new('rift', pl)
        po.location = (70, 60, 40)
        lights.append(po)
        pl = bpy.data.lights.new('rift2', 'POINT')
        pl.energy = 2.0e5
        pl.color = hexcol('#5f80ff')[:3]
        pl.shadow_soft_size = 14.0
        po = bpy.data.objects.new('rift2', pl)
        po.location = (0, 0, 160)
        lights.append(po)
        # 塔顶晶暖光
        pl = bpy.data.lights.new('crystal', 'POINT')
        pl.energy = 1.2e5
        pl.color = hexcol('#ffe2b8')[:3]
        pl.shadow_soft_size = 3.0
        po = bpy.data.objects.new('crystal_light', pl)
        po.location = (0, 0, ISLAND_TOP + 62)
        lights.append(po)
    for lo in lights:
        bpy.context.scene.collection.objects.link(lo)
    return lights


# ================================================================ 相机
def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


CAMS = {
    # hero：地面南侧仰视——裂隙光柱托举空岛，夜空背景（史诗叙事构图）
    'hero':   dict(pos=(300, 560, 130), tgt=(-16, 10, 235), lens=62),
    # dusk：南侧仰视暮色全景（与 hero 同侧不同高度·有落日氛围）
    'dusk':   dict(pos=(312, 480, 235), tgt=(-16, 10, 232), lens=58),
    'tower':  dict(pos=(-72, -155, 335), tgt=(0, 0, 282), lens=52),
    'rift':   dict(pos=(300, 380, 40), tgt=(0, 15, 130), lens=40),
    'axis':   dict(pos=(152, -18, 258), tgt=(-45, 0, 243), lens=42),
    'aerial': dict(pos=(270, 430, 470), tgt=(-8, 18, 190), lens=44),
    'pool':   dict(pos=(-15, 150, 262), tgt=(0, 66, 226), lens=58),
}


def setup_camera(cam_name):
    spec = CAMS[cam_name]
    cam = bpy.data.cameras.new('cam_' + cam_name)
    cam.lens = spec['lens']
    cam.clip_end = 8000
    co = bpy.data.objects.new('cam_' + cam_name, cam)
    bpy.context.scene.collection.objects.link(co)
    co.location = spec['pos']
    look_at(co, spec['tgt'])
    bpy.context.scene.camera = co
    return co


# ================================================================ 场景设置
def setup_scene(res, samples, quick):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples if not quick else 12
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.08 if quick else 0.04
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 3
    sc.cycles.volume_bounces = 0
    sc.cycles.use_fast_gi = False
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    # 合成：辉光
    sc.use_nodes = True
    nt = sc.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    rl = nt.nodes.new('CompositorNodeRLayers')
    glare = nt.nodes.new('CompositorNodeGlare')
    glare.glare_type = 'FOG_GLOW'
    glare.quality = 'HIGH'
    glare.threshold = 1.0
    glare.size = 8
    comp = nt.nodes.new('CompositorNodeComposite')
    nt.links.new(rl.outputs['Image'], glare.inputs['Image'])
    nt.links.new(glare.outputs['Image'], comp.inputs['Image'])
    # 世界底色
    world = bpy.data.worlds.new('world') if not sc.world else sc.world
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs[0].default_value = hexcol('#0c1226')
        bg.inputs[1].default_value = 0.62 if quick else 0.58


# ================================================================ 主流程
def main():
    t0 = time.time()
    args = parse_args()
    os.makedirs(RENDER_DIR, exist_ok=True)
    os.makedirs(WEB_DIR, exist_ok=True)
    clean_scene()
    M = make_all()

    # ---- 几何 ----
    print('[build] geometry ...')
    g = build_ground(M)
    g.to_object()
    build_crystals(M).to_object()
    build_crack_glow(M).to_object()
    pillar, pillar_crystals = build_pillar(M)
    pillar.to_object()
    pillar_crystals.to_object()
    build_river(M).to_object()
    build_island(M).to_object()
    rocks, trees = build_floating_rocks(M)
    rocks.to_object()
    trees.to_object()
    for o in build_all(M):
        pass  # academy 内部已 link
    # 收集所有 mesh 对象
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    tris = sum(len(o.data.polygons) for o in meshes)
    print(f'[build] objects={len(meshes)} faces={tris}  t={time.time()-t0:.0f}s')

    # ---- 外观 ----
    sc = bpy.context.scene
    setup_scene(args['res'], args['samples'], args['quick'])
    build_skydome(M, args['look'])
    build_lights(M, args['look'])
    for k in GLOW_KEYS:
        set_glow(M, k, LOOK_GLOW[args['look']][k])
    cam = setup_camera(args['cam'])

    # ---- 渲染 ----
    if args['render']:
        fname = f"{args['cam']}_{args['look']}.png"
        sc.render.filepath = os.path.join(RENDER_DIR, fname)
        print(f'[render] {fname} res={args["res"]} look={args["look"]} '
              f'samples={sc.cycles.samples} ...')
        bpy.ops.render.render(write_still=True)
        print(f'[render] done t={time.time()-t0:.0f}s')
        print(f'[render] -> {sc.render.filepath}')

    # ---- GLB 导出（排除天幕/星点/相机，保留光柱与全部建筑） ----
    if args['glb']:
        ex = {'skydome', 'stars'}
        for o in bpy.data.objects:
            o.select_set(False)
        sel = [o for o in bpy.data.objects
               if o.type == 'MESH' and not any(o.name.startswith(s) for s in ex)]
        for o in sel:
            o.select_set(True)
        bpy.context.view_layer.objects.active = sel[0]
        bpy.ops.export_scene.gltf(filepath=args['glb'], use_selection=True,
                                  export_apply=True, export_yup=True)
        print(f'[glb] -> {args["glb"]}')

    # ---- .blend ----
    if args['save_blend']:
        bpy.ops.wm.save_as_mainfile(filepath=args['save_blend'])
        print(f'[blend] -> {args["save_blend"]}')


if __name__ == '__main__':
    main()
