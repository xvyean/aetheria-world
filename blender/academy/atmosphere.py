# -*- coding: utf-8 -*-
"""
星槎学院 · 氛围与渲染管线
------------------------
从 build.py 抽离：世界天空、太阳光 rig、云海、大气雾合成与 Cycles 渲染参数。
职责单一：只负责"看起来如何"，不负责几何与导出。
"""
import bpy
import math
from mathutils import Vector, noise

from util import *
import layout as LY
import island as IS

def setup_render(quality):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    Q = {'preview': (16, 960, 540), 'low': (24, 1280, 720), 'high': (48, 1440, 810)}[quality]
    sc.cycles.samples = Q[0]
    denoisers = [i.identifier for i in sc.cycles.bl_rna.properties['denoiser'].enum_items]
    if 'OPENIMAGEDENOISE' in denoisers:
        sc.cycles.use_denoising = True
        sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    else:
        sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 4
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.use_auto_tile = True
    sc.cycles.tile_size = 512          # 分块渲染，2 GB 内存的沙盒也能跑高分辨率
    sc.render.resolution_x = Q[1]
    sc.render.resolution_y = Q[2]
    sc.render.film_transparent = True          # 背景由合成器用 Env 通道贴回（这样雾不会吃掉天空渐变）
    vts = [i.identifier for i in sc.view_settings.bl_rna.properties['view_transform'].enum_items]
    sc.view_settings.view_transform = 'Filmic' if 'Filmic' in vts else ('AgX' if 'AgX' in vts else 'Standard')
    looks = [i.identifier for i in sc.view_settings.bl_rna.properties['look'].enum_items]
    for lk in ('Medium High Contrast', 'High Contrast', 'AgX - Punchy', 'Punchy'):
        if lk in looks:
            sc.view_settings.look = lk
            break
    sc.view_settings.exposure = 0.15
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
    bg.inputs['Strength'].default_value = 0.6
    # 太阳：午后偏西南，暖色，强对比
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 100))
    sun = bpy.context.object
    sun.data.energy = 6.0
    sun.data.angle = math.radians(1.1)
    sun.data.color = (1.0, 0.58, 0.28)
    sun.rotation_euler = (math.radians(72), 0, math.radians(232))
    # 补光：冷色天光（从东北低角度）
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 100))
    fill = bpy.context.object
    fill.data.energy = 0.3
    fill.data.angle = math.radians(24.0)
    fill.data.color = (0.55, 0.70, 1.0)
    fill.rotation_euler = (math.radians(72), 0, math.radians(40))
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
    scale = nt.nodes.new('CompositorNodeMath'); scale.operation = 'MULTIPLY'; scale.inputs[1].default_value = 0.4
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
    glare = nt.nodes.new('CompositorNodeGlare')
    glare.glare_type = 'FOG_GLOW'
    glare.quality = 'HIGH'
    glare.threshold = 1.0
    glare.mix = -0.45
    glare.size = 8
    nt.links.new(over.outputs[0], glare.inputs['Image'])
    nt.links.new(glare.outputs[0], comp.inputs['Image'])


