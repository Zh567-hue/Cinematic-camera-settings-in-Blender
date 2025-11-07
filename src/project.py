#!/usr/bin/env python3
# Keeps simple camera presets in JSON.
# You can list/add/remove presets and export the Blender add-on file.

import json, os, sys, shutil
from dataclasses import dataclass, asdict
import click

PRESETS_PATH = os.path.join(os.path.dirname(__file__), "presets.json")
ADDON_TEMPLATE = os.path.join(os.path.dirname(__file__), "blender_hct_addon.py")

@dataclass
class Preset:
    name: str
    aspect: float
    focal_mm: int
    sensor_mm: str
    shutter_deg: int
    fstop: float = 2.8

def _load_all():
    if not os.path.exists(PRESETS_PATH):
        return []
    with open(PRESETS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Preset(**p) for p in data]

def _save_all(presets):
    with open(PRESETS_PATH, "w", encoding="utf-8") as f:
        json.dump([asdict(p) for p in presets], f, indent=2)

@click.group()
def cli():
    """Preset Planner"""

@cli.command()
def list():
    presets = _load_all()
    if not presets:
        click.echo("No presets yet. Use `add` to create one.")
        return
    for p in presets:
        click.echo(f"- {p.name}: aspect={p.aspect}, focal={p.focal_mm}mm, sensor={p.sensor_mm}, shutter={p.shutter_deg}°, f/{p.fstop}")

@cli.command()
@click.option("--name", required=True)
@click.option("--aspect", type=float, required=True)
@click.option("--focal", "focal_mm", type=int, required=True)
@click.option("--sensor", "sensor_mm", required=True, help="WxH mm, e.g., 36x24")
@click.option("--shutter", "shutter_deg", type=int, default=180, show_default=True)
@click.option("--fstop", type=float, default=2.8, show_default=True)
def add(name, aspect, focal_mm, sensor_mm, shutter_deg, fstop):
    if "x" not in sensor_mm:
        click.echo("Sensor must be WxH mm, e.g., 36x24", err=True); sys.exit(1)
    presets = _load_all()
    if any(p.name == name for p in presets):
        click.echo("Preset name already exists", err=True); sys.exit(1)
    presets.append(Preset(name, aspect, focal_mm, sensor_mm, shutter_deg, fstop))
    _save_all(presets)
    click.echo(f"Added preset: {name}")

@cli.command()
@click.option("--name", required=True)
def remove(name):
    presets = _load_all()
    new_list = [p for p in presets if p.name != name]
    if len(new_list) == len(presets):
        click.echo("No such preset."); return
    _save_all(new_list)
    click.echo(f"Removed preset: {name}")

@cli.command("export-addon")
@click.option("--out", "out_path", default="blender_hct_addon.py", show_default=True)
def export_addon(out_path):
    if not os.path.exists(ADDON_TEMPLATE):
        click.echo("Add-on template not found next to project.py", err=True); sys.exit(1)
    shutil.copyfile(ADDON_TEMPLATE, out_path)
    click.echo(f"Exported add-on to: {out_path}")

def main():
    cli()

if __name__ == "__main__":
    main()
