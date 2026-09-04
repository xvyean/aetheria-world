# -*- coding: utf-8 -*-
"""星槎学院 · 材质库
原则：全部 Principled 常量输入（保证 GLB 导出保真），
细节靠几何与灯光表达 —— 「几何筑造」美学。
"""
import bpy
from helpers import hexcol


def _new(name, base, rough=0.8, metal=0.0, emit=None, emit_str=0.0,
         transmission=0.0, ior=1.45, alpha=1.0, coat=0.0, sheen=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    ins = bsdf.inputs

    def setv(key, val):
        if key in ins:
            ins[key].default_value = val

    setv('Base Color', hexcol(base))
    setv('Roughness', rough)
    setv('Metallic', metal)
    setv('IOR', ior)
    if emission_ok(ins):
        setv('Emission Color', hexcol(emit) if emit else (0, 0, 0, 1))
        setv('Emission Strength', emit_str)
    if 'Transmission Weight' in ins:
        setv('Transmission Weight', transmission)
    setv('Alpha', alpha)
    if coat:
        setv('Coat Weight', coat)
    if sheen:
        setv('Sheen Weight', sheen)
    if alpha < 1.0:
        mat.blend_method = 'BLEND'
    # 视图/固色
    mat.diffuse_color = hexcol(base)
    return mat


def emission_ok(ins):
    return 'Emission Color' in ins and 'Emission Strength' in ins


def make_all():
    M = {}

    # ---------------- 石材与大地 ----------------
    M['rock'] = _new('rock', '#4a4442', rough=0.95)
    M['rock_mid'] = _new('rock_mid', '#5c5750', rough=0.9)
    M['rock_dark'] = _new('rock_dark', '#38333a', rough=0.97)
    M['moss'] = _new('moss', '#3d5432', rough=0.95)
    M['soil'] = _new('soil', '#5a5142', rough=0.95)
    M['grass'] = _new('grass', '#4e6b39', rough=0.92)
    M['wheat'] = _new('wheat', '#b89a55', rough=0.9)
    M['stone_light'] = _new('stone_light', '#d8cbb0', rough=0.75)
    M['stone_cream'] = _new('stone_cream', '#e7dcc2', rough=0.7)
    M['marble'] = _new('marble', '#efe9db', rough=0.35, coat=0.3)
    M['stone_dark'] = _new('stone_dark', '#6b6560', rough=0.85)
    M['paving'] = _new('paving', '#b9ad97', rough=0.8)
    M['roof_slate'] = _new('roof_slate', '#3c4756', rough=0.6)
    M['wood'] = _new('wood', '#6d4a30', rough=0.8)
    M['wood_dark'] = _new('wood_dark', '#4a3322', rough=0.85)
    M['rope'] = _new('rope', '#8a7350', rough=0.9)

    # ---------------- 金属 ----------------
    M['gold'] = _new('gold', '#e8b45b', rough=0.28, metal=1.0)
    M['brass'] = _new('brass', '#b98a44', rough=0.4, metal=1.0)
    M['copper'] = _new('copper', '#c97a4a', rough=0.42, metal=1.0)
    M['iron'] = _new('iron', '#555a60', rough=0.5, metal=1.0)

    # ---------------- 院色 ----------------
    M['h_dawn'] = _new('h_dawn', '#e8b45b', rough=0.85)      # 晨辉 金
    M['h_speak'] = _new('h_speak', '#2f8a4a', rough=0.85)    # 星语 绿
    M['h_forge'] = _new('h_forge', '#c97a4a', rough=0.85)    # 锤音 铜
    M['h_tide'] = _new('h_tide', '#4a9dc9', rough=0.85)      # 海心 蓝

    # ---------------- 琉璃与发光 ----------------
    M['glass_warm'] = _new('glass_warm', '#ffd9a0', rough=0.15,
                           transmission=0.3, ior=1.5)
    M['glass_h_dawn'] = _new('glass_h_dawn', '#e8b45b', rough=0.2,
                             transmission=0.4, ior=1.5)
    M['glass_h_speak'] = _new('glass_h_speak', '#2f8a4a', rough=0.2,
                              transmission=0.4, ior=1.5)
    M['glass_h_forge'] = _new('glass_h_forge', '#c97a4a', rough=0.2,
                              transmission=0.4, ior=1.5)
    M['glass_h_tide'] = _new('glass_h_tide', '#4a9dc9', rough=0.2,
                             transmission=0.4, ior=1.5)

    # 自发光（强度统一由 look 调整）
    M['glow_warm'] = _new('glow_warm', '#ffb45e', rough=0.5,
                          emit='#ffb45e', emit_str=6.0)
    M['glow_lamp'] = _new('glow_lamp', '#ffc887', rough=0.5,
                          emit='#ffc887', emit_str=9.0)
    M['glow_win'] = _new('glow_win', '#f5a85c', rough=0.5,
                         emit='#f0a050', emit_str=4.5)
    M['glow_h_dawn'] = _new('glow_h_dawn', '#e8b45b', rough=0.5,
                            emit='#f2c06a', emit_str=4.0)
    M['glow_h_speak'] = _new('glow_h_speak', '#2f8a4a', rough=0.5,
                             emit='#3fae6a', emit_str=4.0)
    M['glow_h_forge'] = _new('glow_h_forge', '#c97a4a', rough=0.5,
                             emit='#e08a52', emit_str=4.0)
    M['glow_h_tide'] = _new('glow_h_tide', '#4a9dc9', rough=0.5,
                            emit='#5fb2e0', emit_str=4.0)
    M['glow_fire'] = _new('glow_fire', '#ff8a3c', rough=0.5,
                          emit='#ff7a2e', emit_str=9.0)

    # ---------------- 裂隙 / 星辉 ----------------
    M['crystal'] = _new('crystal', '#7fb8d9', rough=0.15,
                        emit='#7fd0e8', emit_str=3.0, transmission=0.2, ior=1.6)
    M['crystal_core'] = _new('crystal_core', '#eaf8ff', rough=0.08,
                             emit='#bfeaff', emit_str=20.0)
    M['pillar'] = _new('pillar', '#5fc8ec', rough=0.5,
                       emit='#4fb8e8', emit_str=1.5)
    M['pillar_core'] = _new('pillar_core', '#b8e8ff', rough=0.5,
                            emit='#98d8f8', emit_str=4.5)
    M['rift_crack'] = _new('rift_crack', '#66ccff', rough=0.4,
                           emit='#4fc0ff', emit_str=5.0)
    M['river'] = _new('river', '#5fd0e8', rough=0.2,
                      emit='#5fd0e8', emit_str=2.2, coat=0.5)
    M['water'] = _new('water', '#1d4a66', rough=0.08,
                      transmission=0.5, ior=1.33, coat=0.6)
    M['magic_moss'] = _new('magic_moss', '#2e5c3a', rough=0.8,
                           emit='#46c86a', emit_str=1.6)

    # ---------------- 自然 ----------------
    M['leaf'] = _new('leaf', '#3d6b33', rough=0.9)
    M['leaf_dark'] = _new('leaf_dark', '#2f5230', rough=0.9)
    M['trunk'] = _new('trunk', '#5a4632', rough=0.9)
    M['sail'] = _new('sail', '#e8dfc8', rough=0.85, sheen=0.5)
    M['banner_dawn'] = _new('banner_dawn', '#e8b45b', rough=0.9, sheen=0.4)
    M['banner_speak'] = _new('banner_speak', '#2f8a4a', rough=0.9, sheen=0.4)
    M['banner_forge'] = _new('banner_forge', '#c97a4a', rough=0.9, sheen=0.4)
    M['banner_tide'] = _new('banner_tide', '#4a9dc9', rough=0.9, sheen=0.4)

    # ---------------- 天幕 ----------------
    M['sky'] = _new('sky', '#101828', rough=1.0,
                    emit='#101828', emit_str=1.0)
    M['sky_dusk'] = _new('sky_dusk', '#2a2438', rough=1.0,
                         emit='#2a2438', emit_str=1.0)
    M['star'] = _new('star', '#ffffff', rough=1.0,
                     emit='#ffffff', emit_str=16.0)
    return M


# 供 look 切换调整的自发光材质
GLOW_KEYS = ['glow_warm', 'glow_lamp', 'glow_win', 'glow_h_dawn', 'glow_h_speak',
             'glow_h_forge', 'glow_h_tide', 'glow_fire', 'crystal',
             'crystal_core', 'pillar', 'pillar_core', 'rift_crack',
             'river', 'water', 'magic_moss']


def set_glow(M, key, strength):
    mat = M[key]
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf and 'Emission Strength' in bsdf.inputs:
        bsdf.inputs['Emission Strength'].default_value = strength


LOOK_GLOW = {
    # look: {key: strength}
    'night': {'glow_warm': 6.0, 'glow_lamp': 10.0, 'glow_win': 4.5,
              'glow_h_dawn': 3.5, 'glow_h_speak': 3.5, 'glow_h_forge': 3.5,
              'glow_h_tide': 3.5, 'glow_fire': 9.0, 'crystal': 2.6,
              'crystal_core': 13.0, 'pillar': 2.2, 'pillar_core': 7.5,
              'rift_crack': 5.0, 'river': 2.0, 'water': 0.0, 'magic_moss': 1.8},
    'dusk': {'glow_warm': 4.0, 'glow_lamp': 7.0, 'glow_win': 3.2,
             'glow_h_dawn': 2.6, 'glow_h_speak': 2.6, 'glow_h_forge': 2.6,
             'glow_h_tide': 2.6, 'glow_fire': 8.0, 'crystal': 1.6,
             'crystal_core': 6.0, 'pillar': 1.6, 'pillar_core': 4.5,
             'rift_crack': 4.0, 'river': 2.2, 'water': 0.0, 'magic_moss': 1.2},
}
