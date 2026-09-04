import bpy, inspect
print("BLENDER", bpy.app.version_string)

# 1) clean scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# 2) principled inputs
m = bpy.data.materials.new("T"); m.use_nodes = True
p = m.node_tree.nodes.get("Principled BSDF")
names = [i.name for i in p.inputs]
print("PRINCIPLED_INPUTS:", names)

# 3) bevel modifier + apply
bpy.ops.mesh.primitive_cube_add()
ob = bpy.context.active_object
mod = ob.modifiers.new("B", 'BEVEL'); mod.width = 0.05; mod.segments = 2
bpy.context.view_layer.objects.active = ob
bpy.ops.object.modifier_apply(modifier="B")
print("BEVEL_OK verts:", len(ob.data.vertices))

# 4) vertex color attribute
me = ob.data
att = me.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')
print("VCOL_OK", att.name)

# 5) cycles device info / render engines
print("ENGINES:", [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items])

# 6) gltf export operator presence
print("HAS_GLTF:", hasattr(bpy.ops.export_scene, "gltf"))

# 7) camera + light basic
bpy.ops.object.camera_add(); cam = bpy.context.active_object
print("CAM_OK", cam.name)
print("API_SMOKE_DONE")
