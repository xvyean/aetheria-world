# -*- coding: utf-8 -*-
"""相机与灯光组：机位 × 氛围。 shot spec 见《建筑志 v2》拾肆。"""
import bpy, math
from math import radians as D
from mathutils import Vector
from . import layout, util

SHOTS = {
    'hero_dusk':    ((84, 72, 40), (0, 0, 8), 40),
    'gate_dusk':    ((34.5, -34.5, 7.5), (20.5, -20.5, 3.2), 42),
    'tower_dusk':   ((13, 27, 10), (0, 0, 18), 44),
    'plaza_dusk':   ((-9, 16.5, 8.5), (0, 10.5, 1), 30),
    'library_dawn': ((-26, 26, 10), (-15, 13, 3.5), 38),
    'pool_night':   ((21, 35.5, 3.6), (14.4, 20, 0.6), 42),
    'cloister_close': ((7, 12, 3), (0, 7, 1.5), 30),
    'island_under': ((78, -58, -12), (0, 0, 7), 52),
    'world_dusk':   ((128, 124, 22), (0, 0, -8), 44),
    'quick_mid':    ((58, 50, 32), (0, 0, 6), 40),
}

ATMOS = {
    'dusk':  dict(sun_dir=(-0.62, 0.36, 0.30), sun_energy=4.2, sun_color=(1.0, 0.80, 0.52),
                  fill_dir=(0.5, -0.4, 0.6), fill_energy=2.6, fill_color=(0.80, 0.87, 1.0),
                  amb_energy=0.55, sky_strength=1.0,
                  sky=(0.38, 0.26, 0.16),
                  exposure=0.55, crystal_glow=6.0),
    'dawn':  dict(sun_dir=(0.85, 0.5, 0.35), sun_energy=4.6, sun_color=(1.0, 0.85, 0.65),
                  fill_dir=(-0.4, -0.5, 0.55), fill_energy=2.6, fill_color=(0.87, 0.92, 1.0),
                  amb_energy=0.7, sky_strength=1.0,
                  sky=(0.60, 0.60, 0.62),
                  exposure=0.5, crystal_glow=3.0),
    'night': dict(amb_energy=0.32, sky_strength=0.6,
                  sky=(0.06, 0.09, 0.18),
                  fill_dir=(0.3, 0.5, 0.45), fill_energy=1.4, fill_color=(0.45, 0.55, 0.8),
                  sun_dir=(0.35, -0.55, 0.6), sun_energy=1.3, sun_color=(0.6, 0.7, 1.0),
                  exposure=0.8, crystal_glow=2.2),
}

def _light(name, kind, energy, color, loc, rot):
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, bpy.data.lights.new(name, kind))
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.energy = energy
    ob.data.color = color
    ob.location = loc
    ob.rotation_euler = rot
    return ob

def _lamp(name, energy, color, loc):
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, bpy.data.lights.new(name, 'POINT'))
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.energy = energy
    ob.data.color = color
    ob.location = loc
    ob.data.shadow_soft_size = 2.0
    return ob

def build_atmosphere(atmos):
    sc = bpy.context.scene
    if sc.world is None:
        sc.world = bpy.data.worlds.new('AetheriaWorld')
    sc.world.use_nodes = True
    nt = sc.world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    # 关键：把背景节点连接到输出（否则世界渲染为黑）
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    # 纯色背景（Cycles 世界背景稳定）——用天空色的"平均色"；大气感交给分层的远山/雾
    bg.inputs['Color'].default_value = (*atmos['sky'], 1.0)
    bg.inputs['Strength'].default_value = atmos['sky_strength']

    _light('SUN_main', 'SUN', atmos['sun_energy'], atmos['sun_color'],
           Vector(atmos['sun_dir']) * 20,
           (-Vector(atmos['sun_dir'])).to_track_quat('-Z', 'Y').to_euler())
    _light('SUN_fill', 'SUN', atmos['fill_energy'], atmos['fill_color'],
           Vector(atmos['fill_dir']) * 18,
           (-Vector(atmos['fill_dir'])).to_track_quat('-Z', 'Y').to_euler())
    for i, d in enumerate([(0.8, 0.4, 0.5), (-0.7, 0.5, 0.35), (0.2, -0.9, 0.3), (-0.4, -0.4, 0.8)]):
        _lamp(f'LIGHT_bounce{i}', atmos['amb_energy'] * 260.0, (0.9, 0.9, 1.0),
              (Vector(d).normalized() * (30 + 2 * i)).to_tuple())
    _lamp('LIGHT_crystal', atmos['crystal_glow'] * 8.0, (0.75, 0.95, 1.0), (0, 0, 34.5))

    # 场景设置：Filmic 保持色彩
    sc.render.film_transparent = False
    try:
        sc.view_settings.view_transform = 'Standard'
        sc.view_settings.exposure = atmos['exposure'] + 0.35
    except Exception:
        pass
    return None

def apply_shot(name):
    sc = bpy.context.scene
    pos, tgt, lens = SHOTS[name]
    cam = bpy.data.objects.get('CAM_main') or bpy.data.objects.new('CAM_main', bpy.data.cameras.new('CAM_main'))
    for c in list(cam.users_collection):
        c.objects.unlink(cam)
    sc.collection.objects.link(cam)
    cam.data.lens = lens
    cam.location = pos
    d = Vector(tgt) - Vector(pos)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    return cam

def apply_atmos(key):
    build_atmosphere(ATMOS[key])
