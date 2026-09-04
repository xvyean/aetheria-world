# -*- coding: utf-8 -*-
"""分区施工包：zone -> builder。build(zones=None) 依次施工。"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

ZONES = {
    'island': None,   # 由 assemble 直接构建
    'tower':  'tower',
    'plaza':  'plaza',
    'cloister': 'cloister',
    'dawu':   'dawu',
    'lingu':  'lingu',
    'hamm':   'hamm',
    'sea':    'sea',
    'pool':   'pool',
    'library': 'library',
    'dorm':   'dorm',
    'gate':   'gate',
    'clock':  'clock',
    'mess':   'mess',
    'bath':   'bath',
    'grave':  'grave',
    'props':  'props',
}

def build(zones=None, M=None):
    objs = []
    if M is not None:
        from .. import geo
        geo._mats._reg  # touch
    names = zones or list(ZONES.keys())
    for zn in names:
        mod = ZONES.get(zn)
        if mod is None:
            continue
        try:
            m = __import__(f'pipeline.city.{mod}', fromlist=['build'])
            objs += m.build(M)
            print(f'[city] {zn} ok')
        except Exception as e:
            import traceback
            print(f'[city] {zn} FAILED: {e}')
            traceback.print_exc()
    return objs
