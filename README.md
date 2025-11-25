# Cinematic Studio‑Level Different Camera Settings (CSL) - Blender Add‑on

Hi, I’m Zhina. This project is my final for Programming for Digital Artists. I built a small tool I actually need for **Keep Going**: a Blender add‑on that drops in a clean camera pack and lets me switch professional framing, lenses, and scene output quickly without digging through menus.

---

## Demo
Demo Video: https://youtu.be/R5Xak1ZJKv4

## GitHub Repository
GitHub Repo: https://github.com/Zh567-hue/Cinematic-camera-settings-in-Blender

---

## What this does 
Create ready‑to‑shoot cameras (Master/Medium/CU/OTS/POV/etc.), set sensor/aspect/FPS/DOF fast, and preview letterbox - all from the N‑panel.

---

## Why I made it
During look‑dev and blocking I keep changing lenses, aspect ratios, and output settings. Doing that manually slows me down and breaks flow. This add‑on keeps everything in one place and matches common cinematography patterns I use in my short film.

---

## Features
- **One‑click Camera Pack**
   Builds a `CSL_Cameras` collection with: Master, Medium, Close‑Up, Extreme CU, OTS (L/R), POV, Insert, Tracking, Crane.
   Adds a **Focus Empty** that all cameras track to (also used for DOF).
- **Fast Scene Output**
   Aspect presets (2.39, 1.85, 16:9, etc.), resolution height → auto width, optional FPS set.
   Filmic view transform + exposure slider.
- **Lens & DOF Controls**
   Sensor presets (Full‑Frame, S35, etc.), focal length, f/stop.
   Quick focal buttons (18–135mm).
- **Apply Anywhere**
   Apply to **Active** camera or **All Pack** cameras in a click.
- **Letterbox Preview**
   Toggle a non‑destructive matte using render border for quick framing checks.
- **N‑Panel UI**
   `View3D ▸ Sidebar (N) ▸ CSL Cam`

---

## File layout
```
repo/
├─ README.md
├─ requirements.txt          # CLI dependencies
├─ csl_cinematography_camera_pack.py   # exported add‑on (install this in Blender)
└─ src/
   ├─ project.py                          # CLI: presets JSON, export add‑on, thumbnail
   └─ csl_cinematography_camera_pack.py   # source add‑on you edit
```

---

## How to use the CLI (project.py)
1) Create and activate a venv, then install deps:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
```

2) Manage presets (optional) and export the add‑on to repo root:
```bash
python src/project.py add --name "Scope_239_40mm" --aspect 2.39 --focal 40 --sensor 36x24 --shutter 180 --fstop 2.8
python src/project.py list
python src/project.py export-addon --from src/csl_cinematography_camera_pack.py --out csl_cinematography_camera_pack.py
```

3) (Optional) Make a tiny thumbnail PNG:
```bash
python src/project.py make-thumb --out csl_thumb.png --text "CSL Cam Pack"
```

> Presets are stored in `data/camera_presets.json`. The CLI is beginner‑friendly and prints clear messages.

---

## Install in Blender
1) Open **Blender 4.4.3** (or later 4.4.x).
2) **Edit ▸ Preferences ▸ Add‑ons ▸ Install…**
3) Select the file **`csl_cinematography_camera_pack.py`** from your repo root.
4) Enable it. You’ll see **CSL Cam** in the **N‑panel**.

---

## Quickstart (in Blender)
1) Open the **CSL Cam** tab.
2) Pick **Aspect** and **Res Height**.
3) Click **Build Camera Pack** → a `CSL_Cameras` collection appears.
4) Select any camera (e.g., `CSL_Master_2.39_24mm`) → press **Ctrl+Num0** to set as active view.
5) Tweak **Sensor / Focal / f/**, then click **Apply → Active** (or **Apply → All Pack**).
6) Toggle **Letterbox Preview** if you want matte bars.
7) Move **CSL_Focus** empty to set where cameras look and focus.

Expected checks:
- New collection with the named cameras.
- Scene resolution matches your Aspect & Res Height.
- Cameras track the focus empty; DOF uses it automatically.
- No red error toasts - the add‑on guards scene writes safely.

---

## Requirements
```
click
pillow
```
(The add‑on itself uses Blender’s built‑in `bpy` and needs no pip install.)

---

## Troubleshooting
- **Add‑on not in the N‑panel?** Ensure it’s enabled in Preferences and you’re in the 3D Viewport.
- **Export can’t find the source file?** Run the CLI from the repo root and verify `src/csl_cinematography_camera_pack.py` exists.
- **Black bars don’t render?** They’re a preview matte (render border), not baked. Keep them for framing only.

---

## Credits
Author: **Zhina Lotfi**  
Course: **ANGM 2335 – Programming for Digital Artists**

Thanks to my Keep Going pipeline for pushing me to make a practical camera tool.
