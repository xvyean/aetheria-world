# -*- coding: utf-8 -*-
"""分区公共助手：把本地坐标（front=-Y 朝塔）摆到世界。"""
import math
from math import radians as D, cos, sin

def place(objs, ox, oy, rotz):
    """objs 以局部坐标构建（front=-Y）；按 yard(theta) 摆位。"""
    c, s = cos(rotz), sin(rotz)
    for o in objs:
        x, y = o.location.x, o.location.y
        o.location = (ox + x * c - y * s, oy + x * s + y * c, o.location.z)
        e = o.rotation_euler
        o.rotation_euler = (e.x, e.y, e.z + rotz)
    return objs

def yard_rot(theta):
    return D(theta) - math.pi / 2

def yard_center(theta, r):
    return (cos(D(theta)) * r, sin(D(theta)) * r)
