# -*- coding: utf-8 -*-
"""星槎空岛 · 一键构建管线
用法（在仓库根目录）：
  python3 blender/build.py --build        # 构建并保存 models/academy.blend
  python3 blender/build.py --render       # 渲染全部镜头到 renders/
  python3 blender/build.py --export       # 导出 models/academy.glb
  python3 blender/build.py --all          # 以上全部
"""
import sys, os, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'blender'))

def main():
    args = sys.argv[1:]
    do_all = '--all' in args
    t0 = time.time()

    import bpy
    from lib import geo
    from lib.mats import build_all
    from academy import assemble as A

    if do_all or '--build' in args:
        print('[build] 构建场景 …')
        bpy.ops.wm.read_factory_settings(use_empty=True)
        build_all()
        zones = A.assemble()
        print('[build] 分区：', list(zones.keys()))
        # 应用全部变换（干净导出前提）
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        os.makedirs(os.path.join(ROOT, 'models'), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'models', 'academy.blend'))
        tris = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
        print(f'[build] 完成 faces={tris} 用时={time.time()-t0:.1f}s')

    if do_all or '--render' in args:
        import render as R
        R.render_all(os.path.join(ROOT, 'renders'))

    if do_all or '--export' in args:
        import export_glb as E
        E.export(os.path.join(ROOT, 'models', 'academy.glb'))

    print('[build] 全部完成')

if __name__ == '__main__':
    main()
