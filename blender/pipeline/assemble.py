# -*- coding: utf-8 -*-
"""总装：岛 + 分区 +（可选）世界场景。"""
from . import island, util, mats as _mats

def build_all(zones=None, with_world=False):
    M = _mats.M
    objs = []
    objs += island.build_all(M)
    from . import city
    objs += city.build(zones, M)
    if with_world:
        from . import worldscene
        objs += worldscene.build(M)
    print(f'[assemble] total objects: {len(objs)}')
    return objs
