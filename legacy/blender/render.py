# -*- coding: utf-8 -*-
"""渲染器：三氛围 × 六机位（建筑志 拾贰 · 镜头基准）。
氛围：dusk(暮潮·主推) / dawn(晨辉) / night(星夜)。CPU Cycles + OpenImageDenoise。
v2：Nishita 渐变天空 + 暖橙低角度太阳 + 环境补光（修复"像正午"的问题）。
"""
import bpy, math, os, time, random
from math import radians as D
from mathutils import Vector

SCN = None

def _set(scn):
    global SCN
    SCN = scn

def _sky(world, elev, azim, sun_int=0.02, sun_disc=0.12, strength=0.42, tint=(1, 1, 1)):
    w = bpy.data.worlds.new(world); w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    sky = nt.nodes.new('ShaderNodeTexSky')
    try:
        sky.sky_type = 'MULTIPLE_SCATTERING'
        sky.sun_elevation = elev
        sky.sun_rotation = azim
        sky.sun_intensity = sun_int
        sky.sun_disc = True
        sky.sun_size = 0.035
        sky.air_density = 1.0
        sky.ozone_density = 0.9
        sky.aerosol_density = 0.9
        sky.ground_albedo = 0.25
        sky.turbidity = 2.6
    except Exception:
        pass
    nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = strength
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    SCN.world = w

def light_setup(mood):
    scn = SCN
    for ob in [o for o in bpy.data.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(ob, do_unlink=True)
    # 清除旧的星星
    old = bpy.data.objects.get('stars')
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    if mood == 'dusk':
        _sky('W_dusk', D(9), D(-128), sun_int=0.045, sun_disc=0.35, strength=0.34)
        sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.0
        sun.color = (1.0, 0.55, 0.22); sun.angle = D(1.2)
        so = bpy.data.objects.new('sun', sun); scn.collection.objects.link(so)
        so.rotation_euler = (D(28), 0, D(-136))
        em = bpy.data.lights.new('dusk_rim', 'AREA'); em.energy = 2600; em.size = 52
        em.color = (1.0, 0.62, 0.35)
        eo = bpy.data.objects.new('dusk_rim', em); scn.collection.objects.link(eo)
        eo.location = (-68, -46, 20); eo.rotation_euler = (D(62), 0, D(-48))
        fl = bpy.data.lights.new('dusk_fill', 'AREA'); fl.energy = 950; fl.size = 58
        fl.color = (0.42, 0.55, 0.85)
        fo = bpy.data.objects.new('dusk_fill', fl); scn.collection.objects.link(fo)
        fo.location = (55, 48, 26); fo.rotation_euler = (D(58), 0, D(138))
    elif mood == 'dawn':
        _sky('W_dawn', D(22), D(-84), sun_int=0.06, sun_disc=0.3, strength=0.55)
        sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 4.4
        sun.color = (1.0, 0.83, 0.58); sun.angle = D(1.5)
        so = bpy.data.objects.new('sun', sun); scn.collection.objects.link(so)
        so.rotation_euler = (D(18), 0, D(-100))
        fl = bpy.data.lights.new('dawn_fill', 'AREA'); fl.energy = 1500; fl.size = 64
        fl.color = (0.6, 0.72, 1.0)
        fo = bpy.data.objects.new('dawn_fill', fl); scn.collection.objects.link(fo)
        fo.location = (40, -60, 30); fo.rotation_euler = (D(55), 0, D(-55))
    else:
        _sky('W_night', D(6), D(35), sun_int=0.0, sun_disc=0.0, strength=0.10, tint=(0.7, 0.78, 1.0))
        # 星空
        random.seed(7)
        verts = []
        for i in range(1100):
            a = random.uniform(0, math.tau)
            el = random.uniform(0.12, math.pi / 2 - 0.04)
            r = 500
            verts.append((math.cos(a) * math.cos(el) * r, math.sin(a) * math.cos(el) * r, math.sin(el) * r))
        me = bpy.data.meshes.new('stars'); me.from_pydata(verts, [], []); me.update()
        st = bpy.data.objects.new('stars', me); scn.collection.objects.link(st)
        sm = bpy.data.materials.new('starmat'); sm.use_nodes = True
        bs = sm.node_tree.nodes['Principled BSDF']
        bs.inputs['Emission Color'].default_value = (0.86, 0.92, 1, 1)
        bs.inputs['Emission Strength'].default_value = 9
        st.data.materials.append(sm)
        moon = bpy.data.lights.new('moon', 'SUN'); moon.energy = 1.1
        moon.color = (0.55, 0.66, 0.95); moon.angle = D(2.5)
        mo = bpy.data.objects.new('moon', moon); scn.collection.objects.link(mo)
        mo.rotation_euler = (D(48), 0, D(38))
        fl = bpy.data.lights.new('night_fill', 'AREA'); fl.energy = 380; fl.size = 60
        fl.color = (0.35, 0.42, 0.7)
        fo = bpy.data.objects.new('night_fill', fl); scn.collection.objects.link(fo)
        fo.location = (0, 0, 60); fo.rotation_euler = (0, 0, 0)
        gl = bpy.data.lights.new('crystal_glow', 'POINT'); gl.energy = 5200
        gl.color = (0.72, 0.9, 1.0); gl.shadow_soft_size = 7
        go = bpy.data.objects.new('crystal_glow', gl); scn.collection.objects.link(go)
        go.location = (0, 0, 37)
    # 学院暖窗点光（三氛围通用补光）
    for i, (x, y, z, e) in enumerate([(6, 6, 7, 260), (-6, -6, 7, 260), (0, 0, 15, 380),
                                      (-11, -11, 6, 200), (14, 14, 3, 160)]):
        if mood == 'night':
            e *= 2.2
        pl = bpy.data.lights.new(f'wl{i}', 'POINT')
        pl.energy = e; pl.color = (1.0, 0.75, 0.45); pl.shadow_soft_size = 2.6
        po = bpy.data.objects.new(f'wl{i}', pl); scn.collection.objects.link(po)
        po.location = (x, y, z)

def camera(name, loc, target, lens=40):
    for c in [o for o in bpy.data.objects if o.type == 'CAMERA']:
        bpy.data.objects.remove(c, do_unlink=True)
    cam = bpy.data.cameras.new(name); cam.lens = lens
    co = bpy.data.objects.new(name, cam); SCN.collection.objects.link(co)
    co.location = loc
    dirv = Vector(target) - Vector(loc)
    co.rotation_euler = dirv.to_track_quat('-Z', 'Y').to_euler()
    SCN.camera = co
    return co

SHOTS = [
    ('hero_dusk',    (52, -58, 44),  (0, 0, 2),     38, 'dusk'),
    ('gate_dusk',    (30, -40, 9),   (20.5, -17, 3.5), 38, 'dusk'),
    ('tower_dusk',   (-15, 27, 9),   (0, 0, 15),     32, 'dusk'),
    ('plaza_dusk',   (15, 28, 7.5),  (0, 8, 2.5),    32, 'dusk'),
    ('library_dawn', (-31, -23, 15), (-10.5, -9, 4), 36, 'dawn'),
    ('sea_night',    (31, 45, 7),    (11, 19, 2.5),  36, 'night'),
]

def render_all(outdir, shots=None, res=(960, 640), samples=40):
    shots = shots or SHOTS
    os.makedirs(outdir, exist_ok=True)
    scn = bpy.context.scene
    _set(scn)
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = samples
    scn.cycles.use_denoising = True
    try:
        scn.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    scn.cycles.device = 'CPU'
    scn.render.resolution_x = res[0]
    scn.render.resolution_y = res[1]
    scn.render.film_transparent = False
    scn.view_settings.look = 'AgX - Medium High Contrast'
    for (name, loc, tgt, lens, mood) in shots:
        t0 = time.time()
        light_setup(mood)
        camera(name, loc, tgt, lens)
        scn.render.filepath = os.path.join(outdir, name + '.png')
        bpy.ops.render.render(write_still=True)
        print(f'[render] {name} {time.time()-t0:.0f}s')

if __name__ == '__main__':
    import sys
    render_all(sys.argv[1] if len(sys.argv) > 1 else 'renders')
