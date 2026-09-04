# 质量评估渲染：高分辨率，检查细节与新增机位
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R

bpy.ops.wm.open_mainfile(filepath=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models', 'academy.blend'))
shots = [
    ('q_hero',    (52, -58, 44), (0, 0, 2),       38, 'dusk'),
    ('q_underside', (34, -44, -26), (0, 0, -12),   36, 'dusk'),
    ('q_dawn',    (30, -8, 10),   (14, 20, 3),     34, 'dusk'),
    ('q_dawn_gate', (24, -26, 6), (21, -18, 3),    40, 'dusk'),
]
R.render_all('renders', shots=shots, res=(960, 640), samples=32)
