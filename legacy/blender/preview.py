# 快速预览渲染（项目迭代用）：加载 models/academy.blend，低采样渲染指定镜头
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R

bpy.ops.wm.open_mainfile(filepath=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models', 'academy.blend'))
shots = [
    ('prev_hero',   (52, -58, 46), (0, 0, 2),     38, 'dusk'),
    ('prev_gate',   (34, -38, 10), (19.5, -15, 4), 40, 'dusk'),
    ('prev_tower',  (-17, 26, 8),  (0, 0, 16),     34, 'dusk'),
    ('prev_plaza',  (16, 27, 7),   (0, 8, 3),      34, 'dusk'),
]
R.render_all('renders', shots=shots, res=(640, 427), samples=12)
