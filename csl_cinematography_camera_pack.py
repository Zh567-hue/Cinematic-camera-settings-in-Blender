# what this add-on does (plain steps):
# 1) give me a panel in the N-Panel called "CSL Cam".
# 2) when I press "Build Camera Pack", make a new collection, drop a Focus empty,
#    and auto-create practical film shots (Master, Medium, CU, Extreme CU, OTS L/R, POV, Insert, Tracking, Crane).
# 3) name cameras with readable tokens (aspect + focal) and aim them at the Focus empty.
# 4) expose simple settings (aspect, res height, sensor, focal, f-stop, exposure, fps).
# 5) let me apply settings to the active camera or the whole pack in one click.
# 6) provide quick focal buttons (18–135 mm) and a preview letterbox toggle.
# 7) register/unregister cleanly and store UI properties on the Scene.

bl_info = {
    "name": "CSL Cinematography Camera Pack",
    "author": "Zhina Lotfi",
    "version": (1, 0, 0),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar (N) > CSL Cam",
    "category": "Camera",
}

import bpy
from math import radians
from mathutils import Vector
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import (
    EnumProperty, FloatProperty, IntProperty, BoolProperty,
    PointerProperty
)

# ---------- constants & helpers (no context here) ----------

SENSOR_PRESETS = {
    "FF_36x24": (36.0, 24.0, "Full Frame 36x24"),
    "S35_24_9x18_7": (24.89, 18.66, "Super 35 24.9x18.7"),
    "APS_C_23_5x15_6": (23.5, 15.6, "APS-C 23.5x15.6"),
    "VV_37_7x24_9": (37.7, 24.9, "VistaVision 37.7x24.9"),
    "S65_52_5x23_0": (52.48, 23.01, "S65 52.5x23.0"),
    "IMAX_70x51": (70.0, 51.0, "IMAX 70x51"),
}

ASPECT_PRESETS = {
    "SCOPE_239": (2.39, "2.39:1 Scope"),
    "UHD_200": (2.00, "2.00:1"),
    "FEATURE_185": (1.85, "1.85:1 Feature"),
    "TV_178": (16/9, "1.78:1 (16:9)"),
    "EURO_166": (1.66, "1.66:1"),
    "ACADEMY_133": (4/3, "1.33:1 Academy"),
}

LENS_KIT = [18, 24, 28, 32, 35, 40, 50, 65, 75, 85, 100, 135]

SHOT_PRESETS = [
    ("Master",    24, 4.0, "FF_36x24", "SCOPE_239",  (0.0, -12.0, 3.0)),
    ("Medium",    50, 4.0, "FF_36x24", "FEATURE_185",(0.0,  -6.0, 1.6)),
    ("CloseUp",   85, 2.8, "FF_36x24", "FEATURE_185",(0.0,  -3.0, 1.6)),
    ("ExtremeCU",135, 2.8, "FF_36x24", "FEATURE_185",(0.0,  -1.5, 1.6)),
    ("OTS_Left",  50, 4.0, "FF_36x24", "TV_178",     (-1.2, -3.0, 1.7)),
    ("OTS_Right", 50, 4.0, "FF_36x24", "TV_178",     ( 1.2, -3.0, 1.7)),
    ("POV",       35, 4.0, "FF_36x24", "FEATURE_185",(0.0,  -2.2, 1.7)),
    ("Insert",    65, 4.0, "FF_36x24", "TV_178",     (0.0,  -1.0, 0.9)),
    ("Tracking",  35, 4.0, "FF_36x24", "SCOPE_239",  (4.0,  -7.0, 1.6)),
    ("Crane",     24, 5.6, "FF_36x24", "SCOPE_239",  (0.0,  -9.0, 6.0)),
]

def aspect_token(key):
    a = ASPECT_PRESETS.get(key, (16/9, ""))[0]
    return f"{a:.2f}"

def ensure_collection(name="CSL_Cameras"):
    scn = bpy.context.scene
    if not scn:
        return None
    coll = bpy.data.collections.get(name)
    if not coll:
        coll = bpy.data.collections.new(name)
        scn.collection.children.link(coll)
    return coll

def kill_collection(name="CSL_Cameras"):
    scn = bpy.context.scene
    coll = bpy.data.collections.get(name)
    if not scn or not coll:
        return
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
    if not scene:
        return
    if enable:
        scene.render.use_border = True
        mh = max(0.0, min(0.49, matte_height_frac))
        scene.render.border_min_y = mh
        scene.render.border_max_y = 1.0 - mh
        scene.render.border_min_x = 0.0
        scene.render.border_max_x = 1.0
    else:
        scene.render.use_border = False

def all_pack_cameras():
    cams = []
    coll = bpy.data.collections.get("CSL_Cameras")
    if not coll:
        return cams
    for obj in coll.objects:
        if obj.type == 'CAMERA':
            cams.append(obj)
    return cams

# ---------- properties ----------

SENSOR_ENUM = [(k, v[2], "") for k, v in SENSOR_PRESETS.items()]
ASPECT_ENUM = [(k, v[1], "") for k, v in ASPECT_PRESETS.items()]

class CSLProps(PropertyGroup):
    # global preview output
    res_y: IntProperty(name="Res Height", default=1080, min=256, max=16384)
    aspect: EnumProperty(name="Aspect", items=ASPECT_ENUM, default="SCOPE_239")
    # per-camera apply
    sensor: EnumProperty(name="Sensor", items=SENSOR_ENUM, default="FF_36x24")
    focal:  FloatProperty(name="Focal (mm)", default=40.0, min=1.0, max=300.0)
    fstop:  FloatProperty(name="f/", default=2.8, min=0.7, max=32.0)
    exposure: FloatProperty(name="Exposure EV", default=0.0, min=-12.0, max=12.0)
    fps_set: BoolProperty(name="Set FPS", default=False)
    fps: IntProperty(name="FPS", default=24, min=1, max=240)
    # mask
    letterbox: BoolProperty(name="Letterbox Preview", default=False)

# ---------- operators ----------

class CSL_OT_build_pack(Operator):
    bl_idname = "csl_cam.build_pack"
    bl_label = "Build Camera Pack"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scn = bpy.context.scene
        if not scn:
            self.report({'WARNING'}, "No active scene")
            return {'CANCELLED'}

        # set scene output aspect
        P = getattr(scn, "csl_cam", None)
        if P:
            try:
                a = ASPECT_PRESETS.get(P.aspect, (16/9, ""))[0]
                scn.render.resolution_y = int(P.res_y)
                scn.render.resolution_x = int(round(P.res_y * a))
                if hasattr(scn, "view_settings"):
                    scn.view_settings.view_transform = 'Filmic'
                    scn.view_settings.exposure = float(P.exposure)
                if P.fps_set:
                    scn.render.fps = int(P.fps)
            except Exception:
                pass

        # clear old
        kill_collection("CSL_Cameras")
        coll = ensure_collection("CSL_Cameras")
        if not coll:
            self.report({'WARNING'}, "Could not create collection")
            return {'CANCELLED'}

        # focus empty
        focus = new_empty("CSL_Focus")
        focus.location = Vector((0.0, 0.0, 1.6))
        coll.objects.link(focus)

        # build cameras
        created = []
        for nice, focal, fnum, sensor_key, aspect_key, loc in SHOT_PRESETS:
            cam_data = bpy.data.cameras.new(f"CSL_{nice}_Data")
            cam_obj = bpy.data.objects.new("Camera", cam_data)
            coll.objects.link(cam_obj)

            # core
            cam_data.type = 'PERSP'
            # sensor
            sw, sh, _ = SENSOR_PRESETS.get(sensor_key, (36.0, 24.0, ""))
            cam_data.sensor_width  = float(sw)
            cam_data.sensor_height = float(sh)
            # lens + dof
            cam_data.lens = float(focal)
            cam_data.dof.use_dof = True
            cam_data.dof.focus_object = focus
            cam_data.dof.aperture_fstop = float(fnum)

            # name
            token = aspect_token(aspect_key)
            cam_obj.name = f"CSL_{nice}_{token}_{int(round(focal))}mm"

            # place + look-at
            cam_obj.location = Vector(loc)
            track_to(cam_obj, focus)

            created.append(cam_obj)

        # set master active
        for obj in created:
            if obj.name.startswith("CSL_Master_"):
                scn.camera = obj
                break

        # letterbox preview
        if P and P.letterbox:
            set_letterbox(scn, True)
        else:
            set_letterbox(scn, False)

        self.report({'INFO'}, f"Camera pack built ({len(created)} cameras)")
        return {'FINISHED'}


class CSL_OT_apply_active(Operator):
    bl_idname = "csl_cam.apply_active"
    bl_label = "Apply to Active Camera"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scn = bpy.context.scene
        cam = scn.camera if scn else None
        if not cam or cam.type != 'CAMERA':
            self.report({'WARNING'}, "Active scene camera not set; select a pack camera and press Ctrl+Num0")
            return {'CANCELLED'}
        P = getattr(scn, "csl_cam", None)
        if not P:
            return {'CANCELLED'}

        try:
            sw, sh, _ = SENSOR_PRESETS.get(P.sensor, (36.0, 24.0, ""))
            cam.data.sensor_width  = float(sw)
            cam.data.sensor_height = float(sh)
            cam.data.lens = float(P.focal)
            cam.data.dof.use_dof = True
            cam.data.dof.aperture_fstop = float(P.fstop)
        except Exception:
            pass

        try:
            a = ASPECT_PRESETS.get(P.aspect, (16/9, ""))[0]
            scn.render.resolution_y = int(P.res_y)
            scn.render.resolution_x = int(round(P.res_y * a))
            if hasattr(scn, "view_settings"):
                scn.view_settings.view_transform = 'Filmic'
                scn.view_settings.exposure = float(P.exposure)
            if P.fps_set:
                scn.render.fps = int(P.fps)
            set_letterbox(scn, bool(P.letterbox))
        except Exception:
            pass

        self.report({'INFO'}, f"Applied to {cam.name}")
        return {'FINISHED'}


class CSL_OT_apply_all(Operator):
    bl_idname = "csl_cam.apply_all"
    bl_label = "Apply to All Pack Cameras"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scn = bpy.context.scene
        if not scn:
            return {'CANCELLED'}
        P = getattr(scn, "csl_cam", None)
        cams = all_pack_cameras()
        if not cams:
            self.report({'WARNING'}, "No pack cameras found (Build Camera Pack first)")
            return {'CANCELLED'}

        for cam in cams:
            try:
                sw, sh, _ = SENSOR_PRESETS.get(P.sensor, (36.0, 24.0, ""))
                cam.data.sensor_width  = float(sw)
                cam.data.sensor_height = float(sh)
                cam.data.lens = float(P.focal)
                cam.data.dof.use_dof = True
                cam.data.dof.aperture_fstop = float(P.fstop)
            except Exception:
                pass

        try:
            a = ASPECT_PRESETS.get(P.aspect, (16/9, ""))[0]
            scn.render.resolution_y = int(P.res_y)
            scn.render.resolution_x = int(round(P.res_y * a))
            if hasattr(scn, "view_settings"):
                scn.view_settings.view_transform = 'Filmic'
                scn.view_settings.exposure = float(P.exposure)
            if P.fps_set:
                scn.render.fps = int(P.fps)
            set_letterbox(scn, bool(P.letterbox))
        except Exception:
            pass

        self.report({'INFO'}, f"Applied to {len(cams)} cameras")
        return {'FINISHED'}


class CSL_OT_set_active_from_selected(Operator):
    bl_idname = "csl_cam.set_active_from_selected"
    bl_label = "Set Selected as Active Camera"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scn = bpy.context.scene
        obj = context.active_object if context else None
        if not scn or not obj or obj.type != 'CAMERA':
            self.report({'WARNING'}, "Select a camera object first")
            return {'CANCELLED'}
        try:
            scn.camera = obj
        except Exception:
            pass
        self.report({'INFO'}, f"Active camera → {obj.name}")
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

# ---------- panel ----------

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
            layout.label(text="(Props missing; save & reload file)")
            return

        box = layout.box()
        box.label(text="Build")
        box.prop(P, "aspect")
        box.prop(P, "res_y")
        box.operator("csl_cam.build_pack", icon='OUTLINER_OB_CAMERA')
        box.operator("csl_cam.set_active_from_selected", icon='RESTRICT_VIEW_OFF')

        box = layout.box()
        box.label(text="Apply Settings")
        row = box.row(align=True)
        row.prop(P, "sensor", text="Sensor")
        row.prop(P, "focal")
        row = box.row(align=True)
        row.prop(P, "fstop")
        row.prop(P, "exposure")
        row = box.row(align=True)
        row.prop(P, "fps_set")
        if P.fps_set:
            box.prop(P, "fps")

        row = box.row(align=True)
        for f in LENS_KIT:
            op = row.operator("csl_cam.quick_focal", text=f"{f}mm")
            op.value = f

        row = box.row(align=True)
        row.operator("csl_cam.apply_active", text="Apply → Active")
        row.operator("csl_cam.apply_all", text="Apply → All Pack")

        box = layout.box()
        box.label(text="Mask")
        row = box.row(align=True)
        row.prop(P, "letterbox", text="Preview Letterbox")
        row.operator("csl_cam.letterbox_toggle", text="Toggle")

# ---------- register ----------

classes = (
    CSLProps,
    CSL_OT_build_pack,
    CSL_OT_apply_active,
    CSL_OT_apply_all,
    CSL_OT_set_active_from_selected,
    CSL_OT_quick_focal,
    CSL_OT_letterbox_toggle,
    CSL_PT_panel,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    # Only define a pointer property on Scene (no context access)
    if not hasattr(bpy.types.Scene, "csl_cam"):
        bpy.types.Scene.csl_cam = PointerProperty(type=CSLProps)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    if hasattr(bpy.types.Scene, "csl_cam"):
        del bpy.types.Scene.csl_cam

if __name__ == "__main__":
    register()
