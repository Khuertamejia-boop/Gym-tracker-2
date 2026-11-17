# Cable tower + rope for the face pull: one upright steel column in front of the athlete with a pulley carriage at
# face height, a steel cable from the pulley to the rope's clip, and the two rope strands from the clip into the fists
# (rope end knobs below the little fingers).
import bpy, math
from mathutils import Vector, Matrix

def _mat(name, col, rough, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    return m

def _box(name, c, size, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0)); o = bpy.context.active_object; o.name = name
    o.scale = size; bpy.ops.object.transform_apply(scale=True); o.location = Vector(c)
    if bevel > 0: bv = o.modifiers.new('bv', 'BEVEL'); bv.width = bevel; bv.segments = 3
    o.data.materials.append(mat); bpy.ops.object.shade_smooth(); return o

def _cyl(name, a, b, r, mat, verts=32):
    a = Vector(a); b = Vector(b); d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(0, 0, 0))
    o = bpy.context.active_object; o.name = name
    o.matrix_world = Matrix.Translation((a + b) / 2) @ Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    o.data.materials.append(mat); bpy.ops.object.shade_smooth(); return o

def _sphere(name, c, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=r, location=Vector(c))
    o = bpy.context.active_object; o.name = name; o.data.materials.append(mat); bpy.ops.object.shade_smooth(); return o

def _tube(name, pts, r, mat):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 6
    cu.use_fill_caps = True
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for p, P in zip(sp.points, pts): p.co = (P.x, P.y, P.z, 1)
    o = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(o); cu.materials.append(mat); return o

def _bez(p0, p1, p2, n=24):
    return [p0 * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + p2 * t * t for t in [k / (n - 1) for k in range(n)]]

def build(ropes, rR, q, E):
    for o in [o for o in bpy.data.objects if o.name.startswith('Banco')]: bpy.data.objects.remove(o, do_unlink=True)
    steel = _mat('banco_grey', (0.55, 0.55, 0.57), 0.35, 0.6); dark = _mat('banco_dark', (0.035, 0.035, 0.04), 0.5, 0.2)
    rope = _mat('banco_rope', (0.05, 0.05, 0.055), 0.85); cable = _mat('banco_cable', (0.12, 0.12, 0.13), 0.4, 0.7)
    frame = _mat('banco_frame', (0.74, 0.75, 0.77), 0.45, 0.3)
    cL, aL = ropes['L']; cR, aR = ropes['R']
    mid = (cL + cR) / 2
    A = Vector((0, min(cL.y, cR.y) - E('AFWD', 0.21), mid.z + E('ADZ', -0.035)))     # rope clip
    for Ls, (c, a) in ropes.items():
        # thumbs against the knobs (classic face-pull grip): knob on the index/thumb side, strand leaves the fist
        # under the little finger and bends tightly towards the clip
        top = c + a * E('RTOP', 0.04); ex = c - a * E('REX', 0.045)
        tdir = (A - ex); ctrl = ex - a * min(E('RBEND', 0.025), tdir.length * 0.3)
        pts = [top, c, ex] + _bez(ex, ctrl, A)[1:]
        _tube('Banco_rope_' + Ls, pts, rR * 0.92, rope)
        _sphere('Banco_knob_' + Ls, c + a * (E('RTOP', 0.04) + 0.012), rR * 1.75, rope)
    _cyl('Banco_clip', A + Vector((0, 0.012, 0)), A - Vector((0, 0.03, 0)), 0.009, cable, 16)
    Pp = Vector((0, E('PULY', -1.20), E('PULZ', 1.50)))                                   # pulley (fixed)
    _tube('Banco_cable', [A - Vector((0, 0.03, 0)), Pp + Vector((0, 0.03, 0))], 0.0035, cable)
    _cyl('Banco_wheel', Pp + Vector((0.016, 0, 0)), Pp - Vector((0.016, 0, 0)), 0.045, dark)
    _cyl('Banco_axle', Pp + Vector((0.032, 0, 0)), Pp - Vector((0.032, 0, 0)), 0.010, steel, 16)
    # cable tower in the style of the reference plates: light-grey frame, black weight stack and feet
    ry = Pp.y - 0.075                                    # adjustable rail (front, centred) that carries the pulley
    _box('Banco_rail', (0, ry, 1.13), (0.06, 0.06, 2.06), frame, 0.006)
    _box('Banco_carriage', (0, ry + 0.01, Pp.z), (0.085, 0.08, 0.20), frame, 0.008)
    _box('Banco_pin', (0.058, ry + 0.01, Pp.z - 0.06), (0.03, 0.018, 0.018), dark, 0.004)
    W2, yc, H = 0.27, ry - 0.22, 2.20
    for sx in (-1, 1):
        _box('Banco_up%d' % sx, (sx * W2, yc, H / 2 + 0.05), (0.075, 0.075, H - 0.1), frame, 0.008)
        _box('Banco_foot%d' % sx, (sx * W2, yc + 0.02, 0.03), (0.08, 0.62, 0.06), dark, 0.01)
        for ey in (-0.29, 0.33):
            _box('Banco_pad%d%d' % (sx, int(ey * 100)), (sx * W2, yc + ey, 0.025), (0.10, 0.07, 0.05), dark, 0.01)
        _cyl('Banco_rod%d' % sx, (sx * 0.085, yc, 0.08), (sx * 0.085, yc, H), 0.012, frame, 16)
    _box('Banco_topbeam', (0, yc + 0.05, H + 0.02), (2 * W2 + 0.10, 0.36, 0.07), frame, 0.008)
    _box('Banco_lowbeam', (0, yc, 0.07), (2 * W2, 0.08, 0.05), frame, 0.006)
    _box('Banco_railfoot', (0, (ry + yc) / 2, 0.08), (0.08, ry - yc + 0.08, 0.05), frame, 0.006)
    n = 15
    nsel, lift = int(E('NSEL', 6)), E('LIFT', 0.20) * q   # selected plates rise as the rope is pulled
    for k in range(n):                                   # weight plates
        dz = lift if k >= n - nsel else 0.0
        _box('Banco_plate%02d' % k, (0, yc, 0.12 + k * 0.034 + dz), (0.30, 0.15, 0.030), dark, 0.004)
    _box('Banco_stacktop', (0, yc, 0.12 + n * 0.034 + 0.01 + lift), (0.26, 0.10, 0.035), frame, 0.006)
    print('rope clip %s pulley %s' % (tuple(round(v, 3) for v in A), tuple(round(v, 3) for v in Pp)))
