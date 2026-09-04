# -*- coding: utf-8 -*-
"""星槎空岛 · Build CLI
blender -b -noaudio --python blender/build.py -- --build --qa
blender -b -noaudio --python blender/build.py -- --render --shot hero_dusk --samples 48 --quick
blender -b -noaudio --python blender/build.py -- --export
"""
import sys, os, time, json, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'blender'))

OUT_TEX = os.path.join(ROOT, 'assets', 'textures')
OUT_MODEL = os.path.join(ROOT, 'models')
OUT_RENDER = os.path.join(ROOT, 'renders')

def parse():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('--build', action='store_true')
    p.add_argument('--zones', default='')
    p.add_argument('--render', action='store_true')
    p.add_argument('--shot', default='quick_mid')
    p.add_argument('--atmos', default='dusk')
    p.add_argument('--samples', type=int, default=48)
    p.add_argument('--res', default='1280x800')
    p.add_argument('--quick', action='store_true')
    p.add_argument('--export', action='store_true')
    p.add_argument('--qa', action='store_true')
    p.add_argument('--world', action='store_true', help='含世界场景（光柱/海面/灰港）')
    return p.parse_args(argv)

def main():
    a = parse()
    import bpy
    from pipeline import util, mats, geo
    from pipeline import island, cameras, assemble, qa

    t0 = time.time()
    if a.build or a.export or a.render:
        mats.init(OUT_TEX)
        # 分部分收集对象（世界场景仅 --world）
        if a.build or a.export:
            bpy.ops.wm.read_factory_settings(use_empty=True)
            mats.reset()
            util._used_names.clear()
            from pipeline import city
            zones = [z.strip() for z in a.zones.split(',') if z.strip()] or None
            objs = assemble.build_all(zones=zones, with_world=a.world or a.render)
            if a.qa:
                rep = qa.run(objs)
                print('[QA]', json.dumps(rep, ensure_ascii=False, default=str))
            if a.build:
                fn = os.path.join(OUT_MODEL, 'academy.blend')
                bpy.ops.wm.save_as_mainfile(filepath=fn)
                print(f'[build] saved {fn}  ({time.time() - t0:.1f}s)')
        elif a.render:
            # 渲染模式：直接重构建（保证与资产一致）
            bpy.ops.wm.read_factory_settings(use_empty=True)
            mats.reset()
            util._used_names.clear()
            from pipeline import city
            assemble.build_all(zones=None, with_world=True)
    if a.render:
        sc = bpy.context.scene
        sc.render.engine = 'CYCLES'
        sc.cycles.device = 'CPU'
        sc.cycles.samples = a.samples
        sc.cycles.use_denoising = False
        sc.cycles.use_adaptive_sampling = True
        sc.render.use_persistent_data = True
        try:
            w, h = map(int, a.res.split('x'))
        except Exception:
            w, h = 1280, 800
        sc.render.resolution_x = w
        sc.render.resolution_y = h
        if a.quick:
            sc.render.resolution_percentage = 40
        cameras.apply_atmos(a.atmos)
        cameras.apply_shot(a.shot)
        os.makedirs(OUT_RENDER, exist_ok=True)
        fn = os.path.join(OUT_RENDER, f'{a.shot}.png')
        sc.render.filepath = fn
        bpy.ops.render.render(write_still=True)
        print(f'[render] {fn}  ({time.time() - t0:.1f}s)')
    if a.export:
        from pipeline.export_glb import do_export
        do_export(with_world=a.world)
        print(f'[export] done ({time.time() - t0:.1f}s)')

if __name__ == '__main__':
    main()
