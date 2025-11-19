bl_info = {
    "name": "CSL Cinematography Camera Pack",
    "author": "Zhina Lotfi",
    "version": (1, 0, 0),
    "blender": (4, 4, 3),
    "location": "View3D > Sidebar (N) > CSL Cam",
    "category": "Camera",
}

# plain notes (what I can do now):
# - Build Camera Pack: creates collection, focus empty, and practical shot cameras
# - Quick focal buttons to set a focal value in the UI
# - Letterbox toggle using render border

import bpy
from mathutils import Vector
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import EnumProperty, FloatProperty, IntProperty, BoolProperty, PointerProperty

ASPECT_PRESETS = {
    "SCOPE_239": (2.39, "2.39:1 Scope"),
    "FEATURE_185": (1.85, "1.85:1 Feature"),
    "TV_178": (16/9, "1.78:1 (16:9)"),
}
ASPECT_ENUM = [(k, v[1], "") for k, v in ASPECT_PRESETS.items()]

SENSOR_PRESETS = {
    "FF_36x24": (36.0, 24.0, "Full Frame 36x24"),
}
SENSOR_ENUM = [(k, v[2], "") for k, v in SENSOR_PRESETS.items()]

LENS_KIT = [24, 35, 50, 85]

SHOT_PRESETS = [
    ("Master", 24, 4.0, "FF_36x24", "SCOPE_239",  (0.0, -12.0, 3.0)),
    ("Medium", 50, 4.0, "FF_36x24", "FEATURE_185",(0.0,  -6.0, 1.6)),
    ("CloseUp",85, 2.8, "FF_36x24", "FEATURE_185",(0.0,  -3.0, 1.6)),
]

def aspect_token(key): return f"{ASPECT_PRESETS.get(key,(16/9,''))[0]:.2f}"

def ensure_collection(name="CSL_Cameras"):
    scn = bpy.context.scene
    if not scn: return None
    coll = bpy.data.collections.get(name)
    if not coll:
        coll = bpy.data.collections.new(name)
        scn.collection.children.link(coll)
    return coll

def kill_collection(name="CSL_Cameras"):
    scn = bpy.context.scene
    coll = bpy.data.collections.get(name)
    if not scn or not coll: return
    try:
        if coll in scn.collection.children:
            scn.collection.children.unlink(coll)
        for obj in list(coll.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(coll)
    except Exception:
        pass

def new_empty(name):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = 'PLAIN_AXES'
    return obj

def track_to(obj, target):
    c = obj.constraints.new('TRACK_TO')
    c.target = target
    c.track_axis = 'TRACK_NEGATIVE_Z'
    c.up_axis = 'UP_Y'
    return c

def set_letterbox(scene, enable=True, matte_height_frac=0.15):
    if not scene: return
    if enable:
        scene.render.use_border = True
        mh = max(0.0, min(0.49, matte_height_frac))
        scene.render.border_min_y = mh
        scene.render.border_max_y = 1.0 - mh
        scene.render.border_min_x = 0.0
        scene.render.border_max_x = 1.0
    else:
        scene.render.use_border = False

class CSLProps(PropertyGroup):
    res_y: IntProperty(name="Res Height", default=1080, min=256, max=16384)
    aspect: EnumProperty(name="Aspect", items=ASPECT_ENUM, default="SCOPE_239")
    sensor: EnumProperty(name="Sensor", items=SENSOR_ENUM, default="FF_36x24")
    focal:  FloatProperty(name="Focal (mm)", default=40.0, min=1.0, max=300.0)
    fstop:  FloatProperty(name="f/", default=2.8, min=0.7, max=32.0)
    letterbox: BoolProperty(name="Letterbox Preview", default=False)

class CSL_OT_build_pack(Operator):
    bl_idname = "csl_cam.build_pack"
    bl_label = "Build Camera Pack"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scn = bpy.context.scene
        if not scn:
            self.report({'WARNING'}, "No active scene")
            return {'CANCELLED'}

        P = getattr(scn, "csl_cam", None)
        if P:
            try:
                a = ASPECT_PRESETS.get(P.aspect, (16/9, ""))[0]
                scn.render.resolution_y = int(P.res_y)
                scn.render.resolution_x = int(round(P.res_y * a))
            except Exception:
                pass

        kill_collection("CSL_Cameras")
        coll = ensure_collection("CSL_Cameras")
        if not coll:
            self.report({'WARNING'}, "Could not create collection")
            return {'CANCELLED'}

        focus = new_empty("CSL_Focus")
        focus.location = Vector((0.0, 0.0, 1.6))
        coll.objects.link(focus)

        created = []
        for nice, focal, fnum, sensor_key, aspect_key, loc in SHOT_PRESETS:
            cam_data = bpy.data.cameras.new(f"CSL_{nice}_Data")
            cam_obj = bpy.data.objects.new("Camera", cam_data)
            coll.objects.link(cam_obj)

            sw, sh, _ = SENSOR_PRESETS.get(sensor_key, (36.0, 24.0, ""))
            cam_data.sensor_width  = float(sw)
            cam_data.sensor_height = float(sh)
            cam_data.lens = float(focal)
            cam_data.dof.use_dof = True
            cam_data.dof.focus_object = focus
            cam_data.dof.aperture_fstop = float(fnum)

            token = aspect_token(aspect_key)
            cam_obj.name = f"CSL_{nice}_{token}_{int(round(focal))}mm"
            cam_obj.location = Vector(loc)
            track_to(cam_obj, focus)
            created.append(cam_obj)

        if P and P.letterbox:
            set_letterbox(scn, True)
        else:
            set_letterbox(scn, False)

        self.report({'INFO'}, f"Camera pack built ({len(created)} cameras)")
        return {'FINISHED'}

class CSL_OT_quick_focal(Operator):
    bl_idname = "csl_cam.quick_focal"
    bl_label = "Quick Focal"
    bl_options = {"INTERNAL"}
    value: IntProperty(default=35)
    def execute(self, context):
        scn = bpy.context.scene
        P = getattr(scn, "csl_cam", None)
        if P:
            P.focal = float(self.value)
        return {'FINISHED'}

class CSL_OT_letterbox_toggle(Operator):
    bl_idname = "csl_cam.letterbox_toggle"
    bl_label = "Toggle Letterbox"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        scn = bpy.context.scene
        P = getattr(scn, "csl_cam", None)
        if not scn or not P:
            return {'CANCELLED'}
        P.letterbox = not P.letterbox
        set_letterbox(scn, bool(P.letterbox))
        self.report({'INFO'}, f"Letterbox {'ON' if P.letterbox else 'OFF'}")
        return {'FINISHED'}

class CSL_PT_panel(Panel):
    bl_label = "Cinematic Camera Pack"
    bl_idname = "CSL_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'CSL Cam'

    def draw(self, context):
        scn = bpy.context.scene
        layout = self.layout
        if not hasattr(bpy.types.Scene, "csl_cam"):
            layout.label(text="(Re-enable add-on if panel broken)")
            return
        P = getattr(scn, "csl_cam", None)
        if P is None:
            layout.label(text="(Props missing)")
            return

        box = layout.box(); box.label(text="Build")
        box.prop(P, "aspect"); box.prop(P, "res_y")
        box.operator("csl_cam.build_pack", icon='OUTLINER_OB_CAMERA')

        box = layout.box(); box.label(text="Apply Settings")
        row = box.row(align=True); row.prop(P, "sensor"); row.prop(P, "focal")
        box.prop(P, "fstop")

        row = box.row(align=True)
        for f in LENS_KIT:
            op = row.operator("csl_cam.quick_focal", text=f"{f}mm")
            op.value = f

        box = layout.box(); box.label(text="Mask")
        row = box.row(align=True)
        row.prop(P, "letterbox", text="Preview Letterbox")
        row.operator("csl_cam.letterbox_toggle", text="Toggle")

classes = (
    CSLProps,
    CSL_OT_build_pack,
    CSL_OT_quick_focal,
    CSL_OT_letterbox_toggle,
    CSL_PT_panel,
)

def register():
    for c in classes: bpy.utils.register_class(c)
    if not hasattr(bpy.types.Scene, "csl_cam"):
        bpy.types.Scene.csl_cam = PointerProperty(type=CSLProps)

def unregister():
    for c in reversed(classes): bpy.utils.unregister_class(c)
    if hasattr(bpy.types.Scene, "csl_cam"):
        del bpy.types.Scene.csl_cam

if __name__ == "__main__":
    register()


