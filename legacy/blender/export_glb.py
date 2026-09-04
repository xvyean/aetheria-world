# -*- coding: utf-8 -*-
"""GLB 导出：供网页（three.js r128 时代 UMD + 配套 GLTFLoader）集成。
策略：材质退化为纯色 + 自发光保留（程序化节点无法进 glTF，导出前重建 flat 材质）。
"""
import bpy, os, sys

FLAT = {
    'sandstone': ('#e8e4d8', 0.0, 0.55, None, 0),
    'limestone': ('#f0ece0', 0.0, 0.5, None, 0),
    'slate': ('#4a4a4a', 0.0, 0.6, None, 0),
    'basalt': ('#6f6660', 0.0, 1.0, None, 0),
    'dark_stone': ('#3a3a3a', 0.0, 0.7, None, 0),
    'mountain_rock': ('#7a6a58', 0.0, 0.9, None, 0),
    'cobble': ('#cfc8b8', 0.0, 0.8, None, 0),
    'plaza_dark': ('#5a5a52', 0.0, 0.75, None, 0),
    'plaza_mid': ('#8a8578', 0.0, 0.75, None, 0),
    'tile_deep': ('#4a4a4a', 0.0, 0.55, None, 0),
    'tile_dawn': ('#e8b45b', 0.15, 0.35, None, 0),
    'tile_speak': ('#2f7d4a', 0.15, 0.35, None, 0),
    'tile_forge': ('#c97a4a', 0.15, 0.35, None, 0),
    'tile_tide': ('#3a6f9a', 0.15, 0.35, None, 0),
    'gold': ('#d9b45b', 0.85, 0.3, None, 0),
    'copperverde': ('#4a8a7a', 0.6, 0.45, None, 0),
    'iron': ('#55504a', 0.8, 0.6, None, 0),
    'bronze': ('#8a6a3a', 0.85, 0.45, None, 0),
    'glass_warm': ('#ffd9a0', 0.0, 0.3, '#ffcf8a', 2.0),
    'glass_cool': ('#d8ecff', 0.0, 0.25, '#bfe8ff', 1.6),
    'crystal': ('#bfefff', 0.0, 0.15, '#bfefff', 3.5),
    'lantern': ('#ffc87a', 0.0, 0.3, '#ffb85a', 2.6),
    'wood': ('#c8b8a0', 0.0, 0.7, None, 0),
    'wood_dark': ('#8a6a4a', 0.0, 0.75, None, 0),
    'wood_beam': ('#a89070', 0.0, 0.7, None, 0),
    'rope': ('#b8a888', 0.0, 0.9, None, 0),
    'grass': ('#4a6a35', 0.0, 0.95, None, 0),
    'soil': ('#4a3a2a', 0.0, 1.0, None, 0),
    'foliage': ('#2f5a34', 0.0, 0.9, None, 0),
    'foliage_light': ('#3f7243', 0.0, 0.9, None, 0),
    'foliage_autumn': ('#c88a3a', 0.0, 0.9, None, 0),
    'trunk': ('#6b4a30', 0.0, 0.9, None, 0),
    'flower_gold': ('#e8c85a', 0.0, 0.7, '#e8c85a', 0.2),
    'flower_white': ('#e8e8e8', 0.0, 0.7, None, 0),
    'flower_blue': ('#5a8ac9', 0.0, 0.7, None, 0),
    'flower_purple': ('#7a5a9a', 0.0, 0.7, None, 0),
    'water': ('#3a9dc0', 0.1, 0.1, '#1a4a66', 0.3),
    'cloth_dawn': ('#e8b45b', 0.0, 0.8, None, 0),
    'cloth_speak': ('#2f7d4a', 0.0, 0.8, None, 0),
    'cloth_forge': ('#c97a4a', 0.0, 0.8, None, 0),
    'cloth_tide': ('#4a9dc9', 0.0, 0.8, None, 0),
    'cloth_white': ('#e8e8e0', 0.0, 0.8, None, 0),
}

def _hx2rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

def flatten_materials():
    """把程序化材质替换为纯色版本（按名称映射，逐 mesh 槽位替换）。"""
    cache = {}
    def flat_of(name):
        if name in cache:
            return cache[name]
        spec = FLAT.get(name)
        if spec is None:
            return None
        hx, metal, rough, ehx, estr = spec
        mat = bpy.data.materials.new('flat_' + name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get('Principled BSDF')
        rgb = _hx2rgb(hx)
        bsdf.inputs['Base Color'].default_value = (*rgb, 1)
        bsdf.inputs['Metallic'].default_value = metal
        bsdf.inputs['Roughness'].default_value = rough
        if ehx:
            e = _hx2rgb(ehx)
            bsdf.inputs['Emission Color'].default_value = (*e, 1)
            bsdf.inputs['Emission Strength'].default_value = estr
        cache[name] = mat
        return mat
    for me in bpy.data.meshes:
        for i, slot in enumerate(me.materials):
            if slot is None:
                continue
            fm = flat_of(slot.name)
            if fm is not None:
                me.materials[i] = fm

def export(path):
    flatten_materials()
    bpy.ops.object.select_all(action='SELECT')
    kwargs = dict(filepath=path, export_format='GLB', use_selection=True,
                  export_apply=True, export_yup=True)
    try:
        bpy.ops.export_scene.gltf(**kwargs)
    except TypeError:
        kwargs.pop('export_yup', None)
        bpy.ops.export_scene.gltf(**kwargs)
    print('[glb] exported', path, os.path.getsize(path) // 1024, 'KB')

if __name__ == '__main__':
    export(sys.argv[1] if len(sys.argv) > 1 else 'models/academy.glb')
