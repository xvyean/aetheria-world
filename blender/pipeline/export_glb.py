# -*- coding: utf-8 -*-
"""GLB 导出：apply 全部 modifier；按集合过滤（WORLD 可选）；贴图随文件打包。"""
import bpy, os
from .qa import apply_all_modifiers

def do_export(with_world=False):
    apply_all_modifiers()
    from . import util
    bpy.ops.object.select_all(action='DESELECT')
    keep = []
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        ck = o.name.split('_')[0]
        if not with_world and ck == 'Z99':
            continue
        o.select_set(True)
        keep.append(o)
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    fn = os.path.join(ROOT, 'models', 'academy.glb' if not with_world else 'world.glb')
    bpy.context.view_layer.objects.active = keep[0] if keep else None
    bpy.ops.export_scene.gltf(filepath=fn, export_format='GLB', use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials='EXPORT', export_image_format='AUTO',
                              export_texcoords=True, export_normals=True)
    print('[export]', fn, len(keep), 'objects')
