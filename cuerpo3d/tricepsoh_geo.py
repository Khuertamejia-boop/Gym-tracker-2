# Cable tower BEHIND the athlete for the overhead triceps extension (same tower and rope as the face pull, mirrored):
# high pulley behind and above the head, steel cable to the rope clip, two rope strands into the fists (knob on the
# thumb side, strand leaves under the little finger and bends towards the clip). Selected plates rise as the hands
# move away from the pulley.
import bpy, math
from mathutils import Vector, Matrix
from facepull_geo import _mat, _box, _cyl, _sphere, _tube, _bez

def build(ropes, rR, q, E):
    for o in [o for o in bpy.data.objects if o.name.startswith('Banco')]: bpy.data.objects.remove(o, do_unlink=True)
    steel = _mat('banco_grey', (0.55, 0.55, 0.57), 0.35, 0.6); dark = _mat('banco_dark', (0.035, 0.035, 0.04), 0.5, 0.2)
    rope = _mat('banco_rope', (0.05, 0.05, 0.055), 0.85); cable = _mat('banco_cable', (0.12, 0.12, 0.13), 0.4, 0.7)
    frame = _mat('banco_frame', (0.97, 0.97, 0.98), 0.6, 0.0)
    Pp = Vector((0, E('PULY', 0.95), E('PULZ', 1.95)))                     # high pulley behind the athlete
    cL, aL = ropes['L']; cR, aR = ropes['R']
    mid = (cL + cR) / 2
    A = mid + (Pp - mid).normalized() * E('CLIPD', 0.20)                     # rope clip, towards the pulley
    for Ls, (c, a) in ropes.items():
        top = c + a * E('RTOP', 0.04); ex = c - a * E('REX', 0.045)
        tdir = (A - ex); ctrl = ex - a * min(E('RBEND', 0.03), tdir.length * 0.3)
        pts = [top, c, ex] + _bez(ex, ctrl, A)[1:]
        _tube('Banco_rope_' + Ls, pts, rR * 0.92, rope)
        _sphere('Banco_knob_' + Ls, c + a * (E('RTOP', 0.04) + 0.012), rR * 1.75, rope)
    cd = (Pp - A).normalized()
    _cyl('Banco_clip', A - cd * 0.012, A + cd * 0.03, 0.009, cable, 16)
    _tube('Banco_cable', [A + cd * 0.03, Pp - cd * 0.045], 0.0035, cable)
    _cyl('Banco_wheel', Pp + Vector((0.016, 0, 0)), Pp - Vector((0.016, 0, 0)), 0.045, dark)
    _cyl('Banco_axle', Pp + Vector((0.032, 0, 0)), Pp - Vector((0.032, 0, 0)), 0.010, steel, 16)
    ry = Pp.y + 0.075                                    # adjustable rail (centred) that carries the pulley
    _box('Banco_rail', (0, ry, 1.13), (0.06, 0.06, 2.06), frame, 0.006)
    _box('Banco_carriage', (0, ry - 0.01, Pp.z), (0.085, 0.08, 0.20), frame, 0.008)
    _box('Banco_pin', (0.058, ry - 0.01, Pp.z - 0.06), (0.03, 0.018, 0.018), dark, 0.004)
    W2, yc, H = 0.27, ry + 0.22, 2.20
    for sx in (-1, 1):
        _box('Banco_up%d' % sx, (sx * W2, yc, H / 2 + 0.05), (0.075, 0.075, H - 0.1), frame, 0.008)
        _box('Banco_foot%d' % sx, (sx * W2, yc - 0.02, 0.03), (0.08, 0.62, 0.06), dark, 0.01)
        for ey in (0.29, -0.33):
            _box('Banco_pad%d%d' % (sx, int(ey * 100)), (sx * W2, yc + ey, 0.025), (0.10, 0.07, 0.05), dark, 0.01)
        _cyl('Banco_rod%d' % sx, (sx * 0.085, yc, 0.08), (sx * 0.085, yc, H), 0.012, frame, 16)
    _box('Banco_topbeam', (0, yc - 0.05, H + 0.02), (2 * W2 + 0.10, 0.36, 0.07), frame, 0.008)
    _box('Banco_lowbeam', (0, yc, 0.07), (2 * W2, 0.08, 0.05), frame, 0.006)
    _box('Banco_railfoot', (0, (ry + yc) / 2, 0.08), (0.08, yc - ry + 0.08, 0.05), frame, 0.006)
    n = 15
    nsel, lift = int(E('NSEL', 5)), E('LIFT', 0.30) * q
    for k in range(n):
        dz = lift if k >= n - nsel else 0.0
        _box('Banco_plate%02d' % k, (0, yc, 0.12 + k * 0.034 + dz), (0.30, 0.15, 0.030), dark, 0.004)
    _box('Banco_stacktop', (0, yc, 0.12 + n * 0.034 + 0.01 + lift), (0.26, 0.10, 0.035), frame, 0.006)
    print('rope clip %s pulley %s' % (tuple(round(v, 3) for v in A), tuple(round(v, 3) for v in Pp)))
