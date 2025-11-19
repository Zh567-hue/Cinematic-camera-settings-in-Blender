#!/usr/bin/env python3
# my notes:
# - set ROOT path to repo.
# - make sure I have a data folder for JSON files.

import os
import click

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

@click.group(help="CSL — Final Project CLI")
def cli():
    pass

@cli.command("hello")
def cmd_hello():
    print("Hello from CSL CLI (paths ready)!")

def main():
    cli()

if __name__ == "__main__":
    main()


