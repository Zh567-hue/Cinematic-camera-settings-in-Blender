#!/usr/bin/env python3
"""
my notes:
- this CLI manages camera presets (JSON), exports my Blender add-on file to repo root,
  and can generate a simple thumbnail PNG (Pillow).
- keep commands small.
Run examples I can paste into terminal:
  python src/project.py list
  python src/project.py add --name "Scope_239_40mm" --aspect 2.39 --focal 40 --sensor 36x24 --shutter 180 --fstop 2.8
  python src/project.py remove --name "Scope_239_40mm"
  python src/project.py export-addon --from src/csl_cinematography_camera_pack.py --out csl_cinematography_camera_pack.py
  python src/project.py make-thumb --out csl_thumb.png --text "CSL Cam Pack"
"""

import os, sys, json
from dataclasses import dataclass, asdict
from typing import List, Dict
import click

# my notes:
# - try Pillow; if missing, just warn when thumbnail is used.
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# my notes:
# - compute paths once; ensure data exists; define JSON path.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)
PRESETS_PATH = os.path.join(DATA_DIR, "camera_presets.json")

# my notes:
# - default source of add-on is under src/, output copy goes to repo root (easy Blender install).
DEFAULT_ADDON_SOURCE = os.path.join(ROOT, "src", "csl_cinematography_camera_pack.py")
DEFAULT_ADDON_OUT    = os.path.join(ROOT, "csl_cinematography_camera_pack.py")

# my notes:
# - camera preset structure.
@dataclass
class Preset:
    name: str
    aspect: float
    focal_mm: int
    sensor_mm: str
    shutter_deg: int = 180
    fstop: float = 2.8
    def to_dict(self) -> Dict:
        return asdict(self)

# my notes:
# - load all presets from JSON file; be defensive if file is missing or bad.
def load_all() -> List[Preset]:
    if not os.path.exists(PRESETS_PATH):
        return []
    try:
        with open(PRESETS_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        out: List[Preset] = []
        for row in raw:
            try:
                out.append(Preset(**row))
            except TypeError:
                continue
        return out
    except Exception as e:
        print(f("[WARN] Could not read {PRESETS_PATH}: {e}"))
        return []

# my notes:
# - save all presets to JSON file (pretty formatted).
def save_all(presets: List[Preset]) -> None:
    try:
        with open(PRESETS_PATH, "w", encoding="utf-8") as f:
            json.dump([p.to_dict() for p in presets], f, indent=2)
        print(f"[OK] Saved {len(presets)} presets → {PRESETS_PATH}")
    except Exception as e:
        print(f"[ERROR] Could not write {PRESETS_PATH}: {e}")

# my notes:
# - simple title PNG with letterbox bars; works even with default font.
def make_thumbnail(path: str, text: str = "CSL", w: int = 640, h: int = 360) -> bool:
    if not PIL_AVAILABLE:
        print("[WARN] Pillow not installed. Run: pip install -r requirements.txt")
        return False
    try:
        img = Image.new("RGB", (w, h), (20, 20, 24))
        draw = ImageDraw.Draw(img)
        bar = int(h * 0.15)
        draw.rectangle([(0, 0), (w, bar)], fill=(0, 0, 0))
        draw.rectangle([(0, h - bar), (w, h)], fill=(0, 0, 0))
        try:
            font = ImageFont.truetype("arial.ttf", size=36)
        except Exception:
            font = ImageFont.load_default()
        tw, th = draw.textbbox((0, 0), text, font=font)[2:]
        draw.text(((w - tw) / 2, (h - th) / 2), text, fill=(240, 240, 240), font=font)
        img.save(path, format="PNG")
        print(f"[OK] Wrote thumbnail → {path}")
        return True
    except Exception as e:
        print(f"[ERROR] Could not create thumbnail: {e}")
        return False

@click.group(help="CSL — Final Project CLI (presets + export + thumbnail)")
def cli():
    pass

# my notes:
# - print all presets or suggest 'add' if none exist.
@cli.command("list")
def cmd_list():
    presets = load_all()
    if not presets:
        print("No presets yet. Use `add` to create one.")
        return
    for p in presets:
        print(f"- {p.name}: aspect={p.aspect}, focal={p.focal_mm}mm, sensor={p.sensor_mm}, "
              f"shutter={p.shutter_deg}°, f/{p.fstop}")

# my notes:
# - add a preset with basic validation (sensor format), guard duplicate names.
@cli.command("add")
@click.option("--name", required=True)
@click.option("--aspect", type=float, required=True)
@click.option("--focal", "focal_mm", type=int, required=True)
@click.option("--sensor", "sensor_mm", required=True, help="WxH mm (e.g. 36x24)")
@click.option("--shutter", "shutter_deg", type=int, default=180, show_default=True)
@click.option("--fstop", type=float, default=2.8, show_default=True)
def cmd_add(name, aspect, focal_mm, sensor_mm, shutter_deg, fstop):
    if "x" not in sensor_mm:
        print("Sensor must be WxH mm (example: 36x24)")
        sys.exit(1)
    presets = load_all()
    if any(p.name == name for p in presets):
        print("Preset name already exists.")
        sys.exit(1)
    presets.append(Preset(name, aspect, focal_mm, sensor_mm, shutter_deg, fstop))
    save_all(presets)
    print(f"[OK] Added preset: {name}")

# my notes:
# - remove by name; if not found, just say so.
@cli.command("remove")
@click.option("--name", required=True)
def cmd_remove(name):
    presets = load_all()
    new_list = [p for p in presets if p.name != name]
    if len(new_list) == len(presets):
        print("No such preset.")
        return
    save_all(new_list)
    print(f"[OK] Removed preset: {name}")

# my notes:
# - copy my add-on from src/ to repo root so Blender can install it easily.
@cli.command("export-addon")
@click.option("--from", "src_path", default=DEFAULT_ADDON_SOURCE, show_default=True)
@click.option("--out", "out_path", default=DEFAULT_ADDON_OUT, show_default=True)
def cmd_export_addon(src_path, out_path):
    try:
        if not os.path.exists(src_path):
            print(f"[WARN] Source add-on not found at: {src_path}")
            sys.exit(1)
        with open(src_path, "r", encoding="utf-8") as f_in:
            code = f_in.read()
        with open(out_path, "w", encoding="utf-8") as f_out:
            f_out.write(code)
        print(f"[OK] Exported add-on → {out_path}")
    except Exception as e:
        print(f"[ERROR] Could not export add-on: {e}")
        sys.exit(1)

# my notes:
# - optional thumbnail (tests Pillow + basic imaging).
@cli.command("make-thumb")
@click.option("--out", "out_path", default=os.path.join(ROOT, "csl_thumb.png"), show_default=True)
@click.option("--text", default="CSL Cam Pack", show_default=True)
def cmd_make_thumb(out_path, text):
    ok = make_thumbnail(out_path, text=text)
    if not ok:
        sys.exit(1)

def main():
    cli()

if __name__ == "__main__":
    main()



