# Cinematic Studio-Level Different Camera Settings

## Repository
https://github.com/Zh567-hue/Cinematic-camera-settings-in-Blender/new/main

## Description
A Python-driven toolset for digital arts students and filmmakers. It includes a Blender add-on that builds a clean camera rig with cinematic aspect presets, framing/letterbox guides, depth-of-field helper, and motion operators (dolly, crane, orbit). A simple Python CLI manages JSON shot presets and exports the add-on.

## Features
 **Cinematic Presets**
  - One-click aspect/focal/f-stop presets (2.39, 1.85, 16:9).
 **Camera Rig Generator**
  - Auto-creates a tidy hierarchy: root → dolly → crane → pan/tilt → camera.
 **Framing Guides**
  - Quick letterbox matte switch for scope preview.
 **Motion Operators**
  - Dolly, crane, and orbit by exact meters/degrees.
 **DOF Helper**
  - Sets camera focus to the active object.
 **CLI Planner**
  - `project.py` lists/adds/removes presets and exports the Blender add-on file.

## Challenges
- Review Blender `bpy` registration patterns (operators, panels, props).
- Keep DOF and aspect math simple and predictable.
- Package instructions so non-technical users can adopt quickly.

## Outcomes
Ideal Outcome:
- Polished Blender add-on GUI with presets and motion. A short demo scene showing perspective swaps and DOF.

Minimal Viable Outcome:
- Working add-on that creates the rig, applies 2–3 presets, toggles the letterbox, focuses to active object, and moves the rig. CLI can add/list/export.

## Milestones
- **Week 1**
  1. Create repo and proposal; scaffold code files.
  2. Implement CLI preset manager + JSON I/O.

- **Week 2**
  1. Build Blender rig and register UI panel/operators.
  2. Add presets, DOF helper, letterbox toggle.

- **Week 3 (Final)**
  1. Add motion operators (dolly, crane, orbit) and polish UI.
  2. Record <3-min demo; complete README.
