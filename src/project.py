#!/usr/bin/env python3
# my notes:
# - define a simple Preset data container (name, aspect, focal, etc.).
# - keep hello so I can still run a quick check.

import os
from dataclasses import dataclass, asdict
from typing import Dict
import click

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

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

@click.group(help="CSL — Final Project CLI")
def cli():
    pass

@cli.command("hello")
def cmd_hello():
    print("Hello from CSL CLI (model added)!")

def main():
    cli()

if __name__ == "__main__":
    main()



