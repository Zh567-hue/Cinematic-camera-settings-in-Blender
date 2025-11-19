#!/usr/bin/env python3
# Pseudocode:
# - Make a tiny CLI group with a hello command.
# - We'll expand it step by step.

import click

@click.group(help="CSL — Final Project CLI")
def cli():
    pass

@cli.command("hello")
def cmd_hello():
    print("Hello from CSL CLI!")

def main():
    cli()

if __name__ == "__main__":
    main()

