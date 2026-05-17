#!/data/data/com.termux/files/usr/bin/python3

import subprocess
import sys
from pathlib import Path

import typer
import yaml

app = typer.Typer(help="pd-compose: proot-distro compose tool")


def load_config(file: Path) -> dict:
    if not file.exists():
        typer.echo(f"error: {file} not found", err=True)
        raise typer.Exit(1)
    with open(file) as f:
        return yaml.safe_load(f) or {}


@app.command()
def up(
    file: Path = typer.Option("pd-compose.yaml", "--file", "-f", help="Config file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print commands without running"),
):
    """Install and prepare containers defined in pd-compose.yaml"""
    config = load_config(file)
    for name, svc in config.get("services", {}).items():
        image = svc.get("image", "ubuntu")
        typer.echo(f"Installing {name} from {image}...")
        if not dry_run:
            subprocess.run(["proot-distro", "install", "--name", name, image])

        login_args = ["proot-distro", "login", name]
        for bind in svc.get("binds", []):
            login_args += ["--bind", bind]
        for k, v in svc.get("environment", {}).items():
            login_args += ["--env", f"{k}={v}"]

        typer.echo(" ".join(login_args))


@app.command()
def down(
    file: Path = typer.Option("pd-compose.yaml", "--file", "-f", help="Config file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print commands without running"),
):
    """Remove containers defined in pd-compose.yaml"""
    config = load_config(file)
    for name in config.get("services", {}):
        typer.echo(f"Removing {name}...")
        if not dry_run:
            subprocess.run(["proot-distro", "remove", name])


@app.command()
def ps():
    """List installed containers"""
    subprocess.run(["proot-distro", "list"])


if __name__ == "__main__":
    app()
